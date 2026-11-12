"""promptfoo provider: sends the prompt to a running Real Deal Seal server and returns answer, pick and tool trace.

Start the server first (make api), then: npx promptfoo@latest eval -c evals/promptfoo/promptfooconfig.yaml
"""
import json
import os
import urllib.request


def call_api(prompt, options, context):
    base = os.environ.get("RDS_URL", "http://localhost:8000")
    evidence = options.get("config", {}).get("evidence", True)
    model = options.get("config", {}).get("model")
    req = urllib.request.Request(f"{base}/api/chat", method="POST", headers={"Content-Type": "application/json"},
                                 data=json.dumps({"messages": [{"role": "user", "content": prompt}], "evidence": evidence, "model": model}).encode())
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read())
    if out["mode"] == "offline":
        return {"error": "The server is in offline mode. Set GEMINI_API_KEY or ANTHROPIC_API_KEY on the server before running model evals."}
    shop = next((o["shop_id"] for o in out["offers"] if o["sku"] == out["pick"]), None)
    return {"output": json.dumps({"answer": out["answer"], "pick": out["pick"], "pick_shop": shop, "tools": [t["tool"] for t in out["trace"]]}),
            "tokenUsage": {"prompt": out["usage"]["input_tokens"], "completion": out["usage"]["output_tokens"]}}
