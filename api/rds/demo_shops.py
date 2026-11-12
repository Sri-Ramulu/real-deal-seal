"""Four fictional shops that join at startup through the same onboarding a real business uses.

They make the Evidence switch visible. Two of them are convincing scams: clean, complete, cheaper listings with no
tricks in the text, and a record of refunds and lost disputes that led Real Deal Seal to withdraw their seals. With
evidence off, an assistant sees only the listing and has no reason to avoid them; with evidence on, it reads the
record. One shop has a weak record that is not withdrawn, and one is an honest new maker with too little history.

Everything here is labelled as what it is:
- the shops are fictional and say so on the site;
- their order histories are imported records with simulated_demo=True, so refunds show as reported by the business
  and disputes as simulated; none of it is presented as PayPal-confirmed;
- their PayPal connection is the labelled simulated connection (no sandbox app is configured for them).

Runs once: a shop that already exists is left alone, so a restart never duplicates anything.
"""
from __future__ import annotations

import datetime
import random
import secrets

from . import onboarding, refresh, store

SHOPS = [
    {
        "name": "Violet & Vine Home", "role": "scam", "seed": 11, "orders": 48,
        "ships_from": "Denver, CO", "returns": "30-day returns", "sells": "Linen table and bed linens",
        "profile": {"refund": 0.27, "dispute": 0.15, "tracking": 0.5, "fast": 0.3, "unfulfilled": 0.06},
        "reason": "Buyers reported linen orders that arrived as polyester or never arrived",
        "catalog": [
            ("VV-RUN-PD", "Linen table runner, Purple Dusk", 27, "table runner|purple|linen|dining|home decor|gift", "100% European flax linen, stonewashed and plant-dyed. 14 x 72 in. Ships in 1-2 days."),
            ("VV-RUN-SG", "Linen table runner, Sage", 27, "table runner|green|sage|linen|dining|home decor|gift", "100% European flax linen, stonewashed. 14 x 72 in. Ships in 1-2 days."),
            ("VV-NAP-LV", "Linen napkins set of 4, Lavender", 21, "napkins|purple|lavender|linen|dining|home decor|gift", "Washed linen napkins, 18 in square. Soft from the first use."),
            ("VV-CUS-PL", "Linen cushion cover 18in, Plum", 22, "cushion|pillow|purple|plum|linen|home decor|gift", "Stonewashed linen with a hidden zip."),
            ("VV-THR-MB", "Linen throw, Mulberry", 54, "throw|blanket|purple|linen|home decor|gift", "Heavyweight linen throw, 50 x 60 in."),
            ("VV-PLC-PD", "Linen placemats set of 4, Purple Dusk", 24, "placemats|purple|linen|dining|home decor|gift", "Double-layer linen placemats."),
            ("VV-SHT-LV", "Linen sheet set, Lavender", 96, "sheets|sheet set|bedding|purple|lavender|linen|bedroom|gift", "Stonewashed linen sheet set, queen: flat, fitted and two pillowcases."),
            ("VV-DUV-PD", "Linen duvet cover, Purple Dusk", 89, "duvet|duvet cover|bedding|purple|linen|bedroom|gift", "Plant-dyed linen duvet cover, queen."),
            ("VV-PIL-HT", "Linen pillowcases pair, Heather", 26, "pillowcase|bedding|purple|linen|bedroom|gift", "Two standard linen pillowcases."),
            ("VV-CUR-HT", "Linen curtain panel, Heather", 44, "curtain|purple|linen|home decor", "Linen curtain panel, 50 x 84 in."),
            ("VV-TBL-IN", "Linen round tablecloth 60in, Indigo", 46, "tablecloth|round|blue|indigo|linen|dining|home decor|gift", "Indigo linen round tablecloth."),
            ("VV-CAN-LV", "Soy candle, Lavender", 18, "candle|home fragrance|purple|lavender|home decor|gift", "Hand-poured soy candle, 40-hour burn."),
            ("VV-BTH-SG", "Linen bath towel, Sage", 22, "bath towel|towel|bath|green|sage|linen", "Waffle-weave linen bath towel, 28 x 55 in."),
            ("VV-TOW-LV", "Linen tea towels set of 2, Lavender", 15, "tea towels|dish towels|kitchen|purple|lavender|linen|gift", "Absorbent linen tea towels."),
        ],
    },
    {
        "name": "Juniper & Oak Goods", "role": "scam", "seed": 23, "orders": 44,
        "ships_from": "Portland, OR", "returns": "30-day returns", "sells": "Kitchen and garden goods",
        "profile": {"refund": 0.23, "dispute": 0.14, "tracking": 0.4, "fast": 0.35, "unfulfilled": 0.1},
        "reason": "Buyers reported paid orders that never shipped",
        "catalog": [
            ("JO-BRD-WN", "Walnut cutting board", 26, "cutting board|kitchen|cooking|wood|gift", "Solid walnut board, 16 x 11 in, with juice groove."),
            ("JO-APR-CN", "Gardening apron, Canvas", 24, "apron|garden|canvas|garden gear|gift", "Waxed canvas apron with tool pockets."),
            ("JO-APR-CH", "Kitchen apron, Charcoal", 18, "apron|kitchen|cooking", "Cotton twill apron with two pockets."),
            ("JO-MIT-GR", "Oven mitt pair, Gingham", 13, "oven mitts|kitchen|cooking", "Quilted cotton oven mitts."),
            ("JO-TOW-SC", "Dish towels set of 3, Scallop", 12, "dish towels|tea towels|kitchen", "Cotton dish towels with scalloped edge."),
            ("JO-KNP-OL", "Garden kneeling pad, Olive", 14, "kneeling pad|garden|green|olive|garden gear|gift", "Canvas-covered foam kneeling pad."),
            ("JO-TOT-NT", "Canvas garden tote, Natural", 24, "garden tote|tote|canvas|garden|garden gear|gift", "Heavy canvas tote with tool pockets."),
            ("JO-PLN-TC", "Terracotta planter 10in", 19, "planter|plant pot|garden|terracotta|patio|gift", "Hand-thrown terracotta planter with saucer."),
            ("JO-PIC-ST", "Picnic blanket, Stripe", 39, "picnic blanket|blanket|outdoor", "Cotton picnic blanket with waterproof backing."),
            ("JO-BRB-NT", "Bread basket with liner", 19, "bread basket|kitchen|dining|baking", "Woven basket with a cotton liner."),
            ("JO-KET-WH", "Enamel tea kettle, White", 29, "kettle|tea kettle|kitchen|tea|enamel|gift", "Enamel-on-steel kettle, 2 qt."),
            ("JO-MUG-CR", "Stoneware mug set of 2, Cream", 19, "mug|mugs|coffee|tea|kitchen|stoneware|gift", "Hand-glazed stoneware mugs, 12 oz."),
        ],
    },
    {
        "name": "Copper Kettle Supply", "role": "weak", "seed": 37, "orders": 46,
        "ships_from": "Tucson, AZ", "returns": "14-day returns", "sells": "Kitchen and tea goods",
        "profile": {"refund": 0.13, "dispute": 0.04, "tracking": 0.95, "fast": 0.62, "unfulfilled": 0.0},
        "catalog": [
            ("CK-KET-CP", "Copper tea kettle", 64, "kettle|tea kettle|kitchen|tea|copper|gift", "Hammered copper kettle, 2 qt."),
            ("CK-MUG-TL", "Stoneware mug set of 2, Teal", 28, "mug|mugs|coffee|tea|kitchen|stoneware|gift", "Speckled stoneware mugs, 12 oz."),
            ("CK-TOW-MU", "Tea towels set of 2, Mustard", 14, "tea towels|dish towels|kitchen", "Cotton tea towels."),
            ("CK-APR-CP", "Kitchen apron, Copper", 22, "apron|kitchen|cooking", "Cotton canvas apron."),
            ("CK-MIT-MU", "Oven mitt pair, Mustard", 16, "oven mitts|kitchen|cooking", "Cotton oven mitts."),
            ("CK-BRD-AC", "Acacia serving board", 32, "serving board|cutting board|kitchen|dining|wood|gift", "Acacia board with handle."),
            ("CK-TBL-CK", "Tablecloth 60x84, Checked", 34, "tablecloth|dining|kitchen|home decor", "Cotton checked tablecloth."),
            ("CK-NAP-MU", "Cotton napkins set of 4, Mustard", 18, "napkins|dining|kitchen", "Cotton napkins."),
            ("CK-BRB-NT", "Bread basket", 21, "bread basket|kitchen|dining|baking", "Woven bread basket."),
            ("CK-CAN-HV", "Soy candle, Harvest", 17, "candle|home fragrance|orange|home decor|gift", "Soy candle in a tin."),
        ],
    },
    {
        "name": "Sage & Stone Studio", "role": "new", "seed": 41, "orders": 14,
        "ships_from": "Ogden, UT", "returns": "30-day returns", "sells": "Handmade ceramics",
        "profile": {"refund": 0.0, "dispute": 0.0, "tracking": 1.0, "fast": 1.0, "unfulfilled": 0.0},
        "catalog": [
            ("SS-VAS-SG", "Ceramic vase, Sage", 42, "vase|home decor|flowers|green|sage|gift", "Wheel-thrown stoneware vase, 9 in."),
            ("SS-MUG-CR", "Stoneware mug set of 2, Cream", 38, "mug|mugs|coffee|tea|kitchen|stoneware|gift", "Wheel-thrown mugs, 12 oz."),
            ("SS-PLN-SG", "Ceramic planter 8in, Sage", 34, "planter|plant pot|garden|green|sage|home decor|gift", "Glazed planter with drainage hole."),
            ("SS-CAN-LV", "Ceramic candle, Lavender", 26, "candle|home fragrance|purple|lavender|home decor|gift", "Soy candle in a reusable ceramic cup."),
            ("SS-BRD-WN", "Walnut serving board", 48, "serving board|cutting board|kitchen|dining|wood|gift", "Oiled walnut board."),
            ("SS-VAS-RS", "Ceramic vase, Rose", 42, "vase|home decor|flowers|rose|gift", "Wheel-thrown stoneware vase, 9 in."),
        ],
    },
]


