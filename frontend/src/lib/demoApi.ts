import type {
  AIRecommendationTrace,
  AdminUser,
  Approval,
  ApprovalContext,
  AuditLog,
  BehaviorRow,
  Customer,
  DataQuality,
  EnterpriseReadiness,
  GovernanceSummary,
  Inventory,
  Kpis,
  ModelRun,
  NegotiationAssistant,
  Product,
  QuoteDetail,
  QuoteFinanceSnapshot,
  QuotePolicyCheck,
  Recommendation,
  ReviewQueueItem,
  Role,
  Rule,
  SeriesPoint,
  UploadedFileRecord,
  UploadType,
  UserMe,
} from '../types/api';

export interface ApiResponse<T> {
  data: T;
}

export interface ApiClient {
  get<T = unknown>(url: string, config?: unknown): Promise<ApiResponse<T>>;
  post<T = unknown>(url: string, data?: unknown, config?: unknown): Promise<ApiResponse<T>>;
  patch<T = unknown>(url: string, data?: unknown, config?: unknown): Promise<ApiResponse<T>>;
  delete<T = unknown>(url: string, config?: unknown): Promise<ApiResponse<T>>;
}

type UploadReviewAction = 'save_draft' | 'confirm_and_save' | 'submit_for_review' | 'activate' | 'reject';

interface SandboxProduct {
  id: string;
  sku: string;
  name: string;
  category: string;
  base_cost: number;
  current_price: number;
}

interface UploadTypeInfo {
  type: UploadType;
  label: string;
  extensions: string[];
}

interface ExtractionEntity {
  type: string;
  count: number;
  samples: string[];
}

interface ExtractionPayload {
  summary: string;
  detected_type: string;
  entities: ExtractionEntity[];
  entities_count: number;
  confidence: number;
  suggested_rules: string[];
  text_preview: string;
}

interface UploadReviewPayload {
  file_id: string;
  file_name: string;
  upload_type: string;
  status: string;
  review_id: string | null;
  review_status: string;
  review_notes: string | null;
  next_step: string;
  current_extraction: ExtractionPayload;
  original_extraction: Record<string, unknown>;
  corrected_extraction: Record<string, unknown> | null;
  extraction?: ExtractionPayload;
  message?: string;
}

interface DemoState {
  users: AdminUser[];
  customers: Customer[];
  products: Product[];
  inventory: Inventory[];
  quotes: QuoteDetail[];
  approvals: Approval[];
  rules: Rule[];
  uploads: UploadedFileRecord[];
  uploadReviews: Record<string, UploadReviewPayload>;
  financeSnapshots: Record<string, QuoteFinanceSnapshot>;
  modelRuns: ModelRun[];
  aiRecommendations: AIRecommendationTrace[];
  auditLogs: AuditLog[];
}

const now = new Date('2026-06-08T10:30:00+08:00').toISOString();
const stateKey = 'revenuemind_demo_state_v1';

const users: AdminUser[] = [
  {
    id: 'u-sales',
    name: 'Sales Manager',
    email: 'salesmanager@gmail.com',
    role: 'sales',
    approval_status: 'approved',
    account_status: 'active',
    approved_by_user_id: 'u-admin',
    approved_at: now,
    approval_reason: 'Seeded portfolio demo account',
    created_at: '2026-01-05T02:00:00.000Z',
  },
  {
    id: 'u-approver',
    name: 'Sales Director Approver',
    email: 'salesdirector@gmail.com',
    role: 'approver',
    approval_status: 'approved',
    account_status: 'active',
    approved_by_user_id: 'u-admin',
    approved_at: now,
    approval_reason: 'Seeded portfolio demo account',
    created_at: '2026-01-06T02:00:00.000Z',
  },
  {
    id: 'u-executive',
    name: 'Executive Viewer',
    email: 'executiveviewer@gmail.com',
    role: 'executive',
    approval_status: 'approved',
    account_status: 'active',
    approved_by_user_id: 'u-admin',
    approved_at: now,
    approval_reason: 'Seeded portfolio demo account',
    created_at: '2026-01-07T02:00:00.000Z',
  },
  {
    id: 'u-admin',
    name: 'Admin Governance',
    email: 'admin@gmail.com',
    role: 'admin',
    approval_status: 'approved',
    account_status: 'active',
    approved_by_user_id: 'u-admin',
    approved_at: now,
    approval_reason: 'Seeded portfolio demo account',
    created_at: '2026-01-04T02:00:00.000Z',
  },
];

const customers: Customer[] = [
  { id: 'c-sunway', name: 'Sunway Project Supply', tier: 'strategic', region: 'Central' },
  { id: 'c-penang', name: 'Penang Trade Partner', tier: 'core', region: 'Northern' },
  { id: 'c-johor', name: 'Johor Growth Builders', tier: 'growth', region: 'Southern' },
];

const products: Product[] = [
  {
    id: 'p-dc-pump',
    sku: 'CH-DC-220',
    name: 'DC Pump Controller 220W',
    category: 'Water Pump',
    list_price: 1480,
    unit_cost: 910,
  },
  {
    id: 'p-solar-heater',
    sku: 'CH-SWH-300',
    name: 'Solar Water Heater 300L',
    category: 'Water Heating',
    list_price: 3290,
    unit_cost: 2110,
  },
  {
    id: 'p-booster',
    sku: 'CH-BST-150',
    name: 'Booster Pump 1.5HP',
    category: 'Water Pump',
    list_price: 1880,
    unit_cost: 1185,
  },
  {
    id: 'p-filter',
    sku: 'CH-FLT-RO',
    name: 'Commercial RO Filter Set',
    category: 'Filtration',
    list_price: 2380,
    unit_cost: 1510,
  },
  {
    id: 'p-smart-valve',
    sku: 'CH-VLV-IOT',
    name: 'Smart Valve Control Kit',
    category: 'Controls',
    list_price: 980,
    unit_cost: 545,
  },
  {
    id: 'p-storage-tank',
    sku: 'CH-TNK-500',
    name: 'Storage Tank 500L',
    category: 'Storage',
    list_price: 1190,
    unit_cost: 680,
  },
];

const inventory: Inventory[] = [
  { id: 'i-dc-pump', product_id: 'p-dc-pump', on_hand: 420, stock_age_days_avg: 33 },
  { id: 'i-solar-heater', product_id: 'p-solar-heater', on_hand: 86, stock_age_days_avg: 72 },
  { id: 'i-booster', product_id: 'p-booster', on_hand: 154, stock_age_days_avg: 51 },
  { id: 'i-filter', product_id: 'p-filter', on_hand: 98, stock_age_days_avg: 46 },
  { id: 'i-smart-valve', product_id: 'p-smart-valve', on_hand: 610, stock_age_days_avg: 28 },
  { id: 'i-storage-tank', product_id: 'p-storage-tank', on_hand: 240, stock_age_days_avg: 64 },
];

const uploadTypes: UploadTypeInfo[] = [
  { type: 'sales_history', label: 'Sales History', extensions: ['.csv', '.xlsx'] },
  { type: 'product_catalog', label: 'Product Catalog', extensions: ['.csv', '.xlsx'] },
  { type: 'current_price_list', label: 'Current Price List', extensions: ['.csv', '.xlsx'] },
  { type: 'competitor_price_data', label: 'Competitor Price Data', extensions: ['.csv', '.xlsx'] },
  { type: 'promotion_calendar', label: 'Promotion Calendar', extensions: ['.csv', '.xlsx'] },
  { type: 'pricing_approval_sheet', label: 'Pricing Approval Sheet', extensions: ['.xlsx'] },
  { type: 'strategic_pricing_guideline', label: 'Strategic Pricing Guideline', extensions: ['.pdf'] },
  { type: 'quarterly_pricing_plan', label: 'Quarterly Pricing Plan', extensions: ['.xlsx'] },
  { type: 'strategic_targets', label: 'Strategic Targets', extensions: ['.csv', '.xlsx'] },
  { type: 'market_reports', label: 'Market Reports', extensions: ['.pdf', '.txt'] },
  { type: 'user_role_config', label: 'User Role Config', extensions: ['.csv', '.json'] },
  { type: 'pricing_policy', label: 'Pricing Policy', extensions: ['.pdf', '.txt'] },
  { type: 'audit_log_archive', label: 'Audit Log Archive', extensions: ['.csv'] },
  { type: 'model_configuration', label: 'Model Configuration', extensions: ['.json'] },
  { type: 'rule_mapping_template', label: 'Rule Mapping Template', extensions: ['.csv', '.xlsx'] },
  { type: 'campaign_memo', label: 'Campaign Memo', extensions: ['.pdf', '.txt'] },
  { type: 'trading_terms', label: 'Trading Terms', extensions: ['.pdf'] },
  { type: 'rebate_agreement', label: 'Rebate Agreement', extensions: ['.csv', '.xlsx'] },
  { type: 'contract_pricing', label: 'Contract Pricing', extensions: ['.xlsx'] },
  { type: 'margin_target_sheet', label: 'Margin Target Sheet', extensions: ['.csv', '.xlsx'] },
];

