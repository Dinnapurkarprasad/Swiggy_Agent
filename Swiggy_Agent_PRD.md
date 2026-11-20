# Swiggy Party Agent — PRD

> Initial product doc. Gives context to anyone (human or coding agent) working in this repo.

## 1. The idea

Hosting a party means asking every guest what they eat: veg, Jain, halal, allergies, spice level, cuisine. It's messy and someone always gets left out.

**Swiggy Party Agent** fixes this:

1. The host creates a party and shares one link.
2. Each guest fills a short form with their food preferences.
3. An AI agent reads all responses, searches Swiggy, finds the best restaurants and coupons, and builds a meal plan that works for everyone.
4. The host reviews the plan and approves it.
5. The agent places the order(s) on Swiggy and shows live tracking.

## 2. Goals and non-goals

**Goals (MVP)**
- Guests can submit preferences in under 30 seconds, with no login.
- The agent produces 2–3 meal plans that cover every guest's diet and allergies.
- Coupons are found and applied automatically; savings are shown.
- Nothing is ordered without the host's explicit approval.
- Orders can come from multiple restaurants (one Swiggy order per restaurant).
- **MVP targets small parties (up to ~10 people)**, because of Swiggy's ₹1000-per-order cap (see section 9.1).

**Non-goals (for now)**
- Splitting the bill between guests.
- Alcohol, groceries (Instamart), or table booking (Dineout).
- Guest accounts / login. Hosts sign in with Google; guests never log in.
- Mobile app (web only, mobile-friendly).

## 3. Users

- **Host**: signs in with Google (first sign-in = sign-up), creates the party, reviews plans, approves, pays (COD/UPI on their Swiggy account). Connects Swiggy (phone + OTP) only when ordering.
- **Guest**: opens the shared link and fills the form. No account needed.

Why two logins for the host: Swiggy OAuth only authorizes ordering on the host's account and returns no profile, so it can't identify the host. Google sign-in does that.

## 4. User flow

```
Host signs in with Google ──► creates party ──► gets the guest link (public) to share
   • Dashboard: host's own parties, visible only when signed in
        │
Guests submit form ──► host sees live responses
        │
Host clicks "Generate plan" (or RSVP deadline passes)
        │
Agent builds 2–3 plans ──► host reviews
        │            ▲
        │            └── "Regenerate" with feedback (e.g. "cheaper", "more biryani")
        ▼
Host approves a plan ──► agent places orders one restaurant at a time
        │
Live order status + ETA on the host dashboard
```

## 5. Party setup (host)

