// "Thursday 26 November 2026: the world on one page" (Node 22, standard library only).
// entry.png is the front page tools/dispatch-page.mjs draws from the 32 stories in
// tools/edition.mjs, each first reported on 26 November 2026; this program hands it in by
// copying it to the grader's output directory.
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
import { copyFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outputDir, { recursive: true });
copyFileSync(new URL('./entry.png', import.meta.url), join(outputDir, 'entry.png'));
