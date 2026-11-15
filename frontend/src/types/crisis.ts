export type Priority = 'critical' | 'high' | 'medium' | 'low';
export type RequestStatus = 'pending' | 'assigned' | 'delivered';

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface Depot {
  id: string;
  name: string;
  location: Coordinates;
}

export interface SupplyRequest {
  id: string;
  rawText?: string;
  locationName: string;
  location: Coordinates;
  supplyType: string;
  quantity: number;
  priority: Priority;
  status: RequestStatus;
  assignedVehicleId?: string;
}

export interface Vehicle {
  id: string;
  name: string;
  capacity: number;
  currentLoad: number;
  location: Coordinates;
  color: string;
}

export interface BlockedRoad {
  id: string;
  label: string;
  location: Coordinates;
}

export interface RouteAssignment {
  vehicleId: string;
  vehicleName: string;
  color: string;
  stops: {
    requestId: string;
    locationName: string;
    location: Coordinates;
    supplyType: string;
    quantity: number;
  }[];
  totalDistanceKm: number;
  estimatedMinutes: number;
}