const rules: Rule[] = [
  {
    id: 'rule-direct-water-pump',
    channel: 'direct',
    category: 'Water Pump',
    margin_floor_percent: 18,
    max_discount_percent: 14,
    approval_required_below_margin_buffer: 3,
  },
  {
    id: 'rule-distributor-heating',
    channel: 'distributor',
    category: 'Water Heating',
    margin_floor_percent: 16,
    max_discount_percent: 12,
    approval_required_below_margin_buffer: 2,
  },
  {
    id: 'rule-project-controls',
    channel: 'project',
    category: 'Controls',
    margin_floor_percent: 20,
    max_discount_percent: 9,
    approval_required_below_margin_buffer: 4,
  },
];

const initialUploads: UploadedFileRecord[] = [
  createUploadRecord('up-pricebook', 'current_price_list_channels.xlsx', 'current_price_list', 'active', 'approved', 'u-admin'),
  createUploadRecord('up-policy', 'pricing_policy_master_2026.pdf', 'pricing_policy', 'active', 'approved', 'u-admin'),
  createUploadRecord('up-competitor', 'competitor_pricing_market_scan.csv', 'competitor_price_data', 'parsed', 'confirmed', 'u-sales'),
  createUploadRecord('up-campaign', 'campaign_memo_dc_pump_q3_2026.pdf', 'campaign_memo', 'needs_review', 'pending_review', 'u-admin'),
  createUploadRecord('up-market', 'market_report_water_heaters_2026.pdf', 'market_reports', 'active', 'approved', 'u-executive'),
];

const initialUploadReviews = Object.fromEntries(
  initialUploads.map((upload) => [upload.id, createUploadReview(upload, `Imported demo file ${upload.file_name}.`)]),
);

const initialQuotes = createInitialQuotes();

const INITIAL_STATE: DemoState = {
  users,
  customers,
  products,
  inventory,
  quotes: initialQuotes,
  approvals: [
    {
      id: 'ap-q-1002',
      quote_id: 'q-1002',
      requested_by_user_id: 'u-sales',
      approver_user_id: 'u-approver',
      requested_price: 1555,
      requested_discount: 17.3,
      status: 'pending',
      request_justification:
        'Strategic project requires one-time project pricing while staying near the AI lower band.',
      decision_reason: null,
      created_at: '2026-06-08T01:50:00.000Z',
      decided_at: null,
    },
  ],
  rules,
  uploads: initialUploads,
  uploadReviews: initialUploadReviews,
  financeSnapshots: Object.fromEntries(
    initialQuotes.map((quote) => [
      quote.id,
      createFinanceSnapshot(quote, quote.item.final_price ?? quote.item.requested_price ?? quote.item.recommended_price ?? 0),
    ]),
  ),
  modelRuns: [
    createModelRun('run-q-1001', 'q-1001', 'success', false, 820),
    createModelRun('run-q-1002', 'q-1002', 'success', false, 940),
    createModelRun('run-q-1003', 'q-1003', 'success', true, 410),
  ],
  aiRecommendations: initialQuotes
    .filter((quote) => quote.latest_recommendation)
    .map((quote, index) => createTrace(`trace-${index + 1}`, quote)),
  auditLogs: [
    createAuditLog('audit-1', 'u-admin', 'activate_upload', 'upload', 'up-policy', 'Policy document activated.'),
    createAuditLog('audit-2', 'u-sales', 'recommend_quote', 'quote', 'q-1001', 'AI price recommendation generated.'),
    createAuditLog('audit-3', 'u-sales', 'request_approval', 'approval', 'ap-q-1002', 'Approval requested for project discount.'),
  ],
};

function createInitialQuotes(): QuoteDetail[] {
  return [
    createQuote({
      id: 'q-1001',
      customer_id: 'c-sunway',
      product_id: 'p-dc-pump',
      quantity: 45,
      channel: 'direct',
      strategy_mode: 'maximize_profit',
      requested_price: 1210,
      status: 'recommended',
      created_at: '2026-06-08T00:20:00.000Z',
    }),
    createQuote({
      id: 'q-1002',
      customer_id: 'c-penang',
      product_id: 'p-booster',
      quantity: 80,
      channel: 'project',
      strategy_mode: 'market_expansion',
      requested_price: 1555,
      status: 'approval_pending',
      created_at: '2026-06-08T01:40:00.000Z',
    }),
    createQuote({
      id: 'q-1003',
      customer_id: 'c-johor',
      product_id: 'p-smart-valve',
      quantity: 120,
      channel: 'distributor',
      strategy_mode: 'clear_inventory',
      requested_price: 875,
      final_price: 890,
      status: 'finalized',
      created_at: '2026-06-07T04:10:00.000Z',
    }),
  ];
}

function createQuote(input: {
  id: string;
  customer_id: string;
  product_id: string;
  quantity: number;
  channel: string;
  strategy_mode: QuoteDetail['strategy_mode'];
  requested_price: number | null;
  final_price?: number | null;
  status: QuoteDetail['status'];
  created_at: string;
}): QuoteDetail {
  const customer = customers.find((item) => item.id === input.customer_id) ?? customers[0];
  const product = products.find((item) => item.id === input.product_id) ?? products[0];
  const requestedDiscount =
    input.requested_price === null ? null : ((product.list_price - input.requested_price) / product.list_price) * 100;
  const recommendation = buildRecommendation(input.id, product, input.quantity, input.requested_price ?? undefined, input.channel);

  return {
    id: input.id,
    created_by_user_id: 'u-sales',
    customer_id: input.customer_id,
    customer_name: customer.name,
    channel: input.channel,
    strategy_mode: input.strategy_mode,
    status: input.status,
    item: {
      id: `${input.id}-item`,
      product_id: input.product_id,
      quantity: input.quantity,
      requested_price: input.requested_price,
      requested_discount: requestedDiscount,
      recommended_price: recommendation.best_price,
      recommended_band_low: recommendation.band_low,
      recommended_band_high: recommendation.band_high,
      final_price: input.final_price ?? null,
      final_discount:
        input.final_price === undefined || input.final_price === null
          ? null
          : ((product.list_price - input.final_price) / product.list_price) * 100,
      margin_percent: recommendation.margin_percent,
      expected_profit: recommendation.expected_profit,
      win_probability: recommendation.win_probability,
      confidence: recommendation.confidence,
      risk_level: recommendation.risk_level,
    },
    latest_recommendation: {
      xgb: {
        win_probability: recommendation.win_probability,
        confidence: recommendation.confidence,
      },
      optimizer: {
        best: {
          price: recommendation.best_price,
          discount_percent: ((product.list_price - recommendation.best_price) / product.list_price) * 100,
          margin_percent: recommendation.margin_percent,
          expected_profit: recommendation.expected_profit,
          win_probability: recommendation.win_probability,
        },
        band_low: recommendation.band_low,
        band_high: recommendation.band_high,
        suggested_discount_low: recommendation.suggested_discount_low,
        suggested_discount_high: recommendation.suggested_discount_high,
        confidence: recommendation.confidence,
        points: recommendation.candidates,
      },
      gpt: recommendation.explanation,
      model_version: 'demo-v2026.06',
    },
    pricebook_compliance_summary: recommendation.pricebook_compliance_summary ?? null,
    contract_pricing_summary: recommendation.contract_pricing_summary ?? null,
    market_comparison_summary: recommendation.market_comparison_summary ?? null,
    created_at: input.created_at,
    updated_at: input.created_at,
  };
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function loadState(): DemoState {
  if (typeof window === 'undefined') return clone(INITIAL_STATE);
  const raw = window.localStorage.getItem(stateKey);
  if (!raw) return clone(INITIAL_STATE);
  try {
    const parsed = JSON.parse(raw) as DemoState;
    return { ...clone(INITIAL_STATE), ...parsed };
  } catch {
    return clone(INITIAL_STATE);
  }
}

function saveState(state: DemoState) {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(stateKey, JSON.stringify(state));
  }
}

