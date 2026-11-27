// Renders the day as a front page that reads at a glance (entry.png, 1024×1024): a masthead,
// three illustrated leads and nine illustrated cards with short headlines, a band of the
// day's numbers, twenty more briefs in large type, a story map, the date check and sources.
// Data: tools/edition.mjs; drawings: tools/art.mjs; map: data/land-110m.json (Natural Earth).
// Usage: node tools/dispatch-page.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { DAY, REGIONS, LEADS, CARDS, NUMBERS, BRIEFS, DATE_CHECK, SOURCES } from './edition.mjs';
import { LEAD_ART, CARD_ART } from './art.mjs';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SERIF = "'DejaVu Serif', 'Liberation Serif', Georgia, serif";
const SANS = "'Liberation Sans', Helvetica, Arial, sans-serif";
const INK = '#17202a';
const NAVY = '#13324d';
const PAPER = '#f8f3e8';
const SURE = { OFFICIAL: '#1e8449', CONFIRMED: '#1f618d', REPORTED: '#9a6b12', CLAIM: '#b03a2e' };

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function textWidth(str, size, serif = false) {
  let units = 0;
  for (const ch of str) {
    if (ch === ' ') units += 0.3;
    else if (/[A-Z0-9%]/.test(ch)) units += 0.7;
    else if (/[il.,'’:;|]/.test(ch)) units += 0.3;
    else if (/[mwMW]/.test(ch)) units += 0.9;
    else units += 0.56;
  }
  return units * size * (serif ? 1.12 : 1.05);
}

function wrap(str, size, maxWidth, serif) {
  const lines = [];
  let line = '';
  for (const word of str.split(' ')) {
    const next = line ? `${line} ${word}` : word;
    if (line && textWidth(next, size, serif) > maxWidth) {
      lines.push(line);
      line = word;
    } else line = next;
  }
  if (line) lines.push(line);
  return lines;
}

// Largest size up to `size` at which the line fits.
function fit(str, size, maxWidth, serif) {
  let s = size;
  while (s > 10 && textWidth(str, s, serif) > maxWidth) s -= 0.5;
  return s;
}

const T = (x, y, str, size, { fill = INK, weight = 400, serif = false, anchor = 'start', spacing = 0 } = {}) =>
  `<text x="${x}" y="${y}" font-family="${serif ? SERIF : SANS}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}"${spacing ? ` letter-spacing="${spacing}"` : ''}>${esc(str)}</text>`;

function tag(x, y, label, tint, size = 10.5) {
  const w = textWidth(label, size) + 10;
  return `<rect x="${x}" y="${y - size}" width="${w}" height="${size + 5}" fill="${tint}"/>${T(x + 5, y + 1, label, size, { fill: '#fff', weight: 700 })}`;
}

function tagRight(xr, y, label, tint, size = 10) {
  return tag(xr - textWidth(label, size) - 10, y, label, tint, size);
}

function masthead() {
  return `
  <rect width="1024" height="26" fill="${NAVY}"/>
  ${T(14, 18, 'THE DAY IN ONE PAGE', 12.5, { fill: '#f5c542', weight: 700, spacing: 3 })}
  ${T(1010, 18, `${LEADS.length + CARDS.length + BRIEFS.length} STORIES · 6 REGIONS · ALL FIRST REPORTED ${DAY.long.toUpperCase()}`, 11.5, { fill: '#fff', weight: 700, anchor: 'end', spacing: 0.5 })}
  ${T(512, 84, DAY.long, 58, { weight: 700, serif: true, anchor: 'middle' })}
  <rect y="96" width="1024" height="30" fill="${NAVY}"/>
  ${DAY.top.map((t, i) => T(14 + i * 336 + 8, 117, `• ${t}`, 17, { fill: '#fff', weight: 700 })).join('')}`;
}

function leadCard([region, place, sure, , art, head, deck, src], i) {
  const w = 326;
  const x = 14 + i * (w + 9);
  const y = 134;
  const tint = REGIONS[region].tint;
  return `
  <rect x="${x}" y="${y}" width="${w}" height="232" fill="#fff" stroke="#d6cdb8"/>
  <clipPath id="L${i}"><rect x="${x + 6}" y="${y + 6}" width="${w - 12}" height="110"/></clipPath>
  <g clip-path="url(#L${i})"><g transform="translate(${x + 6},${y - 40}) scale(${(w - 12) / 200})">${LEAD_ART[art]()}</g></g>
  <rect x="${x + 6}" y="${y + 6}" width="30" height="24" fill="${INK}"/>${T(x + 21, y + 24, String(i + 1).padStart(2, '0'), 15, { fill: '#fff', weight: 700, anchor: 'middle' })}
  ${T(x + 10, y + 136, place, 11.5, { fill: tint, weight: 700, spacing: 1 })}${tagRight(x + w - 8, y + 135, sure, SURE[sure])}
  ${T(x + 10, y + 167, head, fit(head, 28, w - 20, true), { weight: 700, serif: true })}
  ${wrap(deck, 14, w - 20).slice(0, 2).map((l, k) => T(x + 10, y + 189 + k * 17, l, 14, { fill: '#2c3e50' })).join('')}
  ${T(x + w - 10, y + 225, src, 9.5, { fill: '#7f8c8d', anchor: 'end' })}`;
}

function card([region, place, sure, , art, head, deck, src], i) {
  const w = 326;
  const col = i % 3;
  const row = Math.floor(i / 3);
  const x = 14 + col * (w + 9);
  const y = 374 + row * 86;
  const tint = REGIONS[region].tint;
  return `
  <rect x="${x}" y="${y}" width="${w}" height="80" fill="#fff" stroke="#d6cdb8"/>
  <clipPath id="C${i}"><rect x="${x + 5}" y="${y + 5}" width="92" height="70"/></clipPath>
  <g clip-path="url(#C${i})"><g transform="translate(${x + 5},${y + 5})">${CARD_ART[art](92, 70)}</g></g>
  <rect x="${x + 5}" y="${y + 5}" width="24" height="18" fill="${INK}"/>${T(x + 17, y + 19, String(i + 4).padStart(2, '0'), 12, { fill: '#fff', weight: 700, anchor: 'middle' })}
  ${T(x + 106, y + 19, place, 10.5, { fill: tint, weight: 700, spacing: 0.8 })}${tagRight(x + w - 6, y + 18, sure, SURE[sure], 9)}
  ${T(x + 106, y + 43, head, fit(head, 21, w - 116, true), { weight: 700, serif: true })}
  ${wrap(deck, 12.5, w - 116).slice(0, 2).map((l, k) => T(x + 106, y + 60 + k * 14, l, 12.5, { fill: '#2c3e50' })).join('')}`;
}

function numbersBand() {
  const w = 249;
  return `<rect x="14" y="634" width="996" height="54" fill="${NAVY}"/>
  ${NUMBERS.map(([big, label], i) => {
    const x = 14 + i * w;
    const lines = wrap(label, 12.5, w - 110);
    return `${i ? `<line x1="${x}" y1="642" x2="${x}" y2="680" stroke="#3d5a73"/>` : ''}
    ${T(x + 12, 672, big, 30, { fill: '#f5c542', weight: 700, serif: true })}
    ${lines.slice(0, 2).map((l, k) => T(x + 100, 660 + k * 15 - (lines.length > 1 ? 0 : -7), l, 12.5, { fill: '#fff' })).join('')}`;
  }).join('')}`;
}

// ---- the story map (Natural Earth land) ----
const MAP = { lonMin: -170, lonMax: 190, latMin: -45, latMax: 72 };
function project(lon, lat, box) {
  const l = lon < MAP.lonMin ? lon + 360 : lon;
  return [box.x + ((l - MAP.lonMin) / (MAP.lonMax - MAP.lonMin)) * box.w, box.y + ((MAP.latMax - lat) / (MAP.latMax - MAP.latMin)) * box.h];
}
function landPath(box) {
  const topo = JSON.parse(readFileSync(`${ROOT}data/land-110m.json`, 'utf8'));
  const [sx, sy] = topo.transform.scale;
  const [tx, ty] = topo.transform.translate;
  const arcs = topo.arcs.map((arc) => {
    let x = 0;
    let y = 0;
    return arc.map(([dx, dy]) => [(x += dx) * sx + tx, (y += dy) * sy + ty]);
  });
  const ring = (r) => r.flatMap((i) => (i >= 0 ? arcs[i] : [...arcs[~i]].reverse()));
  let d = '';
  for (const geom of topo.objects.land.geometries) {
    for (const polygon of geom.type === 'Polygon' ? [geom.arcs] : geom.arcs) {
      for (const r of polygon) {
        let prev = null;
        ring(r).forEach(([lon, lat], k) => {
          const [px, py] = project(lon, lat, box);
          d += `${k === 0 || (prev !== null && Math.abs(px - prev) > box.w / 2) ? 'M' : 'L'}${px.toFixed(1)} ${py.toFixed(1)}`;
          prev = px;
        });
        d += 'Z';
      }
    }
  }
  return d;
}

function mapPanel() {
  const box = { x: 20, y: 720, w: 318, h: 160 };
  const numbered = [...LEADS, ...CARDS].map((s, i) => ({ region: s[0], at: s[3], n: i + 1 }));
  const dots = BRIEFS.filter((b) => b[4]).map((b) => ({ region: b[2], at: b[4] }));
  return `
  <rect x="14" y="696" width="330" height="214" fill="#fff" stroke="#d6cdb8"/>
  ${T(22, 713, 'WHERE IT HAPPENED', 12, { weight: 700, spacing: 1.5 })}${T(336, 713, 'numbers match the stories', 10, { fill: '#7f8c8d', anchor: 'end' })}
  <clipPath id="mc"><rect x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}"/></clipPath>
  <rect x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}" fill="#d9e8f0"/>
  <g clip-path="url(#mc)"><path d="${landPath(box)}" fill="#ece5d1" stroke="#b7ab8e" stroke-width="0.5"/></g>
  ${dots.map((d) => { const [px, py] = project(d.at[0], d.at[1], box); return `<circle cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="3" fill="${REGIONS[d.region].tint}" stroke="#fff" stroke-width="0.8"/>`; }).join('')}
  ${numbered.map((s) => { const [px, py] = project(s.at[0], s.at[1], box); return `<circle cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="7.5" fill="${REGIONS[s.region].tint}" stroke="#fff" stroke-width="1.2"/>${T(px, py + 3.5, String(s.n), 9.5, { fill: '#fff', weight: 700, anchor: 'middle' })}`; }).join('')}
  ${(() => { let lx = 22; return Object.values(REGIONS).map((r) => { const out = `<rect x="${lx}" y="890" width="9" height="9" fill="${r.tint}"/>${T(lx + 12, 899, r.name, 9.5)}`; lx += 12 + textWidth(r.name, 9.5) + 8; return out; }).join(''); })()}`;
}

function briefsPanel() {
  const x0 = 352;
  const half = Math.ceil(BRIEFS.length / 2);
  return `
  <rect x="${x0}" y="696" width="658" height="214" fill="#fff" stroke="#d6cdb8"/>
  ${T(x0 + 10, 718, `Also on ${DAY.weekday.charAt(0)}${DAY.weekday.slice(1).toLowerCase()}`, 19, { weight: 700, serif: true })}
  ${T(x0 + 648, 717, `${BRIEFS.length} MORE REPORTS`, 11, { fill: '#7f8c8d', weight: 700, anchor: 'end', spacing: 1 })}
  ${BRIEFS.map(([place, text, region, sure], i) => {
    const col = Math.floor(i / half);
    const x = x0 + 10 + col * 324;
    const y = 742 + (i % half) * 16.6;
    const line = `${place}: ${text}${sure === 'CLAIM' ? ' (claim)' : ''}`;
    const size = Math.min(13.5, fit(line, 13.5, 300));
    return `<rect x="${x}" y="${y - 10}" width="4" height="12" fill="${REGIONS[region].tint}"/>
      <text x="${x + 9}" y="${y}" font-family="${SANS}" font-size="${size}" fill="${INK}"><tspan font-weight="700">${esc(place)}:</tspan> ${esc(text)}${sure === 'CLAIM' ? ' (claim)' : ''}</text>`;
  }).join('')}`;
}

function footer() {
  return `
  <rect x="14" y="916" width="996" height="44" fill="#fbeee6" stroke="#b03a2e"/>
  ${tag(22, 934, 'DATE CHECK', '#b03a2e', 10.5)}
  ${T(112, 935, `Every story here happened or was first reported on ${DAY.long}.`, 12, { weight: 700 })}
  ${T(22, 952, DATE_CHECK, fit(DATE_CHECK, 11.5, 976), { fill: '#4d5656' })}
  ${Object.entries(SURE).map(([k, c], i) => tag(14 + i * 82, 980, k, c, 9.5)).join('')}
  ${T(352, 980, 'official = an authority’s word · confirmed = two outlets · reported = one · claim = one side', 10, { fill: '#5d6d7e' })}
  ${T(14, 1006, `Sources: ${SOURCES}`, fit(`Sources: ${SOURCES}`, 10.5, 860), { fill: '#4d5656' })}
  ${T(1010, 1006, 'drawings original', 10, { fill: '#7f8c8d', anchor: 'end' })}`;
}

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <rect width="1024" height="1024" fill="${PAPER}"/>
  ${masthead()}
  ${LEADS.map(leadCard).join('')}
  ${CARDS.map(card).join('')}
  ${numbersBand()}
  ${mapPanel()}
  ${briefsPanel()}
  ${footer()}
</svg>`;

writeFileSync(`${ROOT}entry.svg`, svg);
const { chromium } = createRequire(import.meta.url)('playwright');
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1024, height: 1024 }, deviceScaleFactor: 1 });
await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
await page.screenshot({ path: `${ROOT}entry.png`, type: 'png' });
await browser.close();
console.log(`wrote entry.png: ${LEADS.length + CARDS.length + BRIEFS.length} stories`);
