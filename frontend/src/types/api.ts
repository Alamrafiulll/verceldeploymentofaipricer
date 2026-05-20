export type Role = 'sales' | 'approver' | 'executive' | 'admin';
export type UserApprovalStatus = 'pending' | 'approved' | 'rejected';
export type UserAccountStatus = 'active' | 'inactive';

export type StrategyMode = 'maximize_profit' | 'clear_inventory' | 'market_expansion';

export type QuoteStatus =
  | 'draft'
  | 'recommended'
  | 'approval_pending'
  | 'approved'
  | 'rejected'
  | 'finalized';

export interface UserMe {
  id: string;
  name: string;
  email: string;
  role: Role;
  approval_status: UserApprovalStatus;
  account_status: UserAccountStatus;
}

export interface Customer {
  id: string;
  name: string;
  tier: 'strategic' | 'core' | 'growth';
  region: string;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  category: string;
  list_price: number;
  unit_cost: number;
}

export interface Inventory {
  id: string;
  product_id: string;
  on_hand: number;
  stock_age_days_avg: number;
}

export interface QuoteListRow {
  id: string;
  customer_name: string;
  channel: string;
  strategy_mode: StrategyMode;
  status: QuoteStatus;
  created_at: string;
  updated_at: string;
}

export interface CandidatePoint {
  price: number;
  discount_percent: number;
  margin_percent: number;
  win_probability: number;
  expected_profit: number;
  allowed: boolean;
}

export interface Recommendation {
  quote_id: string;
  band_low: number;
  band_high: number;
  best_price: number;
  suggested_discount_low: number;
  suggested_discount_high: number;
  win_probability: number;
  expected_profit: number;
  margin_percent: number;
  confidence: number;
  risk_level: 'low' | 'medium' | 'high';
  safe_band: 'green' | 'yellow' | 'red';
  explanation: {
    short_reason: string;
    top_drivers: string[];
    negotiation_tips: string[];
    approval_justification_suggestion?: string;
    executive_summary?: string;
  };
  candidates: CandidatePoint[];
  safe_price_range?: { low: number; high: number };
  true_margin_snapshot_summary?: Record<string, unknown> | null;
  policy_entitlements_summary?: Array<Record<string, unknown>> | null;
  pricebook_compliance_summary?: Record<string, unknown> | null;
  contract_pricing_summary?: Record<string, unknown> | null;
  campaign_summary?: Record<string, unknown> | null;
  campaign_evaluations?: Array<Record<string, unknown>> | null;
  market_comparison_summary?: Record<string, unknown> | null;
  value_positioning_label?: string | null;
  next_best_action?: string | null;
}

