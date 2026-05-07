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
<img width="2876" height="1432" alt="image" src="https://github.com/user-attachments/assets/14ca8fe1-15b6-4959-86e7-65df0e652662" />

---

## Setup

### Prerequisites

- Node.js 18+ (for the React frontend)
- Python 3.10+ (for the FastAPI backend)
- NOTE: This project has been developed and verified on **Python 3.13.13**. FastAPI supports Python 3.10+ and the app may run on earlier versions, however SQLAlchemy 2.1.0b2 compatibility has only been confirmed on Python 3.13.13. If you encounter issues with SQLAlchemy on a different Python version, upgrading to Python 3.13.13 is recommended.

- A LaunchDarkly account with the following configured:
   - Create a new project in LaunchDarkly titled "naman-singhal-demo" and make sure a "test" environment is available 
  - LD server-side-sdk key (for naman-singhal-demo project)
  - LD API key with admin role as a service token
  - LD client-id for the test environmnet
  - An OpenAI API key


### Environment variables

**Backend `.env`:**
```
LD_SDK_KEY=your-python-server-side-sdk-key
OPENAI_API_KEY=your-openai-api-key
LD_API_KEY=your-admin-access-service-token-api
```

**Frontend `.env`:**
```
VITE_LD_CLIENT_KEY=your-client-side-ID-for-the-env
```

### Running the app

**Backend:**
```bash
cd backend
pip3 install -r requirements.txt
python3 run.py
```

**Frontend:**
```bash
npm install
npm run dev
```

Open `http://localhost:5173/login` and log in with any of the predefined usernames below.

---

## Demo users


Account status types -
1. Free : These are users of CLEAR that have signed up and created an account with CLEAR but don't have an active paid subscription. 
2. Expired : These are users of CLEAR that had an active paying membership in the past but have not renewed their subscription after it had expired. 
3. Active : These are users of CLEAR that are currently enrolled in a paid subscription


| Username | Account status | Airport |
|---|---|---|
| `user1` | free | jfk | 
| `user2` | expired | sfo | 
| `user3` | active | jfk | 
| `jfk-expired-1` | expired | jfk | 
| `sfo-expired-1` | expired | sfo |
| `jfk-free-1` | free | jfk | 
| `sfo-free-1` | free | sfo |


Each user requires a non-null password, which can be a random string. Without this, the /api/user login request will not be triggered.

The login screen passes the username directly to the backend as the LaunchDarkly user context key.

The /api/user login request will take the user directly to the subscribe page which should currently only show the single annual membership plan available to the user. Since the launchdarkly flag has not been configured yet, this is the default subscription option available to the users. 

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

--- 

## LaunchDarkly integration

**In a new terminal:**
```bash
cd backend
python3 ldsetup.py
```
The above command creates a new flag in launchdarkly - flex-subscription-enabled and adds default rule configurations, a segment rule, and an external user targeting rule. 

The script also creates a segment "clear-internal-qa" with three users - user1, user2, user3 which for this demo purposes will be treated as test accounts of the internal QA team at CLEAR. 

**⚠️ In case the script does not work:** 1. Manually create a segment CLEAR Internal QA with the key `clear-internal-qa` by going to the segments section on the right panel. Add the three users - user1, user2, user3 to individual targeting as shown in the screenshot below. 
<img width="2876" height="1258" alt="image" src="https://github.com/user-attachments/assets/4628023e-9baa-469d-b5c6-6167808ee69f" />


2. Create a new flag `flex-subscription-enabled` in Launchdarkly test environment as depicted in the image below. 

<img width="1440" height="779" alt="image" src="https://github.com/user-attachments/assets/7ec6deaa-7788-4eef-993c-8d917e6f0b35" />



### 1. Feature flags — dual evaluation (client + server)

**Flag key:** `flex-subscription-enabled`
**Type:** Boolean
**Default when targeting off:** `false` 
**Default when targeting on:** `false` 
**SDK:** Evaluated on both the server-side SDK and the client-side SDK

The flex subscription feature is gated on both sides of the stack deliberately:

On the **backend**, the `/api/plans` endpoint evaluates the flag using the server-side SDK before returning plan data. If the flag is off, the flex SKUs (day, week, month) are never included in the API response — they never leave the server. This protects against client-side manipulation and ensures pricing data is only served when the feature is intentionally enabled.

On the **frontend**, the client-side SDK reads the same flag to control rendering. When the flag is off, the subscription page shows only the annual plan. When it is on, the flex plan cards animate in.

This dual-evaluation pattern means the kill switch is complete. Toggling the flag off in the LaunchDarkly dashboard removes the feature from both the UI and the API response simultaneously, with no redeployment required.

