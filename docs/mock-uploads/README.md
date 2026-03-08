# Mock Upload Pack

This folder contains realistic sample files for the Chin Hin AI Pricing Strategist upload flows.

## Valid files

- `sales_history_q1_2026.csv` -> upload as `sales_history`
- `product_catalog_2026.xlsx` -> upload as `product_catalog`
- `current_price_list_channels.xlsx` -> upload as `current_price_list`
- `competitor_pricing_market_scan.csv` -> upload as `competitor_price_data`
- `promotion_calendar_2026.xlsx` -> upload as `promotion_calendar`
- `pricing_approval_sheet_q2.xlsx` -> upload as `pricing_approval_sheet`
- `strategic_pricing_guideline_2026.pdf` -> upload as `strategic_pricing_guideline`
- `quarterly_pricing_plan_q3.xlsx` -> upload as `quarterly_pricing_plan`
- `margin_target_sheet_2026.xlsx` -> upload as `margin_target_sheet`
- `strategic_targets_2026.csv` -> upload as `strategic_targets`
- `market_report_water_heaters_2026.pdf` -> upload as `market_reports`
- `pricing_policy_master_2026.pdf` -> upload as `pricing_policy`
- `campaign_memo_dc_pump_q3_2026.pdf` -> upload as `campaign_memo`
- `trading_terms_fy2026.pdf` -> upload as `trading_terms`
- `rebate_agreement_fy2026.csv` -> upload as `rebate_agreement`
- `contract_pricing_strategic_accounts.xlsx` -> upload as `contract_pricing`
- `model_configuration_control_tower.json` -> upload as `model_configuration`
- `rule_mapping_template.csv` -> upload as `rule_mapping_template`
- `user_role_config.csv` -> upload as `user_role_config`
- `audit_log_archive_sample.csv` -> upload as `audit_log_archive`

## Invalid files

- `current_price_list_invalid_headers.csv` -> test pricebook validation failure
- `campaign_memo_empty.txt` -> test empty-file handling
- `model_configuration_invalid.json` -> test invalid config parsing

## Suggested manual upload order

1. `product_catalog_2026.xlsx`
2. `current_price_list_channels.xlsx`
3. `competitor_pricing_market_scan.csv`
4. `promotion_calendar_2026.xlsx`
5. `pricing_policy_master_2026.pdf`
6. `campaign_memo_dc_pump_q3_2026.pdf`
7. `trading_terms_fy2026.pdf`
8. `rebate_agreement_fy2026.csv`
9. `contract_pricing_strategic_accounts.xlsx`
10. `strategic_targets_2026.csv`

These files are designed to help you see:

- upload governance
- extracted summaries
- policy ingestion
- campaign eligibility
- rebate and contract linkage
- market comparison with uploaded competitor data
- recommendation traceability after running quote recommendations