export interface QuoteDetail {
  id: string;
  created_by_user_id: string;
  customer_id: string;
  customer_name: string;
  channel: string;
  strategy_mode: StrategyMode;
  status: QuoteStatus;
  item: {
    id: string;
    product_id: string;
    quantity: number;
    requested_price: number | null;
    requested_discount: number | null;
    recommended_price: number | null;
    recommended_band_low: number | null;
    recommended_band_high: number | null;
    final_price: number | null;
    final_discount: number | null;
    margin_percent: number | null;
    expected_profit: number | null;
    win_probability: number | null;
    confidence: number | null;
    risk_level: 'low' | 'medium' | 'high' | null;
  };
  latest_recommendation: {
    xgb: Record<string, unknown>;
    optimizer: Record<string, unknown>;
    gpt: Record<string, unknown>;
    model_version: string;
  } | null;
  pricebook_compliance_summary?: Record<string, unknown> | null;
  contract_pricing_summary?: Record<string, unknown> | null;
  market_comparison_summary?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface PolicyViolation {
  severity: 'low' | 'medium' | 'high';
  code: string;
  message: string;
  source_document_id: string | null;
  clause_id: string | null;
}

export interface PolicyEntitlement {
  campaign_id: string;
  campaign_name: string;
  rule_type: string;
  sku_codes: string[];
  quantity: number;
  source_document_id: string | null;
  eligibility_status?: string | null;
  estimated_campaign_cost?: number | null;
  summary?: string | null;
  next_action?: string | null;
  discount_percent?: number | null;
  discount_amount?: number | null;
  bundle_skus?: string[];
}

export interface QuotePolicyCheck {
  quote_id: string;
  checked_at: string;
  pricebook_compliance_summary?: Record<string, unknown> | null;
  contract_pricing_summary?: Record<string, unknown> | null;
  campaign_summary?: Record<string, unknown> | null;
  campaign_evaluations?: Array<Record<string, unknown>> | null;
  market_comparison_summary?: Record<string, unknown> | null;
  recommended_action?: string | null;
  violations: PolicyViolation[];
  entitlements: PolicyEntitlement[];
}

export interface QuoteFinanceSnapshot {
  quote_id: string;
  proposed_price: number;
  list_revenue_total: number;
  discounted_revenue_total: number;
  revenue_total: number;
  cogs_total: number;
  rebate_amount: number;
  gift_cost_amount: number;
  bundle_cost_amount: number;
  promotion_allocation_amount: number;
  campaign_cost_amount: number;
  freight_amount: number;
  fees_amount: number;
  mdf_amount: number;
  contract_effect_amount: number;
  list_margin_amount: number;
  price_discount_amount: number;
  gross_margin_amount: number;
  net_margin_amount: number;
  net_margin_percent: number;
  leakage_amount: number;
  leakage_reasons_json: Array<Record<string, unknown>>;
  leakage_flags_json: {
    flags?: Array<{ code: string; severity: string; message: string }>;
    contract_bounds?: Record<string, unknown> | null;
    policy_violations?: PolicyViolation[];
    contract_summary?: Record<string, unknown> | null;
  };
  rebate_summary?: Record<string, unknown> | null;
  contract_pricing_summary?: Record<string, unknown> | null;
  created_at: string;
}

export interface NegotiationAssistant {
  quote_id: string;
  strategy_summary: string;
  concession_ladder: Array<{ step: number; target_price: number; message: string }>;
  guardrails: string[];
  must_not_do: string[];
  policy_refs: string[];
}

export interface Kpis {
  average_margin_percent: number;
  average_decision_time_hours: number;
  override_rate: number;
  approval_rate: number;
  win_rate_proxy: number;
  aging_inventory_addressed_value: number;
  pricing_health_score: number;
  average_leakage_amount: number;
  recommendation_acceptance_rate: number;
}

export interface SeriesPoint {
  label: string;
  value: number;
}

export interface OverrideRow {
  quote_id: string;
  sales_manager: string;
  ai_price: number;
  final_price: number;
  reason: string | null;
}

export interface BehaviorRow {
  sales_manager: string;
  override_frequency: number;
  avg_discount_vs_ai: number;
  avg_margin_percent: number;
}

export interface Rule {
  id: string;
  channel: string;
  category: string;
  margin_floor_percent: number;
  max_discount_percent: number;
  approval_required_below_margin_buffer: number;
}

export interface Approval {
  id: string;
  quote_id: string;
  requested_by_user_id: string;
  approver_user_id: string | null;
  requested_price: number | null;
  requested_discount: number | null;
  status: 'pending' | 'approved' | 'rejected';
  request_justification: string;
  decision_reason: string | null;
  created_at: string;
  decided_at: string | null;
}

export interface AuditLog {
  id: string;
  actor_user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  old_json: Record<string, unknown> | null;
  new_json: Record<string, unknown> | null;
  reason: string | null;
  model_version: string | null;
  created_at: string;
}

export interface PendingUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  approval_status: UserApprovalStatus;
  created_at: string;
}

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  approval_status: UserApprovalStatus;
  account_status: UserAccountStatus;
  approved_by_user_id: string | null;
  approved_at: string | null;
  approval_reason: string | null;
  created_at: string;
}

export type PriceBookChannel = 'lsp' | 'wm' | 'em';

export interface PriceBookItem {
  id: string;
  product_id: string;
  list_price: number;
  notes: string | null;
}

export interface PriceBook {
  id: string;
  name: string;
  channel: PriceBookChannel;
  currency: string;
  effective_start: string | null;
  effective_end: string | null;
  source_document_id: string | null;
  uploaded_by_user_id: string | null;
  uploaded_by_name: string | null;
  uploaded_by_email: string | null;
  created_at: string;
  items: PriceBookItem[];
}

export type PolicyDocumentType = 'memo' | 'price_list' | 'trading_terms' | 'finance';
export type PolicyDocumentStatus = 'draft' | 'active' | 'archived';

export interface PolicyClause {
  id: string;
  clause_type:
    | 'eligibility'
    | 'exclusion'
    | 'entitlement'
    | 'pricing'
    | 'rebate'
    | 'incentive'
    | 'payment_terms'
    | 'returns'
    | 'exchange'
    | 'other';
  structured_json: Record<string, unknown>;
  raw_text: string;
  confidence: number;
}

