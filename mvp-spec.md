# Product Spec: SnapSort — Screenshot to Notion
## Web App MVP

**Version:** 1.0 MVP (Web App)
**Platform:** Web (FastAPI + HTMX) — mobile-responsive
**Purpose:** Validate core value before building native app
**Stack:** FastAPI, Jinja2, HTMX, Supabase, OpenAI Vision API, Notion API  

---

## 1. What This Does

User visits the web app, connects their Notion account, and uploads a screenshot.
The app:
1. Shows their Notion databases as destination tiles
2. User picks one (or taps Auto) → AI extracts structured data → creates a Notion entry
3. Confirmation shown with what was extracted and where it went

No App Store. No native install. Ships in days, not weeks.

---

## 2. What We're Testing

The webapp MVP answers one question: **do people find enough value in the AI extraction and routing to change their behavior at all?**

If users tolerate a manual upload step to get their screenshot into Notion as a structured entry, the native app is worth building. If they don't bother, the idea needs rethinking before investing in iOS development.

Secondary questions:
- Is the AI extraction accurate enough to be useful?
- Do users want manual routing, auto-routing, or both?
- Which content types get routed most (recipes, products, articles)?

---

## 3. Core User Flow

```
User visits snapsort.app
        ↓
Landing page → "Connect Notion" button
        ↓
Notion OAuth → fetch user's databases
        ↓
Dashboard: Upload Zone + Database Picker
        ↓
User uploads screenshot (drag/drop, paste, or file picker)
        ↓
Destination Picker appears:
  [ Recipes ]  [ Business Ideas ]  [ Design Inspo ]
  [ Reading List ]  [ Products ]  [ Auto-Route ✨ ]
        ↓
        ├── User clicks a database → AI extracts → Notion entry created
        └── User clicks Auto → AI classifies + routes → Notion entry created
        ↓
Confirmation card: what was extracted, which database, link to Notion entry
```

---

## 4. Pages / Screens

### 4.1 Landing Page (unauthenticated)

Keep it minimal. One job: explain the value and get the click.

- Headline: "Every screenshot, exactly where it belongs in Notion"
- Subheadline: "Upload a screenshot. AI reads it and sends it to the right Notion database — fully structured."
- Single CTA button: "Connect Notion — it's free"
- 3 simple before/after examples (screenshot in → structured Notion entry out)
- No pricing, no feature lists, no footer bloat

---

### 4.2 Onboarding (post-OAuth, first visit only)

**Step 1 — Database Selection**
- "Which Notion databases do you want to route screenshots to?"
- List of all user's databases with checkboxes (fetched from Notion)
- Each item shows database icon + name
- Select up to 8
- "Done" button → goes to Dashboard

---

### 4.3 Dashboard (main screen)

Three zones:

**Zone A — Upload Area (top, prominent)**
- Large drag-and-drop zone: "Drop a screenshot here"
- Also accepts: paste from clipboard (Cmd+V / Ctrl+V), click to open file picker
- Accepts PNG, JPG, WEBP
- Max file size: 10MB (compress client-side if larger)
- On upload → immediately show thumbnail + trigger Destination Picker