function ok<T>(data: T): Promise<ApiResponse<T>> {
  return Promise.resolve({ data });
}

function fail(url: string, status: number, detail: string): never {
  const error = new Error(detail) as Error & {
    response: { status: number; data: { detail: string } };
    config: { url: string };
  };
  error.response = { status, data: { detail } };
  error.config = { url };
  throw error;
}

function id(prefix: string) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function roleFromToken(token: string | null): Role | null {
  if (!token) return null;
  if (token.startsWith('bypass-')) return token.replace('bypass-', '') as Role;
  const user = users.find((item) => token === `demo-${item.id}`);
  return user?.role ?? null;
}

function currentUser(state: DemoState, config?: unknown): UserMe {
  const headers = (config as { headers?: Record<string, string> } | undefined)?.headers;
  const explicitToken = headers?.Authorization?.replace('Bearer ', '') ?? null;
  const token = explicitToken ?? (typeof window !== 'undefined' ? window.localStorage.getItem('auth_token') : null);
  const role = roleFromToken(token);
  const session = typeof window !== 'undefined' ? window.localStorage.getItem('pricing_session') : null;
  if (session && !role) {
    try {
      return JSON.parse(session).user as UserMe;
    } catch {
      /* Fall back to admin below. */
    }
  }
  const user = state.users.find((item) => item.role === role) ?? state.users.find((item) => item.role === 'admin')!;
  return toUserMe(user);
}

function toUserMe(user: AdminUser): UserMe {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role,
    approval_status: user.approval_status,
    account_status: user.account_status,
  };
}

function sandboxProducts(state: DemoState): SandboxProduct[] {
  return state.products.map((product) => ({
    id: product.id,
    sku: product.sku,
    name: product.name,
    category: product.category,
    base_cost: product.unit_cost,
    current_price: product.list_price,
  }));
}

function productById(state: DemoState, productId: string) {
  const product = state.products.find((item) => item.id === productId);
  if (!product) fail(`/products/${productId}`, 404, 'Product not found');
  return product;
}

function quoteById(state: DemoState, quoteId: string) {
  const quote = state.quotes.find((item) => item.id === quoteId);
  if (!quote) fail(`/quotes/${quoteId}`, 404, 'Quote not found');
  return quote;
}

function buildRecommendation(
  quoteId: string,
  product: Product,
  quantity = 1,
  requestedPrice?: number,
  channel = 'direct',
): Recommendation {
  const inventoryRow = inventory.find((item) => item.product_id === product.id);
  const agingDiscount = inventoryRow && inventoryRow.stock_age_days_avg > 60 ? 0.04 : 0;
  const channelDiscount = channel === 'distributor' ? 0.06 : channel === 'project' ? 0.1 : 0.03;
  const targetDiscount = Math.min(0.18, Math.max(0.04, channelDiscount + agingDiscount));
  const anchor = requestedPrice ?? product.list_price * (1 - targetDiscount);
  const bestPrice = roundMoney(Math.min(product.list_price * 0.98, Math.max(product.unit_cost * 1.24, anchor)));
  const bandLow = roundMoney(Math.max(product.unit_cost * 1.18, bestPrice * 0.95));
  const bandHigh = roundMoney(Math.min(product.list_price, bestPrice * 1.06));
  const margin = ((bestPrice - product.unit_cost) / bestPrice) * 100;
  const riskLevel = margin < 16 ? 'high' : margin < 22 ? 'medium' : 'low';
  const candidates = [-0.08, -0.04, 0, 0.04, 0.08].map((shift) => {
    const price = roundMoney(bestPrice * (1 + shift));
    const marginPercent = ((price - product.unit_cost) / price) * 100;
    const discountPercent = ((product.list_price - price) / product.list_price) * 100;
    return {
      price,
      discount_percent: discountPercent,
      margin_percent: marginPercent,
      win_probability: Math.max(0.35, Math.min(0.88, 0.77 - shift * 2.1)),
      expected_profit: roundMoney((price - product.unit_cost) * quantity * Math.max(0.35, Math.min(0.88, 0.77 - shift * 2.1))),
      allowed: price >= bandLow,
    };
  });

  return {
    quote_id: quoteId,
    band_low: bandLow,
    band_high: bandHigh,
    best_price: bestPrice,
    suggested_discount_low: ((product.list_price - bandHigh) / product.list_price) * 100,
    suggested_discount_high: ((product.list_price - bandLow) / product.list_price) * 100,
    win_probability: 0.73,
    expected_profit: roundMoney((bestPrice - product.unit_cost) * quantity * 0.73),
    margin_percent: margin,
    confidence: 0.87,
    risk_level: riskLevel,
    safe_band: riskLevel === 'high' ? 'red' : riskLevel === 'medium' ? 'yellow' : 'green',
    explanation: {
      short_reason:
        'Recommended price balances current list price, true margin, inventory age, channel guardrails, and competitor positioning.',
      top_drivers: [
        `${product.category} margin floor remains protected at ${margin.toFixed(1)}%.`,
        `${channel.replace(/_/g, ' ')} channel receives controlled discounting for win probability.`,
        'Uploaded policy and pricebook files support the safe-band recommendation.',
      ],
      negotiation_tips: [
        'Anchor near the recommended price and trade any discount for volume commitment.',
        'Use delivery speed and warranty support as value proof before conceding price.',
        'Escalate below the safe band with clear competitor evidence.',
      ],
      approval_justification_suggestion:
        'Price is below the preferred AI band for strategic deal conversion; governance review requested with margin evidence.',
      executive_summary:
        'Deal remains commercially viable if final price stays inside the safe band and leakage controls are respected.',
    },
    candidates,
    safe_price_range: { low: bandLow, high: bandHigh },
    true_margin_snapshot_summary: {
      net_margin_percent: margin,
      leakage_amount: Math.max(0, bandLow - bestPrice),
    },
    policy_entitlements_summary: [
      {
        campaign_name: 'Q3 DC Pump Conversion Campaign',
        eligibility_status: product.category === 'Water Pump' ? 'eligible' : 'not_applicable',
      },
    ],
    pricebook_compliance_summary: {
      status: bestPrice >= bandLow ? 'compliant' : 'below_floor',
      source: 'current_price_list_channels.xlsx',
    },
    contract_pricing_summary: {
      status: channel === 'project' ? 'requires_review' : 'within_standard_terms',
      lower_bound: bandLow,
      upper_bound: bandHigh,
    },
    campaign_summary: {
      eligible: product.category === 'Water Pump',
      estimated_support: product.category === 'Water Pump' ? 1200 : 0,
    },
    campaign_evaluations: [
      {
        campaign_name: 'Q3 DC Pump Conversion Campaign',
        result: product.category === 'Water Pump' ? 'eligible' : 'not_applicable',
      },
    ],
    market_comparison_summary: {
      value_positioning_label: bestPrice > product.list_price * 0.9 ? 'premium_aligned' : 'market_defensive',
      market_comparison_summary:
        'Competitor scan shows comparable products clustered within 4-7% of the recommended price.',
    },
    value_positioning_label: bestPrice > product.list_price * 0.9 ? 'premium_aligned' : 'market_defensive',
    next_best_action:
      riskLevel === 'high' ? 'Request approval before committing this concession.' : 'Proceed inside the safe band.',
  };
}

