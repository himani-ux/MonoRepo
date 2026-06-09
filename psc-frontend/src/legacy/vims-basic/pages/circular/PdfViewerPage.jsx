// src/components/PdfViewerPage.jsx
import { useEffect, useState, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import * as pdfjsLib from "pdfjs-dist";
import { useAuth } from "../../hooks/auth/useAuth";

// IMPORTANT: Set worker source (adjust path if needed)
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

export default function PdfViewerPage() {

  const { user } = useAuth();
  console.log("PdfViewerPage rendered");
  const [searchParams] = useSearchParams();
  const notificationId = searchParams.get("notificationId");
  const navigate = useNavigate();

  const [pdfUrl, setPdfUrl] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasAcknowledged, setHasAcknowledged] = useState(false);
  const [isScrolledToBottom, setIsScrolledToBottom] = useState(false);

  const pdfContainerRef = useRef(null);
  const pdfViewerRef = useRef(null);
  const pdfDocRef = useRef(null);
  const pdfPageRef = useRef(null);

  useEffect(() => {
    console.log("PdfViewerPage useEffect triggered");
    if (!notificationId) {
      setError("Missing notification ID");
      setLoading(false);
      return;
    }

    const fetchPdfUrl = async () => {
      const currentUser = user
      if (!currentUser?.crew_id) {
        setError("Not logged in");
        setLoading(false);
        return;
      }

      try {
        console.log("PdfViewerPage loaded â€” notificationId:", notificationId);
        console.log("crew_id:", currentUser.crew_id)
        console.log("crew_role:", currentUser.role)
        const res = await fetch(
          `http://localhost:8000/api/circular/api/msc/pdf-url/?notificationId=${encodeURIComponent(notificationId)}&crew_id=${currentUser.crew_id}`
        );
        console.log("Fetch response:", res.status);

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || "Failed to load PDF");
        }

        const data = await res.json();
        console.log("PDF URL data:", data);
        setPdfUrl(data.attachment_url);
      } catch (err) {
        console.error("Error fetching PDF URL:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    console.log("Fetching PDF URL for notificationId:", notificationId);
    fetchPdfUrl();
    console.log("PdfViewerPage useEffect completed");
  }, [notificationId]);

  // Render PDF using PDF.js
  useEffect(() => {
    if (!pdfUrl || !pdfContainerRef.current) return;

    const renderPdf = async () => {
      try {
        const loadingTask = pdfjsLib.getDocument(pdfUrl);
        const pdfDoc = await loadingTask.promise;
        pdfDocRef.current = pdfDoc;

        const numPages = pdfDoc.numPages;
        const container = pdfContainerRef.current;

        // Clear previous content
        container.innerHTML = "";

        for (let pageNum = 1; pageNum <= numPages; pageNum++) {
          const page = await pdfDoc.getPage(pageNum);
          const viewport = page.getViewport({ scale: 1.5 }); // Adjust scale as needed

          const canvas = document.createElement("canvas");
          const context = canvas.getContext("2d");
          canvas.height = viewport.height;
          canvas.width = viewport.width;

          const renderContext = {
            canvasContext: context,
            viewport: viewport,
          };

          await page.render(renderContext).promise;

          const pageDiv = document.createElement("div");
          pageDiv.style.marginBottom = "20px";
          pageDiv.appendChild(canvas);
          container.appendChild(pageDiv);

          // Add page number indicator (optional)
          const pageNumEl = document.createElement("div");
          pageNumEl.textContent = `Page ${pageNum} of ${numPages}`;
          pageNumEl.style.textAlign = "center";
          pageNumEl.style.fontSize = "12px";
          pageNumEl.style.color = "#666";
          pageDiv.appendChild(pageNumEl);
        }

        // Set up scroll listener
        const handleScroll = () => {
          const container = pdfContainerRef.current;
          const scrollTop = container.scrollTop;
          const scrollHeight = container.scrollHeight;
          const clientHeight = container.clientHeight;

          // Check if scrolled to bottom (within 10px tolerance)
          if (scrollTop + clientHeight >= scrollHeight - 10) {
            setIsScrolledToBottom(true);
          } else {
            setIsScrolledToBottom(false);
          }
        };

        container.addEventListener("scroll", handleScroll);
        return () => container.removeEventListener("scroll", handleScroll);

      } catch (err) {
        console.error("Error rendering PDF:", err);
        setError("Failed to render PDF");
      }
    };

    renderPdf();
  }, [pdfUrl]);

  // Set up automatic acknowledgment timer
  

  const handleReadAck = async () => {
    if (hasAcknowledged) {
      console.log("Already acknowledged.");
      return;
    }

    const currentUser = user
    if (!currentUser?.crew_id || !notificationId) {
      alert("Invalid session or notification");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/msc/read-ack/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          msc_sr_no: notificationId,
          crew_id: currentUser.crew_id,
          crew_role: currentUser.role
        }),
      })

      if (response.ok) {
        console.log("Acknowledged automatically after viewing time!");
        setHasAcknowledged(true);
        console.log(currentUser.role)
        currentUser.role === 'MASTER' ? navigate("/master") : navigate("/crew");
      } else {
        const err = await response.json();
        alert("Failed: " + (err.error || "Unknown error"));
        setHasAcknowledged(false);
      }
    } catch (err) {
      console.error("Network error:", err);
      alert("Network error");
      setHasAcknowledged(false);
    }
  };

  if (loading) return <div className="p-8">Loading PDF...</div>;
  if (error) return <div className="p-8 text-red-600">{error}</div>;

  return (
    <div className="min-h-screen flex flex-col bg-sky-50">
      <header className="bg-white p-4 shadow flex items-center justify-between">
        <h1 className="text-lg font-semibold">Review Document</h1>
        {pdfUrl && (
          <a
            href={pdfUrl}
            download={`MSC-${notificationId}.pdf`}
            className="px-2 py-[6px] bg-green-600 text-white text-xs rounded hover:bg-green-700 transition"
          >
            Download PDF
          </a>
        )}
        
      </header>

      <div 
        className="flex-1 p-4 overflow-y-auto"
        ref={pdfContainerRef}
        style={{ maxHeight: "calc(100vh - 150px)" }} // Adjust as needed
      >
        {/* PDF will be rendered here by PDF.js */}
      </div>

      {/* Acknowledge Button (appears only when scrolled to bottom AND not yet acknowledged) */}
      {!hasAcknowledged && isScrolledToBottom && (
        <div className="p-4 bg-blue-50 border-t flex justify-center">
          <button
            onClick={handleReadAck}
            className="py-3 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition -ml-15"
          >
            Read & Acknowledge
          </button>
        </div>
      )}

    </div>
  );
}