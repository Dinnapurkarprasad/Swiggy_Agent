# CLAUDE.md — Swiggy Party Agent

Guidance for Claude (and any coding agent) working in this repo. Read this first, then `Swiggy_Agent_PRD.md` for the full product spec.

## 1. What we're building (one paragraph)

The host signs in with Google, creates a party and shares a guest link. Each guest fills a short form with their food preferences, with no login needed. A LangGraph agent then reads all the responses, searches Swiggy through the Builders Club MCP, and builds 2–3 meal plans that cover every guest's diet and allergies, with coupons applied. The host approves one plan. The agent then places one Swiggy order per restaurant cart, and **every order must be ≤ ₹1000**. After that it tracks the orders live. The MVP is for small parties of up to ~10 people.

## 2. Swiggy Builders Club docs — the authoritative source

You have access to the Swiggy Builders Club docs. They are the authoritative source for Swiggy MCP (Food, Instamart, Dineout, Scenes). **Always consult them before writing Swiggy code.**

- Index:      https://mcp.swiggy.com/builders/llms.txt
- Full text:  https://mcp.swiggy.com/builders/llms-full.txt
- Per-page:   append `.md` to any `https://mcp.swiggy.com/builders/docs/...` URL

Where to look:

- Tool schemas: `/docs/reference/{food,instamart,dineout,scenes}`
- Error codes: `/docs/reference/errors`
- Auth flow: `/docs/start/authenticate`
- Rate limits: `/docs/operate/rate-limits`
- Go-live checklist, retries, observability: `/docs/build/ship-to-production`

### Rules

1. Before recommending a tool name, parameter, error code, rate limit, or auth flow, fetch the relevant doc and verify it.
2. Never invent tool names or parameters. If the docs don't cover something, say so and ask.
3. Prefer `.md` page fetches over `llms-full.txt` when you know the exact area. They are cheaper on context.
4. If the docs and the PRD disagree, **the docs win**. Point out the mismatch to Prasad and update the PRD.

### Smoke test (verified 2026-11-19)

`llms.txt` lists **20 tools** on the Food server:

| Group | Tools |
|---|---|
| Discovery | `search_restaurants`, `get_restaurant_menu`, `search_menu` |
| Cart | `update_food_cart`, `get_food_cart`, `flush_food_cart` |
| Coupons | `fetch_food_coupons`, `apply_food_coupon` |
| Ordering | `place_food_order`, `get_food_orders`, `get_food_order_details` |
| Tracking | `track_food_order`, `get_food_delivery_status` |
| Payment (shared across servers) | `get_payment_options`, `check_payment_status`, `confirm_order` |
| Address (shared) | `get_addresses`, `create_address`, `delete_address` |
| Support (shared) | `report_error` |

The PRD (section 9) doesn't mention `get_food_order_details`, `get_food_delivery_status`, `create_address`, `delete_address` or `report_error`. Check their schemas before deciding whether we need them.

### Doc notes to re-verify before coding against them

- **UPI flow:** `place_food_order` returns a PENDING_PAYMENT state. Call `confirm_order` **only** after `check_payment_status` reports a successful terminal state, and only if the order wasn't already auto-confirmed.
- `place_food_order` needs a delivery **address ID**, taken from `get_addresses`.
- `llms.txt` says `fetch_food_coupons` should only surface **COD-valid** coupons. This may conflict with PRD 9.2, which says coupons are fetched per payment method. Check `/docs/reference/food` before building the coupon logic.
- Rate-limit numbers are not in `llms.txt`. Read `/docs/operate/rate-limits.md` before writing any polling or retry code.

## 3. Non-negotiable rules (safety and money)

