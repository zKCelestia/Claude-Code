// Thursday 26 November 2026, as reported that day: twelve illustrated stories with short
// headlines that read at a glance, the day's numbers, and twenty more briefs. Each story
// names its outlets and how sure the report is:
//   OFFICIAL  an authority's own word        CONFIRMED  two or more outlets report it
//   REPORTED  one outlet's reporting          CLAIM      one side's account, not verified
// Sources read: Wikipedia's Current events for 26 November 2026 (citing BBC, AFP, AA,
// Al Jazeera, Reuters, AP, FT, The Daily Star, The Business Standard, L'Orient Today, The
// Daily Telegraph) and the Long Story Short digest for 26 Nov (LSS), keeping only its items
// that name no earlier day. Stories from 24-25 Nov are listed in the date check, not used.

export const DAY = {
  long: 'Thursday 26 November 2026',
  weekday: 'THURSDAY',
  top: ['Drone kills 2 Italians in Kuwait', 'De Cos to lead the ECB', 'SpaceX cleared for 1m satellites'],
};

export const REGIONS = {
  ME: { name: 'Middle East', tint: '#b03a2e' },
  EU: { name: 'Europe', tint: '#1f618d' },
  AF: { name: 'Africa', tint: '#b9770e' },
  AS: { name: 'Asia', tint: '#1e8449' },
  AM: { name: 'Americas', tint: '#7d3c98' },
  GL: { name: 'World', tint: '#5d6d7e' },
};

// [region, place, sureness, [lon, lat], art, headline, deck, source]
export const LEADS = [
  ['ME', 'KUWAIT', 'REPORTED', [47.98, 29.37], 'drone', 'Drone kills 2 Italians', 'Rheinmetall technicians die in a strike in Kuwait; Iran is blamed and denies it.', 'BBC'],
  ['EU', 'FRANKFURT', 'REPORTED', [8.68, 50.11], 'ecb', 'De Cos to lead the ECB', 'Spain’s Pablo Hernández de Cos is elected to succeed Christine Lagarde.', 'FT'],
  ['AM', 'WASHINGTON', 'OFFICIAL', [-77.0, 38.9], 'satellites', 'SpaceX gets 1m satellites', 'The FCC clears up to a million for Starmind orbital data centres.', 'AFP'],
];

export const CARDS = [
  ['ME', 'YEMEN', 'CLAIM', [44.2, 15.35], 'jets', 'Saudis hit 50 targets', 'Air strikes on Sanaa, Hudaydah and Saada, Riyadh says.', 'AFP · AJ'],
  ['AS', 'SAVAR', 'REPORTED', [90.26, 23.85], 'factory', '400 factories shut', 'Workers reject a Tk 17,000 wage and block highways.', 'TBS'],
  ['EU', 'IBIZA', 'REPORTED', [1.43, 38.9], 'ship', 'Tanker sinks off Ibiza', 'One crew member dead, 16 rescued from a Maltese ship.', 'Reuters'],
  ['AS', 'BANGKOK', 'REPORTED', [100.5, 13.75], 'refinery', 'Oil site blast hurts 9', 'Fire at a Bangchak facility; three are critical.', 'AP'],
  ['AF', 'BISSAU', 'REPORTED', [-15.6, 11.86], 'ballot', 'Vote pushed to 2028', 'Guinea-Bissau’s junta delays December’s elections.', 'Reuters'],
  ['EU', 'MOSCOW', 'REPORTED', [37.6, 55.75], 'oil', 'Lukoil assets sold', 'An Eldridge-led group agrees to buy them abroad.', 'AP'],
  ['EU', 'BELGRADE', 'OFFICIAL', [20.46, 44.8], 'vote', 'Serbia votes 27 Dec', 'Parliament sets the presidential election date.', 'AP'],
  ['AS', 'BEIJING', 'CONFIRMED', [116.4, 39.9], 'golf', '18 golf courses close', 'Clubs cite government orders amid anti-graft drive.', 'AFP · Telegraph'],
  ['EU', 'CAMBRIDGE', 'OFFICIAL', [0.12, 52.2], 'court', 'Train attacker guilty', 'Convicted of trying to murder 14, incl. on an LNER train.', 'AP'],
];

export const NUMBERS = [
  ['2', 'Italians killed by a drone in Kuwait'],
  ['50', 'Houthi targets Saudi Arabia says it hit'],
  ['1m', 'satellites the FCC lets SpaceX fly'],
  ['3.8%', 'US inflation in October'],
];

// [place, brief, region, sureness, [lon, lat] or null]
export const BRIEFS = [
  ['Beirut', 'Minibus drivers’ shootout kills 2', 'ME', 'REPORTED', [35.5, 33.9]],
  ['Jerusalem', 'Judges doubt Netanyahu conviction', 'ME', 'REPORTED', [35.2, 31.8]],
  ['Munshiganj', 'BNP faction clash kills 1', 'AS', 'REPORTED', [90.5, 23.5]],
  ['Cairo', 'Driver held over tanker fire', 'AF', 'OFFICIAL', [31.2, 30.0]],
  ['Enugu', 'Actor Pete Edochie dies at 79', 'AF', 'REPORTED', [7.5, 6.45]],
  ['London', 'Farage backs "Keep Britain Out"', 'EU', 'REPORTED', [-0.13, 51.5]],
  ['London', 'No home fees for EU students', 'EU', 'OFFICIAL', [-0.1, 51.45]],
  ['Russia', 'Kyiv says 5 jets hit at airbase', 'EU', 'CLAIM', [42.3, 55.3]],
  ['Venice', 'Nick Cave, India win Biennale vote', 'EU', 'REPORTED', [12.33, 45.44]],
  ['Bournemouth', 'King Crimson’s Michael Giles dies', 'EU', 'REPORTED', [-1.88, 50.72]],
  ['Washington', 'Birthright order blocked again', 'AM', 'OFFICIAL', [-77.1, 38.8]],
  ['Washington', 'US inflation 3.8% in October', 'AM', 'OFFICIAL', [-76.9, 38.95]],
  ['Washington', 'Senators: Pentagon bars Gulf visits', 'AM', 'REPORTED', [-77.05, 38.85]],
  ['San Juan', 'Court voids Luma Energy deal', 'AM', 'OFFICIAL', [-66.1, 18.47]],
  ['Albany', 'NY bans AI chatbot toys', 'AM', 'OFFICIAL', [-73.75, 42.65]],
  ['California', '42 states fight Character.AI sale', 'AM', 'REPORTED', [-121.5, 38.6]],
  ['Iowa', 'Army knew lead azide risk: CBS', 'AM', 'REPORTED', [-91.3, 40.8]],
  ['Austin', 'Duran Duran’s Andy Taylor dies', 'AM', 'REPORTED', [-97.7, 30.3]],
  ['Space', 'Hera sends Dimorphos close-ups', 'GL', 'REPORTED', null],
  ['White House', 'Melania helps reunite 9 children', 'GL', 'OFFICIAL', null],
];

export const DATE_CHECK = 'Left out as other days’ news: Cairo tanker blast, US tariff plan, Houthi hits on Jeddah, California tides, Macy’s parade delay (all Wed 25) · Mississippi plane crash (Tue 24).';

export const SOURCES = 'BBC · AFP · AA · Al Jazeera (AJ) · Reuters · AP · FT · CBS · The Daily Star · The Business Standard (TBS) · L’Orient Today · Telegraph · Long Story Short';
