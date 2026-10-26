# Contently AI Content Platform - Backend (PostgreSQL)

Production-grade, asynchronous backend built from scratch for the **Contently AI Content Creation & Distribution Platform**, powered by **PostgreSQL**, **Python 3.13**, and **FastAPI**.

---

## 1. Database: PostgreSQL Configuration

The backend is configured to use your local PostgreSQL installation (`postgresql-x64-18` on port `5432`). It connects via `psycopg2-binary` and SQLAlchemy connection pooling.

### Security & Safety Rules
- **No hardcoded secrets:** Credentials must be set only in `backend/.env`. Real passwords are never committed to Git.
- **Data safety:** Never drop, reset, or overwrite existing databases or data. The `contently_db` database is isolated.
- **Frontend remains read-only:** The frontend is treated strictly as read-only.

---

## 2. Step-by-Step Setup Guide

### Step 1: Verify PostgreSQL Service Status
PostgreSQL 18 is installed at `C:\Program Files\PostgreSQL\18`.

Check if the Windows service is running:
```powershell
Get-Service postgresql-x64-18
```
If it is stopped, start it:
```powershell
Start-Service postgresql-x64-18
```
Verify the server is accepting connections:
```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_isready.exe" -h localhost -p 5432
```
Expected output: `:5432 - accepting connections`.

---

### Step 2: Create the `contently_db` Database
Create a dedicated database for Contently. This preserves all existing databases:

**Option A: Using PostgreSQL CLI (`createdb.exe`)**
```powershell
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U postgres -h localhost -p 5432 contently_db
```
*(Enter your PostgreSQL password when prompted).*

**Option B: Using `psql.exe`**
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -p 5432 -c "CREATE DATABASE contently_db;"
```

**Option C: Using pgAdmin GUI**
1. Open pgAdmin.
2. Connect to your local PostgreSQL server.
3. Right-click **Databases** → **Create** → **Database...**
4. Name the database `contently_db` and click **Save**.

---

### Step 3: Configure Environment Variables
Copy the template file to create your local `.env`:
```powershell
copy backend\.env.example backend\.env
```

Open `backend/.env` and update `DATABASE_URL` with your local PostgreSQL password:
```ini
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD_HERE@localhost:5432/contently_db
```
*(Alternatively, you can provide granular variables: `POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=YOUR_PASSWORD_HERE`, `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5432`, `POSTGRES_DB=contently_db`)*.

---

### Step 4: Apply Versioned Database Migrations
Run Alembic to create all application tables (`users`, `workspaces`, `content_items`, `generation_history`, `templates`, `brand_kits`, `scheduled_posts`, `seo_analyses`) in `contently_db`:
```powershell
python -m alembic -c backend/alembic.ini upgrade head
```

---

### Step 5: Start the Backend Server
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
On startup:
- Database schema tables are verified.
- The default demo user (`demo@contently.local` / `ContentlyDemo123!`) and initial framework templates are automatically seeded.
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **Health Check**: `http://127.0.0.1:8000/health`

---

### Step 6: Start the Frontend Prototype
In a separate terminal:
```powershell
node server.js
```
Open `http://localhost:3000` in your browser.

---

## 3. Troubleshooting PostgreSQL

| Issue | Cause | Action |
|---|---|---|
| `connection refused` or `pg_isready` fails | PostgreSQL service is not running | Run `Start-Service postgresql-x64-18` in PowerShell as Administrator. |
| `fe_sendauth: no password supplied` | Password missing in `backend/.env` | Set your password in `backend/.env`: `DATABASE_URL=postgresql://postgres:<password>@localhost:5432/contently_db`. |
| `database "contently_db" does not exist` | Database has not been created yet | Run `& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U postgres contently_db`. |
| `password authentication failed for user "postgres"` | Incorrect password | Use the password specified during PostgreSQL installation, or reset it via pgAdmin. |

---

## 4. Environment Variables Reference

