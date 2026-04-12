# Solar Suitability FastAPI → Google Cloud Run demo deployment

This plan assumes:
- FastAPI app object is `api.main:app`
- Cloud Run serves both `/score` and `/score_plot`
- PostgreSQL is hosted in Cloud SQL
- PostGIS is enabled in the Cloud SQL database
- Your processed files stay in the repo and are loaded once into Cloud SQL

## 1) Recommended architecture

Use **one Cloud Run service** for the API and **one Cloud SQL for PostgreSQL instance** for data.

Why this is the best fit for a class demo:
- Cloud Run is simple, fully managed, and scales to zero.
- Cloud SQL gives managed PostgreSQL and supports **PostGIS**.
- Your dataset is tiny (~37 KB), so a one-time load is fast and low risk.
- Keeping plotting inside the same service means `/score` and `/score_plot` stay together.

Recommended components:
- **Cloud Run service:** `solar-suitability-api`
- **Cloud SQL Postgres instance:** `solar-db`
- **Database name:** `solar_db`
- **Database user:** `solar_app`
- **Region:** keep Cloud Run and Cloud SQL in the **same region**
- **Artifact Registry repository:** store the built Docker image there

## 2) App/database connection pattern

For Cloud Run → Cloud SQL, use the built-in Cloud SQL connection and connect over the Unix socket path:

`/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME`

The Cloud SQL docs show Cloud Run can attach a Cloud SQL instance using `--add-cloudsql-instances`, and applications can connect by using that mounted Unix socket path. Cloud SQL also supports the PostGIS extension for PostgreSQL. citeturn799566view0turn874477view1turn874477view0

## 3) Cloud Run startup command

Use this container command:

```bash
uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

Cloud Run starts the image entrypoint by default, but you can also override it with the service `command` and `args` settings if needed. citeturn799566view2

## 4) Environment variables

Set these on the Cloud Run service:

```bash
APP_ENV=production
MPLBACKEND=Agg
DB_USER=solar_app
DB_PASS=YOUR_DB_PASSWORD
DB_NAME=solar_db
DB_HOST=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
DB_PORT=5432
INSTANCE_CONNECTION_NAME=PROJECT_ID:REGION:INSTANCE_NAME
DATABASE_URL=postgresql+psycopg2://solar_app:YOUR_DB_PASSWORD@/solar_db?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

### Notes
- `MPLBACKEND=Agg` is important for server-side plotting on Cloud Run.
- If your app already uses discrete `DB_*` values, keep those.
- If your app already uses `DATABASE_URL`, prefer that and derive the rest only if needed.

## 5) Managed Postgres + PostGIS setup

### Create the Cloud SQL instance
Example:

```bash
gcloud sql instances create solar-db \
  --database-version=POSTGRES_16 \
  --cpu=1 \
  --memory=3840MiB \
  --region=us-central1
```

### Create database and user

```bash
gcloud sql databases create solar_db --instance=solar-db

gcloud sql users create solar_app \
  --instance=solar-db \
  --password='YOUR_DB_PASSWORD'
```

### Enable PostGIS in the database
Connect once with `gcloud sql connect` and run:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Cloud SQL supports PostGIS on all major PostgreSQL versions it offers for Cloud SQL PostgreSQL. citeturn874477view0

## 6) Database initialization sequence

For a demo, do **not** make Cloud Run initialize the database on startup.
Do it once, ahead of time.

### Recommended one-time load flow
1. Create the Cloud SQL instance.
2. Create the database and user.
3. Enable PostGIS with `CREATE EXTENSION postgis;`
4. Run `schema.sql` against `solar_db`.
5. Run `database/load_tiles.py`.
6. Run `database/load_boundary.py`.
7. Verify expected rows exist.
8. Then deploy Cloud Run.

### Simplest way to initialize for a demo
Run the schema and loaders from **your local machine** against Cloud SQL before the demo.

Use the Cloud SQL Auth Proxy or `gcloud sql connect` for SQL initialization, then run the Python loaders with environment variables pointed at the Cloud SQL instance.

#### Option A: schema through `gcloud sql connect`

```bash
gcloud sql connect solar-db --user=postgres --database=solar_db
```

