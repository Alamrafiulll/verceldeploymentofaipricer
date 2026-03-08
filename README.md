# Chin Hin AI Pricing Strategist

Chin Hin AI Pricing Strategist is an enterprise pricing control tower for pricing decisions, approvals, document understanding, market comparison, and governance. It is designed for business users, not developers.

The system combines:
- AI pricing recommendation
- smart document understanding
- policy ingestion
- pricebook enforcement
- campaign eligibility
- rebate and contract logic
- true margin and leakage control
- market comparison and value positioning
- approval governance
- decision traceability

## What The System Does

The platform helps Chin Hin replace fragmented pricing work across Excel files, CSVs, PDFs, memos, approval sheets, rebate terms, campaign notices, and manual judgment.

Main outcomes:
- faster quote decisions
- more consistent pricing
- clearer true margin visibility
- lower leakage risk
- easier approval review
- document-to-rule traceability
- better competitor comparison

## How The System Works

### 1. Upload Business Files
Users upload business files through the Upload Center.

Supported formats:
- PDF
- CSV
- XLSX
- JSON
- TXT for testing fallback imports

The system:
- validates the user role and document type
- checks the file format
- extracts structured content
- creates a plain-language summary
- stores extracted entities and confidence
- keeps file traceability and review status

### 2. Convert Documents Into Usable Business Controls
Uploaded files can become:
- policy documents and clauses
- channel pricebooks
- campaign rules
- rebate programs
- contract pricing controls
- market comparison inputs
- model and governance configurations

### 3. Evaluate Quotes
When a quote is reviewed, the backend combines:
- quote data
- customer and product data
- active policy rules
- pricebooks
- campaigns
- rebate and incentive effects
- contract constraints
- finance logic
- uploaded competitor data

It then calculates:
- best price recommendation
- low and high pricing range
- recommendation confidence
- true margin
- leakage amount and reasons
- policy and contract warnings
- campaign impact
- market position

### 4. Support Governance
If the quote is risky, the system shows:
- why approval is needed
- policy source reference
- margin risk
- leakage control impact
- AI recommended action
- decision trail

## Roles And What They See

### Sales Manager
- create and update quotes
- get AI recommendation
- see true margin and leakage control summary
- review competitor comparison
- review campaign and rebate effects
- request approval when needed

### Sales Director Approver
- review pending approvals
- compare requested price vs AI recommendation
- review policy source references
- review true margin and leakage impact
- approve or reject with reason

### Executive Viewer
- review pricing health
- review approval performance
- review margin and leakage trends
- review competitor and category performance

### Admin Governance
- upload and review business files
- manage users and roles
- manage policies, campaigns, contracts, and pricebooks
- review extraction quality
- review AI traceability and model runs

## Login Accounts

All seeded demo users use password `123456`.

- Admin: `admin@gmail.com`
- Sales Manager: `salesmanager@gmail.com`
- Sales Director Approver: `salesdirector@gmail.com`
- Executive Viewer: `executiveviewer@gmail.com`

Important:
- only the admin account can create new users
- registration is not public

## Main Pages

- `/login`
- `/sales`
- `/sales/quotes/new`
- `/sales/quotes/:id`
- `/approvals`
- `/analytics`
- `/admin`
- `/upload-center`

## Run The System Locally Without Docker

This project is configured to run against native PostgreSQL on:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/pricing_db
```

### 1. Check PostgreSQL

```powershell
Test-NetConnection -ComputerName localhost -Port 5432
```

You want:

```text
TcpTestSucceeded : True
```

### 2. Run Migrations And Seed Data

```powershell
cd "backend"
& ".\.venv\Scripts\Activate.ps1"
python -m alembic upgrade head
python -m app.scripts.seed_data
```

### 3. Start The Backend

```powershell
cd "backend"
& ".\.venv\Scripts\Activate.ps1"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start The Frontend

Open a second terminal:

```powershell
cd "frontend"
npm install
npm run dev
```

### 5. Open The App

- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

## Quick Tests

### Database Test

