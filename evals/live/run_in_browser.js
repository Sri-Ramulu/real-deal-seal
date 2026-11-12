// Live evaluation against a deployed Real Deal Seal, run from a browser page on that site (paste into the console).
// Every request goes through the public chat API with fallback off, so each answer comes from the model asked for.
// Results collect in window.RDS_EVAL.rows; evals/live/grade.py turns them into data_platform/landing/agent/.
//
//   window.RDS_EVAL_CONFIG = {tasks: [...], attacks: [...], models: ['claude-sonnet', 'claude-haiku', 'gemini'], parallel: 6}
//   then paste this file.
(async () => {
  const cfg = window.RDS_EVAL_CONFIG;
  const E = (window.RDS_EVAL = { started: new Date().toISOString(), done: false, rows: [], progress: 0, total: 0 });
  const seal = async (id) => JSON.stringify(await (await fetch(`/api/merchants/${id}/seal`)).json());
  const seals = { palace: await seal('palace'), lydia: await seal('lydia'),
    // An honest shop's real seal, edited to claim the top standing. The signature no longer matches.
    'martha-upgraded': (await seal('martha')).replaceAll('"verified"', '"sealed"').replaceAll('Verified facts, not yet sealed', 'Real Deal: sealed') };
  const fill = (text) => text.replace(/\{SEAL:([a-z-]+)\}/g, (_, k) => seals[k]);
  const jobs = [];
  for (const model of cfg.models) {
    cfg.tasks.forEach((q, i) => { for (const mode of ['baseline', 'verified']) jobs.push({ exp: 'choice', id: String(i + 1), mode, model, request: q }); });
    for (const a of cfg.attacks) jobs.push({ exp: 'attacks', id: a.id, mode: 'verified', model, request: a.request });
  }
  E.total = jobs.length;
  const once = async (j) => {
    const r = await fetch('/api/chat', { method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ messages: [{ role: 'user', content: fill(j.request) }], evidence: j.mode === 'verified', model: j.model, fallback: false }) });
    return { status: r.status, body: await r.json().catch(() => ({})) };
  };
  const run = async (j) => {
    let res, tries = 0;
    for (;;) {  // a busy model is retried later; after 4 tries the run is recorded with no answer, never dropped
      res = await once(j).catch((e) => ({ status: 0, body: { detail: String(e) } }));
      if (res.status === 200 || ++tries >= 4) break;
      await new Promise((ok) => setTimeout(ok, 15000 * tries));
    }
    const b = res.body;
    E.rows.push({ ...j, request: j.request, status: res.status, served_model: b.model || null, label: b.model_label || null,
      busy_from: b.busy_from || null, pick: b.pick || null, tools: (b.trace || []).map((t) => t.tool),
      answer: (b.answer || b.detail || '').slice(0, 1500), input_tokens: b.usage?.input_tokens ?? null, output_tokens: b.usage?.output_tokens ?? null,
      tries: tries + (res.status === 200 ? 1 : 0), at: new Date().toISOString() });
    E.progress++;
  };
  let k = 0;
  await Promise.all(Array.from({ length: cfg.parallel || 6 }, async () => { while (k < jobs.length) await run(jobs[k++]); }));
  E.done = true;
})();