export interface PolicyDocument {
  id: string;
  title: string;
  doc_type: PolicyDocumentType;
  source_uri: string | null;
  file_hash: string;
  uploaded_by_user_id: string;
  uploaded_at: string;
  effective_start: string | null;
  effective_end: string | null;
  status: PolicyDocumentStatus;
  clauses: PolicyClause[];
}

export interface ModelRun {
  id: string;
  run_type: string;
  model_name: string;
  model_version: string | null;
  model_provider: string | null;
  request_id: string | null;
  status: string;
  fallback_used: boolean;
  latency_ms: number | null;
  input_hash: string | null;
  related_quote_id: string | null;
  related_product_id: string | null;
  related_recommendation_id: string | null;
  meta_json: Record<string, unknown>;
  created_at: string;
}

export type UploadType =
  | 'sales_history'
  | 'product_catalog'
  | 'current_price_list'
  | 'competitor_price_data'
  | 'promotion_calendar'
  | 'pricing_approval_sheet'
  | 'strategic_pricing_guideline'
  | 'quarterly_pricing_plan'
  | 'strategic_targets'
  | 'market_reports'
  | 'user_role_config'
  | 'pricing_policy'
  | 'audit_log_archive'
  | 'model_configuration'
  | 'rule_mapping_template'
  | 'campaign_memo'
  | 'trading_terms'
  | 'rebate_agreement'
  | 'contract_pricing'
  | 'margin_target_sheet';

export interface UploadedFileRecord {
  id: string;
  uploaded_by_user_id: string | null;
  uploaded_by_role: Role;
  upload_type: UploadType;
  file_name: string;
  file_ext: string;
  mime_type: string | null;
  file_hash: string;
  file_size_bytes: number;
  source_uri: string | null;
  status: 'active' | 'archived' | 'draft' | 'parsed' | 'needs_review' | 'rejected';
  meta_json: Record<string, unknown>;
  extraction_summary?: string | null;
  extracted_entities_count?: number | null;
  linked_policy_id?: string | null;
  linked_pricebook_id?: string | null;
  linked_contract_id?: string | null;
  validation_issues?: Record<string, unknown> | null;
  review_status?: string | null;
  created_at: string;
}

export interface AIRecommendationTrace {
  id: string;
  quote_id: string | null;
  product_id: string;
  recommended_price: number;
  recommended_price_low: number | null;
  recommended_price_high: number | null;
  confidence: number;
  win_probability: number | null;
  model_version: string;
  model_provider: string | null;
  fallback_used: boolean;
  explanation_json: Record<string, unknown>;
  source_rule_ids_json: string[];
  source_document_ids_json: string[];
  finance_snapshot_id: string | null;
  risk_level: string | null;
  competitor_comparison_summary_json: Record<string, unknown>;
  value_positioning_label: string | null;
  approved_by_user_id: string | null;
  approval_status: 'pending' | 'approved' | 'rejected';
  timestamp: string;
}

export interface GovernanceSummary {
  pending_upload_reviews: number;
  pending_policy_reviews: number;
  active_pricebooks: number;
  active_campaigns: number;
  active_contracts: number;
  active_rebate_programs: number;
  model_run_failures: number;
  ai_trace_count: number;
  unmatched_competitor_records: number;
  average_policy_confidence: number;
}

export interface ReviewQueueItem {
  item_type: string;
  item_id: string;
  label: string;
  status: string;
  source_reference: string | null;
  uploaded_at: string | null;
  next_step: string | null;
}

export interface DataQuality {
  upload_parse_failures: number;
  uploads_needing_review: number;
  reviews_pending_activation: number;
  unmatched_competitor_records: number;
  recommendations_with_fallback: number;
  model_run_failures: number;
  average_clause_confidence: number;
}

export interface SimilarApprovalCase {
  recommendation_id: string;
  quote_id: string | null;
  recommended_price: number;
  win_probability: number | null;
  confidence: number;
  approval_status: string;
  risk_level: string | null;
  value_positioning_label: string | null;
  timestamp: string;
}

export interface ApprovalContext {
  approval: Approval;
  quote_summary: Record<string, unknown>;
  ai_recommendation_summary: Record<string, unknown> | null;
  current_finance: Record<string, unknown> | null;
  requested_finance: Record<string, unknown> | null;
  policy_check: QuotePolicyCheck | null;
  market_comparison_summary: Record<string, unknown> | null;
  similar_cases: SimilarApprovalCase[];
  recommended_action: string;
}
