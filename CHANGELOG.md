## GUI hotfix

- Fixed AutoResponder tab crash caused by responsive `col` arguments passed into `field()`.
- Added responsive column support to the shared field factory.
- Fixed the Retry action in error tabs so it rebuilds the selected tab directly and reports reload failures.
- Updated the Flet dependency range to match the current 0.90+ API used by the GUI.

# Changelog

## 0.3.0

- Reworked Fragment Stars purchase flow around current public pyfragment patterns.
- Added dynamic Fragment API hash discovery with configured fallback.
- Added authenticated cookie validation and Fragment request throttling.
- Added `updateStarsBuyState` before Stars purchase initialization.
- Generate Fragment account payload from the configured V4R2 wallet.
- Use the exact destination, amount and payload returned by Fragment.
- Added bounded retry handling for transient Fragment errors.
- Serialized FunPay order processing to protect wallet seqno and order idempotency.
- Unified FunPay orders and auto-replies on a shared `Account` and `Runner`.
- Added persistent TON payment destination for safe `unknown` recovery.
- Expanded tests and documentation.

# Changelog

## 0.2.0

- split runtime data from source files
- added database recovery for in-flight orders
- improved trace validation
- added automated tests and CI scaffolding
- polished repository documentation
