# RevenueMind Demo

This project was made for the Chin Hin hackathon.

This repository is only a demo of the original project.

## Frontend

The frontend uses Next.js for the deployable app shell and static export, while the existing React screens continue to run as a client-side pricing workspace.

```bash
cd frontend
npm install
npm run dev
npm run build
```

Public frontend environment variables use Next.js names:

- `NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000/api`
- `NEXT_PUBLIC_USE_REAL_API` defaults to `false`
- `NEXT_PUBLIC_AUTH_BYPASS` defaults to `true`

## UI Screenshots

![Login screen](docs/screenshots/01-login.png)

![Sales dashboard](docs/screenshots/02-sales-dashboard.png)

![Quote workspace](docs/screenshots/03-quote-workspace.png)

![Admin governance](docs/screenshots/04-admin-governance.png)

![Analytics dashboard](docs/screenshots/05-analytics.png)

## Actor Screenshots

### Sales Manager

![Sales Manager actor screen](docs/screenshots/06-actor-sales-manager.png)

### Sales Director Approver

![Sales Director Approver actor screen](docs/screenshots/07-actor-sales-director-approver.png)

### Executive Viewer

![Executive Viewer actor screen](docs/screenshots/08-actor-executive-viewer.png)

### Admin Governance

![Admin Governance actor screen](docs/screenshots/09-actor-admin-governance.png)
