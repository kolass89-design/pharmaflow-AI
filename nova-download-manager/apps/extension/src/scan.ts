import { findDirectMedia } from './detect';

/** Injected on demand by the popup (activeTab) — no permanent presence needed. */
(window as unknown as { __novaScan: () => unknown }).__novaScan = () => findDirectMedia(document, location.href);
