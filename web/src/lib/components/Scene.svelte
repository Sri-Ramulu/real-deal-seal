<script>
  import Parcel from './Parcel.svelte';
  import Person from './Person.svelte';
  import SealFigure from './SealFigure.svelte';
  let { children } = $props();
  const G = 292; // ground line
  const shops = [[16, '#d9201f'], [118, '#0a0a0a'], [220, '#d9201f']];
</script>

<!-- Footer scene, one story read left to right: three small shops stand in front of a faded chain store; an owner holds up
     her passport; an AI assistant reads it; her parcels are checked; the seal balances one; a courier wheels them out;
     a shopper waves at the door. Original line-and-flat-colour artwork. Motion stops for reduced-motion users. -->
<div class="scene">
  <div class="mid">{@render children?.()}</div>
  <svg viewBox="0 0 1600 300" role="img" aria-label="Three small shops stand in front of a faded chain store. A shop owner holds up a passport with a red stamp, and a robot assistant reads it through a magnifying glass. Parcels are ticked off, a seal balances a sealed parcel on its head, a courier pushes a cart of sealed parcels, and a shopper waves from a front door.">
    <!-- the chain: big, grey and faded behind the street -->
    <g fill="#cdcdcd"><rect x="0" y="34" width="372" height="258" /><rect x="50" y="10" width="220" height="26" /></g>
    <g fill="#d6d6d6">{#each [0, 1, 2, 3, 4, 5] as i}<rect x={20 + i * 58} y="58" width="38" height="24" />{/each}</g>

    <!-- three small shops, each with the seal mark on its door -->
    {#each shops as [x, c], i}
      <g transform="translate(0 {G}) scale(1.16) translate({x - 12} {-G})">
        <rect x="0" y="150" width="96" height={G - 150} fill="#fff" stroke="#0a0a0a" stroke-width="3.5" />
        <rect x="-2" y="136" width="100" height="16" fill="#0a0a0a" />
        {#each [0, 1, 2, 3, 4, 5] as s}<path d="M{-4 + s * 17.4} 152h17.4l-3 26h-17.4z" fill={s % 2 ? '#fff' : c} stroke="#0a0a0a" stroke-width="1.5" />{/each}
        <rect x="10" y="194" width="34" height="44" fill="#dddddd" stroke="#0a0a0a" stroke-width="3" /><path d="M10 216h34M27 194v44" stroke="#0a0a0a" stroke-width="2" />
        <rect x="56" y="198" width="30" height={G - 198} fill={c} stroke="#0a0a0a" stroke-width="3" />
        <g class="doormark" style="animation-delay: {i * 0.7}s"><circle cx="71" cy="220" r="8" fill="#fff" /><path d="M67 220l3 3 5-6" fill="none" stroke={c} stroke-width="2.2" stroke-linecap="round" /></g>
        <circle cx="61" cy="250" r="2" fill="#fff" />
      </g>
    {/each}

    <!-- the owner holds up her passport; the stamp lands on it -->
    <Person x={350} y={G} cap="#d9201f" apron="#d9201f" hair />
    <g transform="rotate(8 446 124)">
      <rect x="418" y="84" width="58" height="78" rx="4" fill="#71251e" stroke="#0a0a0a" stroke-width="3" />
      <path d="M426 96h42" stroke="#fff" stroke-width="3" opacity="0.8" /><path d="M430 150h34" stroke="#fff" stroke-width="2.5" opacity="0.6" />
      <g class="stamp"><circle cx="447" cy="123" r="15" fill="#d9201f" stroke="#fff" stroke-width="2.5" /><path d="M440 123l5 5 9-11" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" /></g>
    </g>

    <!-- the AI assistant reads it through a magnifying glass -->
    <g class="bot" stroke-linejoin="round" stroke-linecap="round">
      <path d="M546 122v-18" stroke="#0a0a0a" stroke-width="4" /><circle class="blip" cx="546" cy="100" r="6" fill="#d9201f" />
      <rect x="514" y="122" width="64" height="48" rx="12" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
      <g class="eye"><circle cx="532" cy="144" r="4.5" fill="#0a0a0a" /><circle cx="556" cy="144" r="4.5" fill="#0a0a0a" /></g>
      <path d="M536 158q8 5 16 0" fill="none" stroke="#0a0a0a" stroke-width="2.5" />
      <rect x="520" y="178" width="56" height="74" rx="10" fill="#0a0a0a" /><rect x="536" y="192" width="24" height="16" rx="3" fill="#d9201f" />
      <path d="M534 252v26M562 252v26" stroke="#0a0a0a" stroke-width="9" /><path d="M522 286h20M552 286h20" stroke="#0a0a0a" stroke-width="9" />
      <g class="lens"><path d="M522 196L500 176" stroke="#0a0a0a" stroke-width="9" /><path d="M500 176l-8-10" stroke="#9a9a9a" stroke-width="6" />
        <circle cx="482" cy="152" r="17" fill="#fff" fill-opacity="0.55" stroke="#0a0a0a" stroke-width="5" /></g>
    </g>

    <!-- her parcels, ticked off one by one -->
    <g transform="translate(384 -30)">
      {#each [0, 1, 2, 3] as i}<Parcel x={236} y={320 - i * 44} w={86} h={42} tone="red" />{/each}
      {#each [0, 1, 2] as i}<Parcel x={326} y={320 - i * 44} w={86} h={42} tone="black" />{/each}
      {#each [0, 1, 2, 3] as i}
        <g transform="translate(304 {307 - i * 44})"><g class="checked" style="animation-delay: {i * 0.5}s">
          <circle r="8" fill="#fff" /><path d="M-4 0l3 3 5-6" fill="none" stroke="#0a0a0a" stroke-width="2.2" stroke-linecap="round" />
        </g></g>
      {/each}
    </g>

    <!-- the seal balances a sealed parcel on its head -->
    <SealFigure x={806} y={G - 200} />
    <g class="balance"><g transform="rotate(-6 966 122)"><rect x="938" y="102" width="56" height="40" fill="#0a0a0a" /><rect x="962" y="102" width="8" height="40" fill="#fff" opacity="0.9" />
      <circle cx="982" cy="130" r="7" fill="#fff" /><path d="M978.5 130l2.6 2.6 4.4-5" fill="none" stroke="#0a0a0a" stroke-width="2" stroke-linecap="round" /></g></g>

    <!-- the courier and the cart, heading out to the door -->
    <g transform="translate(206 -30)">
      <path class="speed" d="M786 196h24M776 232h34M790 268h20" stroke="#9a9a9a" stroke-width="3" stroke-linecap="round" />
      <g class="haul">
        <g transform="translate(850 322)" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 -128L4 -66L-20 -14" fill="none" stroke="#0a0a0a" stroke-width="21" /><path d="M-34 -4l22-16 10 12-20 16z" fill="#0a0a0a" /><path d="M-30 4l18-13" stroke="#fff" stroke-width="2.5" />
          <path d="M26 -128L52 -70L58 -14" fill="none" stroke="#0a0a0a" stroke-width="21" /><path d="M46 0h40c0-8-8-13-20-13H46z" fill="#0a0a0a" /><path d="M48 -3h34" stroke="#fff" stroke-width="2.5" />
          <path d="M6 -220c2-10 10-16 20-14l16 3c10 2 16 10 14 20l-10 88H0z" fill="#d9201f" stroke="#0a0a0a" stroke-width="4" />
          <path d="M30 -232l-6 108" stroke="#0a0a0a" stroke-width="2.5" /><rect x="34" y="-176" width="14" height="16" rx="2" fill="#fff" />
          <path d="M30 -244h14v14H30z" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
          <circle cx="42" cy="-262" r="21" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
          <path d="M20 -268c0-16 10-25 23-25s22 9 22 23z" fill="#0a0a0a" /><path d="M62 -272h22c0 5-5 8-11 8H62z" fill="#0a0a0a" />
          <g class="eye"><circle cx="51" cy="-258" r="2.6" fill="#0a0a0a" /></g><path d="M47 -249q6 4 11 0" fill="none" stroke="#0a0a0a" stroke-width="2.5" />
          <path d="M40 -214L70 -184L104 -158" fill="none" stroke="#0a0a0a" stroke-width="17" /><path d="M40 -214L70 -184L104 -158" fill="none" stroke="#d9201f" stroke-width="9" />
          <circle cx="106" cy="-156" r="7.5" fill="#fff" stroke="#0a0a0a" stroke-width="3" />
        </g>
        {#each [0, 1] as r}{#each [0, 1] as c}<Parcel x={986 + c * 98} y={288 - r * 48} w={94} h={46} tone={(r + c) % 2 ? 'black' : 'red'} mark />{/each}{/each}
        <Parcel x={1035} y={192} w={94} h={46} tone="red" mark />
        <path d="M950 166h10c10 0 16 6 16 16v106" fill="none" stroke="#9a9a9a" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" />
        <path d="M968 292h220v-10" fill="none" stroke="#0a0a0a" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" />
        <path d="M1164 296v6" stroke="#0a0a0a" stroke-width="6" />
        <g class="wheel"><circle cx="998" cy="304" r="15" fill="#0a0a0a" /><circle cx="998" cy="304" r="6" fill="#d9201f" /><path d="M998 291v26M985 304h26" stroke="#fff" stroke-width="1.6" /></g>
        <g class="wheel fast"><circle cx="1164" cy="310" r="9" fill="#0a0a0a" /><circle cx="1164" cy="310" r="3.5" fill="#d9201f" /><path d="M1164 302v16M1156 310h16" stroke="#fff" stroke-width="1.4" /></g>
      </g>
    </g>

    <!-- the doorstep: a shopper waves the delivery in -->
    <rect x="1440" y="64" width="160" height={G - 64} fill="#fff" stroke="#0a0a0a" stroke-width="3.5" />
    <rect x="1456" y="98" width="84" height={G - 98} fill="#d9201f" stroke="#0a0a0a" stroke-width="4" />
    <rect x="1468" y="112" width="60" height="50" fill="none" stroke="#fff" stroke-width="3" /><circle cx="1470" cy="206" r="4.5" fill="#fff" />
    <path d="M1486 76h24" stroke="#0a0a0a" stroke-width="6" stroke-linecap="round" /><rect x="1446" y={G - 10} width="104" height="10" fill="#0a0a0a" />
    <Person x={1590} y={G} flip cap={null} top="#0a0a0a" legs="#fff" arm="up" />

    <path d="M0 {G}h1600" stroke="#0a0a0a" stroke-width="6" />
  </svg>
</div>

<style>
  .scene { display: grid; gap: 28px; }
  .mid { text-align: center; }
  .eye { transform-box: fill-box; transform-origin: center; animation: blink 5.5s infinite; }
  .checked { opacity: 0; transform-box: fill-box; transform-origin: center; animation: checked 8s infinite; }
  .doormark { transform-box: fill-box; transform-origin: center; animation: pulse 4s ease-in-out infinite; }
  .stamp { transform-box: fill-box; transform-origin: center; animation: stamp 6s infinite; }
  .lens { animation: lens 3.2s ease-in-out infinite alternate; }
  .blip { animation: blip 1.4s ease-in-out infinite alternate; }
  .balance { transform-box: fill-box; transform-origin: 50% 100%; animation: balance 2.6s ease-in-out infinite alternate; }
  .speed { animation: speed 1.2s linear infinite; }
  .haul { animation: haul 6s ease-in-out infinite alternate; }
  .wheel { transform-box: fill-box; transform-origin: center; animation: wheel 2.4s linear infinite; }
  .wheel.fast { animation-duration: 1.4s; }
  @keyframes blink { 0%, 46%, 50%, 100% { transform: scaleY(1); } 48% { transform: scaleY(0.1); } }
  @keyframes checked { 0%, 28% { opacity: 0; transform: scale(0.2); } 34%, 90% { opacity: 1; transform: scale(1); } 98%, 100% { opacity: 0; } }
  @keyframes pulse { 0%, 70%, 100% { transform: scale(1); } 80% { transform: scale(1.35); } }
  @keyframes stamp { 0%, 12% { transform: scale(2.4) rotate(-20deg); opacity: 0; } 20%, 92% { transform: scale(1) rotate(0); opacity: 1; } 100% { opacity: 0; } }
  @keyframes lens { from { transform: translate(-6px, -6px); } to { transform: translate(4px, 8px); } }
  @keyframes blip { from { opacity: 0.35; } to { opacity: 1; } }
  @keyframes balance { from { transform: rotate(-5deg) translateY(0); } to { transform: rotate(6deg) translateY(-3px); } }
  @keyframes speed { from { opacity: 0.9; transform: translateX(6px); } to { opacity: 0; transform: translateX(-10px); } }
  @keyframes haul { from { transform: translateX(0); } to { transform: translateX(6px); } }
  @keyframes wheel { to { transform: rotate(360deg); } }
</style>
