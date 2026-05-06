# CLEAR Flex Subscription Demo
### A LaunchDarkly integration demo built for the SE assignment

---

## The scenario

CLEAR (the company behind TSA PreCheck fast lanes) currently offers a single annual membership at $189/year. This demo simulates a product team at CLEAR preparing to launch a new **flexible subscription model** that allows users to purchase access by the day ($9), week ($29), or month ($49) as a lower-commitment alternative to the annual plan.

This is a high-stakes, revenue-impacting release. The flex subscription model affects pricing, checkout flows, and user segmentation across CLEAR's entire platform. A pricing bug, an unexpected surge in day-pass purchases cannibalizing annual subscriptions, or a broken checkout flow could have immediate and measurable revenue consequences.

The demo shows how LaunchDarkly enables CLEAR's engineering and product teams to ship this feature with confidence, iterate on it with data, and manage it in production. Without requiring redeployments!

---

## App overview

The demo is a two-screen web application built with React and Vite on the frontend, and Python 3 with FastAPI on the backend. User profiles and session data are stored in a lightweight SQLite database, keeping the setup self-contained with no external database dependency.

**Login screen** : a simple username input that loads a predefined user profile. No authentication is performed. The username maps to a user context (account_status, airport) that drives all LaunchDarkly flag evaluations downstream.

**Subscription page** : displays the CLEAR membership plans available to the logged-in user. Which plans are shown, how they are presented, and how the AI assistant behaves are all controlled by LaunchDarkly at runtime.

---

## Demo users

Fifteen predefined users cover the key scenarios. Use these to navigate the demo:

| Username | Account status | Airport |
|---|---|---|
| `user1` | free | jfk | 
| `user2` | expired | sfo | 
| `user3` | active | jfk | 
| `jfk-expired-1` | expired | jfk | 
| `jfk-expired-2` | expired | jfk | 
| `jfk-expired-3` | expired | jfk | 
| `sfo-expired-1` | expired | sfo |
| `sfo-expired-2` | expired | sfo | 
| `sfo-expired-3` | expired | sfo | 
| `jfk-free-1` | free | jfk | 
| `jfk-free-2` | free | jfk | 
| `jfk-free-3` | free | jfk | 
| `sfo-free-1` | free | sfo |
| `sfo-free-2` | free | sfo |
| `sfo-free-3` | free | sfo |


Each user requires a non-null password, which can be a randomly generated string. Without this, the /api/user login request will not be triggered.

The login screen passes the username directly to the backend as the LaunchDarkly user context key.

---

## LaunchDarkly integration

### 1. Feature flags — dual evaluation (client + server)

**Flag key:** `flex-subscription-enabled`
**Type:** Boolean
**Default:** `false` 
**SDK:** Evaluated on both the server-side SDK and the client-side SDK

The flex subscription feature is gated on both sides of the stack deliberately:

On the **backend**, the `/api/plans` endpoint evaluates the flag using the server-side SDK before returning plan data. If the flag is off, the flex SKUs (day, week, month) are never included in the API response — they never leave the server. This protects against client-side manipulation and ensures pricing data is only served when the feature is intentionally enabled.

On the **frontend**, the client-side SDK reads the same flag to control rendering. When the flag is off, the subscription page shows only the annual plan. When it is on, the flex plan cards animate in.

This dual-evaluation pattern means the kill switch is complete. Toggling the flag off in the LaunchDarkly dashboard removes the feature from both the UI and the API response simultaneously, with no redeployment required.

**Segments — internal QA validation before customer rollout:** Before the flex subscription feature is released to any customer segment, it is first validated internally using a LaunchDarkly segment called **CLEAR Internal QA**. This segment is defined by user keys (`user1`, `user2`) and represents CLEAR's internal QA team's free and expired accounts. A targeting rule at the top of the flag's rule stack serves `true` to any user in the CLEAR Internal QA segment, regardless of their account status or airport. This allows the engineering and QA team to test the full flex subscription experience in the production environment before the flag is ever enabled for customers. Once internal validation is complete, the user-facing targeting rules are activated while the QA segment rule remains in place, ensuring the internal team can always access the feature for ongoing monitoring.

