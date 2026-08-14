# Security

## Secrets

Do not commit the following values:

- `config.json`
- TON mnemonic
- Fragment cookie
- Fragment hash fallback
- TON API key
- FunPay Golden Key
- Telegram bot token

## Operational rules

- Use the generated `.autostars.lock` to keep only one process alive.
- Keep `unknown` orders for manual or later automated recheck only.
- Validate `wallet_address` against the mnemonic-derived wallet before going live.
- Use a dedicated wallet for production.

## Safe testing

Test the project first with:

- a disposable FunPay account,
- a small TON balance,
- a non-production Telegram bot,
- and a test target username.

## Fragment wallet binding

Account payload for `getBuyStarsLink` is generated from the configured TON wallet at runtime. A legacy `PAYMENT.account` value is treated only as a compatibility check and is not used as the source of truth.
