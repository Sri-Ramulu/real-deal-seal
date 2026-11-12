# Sample businesses for onboarding

Invented data for two businesses that are not shops selling parcels, to show that a new business joins with no
code change and is judged only on evidence that fits its type.

| Files | Business type | Rule set applied |
|---|---|---|
| `bright-clean.*.csv` | services (home cleaning) | completion, cancellations, disputes, refunds |
| `pixel-press.*.csv` | digital (templates) | delivery, disputes, refunds |

Order columns: `order_id, order_date, amount_usd, currency, status, buyer_ref, refunded_usd, fulfilled_days, tracking_ref, cancelled, dispute`.
`buyer_ref` is turned into a one-way key on import and is not stored.

Load them through the public API with `python scripts/seed_samples.py` while the server runs. They are imported
with `simulated_demo: true`, so every fact they produce is labelled simulated or reported, never PayPal-confirmed,
and neither business can earn the seal from these files.