**Targeting rule:** The flag serves `true` only when `account_status = expired` and `airport = jfk`. This reflects the business decision to launch flex subscriptions initially as a re-engagement tool for lapsed members, before a broader rollout to all users. However, this is not a fixed decision. The targeting rules can change as the rollout strategy changes, say if the business / product org wants to enable it for `airport = sfo` instead or not include airport at all. The option of having these attributes available, allow for more control around the rollout and release strategy.

**Kill switch demo moment:** Toggle the flag off while logged in as an expired user if the flag was targeted for expired user. The flex plans disappear from the UI immediately without requiring any code changes from front end or the backend, giving complete control on the release without the need for deployments. 

---

### 2. Experimentation — A/B/C test on plan card highlighting

**Flag key:** `highlighted-plan-variant`
**Type:** String
**Variations:** `week` / `day` / `none`
**Default:** `none`
**SDK:** Client-side only

This experiment tests whether visually highlighting a specific plan card on the subscription page influences users to select a plan. The hypothesis is that highlighting a specific plan card increases the likelihood of a user selecting a plan for checkout.

**Variation A — `week`:** The week pass card is highlighted with a blue border and a check mark as the default selected plan. 

**Variation B — `day`:** The day pass card is highlighted. Tests whether a lower price point as the anchor drives more plan selections overall, even if at lower revenue per transaction.

**Variation C — `none`:** No card is highlighted.

**Prerequisite flag:** `highlighted-plan-variant` uses `flex-subscription-enabled` as a prerequisite flag. Without this, if `highlighted-plan-variant` were to serve `day` or `week` to a user who does not have flex subscriptions enabled — meaning those plan cards are not rendered on the page at all — the app would throw a browser-level alert dialog notifying the user of an error. The prerequisite flag relationship in LaunchDarkly prevents this by ensuring the targeting rules of `highlighted-plan-variant` are only evaluated and applied when `flex-subscription-enabled` is already serving `true` for that user. This demonstrates how prerequisite flags can be used to enforce safe flag dependencies and prevent UI errors caused by flags being evaluated out of order or for the wrong audience.

Traffic is split 33/33/33 across all three variations. Each user is consistently assigned the same variation on every session, based on their user key.

**Metric:** `plan-selected` — a custom Occurrence (binary) metric that fires when the user clicks "Continue with this plan." Tracked via `ldClient.track("plan-selected")` on the frontend at the moment of selection of "continue with XYZ plan".

**Statistical approach:** Bayesian at 90% confidence threshold. Bayesian was chosen over the traditional Frequentist approach because it starts surfacing directional results as soon as events come in, without needing a large sample size upfront. This makes it better suited for a demo environment where the number of users is limited.

**Important assumption:** With only a few demo users, the experiment will not reach statistical significance or declare a winner. The demo shows the experiment mechanism of traffic splitting, event tracking, and result accumulation rather than a concluded experiment. In a production environment with real CLEAR traffic, even a 1% rollout would generate thousands of events per day.

---

### 3. AI Config — chat assistant prompt management

**AI Config key:** `chat-assistant-prompt`
**Type:** Completion
**Default:** `disabled`
**Model:** OpenAI GPT-4o-mini

A floating chat assistant on the subscription page helps non paying users choose the right plan. The assistant's system prompt which makes its tone, personality, and instructions is managed as a LaunchDarkly AI Config rather than hardcoded in the application.

Two prompt variations are defined:

**Variation A — neutral:** You are Alex, a friendly CLEAR membership concierge who genuinely cares about helping users get back through airport fast lanes. You have access to the following subscription plans: Day pass at $9, Week pass at $29, Month pass at $49, and Annual membership at $189. When a user asks for help, respond warmly and conversationally, ask a follow up question about their travel habits if needed, and walk them through why a specific plan fits their lifestyle. Use the user's name if you know it, and express genuine enthusiasm about getting them back on track with their travels.

