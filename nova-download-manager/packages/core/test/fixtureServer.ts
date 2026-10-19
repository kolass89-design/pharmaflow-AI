import * as http from 'node:http';
import type { AddressInfo } from 'node:net';

/** Deterministic pseudo-random content so tests can regenerate + hash-compare. */
export function makeBytes(n: number, seed = 7): Buffer {
  const buf = Buffer.alloc(n);
  for (let i = 0; i < n; i++) buf[i] = (i * 31 + seed * 17 + (i >> 8)) % 251;
  return buf;
}

export interface FixtureServer {
  base: string;
  rangeStarts: number[];
  hits: Map<string, number>;
  close: () => Promise<void>;
}

function parseRange(header: string | undefined, total: number): { start: number; end: number } | null {
  if (!header) return null;
  const m = header.match(/bytes=(\d*)-(\d*)/);
  if (!m) return null;
  const start = m[1] === '' ? Math.max(0, total - parseInt(m[2], 10)) : parseInt(m[1], 10);
  const end = m[2] === '' || m[1] === '' ? total - 1 : Math.min(parseInt(m[2], 10), total - 1);
  if (Number.isNaN(start) || start >= total) return null;
  return { start, end };
}

export function startFixtureServer(): Promise<FixtureServer> {
  const rangeStarts: number[] = [];
  const hits = new Map<string, number>();
  const hit = (k: string) => {
    const v = (hits.get(k) ?? 0) + 1;
    hits.set(k, v);
    return v;
  };

  const server = http.createServer((req, res) => {
    const url = new URL(req.url ?? '/', 'http://x');
    const n = Math.max(1, parseInt(url.searchParams.get('n') ?? '100000', 10));
    const key = url.searchParams.get('k') ?? 'default';
    const isHead = req.method === 'HEAD';
    const total = n;
    const body = makeBytes(total);

    const sendRangeAware = (supportRange: boolean, extraHeaders: Record<string, string> = {}) => {
      const range = supportRange ? parseRange(req.headers.range, total) : null;
      if (range) {
        rangeStarts.push(range.start);
        res.writeHead(206, {
          'Content-Type': 'application/octet-stream',
          'Content-Range': `bytes ${range.start}-${range.end}/${total}`,
          'Content-Length': String(range.end - range.start + 1),
          'Accept-Ranges': 'bytes',
          ETag: '"nova-fixture-v1"',
          ...extraHeaders,
        });
        if (!isHead) res.end(body.subarray(range.start, range.end + 1));
        else res.end();
      } else {
        res.writeHead(200, {
          'Content-Type': 'application/octet-stream',
          'Content-Length': String(total),
          ...(supportRange ? { 'Accept-Ranges': 'bytes' } : {}),
          ETag: '"nova-fixture-v1"',
          ...extraHeaders,
        });
        if (!isHead) res.end(body);
        else res.end();
      }
    };

    switch (url.pathname) {
      case '/file.bin':
        sendRangeAware(true);
        break;
      case '/named.mp4':
        sendRangeAware(true, { 'Content-Type': 'video/mp4' });
        break;
      case '/norange.bin':
        sendRangeAware(false);
        break;
      case '/redirect':
        res.writeHead(302, { Location: `/file.bin?n=${n}` });
        res.end();
        break;
      case '/missing':
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('not found');
        break;
      case '/denied':
        res.writeHead(403, { 'Content-Type': 'text/plain' });
        res.end('forbidden');
        break;
      case '/evilname':
        res.writeHead(200, {
          'Content-Type': 'text/plain',
          'Content-Length': String(total),
          'Content-Disposition': 'attachment; filename="../../evil?.txt"',
        });
        if (!isHead) res.end(body);
        else res.end();
        break;
      case '/flaky.bin': {
        // First real GET dies mid-body; resume (Range) succeeds afterwards.
        // HEAD probes must not consume the "first hit".
        if (isHead) {
          sendRangeAware(true);
          break;
        }
        const h = hit(`flaky:${key}`);
        const range = parseRange(req.headers.range, total);
        if (h === 1 && !range) {
          res.writeHead(200, { 'Content-Type': 'application/octet-stream', 'Content-Length': String(total), 'Accept-Ranges': 'bytes' });
          res.write(body.subarray(0, Math.floor(total * 0.4)), () => res.socket?.destroy());
        } else {
          sendRangeAware(true);
        }
        break;
      }
      case '/ratelimit.bin': {
        const h = hit(`ratelimit:${key}`);
        if (h <= 3) {
          res.writeHead(429, { 'Retry-After': '0', 'Content-Type': 'text/plain' });
          res.end('slow down');
        } else {
          sendRangeAware(true);
        }
        break;
      }
      case '/truncate.bin': {
        // Always cuts at 55% of total, even for range requests → can never complete.
        const cut = Math.floor(total * 0.55);
        const range = parseRange(req.headers.range, total);
        if (range && range.start < cut) {
          res.writeHead(206, {
            'Content-Range': `bytes ${range.start}-${range.end}/${total}`,
            'Content-Length': String(range.end - range.start + 1),
            'Accept-Ranges': 'bytes',
          });
          if (!isHead) res.write(body.subarray(range.start, cut), () => res.socket?.destroy());
          else res.end();
        } else if (!range) {
          res.writeHead(200, { 'Content-Length': String(total), 'Accept-Ranges': 'bytes' });
          if (!isHead) res.write(body.subarray(0, cut), () => res.socket?.destroy());
          else res.end();
        } else {
          res.writeHead(416);
          res.end();
        }
        break;
      }
      case '/slow.bin': {
        // Drip-feed ~4 KB every 25ms; Range capable. Used for pause/resume tests.
        const range = parseRange(req.headers.range, total);
        const start = range ? range.start : 0;
        const end = range ? range.end : total - 1;
        if (range) rangeStarts.push(start);
        res.writeHead(range ? 206 : 200, {
          'Content-Type': 'application/octet-stream',
          'Content-Length': String(end - start + 1),
          ...(range ? { 'Content-Range': `bytes ${start}-${end}/${total}` } : {}),
          'Accept-Ranges': 'bytes',
          ETag: '"nova-fixture-v1"',
        });
        if (isHead) {
          res.end();
          break;
        }
        let pos = start;
        const timer = setInterval(() => {
          if (res.writableEnded || res.destroyed) {
            clearInterval(timer);
            return;
          }
          const chunkEnd = Math.min(pos + 4096, end + 1);
          res.write(body.subarray(pos, chunkEnd));
          pos = chunkEnd;
          if (pos > end) {
            clearInterval(timer);
            res.end();
          }
        }, 25);
        res.on('close', () => clearInterval(timer));
        break;
      }
      default:
        res.writeHead(404);
        res.end();
    }
  });

  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const port = (server.address() as AddressInfo).port;
      resolve({
        base: `http://127.0.0.1:${port}`,
        rangeStarts,
        hits,
        close: () => new Promise<void>((r) => server.close(() => r())),
      });
    });
  });
}
