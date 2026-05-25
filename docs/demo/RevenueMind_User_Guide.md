# RevenueMind User Guide

## Purpose

RevenueMind helps business users make faster, safer, and more explainable pricing decisions. It combines uploaded business documents, AI recommendations, finance logic, approval governance, and decision traceability in one platform.

## Who Uses The System

### Sales Manager
- builds quotes
- reviews AI recommendations
- checks true margin and leakage control
- reviews campaign, contract, and competitor context
- requests approval if required

### Sales Director Approver
- reviews pending approvals
- compares requested price vs AI recommendation
- checks policy source references
- checks business impact before approving or rejecting

### Executive Viewer
- tracks pricing health
- monitors leakage and margin trends
- reviews approval speed and pricing compliance

### Admin Governance
- uploads and governs business files
- manages users and roles
- reviews extracted rules
- manages policy, campaign, contract, and rebate controls
- reviews AI traceability and model activity

## Login Details

All demo users use password `123456`.

- Admin: `admin@gmail.com`
- Sales Manager: `salesmanager@gmail.com`
- Sales Director Approver: `salesdirector@gmail.com`
- Executive Viewer: `executiveviewer@gmail.com`

Important:
- only the admin account can create new users

## Main Areas

- Login: `/login`
- Sales: `/sales`
- Approvals: `/approvals`
- Analytics: `/analytics`
- Admin: `/admin`
- Upload Center: `/upload-center`

## How The Platform Works

### 1. Upload Business Files
Business files are uploaded through the Upload Center.

Examples:
- price lists
- policy PDFs
- campaign memos
- trading terms
- rebate agreements
- contract pricing sheets
- competitor pricing files
- strategic target sheets

### 2. Extract And Structure Information
The system:
- detects the document category
- validates whether the role can upload it
- extracts useful business data
- creates a summary
- stores confidence and review status

### 3. Activate Business Rules
Once reviewed, uploaded data becomes usable pricing logic such as:
- policy clauses
- active pricebooks
- campaign rules
- rebate programs
- contract pricing controls

### 4. Generate Recommendations
When a quote is evaluated, the system combines:
- quote details
- finance logic
- policy rules
- pricebooks
- campaigns
- rebates
- contracts
- competitor data

The output includes:
- recommended price
- confidence
- true margin
- leakage amount and reasons
- market comparison
- next best action

### 5. Route For Approval If Needed
If a quote is risky or out of policy, it is routed to the approver with:
- requested price
- AI recommendation
- policy source reference
- business impact
- approval trail

## First-Time Setup

### Start The Backend

```powershell
cd "backend"
& ".\.venv\Scripts\Activate.ps1"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start The Frontend

```powershell
cd "frontend"
npm run dev
```

### Open The App

- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

## Demo Upload Pack

Use the ready-made upload pack here:

- [docs/demo-upload-pack](c:/Users/rafiu/OneDrive/Desktop/github%20upload/Chin%20hin/ai%20pricing/docs/demo-upload-pack)
- [docs/demo-upload-pack/README.md](c:/Users/rafiu/OneDrive/Desktop/github%20upload/Chin%20hin/ai%20pricing/docs/demo-upload-pack/README.md)
- [docs/demo-upload-pack/upload-checklist.csv](c:/Users/rafiu/OneDrive/Desktop/github%20upload/Chin%20hin/ai%20pricing/docs/demo-upload-pack/upload-checklist.csv)

## Recommended Upload Order

1. Product Catalog
2. Current Price List
3. Competitor Pricing
4. Promotion Calendar
5. Pricing Policy
6. Campaign Memo
7. Trading Terms
8. Rebate Agreement
9. Contract Pricing Document
10. Strategic Targets

## What To Show In A Demo

### Sales Manager
Show:
- quote creation or quote opening
- AI recommendation
- true margin
- pricebook enforcement
- campaign eligibility
- competitor comparison
- next best action

### Approver
Show:
- pending approval
- requested vs recommended price
- policy source reference
- margin and leakage impact
- approval action

### Executive
Show:
- pricing health
- margin and leakage trends
- approval turnaround
- competitor position

### Admin
Show:
- upload review
- user management
- policy and contract governance
- AI recommendation trace viewer
- model run observability

## Troubleshooting

### Upload Rejected
Check:
- correct document category
- allowed file format
- correct actor role
- file is not empty

### Backend Not Starting
Check:
- PostgreSQL is running on port `5432`
- migrations have been applied
- backend `.venv` is activated

### Login Fails
Check:
- email is typed exactly
- password is `123456`
- backend is running

## Summary

RevenueMind helps users upload business documents, convert them into pricing controls, generate explainable recommendations, control leakage, govern approvals, and maintain full business traceability.