1. **The LLM never places orders.** `place_food_order` and `confirm_order` are called only from the `place_orders` node (deterministic code), and only after the host has approved. They are never bound as LLM tools.
2. **Allergen and diet safety comes before preference.** An allergy, Jain or halal requirement always wins. If a restaurant doesn't clearly state Jain or halal prep, raise a warning instead of assuming.
3. **Validation lives in code, not in the LLM.** `validate_plans` must check:
   - every guest has at least one main they can eat
   - there are no allergen conflicts
   - every `menu_item_id` exists and is in stock
   - every order total is ≤ ₹1000 (after the coupon, including fees)
   - coupon savings are shown only after the cart confirms them
4. **`place_food_order` is not idempotent (COD).** On any error or timeout, call `get_food_orders` to check whether the order went through before retrying. Never blindly retry.
5. **One restaurant per cart.** Switching restaurant clears the cart, so place orders sequentially. Call `flush_food_cart` before starting each new order.
6. **Swiggy OAuth tokens stay on the server and are encrypted at rest.** Never send them to the frontend, write them to logs, or include them in LLM prompts.
   - Host identity comes from **Google sign-in** (`POST /auth/google` → httpOnly `party_session` cookie), not from Swiggy: Swiggy OAuth only authorizes MCP tool access and returns no profile (verified in `/docs/start/authenticate`, 2026-11-20). Every host route checks the logged-in user owns the party.
7. **Partial failure:** if order 2 fails after order 1 succeeded, stop and tell the host clearly. Suggest a replacement for the affected guests, and never silently re-plan and re-order.
8. Quantities come from fixed rules in `planner/quantities.py`, not from LLM guesses. See PRD section 7.

## 4. Architecture at a glance

```
LangGraph:
aggregate_responses → discover_restaurants → fetch_menus_and_coupons
   → generate_plans (LLM, structured output) → validate_plans (code, ≤2 retries)
   → host_approval (interrupt; Postgres checkpointer) → place_orders → track_orders
```

- **Swiggy access goes through one interface, `SwiggyClient`.** It has two implementations, `MockSwiggyClient` and `RealSwiggyClient`, selected by `SWIGGY_MODE=mock|staging|production`.
  - Nodes depend on the interface only, so no MCP calls are scattered around the codebase.
  - Method names and arguments on the interface mirror the real MCP tool names, so swapping the mock for the real client is mechanical.
- **The mock must behave like real Swiggy:**
  - the ₹1000 cap is enforced
  - one restaurant per cart (switching clears the cart)
  - some items can be out of stock and some restaurants closed
  - coupons sometimes fail to apply
  - UPI orders go through PENDING_PAYMENT before PLACED

  If the mock is too friendly, we will only find bugs on staging.
- **Plan JSON is validated with Pydantic** (`planner/schema.py`). The LLM is called with `with_structured_output`.
- The LLM provider is configurable through env. The default is Gemini free tier, so prompts and token use should stay compact. Send the LLM trimmed menus (id, name, price, veg flag, tags), never raw MCP payloads.

## 5. Tech stack

- **Backend:** Python, FastAPI, Pydantic, LangGraph, LangChain, `langchain-mcp-adapters` + `mcp` SDK, SQLModel + Alembic, PostgreSQL (Supabase/Neon), LangGraph Postgres checkpointer. Tooling is `uv`, `ruff` and `pytest`.
- **Frontend:** Next.js (App Router) + TypeScript, Tailwind CSS + shadcn/ui, react-hook-form + zod, TanStack Query.
- **Hosting:** Vercel (frontend), Render/Railway (backend), Supabase/Neon (DB).

## 6. Repo layout