```powershell
cd "backend"
& ".\.venv\Scripts\Activate.ps1"
python -c "from sqlalchemy import create_engine,text; from app.core.config import get_settings; e=create_engine(get_settings().database_url); c=e.connect(); print(c.execute(text('select 1')).scalar()); c.close()"
```

### Login Test

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"admin@gmail.com","password":"123456"}'
```

### Recommendation Test

```powershell
$sales = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"salesmanager@gmail.com","password":"123456"}'

$headers = @{ Authorization = "Bearer $($sales.access_token)" }
$quotes = Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/api/quotes?mine=true" `
  -Headers $headers

$quoteId = $quotes[0].id

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/quotes/$quoteId/recommend" `
  -Headers $headers
```

## Upload Mock Files

Mock files for testing the Upload Center are already prepared in:

- [docs/mock-uploads/valid](docs/mock-uploads/valid)
- [docs/mock-uploads/invalid](docs/mock-uploads/invalid)
- [docs/mock-uploads/README.md](docs/mock-uploads/README.md)

### Recommended Upload Order

Upload these first as `admin@gmail.com`:

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

These are designed to help you test:
- upload governance
- extracted summary and review flow
- pricebook enforcement
- policy ingestion
- campaign eligibility
- rebate and incentive logic
- contract pricing logic
- market comparison
- decision traceability

### Validation Failure Testing

Use these files to test rejection and validation handling:
- `current_price_list_invalid_headers.csv`
- `campaign_memo_empty.txt`
- `model_configuration_invalid.json`

## Suggested End-To-End Demo Flow

### Admin Flow
1. Login as `admin@gmail.com`
2. Open Upload Center
3. Upload the recommended mock files
4. Review extracted summaries and statuses
5. Open Admin to inspect governance and traceability

### Sales Flow
1. Login as `salesmanager@gmail.com`
2. Open Sales or Deal Workspace
3. Open a quote
4. Generate recommendation
5. Review true margin, leakage, campaign, contract, and market comparison outputs
6. Request approval if required

### Approver Flow
1. Login as `salesdirector@gmail.com`
2. Open Approvals
3. Compare requested price against AI recommendation
4. Review policy source reference and business impact
5. Approve or reject

### Executive Flow
1. Login as `executiveviewer@gmail.com`
2. Open Analytics
3. Review pricing health, leakage trends, approval performance, and strategic views

## Repo Structure

Key directories:
- `backend/` FastAPI app, models, services, schemas, migrations, tests
- `frontend/` React and TypeScript UI
- `docs/mock-uploads/` sample upload files
- `docs/screenshots/` screenshot target folder

## Core API Areas

- Auth: `/api/auth/*`
- Quotes: `/api/quotes/*`
- Approvals: `/api/approvals/*`
- Analytics: `/api/analytics/*`
- Admin: `/api/admin/*`
- Policies: `/api/policies/*`
- Pricebooks: `/api/pricebooks/*`
- Campaigns: `/api/campaigns/*`
- Uploads: `/api/uploads/*`
- Upload Center: `/api/upload-center/*`
- Market: `/api/market/*`
- Sandbox: `/api/sandbox/*`

## AI Behavior

The system uses configured Azure OpenAI / Foundry endpoints for recommendation and explanation workflows where available.

If the external service is unavailable:
- the system can use fallback logic for continuity
- governance, finance, policy, contract, campaign, and pricebook logic still run from stored business data

## Tests

Backend:

```powershell
cd "backend"
& ".\.venv\Scripts\Activate.ps1"
python -m pytest tests -q
```

Frontend:

```powershell
cd "frontend"
npm run build
```

## Git Setup And Push

Initialize and push the repository:

```powershell
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/Alamrafiulll/chinhin_group_cashmeifyoucan.git
git push -u origin main
```

If `origin` already exists:

```powershell
git remote set-url origin https://github.com/Alamrafiulll/chinhin_group_cashmeifyoucan.git
git branch -M main
git push -u origin main
```

## Notes

- `.env` files are ignored by git
- logs are ignored by git
- the local virtual environment is ignored by git
- use PostgreSQL, not SQLite, for local runtime
- competitor data is upload-driven; no live web scraping is required
