from typing import Optional
import report_parser
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

import database
import optimizer

app = FastAPI(title="CrisisGrid API")

# lets the frontend call this from another origin
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------- models ----------

class LatLng(BaseModel):
    lat: float = Field(ge=-90, le=90, examples=[29.76])
    lng: float = Field(ge=-180, le=180, examples=[-95.37])


class RequestCreate(BaseModel):
    name: str
    location: LatLng
    quantity: int = Field(gt=0, description="Supply units needed")
    priority: int = Field(default=3, ge=1, le=5, description="1 = most critical")
    window_start_min: Optional[int] = Field(default=None, ge=0)
    window_end_min: Optional[int] = Field(default=None, ge=0)
    service_minutes: int = Field(default=5, ge=0)
    notes: Optional[str] = None
    source_text: Optional[str] = None  # raw report the AI parser extracted this from

    @model_validator(mode="after")
    def check_window(self):
        if (self.window_start_min is not None and self.window_end_min is not None
                and self.window_end_min < self.window_start_min):
            raise ValueError("window_end_min must be >= window_start_min")
        return self


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|delivered|cancelled)$")


class VehicleCreate(BaseModel):
    name: str
    capacity: int = Field(gt=0)
    start: LatLng  # depot; vehicle returns here


class ZoneCreate(BaseModel):
    name: str = "Closed road / flooded area"
    center: LatLng
    radius_m: float = Field(default=500, gt=0)


class ReportText(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    city_hint: Optional[str] = None  # e.g. "Houston, TX" improves geocoding


@app.post("/parse-report")
def parse_report(body: ReportText):
    """Gemini turns a text report into DRAFT requests. Nothing is saved yet."""
    try:
        drafts = report_parser.parse_report(body.text, body.city_hint)
    except RuntimeError as e:        # e.g. missing API key
        raise HTTPException(503, str(e))
    except Exception as e:           # Gemini/network failure
        raise HTTPException(502, f"Gemini request failed: {e}")
    return {"drafts": drafts}


# ---------- helpers ----------

def build_plan(reason: Optional[str] = None) -> dict:
    """Re-solve from current state and save the result."""
    requests = database.list_requests(status="pending")
    vehicles = database.list_vehicles()
    zones = database.list_zones()

    result = optimizer.generate_plan(requests, vehicles, zones)

    latest = database.latest_plan()
    plan = {
        **result,
        "id": database.new_id("plan"),
        "version": (latest["version"] + 1) if latest else 1,
        "reason": reason,
        "created_at": database.now_iso(),
        "blocked_zones": zones,
    }
    return database.save_plan(plan)


def maybe_replan(replan: bool, reason: str):
    if replan:
        build_plan(reason)


# ---------- health ----------

@app.get("/health")
def health():
    return {"ok": True}


# ---------- requests ----------

@app.post("/requests", status_code=201)
def create_request(body: RequestCreate, replan: bool = False):
    """replan=true re-solves right away; fetch the result with GET /plans/latest."""
    r = database.create_request(body.model_dump(mode="json"))
    maybe_replan(replan, f"new request: {r['name']}")
    return r


@app.get("/requests")
def list_requests(status: Optional[str] = None):
    return database.list_requests(status)


@app.get("/requests/{request_id}")
def get_request(request_id: str):
    r = database.get_request(request_id)
    if r is None:
        raise HTTPException(404, "request not found")
    return r


@app.patch("/requests/{request_id}/status")
def update_status(request_id: str, body: StatusUpdate, replan: bool = False):
    r = database.update_request_status(request_id, body.status)
    if r is None:
        raise HTTPException(404, "request not found")
    maybe_replan(replan, f"{r['name']} marked {body.status}")
    return r


@app.delete("/requests/{request_id}", status_code=204)
def delete_request(request_id: str):
    if not database.delete_request(request_id):
        raise HTTPException(404, "request not found")
    return Response(status_code=204)


# ---------- vehicles ----------

@app.post("/vehicles", status_code=201)
def create_vehicle(body: VehicleCreate):
    return database.create_vehicle(body.model_dump(mode="json"))


@app.get("/vehicles")
def list_vehicles():
    return database.list_vehicles()


@app.delete("/vehicles/{vehicle_id}", status_code=204)
def delete_vehicle(vehicle_id: str):
    if not database.delete_vehicle(vehicle_id):
        raise HTTPException(404, "vehicle not found")
    return Response(status_code=204)


# ---------- blocked zones ----------

@app.post("/blocked-zones", status_code=201)
def create_zone(body: ZoneCreate, replan: bool = False):
    z = database.create_zone(body.model_dump(mode="json"))
    maybe_replan(replan, f"blocked: {z['name']}")
    return z


@app.get("/blocked-zones")
def list_zones():
    return database.list_zones()


@app.delete("/blocked-zones/{zone_id}", status_code=204)
def delete_zone(zone_id: str, replan: bool = False):
    if not database.delete_zone(zone_id):
        raise HTTPException(404, "zone not found")
    maybe_replan(replan, "road reopened")
    return Response(status_code=204)


# ---------- plans ----------

@app.post("/plans/generate")
def generate_plan(reason: Optional[str] = None):
    return build_plan(reason)


@app.get("/plans")
def list_plans():
    return database.list_plans()


@app.get("/plans/latest")
def latest_plan():
    plan = database.latest_plan()
    if plan is None:
        raise HTTPException(404, "no plans yet; POST /plans/generate first")
    return plan
