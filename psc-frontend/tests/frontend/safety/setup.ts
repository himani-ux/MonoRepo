import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach } from "vitest";
import { cleanup } from "@testing-library/react";

class ResizeObserverMock {
  observe() {}

  unobserve() {}

  disconnect() {}
}

function resizeTo(width: number, height: number) {
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    value: width,
    writable: true,
  });
  Object.defineProperty(window, "innerHeight", {
    configurable: true,
    value: height,
    writable: true,
  });
  window.dispatchEvent(new Event("resize"));
}

beforeEach(() => {
  resizeTo(768, 1024);

  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: () => {},
      addListener: () => {},
      dispatchEvent: () => false,
      removeEventListener: () => {},
      removeListener: () => {},
    }),
    writable: true,
  });

  Object.defineProperty(window, "ResizeObserver", {
    configurable: true,
    value: ResizeObserverMock,
    writable: true,
  });

  Object.defineProperty(window, "scrollTo", {
    configurable: true,
    value: () => {},
    writable: true,
  });
});

afterEach(() => {
  cleanup();
});

Object.defineProperty(window, "resizeTo", {
  configurable: true,
  value: resizeTo,
  writable: true,
});