**Zone B — Destination Picker (appears after upload)**
- Grid of database tiles (the user's selected databases)
- Each tile: icon + name, hover state
- "Auto-Route ✨" tile always last
- Clicking a tile immediately starts processing

**Zone C — Recent Activity Feed (below upload)**
- Last 10 routed screenshots
- Each item: thumbnail, destination database, title extracted, timestamp, link to Notion entry
- Empty state: "Your routed screenshots will appear here"

---

### 4.4 Processing State

After user selects a destination:
- Overlay on the upload zone showing progress
- Step 1: "Reading your screenshot..." (OpenAI Vision API call)
- Step 2: "Sending to [Database Name]..." (Notion API call)
- Step 3: Success ✓ with green checkmark

If it fails at any step: show specific error with retry button.

---

### 4.5 Confirmation Card

Shown after successful routing. Replaces the processing overlay.

- Database icon + name: "Sent to Recipes ✓"
- Extracted fields preview:
  - Title: "Miso Glazed Salmon"
  - Cuisine: Japanese
  - Cook Time: 25 min
  - (etc.)
- Two buttons:
  - "Open in Notion →" (opens the created page)
  - "Route another screenshot" (resets upload zone)
- Optional: "Wrong database?" link → shows destination picker again

---

### 4.6 Settings Page

Accessible from nav. Three sections:

**Notion Connection**
- Connected workspace name
- "Disconnect" button

**My Databases**
- Same checklist as onboarding
- Reorder via drag-and-drop
- "Sync from Notion" button (re-fetches database list)

**Auto-Route Behavior**
- Radio: "Always ask me" / "Auto-route and show confirmation" / "Auto-route silently"
- Default: "Auto-route and show confirmation"

---

## 5. AI Extraction

Identical to native app spec. No changes needed here.

### Extraction prompt (send to OpenAI Vision API)

```
You are a data extraction assistant. Analyze this screenshot and:
1. Identify the content type (recipe, product, article, quote, event, 
   business idea, design inspiration, person/contact, or general)
2. Extract all relevant structured data
3. Return as JSON only — no explanation

The destination Notion database is: {database_name}
The database has these properties: {database_schema}

Match extracted fields to the database properties as closely as possible.
For fields that don't map cleanly, add them to a "Notes" text field.

Return format:
{
  "content_type": "recipe",
  "confidence": 0.95,
  "title": "...",
  "extracted_fields": {
    "property_name": "value",
    ...
  },
  "notes": "Any additional info that didn't fit the schema"
}
```

### Auto-routing classification prompt

```
You are a routing assistant. Analyze this screenshot and decide which 
database it belongs in.

Available databases:
{list of database names + their descriptions/schemas}

Return JSON only:
{
  "recommended_database": "database_id",
  "confidence": 0.87,
  "content_type": "recipe",
  "reasoning": "Contains ingredients list and cooking instructions"
}

If confidence < 0.75, set recommended_database to null.
```

---

## 6. Notion API Integration

### On OAuth connect
```
1. Notion OAuth → get access_token
2. GET /v1/databases → fetch all user databases
3. For each database: store id, name, icon, properties schema
4. Store in Supabase (server-side, not localStorage)
5. Refresh on "Sync from Notion" button or if >24hrs stale
```

### Creating a Notion page
```
POST /v1/pages
{
  "parent": { "database_id": "selected_database_id" },
  "properties": {
    "Name": { "title": [{ "text": { "content": "Miso Glazed Salmon" } }] },
    "Cuisine": { "select": { "name": "Japanese" } },
    "Cook Time": { "rich_text": [{ "text": { "content": "25 min" } }] },
    ...
  },
  "children": [
    {
      "type": "image",
      "image": {
        "type": "external",
        "external": { "url": "screenshot_url_from_supabase" }
      }
    }
  ]
}
```

### Screenshot storage
- Upload to Supabase Storage on receipt
- Get public URL
- Embed in Notion page as image block
- Keep in Supabase for 30 days then delete (free tier storage management)

---

## 7. Data Model (Supabase)

```sql
-- Users (created on first Notion OAuth)
users
  id                  uuid primary key
  notion_access_token text
  notion_workspace_id text
  plan                text default 'free'
  created_at          timestamptz

-- Cached Notion databases per user
databases
  id                  uuid primary key
  user_id             uuid references users
  notion_database_id  text
  name                text
  icon                text
  is_in_picker        boolean default true
  picker_order        int
  schema              jsonb
  last_synced_at      timestamptz

-- Routing history (for activity feed + future AI learning)
routing_history
  id                    uuid primary key
  user_id               uuid references users
  screenshot_url        text
  content_type_detected text
  database_routed_to    text
  extracted_fields      jsonb
  was_corrected         boolean default false
  correct_database      text
  created_at            timestamptz
```

---

## 8. Tech Stack

```
Backend:      FastAPI (Python)
Package Mgr:  uv
Templates:    Jinja2 + Tailwind CSS
Interactivity: HTMX
Upload UX:    Vanilla JS (minimal, upload zone only)
Database:     Supabase Postgres
File Storage: Supabase Storage
AI:           OpenAI GPT-4o Vision API
Notion:       notion-client Python SDK
Deployment:   Railway
Payments:     Stripe (when ready — skip for MVP)
```

Why FastAPI: Simple Python backend with Jinja2 templates. HTMX provides
interactivity without a JS framework. API keys stay server-side.
Railway deployment is straightforward.

---

## 9. Environment Variables

```
# Notion OAuth
NOTION_CLIENT_ID=
NOTION_CLIENT_SECRET=
NOTION_REDIRECT_URI=https://snapsort.app/auth/notion/callback

# OpenAI
OPENAI_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# App
SECRET_KEY=
APP_URL=https://snapsort.app
```

---

## 10. Routes (FastAPI)

### Pages (return HTML via Jinja2)
```
GET  /                             → landing page
GET  /dashboard                    → main dashboard (upload + picker + feed)
GET  /onboarding                   → database selection (first visit)
GET  /settings                     → settings page
```

### Auth
```
GET  /auth/notion                  → start Notion OAuth
GET  /auth/notion/callback         → handle OAuth callback, store token
POST /auth/logout                  → clear session
```

### API (return HTML partials for HTMX)
```
POST /api/databases/sync           → re-fetch user's Notion databases
POST /api/route                    → receive screenshot, run AI, create Notion entry
GET  /api/history                  → fetch recent routing history (partial)
```

### /api/route endpoint logic
```
1. Receive: uploaded image file + database_id (or "auto")
2. If "auto": call classification prompt → get recommended database_id
3. Fetch database schema from Supabase
4. Call OpenAI Vision API with extraction prompt + schema
5. Upload image to Supabase Storage → get URL
6. Create Notion page with extracted fields + image URL
7. Save to routing_history table
8. Return: HTML partial with confirmation card (for HTMX swap)
```

---

## 11. MVP Build Order

**Phase 1 — Project Foundation**
- [ ] FastAPI project setup + Jinja2 + Tailwind CSS
- [ ] Supabase connection + database schema
- [ ] Basic page templates (layout, landing placeholder)

**Phase 2 — Notion OAuth**
- [ ] Notion OAuth flow (connect + callback + store token)
- [ ] Session management
- [ ] Fetch and store user's databases

**Phase 3 — Onboarding + Dashboard UI**
- [ ] Onboarding page: database selection checklist
- [ ] Dashboard layout: upload zone + database picker grid
- [ ] HTMX partials for dynamic updates

**Phase 4 — File Upload**
- [ ] Upload zone (drag/drop, paste, file picker) with vanilla JS
- [ ] Image upload to Supabase Storage
- [ ] Thumbnail preview

**Phase 5 — AI Extraction + Notion**
- [ ] OpenAI Vision API integration
- [ ] Notion page creation with extracted fields
- [ ] Processing states + confirmation card (HTMX)

**Phase 6 — Polish**
- [ ] Auto-routing classifier
- [ ] Recent activity feed
- [ ] Settings page
- [ ] Error states + loading states

**Phase 7 — Deploy**
- [ ] Deploy to Railway
- [ ] Test end-to-end with real Notion workspace
- [ ] Share with first users

---

## 12. Free Tier Limits (MVP — no paywall yet)

Skip payments entirely for the MVP. Focus on learning, not revenue.
Add Stripe after validating that people use it more than once.

When you do add pricing, carry over the same tiers:
- Free: 30 screenshots/month, 2 databases
- Pro ($9/mo): unlimited screenshots, unlimited databases, auto-routing

---

## 13. Error States

- Notion OAuth fails → "Couldn't connect to Notion. Try again."
- No databases found → "No databases found. Create one in Notion first." + link to Notion
- File too large → compress client-side, warn if still >10MB
- AI extraction fails → show raw filename + manual field entry form as fallback
- Notion API rate limit → retry after 1s, surface error after 3 attempts
- OpenAI timeout → "Having trouble reading this screenshot. Try again or enter details manually."

---

## 14. Key UX Rules

1. **Paste should just work.** Cmd+V on the dashboard should instantly grab a screenshot from clipboard. This is the fastest possible capture flow on desktop.
2. **Never lose the screenshot.** If Notion creation fails, keep the image in Supabase and show a retry button. Never silently drop it.
3. **Show what the AI extracted before confirming.** The confirmation card is not optional — users need to see the extracted fields to build trust in the product.
4. **The Notion link must be one click away.** Every confirmation card and every activity feed item links directly to the created Notion page.
5. **Mobile upload must work.** On iPhone, user can share a screenshot to Safari, open snapsort.app, and use the file picker to upload. Not as slick as a native share sheet but functional enough to test.

---

## 15. What This MVP Does NOT Include

Save these for the native app once the webapp validates the idea:

- iOS Share Sheet / Share Extension
- macOS menubar app
- Push notifications
- Offline queue / sync
- AI learning from corrections
- Batch upload (multiple screenshots at once)
- Subscription / payments (validate first, charge later)