function applyRecommendation(state: DemoState, quote: QuoteDetail): Recommendation {
  const product = productById(state, quote.item.product_id);
  const rec = buildRecommendation(
    quote.id,
    product,
    quote.item.quantity,
    quote.item.requested_price ?? undefined,
    quote.channel,
  );
  quote.item.recommended_price = rec.best_price;
  quote.item.recommended_band_low = rec.band_low;
  quote.item.recommended_band_high = rec.band_high;
  quote.item.margin_percent = rec.margin_percent;
  quote.item.expected_profit = rec.expected_profit;
  quote.item.win_probability = rec.win_probability;
  quote.item.confidence = rec.confidence;
  quote.item.risk_level = rec.risk_level;
  quote.status = quote.status === 'approval_pending' ? quote.status : 'recommended';
  quote.updated_at = new Date().toISOString();
  quote.latest_recommendation = {
    xgb: { win_probability: rec.win_probability, confidence: rec.confidence },
    optimizer: {
      best: {
        price: rec.best_price,
        discount_percent: ((product.list_price - rec.best_price) / product.list_price) * 100,
        margin_percent: rec.margin_percent,
        expected_profit: rec.expected_profit,
        win_probability: rec.win_probability,
      },
      band_low: rec.band_low,
      band_high: rec.band_high,
      suggested_discount_low: rec.suggested_discount_low,
      suggested_discount_high: rec.suggested_discount_high,
      confidence: rec.confidence,
      points: rec.candidates,
    },
    gpt: rec.explanation,
    model_version: 'demo-v2026.06',
  };
  quote.pricebook_compliance_summary = rec.pricebook_compliance_summary ?? null;
  quote.contract_pricing_summary = rec.contract_pricing_summary ?? null;
  quote.market_comparison_summary = rec.market_comparison_summary ?? null;
  state.financeSnapshots[quote.id] = createFinanceSnapshot(quote, rec.best_price);
  state.modelRuns.unshift(createModelRun(id('run'), quote.id, 'success', false, 650));
  state.aiRecommendations.unshift(createTrace(id('trace'), quote));
  state.auditLogs.unshift(createAuditLog(id('audit'), 'u-sales', 'recommend_quote', 'quote', quote.id, 'AI recommendation generated.'));
  return rec;
}

function createFinanceSnapshot(quote: QuoteDetail, proposedPrice: number): QuoteFinanceSnapshot {
  const product = products.find((item) => item.id === quote.item.product_id) ?? products[0];
  const quantity = quote.item.quantity;
  const listRevenue = product.list_price * quantity;
  const revenue = proposedPrice * quantity;
  const cogs = product.unit_cost * quantity;
  const rebate = revenue * (quote.channel === 'distributor' ? 0.025 : 0.012);
  const freight = quantity * 9.5;
  const fees = revenue * 0.008;
  const campaignCost = product.category === 'Water Pump' ? quantity * 12 : 0;
  const grossMargin = revenue - cogs;
  const netMargin = grossMargin - rebate - freight - fees - campaignCost;
  const leakage = Math.max(0, (quote.item.recommended_price ?? proposedPrice) - proposedPrice) * quantity;
  const netMarginPercent = revenue > 0 ? (netMargin / revenue) * 100 : 0;

  return {
    quote_id: quote.id,
    proposed_price: proposedPrice,
    list_revenue_total: roundMoney(listRevenue),
    discounted_revenue_total: roundMoney(revenue),
    revenue_total: roundMoney(revenue),
    cogs_total: roundMoney(cogs),
    rebate_amount: roundMoney(rebate),
    gift_cost_amount: product.category === 'Water Pump' ? 220 : 0,
    bundle_cost_amount: product.category === 'Controls' ? 180 : 0,
    promotion_allocation_amount: roundMoney(campaignCost),
    campaign_cost_amount: roundMoney(campaignCost),
    freight_amount: roundMoney(freight),
    fees_amount: roundMoney(fees),
    mdf_amount: roundMoney(revenue * 0.01),
    contract_effect_amount: quote.channel === 'project' ? roundMoney(revenue * 0.018) : 0,
    list_margin_amount: roundMoney(listRevenue - cogs),
    price_discount_amount: roundMoney(listRevenue - revenue),
    gross_margin_amount: roundMoney(grossMargin),
    net_margin_amount: roundMoney(netMargin),
    net_margin_percent: netMarginPercent,
    leakage_amount: roundMoney(leakage),
    leakage_reasons_json: leakage
      ? [{ code: 'PRICE_BELOW_AI', message: 'Selected price is below AI recommendation.' }]
      : [],
    leakage_flags_json: {
      flags:
        netMarginPercent < 16
          ? [{ code: 'LOW_TRUE_MARGIN', severity: 'high', message: 'True margin is below governance floor.' }]
          : [],
      contract_bounds: quote.contract_pricing_summary ?? null,
      policy_violations: createPolicyCheck(quote, proposedPrice).violations,
      contract_summary: quote.contract_pricing_summary ?? null,
    },
    rebate_summary: { program: 'FY2026 volume rebate', estimated_rebate: roundMoney(rebate) },
    contract_pricing_summary: quote.contract_pricing_summary ?? null,
    created_at: new Date().toISOString(),
  };
}

function createPolicyCheck(quote: QuoteDetail, selectedPrice?: number): QuotePolicyCheck {
  const product = products.find((item) => item.id === quote.item.product_id) ?? products[0];
  const price = selectedPrice ?? quote.item.final_price ?? quote.item.requested_price ?? quote.item.recommended_price ?? product.list_price;
  const margin = ((price - product.unit_cost) / price) * 100;
  const violations =
    margin < 16
      ? [
          {
            severity: 'high' as const,
            code: 'MARGIN_FLOOR',
            message: `True margin ${margin.toFixed(1)}% is below the governed floor for ${product.category}.`,
            source_document_id: 'up-policy',
            clause_id: 'POLICY-2026-04',
          },
        ]
      : price < (quote.item.recommended_band_low ?? 0)
        ? [
            {
              severity: 'medium' as const,
              code: 'BELOW_SAFE_BAND',
              message: 'Requested price is below the AI safe band and needs approval evidence.',
              source_document_id: 'up-pricebook',
              clause_id: 'PRICEBOOK-LSP-08',
            },
          ]
        : [];

  return {
    quote_id: quote.id,
    checked_at: new Date().toISOString(),
    pricebook_compliance_summary: quote.pricebook_compliance_summary ?? null,
    contract_pricing_summary: quote.contract_pricing_summary ?? null,
    campaign_summary: {
      eligible: product.category === 'Water Pump',
      support: product.category === 'Water Pump' ? 'Gift bundle plus MDF support available.' : 'No campaign match.',
    },
    campaign_evaluations: [
      {
        campaign_name: 'Q3 DC Pump Conversion Campaign',
        eligibility_status: product.category === 'Water Pump' ? 'eligible' : 'not_applicable',
      },
    ],
    market_comparison_summary: quote.market_comparison_summary ?? null,
    recommended_action: violations.length ? 'Route to approver with source evidence.' : 'Proceed inside approved guardrails.',
    violations,
    entitlements:
      product.category === 'Water Pump'
        ? [
            {
              campaign_id: 'camp-dc-q3',
              campaign_name: 'Q3 DC Pump Conversion Campaign',
              rule_type: 'gift_with_purchase',
              sku_codes: ['CH-VLV-IOT', 'CH-FLT-RO'],
              quantity: Math.max(1, Math.floor(quote.item.quantity / 20)),
              source_document_id: 'up-campaign',
              eligibility_status: 'eligible',
              estimated_campaign_cost: 720,
              summary: 'Bundle support available for project conversion volume.',
              next_action: 'Confirm stock and attach campaign memo.',
              discount_percent: 2,
              discount_amount: 120,
              bundle_skus: ['CH-VLV-IOT'],
            },
          ]
        : [],
  };
}

function createNegotiationAssistant(quote: QuoteDetail): NegotiationAssistant {
  const price = quote.item.recommended_price ?? quote.item.requested_price ?? 0;
  return {
    quote_id: quote.id,
    strategy_summary:
      'Lead with operational reliability and governance-backed pricing. Use price concessions only after securing volume, payment, or delivery commitments.',
    concession_ladder: [
      { step: 1, target_price: roundMoney(price * 1.02), message: 'Anchor above recommendation with service-level proof.' },
      { step: 2, target_price: roundMoney(price), message: 'Offer AI recommended price for signed volume commitment.' },
      { step: 3, target_price: roundMoney(price * 0.96), message: 'Concede only with approval evidence and restricted validity.' },
    ],
    guardrails: ['Stay inside safe band when possible.', 'Keep rebate and freight leakage visible.', 'Document competitor evidence.'],
    must_not_do: ['Do not promise below-floor pricing verbally.', 'Do not stack campaign support without approval.'],
    policy_refs: ['pricing_policy_master_2026.pdf', 'current_price_list_channels.xlsx'],
  };
}

