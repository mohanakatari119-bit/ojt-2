# Railway Deployment Guide

You will deploy two apps as separate Railway services inside one project:

| Service | What it is | Has DB? |
|---|---|---|
| **api-monitor** | The monitoring backend + dashboard frontend | Yes — PostgreSQL |
| **demo-app** | The TaskBoard app being monitored | No — in-memory |

> **Think of it like this:** api-monitor is the CCTV room. demo-app is the shop floor.
> The shop floor sends footage (request logs) to the CCTV room automatically.

---

## Before you start — one-time local setup

Run these from inside the `ojt_mohana/` folder on your machine.

### Step 1 — Create two GitHub repos

Go to github.com → New repository → create these two (both private or public, your choice):
- `api-monitor`
- `demo-app`

### Step 2 — Push api-monitor to GitHub

```bash
cd /Users/puneethadityamyakam/ojt_mohana/api-monitor
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/api-monitor.git
git push -u origin main
```

### Step 3 — Push demo-app to GitHub

```bash
cd /Users/puneethadityamyakam/ojt_mohana/demo-app
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/demo-app.git
git push -u origin main
```

---

## Part 1 — Deploy api-monitor on Railway

### Step 4 — Create a new Railway project

1. Go to https://railway.app and sign in (use GitHub login — easier)
2. Click **New Project**
3. Select **Empty Project**
4. Rename the project to `api-monitor-project` (click the name at the top)

### Step 5 — Add a PostgreSQL database

