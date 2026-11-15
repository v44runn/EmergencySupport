import { useState } from 'react';
import type { Depot, SupplyRequest, Vehicle, BlockedRoad, RouteAssignment, Coordinates } from './types/crisis';
import { parseAndCreateRequest, optimizeDispatch } from './services/api';
import { MapView } from './components/MapView';
import { RequestForm } from './components/RequestForm';
import { RequestList } from './components/RequestList';
import { VehiclePanel } from './components/VehiclePanel';
import { DispatchPanel } from './components/DispatchPanel';
import './App.css';

const INITIAL_DEPOT: Depot = {
  id: 'depot-1',
  name: 'Central Emergency Depot (Civic Auditorium)',
  location: { lat: 36.9738, lng: -122.0289 },
};

const INITIAL_VEHICLES: Vehicle[] = [
  { id: 'v1', name: 'Unit Alpha (Box Truck)', capacity: 200, currentLoad: 0, location: { lat: 36.9738, lng: -122.0289 }, color: '#2563eb' },
  { id: 'v2', name: 'Unit Bravo (4x4 Van)', capacity: 150, currentLoad: 0, location: { lat: 36.9745, lng: -122.0275 }, color: '#16a34a' },
  { id: 'v3', name: 'Unit Charlie (Utility)', capacity: 150, currentLoad: 0, location: { lat: 36.9731, lng: -122.0298 }, color: '#d97706' },
];

const INITIAL_REQUESTS: SupplyRequest[] = Array.from({ length: 15 }, (_, i) => ({
  id: `req-${i + 1}`,
  locationName: `Sector ${i + 1} Relief Point`,
  location: {
    lat: 36.965 + ((i * 37) % 19) * 0.0012,
    lng: -122.045 + ((i * 53) % 23) * 0.0014,
  },
  supplyType: i % 3 === 0 ? 'Medical Kits' : i % 2 === 0 ? 'Drinking Water' : 'MRE Packs',
  quantity: 15 + (i % 4) * 5,
  priority: i < 4 ? 'critical' : i < 9 ? 'high' : 'medium',
  status: 'pending',
}));

export function App() {
  const [requests, setRequests] = useState<SupplyRequest[]>(INITIAL_REQUESTS);
  const [vehicles] = useState<Vehicle[]>(INITIAL_VEHICLES);
  const [blockedRoads, setBlockedRoads] = useState<BlockedRoad[]>([]);
  const [routes, setRoutes] = useState<RouteAssignment[]>([]);
  const [blockingMode, setBlockingMode] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runOptimization = async (currentRequests = requests, currentBlocks = blockedRoads) => {
    setIsOptimizing(true);
    setError(null);
    try {
      const plan = await optimizeDispatch({
        depot: INITIAL_DEPOT,
        requests: currentRequests,
        vehicles,
        blockedRoads: currentBlocks,
      });
      setRoutes(plan);
      const assignedIds = new Set(plan.flatMap((r) => r.stops.map((s) => s.requestId)));
      setRequests((prev) =>
        prev.map((r) => ({ ...r, status: assignedIds.has(r.id) ? 'assigned' : 'pending' }))
      );
    } catch {
      setError('Failed to calculate dispatch routes.');
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleAddRequest = async (rawText: string) => {
    const newReq = await parseAndCreateRequest(rawText);
    const updated = [newReq, ...requests];
    setRequests(updated);
    await runOptimization(updated, blockedRoads);
  };

  const handleMapClick = async (coords: Coordinates) => {
    const newBlock: BlockedRoad = {
      id: `block-${Date.now()}`,
      label: `Road Closure #${blockedRoads.length + 1}`,
      location: coords,
    };
    const updatedBlocks = [...blockedRoads, newBlock];
    setBlockedRoads(updatedBlocks);
    setBlockingMode(false);
    await runOptimization(requests, updatedBlocks);
  };

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <header className="brand-header">
          <h1>CrisisGrid</h1>
          <span>Disaster Logistics Command</span>
        </header>

        {error && <div className="error-banner">{error}</div>}

        <DispatchPanel
          routes={routes}
          blockedRoads={blockedRoads}
          isOptimizing={isOptimizing}
          blockingMode={blockingMode}
          onToggleBlockingMode={() => setBlockingMode((b) => !b)}
          onClearBlocks={() => {
            setBlockedRoads([]);
            runOptimization(requests, []);
          }}
          onOptimize={() => runOptimization()}
        />

        <RequestForm onSubmitText={handleAddRequest} />
        <VehiclePanel vehicles={vehicles} routes={routes} />
        <RequestList requests={requests} />
      </aside>

      <main className="map-wrapper">
        <MapView
          depot={INITIAL_DEPOT}
          requests={requests}
          vehicles={vehicles}
          blockedRoads={blockedRoads}
          routes={routes}
          blockingMode={blockingMode}
          onMapClick={handleMapClick}
        />
      </main>
    </div>
  );
}

export default App;