Then inside psql:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
\i schema.sql
```

#### Option B: loaders from your local machine
Set env vars locally to the Cloud SQL target and then run:

```bash
python database/load_tiles.py
python database/load_boundary.py
```

### Alternate option for repeatability
Create a **Cloud Run Job** using the same image and a command that runs an init script once. Cloud Run jobs are intended for one-off tasks that run and exit, which makes them a better fit than your web service for initialization. citeturn799566view4

## 7) Plotting dependencies on Cloud Run

For `/score_plot`, the important change is to make plotting headless:

```python
import matplotlib
matplotlib.use("Agg")
```

or rely on:

```bash
MPLBACKEND=Agg
```

### Recommended requirements check
Make sure `requirements.txt` includes what `/score_plot` actually imports.
Typical examples:

```txt
fastapi
uvicorn[standard]
psycopg2-binary
sqlalchemy
pandas
geopandas
shapely
pyproj
matplotlib
```

### Important deployment note
If `/score_plot` currently depends on `geopandas`, `fiona`, `pyproj`, or GDAL-backed packages, the Docker image needs geospatial system libraries. The included Dockerfile installs the common Debian packages used for that.

### Demo-safe recommendation
If you have time before the demo, simplify plotting so `/score_plot` uses only:
- SQL query result
- `matplotlib`
- maybe `shapely`

That reduces build complexity and startup risk.

## 8) Cloud Run service deployment

### Build image

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT_ID/solar-repo/solar-suitability:demo
```

### Deploy service

```bash
gcloud run deploy solar-suitability-api \
  --image us-central1-docker.pkg.dev/PROJECT_ID/solar-repo/solar-suitability:demo \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars APP_ENV=production,MPLBACKEND=Agg,DB_USER=solar_app,DB_PASS=YOUR_DB_PASSWORD,DB_NAME=solar_db,DB_HOST=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME,DB_PORT=5432,INSTANCE_CONNECTION_NAME=PROJECT_ID:REGION:INSTANCE_NAME \
  --add-cloudsql-instances PROJECT_ID:REGION:INSTANCE_NAME
```

The Cloud Run docs show `--add-cloudsql-instances` as the standard way to attach the Cloud SQL instance to the service. citeturn799566view0

## 9) Recommended deployment sequence for your class demo

This is the lowest-risk order:

### A. Prepare cloud infrastructure
1. Create Google Cloud project.
2. Enable Cloud Run, Cloud Build, Artifact Registry, and Cloud SQL Admin APIs.
3. Create Artifact Registry repo.
4. Create Cloud SQL Postgres instance.
5. Create DB + app user.
6. Enable PostGIS.

### B. Initialize data before deploying app
7. Run `schema.sql`.
8. Run `load_tiles.py`.
9. Run `load_boundary.py`.
10. Test with a SQL query that tables and geometries are present.

### C. Deploy app
11. Build Docker image.
12. Deploy Cloud Run service with env vars and Cloud SQL attachment.
13. Test `/docs`, `/score`, and `/score_plot`.

### D. Freeze the demo environment
14. Avoid changing schema after this point.
15. Keep one tested image tag for the demo.
16. Save sample URLs and inputs you know work.

## 10) Small app changes I recommend before deploy

### A. Read Cloud SQL socket host
Make sure your DB connection code can accept:
- `DB_HOST=/cloudsql/...`
- `DB_PORT=5432`

### B. Do not auto-run loaders in the web container
The API container should only serve requests.

### C. Fail clearly if plotting dependencies are missing
Log a useful error if `/score_plot` cannot import a dependency.

### D. Add lightweight health checks
A simple root route like `/health` returning `{ "ok": true }` helps verify the deployment quickly.

## 11) Best recommendation for this project

For **this** app and **this** demo, I recommend:
- Cloud Run service for the API
- Cloud SQL PostgreSQL with PostGIS
- one-time manual database initialization before deploy
- one stable image tag for demo day
- headless matplotlib (`Agg`)
- keep the tiny data files in the repo

That is the cleanest, most teachable deployment story and the least likely to break under demo conditions.

## 12) One thing to verify in your code before using the Dockerfile

Confirm your FastAPI app import path is really:

```python
api.main:app
```

If not, change the `CMD` line in the Dockerfile to the correct module path.
