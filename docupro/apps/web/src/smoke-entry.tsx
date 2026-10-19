/* Browser-free render smoke test used by scripts/dom-smoke.mjs.
 * It mounts the real application against the live API and reports what rendered. */
import { createRoot } from "react-dom/client";
import App from "./App";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function run() {
  const container = document.getElementById("root");
  if (!container) throw new Error("no container");
  const root = createRoot(container);
  root.render(<App />);
  await wait(1200);

  const report: Record<string, unknown> = {};
  report.home = document.body.textContent?.slice(0, 0) ?? "";
  report.hasHero = Boolean(document.body.textContent?.includes("Every document, ready for"));
  report.hasDropzoneLabel = Boolean(document.body.textContent?.includes("Choose a file or drag it here"));
  report.toolLinks = document.querySelectorAll('a[href^="/tool/"]').length;
  report.navLinks = document.querySelectorAll('nav a').length;
  report.hasPdfWordLink = Boolean(document.querySelector('a[href="/tool/pdf-to-word"]'));

  // Navigate to a tool page through the router.
  const link = document.querySelector('a[href="/tool/pdf-to-word"]') as HTMLAnchorElement | null;
  if (link) {
    link.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 }));
    await wait(500);
    report.toolHeading = document.querySelector("h1")?.textContent ?? null;
    report.toolHasDropzone = Boolean(document.body.textContent?.includes("Choose a file or drag it here"));
    report.toolHasOptions = Boolean(document.body.textContent?.includes("Conversion mode"));
    report.toolHasLimitations = Boolean(document.body.textContent?.includes("Known limitations"));
    report.toolHasInputs = document.querySelectorAll('input[type="file"]').length;
  }

  // Visit the tools catalog and settings routes.
  window.history.pushState({}, "", "/tools");
  window.dispatchEvent(new PopStateEvent("popstate"));
  await wait(500);
  report.toolsPage = Boolean(document.body.textContent?.includes("All tools"));

  window.history.pushState({}, "", "/privacy");
  window.dispatchEvent(new PopStateEvent("popstate"));
  await wait(400);
  report.privacyPage = Boolean(document.body.textContent?.includes("Retention policy"));

  console.log("SMOKE_REPORT " + JSON.stringify(report));
  root.unmount();
}

run().catch((error) => {
  console.error("SMOKE_FAILURE", error);
  process.exitCode = 1;
});
