/** Run the UI smoke test in jsdom against the live DOCUPRO server. */
import { JSDOM } from "jsdom";
import { createRequire } from "node:module";

const API = process.env.DOCUPRO_API_URL ?? "http://127.0.0.1:8000";
const dom = new JSDOM(
  `<!doctype html><html><head><meta charset="utf-8"></head><body><div id="root"></div></body></html>`,
  { url: "http://localhost/", pretendToBeVisual: true },
);

const { window } = dom;
global.window = window;
global.document = window.document;
Object.defineProperty(global, "navigator", { value: window.navigator, configurable: true });
global.HTMLElement = window.HTMLElement;
global.Node = window.Node;
global.MouseEvent = window.MouseEvent;
global.PopStateEvent = window.PopStateEvent;
global.CustomEvent = window.CustomEvent;
global.Event = window.Event;
global.FormData = window.FormData;
global.localStorage = window.localStorage;
Object.defineProperty(global, "crypto", {
  value: { ...globalThis.crypto, randomUUID: () => globalThis.crypto.randomUUID() },
  configurable: true,
});
globalThis.IS_REACT_ACT_ENVIRONMENT = false;

window.scrollTo = () => {};
window.matchMedia = () => ({
  matches: false,
  media: "",
  addEventListener() {},
  removeEventListener() {},
  addListener() {},
  removeListener() {},
  dispatchEvent: () => false,
});
window.HTMLElement.prototype.scrollIntoView = () => {};

// Resolve the app's relative API calls against the running server.
const realFetch = globalThis.fetch;
global.fetch = (input, init) => {
  const url = typeof input === "string" ? input : input.url;
  const absolute = url.startsWith("http") ? url : new URL(url, API).toString();
  return realFetch(absolute, init);
};
window.fetch = global.fetch;

const require = createRequire(import.meta.url);
require(process.env.SMOKE_BUNDLE ?? "/tmp/docupro-smoke.cjs");
