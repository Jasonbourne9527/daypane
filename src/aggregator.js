import { getWorkbuddy } from './providers/workbuddy.js';
import { getClaudeCodeUsage } from './providers/claudecode.js';
import { getCodexUsage } from './providers/codex.js';
import { getWeather } from './providers/weather.js';
import { getStocks } from './providers/stocks.js';
import { getClocks } from './providers/clocks.js';
import { getFx } from './providers/fx.js';
import { getNews } from './providers/news.js';
import { getMlb } from './providers/mlb.js';
import { getReported } from './reported.js';
import { getConfig } from './config.js';

// local 模式：直接读本机 DB 与本地日志。
function quotasLocal(db) {
  return {
    workbuddy: getWorkbuddy(db),
    claudecode: getClaudeCodeUsage(),
    codex: getCodexUsage()
  };
}

// cloud 模式：没有本地 DB，用本机上报器推上来的 data/quotas.json。
// stale 时打上标记，看板会显示"电脑离线"而不是假装数据新鲜。
function quotasCloud() {
  const r = getReported();
  const wrap = (v) => {
    if (!v) {
      return { ok: false, error: 'no report', unit: '', used: null, cap: null, remaining: null, percent: 0, stale: true };
    }
    return { ...v, stale: r.stale };
  };
  return {
    workbuddy: wrap(r.quotas && r.quotas.workbuddy),
    claudecode: wrap(r.quotas && r.quotas.claudecode),
    codex: wrap(r.quotas && r.quotas.codex)
  };
}

// Aggregate every section into a single dashboard payload.
// Network calls run concurrently; local calls are synchronous.
export async function buildDashboard(db) {
  const cfg = getConfig();
  const cloud = cfg.mode === 'cloud';
  if (cfg.display?.preset === 'daypane') {
    return { ok: true, serverTime: Date.now(), weather: await getWeather() };
  }

  const [weather, stocks, fx, news, mlb, newsEn] = await Promise.all([
    getWeather(),
    getStocks(),
    getFx(),
    getNews(),
    getMlb(),
    getNews('en')
  ]);

  const reported = cloud ? getReported() : null;
  const now = Date.now();

  // 额度的"刷新时间"：local 模式是从本机 DB 现读的（=此刻），
  // cloud 模式是本机上报器最后一次推送上来的时间。
  const quotas = cloud ? quotasCloud() : quotasLocal(db);

  return {
    ok: true,
    serverTime: now,
    mode: cloud ? 'cloud' : 'local',
    // 电脑是否还"活着"：local 模式永远在线；cloud 模式看上报是否新鲜
    pcOnline: cloud ? !!(reported && reported.ok && !reported.stale) : true,
    quotas: { ...quotas, fetchedAt: cloud ? (reported && reported.ts) || null : now },
    weather,
    stocks,
    clocks: getClocks(),
    fx,
    news,
    newsEn,
    mlb
  };
}
