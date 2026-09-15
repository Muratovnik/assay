// Real integration test: missing dependencies MUST fail, never silently skip.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { scanAccessibility } from '../../assets/playwright/evidence.mjs';
const html = await readFile(new URL('./fixture.html', import.meta.url), 'utf8');
let browser;
before(async () => { browser = await chromium.launch({
  ...(process.env.UI_TEST_CHROMIUM ? { executablePath: process.env.UI_TEST_CHROMIUM } : {}),
}); });
after(async () => { await browser?.close(); });
for (const variant of ['good', 'missing-label']) {
  test(`axe scans the opened editor, not just the initial screen: ${variant}`, async () => {
    const session = await browser.newContext();
    try {
      const page = await session.newPage();
      await page.setContent(html.replace('<script>', `<script>window.fixture = ${JSON.stringify({ scenario: 'accessibility', variant })};`));
      const context = { build: 'synthetic-fixture', scenario: 'accessibility', state: 'closed', data: variant };
      const scan = (scope, state) => scanAccessibility(page, { context: { ...context, state }, scope,
        rules: ['button-name'], createBuilder: ({ page }) => new AxeBuilder({ page }) });
      assert.deepEqual((await scan('#main', 'closed')).findings, []);
      await assert.rejects(scan('#editor', 'closed'), /visible container/);
      await page.getByRole('button', { name: 'Open editor' }).click();
      const result = await scan('#editor', 'open');
      if (variant === 'good') assert.deepEqual(result.findings, []);
      else assert.ok(result.findings.some((f) => f.rule === 'button-name' && f.kind === 'violation'));
    } finally { await session.close(); }
  });
}