function createApprovalContext(state: DemoState, approvalId: string): ApprovalContext {
  const approval = state.approvals.find((item) => item.id === approvalId);
  if (!approval) fail(`/approvals/${approvalId}/context`, 404, 'Approval not found');
  const quote = quoteById(state, approval.quote_id);
  const product = productById(state, quote.item.product_id);
  const currentFinance = createFinanceSnapshot(quote, quote.item.recommended_price ?? product.list_price);
  const requestedFinance = createFinanceSnapshot(quote, approval.requested_price ?? quote.item.requested_price ?? product.list_price);

  return {
    approval,
    quote_summary: {
      customer_name: quote.customer_name,
      channel: quote.channel,
      product_name: product.name,
      quantity: quote.item.quantity,
      status: quote.status,
    },
    ai_recommendation_summary: {
      recommended_price: quote.item.recommended_price,
      recommended_band_low: quote.item.recommended_band_low,
      recommended_band_high: quote.item.recommended_band_high,
      risk_level: quote.item.risk_level,
    },
    current_finance: currentFinance as unknown as Record<string, unknown>,
    requested_finance: requestedFinance as unknown as Record<string, unknown>,
    policy_check: createPolicyCheck(quote, approval.requested_price ?? undefined),
    market_comparison_summary: quote.market_comparison_summary ?? null,
    similar_cases: state.aiRecommendations.slice(0, 3).map((item) => ({
      recommendation_id: item.id,
      quote_id: item.quote_id,
      recommended_price: item.recommended_price,
      win_probability: item.win_probability,
      confidence: item.confidence,
      approval_status: item.approval_status,
      risk_level: item.risk_level,
      value_positioning_label: item.value_positioning_label,
      timestamp: item.timestamp,
    })),
    recommended_action:
      requestedFinance.net_margin_percent < 16
        ? 'Reject or request a revised price because true margin is below floor.'
        : 'Approve with documented project justification and short validity window.',
  };
}

function createUploadRecord(
  uploadId: string,
  fileName: string,
  uploadType: UploadType,
  status: UploadedFileRecord['status'],
  reviewStatus: string | null,
  userId: string,
): UploadedFileRecord {
  const ext = fileName.includes('.') ? `.${fileName.split('.').pop()}` : '';
  const user = users.find((item) => item.id === userId) ?? users[0];
  return {
    id: uploadId,
    uploaded_by_user_id: userId,
    uploaded_by_role: user.role,
    upload_type: uploadType,
    file_name: fileName,
    file_ext: ext,
    mime_type: null,
    file_hash: `demo${uploadId.replace(/[^a-z0-9]/gi, '')}hash0000000000`,
    file_size_bytes: 48000 + uploadId.length * 177,
    source_uri: null,
    status,
    meta_json: { demo: true },
    extraction_summary: `${title(uploadType)} extracted and linked to demo pricing governance.`,
    extracted_entities_count: 12,
    linked_policy_id: uploadType === 'pricing_policy' ? 'policy-2026' : null,
    linked_pricebook_id: uploadType === 'current_price_list' ? 'pricebook-2026' : null,
    linked_contract_id: uploadType === 'contract_pricing' ? 'contract-2026' : null,
    validation_issues: null,
    review_status: reviewStatus,
    created_at: now,
  };
}

function createUploadReview(upload: UploadedFileRecord, summary: string): UploadReviewPayload {
  const extraction: ExtractionPayload = {
    summary,
    detected_type: title(upload.upload_type),
    entities: [
      { type: 'sku', count: 8, samples: ['CH-DC-220', 'CH-BST-150'] },
      { type: 'margin_rule', count: 3, samples: ['floor 18%', 'max discount 12%'] },
      { type: 'channel', count: 3, samples: ['direct', 'project', 'distributor'] },
    ],
    entities_count: 14,
    confidence: 0.91,
    suggested_rules: [
      'Apply channel-specific discount ceilings before approving final price.',
      'Route quotes below safe band to approver with source evidence.',
    ],
    text_preview:
      'Demo extraction preview: pricing policy, channel pricebook, campaign support, and margin guardrails were detected from the uploaded source.',
  };

  return {
    file_id: upload.id,
    file_name: upload.file_name,
    upload_type: upload.upload_type,
    status: upload.status,
    review_id: `review-${upload.id}`,
    review_status: upload.review_status ?? 'draft',
    review_notes: null,
    next_step: nextStep(upload.status, upload.review_status),
    current_extraction: extraction,
    original_extraction: extraction as unknown as Record<string, unknown>,
    corrected_extraction: null,
    extraction,
  };
}

function nextStep(status: string, reviewStatus?: string | null) {
  if (status === 'active') return 'Trusted source is active in pricing decisions.';
  if (status === 'rejected') return 'Review rejected; upload a corrected source file.';
  if (reviewStatus === 'pending_review') return 'Governance reviewer should confirm extracted business rules.';
  return 'Confirm extraction and activate when ready.';
}

function uploadCenterFiles(state: DemoState) {
  return state.uploads.map((upload) => ({
    ...upload,
    next_step: nextStep(upload.status, upload.review_status),
  }));
}

function createModelRun(
  runId: string,
  quoteId: string | null,
  status: string,
  fallbackUsed: boolean,
  latencyMs: number,
): ModelRun {
  return {
    id: runId,
    run_type: 'pricing_recommendation',
    model_name: 'RevenueMind Demo Optimizer',
    model_version: 'demo-v2026.06',
    model_provider: 'browser-demo',
    request_id: `req-${runId}`,
    status,
    fallback_used: fallbackUsed,
    latency_ms: latencyMs,
    input_hash: `hash-${runId}`,
    related_quote_id: quoteId,
    related_product_id: quoteId ? initialQuotes.find((quote) => quote.id === quoteId)?.item.product_id ?? null : null,
    related_recommendation_id: null,
    meta_json: { demo: true },
    created_at: now,
  };
}

function createTrace(traceId: string, quote: QuoteDetail): AIRecommendationTrace {
  const product = products.find((item) => item.id === quote.item.product_id) ?? products[0];
  return {
    id: traceId,
    quote_id: quote.id,
    product_id: product.id,
    recommended_price: quote.item.recommended_price ?? product.list_price,
    recommended_price_low: quote.item.recommended_band_low,
    recommended_price_high: quote.item.recommended_band_high,
    confidence: quote.item.confidence ?? 0.84,
    win_probability: quote.item.win_probability,
    model_version: 'demo-v2026.06',
    model_provider: 'browser-demo',
    fallback_used: false,
    explanation_json: quote.latest_recommendation?.gpt ?? {},
    source_rule_ids_json: ['rule-direct-water-pump'],
    source_document_ids_json: ['up-policy', 'up-pricebook'],
    finance_snapshot_id: `finance-${quote.id}`,
    risk_level: quote.item.risk_level,
    competitor_comparison_summary_json: quote.market_comparison_summary ?? {},
    value_positioning_label:
      typeof quote.market_comparison_summary?.value_positioning_label === 'string'
        ? quote.market_comparison_summary.value_positioning_label
        : 'premium_aligned',
    approved_by_user_id: quote.status === 'approved' || quote.status === 'finalized' ? 'u-approver' : null,
    approval_status: quote.status === 'approval_pending' ? 'pending' : quote.status === 'rejected' ? 'rejected' : 'approved',
    timestamp: quote.updated_at,
  };
}

function createAuditLog(
  auditId: string,
  actorUserId: string | null,
  action: string,
  entityType: string,
  entityId: string,
  reason: string,
): AuditLog {
  return {
    id: auditId,
    actor_user_id: actorUserId,
    action,
    entity_type: entityType,
    entity_id: entityId,
    old_json: null,
    new_json: { demo: true },
    reason,
    model_version: action.includes('recommend') ? 'demo-v2026.06' : null,
    created_at: new Date().toISOString(),
  };
}

