# Commercial licensing

## Customer behavior

The current public pilot grants three unique figure generations through the local ledger. Each later unique generation costs 10 credits. Keep one stable generation ID only while the source reference and scientific brief remain unchanged. Technical failures, reference-parity corrections, and playback of the same Master SVG into Illustrator and PowerPoint are free retries. A new reference, new scientific content, added panels, or a materially different composition is a new charged generation.

Customers obtain an owner-issued signed Key for 100, 500, or 1000 credits. Activate it with `scripts/activate_key.ps1` and use `scripts/license_status.ps1` to show remaining free figures and credits. Never print or expose a customer Key after activation.

If entitlement is insufficient, stop before changing Illustrator or PowerPoint and display exactly:

`欢迎关注“队长的生物实验室”微信公众号/小红书。`

`添加队长的笔记本微信（XBBen01），购买 Key。`

`100积分=10元；500积分=45元；1000积分=85元。`

## Owner behavior

The separate `commercial-admin` directory is not part of the customer Skill. Its generator creates an encrypted Ed25519 private key and publishes only the corresponding public key to `assets/license-public-key.pem`. Credits may be any positive multiple of 10, including 10, 50, and 100.

The advertised packages are 100 credits for CNY 10, 500 credits for CNY 45, and 1000 credits for CNY 85. The owner may issue a small test Key, but customer-facing Keys should match a paid order and customer reference.

Never copy the private signing key, passphrase, administrator environment variables, or customer registry into the distributed Skill. Do not put an activation key in logs, examples, screenshots, or source control.

## Security boundary

Signed offline keys keep customers from minting authentic keys without the private signing key, but a local ledger cannot reliably prevent state copying, rollback, or source modification. A production commercial service should move balance and redemption state to HTTPS endpoints with authenticated activation, device binding, atomic reservation/commit/cancel, revocation, rate limiting, and an audit log. The public Skill should then hold only the service URL and public client protocol, never the server secret.

## Future online storefront

If manual fulfillment becomes too costly, migrate to four production layers:

1. The mini program authenticates the customer and displays fixed credit packages.
2. The commerce backend creates a WeChat Pay API v3 JSAPI/mini-program order and returns only the payment-launch parameters.
3. The backend verifies the signed payment notification and, when needed, queries the order. It grants credits idempotently by the unique WeChat transaction ID; the client-side success callback is never proof of payment.
4. The licensing service binds the balance to the customer account and issues a one-time activation code or rotatable API key. The Skill calls reserve, commit, cancel, and status endpoints over HTTPS.

Required controls include idempotent order creation, amount/SKU verification, webhook signature verification, replay protection, refund handling, audit logs, rate limiting, secret rotation, and a customer-visible order and credit history.

Suggested packages are 100 credits for CNY 10, 500 for CNY 45, and 1000 for CNY 85. If the owner chooses CNY 90 for the 1000-credit package, it has the same unit discount as the 500-credit package and provides little incentive to upgrade.
