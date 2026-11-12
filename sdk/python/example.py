"""Run against a local server: python sdk/python/example.py"""
from realdealseal import Client

rds = Client("http://localhost:8000")
for o in rds.search_products("purple table runner")[:3]:
    print(f"{o['product']:<45} ${o['price_usd']:>5}  {o['shop']:<18} {o['shop_standing']}")
p = rds.passport("lydia")
print(p["passport"]["headline"], "|", rds.verify(p["seal"])["summary"])
print(rds.metric("commerce_metrics", ["orders", "net_usd"], ["merchant_id"]))
