# Demo Upload Pack

This folder is the easiest way to test the full Chin Hin AI Pricing Strategist upload flow.

Use it with the Upload Center in the app:
- Login: `admin@gmail.com`
- Password: `123456`
- Open: `http://localhost:5173/upload-center`

## Folder Guide

### `01-sales-manager`
Use these first if you want to see sales-side inputs and quote support.

- `sales_history_q1_2026.csv` -> choose `Sales History`
- `product_catalog_2026.xlsx` -> choose `Product Catalog`
- `current_price_list_channels.xlsx` -> choose `Current Price List`
- `competitor_pricing_market_scan.csv` -> choose `Competitor Pricing`
- `promotion_calendar_2026.xlsx` -> choose `Promotion Calendar`

What this shows:
- product and pricing inputs
- competitor comparison inputs
- promotion and sales history inputs

### `02-approver`
Use these to test approval governance and strategic plan uploads.

- `pricing_approval_sheet_q2.xlsx` -> choose `Pricing Approval Sheet`
- `strategic_pricing_guideline_2026.pdf` -> choose `Strategic Pricing Guideline`
- `quarterly_pricing_plan_q3.xlsx` -> choose `Quarterly Pricing Plan`
- `margin_target_sheet_2026.xlsx` -> choose `Margin Target Sheet`

What this shows:
- approval-related document ingestion
- strategic pricing reference uploads
- margin planning inputs

### `03-executive-viewer`
Use these to test executive and strategic visibility documents.

- `strategic_targets_2026.csv` -> choose `Strategic Targets`
- `market_report_water_heaters_2026.pdf` -> choose `Market Reports`

What this shows:
- strategic target uploads
- market context uploads

### `04-admin-governance`
Use these to test governance, policies, contracts, rebates, and traceability.

- `pricing_policy_master_2026.pdf` -> choose `Pricing Policy`
- `campaign_memo_dc_pump_q3_2026.pdf` -> choose `Campaign Memo`
- `trading_terms_fy2026.pdf` -> choose `Trading Terms`
- `rebate_agreement_fy2026.csv` -> choose `Rebate Agreement`
- `contract_pricing_strategic_accounts.xlsx` -> choose `Contract Pricing Document`
- `model_configuration_control_tower.json` -> choose `Model Configuration`
- `rule_mapping_template.csv` -> choose `Rule Mapping Template`
- `user_role_config.csv` -> choose `User Role Config`
- `audit_log_archive_sample.csv` -> choose `Audit Log Archive`

What this shows:
- policy ingestion
- campaign eligibility setup
- rebate and incentive setup
- contract pricing setup
- admin governance and configuration uploads

### `05-invalid-tests`
Use these to confirm the validation and review flow is working.

- `current_price_list_invalid_headers.csv` -> choose `Current Price List`
- `campaign_memo_empty.txt` -> choose `Campaign Memo`
- `model_configuration_invalid.json` -> choose `Model Configuration`

What this shows:
- invalid headers
- empty file handling
- invalid JSON validation

## Best Upload Order To See The Most

Upload these in this exact order:

1. `01-sales-manager/product_catalog_2026.xlsx` as `Product Catalog`
2. `01-sales-manager/current_price_list_channels.xlsx` as `Current Price List`
3. `01-sales-manager/competitor_pricing_market_scan.csv` as `Competitor Pricing`
4. `01-sales-manager/promotion_calendar_2026.xlsx` as `Promotion Calendar`
5. `04-admin-governance/pricing_policy_master_2026.pdf` as `Pricing Policy`
6. `04-admin-governance/campaign_memo_dc_pump_q3_2026.pdf` as `Campaign Memo`
7. `04-admin-governance/trading_terms_fy2026.pdf` as `Trading Terms`
8. `04-admin-governance/rebate_agreement_fy2026.csv` as `Rebate Agreement`
9. `04-admin-governance/contract_pricing_strategic_accounts.xlsx` as `Contract Pricing Document`
10. `03-executive-viewer/strategic_targets_2026.csv` as `Strategic Targets`
11. `01-sales-manager/sales_history_q1_2026.csv` as `Sales History`
12. `02-approver/pricing_approval_sheet_q2.xlsx` as `Pricing Approval Sheet`

## After Uploading

After the files are uploaded:

1. Login as `salesmanager@gmail.com`
2. Open a quote in Sales / Deal Workspace
3. Generate an AI recommendation
4. Review:
   - true margin
   - leakage control
   - campaign eligibility
   - pricebook enforcement
   - contract pricing summary
   - market comparison
5. Login as `salesdirector@gmail.com` and review approvals
6. Login as `executiveviewer@gmail.com` and open analytics
7. Login as `admin@gmail.com` and inspect upload statuses, policies, and AI traceability

## Quick Rule

If you are unsure which category to pick in the UI, use the exact category text written next to the file above.
