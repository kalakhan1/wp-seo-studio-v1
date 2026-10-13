/**
 * Types mirroring backend/app/schemas/wc_gateway.py
 */

export interface WCGateway {
  id: string;
  title: string;
  description: string;
  order: number;
  enabled: boolean;
  method_title: string;
  method_description: string;
  method_supports: string[];
  instructions: string;
  enable_for_virtual: boolean;
  enable_for_methods: string[];
}

export interface WCGatewayListResponse {
  items: WCGateway[];
}

export interface CODSettings {
  enabled?: boolean;
  title?: string;
  description?: string;
  instructions?: string;
  enable_for_virtual?: boolean;
}

export interface CODStatus {
  available: boolean;
  enabled: boolean;
  title: string;
  description: string;
  instructions: string;
  enable_for_virtual: boolean;
  shipping_zones_available: boolean;
  warnings: string[];
}