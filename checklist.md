# SnapSort MVP — Build Checklist

## Phase 1: Project Foundation
- [x] **1a: FastAPI Setup** — Initialize project with uv, FastAPI, Jinja2, Tailwind CSS (CDN)
- [x] **1b: Supabase Connection** — Add supabase-py, config module, health check endpoint
- [x] **1c: Database Schema** — Create tables in Supabase (users, databases)
- [x] **1d: HTMX Setup** — Add HTMX to base template for interactive updates

## Phase 2: Notion OAuth
- [x] **2a: OAuth Flow** — Redirect to Notion, handle callback, store access token
- [x] **2b: Session Management** — Cookie-based sessions to track logged-in users
- [x] **2c: Fetch Databases** — Get user's Notion databases and store in Supabase

## Phase 3: Onboarding + Dashboard UI
- [x] **3a: Onboarding Page** — Database selection checklist (first visit)
- [x] **3b: Dashboard Layout** — Upload zone + database picker grid
- [x] **3c: HTMX Partials** — Dynamic updates without full page reloads

## Phase 4: File Upload
- [x] **4a: Upload Zone** — Drag/drop, paste, file picker (vanilla JS)
- [x] **4b: Supabase Storage** — Upload images, get public URLs
- [x] **4c: Thumbnail Preview** — Show uploaded image before routing

## Phase 5: AI Extraction + Notion
- [x] **5a: OpenAI Vision** — Send screenshot, get structured JSON
- [x] **5b: Notion Page Creation** — Create entry with extracted fields
- [x] **5c: Confirmation Card** — Show what was extracted, link to Notion
- [x] **5d: Improved Extraction** — Extract title + detailed description from images
- [x] **5e: Classification Selector** — User selects category (Learning, Business, Recipe, etc.)
- [x] **5f: Smart Field Mapping** — Auto-map extracted data to Notion schema fields

## Phase 6: Polish
- [ ] **6a: Auto-Routing** — AI classifies and picks the right database
- [ ] **6b: Activity Feed** — (deferred) Show last 10 routed screenshots
- [ ] **6c: Settings Page** — Manage databases, disconnect Notion
- [ ] **6d: Error States** — Handle failures gracefully

## Phase 7: Deploy
- [ ] **7a: Railway Setup** — Deploy FastAPI app
- [ ] **7b: Environment Config** — Production env vars
- [ ] **7c: End-to-End Test** — Real Notion workspace test
- [ ] **7d: Share** — First users