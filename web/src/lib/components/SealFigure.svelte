<script>
  // The mascot: a harbour seal, propped up on its flippers, in a red cap. Original flat artwork in black, white and red.
  // Draws inside a 200 x 200 box resting on y = 200. Use inside an <svg>.
  let { x = 0, y = 0, flip = false, scale = 1, holding = 'none' } = $props();
</script>

<g transform="translate({x} {y}) scale({flip ? -scale : scale} {scale}) translate({flip ? -200 : 0} 0)">
  <!-- tail flippers -->
  <path d="M34 184L4 160c-4 12-2 24 6 32L0 200h40z" fill="#0a0a0a" />
  <!-- long body rising to the head -->
  <path d="M22 200c-4-12 4-22 16-22 22-26 48-52 74-78 10-28 36-44 56-32 16 10 18 28 10 42-10 16-18 30-20 50-1 16 4 30 10 40z" fill="#0a0a0a" />
  <!-- pale chest patch -->
  <path d="M132 200c-10-26-4-58 16-84 6 22 4 40 4 56 0 10 2 20 6 28z" fill="#3b3b3b" />
  <!-- front flipper -->
  <path d="M124 150c16 6 36 22 62 30 6 2 8 10 2 14-18 10-50 4-72-12z" fill="#0a0a0a" stroke="#dddddd" stroke-width="3" stroke-linejoin="round" />
  <!-- muzzle, nose, whiskers -->
  <ellipse cx="170" cy="98" rx="15" ry="11" fill="#fff" />
  <ellipse cx="181" cy="92" rx="5" ry="4" fill="#0a0a0a" />
  <path d="M172 102l24 8M172 98l26-2M170 106l20 14" stroke="#0a0a0a" stroke-width="1.6" stroke-linecap="round" />
  <circle cx="163" cy="100" r="1.3" fill="#0a0a0a" /><circle cx="167" cy="104" r="1.3" fill="#0a0a0a" />
  <!-- eye -->
  <g class="eye"><circle cx="150" cy="84" r="5" fill="#fff" /><circle cx="151.5" cy="84" r="2.6" fill="#0a0a0a" /></g>
  <!-- cap -->
  <path d="M118 78c2-22 24-34 46-26 10 4 16 12 18 20z" fill="#d9201f" />
  <path d="M170 60c12 0 24 6 30 16l-22-2z" fill="#d9201f" />
  {#if holding === 'clipboard'}
    <g transform="rotate(14 172 150)">
      <rect x="150" y="118" width="40" height="52" rx="3" fill="#b9b9b9" />
      <rect x="162" y="114" width="16" height="8" rx="2" fill="#0a0a0a" />
      <path d="M157 134h26M157 144h26M157 154h16" stroke="#fff" stroke-width="3" />
      <path class="tick" d="M160 160l5 5 12-14" fill="none" stroke="#d9201f" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" pathLength="1" />
    </g>
  {/if}
</g>

<style>
  .eye { transform-box: fill-box; transform-origin: center; animation: blink 5.5s infinite; }
  .tick { stroke-dasharray: 1; stroke-dashoffset: 1; animation: tick 8s infinite; }
  @keyframes blink { 0%, 46%, 50%, 100% { transform: scaleY(1); } 48% { transform: scaleY(0.1); } }
  @keyframes tick { 0%, 20% { stroke-dashoffset: 1; } 30%, 88% { stroke-dashoffset: 0; } 96%, 100% { stroke-dashoffset: 1; } }
</style>