function analyticsData(state: DemoState, path: string) {
  const quoteCount = state.quotes.length || 1;
  const finalized = state.quotes.filter((quote) => quote.status === 'finalized').length;
  const approvalCount = state.approvals.length;
  const kpis: Kpis = {
    average_margin_percent: 24.8,
    average_decision_time_hours: 6.4,
    override_rate: 0.18,
    approval_rate: approvalCount / quoteCount,
    win_rate_proxy: finalized / quoteCount,
    aging_inventory_addressed_value: 184000,
    pricing_health_score: 86,
    average_leakage_amount: 1240,
    recommendation_acceptance_rate: 0.78,
  };

  const series: Record<string, SeriesPoint[]> = {
    '/analytics/discount-distribution': [
      { label: '0-5%', value: 8 },
      { label: '5-10%', value: 17 },
      { label: '10-15%', value: 11 },
      { label: '15%+', value: 4 },
    ],
    '/analytics/margin-by-category': [
      { label: 'Water Pump', value: 24.4 },
      { label: 'Water Heating', value: 28.1 },
      { label: 'Controls', value: 31.6 },
      { label: 'Filtration', value: 25.8 },
    ],
    '/analytics/inventory-impact': [
      { label: 'Aging stock', value: 62000 },
      { label: 'Normal stock', value: 122000 },
      { label: 'Protected stock', value: 98000 },
    ],
    '/analytics/leakage-over-time': [
      { label: 'Jan', value: 4200 },
      { label: 'Feb', value: 3600 },
      { label: 'Mar', value: 2800 },
      { label: 'Apr', value: 2400 },
      { label: 'May', value: 1600 },
      { label: 'Jun', value: 1240 },
    ],
    '/analytics/top-violation-codes': [
      { label: 'MARGIN_FLOOR', value: 7 },
      { label: 'BELOW_SAFE_BAND', value: 5 },
      { label: 'STACKED_CAMPAIGN', value: 2 },
    ],
    '/analytics/margin-waterfall': [
      { label: 'List margin', value: 32 },
      { label: 'Discount', value: -6 },
      { label: 'Rebate', value: -1.8 },
      { label: 'Freight', value: -0.9 },
      { label: 'True margin', value: 23.3 },
    ],
    '/analytics/campaign-performance': [
      { label: 'DC pump', value: 78 },
      { label: 'Water heater', value: 64 },
      { label: 'Filter set', value: 51 },
    ],
    '/analytics/leakage-sources': [
      { label: 'Discount', value: 48 },
      { label: 'Freight', value: 21 },
      { label: 'Rebate', value: 18 },
      { label: 'Campaign', value: 13 },
    ],
    '/analytics/competitor-positioning': [
      { label: 'Premium', value: 36 },
      { label: 'Market', value: 49 },
      { label: 'Defensive', value: 15 },
    ],
    '/analytics/category-profitability': [
      { label: 'Water Pump', value: 144000 },
      { label: 'Water Heating', value: 118000 },
      { label: 'Controls', value: 96000 },
      { label: 'Filtration', value: 76000 },
    ],
    '/analytics/approval-turnaround': [
      { label: 'Direct', value: 4.2 },
      { label: 'Project', value: 9.6 },
      { label: 'Distributor', value: 5.1 },
    ],
    '/analytics/recommendation-acceptance': [
      { label: 'Accepted', value: 78 },
      { label: 'Adjusted', value: 16 },
      { label: 'Rejected', value: 6 },
    ],
  };

  if (path === '/analytics/kpis') return kpis;
  if (path === '/analytics/overrides') {
    return [
      {
        quote_id: 'q-1002',
        sales_manager: 'Sales Manager',
        ai_price: 1680,
        final_price: 1555,
        reason: 'Strategic project conversion',
      },
      {
        quote_id: 'q-1003',
        sales_manager: 'Sales Manager',
        ai_price: 905,
        final_price: 890,
        reason: 'Inventory aging',
      },
    ];
  }
  if (path === '/analytics/sales-manager-behavior') {
    return [
      { sales_manager: 'Sales Manager', override_frequency: 0.18, avg_discount_vs_ai: 3.8, avg_margin_percent: 24.1 },
      { sales_manager: 'North Region Team', override_frequency: 0.11, avg_discount_vs_ai: 2.1, avg_margin_percent: 26.4 },
    ] satisfies BehaviorRow[];
  }
  return series[path] ?? [];
}

function governanceSummary(state: DemoState): GovernanceSummary {
  return {
    pending_upload_reviews: state.uploads.filter((upload) => upload.status === 'needs_review').length,
    pending_policy_reviews: 1,
    active_pricebooks: 2,
    active_campaigns: 3,
    active_contracts: 2,
    active_rebate_programs: 2,
    model_run_failures: state.modelRuns.filter((run) => run.status !== 'success').length,
    ai_trace_count: state.aiRecommendations.length,
    unmatched_competitor_records: 4,
    average_policy_confidence: 0.91,
  };
}

function dataQuality(state: DemoState): DataQuality {
  return {
    upload_parse_failures: 0,
    uploads_needing_review: state.uploads.filter((upload) => upload.status === 'needs_review').length,
    reviews_pending_activation: state.uploads.filter((upload) => upload.review_status === 'confirmed').length,
    unmatched_competitor_records: 4,
    recommendations_with_fallback: state.modelRuns.filter((run) => run.fallback_used).length,
    model_run_failures: state.modelRuns.filter((run) => run.status !== 'success').length,
    average_clause_confidence: 0.9,
  };
}

function enterpriseReadiness(): EnterpriseReadiness {
  return {
    score: 88,
    status: 'attention_needed',
    summary:
      'The demo control tower is ready for portfolio review with small governance queues intentionally left visible.',
    categories: {
      data: 0.9,
      security: 0.86,
      workflow: 0.92,
      observability: 0.84,
    },
    checks: [
      {
        id: 'ready-auth',
        category: 'Security',
        label: 'Role based access',
        status: 'pass',
        detail: 'Demo roles route to sales, approvals, analytics, and admin workspaces.',
        action: null,
      },
      {
        id: 'ready-upload',
        category: 'Data',
        label: 'Upload governance queue',
        status: 'warning',
        detail: 'One campaign memo remains in review to demonstrate governance workflow.',
        action: 'Open Rules & Files and activate the memo after review.',
      },
      {
        id: 'ready-trace',
        category: 'Observability',
        label: 'AI traceability',
        status: 'pass',
        detail: 'Recommendation traces include source rules, documents, risk level, and finance references.',
        action: null,
      },
    ],
  };
}

function reviewQueue(state: DemoState): ReviewQueueItem[] {
  return state.uploads
    .filter((upload) => upload.status === 'needs_review' || upload.status === 'draft')
    .map((upload) => ({
      item_type: 'upload',
      item_id: upload.id,
      label: upload.file_name,
      status: upload.status,
      source_reference: upload.source_uri,
      uploaded_at: upload.created_at,
      next_step: nextStep(upload.status, upload.review_status),
    }));
}

