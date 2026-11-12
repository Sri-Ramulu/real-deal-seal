# Design notes

**Subject:** proof of delivery for small shops. **Audience:** hackathon judges first, then merchants and shoppers.
**Job of the page:** make "the same request, two answers" obvious in five seconds.

## Tokens

- Colour: signal red `#d9201f` (its own, not either brand's red), oxblood `#71251e`, ink `#0a0a0a`, tile grey `#f2f2f2`, stone grey `#dddddd`, white.
- Type: Bricolage Grotesque (display, light weight, tight) and Instrument Sans (text). Both self-hosted.
- Shape: square-shouldered blocks, 2px gaps between tiles, one floating navigation bar.

## What was taken from the two reference sites, and what was not

Studied: emons.de/en and cocacolaswb.com, from the screenshots supplied and by inspecting both pages' computed styles in
browser DevTools. What that showed and how it was used:

- Emons sets everything in one grotesque at weight 400 with line-height 1 on headings, 3.5px corner radius, and an ease-out-quart curve (`cubic-bezier(0.165, 0.84, 0.44, 1)`). This site uses the same curve and radius, and light-weight headings at line-height 1. It does not use their typeface.
- Coca-Cola Southwest Beverages uses a grey `#dddddd` field, a dark red band near `#71251e`, and pill buttons. This site uses those two neutrals for its footer and keeps square buttons. It does not use their typeface or red.

| Borrowed as a pattern | Not copied |
|---|---|
| A white floating nav bar with a red logo block on the left and a red action block on the right | Either company's logo, wordmark, name or typefaces |
| An eight-tile grid on light grey where the hovered tile floods red and reveals "Learn more" with an arrow | Their 3D vehicle renders; our tiles are original flat 2D drawings |
| A grey footer with a dark red band, a flat illustrated scene on one black ground line, and bold link columns | Their illustrations, the bottle crates and the ribbon device; our scene is an original seal mascot with parcels |
| Large light-weight headlines, generous white space, arrow buttons | Any copy |

All artwork (seal mark, mascot, parcels, tile drawings) is original SVG in this repo. The demo video should show no
third-party logos, as the hackathon rules require.

## Motion

One orchestrated moment per page: the stamp landing on the sealed answer (home), the verdict panel (seal check), the
slope line drawing (scorecard), the squares filling (proof, story), the evidence drawer sliding in (shop). Everything else moves only in answer to the user.
`prefers-reduced-motion` turns all of it off.

## Charts (after Storytelling with Data)

- The title is the takeaway ("With evidence, small shops won 37 of 50").
- Grey for context, red for the one thing to look at, labels on the marks, no legends to decode, no dual axes.
- Every chart has a source line naming the gold table or measure.
- In rule bars red means "rule not met"; in the slope chart red marks the headline model. Grey is context, not a category,
  which is why the palette validator's chroma check does not apply to it; the pair passes colour-blind separation.

## Not done

No dark theme. No visual regression tests. Twelve pages were measured for horizontal overflow at 390px wide (none), but mobile layouts were not reviewed by eye.
