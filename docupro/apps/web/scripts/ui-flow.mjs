/** jsdom-driven end-to-end UI test against a running DOCUPRO server. */
import { JSDOM } from "jsdom";
import { createRequire } from "node:module";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const API = process.env.DOCUPRO_API_URL ?? "http://127.0.0.1:8000";
const CORPUS =
  process.env.DOCUPRO_CORPUS ?? fileURLToPath(new URL("../../../tests/corpus/generated", import.meta.url));

const dom = new JSDOM(`<!doctype html><html><body><div id="root"></div></body></html>`, {
  url: API + "/",
  pretendToBeVisual: true,
});
const { window } = dom;
global.window = window;
global.document = window.document;
Object.defineProperty(global, "navigator", { value: window.navigator, configurable: true });
for (const name of ["HTMLElement", "Node", "MouseEvent", "PopStateEvent", "CustomEvent", "Event", "FormData", "File", "Blob", "EventTarget",
         "XMLHttpRequest"]) {
  global[name] = window[name];
}
global.localStorage = window.localStorage;
const nodeCrypto = globalThis.crypto;
Object.defineProperty(global, "crypto", {
  value: { randomUUID: () => nodeCrypto.randomUUID(), getRandomValues: (a) => nodeCrypto.getRandomValues(a) },
  configurable: true,
});
globalThis.IS_REACT_ACT_ENVIRONMENT = false;
window.scrollTo = () => {};
window.matchMedia = () => ({
  matches: false, media: "", addEventListener() {}, removeEventListener() {},
  addListener() {}, removeListener() {}, dispatchEvent: () => false,
});
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock";
window.URL.revokeObjectURL = () => {};

const realFetch = globalThis.fetch;
global.fetch = (input, init) => {
  const url = typeof input === "string" ? input : input.url;
  return realFetch(url.startsWith("http") ? url : new URL(url, API).toString(), init);
};
window.fetch = global.fetch;

window.__FIXTURE_PDF__ = new Uint8Array(readFileSync(`${CORPUS}/report-fr.pdf`));
window.__FIXTURE_BAD__ = new Uint8Array(readFileSync(`${CORPUS}/corrupted.pdf`));

const bundle = process.env.FLOW_BUNDLE ?? "/tmp/docupro-flow.cjs";
if (!existsSync(bundle)) {
  console.error(
    `Missing UI bundle ${bundle}.\nBuild it first:\n` +
      "  npx esbuild src/flow-entry.tsx --bundle --outfile=/tmp/docupro-flow.cjs \\\n" +
      "    --platform=node --format=cjs --alias:@=./src --jsx=automatic --define:import.meta.env='{}'",
  );
  process.exit(2);
}
const require = createRequire(import.meta.url);
require(bundle);