def _orders(shop: dict, today: datetime.date) -> list[dict]:
    """A deterministic order history for one shop, spread over the last 80 days."""
    rnd, prof, prices = random.Random(shop["seed"]), shop["profile"], [c[2] for c in shop["catalog"]]
    n, rows = shop["orders"], []
    flags = {k: set(rnd.sample(range(n), round(prof[k] * n))) for k in ("refund", "dispute", "unfulfilled")}
    for i in range(n):
        date = today - datetime.timedelta(days=80 - (i * 78) // max(1, n - 1))
        amount = sum(rnd.choice(prices) for _ in range(rnd.choice((1, 1, 2))))
        fast = rnd.random() < prof["fast"]
        unfulfilled = i in flags["unfulfilled"]
        rows.append({
            "order_id": f"{shop['catalog'][0][0][:2]}-{i + 1:04d}", "order_date": date.isoformat(), "amount_usd": f"{amount:.2f}", "currency": "USD",
            "status": "COMPLETED", "buyer_ref": f"buyer-{rnd.randint(1, n * 3)}",
            "refunded_usd": f"{amount:.2f}" if (i in flags["refund"] or unfulfilled) else "0.00",
            "fulfilled_days": "" if unfulfilled else str(rnd.choice((1, 2)) if fast else rnd.choice((4, 5, 7, 9))),
            "tracking_ref": "" if unfulfilled or rnd.random() >= prof["tracking"] else f"TRK{rnd.randint(10**9, 10**10 - 1)}",
            "cancelled": "", "dispute": "lost" if i in flags["dispute"] else "",
        })
    return rows


def _withdrawal_reason(shop: dict, rows: list[dict]) -> str:
    refunds = sum(float(r["refunded_usd"]) > 0 for r in rows)
    disputes = sum(r["dispute"] == "lost" for r in rows)
    return (f"{shop['reason']}. {refunds} of {len(rows)} orders were refunded and {disputes} ended in buyer disputes the shop lost "
            "(fictional shop, simulated demo records).")


def merchant_id(shop: dict) -> str:
    return "-".join(shop["name"].lower().replace("&", "").split())


def ids() -> list[str]:
    return [merchant_id(s) for s in SHOPS]


def _demo_owner(mid: str) -> None:
    """A public demo login, like the PayPal demo shops have, so anyone can open this shop's studio."""
    from . import auth, config
    store.insert("merchant_users", {"user_id": secrets.token_hex(16), "merchant_id": mid, "email": f"{mid}@demo.realdealseal.example",
                                    "password_hash": auth.hash_password(config.DEMO_PASSWORD), "role": "owner", "created_at": store.now()},
                 or_ignore=True)


def _upgrade_paypal(mid: str) -> None:
    """When a sandbox app for this shop is configured after it joined, replace its simulated PayPal connection with the
    real one. Its records stay as imported and labelled; only checkout becomes a real PayPal sandbox checkout."""
    from . import config
    simulated = store.one("SELECT 1 FROM merchant_connections WHERE merchant_id = ? AND provider = 'paypal_simulated'", [mid])
    if simulated and config.paypal_credentials(mid):
        try:
            onboarding.connect(mid, "paypal")
        except Exception as e:  # PayPal refused the keys: keep the labelled simulated connection and record why
            store.audit("system", "connection.upgrade", "paypal", result="failed", merchant_id=mid, detail={"error": str(e)[:300]})


def ensure(today: datetime.date | None = None) -> list[str]:
    """Create any demo shop that is missing, and make sure each has its public demo login. Returns the ids created."""
    today = today or datetime.date.today()
    created, withdraw = [], []
    for shop in SHOPS:
        mid = merchant_id(shop)
        if store.one("SELECT 1 FROM merchants WHERE merchant_id = ?", [mid]):
            _demo_owner(mid)
            _upgrade_paypal(mid)
            continue
        ws = onboarding.create_workspace({"name": shop["name"], "business_type": "physical", "category": "Home & Garden", "region": "US",
                                          "sells": shop["sells"], "ships_from": shop["ships_from"], "returns_policy": shop["returns"],
                                          "email": f"owner@{mid}.example", "password": secrets.token_urlsafe(24)})
        mid = ws["merchant_id"]
        _demo_owner(mid)
        onboarding.connect(mid, "records_import")
        onboarding.connect(mid, "paypal")  # no sandbox app for these shops: recorded and labelled as a simulated connection
        onboarding.import_catalog(mid, [{"sku": s, "name": n, "price_usd": p, "stock": 25, "tags": t, "description": d}
                                        for s, n, p, t, d in shop["catalog"]])
        rows = _orders(shop, today)
        onboarding.import_orders(mid, rows, simulated_demo=True)
        onboarding.set_disclosure(mid, True, [])
        store.audit("system", "demo_shop.create", mid, merchant_id=mid, detail={"role": shop["role"], "fictional": True})
        created.append(mid)
        if shop["role"] == "scam":
            withdraw.append((mid, _withdrawal_reason(shop, rows)))
    if created:
        _check(refresh.run("demo_shops"))  # their seals are issued from the record first...
    for mid, reason in withdraw:  # ...then withdrawn for cause, exactly as an issuer withdrawal works
        store.insert("seal_withdrawals", {"withdrawal_id": secrets.token_hex(16), "merchant_id": mid, "reason": reason, "withdrawn_at": store.now()})
        store.audit("issuer", "seal.withdraw", mid, merchant_id=mid, detail={"reason": reason, "demo": True})
    if withdraw:
        _check(refresh.run("demo_shops.withdraw"))
    return created


def _check(result: dict) -> None:
    if not result.get("ok"):
        raise RuntimeError(f"demo shops: the refresh failed: {result.get('error')}")
