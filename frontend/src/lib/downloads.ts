const UPLOAD_TEMPLATE_HEADERS: Record<string, string[]> = {
  sales_history: ['date', 'customer_name', 'sku', 'quantity', 'net_price', 'channel'],
  product_catalog: ['sku', 'name', 'category', 'unit_cost', 'list_price'],
  current_price_list: ['sku', 'price', 'effective_start', 'effective_end', 'channel'],
  competitor_price_data: ['competitor_name', 'sku', 'competitor_price', 'observed_date', 'source'],
  promotion_calendar: ['campaign_name', 'sku', 'benefit_type', 'start_date', 'end_date', 'terms'],
  pricing_approval_sheet: ['quote_id', 'customer_name', 'sku', 'requested_price', 'approval_reason'],
  strategic_pricing_guideline: ['section', 'policy_name', 'rule', 'effective_start', 'owner'],
  quarterly_pricing_plan: ['quarter', 'category', 'target_margin_percent', 'pricing_action', 'owner'],
  strategic_targets: ['metric', 'category', 'target_value', 'period', 'owner'],
  market_reports: ['report_title', 'category', 'market_signal', 'impact', 'source'],
  user_role_config: ['email', 'name', 'role', 'account_status'],
  pricing_policy: ['policy_name', 'category', 'condition', 'rule', 'effective_start'],
  audit_log_archive: ['event_date', 'actor', 'action', 'entity_type', 'entity_id'],
  model_configuration: ['parameter', 'value', 'environment', 'notes'],
  rule_mapping_template: ['source_field', 'target_field', 'transform_rule', 'required'],
  campaign_memo: ['campaign_name', 'category', 'benefit_type', 'terms', 'effective_start'],
  trading_terms: ['customer_name', 'rebate_percent', 'payment_terms', 'freight_terms', 'effective_start'],
  rebate_agreement: ['customer_name', 'sku', 'rebate_percent', 'volume_threshold', 'effective_start'],
  contract_pricing: ['customer_name', 'sku', 'floor_price', 'ceiling_price', 'effective_start'],
  margin_target_sheet: ['category', 'channel', 'margin_floor_percent', 'target_margin_percent'],
};

const SAMPLE_ROW: Record<string, string> = {
  date: '2026-05-01',
  customer_name: 'Example Customer Sdn Bhd',
  sku: 'SKU-1001',
  quantity: '10',
  net_price: '593.50',
  channel: 'direct',
  name: 'Example Product',
  category: 'Building Materials',
  unit_cost: '420.00',
  list_price: '650.00',
  price: '650.00',
  effective_start: '2026-06-01',
  effective_end: '2026-12-31',
  competitor_name: 'Market Competitor',
  competitor_price: '620.00',
  observed_date: '2026-05-15',
  source: 'market_report',
  campaign_name: 'Q3 Contractor Growth',
  benefit_type: 'rebate',
  start_date: '2026-07-01',
  end_date: '2026-09-30',
  terms: 'Valid for approved accounts',
  quote_id: 'QUOTE-0001',
  requested_price: '590.00',
  approval_reason: 'Strategic account renewal',
  section: 'Discount Governance',
  policy_name: 'Channel Floor Price',
  rule: 'Require approval below floor margin',
  owner: 'Pricing Office',
  quarter: '2026-Q3',
  target_margin_percent: '18',
  pricing_action: 'Hold list price',
  metric: 'Gross Margin',
  target_value: '18%',
  period: '2026-Q3',
  report_title: 'Malaysia Construction Materials Watch',
  market_signal: 'Competitor discount pressure',
  impact: 'Medium',
  email: 'user@example.com',
  role: 'sales',
  account_status: 'active',
  condition: 'Direct channel',
  event_date: '2026-05-20',
  actor: 'pricing.manager@example.com',
  action: 'file_uploaded',
  entity_type: 'uploaded_file',
  entity_id: 'example-id',
  parameter: 'model_name',
  value: 'gpt-5.4-mini',
  environment: 'dev',
  notes: 'Example template row',
  source_field: 'sku',
  target_field: 'product_sku',
  transform_rule: 'trim_uppercase',
  required: 'true',
  rebate_percent: '3',
  payment_terms: '30 days',
  freight_terms: 'customer pickup',
  volume_threshold: '100',
  floor_price: '575.00',
  ceiling_price: '650.00',
  margin_floor_percent: '12',
};

function csvEscape(value: string) {
  if (/[",\r\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function downloadBlob(blob: Blob, fileName: string) {
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(href);
}

export function downloadCsv(fileName: string, headers: string[], rows: string[][]) {
  const csv = [headers, ...rows].map((row) => row.map(csvEscape).join(',')).join('\r\n');
  downloadBlob(new Blob([csv], { type: 'text/csv;charset=utf-8' }), fileName);
}

export function downloadJson(fileName: string, data: unknown) {
  const json = JSON.stringify(data, null, 2);
  downloadBlob(new Blob([json], { type: 'application/json;charset=utf-8' }), fileName);
}

export function downloadProductImportTemplate() {
  const headers = ['sku', 'name', 'category', 'unit_cost', 'list_price'];
  downloadCsv('product-import-template.csv', headers, [
    ['SKU-1001', 'Example Product', 'Building Materials', '420.00', '650.00'],
  ]);
}

export function downloadUploadTemplate(uploadType: string, label?: string) {
  const headers = UPLOAD_TEMPLATE_HEADERS[uploadType] ?? ['field_name', 'value', 'notes'];
  const row = headers.map((header) => SAMPLE_ROW[header] ?? '');
  const safeName = (label || uploadType).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  downloadCsv(`${safeName || 'upload'}-template.csv`, headers, [row]);
}