```
swiggy-party-agent/
├── CLAUDE.md
├── Swiggy_Agent_PRD.md
├── frontend/                 # Next.js
│   ├── app/                  # routes only (thin pages that compose components)
│   │   ├── page.tsx              # landing
│   │   ├── p/[partyId]/          # guest form (public)
│   │   └── host/                 # host dashboard (Google sign-in required)
│   ├── components/           # one folder per section, mirroring app/
│   │   ├── landing/              # for app/page.tsx
│   │   ├── p/                    # for app/p/...
│   │   ├── host/                 # for app/host/...
│   │   └── ui/                   # shadcn components (shadcn installs here)
│   └── lib/                  # all supporting code
│       ├── api/                  # pure functions that call the backend (no React)
│       ├── mutations/            # TanStack Query hooks (queries + mutations) wrapping lib/api/
│       ├── types/                # all TypeScript types (request/response shapes); never declared in api/ or mutations/
│       ├── http.ts               # fetch wrapper used only by lib/api/
│       └── utils.ts              # shadcn cn()
└── backend/
    ├── app/
    │   ├── api/        # FastAPI routes
    │   ├── models/     # SQLModel tables
    │   ├── swiggy/     # SwiggyClient interface, mock, real
    │   ├── agent/      # LangGraph graph, nodes, prompts
    │   ├── planner/    # plan schema, validation, quantity rules
    │   └── ordering/   # order placement, payment, tracking
    └── tests/
```

## 7. Commands

These are the expected commands. Update this section once the scaffold exists.

```bash
# backend
cd backend
uv sync
uv run fastapi dev app/main.py
uv run pytest
uv run ruff check . && uv run ruff format .
uv run alembic upgrade head

# frontend
cd frontend
npm install
npm run dev
npm run lint && npm run build
```

Env vars include `SWIGGY_MODE`, `DATABASE_URL`, `LLM_PROVIDER`, `GOOGLE_API_KEY`, `TOKEN_ENCRYPTION_KEY`, `GOOGLE_OAUTH_CLIENT_ID`, `SESSION_SECRET`, and the Swiggy OAuth client settings. Keep a `.env.example` in sync, and never commit `.env`.

## 8. Coding conventions

- **Make minimal, targeted changes** and don't touch unrelated logic.
- **When sharing code, give complete files**, not partial snippets.
- **Frontend data flow:** component → hook in `lib/mutations/` → function in `lib/api/` → `request()` in `lib/http.ts`. Components never call `lib/api/` or `fetch` directly.
- **Frontend uses Tailwind classes, never inline styles.** Use shadcn/ui components where they fit, and build mobile-first because guests open the link on their phones.
- **Python:**
  - Type hints everywhere and Pydantic models at every boundary (API, LLM output, Swiggy responses).
  - Code that touches DB or network is async.
- Money is stored as **integer paise** (or `Decimal`), never float. Format it as ₹ only in the UI.
- Diet, allergen and restriction values are enums shared between the backend and the frontend zod schema, so the two never drift apart.
- Every node and every Swiggy call logs a structured line with `party_id`, the node name and the tool name. Tokens and guest PII are never logged.

## 9. Testing priorities

1. **`validate_plans`** is the most important code in the repo. Unit-test every rule with deliberately bad plans:
   - an allergen in a dish
   - a guest left uncovered
   - an order of ₹1001
   - a fake `menu_item_id`
   - an out-of-stock item
2. **Quantity rules:** test hunger scaling and rounding.
3. **Ordering:**
   - COD retry-after-error goes through `get_food_orders` and creates no duplicate order
   - UPI pending → paid → confirm works
   - partial-failure handling is correct
4. Run the full graph end to end against `MockSwiggyClient`, including the interrupt and resume.

## 10. Milestones

From PRD section 14:

1. Form + dashboard
2. Mock Swiggy + planner
3. Approval flow
4. Demo video + Builders Club application
5. Staging (`mcp-staging.swiggy.com/food`) + OAuth + UPI
6. Production + polish

Real Swiggy can't be used until access is approved. Until then, everything runs on the mock.

## 11. Open questions (check docs and ask before assuming)

- Will Swiggy raise the ₹1000 cap for party orders?
- Can cooking instructions ("Jain, no onion/garlic", "less spicy") be passed through `update_food_cart`? Check the schema.
- Should the default payment be UPI or COD? Also see the COD-only coupon note in section 2.
- How reliable are the veg, halal and allergen labels in the menu data? Until this is known, treat missing labels as **unknown** and show a warning, not as safe.
