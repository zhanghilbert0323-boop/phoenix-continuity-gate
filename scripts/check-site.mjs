import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'docs');
const source = readFileSync(path.join(root, 'app.js'), 'utf8');
for (const page of ['index.html', 'zh.html', 'guide.html', 'guide-zh.html']) {
 const html = readFileSync(path.join(root, page), 'utf8');
 const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
 assert.equal(new Set(ids).size, ids.length, `${page}: duplicate ids`);
 for (const [, href] of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
  if (href.startsWith('#')) { if (href.length > 1) assert.ok(ids.includes(href.slice(1)), `${page}: missing anchor ${href}`); }
  else if (!href.startsWith('https://')) {
   const [resource, fragment] = href.split('#');
   const destination = path.join(root, resource.split('?')[0]);
   assert.ok(existsSync(destination), `${page}: missing asset ${href}`);
   if (fragment) {
    const destinationIds = [...readFileSync(destination, 'utf8').matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
    assert.ok(destinationIds.includes(fragment), `${page}: missing destination anchor ${href}`);
   }
  }
 }
 assert.match(html, /hreflang="zh-CN"/);
 assert.match(html, /hreflang="en"/);
 assert.match(html, /aria-live="polite"/);
 assert.match(html, /data-release="1\.0\.0rc1"/, `${page}: stale release identity`);
 assert.match(html, /href="downloads\/phoenix-continuity-gate-1\.0\.0rc1\.zip"/, `${page}: missing candidate source download`);
 assert.match(html, /href="downloads\/phoenix_continuity_gate-1\.0\.0rc1-py3-none-any\.whl"/, `${page}: missing candidate wheel`);
 if (page.startsWith('guide')) {
  assert.ok(ids.includes('team'), `${page}: missing team trial entry`);
  assert.match(html, /phoenix-gate team validate/);
  assert.match(html, /phoenix-gate team refresh/);
  assert.match(html, /phoenix-gate team status/);
  assert.match(html, /(?:Version:|版本：)\s*1\.0\.0rc1/);
 } else {
  assert.match(html, /href="guide(?:-zh)?\.html#team"/, `${page}: missing local team trial route`);
 }
}

function element() {
 return { textContent: '', className: '', attrs: {}, events: {}, classList: { toggle() {} },
  setAttribute(key, value) { this.attrs[key] = value; },
  getAttribute(key) { return this.attrs[key]; },
  addEventListener(key, callback) { this.events[key] = callback; } };
}
function start({ lang = 'en', url = 'https://example.test/phoenix/', remembered = null, browser = 'en-US', blocked = false } = {}) {
 const ids = ['command', 'copy-command', 'copy-status', 'demo-kicker', 'demo-title', 'demo-verdict', 'execution', 'freshness', 'demo-output', 'demo-explanation'];
 const nodes = Object.fromEntries(ids.map(id => [id, element()]));
 nodes.command.textContent = 'python -B -m phoenix_continuity_gate demo-record';
 const steps = Array.from({ length: 4 }, element);
 const switcher = element(); switcher.attrs.href = lang === 'en' ? 'zh.html?lang=zh' : 'index.html?lang=en';
 const location = { href: url, hash: new URL(url).hash, replace(value) { this.redirect = value; } };
 const storage = { value: remembered, getItem() { if (blocked) throw Error('denied'); return this.value; }, setItem(key, value) { if (blocked) throw Error('denied'); this.value = value; } };
 const clipboard = { async writeText(value) { this.copied = value; } };
 vm.runInNewContext(source, { URL, window: { location, localStorage: storage }, navigator: { language: browser, clipboard },
  document: { documentElement: { lang }, querySelectorAll: selector => selector === '.step' ? steps : [switcher], getElementById: id => nodes[id] } });
 return { nodes, steps, location, storage, clipboard, switcher };
}
const outcomes = [['SUCCEEDED', 'MATCH', 'PASS'], ['SUCCEEDED', 'CHANGED', 'BLOCK'], ['FAILED', 'MATCH', 'BLOCK'], ['SUCCEEDED', 'MATCH', 'PASS']];
for (const lang of ['en', 'zh-CN']) {
 const session = start({ lang, url: `https://example.test/phoenix/${lang === 'en' ? 'index.html?lang=en' : 'zh.html'}` });
 assert.equal(session.location.redirect, undefined);
 for (let i = 0; i < 4; i++) {
  session.steps[i].events.click();
  assert.deepEqual([session.nodes.execution.textContent, session.nodes.freshness.textContent, session.nodes['demo-verdict'].textContent], outcomes[i]);
  session.steps.forEach((button, index) => assert.equal(button.attrs['aria-pressed'], String(index === i)));
  assert.ok(session.nodes['demo-explanation'].textContent.length > 20);
 }
 session.steps[1].events.click();
 assert.match(session.nodes['demo-explanation'].textContent, lang === 'en' ? /old run/ : /旧运行/);
 await session.nodes['copy-command'].events.click();
 assert.equal(session.clipboard.copied, session.nodes.command.textContent);
 assert.match(session.nodes['copy-status'].textContent, lang === 'en' ? /Copied/ : /已复制/);
 session.clipboard.writeText = async () => { throw Error('denied'); };
 await session.nodes['copy-command'].events.click();
 assert.match(session.nodes['copy-status'].textContent, lang === 'en' ? /Select and copy/ : /选中并复制/);
 session.location.hash = '#demo'; session.switcher.events.click();
 assert.equal(new URL(session.switcher.href).hash, '#demo');
}
assert.equal(new URL(start({ browser: 'zh-CN', url: 'https://example.test/phoenix/#demo' }).location.redirect).pathname, '/phoenix/zh.html');
assert.equal(new URL(start({ remembered: 'zh' }).location.redirect).searchParams.get('lang'), 'zh');
const englishOverride = start({ remembered: 'zh', browser: 'zh-CN', url: 'https://example.test/phoenix/?lang=en' });
assert.equal(englishOverride.location.redirect, undefined); assert.equal(englishOverride.storage.value, 'en');
assert.equal(start({ lang: 'zh-CN', url: 'https://example.test/phoenix/zh.html', remembered: 'en' }).location.redirect, undefined);
assert.equal(start({ blocked: true, browser: 'en-US', url: 'https://example.test/phoenix/?lang=en' }).location.redirect, undefined);
assert.equal(start({ remembered: 'unexpected', url: 'https://example.test/phoenix/?lang=unexpected' }).location.redirect, undefined);
assert.equal(new URL(start({ lang: 'zh-CN', url: 'https://example.test/phoenix/zh.html?lang=en#demo' }).location.redirect).pathname, '/phoenix/index.html');
for (const page of ['guide.html', 'guide-zh.html']) {
 const html = readFileSync(path.join(root, page), 'utf8');
 const targets = {};
 for (const [, id, text] of html.matchAll(/<(?:code|pre) id="([^"]+)">([\s\S]*?)<\/(?:code|pre)>/g)) targets[id] = { textContent: text };
 const copyButtons = [...html.matchAll(/data-copy="([^"]+)"/g)].map(([, id]) => ({ ...element(), dataset: { copy: id } }));
 const notice = { textContent: '' };
 const messages = { copySuccess: html.match(/data-copy-success="([^"]+)"/)[1], copyFailure: html.match(/data-copy-failure="([^"]+)"/)[1] };
 const clipboard = { async writeText(text) { this.copied = text; } };
 vm.runInNewContext(readFileSync(path.join(root, 'guide.js'), 'utf8'), { navigator: { clipboard }, setTimeout: () => 1, clearTimeout() {}, document: { body: { dataset: messages }, querySelectorAll: () => copyButtons, getElementById: id => id === 'guide-copy-status' ? notice : targets[id] } });
 for (const button of copyButtons) {
  assert.ok(targets[button.dataset.copy], `${page}: missing copy target`);
  await button.events.click(); assert.equal(clipboard.copied, targets[button.dataset.copy].textContent); assert.equal(notice.textContent, messages.copySuccess);
 }
 clipboard.writeText = async () => { throw Error('denied'); };
 await copyButtons[0].events.click(); assert.equal(notice.textContent, messages.copyFailure);
}
const expectedDownloads = {
 'phoenix-continuity-gate-v0.2.2-preview.zip': 'f9dd62c3e17514b834d4338cc63f8ba1cba8a05db0f40528e21dbfc1201dc008',
 'phoenix-continuity-gate-1.0.0rc1.zip': 'ab0e85017396693f2b8a242c346c4d13c8030a05fd6f4f6dc99a56ae36ecd32f',
 'phoenix_continuity_gate-1.0.0rc1-py3-none-any.whl': '94754b6bf63675e6f7de2bb68ab7a335f0a49ad65bf04e442abfe97d2b65a80e'
};
const seen = new Set();
for (const line of readFileSync(path.join(root, 'downloads', 'SHA256SUMS.txt'), 'utf8').trim().split(/\r?\n/)) {
 const entry = line.match(/^([a-f0-9]{64})\s+([^/\\]+)$/);
 assert.ok(entry, 'Malformed published download checksum');
 const [, hash, name] = entry;
 assert.ok(!seen.has(name), 'Duplicate checksum entry'); seen.add(name);
 assert.equal(hash, expectedDownloads[name], `Unexpected release checksum for ${name}`);
 const actual = createHash('sha256').update(readFileSync(path.join(root, 'downloads', name))).digest('hex');
 assert.equal(actual, hash, `Mirrored release differs from fixed artifact: ${name}`);
}
assert.deepEqual([...seen].sort(), Object.keys(expectedDownloads).sort(), 'Missing checksum entry');
console.log('PASS: four candidate-version pages, local resources and team/feedback routes; demo and language selection; demo/install/workflow/feedback copying in both languages, including clipboard denial; fixed candidate ZIP/wheel and historical ZIP checksums. Browser rendering remains unverified.');
