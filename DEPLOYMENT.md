# Railway Deployment

## Current status (15 October 2026)

Railway reports the Frappe service deployment as active and successful. The two generated public domains currently return Railway's 404 "domain does not exist" page, so the Frappe login page is not verified and this is not yet a working public demo.

- https://angelic-nature-production-390e.up.railway.app
- https://angelic-nature-production-a044.up.railway.app

## Configuration

- Platform: Railway
- Application: Frappe HRMS (ERPNext/Frappe v16)
- Project/environment: angelic-nature / production
- Railway source repository: udayreddy5643/frappe_railway, branch main
- Root directory: /frappe
- Dockerfile: frappe/Dockerfile
- Application code repository: udayreddy5643/hrms, branch feat/cynaris-w2d5-uday-b (lesson work; this is not the repository currently connected to Railway)
- Public HTTP port: 8000

## Deployment setup

1. Connect the Railway service to the deployment repository and branch shown above.
2. Set the root directory to /frappe and build from frappe/Dockerfile.
3. Configure MariaDB and Redis services in the same Railway project.
4. Add the application variables below with Railway private service references. Keep secret values out of Git.
5. Deploy and wait for image build, database initialization, app installation, and startup checks.
6. In the app service's Settings > Networking, confirm a generated domain targets port 8000 and test it for the Frappe login page.

## Required environment variable names

- DB_HOST
- DB_PORT (defaults to 3306)
- DB_ROOT_PASSWORD
- REDIS_URL (authenticated Redis URL)
- ADMIN_PASSWORD
- SITE_NAME (defaults to frontend)
- FRAPPE_SITE_NAME_HEADER (defaults to SITE_NAME)
- FRAPPE_APPS

Use Railway-generated values for credentials and private hosts. Never put database, Redis, administrator, or AI provider secrets in Git.

## Known issue and next check

The latest Railway deployment is marked active, and its domains are configured for port 8000, but both domains return a Railway 404 before the Frappe app loads. Verify the generated domain assignment in Networking or regenerate the public domain, then retry. Until it displays the Frappe login page, deployment is not verified. Local Docker is separate from the Railway runtime.
