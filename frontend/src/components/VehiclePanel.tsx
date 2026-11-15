import type { FC } from 'react';
import { Truck } from 'lucide-react';
import type { Vehicle, RouteAssignment } from '../types/crisis';

interface Props {
  vehicles: Vehicle[];
  routes: RouteAssignment[];
}

export const VehiclePanel: FC<Props> = ({ vehicles, routes }) => {
  return (
    <div className="panel-card">
      <h3>Fleet Status ({vehicles.length} Active)</h3>
      {vehicles.map((v) => {
        const route = routes.find((r) => r.vehicleId === v.id);
        const assignedQty = route?.stops.reduce((sum, s) => sum + s.quantity, 0) ?? 0;
        return (
          <div key={v.id} className="list-item" style={{ borderLeft: `4px solid ${v.color}` }}>
            <div className="item-header">
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Truck size={15} color={v.color} />
                <strong>{v.name}</strong>
              </span>
              <span>{assignedQty} / {v.capacity} units</span>
            </div>
            <div className="item-meta">
              <span>Assigned stops: {route?.stops.length ?? 0}</span>
              {route && <span>{route.totalDistanceKm} km (~{route.estimatedMinutes} min)</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
};
