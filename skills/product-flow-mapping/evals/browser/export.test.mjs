// Evaluator-only: real portable file loading, no remote service or product data.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import test from 'node:test';
import { chromium } from 'playwright';

const skill = resolve(dirname(fileURLToPath(import.meta.url)), '../..');

test('portable handoff loads real PNGs and exposes the full reader contract', { timeout: 60000 }, async () => {
  const root = await mkdtemp(join(tmpdir(), 'assay-flow-browser-'));
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 800, height: 450 } });
    await page.setContent('<main style="padding:32px;font:18px system-ui"><h1>Synthetic collection</h1><p>Exported result</p><button>Copy link</button></main>');
    const button = await page.getByRole('button', { name: 'Copy link' }).boundingBox();
    assert.ok(button);
    const image = await page.screenshot({ path: join(root, 'screen.png') });
    const sha256 = createHash('sha256').update(image).digest('hex');
    const map = JSON.parse(await readFile(join(skill, 'examples/source-only-map.json'), 'utf8'));
    map.screens[0].purpose = 'Reader must see the screen purpose';
    map.states[0].conditions = 'Reader must see the state prerequisites';
    map.actions[0].effect = 'Reader must see the action effect';
    map.scenarios[0].title = 'ДлинноеНазваниеБезПробелов'.repeat(20);
    map.captures.push({ id: 'CON', state_id: 'VIEW', file: 'screen.png', sha256, width: 800, height: 450,
      scope: 'Synthetic browser fixture', source_revision: 'example-v1', readiness: 'Button rendered',
      captured_at: '2026-09-26T12:00:00Z', simulated: true, redaction: 'reviewed', evidence_ids: ['CODE'],
      callouts: [{ number: 1, action_id: 'COPY', box: [button.x / 800, button.y / 450, button.width / 800, button.height / 450], image_sha256: sha256 }] });
    map.scenarios[1].steps[0].capture_ids = ['CON'];
    const a = structuredClone(map.scenarios[1]);
    const b = structuredClone(a);
    a.id = 'FLOW-A'; a.steps = [{ ...a.steps[0], id: 'OPEN' }];
    b.id = 'FLOW'; b.steps = [{ ...b.steps[0], id: 'A-OPEN' }];
    map.scenarios.push(a, b);
    await writeFile(join(root, 'map.json'), JSON.stringify(map));
    await writeFile(join(root, 'notes.json'), JSON.stringify({ 'EDIT_FLOW/OPEN': '<script>window.injected = true</script>' }));
    const output = join(root, 'bundle');
    execFileSync('python', ['-B', join(skill, 'scripts/flow_map.py'), 'export', join(root, 'map.json'),
      '--notes', join(root, 'notes.json'), '--output', output], { encoding: 'utf8' });
    const remoteRequests = [];
    page.on('request', request => { if (/^https?:/.test(request.url())) remoteRequests.push(request.url()); });
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 900 });
      // No setContent/data-image substitutions: exercise the actual offline path.
      await page.goto(pathToFileURL(join(output, 'index.html')).href);
      await page.waitForFunction(() => [...document.images].length > 0 &&
        [...document.images].every(image => image.complete && image.naturalWidth > 0));
      const geometry = await page.evaluate(() => {
        const ids = [...document.querySelectorAll('[id]')].map(node => node.id);
        const fragments = [...document.querySelectorAll('a[href^="#"]')].map(node => node.getAttribute('href').slice(1));
        const pair = document.querySelector('.pair');
        const [left, right] = [...pair.children].map(node => node.getBoundingClientRect().toJSON());
        return { duplicateIds: ids.filter((id, index) => ids.indexOf(id) !== index),
          missing: fragments.filter(id => !document.getElementById(id)),
          overflow: document.documentElement.scrollWidth > innerWidth, left, right, injected: !!window.injected };
      });
      assert.deepEqual(geometry.duplicateIds, []);
      assert.deepEqual(geometry.missing, []);
      assert.equal(geometry.overflow, false);
      assert.equal(geometry.injected, false);
      if (width > 760) assert.ok(geometry.right.x >= geometry.left.right);
      else assert.ok(geometry.right.y >= geometry.left.bottom);
      assert.match(await page.locator('#screens-COLLECTION').innerText(), /Reader must see the screen purpose/);
      assert.match(await page.locator('#states-VIEW').innerText(), /Reader must see the state prerequisites/);
      assert.match(await page.locator('#action-EDIT').innerText(), /Reader must see the action effect/);
      assert.ok(await page.locator('.missing').count() > 0);
      assert.match(await page.locator('figcaption').first().innerText(), /Callouts: 1 — Copy link/);
      await page.getByRole('link', { name: '1: Copy link', exact: true }).first().click();
      assert.equal(new URL(page.url()).hash, '#action-COPY');
    }
    assert.deepEqual(remoteRequests, []);
  } finally {
    await browser.close();
    await rm(root, { recursive: true, force: true });
  }
});
