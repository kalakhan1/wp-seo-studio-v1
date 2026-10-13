# WordPress WooCommerce SEO Control Studio

A professional, production-oriented application for managing WordPress, WooCommerce, and Rank Math SEO from a single UI — without repeatedly opening the WordPress dashboard.

Built with **Python (FastAPI)** backend and **React + TypeScript** frontend, with a local SQLite database and an optional WordPress companion plugin.

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [Feature Overview](#2-feature-overview)
3. [Technology Stack & Versions](#3-technology-stack--versions)
4. [Directory Structure](#4-directory-structure)
5. [Prerequisites](#5-prerequisites)
6. [Installation — From GitHub Clone](#6-installation--from-github-clone)
7. [Installation — Manual (Without Git)](#7-installation--manual-without-git)
8. [Environment Variables Setup](#8-environment-variables-setup)
9. [Running the Application](#9-running-the-application)
10. [First-Time Setup in the App](#10-first-time-setup-in-the-app)
11. [Every Page — Detailed Overview](#11-every-page--detailed-overview)
12. [WordPress Companion Plugin Setup](#12-wordpress-companion-plugin-setup)
13. [AI Prompts — How to Use with Examples](#13-ai-prompts--how-to-use-with-examples)
14. [GitHub Push Setup (for Your Own Project)](#14-github-push-setup-for-your-own-project)
15. [Running the Tests](#15-running-the-tests)
16. [Troubleshooting — Common Errors & Fixes](#16-troubleshooting--common-errors--fixes)
17. [Security Notes](#17-security-notes)
18. [Known Limitations](#18-known-limitations)
19. [FAQ](#19-faq)

---

## 1. What This Project Does

This is a **single control panel** for a WordPress + WooCommerce store. Instead of logging into WordPress admin every time, you use one app to:

- Connect to any WordPress site (via REST API + Application Password)
- Discover what the site actually supports (truthfully, no guessing)
- Configure WooCommerce store settings (address, currency, taxes, checkout)
- Enable and configure Cash on Delivery (COD)
- Configure shipping zones and methods
- Publish blog posts, pages, and WooCommerce products with SEO metadata
- Upload and manage media
- Configure Rank Math SEO (global settings + per-content meta)
- Get AI-generated content suggestions (optional)
- Manage internal links
- Run a technical SEO audit
- View publishing history, queue, and backups

**It works with a fresh WordPress site.** It does not require pre-existing content, products, or metadata.

---

## 2. Feature Overview

| Feature | What It Does | Status |
|---|---|---|
| **Website Connection** | Connect to WordPress via Application Password; verify & discover capabilities | ✅ |
| **Capability Discovery** | Truthful report on what the site supports (read/write, plugin requirements) | ✅ |
| **Store Setup Wizard** | Aggregated readiness dashboard across settings, COD, shipping | ✅ |
| **WooCommerce Settings** | Edit all WC settings groups (General, Products, Tax, Checkout, etc.) | ✅ |
| **Cash on Delivery** | Enable/disable COD, edit title, description, instructions | ✅ |
| **Shipping Zones** | Create zones, assign locations, add methods (flat rate, free, pickup) | ✅ |
| **Product Publisher** | Publish simple WooCommerce products with images, pricing, SEO | ✅ |
| **Blog Publisher** | Publish blog posts with categories, tags, excerpt, SEO | ✅ |
| **Page Publisher** | Publish WordPress pages with parent/child structure | ✅ |
| **Media Studio** | Upload, browse, edit, and delete media | ✅ |
| **Image Presets** | Design a balanced archive grid; discover registered WP sizes | ✅ |
| **Rank Math SEO** | Global settings + per-content meta (via companion plugin) | ✅ |
| **Internal Linking** | Search content, suggest related items, check anchor text | ✅ |
| **AI Prompt Studio** | Editable prompts + optional AI generation (mock/OpenAI) | ✅ |
| **Technical SEO Audit** | 10 truthful checks with severity and evidence | ✅ |
| **Publishing Queue** | View, cancel, retry queued jobs | ✅ |
| **History & Logs** | Audit trail of every publish operation | ✅ |
| **Backup & Restore** | Export/import app config (no secrets) | ✅ |

---

## 3. Technology Stack & Versions

### Backend

| Tool | Version | Purpose |
|---|---|---|
| Python | **3.11+** (tested on 3.13) | Runtime |
| FastAPI | 0.115.0 | Web framework |
| Uvicorn | 0.32.0 | ASGI server |
| Pydantic | 2.9.2 | Data validation |
| SQLAlchemy | 2.0.36 | ORM (async) |
| aiosqlite | 0.20.0 | Async SQLite driver |
| Alembic | 1.13.3 | Migrations |
| httpx | 0.27.2 | HTTP client |
| structlog | 24.4.0 | Structured logging |
| keyring | 25.5.0 | OS credential store |
| greenlet | 3.1.1 | Required by SQLAlchemy async |
| pytest | 8.3.3 | Testing |
| ruff / black / mypy | latest | Linting / formatting / typing |

### Frontend

| Tool | Version | Purpose |
|---|---|---|
| Node.js | **18+** (tested on 20) | Runtime |
| npm | **9+** | Package manager |
| React | 18.3.1 | UI library |
| TypeScript | 5.6.3 | Type safety |
| Vite | 5.4.9 | Build tool |
| Tailwind CSS | 3.4.14 | Styling |
| React Router | 6.26.2 | Routing |
| Zustand | 5.0.0 | State management |
| lucide-react | 0.452.0 | Icons |
| sonner | 1.5.0 | Toasts |

### External Services (Optional)

| Service | Required? | Notes |
|---|---|---|
| WordPress 6.0+ | Yes (for real mode) | Target site |
| WooCommerce 7.0+ | For WC features | Must be installed |
| Rank Math 1.0.80+ | For SEO features | Free version supported |
| WP SEO Control Companion Plugin | For Rank Math fields | Ships with this project |
| OpenAI API | Optional | Only if using real AI |

**Compatible combos tested:**
- Python 3.11, 3.12, 3.13 ✅
- Node 18, 20 ✅
- WordPress 6.0 – 6.6 ✅
- WooCommerce 7.0 – 9.0 ✅
- Rank Math Free 1.0.80+ ✅

---

## 4. Directory Structure

```
wp-seo-studio/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/routes/           # 18 route modules
│   │   ├── config/                  # settings, logging, constants
│   │   ├── core/                    # HTTP client, security, health
│   │   ├── db/                      # SQLAlchemy, migrations
│   │   ├── integrations/            # WordPress, WooCommerce, Rank Math, AI
│   │   ├── models/                  # SQLAlchemy models
│   │   ├── schemas/                 # Pydantic schemas
│   │   ├── security/                # SSRF guard, secrets, sanitizers
│   │   ├── services/                # Business logic (15 services)
│   │   ├── utils/                   # JSON, idempotency helpers
│   │   └── main.py                  # FastAPI app factory
│   ├── migrations/                  # Alembic
│   ├── tests/                       # 326 tests
│   ├── scripts/                     # run_dev.ps1, run_dev.sh
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml
│
├── frontend/                         # React + TypeScript
│   ├── src/
│   │   ├── components/              # Reusable UI
│   │   ├── features/                # 23 feature pages
│   │   ├── hooks/                   # Custom hooks
│   │   ├── layout/                  # Sidebar, TopNav
│   │   ├── router/                  # Route definitions
│   │   ├── services/                # API clients
│   │   ├── store/                   # Zustand
│   │   ├── types/                   # TS types
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── wordpress-plugin/                 # Companion plugin
│   └── wp-seo-control-companion/
│       ├── wp-seo-control-companion.php
│       ├── includes/
│       └── readme.txt
│
├── docs/                             # Extra documentation
├── .env.example
├── .gitignore
├── README.md
└── start.bat / start.sh
```

---

## 5. Prerequisites

Before installing, ensure you have:

### Required

- **Python 3.11 or newer** → [python.org/downloads](https://www.python.org/downloads/)
  - Windows: check "Add Python to PATH" during install
  - Verify: `python --version`
- **Node.js 18 or newer** → [nodejs.org](https://nodejs.org/)
  - Verify: `node --version` and `npm --version`
- **Git** → [git-scm.com](https://git-scm.com/)
  - Verify: `git --version`

### Optional

- **VS Code** → [code.visualstudio.com](https://code.visualstudio.com/)
  - Recommended extensions: Python, Pylance, ESLint, Tailwind CSS IntelliSense
- **uv** (fast Python package installer) → [astral.sh/uv](https://astral.sh/uv)
- **Postman** or **curl** for API testing

### For Real WordPress Testing

- A WordPress site with **HTTPS enabled**
- WordPress admin account
- **Application Passwords** feature enabled (default in WP 5.6+)
- (Optional) WooCommerce installed and configured
- (Optional) Rank Math SEO installed

---

## 6. Installation — From GitHub Clone

This is the fastest path. Assumes you have Git and want to clone the repo.

### Step 6.1 — Clone the Repository

Open PowerShell (Windows) or Terminal (macOS/Linux):

```powershell
cd C:\Users\YourName\Desktop
git clone https://github.com/YOUR_USERNAME/wp-seo-studio.git
cd wp-seo-studio
```

**Replace `YOUR_USERNAME` with the actual GitHub username.**

### Step 6.2 — Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**If you get "execution policy" error:**
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Install dependencies:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**Faster alternative (if you have `uv`):**
```powershell
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

Initialize the database:
```powershell
alembic upgrade head
```

### Step 6.3 — Frontend Setup

Open a **new terminal**:

```powershell
cd C:\Users\YourName\Desktop\wp-seo-studio\frontend
npm install
```

### Step 6.4 — Environment File

```powershell
cd C:\Users\YourName\Desktop\wp-seo-studio
copy .env.example .env
```

Edit `.env` if needed (defaults work for local development).

### Step 6.5 — Run

Follow [Section 9](#9-running-the-application).

---

## 7. Installation — Manual (Without Git)

If you received the project as a ZIP file:

### Step 7.1 — Extract

Unzip to `C:\Users\YourName\Desktop\wp-seo-studio\`.

### Step 7.2 — Same as Section 6.2 and 6.3

Skip the `git clone` step. Start from `cd backend`.

### Step 7.3 — Create `.env`

```powershell
copy .env.example .env
```

---

## 8. Environment Variables Setup

Open `.env` in VS Code:

```powershell
code .env
```

### Full `.env` Reference

```ini
# ============================================================
# APP
# ============================================================
# Environment: development | staging | production
APP_ENV=development

# Debug mode (verbose errors)
APP_DEBUG=true

# Runtime mode: mock | real
# mock → no external calls; safe for local development
# real → calls the configured WordPress site
# NOTE: production forces real regardless of this value
APP_MODE=mock

# Host & port for backend
APP_HOST=127.0.0.1
APP_PORT=8000

# Logging
LOG_LEVEL=info
LOG_FORMAT=human

# ============================================================
# DATABASE
# ============================================================
# SQLite (default, single-user)
DB_URL=sqlite+aiosqlite:///./data/app.db

# PostgreSQL (advanced, multi-user)
# DB_URL=postgresql+asyncpg://user:pass@localhost/wpscontrol

# ============================================================
# WORDPRESS (Phase 2+)
# ============================================================
# Leave blank if using mock mode.
# Real credentials are entered via the app's Connection page and
# stored in the OS keyring — NOT here.
WP_BASE_URL=
WP_USERNAME=
WP_APP_PASSWORD=

# ============================================================
# WOOCOMMERCE (Phase 2+)
# ============================================================
# Same as above — entered via the app, not here.
WOO_CONSUMER_KEY=
WOO_CONSUMER_SECRET=

# ============================================================
# AI (OPTIONAL)
# ============================================================
# none → mock provider (deterministic test data)
# openai → real OpenAI calls (requires AI_API_KEY)
# mock → force mock provider
AI_PROVIDER=none
AI_API_KEY=
# Leave empty to use default model (gpt-4o-mini)
AI_MODEL=

# ============================================================
# IMAGE SEARCH (OPTIONAL)
# ============================================================
IMAGE_SEARCH_PROVIDER=none
IMAGE_SEARCH_API_KEY=

# ============================================================
# HTTP
# ============================================================
HTTP_TIMEOUT=30
HTTP_MAX_RETRIES=3
```

**Important:** `.env` contains secrets. It's in `.gitignore` and will never be committed.

---

## 9. Running the Application

You need **two terminals** — one for backend, one for frontend.

### Terminal 1 — Backend

```powershell
cd C:\Users\YourName\Desktop\wp-seo-studio\backend
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Application startup complete.
```

Keep this terminal open.

### Terminal 2 — Frontend

Open a **new PowerShell window**:

```powershell
cd C:\Users\YourName\Desktop\wp-seo-studio\frontend
npm run dev
```

**Expected output:**
```
  VITE v5.4.9  ready in ~1s
  ➜  Local:   http://127.0.0.1:5173/
```

Keep this terminal open.

### Open the App

Open in browser:

```
http://127.0.0.1:5173
```

You should see the **Dashboard** — health status + 10 phases (all green).

### Stopping the App

Press `Ctrl + C` in each terminal.

### Restarting Later

Run the same commands again. No state is reset.

---

## 10. First-Time Setup in the App

When you first open the app:

### Step 1 — Check Health

Dashboard should show:

```
Mode: mock
Database: reachable ✓
Settings: loaded ✓
```

### Step 2 — Add a WordPress Connection

1. Sidebar → **Website Connection**
2. Click **New Connection**
3. Fill fields (see example below)
4. Click **Test Connection**
5. If success → **Save Connection**
6. (Optional) Click **Discover Capabilities**

### Example — Connecting to a Real Site

**Prerequisites on WordPress:**
- Site is HTTPS (required for Application Passwords)
- You are logged in as admin

**Get Application Password:**
1. WordPress admin → Users → Profile
2. Scroll to **Application Passwords**
3. Name: `WP SEO Control Studio` → **Add New Application Password**
4. WordPress shows `xxxx xxxx xxxx xxxx xxxx xxxx` — **copy it now** (won't be shown again)

**Get WooCommerce REST Keys (if WC installed):**
1. WooCommerce → Settings → Advanced → REST API
2. **Add key** → Description: `WP SEO Control Studio`, User: your admin, Permissions: **Read/Write**
3. Click **Generate API Key**
4. Copy the `ck_...` (consumer key) and `cs_...` (consumer secret)

**Fill the Connection Form:**

| Field | Value |
|---|---|
| Label | `Production Store` |
| Base URL | `https://your-site.com` (no trailing slash) |
| Username | your WP admin username |
| Application Password | the 24-character string with spaces |
| Require HTTPS | ✓ checked |
| WC consumer key | `ck_...` (optional) |
| WC consumer secret | `cs_...` (optional) |

Click **Test Connection**. If successful → **Save Connection**.

**Security:** Your password is stored in the OS keyring (Windows Credential Manager / macOS Keychain / Linux Secret Service). Never in the database.

---

## 11. Every Page — Detailed Overview

### 11.1 Dashboard (`/dashboard`)

**Purpose:** Overall health + phase completion.

**What it shows:**
- Backend health status (database, settings, mode)
- Overall status: `ok` / `degraded` / `failed`
- Version, active mode, components count
- 10 implementation phases with completion badges

**When to use:** First thing on app start. Confirms everything is running.

---

### 11.2 App Settings (`/app-settings`)

**Purpose:** Runtime non-secret settings.

**What you can do:**
- Change log level (`debug`, `info`, `warning`, `error`, `critical`)
- View read-only values: environment, mode, log format, providers, timeouts

**Example:** If you want detailed logs during troubleshooting → set `debug`, click Save, watch backend terminal.

**What you cannot do here:** Change `APP_MODE`, provider names, or credentials. Those are in `.env` only.

---

### 11.3 Website Connection (`/connection`)

**Purpose:** Manage WordPress connections.

**Actions per connection:**
- **Verify** — re-tests credentials
- **Discover Capabilities** — probes what the site supports
- **Delete** — removes metadata + keyring secrets

**Capability report shows:**
- Site name, URL, timezone
- Current user, roles, capabilities
- Post types (post, page, product)
- Taxonomies (category, tag, product_cat)
- Each capability with status:
  - `Supported` — works with current credentials
  - `Read-only` — read works, write doesn't
  - `Requires elevated permission` — needs higher role
  - `Requires plugin` — companion plugin needed
  - `Requires manual setup` — WP admin action needed
  - `Not verified` — probe failed
  - `Unsupported` — endpoint missing

**Example:** If your user is a `Contributor`:
- `wp.write.posts` → `Requires elevated permission`
- Reason: "Missing required capabilities: publish_posts"

---

### 11.4 Setup Wizard (`/site-setup`)

**Purpose:** Store readiness dashboard.

**5 cards, each with a status:**
1. **Store Profile** — address, currency, units, taxes
2. **Payment Methods** — COD enabled?
3. **Shipping Zones** — zones configured?
4. **Products** — reminder to publish
5. **Other Gateways** — read-only

**Example flow:**
- Card 1 shows `[missing]` → click **Open Store Settings** → fill in the address
- Rerun wizard → Card 1 shows `[ok]`

---

### 11.5 WordPress Settings / WooCommerce Settings (`/wordpress-settings`, `/woocommerce`)

**Purpose:** Edit WooCommerce settings per group.

**Groups (tabs):**
- **General** — address, currency, location, position
- **Products** — weight unit, dimension unit, reviews
- **Tax** — enable tax, prices include tax, tax basis
- **Checkout** — guest checkout, coupons, account creation
- **Shipping** — default locations
- **Accounts & Privacy** — registration options
- **Advanced** — misc

**How it works:**
1. Fields load from the connected site
2. Edit any field → the tab shows "N unsaved change(s)"
3. Click **Save changes** → each dirty field is written individually

**Example:** Change currency from USD to PKR:
1. Go to **General** tab
2. Find `woocommerce_currency` field
3. Change to `PKR`
4. Click Save changes
5. Toast: "Saved 1 setting(s)."

**Why one-by-one?** Because WooCommerce's REST API only supports per-setting writes. If one fails, others still succeed — the toast summarizes the outcome.

---

### 11.6 Cash on Delivery (`/cod`)

**Purpose:** Enable and configure COD payment gateway.

**What you see:**
- **Status card:** available? enabled? shipping zones? virtual products?
- **Warnings** (if any): missing COD, no shipping zones, empty title

**Editable fields:**
- **Enable COD** (checkbox)
- **Title** — shown at checkout
- **Description** — shown under the title
- **Instructions** — shown on thank-you page and email
- **Allow for virtual products** (checkbox)

**Example workflow:**
1. Enable COD
2. Title: `Cash on Delivery`
3. Description: `Pay with cash upon delivery.`
4. Instructions: `Please have exact change ready.`
5. Click **Save COD settings**

**Verification:** Open your WordPress store → add a product → checkout → COD should appear as an option.

**Warning if no shipping zones:** Customers can't reach COD without a shipping method. Configure shipping zones first.

---

### 11.7 Shipping Zones (`/shipping`)

**Purpose:** Define where you ship and how.

**Structure:**
- **Zones** (e.g. "Pakistan", "Rest of the World")
  - **Locations** (countries, states, postcodes)
  - **Methods** (flat rate, free shipping, local pickup)

**Actions:**
- **New zone** — create zone with name + locations
- **Expand a zone** → view locations + methods
- **Add method** — pick type, set cost or minimum amount
- **Edit method** — change title, cost, enabled state
- **Delete zone** — permanently removes

**Example: Setup Pakistan shipping**
1. Click **New zone**
2. Name: `Pakistan`
3. Add location: type=`country`, code=`PK`
4. Click **Create zone**
5. Expand the zone → **Add method**
6. Method: `flat_rate`, Title: `Standard Shipping`, Cost: `200`
7. Click **Add method**
8. Repeat with `free_shipping`, Minimum: `2000`

**Method types:**
- **flat_rate** — fixed cost per order
- **free_shipping** — free, optionally above a minimum
- **local_pickup** — customer picks up

---

### 11.8 Product Publisher (`/product-publisher`)

**Purpose:** Publish WooCommerce products.

**Sections:**
- **Basic** — name, slug, SKU, status, featured, catalog visibility, descriptions
- **Pricing** — regular/sale price, dates, tax status/class
- **Inventory** — manage stock, quantity, status, backorders, low-stock threshold, sold individually
- **Shipping** — weight, dimensions, shipping class
- **Media** — featured image (pick from Media Studio)
- **Organization** — categories, tags
- **Related** — upsells, cross-sells (comma-separated IDs)
- **Advanced** — reviews allowed, purchase note, menu order
- **Rank Math SEO** — title, meta description, focus keyword, canonical, robots

**Example: Create "Herbal Hair Oil"**

| Field | Value |
|---|---|
| Product name | Herbal Hair Oil |
| Slug | herbal-hair-oil |
| SKU | HHO-001 |
| Short description | Daily care hair oil. |
| Full description | `<p>Natural herbal hair oil for daily care.</p>` |
| Regular price | 499.00 |
| Sale price | 399.00 |
| Manage stock | ✓ |
| Stock quantity | 100 |
| Weight | 0.5 |
| Featured image | (pick from library) |
| Categories | Hair Care |
| Tags | herbal, natural |
| SEO title | Herbal Hair Oil for Daily Care |
| Meta description | Natural herbal hair oil for daily care. |
| Focus keyword | herbal hair oil |

Click **Save Draft** first → verify on WordPress → then **Publish**.

---

### 11.9 Blog Publisher (`/blog-publisher`)

**Purpose:** Publish WordPress posts.

**Sections:**
- **Basic** — title, slug, excerpt, content (HTML allowed), status
- **Organization** — categories, tags
- **Advanced** — featured image, comment/ping status
- **Rank Math SEO**

**Special:** Supports **scheduled publishing** — set status to `Schedule`, provide ISO date.

**Example: Blog post**
```
Title: Badam Benefits Guide
Slug: badam-benefits-guide
Excerpt: A practical guide to badam.
Content: <p>Badam is a nutrient-dense nut.</p>
Categories: Health, Nutrition
Tags: badam, wellness
SEO title: Badam Benefits Guide — Practical Tips
Meta description: Learn about badam benefits with practical daily-care tips.
Focus keyword: badam benefits
```

Click **Save Draft** or **Publish**.

---

### 11.10 Page Publisher (`/page-publisher`)

**Purpose:** Publish WordPress pages (About Us, Contact, Privacy, etc.).

**Same as Blog Publisher** but:
- No categories/tags
- Has **Parent page ID** and **Menu order** (for hierarchical pages)

**Example:**
```
Title: About Us
Slug: about-us
Content: <p>We sell herbal products.</p>
Parent page ID: (leave empty for top-level)
Menu order: 1
```

---

### 11.11 Media Studio (`/media-studio`)

**Purpose:** Upload and manage media.

**Actions:**
- **Upload media** — drag-drop or file picker → fill title, alt text, caption, description
- **Search by filename**
- **Click a card** → side panel with edit + delete

**Example: Upload product image**
1. Click **Upload media**
2. Drop `herbal-hair-oil.jpg`
3. Title: `Herbal Hair Oil`
4. Alt text: `Bottle of herbal hair oil on a wooden table`
5. Caption: `Our best-selling hair oil.`
6. Click **Upload to WordPress**
7. Toast: "Uploaded herbal-hair-oil.jpg"

**Supported formats:** JPEG, PNG, WebP, GIF (max 10 MB).

**Magic-byte check:** Files are checked by content, not extension. A `.jpg` labeled "image/png" is treated as JPEG.

**Dedup:** Uploading the same bytes twice reuses the existing WP media ID.

---

### 11.12 Image Presets (`/image-presets`)

**Purpose:** Design a balanced archive grid.

**Sections:**
1. **CSS display presets** — 5 curated options (square cover, square contain, portrait, landscape, rounded)
2. **Fine controls** — aspect ratio, object-fit, object-position, border radius, background
3. **Archive grid preview** — desktop/tablet/mobile views
4. **Suggested presets** — 6 curated dimensions for common uses
5. **Registered WP sizes** — Discover button lists WordPress-registered sizes

**Example workflow:**
1. Click **Square, cover** preset
2. Preview shows 8 sample product cards in a grid
3. Switch to **Mobile** to check responsive
4. Click **Copy CSS** to get ready-to-paste CSS

**Important:** Presets only affect CSS. They do not modify WordPress image files or regenerate thumbnails.

---

### 11.13 Rank Math SEO (`/rankmath`)

**Purpose:** Global Rank Math settings.

**Requires:** Companion plugin installed + activated + Rank Math active.

**Sections:**
- **Titles & Meta** — separator, homepage SEO title, homepage meta description
- **Sitemap** — enable, include products/posts/pages
- **Indexing** — no-index search, author archives, date archives, empty categories
- **Breadcrumbs** — enable, on products
- **WooCommerce** — remove product category base

**Example:** No-index search results:
1. Toggle **No-index search results** to ON
2. Click **Save changes**
3. Toast: "Updated 1 setting(s)."

**Read-only mode:** If companion plugin missing → fields are disabled with a warning explaining why.

---

### 11.14 Internal Linking Studio (`/internal-linking`)

**Purpose:** Prepare internal links before publishing.

**Sections:**
1. **Your content** — title + optional excerpt (used for suggestions)
2. **Suggestions** — based on title/content/category similarity
3. **Search existing content** — by keyword
4. **Your links** — list with anchor text, type, label, context note

**Link types:**
- `contextual` — inline within content
- `related_product` / `related_article` — related section
- `category` / `brand`
- `footer_related` — bottom-of-page related block

**Example:**
1. Title: "Badam Benefits Guide"
2. Click **Suggest related content**
3. Suggested: "Health Benefits of Nuts" (score 0.42, shared category)
4. Click **Add** → link appears in the list
5. Edit anchor text if needed

**Validation:**
- URLs checked against connected site's host
- Anchor text checked for over-optimization (repeated exact matches)

---

### 11.15 AI Prompt Studio (`/ai-prompt-studio`)

**Purpose:** Manage AI prompts and optionally generate content.

See [Section 13](#13-ai-prompts--how-to-use-with-examples) for detailed usage.

**Provider status card:**
- Shows current provider (`mock`, `openai`, `none`)
- Shows model name
- Shows reason if unavailable

---

### 11.16 Technical SEO Audit (`/seo-audit`)

**Purpose:** Run truthful technical checks.

**10 checks:**
1. HTTPS enabled
2. Site URL / Home URL consistent
3. XML sitemap reachable
4. robots.txt reachable
5. Permalinks readable
6. Rank Math integration available
7. Media alt text coverage
8. Published content inventory
9. Taxonomy structure (empty categories)
10. (Extra checks may be added)

**Severity levels:**
- **Fail** — critical, breaks SEO
- **Warn** — recommended fix
- **Info** — informational
- **Pass** — all good

**Each finding shows:**
- Check ID, label, category
- Message
- Evidence (JSON)
- Suggested fix
- **Action path** → link to the relevant page (e.g. `/rankmath`)

**Example finding:**
```
[Warn] No sitemap found
No sitemap was found at the standard locations.
Suggested fix: Enable the XML sitemap in Rank Math.
[Open] → /rankmath
```

**History:** Every audit is saved locally. Recent audits table shows past runs.

---

### 11.17 Publishing Queue (`/queue`)

**Purpose:** View and control queued jobs.

**Summary chips:** Pending, Running, Success, Failed, Partial, Cancelled.

**Table columns:** Job ID, Type, Status, Progress, Error, Created, Actions.

**Actions:**
- **Cancel** — pending/retrying jobs
- **Retry** — failed/partial/cancelled jobs

**Note:** Background execution is not part of this phase. Jobs are recorded but not auto-executed.

---

### 11.18 History and Logs (`/history`)

**Purpose:** Audit trail of publish operations.

**Summary chips:** Total, Success, Failed, Partial.

**Table columns:** When, Object type, Operation, Status, WP ID, Message.

**Example entries:**
```
2026-10-13 14:22   product   create   success   501   —
2026-10-13 14:25   post      create   partial   202   Companion plugin missing
2026-10-13 14:28   product   update   success   501   —
```

**Filter by status** to focus on failures.

---

### 11.19 Backup and Restore (`/backup`)

**Purpose:** Export/import app configuration.

**Warning box:**
> This is NOT a WordPress backup. It does not include posts, pages, products, media, or site settings. Secrets are never exported.

**What's included:**
- Connection metadata (labels, URLs, usernames — NOT passwords)
- Prompt templates
- Non-secret app settings

**Export:** Click **Export backup** → downloads JSON file with timestamp.

**Import:**
1. Paste JSON into textarea
2. Optionally uncheck "Include X" to skip a category
3. Click **Preview (dry run)** → see counts + warnings
4. If preview looks good, click **Apply import**
5. Review the report

**After import:** You must re-add credentials to any connection. The import never restores secrets.

---

### 11.20 Coming Soon / Future

Phase 11+ (not yet implemented):
- Background queue worker (job execution)
- Idempotency keys
- Search Console integration
- Product variations
- Bulk operations
- Theme CSS injection
- Image optimization (WebP)
- Multi-user authentication
- PostgreSQL support
- Docker deployment

---

## 12. WordPress Companion Plugin Setup

The companion plugin is required for:
- Reading/writing Rank Math per-post meta
- Reading/writing Rank Math global settings

Without it, Rank Math fields are unavailable — the app tells you this truthfully.

### 12.1 — Create the Plugin ZIP

WordPress admin only accepts `.zip` files for plugin installation. You must
package the plugin folder into a ZIP before uploading.

**Prerequisite:** The plugin folder exists at:
```
C:\Users\YourName\Desktop\wp-seo-studio\wordpress-plugin\wp-seo-control-companion\
```

#### Method A — PowerShell (Recommended)

Open PowerShell and run:

```powershell
cd C:\Users\YourName\Desktop\wp-seo-studio\wordpress-plugin
Compress-Archive -Path "wp-seo-control-companion" -DestinationPath "wp-seo-control-companion.zip" -Force
```

Verify the ZIP was created:
```powershell
Get-ChildItem | Select-Object Name, Length
```

Expected output:
```
wp-seo-control-companion          (folder)
wp-seo-control-companion.zip      ~9000 bytes
```

Verify the ZIP's internal structure is correct:
```powershell
Expand-Archive -Path "wp-seo-control-companion.zip" -DestinationPath "_test" -Force
Get-ChildItem "_test" -Recurse | Select-Object FullName
Remove-Item "_test" -Recurse -Force
```

Expected (single top-level folder):
```
_test\wp-seo-control-companion\wp-seo-control-companion.php
_test\wp-seo-control-companion\uninstall.php
_test\wp-seo-control-companion\readme.txt
_test\wp-seo-control-companion\includes\class-plugin.php
_test\wp-seo-control-companion\includes\class-rest-controller.php
_test\wp-seo-control-companion\includes\class-rankmath-bridge.php
_test\wp-seo-control-companion\includes\class-rankmath-settings.php
_test\wp-seo-control-companion\includes\class-sanitizer.php
```

If you see extra nesting like `_test\wp-seo-control-companion\wp-seo-control-companion\...`,
the ZIP is wrong. Re-create it by right-clicking the **folder** (not the files
inside it).

#### Method B — Windows Explorer (Right-Click)

1. Open File Explorer
2. Navigate to `C:\Users\YourName\Desktop\wp-seo-studio\wordpress-plugin`
3. **Right-click on the `wp-seo-control-companion` folder** (not the files inside it)
4. Choose **Send to → Compressed (zipped) folder**
5. Windows creates `wp-seo-control-companion.zip` in the same folder

#### Method C — 7-Zip or WinRAR

1. Right-click the `wp-seo-control-companion` folder
2. **7-Zip → Add to "wp-seo-control-companion.zip"**
3. This produces the cleanest ZIP (no Windows metadata)

#### Method D — macOS / Linux

macOS Terminal:
```bash
cd /path/to/wordpress-plugin
zip -r wp-seo-control-companion.zip wp-seo-control-companion -x "*.DS_Store"
```

Linux Terminal:
```bash
cd /path/to/wordpress-plugin
zip -r wp-seo-control-companion.zip wp-seo-control-companion
```

### 12.2 — Upload to WordPress

1. Log in to WordPress admin
2. Go to **Plugins → Add New**
3. Click **Upload Plugin** (top of the page)
4. Click **Choose File** → select `wp-seo-control-companion.zip`
5. Click **Install Now**
6. Click **Activate Plugin**

### 12.3 — Verify the Plugin is Active

Visit:
```
https://your-site.com/wp-json/wp-seo-control/v1/status
```

Expected JSON:
```json
{
  "ok": true,
  "plugin_version": "0.1.0",
  "wp_version": "6.x.x",
  "rank_math_active": true,
  "rank_math_version": "1.x.x",
  "namespace": "wp-seo-control/v1"
}
```

- `404` → Plugin not active
- `rank_math_active: false` → Rank Math plugin not installed/active

### 12.4 — Ensure Rank Math is Active

WordPress admin → **Plugins → Installed Plugins** → `Rank Math SEO` must show **Active**.

If missing:
1. Plugins → Add New
2. Search: `Rank Math SEO`
3. Install + Activate
4. Complete or skip the setup wizard

### 12.5 — Test in the App

1. Open `http://127.0.0.1:5173/rankmath`
2. Status card should show **"Rank Math active"** (green)
3. Fields become editable

### 12.6 — Common Errors

**"The package could not be installed. No valid plugins were found."**

Cause: ZIP has wrong internal structure (extra nesting or files at root).

Fix:
- Extract the ZIP and verify: `wp-seo-control-companion/wp-seo-control-companion.php`
- Re-create the ZIP by right-clicking the **folder** (not files)

**Plugin active but `/wp-json/wp-seo-control/v1/status` returns 404**

Fix:
- WordPress → Settings → Permalinks → Save Changes (flushes rewrite rules)
- Re-check the URL

**"The uploaded file exceeds the upload_max_filesize directive"**

Cause: WordPress upload limit is smaller than the ZIP.

Your ZIP is only ~9 KB, so this should not occur. If it does:
- Add to `wp-config.php`:
  ```php
  define('WP_MEMORY_LIMIT', '256M');
  define('WP_MAX_MEMORY_LIMIT', '512M');
  ```
- Or adjust `php.ini`:
  ```ini
  upload_max_filesize = 20M
  post_max_size = 20M
  ```

### 12.7 — Uninstalling

1. WordPress admin → Plugins → Deactivate
2. Delete the plugin
3. WordPress automatically runs `uninstall.php` which removes plugin options

Per-post Rank Math meta is **never touched** — it belongs to Rank Math.

---

## 13. AI Prompts — How to Use with Examples

### 13.1 Overview

The AI Prompt Studio is **optional**. It works in three modes:

| `AI_PROVIDER` | Behavior |
|---|---|
| `none` | Uses mock provider — returns deterministic JSON samples |
| `mock` | Same as `none` |
| `openai` | Real OpenAI calls (requires `AI_API_KEY`) |

### 13.2 Opening the Studio

```
http://127.0.0.1:5173/ai-prompt-studio
```

You see:
- Provider status card (top)
- Two tabs: **Product prompt** / **Blog prompt**
- Editor with the current template
- Action buttons: Copy, Export, Restore default, Save, Send to AI

### 13.3 Understanding the Templates

**Product prompt template** asks the AI to return a JSON object with:
- Product name, slug, descriptions
- Categories, tags, attributes
- Pricing placeholders (never fabricated prices)
- Image filenames + alt text + title + caption
- Rank Math SEO fields
- Internal link suggestions
- FAQ suggestions
- Schema-relevant facts

**Blog prompt template** asks for:
- Title, slug, excerpt
- Search intent, target audience
- Primary + secondary keywords
- H2/H3 outline
- Introduction, sections, conclusion
- Rank Math SEO fields
- Image concepts
- Internal links, related products
- CTA, FAQ suggestions

**Both templates enforce `NEEDS_INPUT`** — the AI must never invent facts, prices, medical claims, or certifications.

### 13.4 Example 1 — Product Content

**Step 1:** Open Product prompt tab.

**Step 2:** Customize placeholders at the bottom of the template:
```
Product details provided by the user:
- Name: Herbal Hair Oil
- Category: Hair Care
- Short facts: 100ml amber bottle, cold-pressed, no additives
```

**Step 3:** Click **Send to AI**.

**Mock provider** returns:
```json
{
  "product_name": "NEEDS_INPUT",
  "slug": "needs-input",
  "short_description": "NEEDS_INPUT",
  "full_description": "NEEDS_INPUT",
  ...
}
```

**Real OpenAI** (with API key) returns something specific to the input.

**Step 4:** Copy fields you like into **Product Publisher** form.

### 13.5 Example 2 — Blog Content

**Step 1:** Switch to Blog prompt tab.

**Step 2:** Set placeholders:
```
Article details provided by the user:
- Topic: Badam benefits for daily wellness
- Audience: health-conscious adults in Pakistan
- Primary keyword: badam benefits
```

**Step 3:** Click **Send to AI**.

**Step 4:** Response is shown in raw form. Copy the title, slug, excerpt, and outline into the **Blog Publisher**.

### 13.6 Example 3 — Restoring the Default Prompt

If you customized the template and want to start over:

1. Click **Restore default**
2. Confirm the dialog
3. Template resets to the shipped default

### 13.7 Example 4 — Exporting a Template

1. Click **Export**
2. Browser downloads `product-prompt.txt` (or `blog-prompt.txt`)
3. Save it, share it, or import elsewhere

### 13.8 Example 5 — Using OpenAI

**In `.env`:**
```ini
AI_PROVIDER=openai
AI_API_KEY=sk-your-key-here
AI_MODEL=gpt-4o-mini
```

**Restart backend.**

Status card now shows `Provider: openai · Model: gpt-4o-mini`.

**Warning:** OpenAI calls cost money. Use `mock` for testing.

### 13.9 Tips for Better Output

1. **Provide real facts** — replace `{facts}` with actual details
2. **Be specific** — instead of "hair oil", say "cold-pressed amla hair oil in 100ml amber glass"
3. **Never rely on AI for prices** — always verify
4. **Review before publishing** — the AI never publishes automatically
5. **Use Mock first** — test your prompt structure without cost

---

## 14. GitHub Push Setup (for Your Own Project)

If you want to push this project to your own GitHub repo:

### Step 14.1 — Initialize Git

```powershell
cd C:\Users\YourName\Desktop\wp-seo-studio
git init
```

### Step 14.2 — Verify `.gitignore`

Make sure `.gitignore` exists with:
```
# Python
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
dist/
.vite/

# Env / Secrets
.env
.env.local
*.key
*.pem

# Database
*.db
*.sqlite
backend/data/

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

### Step 14.3 — First Commit

```powershell
git add .
git commit -m "Initial commit: WordPress WooCommerce SEO Control Studio"
```

### Step 14.4 — Create GitHub Repo

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `wp-seo-studio`
3. Visibility: **Private** (recommended — contains sensitive config patterns)
4. **Do NOT** initialize with README / .gitignore / license
5. Click **Create repository**

### Step 14.5 — Push

Copy the URLs GitHub shows. Then:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/wp-seo-studio.git
git push -u origin main
```

If prompted for credentials:
- Username: your GitHub username
- Password: **Personal Access Token** (not your account password)

**Create a Personal Access Token:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → scope `repo`
3. Copy the token → use as password

### Step 14.6 — Future Pushes

After changes:
```powershell
git add .
git commit -m "Describe what changed"
git push
```

### Step 14.7 — Cloning on Another Machine

```powershell
git clone https://github.com/YOUR_USERNAME/wp-seo-studio.git
cd wp-seo-studio
```

Then follow [Section 6](#6-installation--from-github-clone).

### Step 14.8 — Handling Secrets

**Never commit `.env`.** It's in `.gitignore`.

If you accidentally commit secrets:
1. Rotate them immediately (regenerate password, WC keys, AI key)
2. Remove from git history: `git filter-branch` or [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
3. Force push: `git push --force`

---

## 15. Running the Tests

### Backend Tests

```powershell
cd C:\Users\YourName\Desktop\wp-seo-studio\backend
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pytest
```

**Expected:** ~326 passed.

**Run specific category:**
```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -v
.\.venv\Scripts\python.exe -m pytest tests/api_schema -v
.\.venv\Scripts\python.exe -m pytest tests/integration -v
```

**With coverage:**
```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

### Frontend Type Check

```powershell
cd frontend
npm run typecheck
```

**Expected:** no errors.

### Linting

```powershell
cd backend
.\.venv\Scripts\ruff check app
.\.venv\Scripts\black --check app
```

---

## 16. Troubleshooting — Common Errors & Fixes

### 16.1 Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Fix:**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

**Error:** `Address already in use`

**Fix:**
```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Stop-Process -Id <PID> -Force
```

Or use a different port:
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001 --reload
```

---

**Error:** `sqlite3.OperationalError: no such table: connections`

**Fix:** Run migrations:
```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

---

**Error:** `ValueError: the greenlet library is required`

**Fix:**
```powershell
pip install greenlet
```

---

### 16.2 Frontend won't start

**Error:** `Cannot find module '@/components/...'`

**Fix:**
1. Ensure `vite.config.ts` has the alias:
```typescript
resolve: {
  alias: { "@": path.resolve(__dirname, "./src") },
},
```
2. Restart frontend: `Ctrl + C` then `npm run dev`

---

**Error:** `Port 5173 is in use`

**Fix:**
```powershell
Get-Process node | Stop-Process -Force
npm run dev
```

---

**Error:** `TypeScript: Cannot find module '@/layout/Layout'`

**Fix:**
1. `Ctrl + Shift + P` in VS Code
2. Type: `TypeScript: Restart TS Server`
3. Enter

---

**Error:** `Module not found: Can't resolve '@/services/connectionApi'`

**Fix:** Ensure the file exists:
```powershell
Test-Path "frontend\src\services\connectionApi.ts"
```

If `False` → recreate it. If `True` → restart TS Server.

---

### 16.3 Connection errors

**Error (in app):** `WordPress rejected the request: HTTP 401`

**Cause:** Wrong username or application password.

**Fix:**
1. Regenerate Application Password in WordPress
2. Delete the connection in the app
3. Re-add with new credentials

---

**Error:** `Site URL / Home URL mismatch`

**Cause:** WordPress is at `/wp/` subdirectory or has a proxy setup.

**Fix:** This is often intentional. Audit reports it as **warn**, not **fail**. Verify canonical URLs are correct in Rank Math.

---

**Error:** `WooCommerce REST API keys are missing`

**Fix:**
1. WooCommerce → Settings → Advanced → REST API
2. Generate keys with Read/Write
3. Edit the connection in the app → add WC keys
4. Save

---

### 16.4 Rank Math errors

**Error:** `The companion plugin is not installed or not active`

**Fix:** See [Section 12](#12-wordpress-companion-plugin-setup).

---

**Error:** `Rank Math is not active on this site`

**Fix:**
1. WordPress → Plugins → Add New → "Rank Math SEO"
2. Install + Activate

---

### 16.5 Media upload errors

**Error:** `Unrecognized image format`

**Cause:** File is not JPEG/PNG/WebP/GIF.

**Fix:** Convert to one of those formats.

---

**Error:** `Upload failed: File exceeds the maximum size`

**Fix:** Resize the image to under 10 MB, or increase in `.env`:
```ini
HTTP_MAX_RESPONSE_BYTES=20971520
```
(20 MB)

---

**Error:** `Upload failed: 413 Payload Too Large`

**Fix:** Increase WordPress upload limit in `wp-config.php`:
```php
define('WP_MEMORY_LIMIT', '256M');
define('WP_MAX_MEMORY_LIMIT', '512M');
```
Also check your server's `php.ini`:
```ini
upload_max_filesize = 20M
post_max_size = 20M
```

---

### 16.6 AI errors

**Error:** `AI_API_KEY is not set`

**Fix:** Either:
- Add key to `.env` (see [Section 13.8](#138-example-5--using-openai))
- Or leave `AI_PROVIDER=none` to use mock

---

**Error:** `Could not parse a JSON object from the AI response`

**Cause:** The AI returned text instead of JSON.

**Fix:** Edit the prompt to be more explicit. The default template already includes:
> Return ONLY the JSON object. No commentary. No markdown fences.

---

### 16.7 Test failures

**Error:** `ImportError: cannot import name 'X' from 'Y'`

**Cause:** File not saved or content truncated.

**Fix:** Verify file size:
```powershell
Get-ChildItem "backend\tests\fixtures" | Select-Object Name, Length
```

If a fixture is under expected size → re-save the file.

---

**Error:** `sqlalchemy.exc.OperationalError: no such table`

**Fix:** Test fixtures create their own tables. Ensure `conftest.py` is present and correct.

---

### 16.8 VS Code "Problems" panel issues

**Issue:** Pylance shows "Import could not be resolved"

**Fix:**
1. Open any `.py` file
2. Bottom status bar → click Python version
3. Select `./backend/.venv/Scripts/python.exe`
4. `Ctrl + Shift + P` → `Developer: Reload Window`

---

**Issue:** TypeScript shows "Cannot find module"

**Fix:**
1. `Ctrl + Shift + P` → `TypeScript: Restart TS Server`
2. If still failing, `Developer: Reload Window`

---

### 16.9 Performance

**Slow pytest:** Normal — 326 tests take ~2 minutes. Run subsets during development.

**Slow pip install:** Use `uv` (10–50x faster):
```powershell
pip install uv
uv pip install -r requirements.txt
```

**Slow npm install:** Clear cache:
```powershell
npm cache clean --force
npm install
```

---

## 17. Security Notes

### Secrets

- **Never** committed to git (`.env` is in `.gitignore`)
- **Never** stored in the SQLite database
- **Never** logged (masking in structlog)
- Stored in **OS keyring** (Windows Credential Manager, macOS Keychain, Linux Secret Service)

### Network

- **SSRF guard** blocks private/internal IPs for external calls
- **HTTPS required** in production (`require_https`)
- **Timeouts** on all HTTP calls
- **Retry limits** prevent runaway loops
- **Rate limiting** per host

### WordPress

- **Only** documented REST endpoints used
- **Companion plugin** requires `manage_options` for global settings
- **Per-post meta** requires `edit_post` capability
- **No** direct database writes
- **No** PHP execution

### Content

- **User content** is sanitized by WordPress on save
- **AI output** is never auto-published
- **Media** validated by magic bytes (not just extension)

### Recommended Production Settings

```ini
APP_ENV=production
APP_DEBUG=false
APP_MODE=real  # (forced real in production anyway)
```

Also:
- Use HTTPS reverse proxy (nginx, Caddy)
- Set CORS origins to specific domains
- Enable rate limiting at proxy level
- Keep `.env` permissions restricted (chmod 600 on Linux)

---

## 18. Known Limitations

| Limitation | Detail |
|---|---|
| **Single-user** | No login/auth for the app itself |
| **No background worker** | Queue records jobs but doesn't auto-execute |
| **Simple products only** | No variations, grouped, or external products |
| **No theme CSS injection** | Image presets only provide copy-able CSS |
| **No bulk operations** | One item at a time |
| **No GSC integration** | Audit does not claim ranking data |
| **Not a WP backup** | Backup covers app config only |
| **SQLite only** | No PostgreSQL in default setup |
| **English UI** | No i18n support |

---

## 19. FAQ

**Q: Do I need a real WordPress site?**
A: No. `APP_MODE=mock` works without any external site. Real features (upload, publish, Rank Math) require a real site.

**Q: Will this affect my live site?**
A: Only when you click **Save** / **Publish** / **Update**. Nothing happens automatically.

**Q: Where are my credentials stored?**
A: Windows Credential Manager (Windows), Keychain (macOS), Secret Service (Linux). Never in the app's database.

**Q: Can I export my configuration?**
A: Yes — Backup page exports connection metadata, prompt templates, and non-secret settings as JSON. Secrets are never exported.

**Q: Can I undo a publish?**
A: Yes — delete the post/product in WordPress, or use the WordPress trash.

**Q: How do I enable HTTPS for the app itself?**
A: Use a reverse proxy (nginx, Caddy) in front of the FastAPI server. The app itself is HTTP only.

**Q: Which Rank Math fields are supported?**
A: SEO title, meta description, focus keyword, canonical URL, robots directives, Facebook/Twitter social metadata. See the companion plugin's `META_KEYS`.

**Q: Does the AI provider see my content?**
A: Only if you click **Send to AI** with `AI_PROVIDER=openai`. Otherwise, no external calls.

**Q: Can I add new presets?**
A: Yes — edit `backend/app/services/image_presets_service.py` and add to `SUGGESTED_PRESETS` or `CSS_PRESETS`.

**Q: How do I reset the database?**
A: Delete `backend/data/app.db` and run `alembic upgrade head` again. **Warning:** this removes all local history.

**Q: How do I update the companion plugin?**
A: Upload the new ZIP to WordPress → it will offer to replace the existing plugin → confirm → keep all settings.

**Q: What's the difference between "partial" and "failed" in history?**
A: "Partial" = content created but Rank Math meta failed. "Failed" = content not created.

**Q: Can I use this with WooCommerce Blocks checkout?**
A: Yes — the app only configures store settings, not checkout rendering.

**Q: Where can I find the companion plugin ZIP?**
A: It's not pre-built. You create it from the `wordpress-plugin/wp-seo-control-companion/` folder using PowerShell, Explorer, 7-Zip, or `zip`. See [Section 12.1](#121--create-the-plugin-zip).

**Q: Do I need to rebuild the ZIP every time I change plugin code?**
A: Yes. If you modify any file inside `wp-seo-control-companion/includes/`, recreate the ZIP and re-upload to WordPress.

---

## License

GPL-2.0-or-later (same as the companion plugin).

---

## Support

For issues:
1. Check [Troubleshooting](#16-troubleshooting--common-errors--fixes)
2. Check logs in the backend terminal
3. Check browser console (F12)
4. Open an issue on GitHub (if you have one)

---

**Made with care. Every field has an example. Every action is truthful. Every change is reversible where feasible.**