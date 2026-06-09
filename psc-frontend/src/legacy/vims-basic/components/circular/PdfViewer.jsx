// src/components/dashboardlayout/PdfViewer.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Download, CheckCircle2, ArrowLeft } from "lucide-react";
import * as pdfjsLib from "pdfjs-dist";

// Set worker for PDF.js (adjust path if needed)
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

const PdfViewer = ({
  user,
  notification,
  onAcknowledge,
  onBack,
  canAcknowledge,
  canDownload,
}) => {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasAcknowledged, setHasAcknowledged] = useState(false);
  const [isScrolledToBottom, setIsScrolledToBottom] = useState(false);

  const pdfContainerRef = useRef(null);

  // ðŸ”¹ Fetch PDF URL
  console.log('PdfViewer notification', notification);
  useEffect(() => {
    const fetchPdfUrl = async () => {
      try {
        console.log('notification.id', notification.id);
        console.log('user.crew_id', user.crew_id);
        const res = await fetch(
          `http://localhost:8000/api/circular/api/msc/pdf-url/?notificationId=${encodeURIComponent(notification.id)}&crew_id=${user.crew_id}`
        );

        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.error || 'PDF not available');
        }

        const data = await res.json();
        const url = data.pdf_url || data.attachment_url;
        if (!url) throw new Error('No PDF URL found');
        setPdfUrl(url);
      } catch (err) {
        console.error('PDF fetch error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (notification?.id && user?.crew_id) {
      fetchPdfUrl();
    }
  }, [notification?.id, user?.crew_id]);

  // ðŸ”¹ Render PDF with PDF.js
  useEffect(() => {
    if (!pdfUrl || !pdfContainerRef.current) return;

    const renderPdf = async () => {
      try {
        const loadingTask = pdfjsLib.getDocument(pdfUrl);
        const pdfDoc = await loadingTask.promise;
        const container = pdfContainerRef.current;
        container.innerHTML = ""; // Clear previous

        const numPages = pdfDoc.numPages;
        for (let i = 1; i <= numPages; i++) {
          const page = await pdfDoc.getPage(i);
          const viewport = page.getViewport({ scale: 1.5 });
          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");
          canvas.height = viewport.height;
          canvas.width = viewport.width;

          await page.render({ canvasContext: ctx, viewport }).promise;

          const pageDiv = document.createElement("div");
          pageDiv.style.marginBottom = "24px";
          pageDiv.appendChild(canvas);

          // Optional: page number
          const pageNumEl = document.createElement("div");
          pageNumEl.textContent = `Page ${i} of ${numPages}`;
          pageNumEl.style.textAlign = "center";
          pageNumEl.style.fontSize = "12px";
          pageNumEl.style.color = "#666";
          pageNumEl.style.marginTop = "8px";
          pageDiv.appendChild(pageNumEl);

          container.appendChild(pageDiv);
        }

        // ðŸ”¹ Scroll listener for bottom detection
        const handleScroll = () => {
          const el = container;
          const isBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 10;
          setIsScrolledToBottom(isBottom);
        };

        container.addEventListener("scroll", handleScroll);
        return () => container.removeEventListener("scroll", handleScroll);
      } catch (err) {
        console.error("PDF render error:", err);
        setError("Failed to render PDF");
      }
    };

    renderPdf();
  }, [pdfUrl]);

  // ðŸ”¹ Handle Acknowledgment
  const handleAcknowledgeClick = async () => {
    if (hasAcknowledged) return;
console.log('Acknowledging notification:', notification.id,user.crew_id,user.role);
    try {
      const res = await fetch('http://localhost:8000/api/circular/api/msc/read-ack/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          msc_sr_no: notification.id,
          crew_id: user.crew_id,
          crew_role: user.role,
        }),
      });

      if (res.ok) {
        alert('Acknowledged successfully!');
        setHasAcknowledged(true);
        onAcknowledge?.(notification);
        onBack();
      } else {
        const errorData = await res.json();
        alert('Failed: ' + (errorData.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('Acknowledge error:', err);
      alert('Network error');
    }
  };

  // ðŸ”¹ Handle Download
  const handleDownloadPdf = () => {
    if (pdfUrl) {
      const link = document.createElement('a');
      link.href = pdfUrl;
      link.download = `MSC-${notification.id}.pdf`;
      link.click();
    }
  };

  // ðŸŸ¡ Loading / Error states
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-slate-500">Loading PDF...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* ðŸ”¸ Header */}
      <div className="sticky top-0 z-30 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="text-slate-600 hover:text-slate-800 flex items-center gap-1"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to List
            </button>
            <h1 className="font-semibold text-slate-800">PDF Viewer</h1>
          </div>

          {canDownload && pdfUrl && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadPdf}
              className="flex items-center gap-1 bg-green-600 text-white border-green-600 hover:bg-green-700 hover:border-green-700"
            >
              <Download className="h-4 w-4" />
              Download
            </Button>
          )}
        </div>
      </div>

      

      {/* ðŸ”¸ PDF Container */}
      <div
        ref={pdfContainerRef}
        className="max-w-7xl mx-auto px-4 pb-24 overflow-y-auto"
        style={{ maxHeight: "calc(100vh - 220px)" }}
      >
        {/* PDF pages rendered by PDF.js */}
      </div>

      {/* ðŸ”¸ Scroll-to-bottom Ack Button */}
      {canAcknowledge && !hasAcknowledged && isScrolledToBottom && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4 shadow-lg">
          <div className="max-w-7xl mx-auto flex justify-center">
            <Button
              variant="default"
              size="lg"
              onClick={handleAcknowledgeClick}
              className="bg-green-600 hover:bg-green-700 flex items-center gap-2 px-6 py-3"
            >
              Read & Acknowledge
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PdfViewer;