**Segments — internal QA validation before customer rollout:** A top-priority targeting rule serves true to all users in the CLEAR Internal QA segment (keys: user1, user2, user3) regardless of account status or airport. This allows the team to validate the feature in production before any customer-facing rules are activated, and remains in place post-launch for ongoing monitoring.

**Targeting rule:** Serves `true` when `account_status` = `expired` and `airport` = `jfk`, scoping the initial rollout to lapsed members in one market. The rule is not fixed as the rollout strategy evolves, attributes like airport can be adjusted or removed entirely from the LD dashboard without any code changes, giving the product team direct control over the release scope.

**Kill switch demo moment:** Toggle the flag off while logged in as an expired user if the flag was targeted for expired user. The flex plans disappear from the UI immediately without requiring any code changes from front end or the backend, giving complete control on the release without the need for deployments. 

---

### 2. Experimentation — A/B/C test on plan card highlighting

**Flag key:** `highlighted-plan-variant`
**Type:** String
**Variations:** `week` / `day` / `none`
**Default when targeting off:** `none`
**Default when targeting on:** `none`
**SDK:** Client-side only

This experiment tests whether visually highlighting a specific plan card on the subscription page influences users to select a plan. The hypothesis is that highlighting a specific plan card increases the likelihood of a user selecting a plan for checkout

**Variation A — `week`:** The week pass card is highlighted with a blue border and a check mark as the default selected plan. 

**Variation B — `day`:** The day pass card is highlighted and checked. Tests whether a lower price point as the anchor drives more plan selections overall, even if at lower revenue per transaction.

**Variation C — `none`:** No card is highlighted.


Traffic is split 33.33/33.33/33.33 across all three variations. Each user is consistently assigned the same variation on every session, based on their user key.

**Metric:** `plan-selected` — a custom Occurrence (binary) metric that fires when the user clicks "Continue with this plan." Tracked via `ldClient.track("plan-selected")` on the frontend at the moment of selection of "continue with XYZ plan".

This is how the flag appears when the experiment is live and completely set up. 
<img width="2858" height="1316" alt="image" src="https://github.com/user-attachments/assets/927a56d1-6b4d-46e1-8232-4312d81ac290" />


**Important assumption:** With only a few demo users, the experiment will not reach statistical significance or declare a winner. The demo shows the experiment mechanism of traffic splitting, event tracking, and result accumulation rather than a concluded experiment. In a production environment with real CLEAR traffic, even a 1% rollout would generate thousands of events per day.

---

### 3. AI Config — chat assistant prompt management

**AI Config key:** `chat-assistant-prompt`
**Type:** Completion
**Default:** `disabled`
**Model:** OpenAI GPT-4o-mini

A floating chat assistant on the subscription page helps non paying users choose the right plan. The assistant's system prompt which makes its tone, personality, and instructions is managed as a LaunchDarkly AI Config rather than hardcoded in the application.

Two prompt variations are defined:

**Variation A — neutral:** 

**Variation B — urgent:** 

<img width="2866" height="1276" alt="image" src="https://github.com/user-attachments/assets/88aefecc-d2c0-4cc6-96e6-b43d88d4c34f" />


The backend `/api/chat` endpoint evaluates the AI Config using the LaunchDarkly server-side AI SDK, passing the user's context (user_id, account_status, airport). The prompt returned by LaunchDarkly is used as the system prompt for the OpenAI API call. The model response is returned to the frontend and displayed in the chat panel. The user's context can be used for targeting the specific variation for different types of users. 

---

## Assumptions

**No real authentication.** The login screen does not perform any authentication. Usernames map directly to hardcoded user profiles in the backend. In a real implementation, user attributes would be loaded from CLEAR's identity and subscription management systems.

**No active user subscription flow.** The demo is scoped to non-paying users, specifically, free and expired accounts. Active paying members are included in the user set for flag targeting demonstration purposes only. Initiating, modifying, or cancelling a real subscription is out of scope for the demo.

**No real payment flow.** Selecting a plan and clicking "Continue" does not initiate a checkout or payment process. The interaction exists solely to generate the `plan-selected` experiment metric event.

**Predefined user profiles.** Account status (`free` / `expired`) and airport are hardcoded in the backend `users.py` file. In production these would be dynamic attributes pulled from CLEAR's user database at session time.

**Single environment.** The demo runs entirely in a single LaunchDarkly environment. A real implementation would use separate Development, Staging, and Production environments with different flag rules in each.

**Experiment sample size.** The demo users are insufficient to generate statistically significant experiment results. The experimentation demo illustrates the tracking and splitting mechanism rather than a concluded test.

**AI Config availability.** AI Configs is an add-on feature in LaunchDarkly. Access was confirmed for this demo environment. In accounts where AI Configs is not enabled, the chat assistant would fall back to the hardcoded system prompt defined in the backend.

**Model used.** The demo uses OpenAI GPT-4o-mini. API calls are made in real time and incur cost. 

---

