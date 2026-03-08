import API from '../lib/api';

export interface SandboxDashboardSummary {
  total_products: number;
  average_price: number | null;
  predictions_made: number;
}

export interface SandboxProduct {
  id: string;
  sku: string;
  name: string;
  category: string;
  base_cost: number;
  current_price: number;
}

export interface SandboxRecommendation {
  product_id: string;
  predicted_price: number;
  confidence: number;
  explanation: string;
  model_version?: string;
  margin_percent?: number;
  rationale?: string;
  channel?: string;
  unit_cost?: number;
  list_price?: number;
}

export const getProducts = () => API.get<SandboxProduct[]>('/sandbox/products');

export const getDashboard = () => API.get<SandboxDashboardSummary>('/sandbox/dashboard/summary');

export const recommendPrice = (productId: string, discountPercent = 5, channel = 'direct') =>
  API.post<SandboxRecommendation>(`/sandbox/pricing/recommend/${productId}`, {
    discount_percent: discountPercent,
    channel,
  });

export default API;

