export interface Brand {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
}

export interface Device {
  id: string;
  name: string;
  slug: string;
  brand: Brand;
  image_url?: string;
  display?: string;
  chipset?: string;
  ram?: string;
  storage?: string;
  camera?: string;
  battery?: string;
  os?: string;
  release_year?: number;
}

export interface Retailer {
  id: string;
  name: string;
  slug: string;
  base_url: string;
  logo_url?: string;
}

export interface Price {
  id: string;
  device_id: string;
  retailer: Retailer;
  price_egp: number;
  original_price_egp?: number;
  product_url: string;
  in_stock: boolean;
  scraped_at: string;
}

export interface PriceTrendPoint {
  date: string;
  retailer: string;
  price_egp: number;
}

export interface PaginatedDevices {
  total: number;
  page: number;
  per_page: number;
  items: Device[];
}
