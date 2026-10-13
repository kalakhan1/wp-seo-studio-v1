/**
 * Types mirroring backend/app/schemas/wc_shipping.py
 */

export type ZoneType = "continent" | "country" | "state" | "postcode";

export interface ZoneLocation {
  code: string;
  type: ZoneType;
}

export interface WCShippingZone {
  id: number;
  name: string;
  order: number;
}

export interface WCShippingMethod {
  id: number | null;
  instance_id: number | null;
  title: string;
  method_id: string;
  method_title: string;
  method_description: string;
  enabled: boolean;
  settings: Record<string, unknown>;
}

export interface WCShippingZoneDetail {
  zone: WCShippingZone;
  locations: ZoneLocation[];
  methods: WCShippingMethod[];
}

export interface ZoneListResponse {
  items: WCShippingZone[];
}

export interface WCAvailableMethod {
  id: string;
  title: string;
  description: string;
}

export interface AvailableMethodsResponse {
  items: WCAvailableMethod[];
}

export interface ZoneCreateRequest {
  name: string;
  order?: number;
  locations?: ZoneLocation[];
}

export interface ZoneUpdateRequest {
  name?: string;
  order?: number;
  locations?: ZoneLocation[];
}

export interface MethodAddRequest {
  method_id: string;
  title?: string;
  enabled?: boolean;
  settings?: Record<string, unknown>;
}

export interface MethodUpdateRequest {
  title?: string;
  enabled?: boolean;
  settings?: Record<string, unknown>;
}