1. Inside the project, click the **+** button (Add a service)
2. Click **Database**
3. Click **Add PostgreSQL**
4. Wait about 30 seconds — Railway creates the database automatically
5. Click on the Postgres service card → go to **Variables** tab
6. You will see a variable called `DATABASE_URL` — copy its value somewhere safe (you'll need it in Step 8)

> The database URL looks like: `postgresql://postgres:xxxx@roundhouse.proxy.rlwy.net:xxxxx/railway`

### Step 6 — Add the api-monitor backend service

1. Click **+** again → **GitHub Repo**
2. If prompted, connect your GitHub account and grant access
3. Select the `api-monitor` repository
4. **Important:** Set **Root Directory** to `/` (leave it as the repo root — the Dockerfile is at the root level now)
5. Click **Deploy**

Railway will detect the `Dockerfile` at the root and build it.

### Step 7 — Wait for the first deploy to finish

The first build takes 2–3 minutes (downloading Python, installing packages).
You will see logs streaming — wait until you see:
```
Application started successfully
```

### Step 8 — Set environment variables for api-monitor

1. Click on the `api-monitor` service card
2. Go to the **Variables** tab
3. Click **New Variable** and add these one by one:

| Variable name | Value |
|---|---|
| `DATABASE_URL` | Paste the value you copied in Step 5 — but **change** `postgresql://` to `postgresql+asyncpg://` at the start |
| `DATABASE_SYNC_URL` | Same value but keep it as `postgresql://` (no change needed) |
| `SECRET_KEY` | Type any random string, e.g. `my-super-secret-key-2024` |
| `DEBUG` | `false` |
| `FRONTEND_DIR` | `/frontend` |

> **Why two DATABASE_URL values?** The async one (`+asyncpg`) is used by FastAPI for all requests. The sync one is needed by Alembic (migration tool). Railway gives you one URL — you use it both ways with different prefixes.

4. Click **Deploy** (or it may redeploy automatically)

### Step 9 — Get the api-monitor public URL

1. Click on the `api-monitor` service
2. Go to the **Settings** tab
3. Under **Networking**, click **Generate Domain**
4. Copy the URL — it looks like `https://api-monitor-production-xxxx.up.railway.app`

**Test it works:** Open `https://YOUR-URL/health` in your browser.
You should see: `{"status":"ok"}`

**View the dashboard:** Open `https://YOUR-URL/` — you should see the api-monitor frontend.

### Step 10 — Create a Service and API Key inside api-monitor

api-monitor needs a "Service" record before it can accept logs. Run these commands (replace YOUR-URL):

**Create the service:**
```bash
curl -X POST https://YOUR-URL/v1/services \
  -H "Content-Type: application/json" \
  -d '{"name":"demo-app","description":"TaskBoard demo app","base_url":"https://demo-app-url.railway.app"}'
```

You will get back a response like:
```json
{
  "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "name": "demo-app",
  ...
}
```

Copy the `id` value — this is your **service_id**.

**Create an API key for that service:**
```bash
curl -X POST https://YOUR-URL/v1/services/SERVICE_ID_HERE/keys \
  -H "Content-Type: application/json" \
  -d '{"name":"prod-key","service_id":"SERVICE_ID_HERE"}'
```

You will get back:
```json
{
  "raw_key": "mkey_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  ...
}
```

**Copy the `raw_key` value** — this is your API key. You will **never see it again** after this step.

---

## Part 2 — Deploy demo-app on Railway

### Step 11 — Update the API key in demo-app source

Open `demo-app/main.py` on your machine and replace the existing `API_KEY` line:

```python
API_KEY = "mkey_PASTE_THE_RAW_KEY_YOU_COPIED_HERE"
```

Then push the change:
```bash
cd /Users/puneethadityamyakam/ojt_mohana/demo-app
git add main.py
git commit -m "set production api key"
git push
```

### Step 12 — Add demo-app as a second service in Railway

1. In the **same Railway project**, click **+** → **GitHub Repo**
2. Select the `demo-app` repository
3. Root Directory: leave as `/`
4. Click **Deploy**

### Step 13 — Set environment variables for demo-app

1. Click on the `demo-app` service card
2. Go to **Variables** tab
3. Add this variable:

| Variable name | Value |
|---|---|
| `MONITOR_URL` | `https://YOUR-API-MONITOR-URL.up.railway.app` (from Step 9, no trailing slash) |

4. It will redeploy automatically.

### Step 14 — Get the demo-app public URL

1. Click on `demo-app` service → **Settings** → **Networking** → **Generate Domain**
2. Copy the URL — e.g. `https://demo-app-production-xxxx.up.railway.app`

**Test it works:** Open `https://YOUR-DEMO-URL/health` → `{"status":"ok"}`

**View the app:** Open `https://YOUR-DEMO-URL/` — you should see the TaskBoard frontend.

---

## Step 15 — Verify the connection end-to-end

1. Open the demo-app frontend: `https://YOUR-DEMO-URL/`
2. Create a user, a project, a task — do some actions
3. Open the api-monitor dashboard: `https://YOUR-API-MONITOR-URL/`
4. You should see logs appearing from demo-app's requests

If logs appear → everything is working correctly.

---

## Troubleshooting

### api-monitor shows no frontend (blank page or 404)
- Check that `FRONTEND_DIR` is set to `/frontend` in the api-monitor service variables
- Check the deploy logs for errors during startup

### demo-app not sending logs to api-monitor
- Check that `MONITOR_URL` in demo-app variables has **no trailing slash** and uses `https://`
- Check api-monitor deploy logs for `422 Unprocessable Entity` errors (means the API key is wrong)

### Database connection error
- Make sure `DATABASE_URL` starts with `postgresql+asyncpg://` (not just `postgresql://`)
- Railway's Postgres URL starts with `postgresql://` by default — you must change the prefix

### "Invalid or inactive API key" errors
- The `raw_key` you copied in Step 10 must match exactly what's in `demo-app/main.py`
- If you lost it, create a new key (Step 10 again) and update `main.py` again

---

## Final URLs summary

| What | URL |
|---|---|
| api-monitor API | `https://YOUR-API-MONITOR-URL/v1/` |
| api-monitor dashboard | `https://YOUR-API-MONITOR-URL/` |
| api-monitor API docs | `https://YOUR-API-MONITOR-URL/docs` |
| demo-app frontend | `https://YOUR-DEMO-URL/` |
| demo-app API docs | `https://YOUR-DEMO-URL/docs` |
