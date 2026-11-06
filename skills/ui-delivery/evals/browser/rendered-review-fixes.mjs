// Evaluator-only reference fixes for rendered-review-cases.json. They show that
// each defect check of rendered-review-oracle.mjs can pass on a corrected
// screen; they are one acceptable correction, not the expected executor diff.
// Every search string must occur exactly once, so a drifted fixture fails loudly.
import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';

export const REFERENCE_FIXES = {
  RR1: {
    // Markers take one 14 px slot plus a 6 px gap; request text starts at the same edge.
    edges: [
      { file: 'index.html', search: '    align-items: center;\n    gap: 7px;\n', replace: '    align-items: center;\n    gap: 6px;\n' },
      {
        file: 'index.html',
        search: '  .dot { width: 8px; height: 8px; border-radius: 50%; flex: none; background: var(--dot); }',
        replace: '  .dot { width: 8px; height: 8px; margin: 0 3px; border-radius: 50%; flex: none; background: var(--dot); }',
      },
      {
        file: 'index.html',
        search: '  .request { padding: 10px 8px; border-top: 1px solid var(--border); }',
        replace: '  .request { padding: 10px 8px 10px 20px; border-top: 1px solid var(--border); }',
      },
    ],
    // Only exceptions are shown on rows; the default is stated once.
    defaults: [
      {
        file: 'index.html',
        search: '<p class="page-note">Открытые заявки по корпусам на этой неделе.</p>',
        replace: '<p class="page-note">Открытые заявки по корпусам на этой неделе. Если не указано иное, приоритет обычный и заявку можно брать.</p>',
      },
      {
        file: 'index.html',
        search: "    meta.append(chip('Приоритет: ' + request.priority, request.priority === 'высокий' ? 'warn' : ''));\n"
          + "    meta.append(chip('Статус: ' + request.status, request.status === 'ждёт деталей' ? 'wait' : ''));\n"
          + '    item.append(meta);\n',
        replace: "    if (request.priority !== 'обычный') meta.append(chip('Приоритет: ' + request.priority, request.priority === 'высокий' ? 'warn' : ''));\n"
          + "    if (request.status !== 'можно брать') meta.append(chip('Статус: ' + request.status, request.status === 'ждёт деталей' ? 'wait' : ''));\n"
          + '    if (meta.childElementCount) item.append(meta);\n',
      },
    ],
  },
  RR2: {
    // The first 28 px text line is centered on the 40 px hit area and its 18 px box.
    checkbox: [
      { file: 'index.html', search: '  .step-text { line-height: 28px; }', replace: '  .step-text { line-height: 28px; padding-top: 6px; }' },
    ],
    // Every details line starts at the title column, not only the first one.
    'meta-wrap': [
      { file: 'index.html', search: 'text-indent: 36px;', replace: 'padding-left: 36px;' },
    ],
  },
  RR3: {
    'pointer-ring': [
      { file: 'index.html', search: '  .select-trigger:focus {', replace: '  .select-trigger:focus-visible {' },
    ],
    // A refresh of the shown site keeps its list; a different site still shows the placeholder.
    refresh: [
      { file: 'index.html', search: '  let requestSeq = 0;\n', replace: '  let requestSeq = 0;\n  let shownSite = null;\n' },
      {
        file: 'index.html',
        search: "    list.replaceChildren(statusRow('Загрузка…'));\n",
        replace: "    if (site !== shownSite) list.replaceChildren(statusRow('Загрузка…'));\n",
      },
      { file: 'index.html', search: '    renderList(items);\n', replace: '    renderList(items);\n    shownSite = site;\n' },
    ],
  },
};

const CASES_URL = new URL('../rendered-review-cases.json', import.meta.url);

export async function loadCase(caseId) {
  const document = JSON.parse(await readFile(CASES_URL, 'utf8'));
  const matches = document.cases.filter((item) => item.id === caseId);
  assert.equal(matches.length, 1, `case ${caseId} must occur once`);
  return matches[0];
}

export function applyFixes(files, caseId, checks) {
  const result = { ...files };
  for (const check of checks) {
    const edits = REFERENCE_FIXES[caseId]?.[check];
    assert.ok(edits, `no reference fix for ${caseId}/${check}`);
    for (const { file, search, replace } of edits) {
      const occurrences = result[file]?.split(search).length - 1;
      assert.equal(occurrences, 1, `${caseId}/${check}: search text must occur once in ${file}: ${JSON.stringify(search)}`);
      result[file] = result[file].replace(search, () => replace);
    }
  }
  return result;
}

// Writes the case's shipped files, with the named reference fixes applied, into dir.
export async function materialize(caseId, dir, checks = []) {
  const { files } = await loadCase(caseId);
  const output = applyFixes(files, caseId, checks);
  for (const [name, text] of Object.entries(output)) {
    const target = join(dir, ...name.split('/'));
    await mkdir(dirname(target), { recursive: true });
    await writeFile(target, text, 'utf8');
  }
  return dir;
}
