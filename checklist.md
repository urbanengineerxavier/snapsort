# SnapSort MVP — Build Checklist

## Phase 1: Project Foundation
- [x] **1a: FastAPI Setup** — Initialize project with uv, FastAPI, Jinja2, Tailwind CSS (CDN)
- [x] **1b: Supabase Connection** — Add supabase-py, config module, health check endpoint
- [x] **1c: Database Schema** — Create tables in Supabase (users, databases)
- [ ] **1d: HTMX Setup** — Add HTMX to base template for interactive updates

## Phase 2: Notion OAuth
- [ ] **2a: OAuth Flow** — Redirect to Notion, handle callback, store access token
- [ ] **2b: Session Management** — Cookie-based sessions to track logged-in users
- [ ] **2c: Fetch Databases** — Get user's Notion databases and store in Supabase

## Phase 3: Onboarding + Dashboard UI
- [ ] **3a: Onboarding Page** — Database selection checklist (first visit)
- [ ] **3b: Dashboard Layout** — Upload zone + database picker grid
- [ ] **3c: HTMX Partials** — Dynamic updates without full page reloads

## Phase 4: File Upload
- [ ] **4a: Upload Zone** — Drag/drop, paste, file picker (vanilla JS)
- [ ] **4b: Supabase Storage** — Upload images, get public URLs
- [ ] **4c: Thumbnail Preview** — Show uploaded image before routing

## Phase 5: AI Extraction + Notion
- [ ] **5a: OpenAI Vision** — Send screenshot, get structured JSON
- [ ] **5b: Notion Page Creation** — Create entry with extracted fields
- [ ] **5c: Confirmation Card** — Show what was extracted, link to Notion

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