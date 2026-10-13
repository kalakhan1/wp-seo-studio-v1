/**
 * Types mirroring backend/app/schemas/wc_settings.py
 */

export type WCSettingValue = string | number | boolean | string[] | null;

export interface WCSetting {
  id: string;
  label: string;
  description: string;
  type: string;
  value: WCSettingValue;
  default: WCSettingValue;
  options: Record<string, string>;
  tip: string;
}

export interface WCSettingsGroupResponse {
  group: string;
  settings: WCSetting[];
}

export interface WCSettingUpdateRequest {
  value: WCSettingValue;
}

export interface StoreAddress {
  address_1: string;
  address_2: string;
  city: string;
  postcode: string;
  country: string;
  state: string;
  country_state_raw: string;
}

export interface StoreProfile {
  address: StoreAddress;
  currency: string;
  currency_symbol: string;
  currency_position: string;
  price_num_decimals: number;
  price_thousand_sep: string;
  price_decimal_sep: string;
  weight_unit: string;
  dimension_unit: string;
  selling_locations_type: string;
  selling_countries: string[];
  shipping_locations_type: string;
  shipping_countries: string[];
  tax_enabled: boolean;
  prices_include_tax: boolean;
  tax_based_on: string;
  default_customer_address: string;
  guest_checkout_enabled: boolean;
  coupons_enabled: boolean;
  account_creation_enabled: boolean;
  registration_generate_password: boolean;
  reviews_enabled: boolean;
  reviews_rating_enabled: boolean;
  reviews_verified_required: boolean;
}

export type ChecklistStatus = "ok" | "recommended" | "missing";

export interface ChecklistItem {
  key: string;
  label: string;
  status: ChecklistStatus;
  message: string;
  current_value: string;
  suggested_value: string;
}

export interface StoreChecklist {
  items: ChecklistItem[];
  complete: number;
  recommended: number;
  missing: number;
}

export interface StoreProfileResponse {
  profile: StoreProfile;
  checklist: StoreChecklist;
  warnings: string[];
}