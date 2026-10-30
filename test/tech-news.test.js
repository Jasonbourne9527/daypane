import test from 'node:test';
import assert from 'node:assert/strict';
import { parseTechFeed } from '../src/providers/news.js';
test('technology feed keeps complete titles, decodes entities and excludes stale/future items', () => {
  const now = Date.parse('2026-10-30T08:00:00Z');
  const item = (title, date) => `<item><title><![CDATA[${title}]]></title><link>https://example.org/article?a=1&amp;b=2</link><pubDate>${date}</pubDate></item>`;
  const xml = item('新芯片 &amp; 开源软件发布', 'Fri, 30 Oct 2026 07:00:00 GMT') + item('旧闻', 'Fri, 23 Oct 2026 07:00:00 GMT') + item('未来新闻', 'Sat, 31 Oct 2026 07:00:00 GMT');
  const result = parseTechFeed(xml, '测试来源', now);
  assert.equal(result.length, 1);
  assert.equal(result[0].title, '新芯片 & 开源软件发布');
  assert.equal(result[0].url, 'https://example.org/article?a=1&b=2');
  assert.equal(result[0].source, '测试来源');
  assert.equal(parseTechFeed(item('长'.repeat(43), 'Fri, 30 Oct 2026 07:00:00 GMT'), '来源', now).length, 0);
});
