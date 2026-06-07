# RevenueMind

RevenueMind is a portfolio-ready React demo for an AI pricing control tower. It shows quote recommendations, true margin simulation, approval governance, upload review, analytics, and admin controls without requiring a separate backend deployment.

## Deployment Mode

This repository is configured for Vercel as a single React web app:

- Vercel builds `frontend/`
- The output directory is `frontend/dist`
- Browser routes are handled by `vercel.json` rewrites
- The Python/FastAPI backend is retained in `backend/` only as original full-stack source and local reference
- The deployed demo uses a browser-side mock API in `frontend/src/lib/demoApi.ts`

No separate backend, database, Python runtime, or API server is required for the portfolio demo.

## Demo Accounts

Password login works with password:

```text
123456
```

Demo users:

- Admin: `admin@gmail.com`
- Sales Manager: `salesmanager@gmail.com`
- Sales Director Approver: `salesdirector@gmail.com`
- Executive Viewer: `executiveviewer@gmail.com`

## Working Demo Flows

The React demo keeps the main product workflows active:

- Sales dashboard and quote creation
- AI pricing recommendation
- Margin and leakage simulation
- Approval request and approval decision
- Upload Center with extraction review
- Admin rules, users, model runs, audit logs, and governance summary
- Executive analytics charts
- Product pricing lab

The browser-side demo API stores temporary changes in local storage, so created quotes, approval actions, uploaded demo files, and admin edits can survive a page refresh in the same browser.

## Run Locally

From the repository root:

```powershell
npm install --prefix frontend
npm run dev
```

Then open:

```text
http://localhost:5173
```

Build the Vercel-ready app:

```powershell
npm run build
```

Preview the production build:

```powershell
npm run preview
```

## Optional Real Backend Mode

The original FastAPI backend is still present for local full-stack experimentation. It is not used by the Vercel portfolio deployment.

To point the frontend back at a real API, set:

```text
VITE_USE_REAL_API=true
VITE_API_URL=http://localhost:8000/api
```

Then run the backend manually from `backend/` using the original Python setup.

## Vercel

The included `vercel.json` uses:

```json
{
  "installCommand": "npm install --prefix frontend",
  "buildCommand": "npm run build --prefix frontend",
  "outputDirectory": "frontend/dist"
}
```

Import this GitHub repository into Vercel and deploy it as-is.

## Repository Notes

- `frontend/` is the deployable React/Vite app
- `frontend/src/lib/demoApi.ts` replaces backend calls for the hosted demo
- `backend/` is kept for reference and local full-stack development
- `.vercelignore` excludes backend and large local/demo assets from Vercel upload
