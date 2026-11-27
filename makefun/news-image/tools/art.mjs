// Original flat vector drawings for the front page. Lead art is drawn in a 200×150 box and
// scaled; card art takes its box size (w×h) and fills it.

const stars = (pts, r = 1.5) => pts.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff"/>`).join('');

export const LEAD_ART = {
  drone: () => `
    <rect width="200" height="150" fill="#f6ddcc"/>
    <rect y="104" width="200" height="46" fill="#dc7633" opacity="0.45"/>
    <g fill="#7b7d7d"><rect x="24" y="72" width="60" height="34"/><rect x="92" y="62" width="40" height="44"/><rect x="138" y="80" width="46" height="26"/></g>
    <path d="M100 60 Q90 30 104 20 Q104 36 114 32 Q112 16 124 8 Q122 30 132 40 Q130 60 100 60Z" fill="#e67e22"/>
    <path d="M60 70 Q70 40 100 44 Q86 50 82 64Z" fill="#566573" opacity="0.7"/>
    <g transform="translate(46,36) rotate(-18)"><path d="M-22 0 L22 0 L28 -4 L22 4 L-22 4Z" fill="#2c3e50"/><path d="M-4 0 L-14 -14 H-8 L4 0Z M-4 4 L-14 18 H-8 L4 4Z" fill="#2c3e50"/></g>
    <g transform="translate(150,40)"><rect x="-14" y="-9" width="28" height="18" fill="#009246"/><rect x="-4.7" y="-9" width="9.4" height="18" fill="#fff"/><rect x="4.7" y="-9" width="9.3" height="18" fill="#ce2b37"/></g>`,
  ecb: () => `
    <rect width="200" height="150" fill="#d6eaf8"/>
    <rect x="70" y="20" width="60" height="110" fill="#5d6d7e"/><rect x="74" y="20" width="24" height="110" fill="#85929e"/>
    ${Array.from({ length: 9 }, (_, i) => `<rect x="104" y="${28 + i * 11}" width="22" height="5" fill="#d6eaf8" opacity="0.7"/>`).join('')}
    <rect y="130" width="200" height="20" fill="#7f8c8d"/>
    <g transform="translate(40,62)"><circle r="26" fill="#1f618d"/><text y="12" font-family="DejaVu Serif, serif" font-size="34" font-weight="700" fill="#f4d03f" text-anchor="middle">€</text></g>
    ${Array.from({ length: 12 }, (_, i) => { const a = (i / 12) * Math.PI * 2; return `<circle cx="${160 + Math.cos(a) * 22}" cy="${62 + Math.sin(a) * 22}" r="3" fill="#f4d03f"/>`; }).join('')}`,
  satellites: () => `
    <rect width="200" height="150" fill="#0b1026"/>
    <path d="M-20 150 Q100 70 220 150Z" fill="#2e86c1"/>
    ${Array.from({ length: 70 }, (_, i) => { const x = (i * 37) % 200; const y = 10 + ((i * 53) % 90); return `<g transform="translate(${x},${y})"><rect x="-3" y="-1" width="6" height="2" fill="#aab7b8"/><rect x="-1" y="-1.5" width="2" height="3" fill="#f4f6f6"/></g>`; }).join('')}
    <g transform="translate(100,62)"><rect x="-26" y="-5" width="20" height="10" fill="#2e4053" stroke="#5dade2"/><rect x="6" y="-5" width="20" height="10" fill="#2e4053" stroke="#5dade2"/><rect x="-6" y="-7" width="12" height="14" fill="#ecf0f1"/></g>
    <text x="192" y="140" font-family="Liberation Sans, Arial" font-size="18" font-weight="700" fill="#f4d03f" text-anchor="end">×1,000,000</text>`,
  tankers: () => `
    <rect width="200" height="150" fill="#1b4f72"/>
    <rect width="200" height="44" fill="#5b7b94"/>
    <path d="M0 98 Q25 92 50 98 T100 98 T150 98 T200 98 V150 H0Z" fill="#154360"/>
    <g transform="translate(14,70)"><path d="M0 18 H82 L74 32 H8Z" fill="#212f3d"/><rect x="54" y="2" width="18" height="16" fill="#ecf0f1"/><rect x="6" y="10" width="44" height="8" fill="#922b21"/></g>
    <g transform="translate(112,80)"><path d="M0 14 H72 L65 26 H7Z" fill="#212f3d"/><rect x="48" y="0" width="16" height="14" fill="#ecf0f1"/><rect x="5" y="7" width="38" height="7" fill="#922b21"/></g>
    <path d="M26 74 Q20 46 38 34 Q36 54 50 46 Q48 26 64 16 Q62 44 76 56 Q74 74 26 74Z" fill="#f39c12"/>
    <path d="M38 74 Q36 58 46 52 Q48 64 58 60 Q60 70 38 74Z" fill="#f7dc6f"/>
    <path d="M122 82 Q118 60 132 52 Q132 66 142 62 Q142 46 154 40 Q152 64 162 72 Q160 84 122 82Z" fill="#f39c12"/>
    <path d="M30 36 Q48 4 92 14 Q70 12 60 28Z" fill="#34495e" opacity="0.85"/>
    <path d="M130 46 Q146 14 182 22 Q160 22 154 38Z" fill="#34495e" opacity="0.85"/>
    <g transform="translate(96,116)"><circle r="9" fill="#0b0f14"/><path d="M0 -14 V14 M-14 0 H14 M-10 -10 L10 10 M10 -10 L-10 10" stroke="#0b0f14" stroke-width="3"/></g>`,
  cairo: () => `
    <rect width="200" height="150" fill="#f5cba7"/>
    <g fill="#a04000" opacity="0.4"><rect x="6" y="42" width="22" height="46"/><rect x="32" y="28" width="16" height="60"/><rect x="154" y="36" width="30" height="46"/><path d="M166 36 L169 16 L172 36Z"/><rect x="186" y="50" width="14" height="32"/></g>
    <path d="M0 110 L200 94 V126 L0 144Z" fill="#424949"/>
    <path d="M0 127 L200 110" stroke="#f4f6f6" stroke-width="2" stroke-dasharray="10 8"/>
    <g transform="translate(70,82) rotate(-16)"><rect x="0" y="10" width="62" height="22" rx="10" fill="#bdc3c7"/><rect x="62" y="12" width="20" height="20" fill="#7b7d7d"/><circle cx="12" cy="34" r="6" fill="#17202a"/><circle cx="72" cy="34" r="6" fill="#17202a"/></g>
    <path d="M52 96 Q44 54 72 38 Q70 64 86 54 Q84 24 104 6 Q102 42 120 56 Q118 28 138 32 Q130 58 146 92 Z" fill="#e67e22"/>
    <path d="M74 96 Q72 70 90 62 Q92 78 104 72 Q104 58 116 52 Q114 76 126 94Z" fill="#f9e79f"/>
    <path d="M60 40 Q80 0 130 6 Q100 8 90 26Z" fill="#5d6d7e" opacity="0.7"/>`,
  tiangong: () => `
    <rect width="200" height="150" fill="#0b1026"/>
    ${stars([[20, 40], [60, 120], [150, 36], [185, 88], [100, 30], [30, 95], [170, 112], [80, 50]])}
    <path d="M0 150 Q100 108 200 150Z" fill="#2e86c1"/>
    <g transform="translate(96,72)">
      <rect x="-52" y="-8" width="40" height="16" fill="#aab7b8"/><rect x="-12" y="-11" width="34" height="22" rx="4" fill="#d5dbdb"/><rect x="22" y="-7" width="22" height="14" fill="#aab7b8"/>
      <rect x="-48" y="-38" width="14" height="28" fill="#2e4053" stroke="#5dade2"/><rect x="-48" y="10" width="14" height="28" fill="#2e4053" stroke="#5dade2"/>
      <rect x="0" y="-40" width="14" height="30" fill="#2e4053" stroke="#5dade2"/><rect x="0" y="12" width="14" height="30" fill="#2e4053" stroke="#5dade2"/>
      <g transform="translate(62,0)"><path d="M-12 -6 H6 L12 0 L6 6 H-12Z" fill="#ecf0f1"/><rect x="-24" y="-3" width="12" height="6" fill="#5dade2"/></g>
    </g>
    <g transform="translate(168,56)"><rect x="-14" y="-9" width="28" height="18" fill="#01411c"/><rect x="-14" y="-9" width="7" height="18" fill="#fff"/><circle cx="4" cy="0" r="5" fill="#fff"/><circle cx="6" cy="-1" r="4.2" fill="#01411c"/></g>
    <g transform="translate(168,84)"><rect x="-14" y="-9" width="28" height="18" fill="#de2910"/><path d="M-9 -5 l1.2 3.4 h3.6 l-2.9 2.2 1.1 3.4 -3 -2.1 -3 2.1 1.1 -3.4 -2.9 -2.2 h3.6z" fill="#ffde00"/></g>`,
};

