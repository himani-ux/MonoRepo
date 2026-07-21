import PdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?worker";

let workerPort = null;

export const configurePdfJsWorker = (pdfjsLib) => {
  if (typeof Worker === "undefined") {
    return;
  }

  if (!workerPort) {
    workerPort = new PdfWorker({ type: "module" });
  }

  pdfjsLib.GlobalWorkerOptions.workerPort = workerPort;
};