- Party name, date/time
- Delivery address (picked from the host's Swiggy saved addresses)
- Budget per person (optional)
- RSVP deadline (optional)

## 6. Guest form

Required: name, diet, spice. Everything else optional.

| Field | Type | Options |
|---|---|---|
| Name | text | — |
| Bringing anyone? | number + kids yes/no | 0–3 |
| Food type | single select | Pure Veg (no egg), Eggetarian, Jain (no onion/garlic/root veg), Vegan, Non-Veg |
| Restrictions (non-veg only) | multi select | Halal only, No beef, No pork, No seafood |
| Allergies | multi select + other | Nuts, Dairy/Lactose, Gluten, Seafood/Shellfish |
| Spice level | single select | Mild, Medium, Spicy, Doesn't matter |
| Cuisines (max 3) | multi select | North Indian, South Indian, Biryani/Mughlai, Tandoor/Kebabs, Street food/Chaat, Thali, Chinese/Indo-Chinese, Thai, Japanese, Pizza/Italian, Burgers/Fast food, Continental, Mexican, Middle Eastern, Healthy/Salads, Anything works |
| Favourite dish | text + suggestion chips | e.g. Dosa, Biryani, Pizza, Paneer, Momos |
| Beverage | single select | Soft drink, Juice, Lassi/Buttermilk, Shake/Cold coffee, Mocktail, None |
| Hunger level | single select | Light, Regular, Very hungry |
| Dessert? | yes/no | — |

## 7. Agent design (LangGraph)

The agent is a **LangGraph state graph**. Code does the deterministic steps; the LLM only does the planning (choosing restaurants and dishes).

```
aggregate_responses        (code)  build party summary from form data
        │
discover_restaurants       (code)  Swiggy search, keep only OPEN ones
        │
fetch_menus_and_coupons    (code)  menus + available coupons per restaurant
        │
generate_plans             (LLM)   returns 2–3 plans as structured JSON
        │
validate_plans             (code)  hard checks (see below)
        │  fail → back to generate_plans (max 2 retries)
        ▼
host_approval              (interrupt)  wait for host: approve / regenerate / edit
        │  regenerate → generate_plans with host feedback
        ▼
place_orders               (code)  one restaurant at a time
        │
track_orders               (code)  poll status every ≥10s
```

### Rules the agent must follow
1. **Safety before preference.** Never give a guest a dish containing an allergen they listed. Jain and halal needs override cuisine choices.
2. **Never guess.** If halal or Jain prep isn't clearly stated by the restaurant, show a warning instead of assuming.
3. **Every guest is covered.** Each guest gets at least one main they can eat.
4. **Fewer restaurants is better.** Each extra restaurant adds a delivery fee and a different arrival time.
5. **Show every compromise.** If someone's favourite dish is skipped, say so.
6. **The LLM never places orders.** `place_food_order` is only called inside `place_orders`, and only after host approval.

### Validation checks (code, not LLM)
- Every guest has ≥1 compatible main dish.
- No allergen conflicts.
- Every `menu_item_id` exists on that restaurant's menu and is in stock.
- Each order total is under the Swiggy cap (₹1000 for Builders Club v1).
- Coupon savings shown only if the cart actually confirms a discount.

### Quantities
Use fixed rules in code (tune later), not LLM guesses. Starting point:
- 1 gravy/main dish per 3 people
- 2–3 breads per person
- 1 rice/biryani per 3–4 people
- +20% for "Very hungry", −20% for "Light"

## 8. Agent output (what the host sees)

1. **Party summary**: headcount, diet split, allergies, spice split, top cuisines.
2. **2–3 plans** (e.g. Budget / Balanced / Max variety), each with:
   - Orders grouped by restaurant: items, qty, veg/non-veg tag, which guests each dish is for
   - Coupon applied, subtotal, discount, delivery fees, total, cost per person
   - ETA per restaurant
   - Coverage check (✅ all guests covered) and warnings (⚠️ confirm Jain prep)
3. **Per-guest view**: what each guest gets.
4. **Actions**: Approve, Swap a dish, Edit quantities, Regenerate with feedback.

Plan JSON returned by the LLM (validated with Pydantic):

```json
{
  "plans": [{
    "label": "Balanced",
    "orders": [{
      "restaurant_id": "r_123",
      "items": [
        { "menu_item_id": "m_45", "qty": 2, "is_veg": true, "for_guests": ["g1", "g4"] }
      ],
      "coupon_code": "PARTY100"
    }],
    "warnings": ["Halal not confirmed for r_123"]
  }]
}
```

## 9. Swiggy integration

We use **Swiggy Builders Club MCP** (Food server: `mcp.swiggy.com/food`). Access is application-based; apply early.

Main tools used:
`get_addresses` → `search_restaurants` → `get_restaurant_menu` / `search_menu` → `update_food_cart` → `fetch_food_coupons` → `apply_food_coupon` → `get_food_cart` → `place_food_order` → `track_food_order` (+ `get_food_orders`, `flush_food_cart`)

Known constraints:
- **One restaurant per cart.** Switching restaurant clears the cart. Multi-restaurant plans = multiple sequential orders.
- **₹1000 cap per order.** See 9.1. This is a hard rule for the planner.
- **`place_food_order` is not idempotent (COD).** On error, check `get_food_orders` before retrying.
- **Auth**: host connects their Swiggy account via OAuth 2.1 (PKCE, phone + OTP). Tokens stored server-side, encrypted. Never sent to the frontend. This authorizes ordering only; host identity comes from Google sign-in.
- **Partial failure**: if one order fails after another succeeded, tell the host clearly and suggest a replacement restaurant for the affected guests.

### 9.1 The ₹1000 per-order cap

Swiggy limits every order placed through Builders Club to **₹1000 maximum**. This is per order (one restaurant's cart), not per party.

So the food for a party must be split into several orders, each ≤ ₹1000:

| Party size | Approx. total | Orders needed |
|---|---|---|
| 5 people | ~₹1,600 | 2 orders (e.g. ₹640 + ₹970) |
| 10 people | ~₹3,200 | ~4 orders |
| 20 people | ~₹6,000 | 6–7 orders |

Even the same restaurant may need several orders (₹950 + ₹980 + ...).

Problems with many orders:
1. **Delivery fee on every order**: 7 orders = 7 delivery fees.
2. **Food arrives at different times**: each order has its own delivery partner.
3. **Host pays many times**: with UPI, each order is a separate payment.

What we do about it:
- **Planner rule**: every order total (after coupon, including fees) must be ≤ ₹1000. If a restaurant's cart goes over, split it into multiple orders. Enforced in `validate_plans` (code, not LLM).
- **Prefer fewer orders**: when choosing between plans, fewer orders is better (cheaper fees, food arrives together).
- **Show it to the host**: plan cards show the number of orders, total delivery fees, and ETA per order.
- **MVP scope**: small parties, up to ~10 people.
- **Ask Swiggy**: in the Builders Club application, explain the party use case and request a higher cap.

### 9.2 Payment

- **COD**: the original v1 payment method. `place_food_order` places the order directly.
- **UPI** (added July 2026): uses the shared Payment tools `get_payment_options`, `check_payment_status`, `confirm_order`.
  - `place_food_order` creates the order in **PENDING_PAYMENT** state. It becomes **PLACED** only after payment succeeds.
  - `confirm_order` is idempotent, so retries are safe.
  - Host pays **each order separately**. Dashboard shows per-order status: waiting for payment → placed → out for delivery.
- Some coupons work only with online payment and some only with COD. Coupons are fetched per order and per payment method.

### 9.3 Access stages (we cannot use real Swiggy until approved)

We can host our own app anytime. What needs Swiggy's approval is calling Swiggy for real users.

1. **Local + mock**: build everything on `localhost` with `MockSwiggyClient` (fake restaurants, menus, coupons). Same interface as `RealSwiggyClient`. Switched with `SWIGGY_MODE=mock|staging|production`.
2. **Apply** at Builders Club with a short screen-recording video of the full flow working. Mention host approval before ordering (Swiggy looks for agents that confirm orders and don't surprise users).
3. **Staging**: `mcp-staging.swiggy.com/food`. Same tools, seeded data, no real orders.
4. **Production**: after staging has worked for ≥ 48 hours and Swiggy confirms access (builders@swiggy.in). Complete their go-live checklist first.

## 10. Tech stack

**Backend (Python)**
- FastAPI
- Pydantic (request validation + LLM output validation)
- LangGraph (agent graph, human-in-the-loop interrupt, checkpointing)
- LangChain (`with_structured_output` for plan JSON)
- `langchain-mcp-adapters` + `mcp` SDK (Swiggy MCP tools)
- LLM: Gemini free tier via LangChain (provider configurable via env)
- PostgreSQL (Supabase or Neon) + SQLModel + Alembic
- LangGraph Postgres checkpointer (saves graph state while waiting for host approval)
- Tooling: uv, ruff, pytest

**Frontend**
- Next.js (App Router) + TypeScript
- Tailwind CSS + shadcn/ui
- react-hook-form + zod (guest form)
- TanStack Query (API calls, polling order status)

**Hosting (free tiers)**: Vercel (frontend), Render/Railway (backend), Supabase/Neon (DB)

## 11. Repo structure

```
swiggy-party-agent/
├── PRD.md
├── frontend/              # Next.js app
│   └── app/
│       ├── p/[partyId]/        # guest form
│       └── host/               # host dashboard (Google sign-in)
└── backend/
    ├── app/
    │   ├── api/           # FastAPI routes
    │   ├── models/        # DB tables (SQLModel)
    │   ├── swiggy/        # SwiggyClient interface, mock + real
    │   ├── agent/         # LangGraph graph, nodes, prompts
    │   ├── planner/       # plan schema, validation, quantity rules
    │   └── ordering/      # place orders, tracking
    └── tests/
```

## 12. Data model (initial)

- **User** (host): id, google_sub, email, name
- **Party**: id, host_user_id, name, date, address_id, budget_per_person, rsvp_deadline, status
- **GuestResponse**: id, party_id, name, plus_ones, kids, food_type, restrictions[], allergies[], spice, cuisines[], fav_dish, beverage, hunger, dessert
- **Plan**: id, party_id, label, plan_json, total, savings, status (draft / approved / rejected)
- **Order**: id, plan_id, restaurant_id, swiggy_order_id, total (≤ ₹1000), payment_method (cod / upi), payment_status, status, eta

## 13. API (initial)

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/google` | Host signs in with Google ID token; sets login cookie |
| GET | `/auth/me` | Current host |
| POST | `/auth/logout` | Clear login cookie |
| POST | `/parties` | Create party (signed in), return guest link |
| GET | `/parties/{id}` | Public party info for the guest form |
| POST | `/parties/{id}/responses` | Submit guest form |
| GET | `/host/parties/{id}` | Host dashboard data (responses + summary) |
| POST | `/host/parties/{id}/plans/generate` | Start the agent |
| GET | `/host/parties/{id}/plans` | Get generated plans |
| POST | `/host/parties/{id}/plans/{planId}/approve` | Approve and place orders |
| POST | `/host/parties/{id}/plans/regenerate` | Regenerate with feedback |
| GET | `/host/parties/{id}/orders` | Order status + ETA |

All `/host/...` routes require sign-in and that the signed-in user owns the party.
| GET | `/swiggy/oauth/start`, `/swiggy/oauth/callback` | Connect host's Swiggy account |

## 14. Milestones

1. **Form + dashboard**: create party, guest form, host sees responses and summary.
2. **Mock Swiggy + planner**: LangGraph graph running end to end on mock data, plans shown to host.
3. **Approval flow**: approve / regenerate / swap dish, mock order placement and tracking.
4. **Demo video + apply**: record the full mock flow, apply to Builders Club.
5. **Staging**: OAuth + real MCP client against Swiggy staging; UPI payment flow.
6. **Production + polish**: go-live checklist, error handling, partial failures, mobile UI.

## 15. Open questions

- Will Swiggy raise the ₹1000 cap for party orders?
- Can we add cooking instructions (e.g. "Jain, no onion/garlic", "less spicy") through the MCP cart?
- UPI vs COD as default payment? (UPI = host pays each order; COD = pay at the door per order.)
- How reliable are veg/halal/allergen labels in Swiggy menu data?
