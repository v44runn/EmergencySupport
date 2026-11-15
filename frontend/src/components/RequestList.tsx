import type { FC } from 'react';
import type { SupplyRequest } from '../types/crisis';

interface Props {
  requests: SupplyRequest[];
}

export const RequestList: FC<Props> = ({ requests }) => {
  return (
    <div className="panel-card">
      <h3>Supply Requests ({requests.length})</h3>
      <div className="scroll-list">
        {requests.map((req) => (
          <div key={req.id} className={`list-item priority-${req.priority}`}>
            <div className="item-header">
              <strong>{req.locationName}</strong>
              <span className={`badge badge-${req.priority}`}>{req.priority}</span>
            </div>
            <div className="item-meta">
              <span>{req.quantity}x {req.supplyType}</span>
              <span className="status-tag">{req.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
