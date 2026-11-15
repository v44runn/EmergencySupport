import type { SupplyRequest, Vehicle, Depot, BlockedRoad, RouteAssignment } from '../types/crisis';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function parseAndCreateRequest(rawText: string): Promise<SupplyRequest> {
  try {
    const res = await fetch(`${API_BASE}/api/requests/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: rawText }),
    });
    if (!res.ok) throw new Error('Backend request failed');
    return await res.json();
  } catch {
    return {
      id: `req-${Date.now()}`,
      rawText,
      locationName: 'Downtown Santa Cruz Shelter',
      location: {
        lat: 36.9741 + (Math.random() - 0.5) * 0.025,
        lng: -122.0308 + (Math.random() - 0.5) * 0.025,
      },
      supplyType: rawText.toLowerCase().includes('medical') ? 'Medical Kits' : 'Water & MREs',
      quantity: 25,
      priority: rawText.toLowerCase().includes('urgent') || rawText.toLowerCase().includes('critical') ? 'critical' : 'high',
      status: 'pending',
    };
  }
}

export async function optimizeDispatch(payload: {
  depot: Depot;
  requests: SupplyRequest[];
  vehicles: Vehicle[];
  blockedRoads: BlockedRoad[];
}): Promise<RouteAssignment[]> {
  try {
    const res = await fetch(`${API_BASE}/api/optimize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Optimization failed');
    return await res.json();
  } catch {
    const activeRequests = [...payload.requests];
    return payload.vehicles.map((vehicle, idx) => {
      const assigned = activeRequests.filter((_, i) => i % payload.vehicles.length === idx);
      const detourPenalty = payload.blockedRoads.length * 1.8;
      return {
        vehicleId: vehicle.id,
        vehicleName: vehicle.name,
        color: vehicle.color,
        stops: assigned.map((r) => ({
          requestId: r.id,
          locationName: r.locationName,
          location: r.location,
          supplyType: r.supplyType,
          quantity: r.quantity,
        })),
        totalDistanceKm: Number((assigned.length * 2.4 + detourPenalty).toFixed(1)),
        estimatedMinutes: Math.round(assigned.length * 7 + detourPenalty * 3),
      };
    });
  }
}
