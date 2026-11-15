import type { FC } from 'react';
import { Route, AlertTriangle, RotateCcw } from 'lucide-react';
import type { RouteAssignment, BlockedRoad } from '../types/crisis';

interface Props {
  routes: RouteAssignment[];
  blockedRoads: BlockedRoad[];
  isOptimizing: boolean;
  blockingMode: boolean;
  onToggleBlockingMode: () => void;
  onClearBlocks: () => void;
  onOptimize: () => void;
}

export const DispatchPanel: FC<Props> = ({
  routes,
  blockedRoads,
  isOptimizing,
  blockingMode,
  onToggleBlockingMode,
  onClearBlocks,
  onOptimize,
}) => {
  return (
    <div className="panel-card">
      <h3>Dispatch & Road Simulation</h3>
      <div className="button-row">
        <button
          type="button"
          className={blockingMode ? 'btn-danger active' : 'btn-secondary'}
          onClick={onToggleBlockingMode}
        >
          <AlertTriangle size={15} />
          {blockingMode ? 'Click Map to Place Block' : 'Mark Road Blocked'}
        </button>
        {blockedRoads.length > 0 && (
          <button type="button" className="btn-secondary" onClick={onClearBlocks}>
            <RotateCcw size={15} /> Clear ({blockedRoads.length})
          </button>
        )}
      </div>

      <button type="button" className="btn-primary full-width" onClick={onOptimize} disabled={isOptimizing}>
        <Route size={16} />
        {isOptimizing ? 'Optimizing Routes...' : 'Generate Dispatch Plan'}
      </button>

      {routes.length > 0 && (
        <div className="route-summary">
          {routes.map((r) => (
            <div key={r.vehicleId} className="route-row">
              <strong style={{ color: r.color }}>{r.vehicleName}:</strong>{' '}
              {r.stops.map((s) => s.locationName).join(' → ') || 'Standby'}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
