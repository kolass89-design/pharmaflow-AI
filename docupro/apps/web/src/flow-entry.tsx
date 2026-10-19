/* End-to-end UI flow: real upload, real worker, real download.
 * Driven by scripts/ui-flow.mjs (jsdom) against a running DOCUPRO service. */
import { createRoot } from "react-dom/client";
import App from "./App";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitForText(text: string, timeout = 60_000): Promise<boolean> {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (document.body.textContent?.includes(text)) return true;
    await wait(150);
  }
  return false;
}

function clickByText(selector: string, text: string): boolean {
  const nodes = Array.from(document.querySelectorAll(selector)) as HTMLElement[];
  const target = nodes.find((node) => (node.textContent ?? "").trim().includes(text));
  if (!target) return false;
  target.click();
  return true;
}

function attachFile(name: string, bytes: Uint8Array, type: string): boolean {
  const input = document.querySelector('input[type="file"]') as HTMLInputElement | null;
  if (!input) return false;
  const file = new File([bytes], name, { type });
  Object.defineProperty(input, "files", { value: [file], configurable: true });
  input.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
}

async function run() {
  const report: Record<string, unknown> = {};
  const container = document.getElementById("root");
  if (!container) throw new Error("no root");
  const root = createRoot(container);
  root.render(<App />);
  report.rendered = await waitForText("Every document, ready for");

  // Go to the PDF → Word tool through the navigation link.
  const link = document.querySelector('a[href="/tool/pdf-to-word"]') as HTMLAnchorElement;
  link.click();
  await wait(400);
  report.toolLoaded = await waitForText("PDF to Word");

  const fixture = (window as unknown as { __FIXTURE_PDF__: Uint8Array }).__FIXTURE_PDF__;
  const corrupted = (window as unknown as { __FIXTURE_BAD__: Uint8Array }).__FIXTURE_BAD__;

  report.fileAttached = attachFile("report-fr.pdf", fixture, "application/pdf");
  await wait(250);
  report.fileListed = Boolean(document.body.textContent?.includes("report-fr.pdf"));

  report.submitClicked = clickByText("button", "Convert now");
  report.progressShown = await waitForText("Converting", 20_000);
  report.succeeded = await waitForText("Ready to download", 90_000);
  report.artifactShown = Boolean(document.body.textContent?.includes("report-fr.docx"));
  report.downloadButton = Boolean(
    Array.from(document.querySelectorAll("button")).find((button) =>
      (button.textContent ?? "").includes("Download"),
    ),
  );
  report.historyRecorded = Boolean(localStorage.getItem("docupro.history.v1")?.includes("pdf-to-word"));

  // Error handling path: a corrupted PDF must never expose a download.
  window.history.pushState({}, "", "/tool/pdf-to-text");
  window.dispatchEvent(new PopStateEvent("popstate"));
  await wait(400);
  attachFile("corrupted.pdf", corrupted, "application/pdf");
  await wait(250);
  clickByText("button", "Convert now");
  report.errorShown = await waitForText("Conversion could not be completed", 60_000);
  report.errorText =
    (document.querySelector('[role="alert"]') as HTMLElement | null)?.textContent?.slice(0, 400) ??
    (document.body.textContent ?? "").slice(-600);
  report.noDownloadOnError = !(
    Array.from(document.querySelectorAll("button")).some((button) =>
      (button.textContent ?? "").includes("Download"),
    ) && (document.body.textContent ?? "").includes("Ready to download")
  );

  console.log("FLOW_REPORT " + JSON.stringify(report));
  root.unmount();
}

run().catch((error) => {
  console.error("FLOW_FAILURE", error);
});
