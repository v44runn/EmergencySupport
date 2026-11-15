
import math

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

SPEED_KMH = 30.0            
DETOUR = 1.3                # straight-line distance -> rough road distance
BLOCK_PENALTY_S = 6 * 3600  # extra cost for a leg that crosses a blocked zone
HORIZON_S = 24 * 3600
TIME_LIMIT_S = 2
# cost of NOT delivering a request, by priority (1 = most critical)
DROP_PENALTY = {1: 1_000_000, 2: 500_000, 3: 250_000, 4: 100_000, 5: 50_000}


# ---------- geometry ----------

def haversine_m(a: dict, b: dict) -> float:
    r = 6_371_000
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dphi = p2 - p1
    dl = math.radians(b["lng"] - a["lng"])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _xy(p: dict, ref: dict):
    """Flat x/y in meters around a reference point (fine for city-sized areas)."""
    return (
        (p["lng"] - ref["lng"]) * math.cos(math.radians(ref["lat"])) * 111_320,
        (p["lat"] - ref["lat"]) * 110_540,
    )


def in_zone(p: dict, zone: dict) -> bool:
    return haversine_m(p, zone["center"]) <= zone["radius_m"]


def crosses_zone(a: dict, b: dict, zone: dict) -> bool:
    """Does the straight leg a->b pass through the zone circle?"""
    ax, ay = _xy(a, zone["center"])
    bx, by = _xy(b, zone["center"])
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / l2))
    return math.hypot(ax + t * dx, ay + t * dy) <= zone["radius_m"]


# ---------- helpers ----------

def _unassigned(r: dict, reason: str) -> dict:
    return {"request_id": r["id"], "name": r["name"], "priority": r.get("priority", 3), "reason": reason}


def _empty_route(v: dict) -> dict:
    return {
        "vehicle_id": v["id"], "vehicle_name": v["name"], "capacity": v["capacity"], "load": 0,
        "distance_km": 0.0, "duration_min": 0.0, "stops": [], "path": [v["start"], v["start"]],
    }


def _result(routes, unassigned, engine="ortools"):
    return {
        "engine": engine,
        "routes": routes,
        "unassigned": unassigned,
        "assigned_count": sum(len(r["stops"]) for r in routes),
        "unassigned_count": len(unassigned),
        "units_delivered": sum(r["load"] for r in routes),
    }


# ---------- main entry point ----------

def generate_plan(requests: list[dict], vehicles: list[dict], zones: list[dict]) -> dict:
    # 1. screen out requests that can't be served at all
    feasible, unassigned = [], []
    max_cap = max((v["capacity"] for v in vehicles), default=0)
    for r in requests:
        if not vehicles:
            unassigned.append(_unassigned(r, "No vehicles available"))
        elif any(in_zone(r["location"], z) for z in zones):
            unassigned.append(_unassigned(r, "Location is inside a blocked zone"))
        elif r["quantity"] > max_cap:
            unassigned.append(_unassigned(
                r, f"Quantity {r['quantity']} exceeds the largest vehicle capacity ({max_cap})"))
        else:
            feasible.append(r)

    if not feasible:
        return _result([_empty_route(v) for v in vehicles], unassigned)

    # 2. build the model. Nodes: [vehicle depots..., requests...]
    nv = len(vehicles)
    pts = [v["start"] for v in vehicles] + [r["location"] for r in feasible]
    n = len(pts)
    speed_ms = SPEED_KMH / 3.6

    travel = [[0] * n for _ in range(n)]  # real seconds (used for time windows / ETAs)
    cost = [[0] * n for _ in range(n)]    # seconds + penalty for crossing a blocked zone
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            t = int(haversine_m(pts[i], pts[j]) * DETOUR / speed_ms)
            travel[i][j] = t
            blocked = any(crosses_zone(pts[i], pts[j], z) for z in zones)
            cost[i][j] = t + (BLOCK_PENALTY_S if blocked else 0)

    service = [0] * nv + [r.get("service_minutes", 5) * 60 for r in feasible]
    demand = [0] * nv + [r["quantity"] for r in feasible]

    manager = pywrapcp.RoutingIndexManager(n, nv, list(range(nv)), list(range(nv)))
    routing = pywrapcp.RoutingModel(manager)

    def arc_cost(fi, ti):
        return cost[manager.IndexToNode(fi)][manager.IndexToNode(ti)]

    def transit_time(fi, ti):
        f, t = manager.IndexToNode(fi), manager.IndexToNode(ti)
        return travel[f][t] + service[f]

    def demand_cb(fi):
        return demand[manager.IndexToNode(fi)]

    routing.SetArcCostEvaluatorOfAllVehicles(routing.RegisterTransitCallback(arc_cost))
    routing.AddDimension(routing.RegisterTransitCallback(transit_time), HORIZON_S, HORIZON_S, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    routing.AddDimensionWithVehicleCapacity(
        routing.RegisterUnaryTransitCallback(demand_cb), 0, [v["capacity"] for v in vehicles], True, "Capacity")

    for k, r in enumerate(feasible):
        idx = manager.NodeToIndex(nv + k)
        lo = (r.get("window_start_min") or 0) * 60
        end = r.get("window_end_min")
        hi = end * 60 if end is not None else HORIZON_S
        time_dim.CumulVar(idx).SetRange(lo, min(hi, HORIZON_S))
        # allow dropping a request, at a cost that grows with priority
        routing.AddDisjunction([idx], DROP_PENALTY.get(r.get("priority", 3), 100_000))

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = TIME_LIMIT_S

    # 3. solve
    solution = routing.SolveWithParameters(params)
    if solution is None:
        unassigned += [_unassigned(r, "Solver found no feasible plan") for r in feasible]
        return _result([_empty_route(v) for v in vehicles], unassigned)

    # 4. read the solution back out
    routes = []
    for vi, v in enumerate(vehicles):
        index = routing.Start(vi)
        stops, path, load, dist, prev = [], [v["start"]], 0, 0.0, v["start"]
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node >= nv:
                r = feasible[node - nv]
                dist += haversine_m(prev, r["location"]) * DETOUR
                prev = r["location"]
                load += r["quantity"]
                path.append(r["location"])
                stops.append({
                    "seq": len(stops) + 1,
                    "request_id": r["id"],
                    "name": r["name"],
                    "location": r["location"],
                    "quantity": r["quantity"],
                    "priority": r.get("priority", 3),
                    "eta_min": round(solution.Min(time_dim.CumulVar(index)) / 60, 1),
                })
            index = solution.Value(routing.NextVar(index))
        dist += haversine_m(prev, v["start"]) * DETOUR
        path.append(v["start"])
        duration = solution.Min(time_dim.CumulVar(index)) / 60 if stops else 0.0
        routes.append({
            "vehicle_id": v["id"], "vehicle_name": v["name"], "capacity": v["capacity"], "load": load,
            "distance_km": round(dist / 1000, 2), "duration_min": round(duration, 1),
            "stops": stops, "path": path,
        })

    for k, r in enumerate(feasible):
        idx = manager.NodeToIndex(nv + k)
        if solution.Value(routing.NextVar(idx)) == idx:  # node skipped
            unassigned.append(_unassigned(
                r, "Dropped: capacity or time window can't be met alongside higher-priority requests"))

    return _result(routes, unassigned)