function title(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function roundMoney(value: number) {
  return Math.round(value * 100) / 100;
}

function readFormFile(data: unknown) {
  if (typeof FormData === 'undefined' || !(data instanceof FormData)) {
    return { name: 'demo-upload.csv', size: 48000 };
  }
  const entry = data.get('file');
  if (typeof File !== 'undefined' && entry instanceof File) {
    return { name: entry.name, size: entry.size };
  }
  return { name: 'demo-upload.csv', size: 48000 };
}

function readFormString(data: unknown, key: string, fallback: string) {
  if (typeof FormData === 'undefined' || !(data instanceof FormData)) return fallback;
  const value = data.get(key);
  return typeof value === 'string' && value.trim() ? value : fallback;
}

export function createDemoApi(): ApiClient {
  const state = loadState();

  const persist = <T>(data: T) => {
    saveState(state);
    return ok(data);
  };

  return {
    async get<T = unknown>(url: string, config?: unknown) {
      const parsed = new URL(url, 'https://demo.local');
      const path = parsed.pathname;

      if (path === '/auth/me') return ok(currentUser(state, config) as T);
      if (path === '/customers') return ok(clone(state.customers) as T);
      if (path === '/products') return ok(clone(state.products) as T);
      if (path === '/inventory') return ok(clone(state.inventory) as T);
      if (path === '/sandbox/products') return ok(sandboxProducts(state) as T);
      if (path === '/sandbox/dashboard/summary') {
        const demoProducts = sandboxProducts(state);
        return ok({
          total_products: demoProducts.length,
          average_price:
            demoProducts.reduce((sum, product) => sum + product.current_price, 0) / Math.max(1, demoProducts.length),
          predictions_made: state.aiRecommendations.length,
        } as T);
      }
      if (path === '/quotes') {
        return ok(
          state.quotes.map((quote) => ({
            id: quote.id,
            customer_name: quote.customer_name,
            channel: quote.channel,
            strategy_mode: quote.strategy_mode,
            status: quote.status,
            created_at: quote.created_at,
            updated_at: quote.updated_at,
          })) as T,
        );
      }
      if (/^\/quotes\/[^/]+$/.test(path)) {
        return ok(clone(quoteById(state, path.split('/')[2])) as T);
      }
      if (/^\/quotes\/[^/]+\/policy-check$/.test(path)) {
        const quote = quoteById(state, path.split('/')[2]);
        return ok(createPolicyCheck(quote) as T);
      }
      if (/^\/quotes\/[^/]+\/finance$/.test(path)) {
        const quoteId = path.split('/')[2];
        const quote = quoteById(state, quoteId);
        return ok((state.financeSnapshots[quoteId] ?? createFinanceSnapshot(quote, quote.item.recommended_price ?? 0)) as T);
      }
      if (/^\/quotes\/[^/]+\/negotiation-assistant$/.test(path)) {
        return ok(createNegotiationAssistant(quoteById(state, path.split('/')[2])) as T);
      }
      if (path === '/approvals') {
        const status = parsed.searchParams.get('status');
        return ok(state.approvals.filter((approval) => !status || approval.status === status) as T);
      }
      if (/^\/approvals\/[^/]+\/context$/.test(path)) {
        return ok(createApprovalContext(state, path.split('/')[2]) as T);
      }
      if (path.startsWith('/analytics/')) return ok(analyticsData(state, path) as T);
      if (path === '/upload-center/types') return ok(clone(uploadTypes) as T);
      if (path === '/upload-center/files') return ok(uploadCenterFiles(state) as T);
      if (/^\/upload-center\/files\/[^/]+\/review$/.test(path)) {
        const fileId = path.split('/')[3];
        const review = state.uploadReviews[fileId];
        if (!review) fail(path, 404, 'Upload review not found');
        return ok(clone(review) as T);
      }
      if (path === '/uploads') {
        const mine = parsed.searchParams.get('mine') !== 'false';
        const user = currentUser(state);
        return ok((mine ? state.uploads.filter((upload) => upload.uploaded_by_user_id === user.id) : state.uploads) as T);
      }
      if (path === '/admin/rules') return ok(clone(state.rules) as T);
      if (path === '/admin/audit-logs') return ok(clone(state.auditLogs) as T);
      if (path === '/admin/model-runs') return ok(clone(state.modelRuns) as T);
      if (path === '/admin/users') return ok(clone(state.users) as T);
      if (path === '/admin/ai-recommendations') return ok(clone(state.aiRecommendations) as T);
      if (path === '/admin/governance-summary') return ok(governanceSummary(state) as T);
      if (path === '/admin/document-review-queue') return ok(reviewQueue(state) as T);
      if (path === '/admin/data-quality') return ok(dataQuality(state) as T);
      if (path === '/admin/enterprise-readiness') return ok(enterpriseReadiness() as T);

      fail(path, 404, `Demo endpoint not implemented: ${path}`);
    },

    async post<T = unknown>(url: string, data?: unknown) {
      const parsed = new URL(url, 'https://demo.local');
      const path = parsed.pathname;

      if (path === '/auth/login') {
        const payload = data as { email?: string; password?: string };
        const user = state.users.find((item) => item.email.toLowerCase() === String(payload.email ?? '').toLowerCase());
        if (!user || payload.password !== '123456') fail(path, 401, 'Invalid demo credentials. Use password 123456.');
        return ok({ access_token: `demo-${user.id}` } as T);
      }
      if (path === '/auth/dev-login') {
        const role = (data as { role?: Role }).role ?? 'admin';
        const user = state.users.find((item) => item.role === role) ?? state.users[0];
        return ok({ access_token: `demo-${user.id}` } as T);
      }
      if (path === '/sandbox/pricing/recommend' || /^\/sandbox\/pricing\/recommend\/[^/]+$/.test(path)) {
        const productId = path.split('/').pop() ?? '';
        const product = productById(state, productId);
        const payload = data as { discount_percent?: number; channel?: string } | undefined;
        const recommendation = buildRecommendation(
          'sandbox',
          product,
          1,
          product.list_price * (1 - (payload?.discount_percent ?? 5) / 100),
          payload?.channel ?? 'direct',
        );
        return persist({
          product_id: product.id,
          predicted_price: recommendation.best_price,
          confidence: recommendation.confidence,
          explanation: recommendation.explanation.short_reason,
          model_version: 'demo-v2026.06',
          margin_percent: recommendation.margin_percent,
          rationale: recommendation.explanation.top_drivers.join(' '),
          channel: payload?.channel ?? 'direct',
          unit_cost: product.unit_cost,
          list_price: product.list_price,
        } as T);
      }
      if (path === '/quotes') {
        const payload = data as {
          customer_id: string;
          channel: string;
          strategy_mode: QuoteDetail['strategy_mode'];
          item: {
            product_id: string;
            quantity: number;
            requested_price: number | null;
            requested_discount: number | null;
          };
        };
        const product = productById(state, payload.item.product_id);
        const requestedPrice =
          payload.item.requested_price ??
          (payload.item.requested_discount === null
            ? product.list_price * 0.94
            : product.list_price * (1 - payload.item.requested_discount / 100));
        const quote = createQuote({
          id: id('q'),
          customer_id: payload.customer_id,
          product_id: payload.item.product_id,
          quantity: payload.item.quantity,
          channel: payload.channel,
          strategy_mode: payload.strategy_mode,
          requested_price: roundMoney(requestedPrice),
          status: 'draft',
          created_at: new Date().toISOString(),
        });
        state.quotes.unshift(quote);
        state.financeSnapshots[quote.id] = createFinanceSnapshot(quote, requestedPrice);
        state.auditLogs.unshift(createAuditLog(id('audit'), 'u-sales', 'create_quote', 'quote', quote.id, 'Quote created in demo.'));
        return persist({ id: quote.id } as T);
      }
      if (/^\/quotes\/[^/]+\/recommend$/.test(path)) {
        return persist(applyRecommendation(state, quoteById(state, path.split('/')[2])) as T);
      }
      if (/^\/quotes\/[^/]+\/finalize$/.test(path)) {
        const quote = quoteById(state, path.split('/')[2]);
        const price = Number((data as { final_price?: number })?.final_price ?? quote.item.recommended_price ?? 0);
        quote.item.final_price = price;
        quote.item.final_discount = ((productById(state, quote.item.product_id).list_price - price) / productById(state, quote.item.product_id).list_price) * 100;
        quote.status = 'finalized';
        quote.updated_at = new Date().toISOString();
        state.financeSnapshots[quote.id] = createFinanceSnapshot(quote, price);
        state.auditLogs.unshift(createAuditLog(id('audit'), 'u-sales', 'finalize_quote', 'quote', quote.id, 'Quote finalized.'));
        return persist({ ok: true } as T);
      }
      if (/^\/quotes\/[^/]+\/request-approval$/.test(path)) {
        const quote = quoteById(state, path.split('/')[2]);
        const payload = data as { requested_price?: number; requested_discount?: number; justification?: string };
        quote.status = 'approval_pending';
        quote.updated_at = new Date().toISOString();
        const approval: Approval = {
          id: id('ap'),
          quote_id: quote.id,
          requested_by_user_id: 'u-sales',
          approver_user_id: 'u-approver',
          requested_price: payload.requested_price ?? quote.item.requested_price,
          requested_discount: payload.requested_discount ?? quote.item.requested_discount,
          status: 'pending',
          request_justification: payload.justification ?? 'Requested outside AI safe band.',
          decision_reason: null,
          created_at: new Date().toISOString(),
          decided_at: null,
        };
        state.approvals.unshift(approval);
        state.auditLogs.unshift(createAuditLog(id('audit'), 'u-sales', 'request_approval', 'approval', approval.id, approval.request_justification));
        return persist({ ok: true } as T);
      }
      if (/^\/quotes\/[^/]+\/simulate-finance$/.test(path)) {
        const quote = quoteById(state, path.split('/')[2]);
        const price = Number((data as { proposed_price?: number })?.proposed_price ?? quote.item.recommended_price ?? 0);
        const snapshot = createFinanceSnapshot(quote, price);
        state.financeSnapshots[quote.id] = snapshot;
        return persist(snapshot as T);
      }
      if (/^\/quotes\/[^/]+\/save-draft$/.test(path)) {
        const quote = quoteById(state, path.split('/')[2]);
        const payload = data as { requested_price?: number; strategy_mode?: QuoteDetail['strategy_mode'] };
        quote.item.requested_price = payload.requested_price ?? quote.item.requested_price;
        quote.strategy_mode = payload.strategy_mode ?? quote.strategy_mode;
        quote.status = 'draft';
        quote.updated_at = new Date().toISOString();
        return persist({ ok: true } as T);
      }
      if (/^\/approvals\/[^/]+\/(approve|reject)$/.test(path)) {
        const [, , approvalId, decision] = path.split('/');
        const approval = state.approvals.find((item) => item.id === approvalId);
        if (!approval) fail(path, 404, 'Approval not found');
        approval.status = decision === 'approve' ? 'approved' : 'rejected';
        approval.decision_reason = (data as { decision_reason?: string })?.decision_reason ?? 'Reviewed decision';
        approval.decided_at = new Date().toISOString();
        const quote = quoteById(state, approval.quote_id);
        quote.status = decision === 'approve' ? 'approved' : 'rejected';
        quote.updated_at = new Date().toISOString();
        state.auditLogs.unshift(createAuditLog(id('audit'), 'u-approver', decision, 'approval', approval.id, approval.decision_reason));
        return persist({ ok: true } as T);
      }
      if (path === '/bulk-import/products') {
        return persist({ imported: 3, skipped: 1, errors: [], total_rows: 4 } as T);
      }
      if (path === '/upload-center/upload' || path === '/uploads') {
        const file = readFormFile(data);
        const uploadType = readFormString(data, 'upload_type', 'product_catalog') as UploadType;
        const current = currentUser(state);
        const upload = createUploadRecord(id('up'), file.name, uploadType, path === '/uploads' ? 'parsed' : 'needs_review', path === '/uploads' ? 'confirmed' : 'draft', current.id);
        upload.file_size_bytes = file.size;
        upload.source_uri = readFormString(data, 'source_uri', '');
        const review = createUploadReview(upload, `${file.name} analyzed in the browser demo and ready for governance review.`);
        review.message = 'File analyzed in demo mode. No backend service is required.';
        state.uploads.unshift(upload);
        state.uploadReviews[upload.id] = review;
        state.auditLogs.unshift(createAuditLog(id('audit'), current.id, 'upload_file', 'upload', upload.id, 'Demo upload recorded.'));
        return persist(review as T);
      }
      if (path === '/admin/rules') {
        const payload = data as Omit<Rule, 'id'>;
        const existing = state.rules.find((rule) => rule.channel === payload.channel && rule.category === payload.category);
        if (existing) Object.assign(existing, payload);
        else state.rules.unshift({ id: id('rule'), ...payload });
        return persist({ ok: true } as T);
      }
      if (path === '/admin/users') {
        const payload = data as { name: string; email: string; role: Role; account_status: AdminUser['account_status'] };
        if (state.users.some((user) => user.email.toLowerCase() === payload.email.toLowerCase())) {
          fail(path, 400, 'Email already exists in demo directory.');
        }
        const user: AdminUser = {
          id: id('u'),
          name: payload.name,
          email: payload.email,
          role: payload.role,
          approval_status: 'approved',
          account_status: payload.account_status,
          approved_by_user_id: 'u-admin',
          approved_at: new Date().toISOString(),
          approval_reason: 'Created from demo admin workspace',
          created_at: new Date().toISOString(),
        };
        state.users.unshift(user);
        state.auditLogs.unshift(createAuditLog(id('audit'), 'u-admin', 'create_user', 'user', user.id, 'Employee created.'));
        return persist(user as T);
      }
      if (/^\/admin\/users\/[^/]+\/reset-password$/.test(path)) {
        const user = state.users.find((item) => item.id === path.split('/')[3]);
        if (!user) fail(path, 404, 'User not found');
        state.auditLogs.unshift(createAuditLog(id('audit'), 'u-admin', 'reset_password', 'user', user.id, 'Password reset in demo.'));
        return persist({ user_id: user.id, email: user.email, message: 'Demo password is now 123456.' } as T);
      }

      fail(path, 404, `Demo endpoint not implemented: ${path}`);
    },

    async patch<T = unknown>(url: string, data?: unknown) {
      const parsed = new URL(url, 'https://demo.local');
      const path = parsed.pathname;

      if (/^\/admin\/users\/[^/]+\/status$/.test(path)) {
        const user = state.users.find((item) => item.id === path.split('/')[3]);
        if (!user) fail(path, 404, 'User not found');
        user.account_status = (data as { account_status?: AdminUser['account_status'] }).account_status ?? user.account_status;
        return persist({ ok: true } as T);
      }
      if (/^\/upload-center\/files\/[^/]+\/review$/.test(path)) {
        const fileId = path.split('/')[3];
        const review = state.uploadReviews[fileId];
        const upload = state.uploads.find((item) => item.id === fileId);
        if (!review || !upload) fail(path, 404, 'Upload review not found');
        const payload = data as Partial<ExtractionPayload> & { action?: UploadReviewAction; review_notes?: string };
        review.current_extraction = {
          ...review.current_extraction,
          summary: payload.summary ?? review.current_extraction.summary,
          detected_type: payload.detected_type ?? review.current_extraction.detected_type,
          confidence: payload.confidence ?? review.current_extraction.confidence,
          entities: payload.entities ?? review.current_extraction.entities,
          entities_count: payload.entities?.reduce((sum, entity) => sum + entity.count, 0) ?? review.current_extraction.entities_count,
          suggested_rules: payload.suggested_rules ?? review.current_extraction.suggested_rules,
        };
        review.review_notes = payload.review_notes ?? review.review_notes;
        review.corrected_extraction = review.current_extraction as unknown as Record<string, unknown>;
        const action = payload.action ?? 'save_draft';
        if (action === 'activate') {
          upload.status = 'active';
          upload.review_status = 'approved';
        } else if (action === 'reject') {
          upload.status = 'rejected';
          upload.review_status = 'rejected';
        } else if (action === 'submit_for_review') {
          upload.status = 'needs_review';
          upload.review_status = 'pending_review';
        } else if (action === 'confirm_and_save') {
          upload.status = 'parsed';
          upload.review_status = 'confirmed';
        } else {
          upload.status = 'draft';
          upload.review_status = 'draft';
        }
        review.status = upload.status;
        review.review_status = upload.review_status ?? 'draft';
        review.next_step = nextStep(upload.status, upload.review_status);
        upload.extraction_summary = review.current_extraction.summary;
        upload.extracted_entities_count = review.current_extraction.entities_count;
        return persist(clone(review) as T);
      }

      fail(path, 404, `Demo endpoint not implemented: ${path}`);
    },

    async delete<T = unknown>(url: string) {
      const parsed = new URL(url, 'https://demo.local');
      const path = parsed.pathname;

      if (/^\/uploads\/[^/]+$/.test(path)) {
        const uploadId = path.split('/')[2];
        state.uploads = state.uploads.filter((upload) => upload.id !== uploadId);
        delete state.uploadReviews[uploadId];
        return persist({ ok: true } as T);
      }
      if (/^\/admin\/users\/[^/]+$/.test(path)) {
        const userId = path.split('/')[3];
        state.users = state.users.filter((user) => user.id !== userId);
        return persist({ ok: true } as T);
      }

      fail(path, 404, `Demo endpoint not implemented: ${path}`);
    },
  };
}