**Variation B — urgent:** You are a CLEAR membership assistant. You have access to the following subscription plans: Day pass at $9, Week pass at $29, Month pass at $49, and Annual membership at $189. When a user asks for help, respond in 2 sentences maximum. Be direct, factual, and recommend the single best plan for their situation with no elaboration.

The backend `/api/chat` endpoint evaluates the AI Config using the LaunchDarkly server-side AI SDK, passing the user's context (user_id, account_status, airport). The prompt returned by LaunchDarkly is used as the system prompt for the OpenAI API call. The model response is returned to the frontend and displayed in the chat panel. The user's context can be used for targeting the specific variation for different types of users. 

**What this demonstrates:** The prompt that drives the AI assistant's behavior lives in LaunchDarkly, not in the application code. CLEAR's product or marketing team can change the assistant's tone, update its instructions, or switch between prompt variations from the LaunchDarkly dashboard without requiring a redeployment or code changes. The same kill switch and targeting capabilities that apply to feature flags apply to AI Configs: the flag can be turned off instantly and that would make thee AI serve a default system prompt that is defined in the code, or served different prompts to different users.

---

## Assumptions

**No real authentication.** The login screen does not perform any authentication. Usernames map directly to hardcoded user profiles in the backend. In a real implementation, user attributes would be loaded from CLEAR's identity and subscription management systems.

**No real payment flow.** Selecting a plan and clicking "Continue" does not initiate a checkout or payment process. The interaction exists solely to generate the `plan-selected` experiment metric event.

**Predefined user profiles.** Account status (`free` / `expired`) and airport are hardcoded in the backend `users.py` file. In production these would be dynamic attributes pulled from CLEAR's user database at session time.

**Single environment.** The demo runs entirely in a single LaunchDarkly environment. A real implementation would use separate Development, Staging, and Production environments with different flag rules in each.

**Experiment sample size.** The demo users are insufficient to generate statistically significant experiment results. The experimentation demo illustrates the tracking and splitting mechanism rather than a concluded test.

**AI Config availability.** AI Configs is an add-on feature in LaunchDarkly. Access was confirmed for this demo environment. In accounts where AI Configs is not enabled, the chat assistant would fall back to the hardcoded system prompt defined in the backend.

**Model used.** The demo uses OpenAI GPT-4o-mini. API calls are made in real time and incur cost. 

---

## Setup

### Prerequisites

- Node.js 18+ (for the React frontend)
- Python 3.10+ (for the FastAPI backend)
- A LaunchDarkly account with the following configured:
  - Boolean flag: `flex-subscription-enabled` (client-side SDK enabled)
  - String flag: `highlighted-plan-variant` with values `week`, `day`, `none`
  - AI Config: `chat-assistant-prompt` with two prompt variations
  - Experiment on `highlighted-plan-variant` with `plan-selected` metric
- An OpenAI API key

### Environment variables

**Backend `.env`:**
```
LD_SDK_KEY=your-python-server-side-sdk-key
OPENAI_API_KEY=your-openai-api-key
```

**Frontend `.env`:**
```
VITE_LD_CLIENT_KEY=your-react-client-side-sdk-key
```

### Running the app

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
python3 backend/run.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/login` and log in with any of the predefined usernames above.

---

## LaunchDarkly features demonstrated

| Feature | Flag / Config | Where |
|---|---|---|
| Feature flag — server-side gating | `flex-subscriptions-enabled` | `/api/plans` backend |
| Feature flag — client-side rendering | `flex-subscriptions-enabled` | `FlagContext.jsx` frontend |
| Targeting by user attribute | `account_status = expired` | LD dashboard targeting rules |
| Kill switch | `flex-subscriptions-enabled` | Toggle off in LD dashboard |
| A/B/C experimentation | `highlighted-plan-variant` | Subscription page card highlight |
| Custom metric tracking | `plan-selected` | `ldClient.track()` on plan selection |
| AI Config — prompt management | `chat-assistant-prompt` | `/api/chat` backend |
| AI Config — variation targeting | Neutral vs urgent tone | LD AI Config dashboard |