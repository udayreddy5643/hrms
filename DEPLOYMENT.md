# Railway Deployment

## Platform and URL

- Platform: Railway
- Application: Frappe HRMS (ERPNext/Frappe v16)
- Deployment URL: https://angelic-nature-production-390e.up.railway.app
- Railway service: angelic-nature, production environment
- Source: this repository's feat/cynaris-w2d5-uday-b branch, built with the Railway Docker setup in udayreddy5643/frappe_railway.

## Deployment setup

1. Create a Railway project and connect the GitHub repository.
2. Set the service root to frappe so Railway uses frappe/Dockerfile.
3. Configure a MariaDB service and a Redis service in the same Railway project.
4. Add the application service variables listed below, using Railway private service hostnames and references for database and Redis credentials. Do not commit secret values.
5. Deploy the service and wait for the image build, database initialization, app installation, and health check to complete.
6. Open the generated Railway domain and confirm the Frappe login page loads.

## Required environment variable names

- DB_HOST
- DB_PORT (defaults to 3306)
- DB_ROOT_PASSWORD
- REDIS_URL (authenticated Redis URL)
- ADMIN_PASSWORD
- SITE_NAME (defaults to frontend)
- FRAPPE_SITE_NAME_HEADER (defaults to SITE_NAME)
- FRAPPE_APPS (the build configuration selects the HRMS feature branch)

Use Railway-generated values for credentials and private hosts. Never put database, Redis, administrator, or AI provider secrets in Git.

## Known issues and verification

- The first deploy can take several minutes while assets are built and the site is initialized.
- The startup script must parse an authenticated REDIS_URL before passing its host to wait-for-it; the startup dependency check was fixed to remove URL credentials from that host argument while preserving the complete URL in Frappe Redis configuration.
- The first deployment attempt returned 502 while Redis readiness checking failed. A new build containing the startup fix is in progress; verify that Railway marks it active and that the generated URL shows the login page before treating the deployment as complete.
- Local Docker setup is separate and is not required for Railway runtime.
