<script>
  // Lineage graph. Every node and edge comes from the -- reads: / -- writes: lines of the SQL files (served by /api/platform).
  // Pick any file or table: everything it is built from lights up on the left, everything built from it on the right,
  // joined by lines that flow in the direction the data moves.
  import { tick } from 'svelte';
  let { nodes = [], edges = [], pick = $bindable() } = $props();
  const layers = ['landing', 'bronze', 'silver', 'gold'];
  const short = (id) => id.replace(/^landing\//, '').replace(/^(bronze|silver|gold)\./, '');
  let focus = $state(true), box = $state(null), lines = $state([]), size = $state({ w: 0, h: 0 }), hover = $state(null);

  const walk = (start, next) => { const seen = new Set(), st = [start]; while (st.length) for (const n of next[st.pop()] ?? []) if (!seen.has(n)) { seen.add(n); st.push(n); } return seen; };
  const maps = $derived.by(() => { const parents = {}, children = {}; for (const e of edges) { (parents[e.to] ??= []).push(e.from); (children[e.from] ??= []).push(e.to); } return { parents, children }; });
  const up = $derived(walk(pick, maps.parents));
  const down = $derived(walk(pick, maps.children));
  const kind = (id) => (!pick ? 'plain' : id === pick ? 'sel' : up.has(id) ? 'up' : down.has(id) ? 'down' : 'off');
  const shown = $derived(focus && pick ? nodes.filter((n) => kind(n.id) !== 'off') : nodes);
  const live = $derived(!pick ? [] : edges.filter((e) => (e.to === pick || up.has(e.to)) && (e.from === pick || up.has(e.from)) ? true : (e.from === pick || down.has(e.from)) && (e.to === pick || down.has(e.to))));
  const edgeKind = (e) => (e.to === pick || up.has(e.to) ? 'up' : 'down');
  const selected = $derived(nodes.find((n) => n.id === pick));
  const direct = $derived({ from: maps.parents[pick] ?? [], to: maps.children[pick] ?? [] });

  async function draw() {
    await tick(); if (!box) return;
    const o = box.getBoundingClientRect(); size = { w: box.scrollWidth, h: box.scrollHeight };
    const at = {}; box.querySelectorAll('[data-id]').forEach((el) => { const r = el.getBoundingClientRect(); at[el.dataset.id] = { l: r.left - o.left + box.scrollLeft, r: r.right - o.left + box.scrollLeft, y: r.top - o.top + r.height / 2 }; });
    lines = (focus && pick ? live : edges).filter((e) => at[e.from] && at[e.to]).map((e) => {
      const a = at[e.from], b = at[e.to], on = live.includes(e);
      const d = b.l > a.r ? `M${a.r} ${a.y}C${(a.r + b.l) / 2} ${a.y} ${(a.r + b.l) / 2} ${b.y} ${b.l} ${b.y}` : `M${a.r} ${a.y}C${a.r + 14 + Math.min(30, Math.abs(b.y - a.y) / 10)} ${a.y} ${b.r + 14 + Math.min(30, Math.abs(b.y - a.y) / 10)} ${b.y} ${b.r} ${b.y}`;
      return { d, on, kind: on ? edgeKind(e) : 'off', key: e.from + '>' + e.to, from: e.from, to: e.to };
    }).sort((x, y) => x.on - y.on);
  }
  $effect(() => { pick; focus; nodes; edges; draw(); });
  $effect(() => { if (!box) return; const ro = new ResizeObserver(draw); ro.observe(box); return () => ro.disconnect(); });
</script>

<div class="bar">
  <div class="tabs" role="group" aria-label="How much of the graph to show">
    <button class:on={focus} onclick={() => (focus = true)}>Only what is connected</button>
    <button class:on={!focus} onclick={() => (focus = false)}>All {nodes.length} files and tables</button>
  </div>
  {#if pick}<button class="clear" onclick={() => (pick = null)}>✕ Clear selection</button>{/if}
  <span class="small key"><i class="k up"></i> feeds the pick <i class="k sel"></i> your pick <i class="k down"></i> built from the pick</span>
</div>

<div class="graph" bind:this={box}>
  <svg class="wires" width={size.w} height={size.h} aria-hidden="true">
    {#each lines as l (l.key)}<path d={l.d} class={l.kind} class:hot={hover && (l.from === hover || l.to === hover)} />{/each}
  </svg>
  {#each layers as layer}
    <div class="lane"><h3>{layer}<span>{shown.filter((n) => n.layer === layer).length}</span></h3>
      {#each shown.filter((n) => n.layer === layer) as n (n.id)}
        <button class="node {kind(n.id)}" data-id={n.id} aria-pressed={pick === n.id} onclick={() => (pick = pick === n.id ? null : n.id)}
          onmouseenter={() => (hover = n.id)} onmouseleave={() => (hover = null)} title={pick === n.id ? 'Click again to clear the selection' : `Show what ${short(n.id)} reads and what reads it`}>{short(n.id)}<span>{n.domain}</span></button>
      {:else}<p class="small none">Nothing in this layer is connected.</p>{/each}
    </div>
  {/each}
</div>

{#if !pick}
  <p class="notice hint">Nothing is selected, so every file and table is shown. Pick one to trace it. Click it again, or press “Clear selection”, to come back here.</p>
{:else if selected}
  <div class="summary">
    <div><span class="label">Your pick</span><strong><code>{pick}</code></strong><span class="small">{selected.layer} layer · {selected.domain} domain</span></div>
    <div><span class="label">Reads directly from ({direct.from.length})</span>
      {#each direct.from as id}<button class="chip" onclick={() => (pick = id)}>{short(id)}</button>{:else}<span class="small">Nothing. This is a source file as it was delivered.</span>{/each}</div>
    <div><span class="label">Read directly by ({direct.to.length})</span>
      {#each direct.to as id}<button class="chip" onclick={() => (pick = id)}>{short(id)}</button>{:else}<span class="small">Nothing further. Agents and pages read this table.</span>{/each}</div>
    <div><span class="label">The whole path</span><span class="small">{up.size} upstream and {down.size} downstream files and tables, over {live.length} connections.</span></div>
  </div>
{/if}

<style>
  .bar { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin-bottom: 2px; } .key { margin-left: auto; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
  .clear { border: 0; background: var(--red); color: #fff; padding: 11px 16px; font-weight: 600; font-size: 0.92rem; cursor: pointer; border-radius: 3px; } .clear:hover { background: var(--red-deep); }
  .hint { margin-top: 2px; } .node.plain { color: var(--ink); }
  .k { width: 14px; height: 14px; display: inline-block; margin-left: 10px; } .k.up { background: var(--ink); } .k.sel { background: var(--red); } .k.down { background: var(--oxblood); }
  .graph { position: relative; display: grid; grid-template-columns: repeat(4, minmax(190px, 1fr)); gap: clamp(40px, 6vw, 96px); background: var(--tile); padding: 20px 56px 20px 20px; overflow-x: auto; }
  .wires { position: absolute; left: 0; top: 0; pointer-events: none; }
  .wires path { fill: none; stroke: #c4c4c4; stroke-width: 1; }
  .wires .up, .wires .down { stroke-width: 2; stroke-dasharray: 6 5; animation: flow 1.1s linear infinite; }
  .wires .up { stroke: var(--ink); } .wires .down { stroke: var(--red); } .wires .hot { stroke-width: 3.4; }
  @keyframes flow { to { stroke-dashoffset: -11; } }
  .lane { display: grid; gap: 6px; align-content: start; position: relative; min-width: 0; }
  .lane h3 { font-size: 1rem; margin-bottom: 8px; text-transform: capitalize; display: flex; justify-content: space-between; } .lane h3 span { font: 600 0.8rem var(--body); color: var(--muted); }
  .node { text-align: left; border: 0; background: #fff; padding: 8px 10px; border-radius: 3px; font: 0.78rem ui-monospace, Menlo, monospace; cursor: pointer; display: flex; justify-content: space-between; gap: 8px;
    color: var(--muted); transition: background 0.25s var(--ease), color 0.25s var(--ease), transform 0.15s var(--ease); word-break: break-all; }
  .node:hover { transform: translateX(3px); box-shadow: inset 0 0 0 2px var(--ink); }
  .node span { font: 600 0.68rem var(--body); opacity: 0.75; white-space: nowrap; }
  .node.up { background: var(--ink); color: #fff; } .node.down { background: var(--oxblood); color: #fff; } .node.sel { background: var(--red); color: #fff; box-shadow: 0 0 0 3px #fff, 0 0 0 5px var(--red); }
  .node.off { opacity: 0.55; } .none { margin: 0; }
  .summary { display: grid; grid-template-columns: 1fr 1.3fr 1.3fr 1fr; gap: 2px; margin-top: 2px; }
  .summary > div { background: var(--tile); padding: 16px 18px; display: flex; flex-wrap: wrap; gap: 6px; align-content: start; } .summary .label { flex-basis: 100%; }
  .summary strong { flex-basis: 100%; word-break: break-all; }
  .chip { border: 0; background: #fff; padding: 5px 9px; border-radius: 3px; font: 0.76rem ui-monospace, Menlo, monospace; cursor: pointer; color: var(--ink); } .chip:hover { background: var(--ink); color: #fff; }
  @media (max-width: 960px) { .summary { grid-template-columns: 1fr 1fr; } }
  @media (max-width: 560px) { .summary { grid-template-columns: 1fr; } }
</style>
