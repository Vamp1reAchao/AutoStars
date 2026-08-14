# Architecture

AutoStars is organized around four small cores:

- `FragmentStarsProcessor` — owns Fragment session handling, dynamic API hash discovery, purchase state, wallet-derived account data, rate limiting, exact TON payload handling, and transaction confirmation.
- `Database` — stores order state, transaction hashes, and recovery data in SQLite.
- `AutoResponder` — handles FunPay message events using rule-based matching.
- `StarBot` — owns one FunPay `Account`, one shared `Runner`, payment serialization, recovery, Telegram notifications, and shutdown.

## Flow

```text
FunPay `NEW_ORDER` event
    ↓
Order parser
    ↓
Unit stars validation
    ↓
Total stars = unit × count
    ↓
Fragment recipient lookup
    ↓
Fragment request + payload extraction
    ↓
TON transfer
    ↓
TON Center trace confirmation
    ↓
completed / failed / unknown
```

## Why this structure

The code keeps the pay/confirm path isolated from the UI and the reply engine. That makes it easier to test the payment flow, swap providers later, and keep the public repository readable.

## Recovery model

- `processing` means the order is in-flight.
- `unknown` means the app cannot prove whether TON was accepted.
- `failed` means a deterministic failure happened.
- `completed` means the trace was confirmed and recorded.

`unknown` is intentionally conservative so the bot never auto-sends a second payment when the first one may already have succeeded.

## Fragment design references

The Fragment flow follows the same high-level patterns used by current public Fragment clients: dynamic API hash discovery, authenticated cookie validation, `updateStarsBuyState` before `initBuyStarsRequest`, wallet-derived account information, exact transaction message data, and bounded retries. The project does not import `pyfragment` because its current wallet/provider stack targets newer `tonutils` APIs than this project's deliberately pinned V4R2 integration.

The FunPay Runner is shared by order delivery and auto-replies. The periodic task is retained only for recovery of `unknown` transactions and session refresh, not as the primary order trigger.