| Variable | Description | Default / Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:<password>@localhost:5432/contently_db` |
| `POSTGRES_USER` | (Optional) Granular username | `postgres` |
| `POSTGRES_PASSWORD` | (Optional) Granular password | `<your_password>` |
| `POSTGRES_HOST` | (Optional) Host | `localhost` |
| `POSTGRES_PORT` | (Optional) Port | `5432` |
| `POSTGRES_DB` | (Optional) Database name | `contently_db` |
| `JWT_SECRET_KEY` | Secret key for signing session tokens | `32+ characters` |
| `OPENAI_API_KEY` | OpenAI API Key (for real AI Studio synthesis) | [platform.openai.com](https://platform.openai.com/api-keys) |
| `GEMINI_API_KEY` | Google Gemini API Key | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:3000,http://127.0.0.1:3000` |

---

## 5. Verification Test Suite

All 46 automated tests can be run at any time:
```powershell
python -m pytest backend/tests -v
```
The test suite validates:
1. Authentication, sessions, password hashing.
2. Multi-tenant user and workspace isolation (User A cannot access User B's content).
3. Drafts and content library CRUD, filtering, searching, and bulk actions.
4. Dashboard metric aggregations and recent content list.
5. Actionable HTTP 503 errors on missing AI credentials (no fake generation output).
6. Templates catalog, Content Planner scheduling, Brand Kit calibration, and SEO analysis math.
7. **Razorpay Billing & Subscriptions**:
   - Plan catalog integrity ($49/mo Pro Creator, $468/yr Pro Creator Annual).
   - Server-side amount computation (zero client trust).
   - Unauthenticated checkout prevention (HTTP 401).
   - Actionable HTTP 503 on unconfigured Razorpay credentials.
   - Razorpay Checkout session creation (Orders and Subscriptions).
   - Cryptographic signature validation for payments.
   - Tampered signature rejection (HTTP 400).
   - Raw request HMAC SHA256 Webhook signature verification.
   - Idempotent webhook handling (duplicate events processed safely without duplicate charges/records).
   - Authoritative subscription state updates (`active`, `pending`, `past_due`, `cancelled`).
   - Subscription cancellation lifecycle.
   - Protection of paid backend features against unsubscribed users (HTTP 402).

---

## 6. Razorpay Subscriptions & Payments Setup Guide

### 1. Account & Subscription Plans Setup

1. **Sign Up / Log In**:
   - Visit [dashboard.razorpay.com](https://dashboard.razorpay.com/) and create or sign in to your merchant account.
2. **Switch to Test Mode**:
   - Toggle the environment switch in the top header from **Live Mode** to **Test Mode**.
3. **Generate API Keys**:
   - Navigate to **Settings** → **API Keys** → click **Generate Key**.
   - Copy `Key Id` (`rzp_test_...`) and `Key Secret`.
   - Store them immediately in `backend/.env`.
4. **Create Subscription Plans (For Recurring Subscriptions)**:
   - Navigate to **Subscriptions** → **Plans** → click **Create Plan**.
   - **Monthly Plan**:
     - Plan Name: `Pro Creator Tier (Monthly)`
     - Billing Frequency: `Monthly` (Interval: `1`)
     - Amount: `USD 49.00` (or `INR 3,999.00` if your Razorpay account is domestic INR)
     - Copy the generated `Plan ID` (e.g. `plan_ABC1234567890`) into `RAZORPAY_PLAN_PRO_MONTHLY` in `backend/.env`.
   - **Yearly Plan**:
     - Plan Name: `Pro Creator Tier (Yearly)`
     - Billing Frequency: `Yearly` (Interval: `1`)
     - Amount: `USD 468.00` (or `INR 38,390.00` for 20% annual discount)
     - Copy the generated `Plan ID` into `RAZORPAY_PLAN_PRO_YEARLY` in `backend/.env`.
   *(Note: If you do not configure recurring Plan IDs, the backend will automatically generate seamless Checkout Orders for the plan amount as a fallback).*

---

### 2. Required Environment Variables

Add or verify the following variables in `backend/.env`:

```ini
# ==============================================================================
# Razorpay Subscriptions & Payments Configuration
# ==============================================================================
RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID_HERE
RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET_HERE
RAZORPAY_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET_HERE

# Currency ('INR' or 'USD' - defaults to INR to display Indian Rupee ₹3,999/mo)
RAZORPAY_CURRENCY=INR

# Optional: Razorpay recurring Plan IDs from Subscriptions dashboard
RAZORPAY_PLAN_PRO_MONTHLY=plan_pro_monthly_id_here
RAZORPAY_PLAN_PRO_YEARLY=plan_pro_yearly_id_here

# App URL for redirects and webhooks
PUBLIC_APP_URL=http://localhost:3000
```

---

### 3. Webhook Configuration

Razorpay webhooks are the **authoritative** trigger for activating, renewing, cancelling, or halting subscriptions.

1. Navigate to **Settings** → **Webhooks** → click **Add New Webhook**.
2. **Webhook URL**:
   - For local development with tunnel (e.g., ngrok/cloudflared):
     `https://<your-tunnel-subdomain>.ngrok-free.app/api/billing/webhook`
   - For staging/production:
     `https://api.yourdomain.com/api/billing/webhook`
3. **Secret**:
   - Enter a strong secret string (e.g., generated with `python -c "import secrets; print(secrets.token_hex(24))"`).
   - Enter the exact same secret in `backend/.env` under `RAZORPAY_WEBHOOK_SECRET`.
4. **Active Events to Enable**:
   Check the following events in the Razorpay Webhooks dashboard:
   - `subscription.authenticated`
   - `subscription.activated`
   - `subscription.charged`
   - `subscription.pending`
   - `subscription.halted`
   - `subscription.cancelled`
   - `subscription.resumed`
   - `payment.captured`
   - `payment.failed`
   - `order.paid`

---

### 4. How to Test the Flow, Apply Migrations & Switch to Live Credentials

#### Step A: Apply Database Migrations
Run the versioned Alembic migration to ensure the `subscriptions`, `payments`, and `webhook_events` tables exist in your database:
```powershell
python -m alembic -c backend/alembic.ini upgrade head
```

#### Step B: Test with Razorpay Test Cards
1. Start the backend:
   ```powershell
   python -m uvicorn backend.app.main:app --port 8000 --reload
   ```
2. Start the frontend:
   ```powershell
   node server.js
   ```
3. Open `http://localhost:3000/profile-settings` (or sign in with `demo@contently.local` / `ContentlyDemo123!`).
4. Click **Manage Subscription & Seats** in Section 04.
5. In the Razorpay Checkout popup, use Razorpay test card credentials:
   - **Card Number**: `4111 1111 1111 1111` (or any valid Razorpay test card from Razorpay docs)
   - **Expiry**: Any future date (e.g., `12/30`)
   - **CVV**: `123`
   - **OTP**: `123456` or click **Success** in test mode emulator.
6. The client callback submits the payment ID and signature to `/api/billing/verify-payment`, and the server validates the signature and authorizes the tier.
7. To simulate recurring charges or status transitions, send test webhook events from **Razorpay Dashboard** → **Webhooks** → **Test Webhook**.

#### Step C: Switching to Live Credentials
When ready for production:
1. Complete Razorpay KYC and Merchant Onboarding on the Razorpay Dashboard.
2. Switch dashboard toggle to **Live Mode**.
3. Generate Live API Keys (**Settings** → **API Keys**).
4. Update production environment variables:
   - Replace `RAZORPAY_KEY_ID` (`rzp_live_...`)
   - Replace `RAZORPAY_KEY_SECRET`
   - Update `RAZORPAY_WEBHOOK_SECRET` for the production webhook URL.
   - Create matching live subscription plans and paste their live IDs into `RAZORPAY_PLAN_PRO_MONTHLY` and `RAZORPAY_PLAN_PRO_YEARLY`.
5. Restart the backend process.

---

### 5. Features Requiring Razorpay Account Approval Before Going Live

| Feature | Test Mode Status | Live Mode Requirements |
|---|---|---|
| **Subscriptions API (Recurring Auto-debit)** | Available immediately in Test Mode | Requires **Subscriptions / Mandates Activation** approval on your Razorpay merchant profile. E-mandate / recurring compliance requires RBI e-mandate registration or card network recurring consent. |
| **International Currency (USD $49/mo)** | Simulated in Test Mode | Requires **International Payments** approval in Razorpay Dashboard (**Settings** → **Payment Methods** → **International Cards**). If international payments are not yet enabled, you can set `RAZORPAY_CURRENCY=INR` (₹3,999/mo). |
| **UPI AutoPay / eNACH** | Available in Test Mode | Requires Razorpay merchant approval and business registration documents. |
| **Live Webhooks** | Test simulation available | Requires a publicly reachable HTTPS endpoint with a valid SSL/TLS certificate. |
