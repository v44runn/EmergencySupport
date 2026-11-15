/// <reference types="@types/google.maps" />
import { useEffect, type FC } from 'react';
import { APIProvider, Map as GoogleMap, Marker, useMap, type MapMouseEvent } from '@vis.gl/react-google-maps';
import type { Depot, SupplyRequest, Vehicle, BlockedRoad, RouteAssignment, Coordinates } from '../types/crisis';

interface Props {
  depot: Depot;
  requests: SupplyRequest[];
  vehicles: Vehicle[];
  blockedRoads: BlockedRoad[];
  routes: RouteAssignment[];
  blockingMode: boolean;
  onMapClick: (coords: Coordinates) => void;
}

const RoutePolylines: FC<{ depot: Depot; routes: RouteAssignment[] }> = ({ depot, routes }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || typeof google === 'undefined') return;
    const polylines = routes.map((route) => {
      const path = [depot.location, ...route.stops.map((s) => s.location)];
      return new google.maps.Polyline({
        path,
        geodesic: true,
        strokeColor: route.color,
        strokeOpacity: 0.9,
        strokeWeight: 4,
        map,
      });
    });

    return () => {
      polylines.forEach((p) => p.setMap(null));
    };
  }, [map, depot, routes]);

  return null;
};

export const MapView: FC<Props> = ({
  depot,
  requests,
  vehicles,
  blockedRoads,
  routes,
  blockingMode,
  onMapClick,
}) => {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  const handleMapClick = (e: MapMouseEvent) => {
    if (blockingMode && e.detail.latLng) {
      onMapClick({ lat: e.detail.latLng.lat, lng: e.detail.latLng.lng });
    }
  };

  return (
    <div className="map-container">
      {blockingMode && (
        <div className="map-banner">Click anywhere on the map to simulate a flooded / blocked road</div>
      )}
      <APIProvider apiKey={apiKey}>
        <GoogleMap
          defaultCenter={depot.location}
          defaultZoom={13}
          gestureHandling="greedy"
          onClick={handleMapClick}
        >
          <Marker position={depot.location} label="D" title={depot.name} />
          {requests.map((req, i) => (
            <Marker
              key={req.id}
              position={req.location}
              label={String(i + 1)}
              title={`${req.locationName} (${req.quantity}x ${req.supplyType})`}
            />
          ))}
          {vehicles.map((v) => (
            <Marker key={v.id} position={v.location} label="V" title={v.name} />
          ))}
          {blockedRoads.map((b) => (
            <Marker key={b.id} position={b.location} label="X" title={b.label} />
          ))}
          <RoutePolylines depot={depot} routes={routes} />
        </GoogleMap>
      </APIProvider>
    </div>
  );
};