export const CARD_ART = {
  vote: (w, h) => `
    <rect width="${w}" height="${h}" fill="#e8daef"/>
    <rect x="${w / 2 - 22}" y="${h - 28}" width="44" height="24" fill="#5b2c6f"/><rect x="${w / 2 - 11}" y="${h - 28}" width="22" height="3" fill="#2c3e50"/>
    <rect x="${w / 2 - 8}" y="${h - 46}" width="16" height="20" fill="#fff" stroke="#7b7d7d"/><path d="M${w / 2 - 4} ${h - 36} l3 3 6 -7" stroke="#1e8449" stroke-width="2" fill="none"/>
    <text x="${w - 6}" y="16" font-family="Liberation Sans, Arial" font-size="12" font-weight="700" fill="#5b2c6f" text-anchor="end">27 DEC</text>`,
  golf: (w, h) => `
    <rect width="${w}" height="${h}" fill="#d5f5e3"/>
    <path d="M0 ${h - 16} Q${w / 2} ${h - 30} ${w} ${h - 16} V${h} H0Z" fill="#58d68d"/>
    <path d="M${w / 2} ${h - 22} V${h - 52}" stroke="#555" stroke-width="2"/><path d="M${w / 2} ${h - 52} L${w / 2 + 18} ${h - 46} L${w / 2} ${h - 40}Z" fill="#c0392b"/>
    <circle cx="${w / 2 - 20}" cy="${h - 20}" r="3" fill="#fff"/>
    <rect x="${w - 50}" y="8" width="44" height="14" fill="#c0392b"/><text x="${w - 28}" y="18" font-family="Liberation Sans, Arial" font-size="9" font-weight="700" fill="#fff" text-anchor="middle">CLOSED</text>`,
  court: (w, h) => `
    <rect width="${w}" height="${h}" fill="#eaecee"/>
    <path d="M${w / 2 - 34} ${h - 40} L${w / 2} ${h - 56} L${w / 2 + 34} ${h - 40}Z" fill="#7b7d7d"/>
    ${[-24, -8, 8, 24].map((dx) => `<rect x="${w / 2 + dx - 3}" y="${h - 40}" width="6" height="26" fill="#aab7b8"/>`).join('')}
    <rect x="${w / 2 - 38}" y="${h - 14}" width="76" height="6" fill="#7b7d7d"/>
    <g transform="translate(16,18) rotate(-35)"><rect x="-10" y="-5" width="20" height="10" rx="2" fill="#784212"/><rect x="-2" y="5" width="4" height="16" fill="#784212"/></g>`,
  jets: (w, h) => `
    <rect width="${w}" height="${h}" fill="#fdebd0"/>
    <rect y="${h - 12}" width="${w}" height="12" fill="#ca6f1e" opacity="0.5"/>
    ${[[30, 16], [70, 26], [110, 12]].map(([x, y]) => `<g transform="translate(${x},${y})"><path d="M-14 0 H12 L16 -2 L12 2 H-14Z M-2 0 L-8 -8 H-4 L4 0Z M-2 2 L-8 10 H-4 L4 2Z M-12 0 L-15 -5 H-12 L-9 0Z" fill="#2c3e50"/></g>`).join('')}
    <path d="M${w - 40} ${h - 12} Q${w - 46} ${h - 30} ${w - 32} ${h - 34} Q${w - 30} ${h - 22} ${w - 20} ${h - 26} Q${w - 18} ${h - 14} ${w - 40} ${h - 12}Z" fill="#e67e22"/>
    <text x="${w - 6}" y="16" font-family="Liberation Sans, Arial" font-size="13" font-weight="700" fill="#b03a2e" text-anchor="end">50</text>`,
  factory: (w, h) => `
    <rect width="${w}" height="${h}" fill="#e8f8f5"/>
    <path d="M8 ${h - 6} V${h - 30} L28 ${h - 40} V${h - 30} L48 ${h - 40} V${h - 30} L68 ${h - 40} V${h - 6}Z" fill="#7b7d7d"/>
    <rect x="22" y="${h - 22}" width="34" height="16" fill="#566573"/><path d="M22 ${h - 22} H56 M22 ${h - 18} H56 M22 ${h - 14} H56 M22 ${h - 10} H56" stroke="#aab7b8"/>
    <rect x="18" y="${h - 32}" width="44" height="8" fill="#c0392b"/><text x="40" y="${h - 25.5}" font-family="Liberation Sans, Arial" font-size="7" font-weight="700" fill="#fff" text-anchor="middle">CLOSED</text>
    ${Array.from({ length: 5 }, (_, i) => `<g transform="translate(${86 + i * 12},${h - 4})"><circle cy="-20" r="3.5" fill="#1e8449"/><rect x="-3.5" y="-16" width="7" height="13" rx="2" fill="#1e8449"/></g>`).join('')}
    <text x="${w - 6}" y="16" font-family="Liberation Sans, Arial" font-size="12" font-weight="700" fill="#1e8449" text-anchor="end">~400</text>`,
  ship: (w, h) => `
    <rect width="${w}" height="${h}" fill="#d6eaf8"/>
    <rect y="${h * 0.45}" width="${w}" height="${h * 0.55}" fill="#2e86c1"/>
    <g transform="translate(${w / 2},${h * 0.5}) rotate(14)"><path d="M-44 0 H36 L44 -6 V6 L36 12 H-40Z" fill="#212f3d"/><rect x="20" y="-12" width="14" height="12" fill="#ecf0f1"/><rect x="-36" y="-6" width="50" height="6" fill="#922b21"/></g>
    <path d="M0 ${h * 0.55} Q${w / 4} ${h * 0.5} ${w / 2} ${h * 0.58} T${w} ${h * 0.55} V${h} H0Z" fill="#1b4f72" opacity="0.8"/>
    ${[[18, 12], [w - 22, 14]].map(([x, y]) => `<g transform="translate(${x},${y})"><circle r="5" fill="none" stroke="#c0392b" stroke-width="3"/></g>`).join('')}`,
  ballot: (w, h) => `
    <rect width="${w}" height="${h}" fill="#fcf3cf"/>
    <rect x="${w / 2 - 24}" y="${h - 30}" width="48" height="26" fill="#566573"/><rect x="${w / 2 - 12}" y="${h - 30}" width="24" height="3" fill="#2c3e50"/>
    <rect x="${w / 2 - 9}" y="${h - 48}" width="18" height="20" fill="#fff" stroke="#7b7d7d"/>
    <text x="${w - 8}" y="22" font-family="Liberation Sans, Arial" font-size="14" font-weight="700" fill="#b9770e" text-anchor="end">2028</text>`,
  oil: (w, h) => `
    <rect width="${w}" height="${h}" fill="#eaeded"/>
    <rect y="${h - 10}" width="${w}" height="10" fill="#aab7b8"/>
    <g fill="#566573"><path d="M20 ${h - 10} L30 ${h - 44} L40 ${h - 10}Z" fill="none" stroke="#566573" stroke-width="2.5"/><rect x="26" y="${h - 50}" width="8" height="6"/></g>
    <path d="M44 ${h - 22} H${w - 10}" stroke="#7b7d7d" stroke-width="5"/>
    <circle cx="80" cy="${h - 30}" r="12" fill="#85929e"/><circle cx="108" cy="${h - 28}" r="10" fill="#85929e"/>
    <text x="${w - 8}" y="18" font-family="Liberation Sans, Arial" font-size="11" font-weight="700" fill="#1f618d" text-anchor="end">SOLD</text>`,
  pact: (w, h) => `
    <rect width="${w}" height="${h}" fill="#d6eaf8"/>
    <path d="M0 ${h * 0.72} Q${w / 4} ${h * 0.64} ${w / 2} ${h * 0.72} T${w} ${h * 0.72} V${h} H0Z" fill="#5dade2"/>
    <path d="M8 ${h * 0.8} Q26 ${h * 0.5} 46 ${h * 0.78}Z" fill="#27ae60"/>
    <path d="M${w - 60} ${h * 0.82} Q${w - 30} ${h * 0.38} ${w - 6} ${h * 0.8}Z" fill="#d4ac0d"/>
    <g transform="translate(${w / 2},${h * 0.5})"><path d="M-30 6 Q-16 -4 -4 2 L4 -1 Q16 -4 30 6 L24 13 Q12 6 2 11 Q-10 6 -24 13Z" fill="#f0b27a" stroke="#784212" stroke-width="1.5"/><rect x="-10" y="-22" width="20" height="16" fill="#fff" stroke="#1a5276"/></g>`,
  wage: (w, h) => `
    <rect width="${w}" height="${h}" fill="#e8f8f5"/>
    <g transform="translate(26,${h / 2 + 2})"><path d="M-10 -16 L-18 -10 L-14 -3 L-11 -5 V16 H11 V-5 L14 -3 L18 -10 L10 -16 Q0 -10 -10 -16Z" fill="#1e8449"/></g>
    <text x="${w / 2 + 8}" y="${h / 2 - 6}" font-family="Liberation Sans, Arial" font-size="12" font-weight="700" fill="#566573" text-anchor="middle">Tk 12,500</text>
    <path d="M${w / 2 - 20} ${h / 2 + 2} H${w / 2 + 34}" stroke="#1e8449" stroke-width="3"/><path d="M${w / 2 + 28} ${h / 2 - 4} L${w / 2 + 38} ${h / 2 + 2} L${w / 2 + 28} ${h / 2 + 8}" fill="#1e8449"/>
    <text x="${w / 2 + 8}" y="${h / 2 + 22}" font-family="Liberation Sans, Arial" font-size="15" font-weight="700" fill="#1e8449" text-anchor="middle">Tk 17,000</text>
    <text x="${w - 8}" y="18" font-family="Liberation Sans, Arial" font-size="13" font-weight="700" fill="#b03a2e" text-anchor="end">+36%</text>`,
  refinery: (w, h) => `
    <rect width="${w}" height="${h}" fill="#fad7a0"/>
    <rect y="${h - 12}" width="${w}" height="12" fill="#a04000" opacity="0.5"/>
    <g fill="#566573"><rect x="20" y="${h - 36}" width="14" height="24"/><rect x="40" y="${h - 44}" width="10" height="32"/><circle cx="72" cy="${h - 22}" r="12"/><circle cx="100" cy="${h - 20}" r="10"/><rect x="118" y="${h - 40}" width="8" height="28"/></g>
    <path d="M60 ${h - 30} Q54 ${h - 52} 66 ${h - 60} Q66 ${h - 48} 76 ${h - 52} Q76 ${h - 34} 60 ${h - 30}Z" fill="#e67e22"/>
    <path d="M90 12 Q110 2 136 10 Q114 10 104 22Z" fill="#5d6d7e" opacity="0.6"/>
    <g transform="translate(${w - 20},14) rotate(30)"><path d="M-8 0 H8 M0 -4 V4" stroke="#17202a" stroke-width="2.5"/></g>`,
  blast: (w, h) => `
    <rect width="${w}" height="${h}" fill="#d5f5e3"/>
    <rect y="${h - 14}" width="${w}" height="14" fill="#7dcea0"/>
    <path d="M${w / 2 - 22} ${h - 14} Q${w / 2 - 30} ${h - 30} ${w / 2 - 16} ${h - 34} Q${w / 2 - 22} ${h - 50} ${w / 2} ${h - 50} Q${w / 2 + 22} ${h - 52} ${w / 2 + 18} ${h - 34} Q${w / 2 + 32} ${h - 28} ${w / 2 + 22} ${h - 14}Z" fill="#aab7b8"/>
    <path d="M${w / 2 - 8} ${h - 14} Q${w / 2 - 6} ${h - 26} ${w / 2} ${h - 30} Q${w / 2 + 6} ${h - 26} ${w / 2 + 8} ${h - 14}Z" fill="#f39c12"/>
    <text x="10" y="16" font-family="Liberation Sans, Arial" font-size="11" font-weight="700" fill="#7d3c98">~5 TONS</text>
    <rect x="${w - 34}" y="${h - 30}" width="20" height="16" fill="#7b7d7d"/><path d="M${w - 36} ${h - 30} L${w - 24} ${h - 40} L${w - 12} ${h - 30}Z" fill="#566573"/>`,
  march: (w, h) => `
    <rect width="${w}" height="${h}" fill="#d6eaf8"/>
    <g fill="#0d5eaf"><rect x="10" y="8" width="44" height="28"/></g><g fill="#fff"><rect x="10" y="12" width="44" height="3"/><rect x="10" y="19" width="44" height="3"/><rect x="10" y="26" width="44" height="3"/></g>
    ${Array.from({ length: 9 }, (_, i) => `<g transform="translate(${18 + i * 15},${h - 4})"><circle cy="-22" r="4" fill="#34495e"/><rect x="-4" y="-17" width="8" height="15" rx="2" fill="#34495e"/></g>`).join('')}
    <rect x="${w - 60}" y="10" width="48" height="16" fill="#c0392b"/><text x="${w - 36}" y="22" font-family="Liberation Sans, Arial" font-size="10" font-weight="700" fill="#fff" text-anchor="middle">STRIKE</text>`,
  gaza: (w, h) => `
    <rect width="${w}" height="${h}" fill="#ebdef0"/>
    <g fill="#7b7d7d"><rect x="12" y="${h - 34}" width="22" height="34"/><rect x="38" y="${h - 26}" width="18" height="26"/><rect x="62" y="${h - 40}" width="24" height="40"/><rect x="92" y="${h - 22}" width="20" height="22"/><rect x="116" y="${h - 32}" width="22" height="32"/></g>
    <path d="M62 ${h - 40} L70 ${h - 46} L78 ${h - 38} L86 ${h - 44} V${h - 40}Z" fill="#ebdef0"/>
    <path d="M72 ${h - 44} Q60 ${h - 60} 80 ${h - 66} Q100 ${h - 70} 96 ${h - 52} Q90 ${h - 44} 72 ${h - 44}Z" fill="#566573" opacity="0.75"/>`,
};
