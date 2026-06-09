// src/components/PDFArchive.jsx
import React, { useState, useEffect } from 'react';
import { Card, Button as OrbUIButton } from '../../components/orb/OrbUI';
import { useAuth } from '../../hooks/auth/useAuth';

const PDFArchive = () => {
  const {user} = useAuth();
  const [pdfs, setPdfs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  // Add state for vessel name and imo number
  const [vessel, setVessel] = useState(null);
  // Get vessel ID from session storage
  const vesselId = user?.vessel_id;

  // Fetch vessel details when component mounts or vesselId changes (similar to ORBHeader)
  useEffect(() => {
    if (!vesselId) return;

    fetch("http://localhost:8000/api/orb/api/vessels/")
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        // Handle both array and paginated response
        const vesselList = Array.isArray(data) ? data : (data.results || []);

        // Find the selected vessel (case-insensitive comparison)
        const selectedVessel = vesselList.find(v => v.id.toLowerCase() === vesselId.toLowerCase());

        if (selectedVessel) {
          setVessel({
            vesselName: selectedVessel.vesselName,
            imoNumber: selectedVessel.imonumber
          });
        } else {
          console.warn("Vessel not found for ID:", vesselId);
          // Consider showing an alert or setting an error state here
          // alert(" Vessel not found. Please select a vessel.");
        }
      })
      .catch(err => {
        console.error(" Network error: Cannot load vessel data.", err);
        // Consider setting an error state here
        // alert(" Network error: Cannot load vessel data. Check backend.");
      });
  }, [vesselId]); // Dependency: re-run if vesselId changes


  const loadPdfs = async (page = 1) => {
    setLoading(true);
    setError(null);

    try {
      // Use the vesselId from state or sessionStorage (it should be available now)
      // const vesselId = sessionStorage.getItem("selectedVesselId"); // Already defined above

      let url = `http://localhost:8000/api/orb/api/list-pdfs/?page=${page}&page_size=10`;
      if (vesselId) {
        url += `&vessel_id=${vesselId}`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`${response.status} - ${text}`);
      }

      const data = await response.json();
      setPdfs(data.pdfs);
      setTotalPages(data.total_pages);
      setCurrentPage(data.current_page);

    } catch (err) {
      console.error("Error fetching PDFs:", err);
      setError(`Error loading PDFs: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPdfs(1);
  }, []);

  const handleDownload = (downloadUrl) => {
    const link = document.createElement('a');
    link.href = `${downloadUrl}`;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      loadPdfs(newPage);
    }
  };

  if (loading) {
    return <div className="pdf-archive orb-theme orb-page-status">Loading PDFs...</div>;
  }

  if (error) {
    return <div className="pdf-archive orb-theme orb-page-status">Error: {error}</div>;
  }

  return (
    <div className="pdf-archive orb-theme orb-page">
      <Card title="PDF Archive">
        <div className="orb-meta">
          <strong>Vessel:</strong>
          <span>{vessel ? vessel.vesselName || 'N/A' : 'Loading...'}</span>
        </div>

        {pdfs.length === 0 ? (
          <p className="orb-empty">No PDFs found.</p>
        ) : (
          <>
            <div className="orb-table-shell">
              <table className="orb-table orb-table-compact">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Description</th>
                    <th>Created By</th>
                    <th>Created At</th>
                    <th>Download</th>
                  </tr>
                </thead>

                <tbody>
                  {pdfs.map((pdf) => (
                    <tr key={pdf.id}>
                      <td>{pdf.title}</td>
                      <td>{pdf.description || '-'}</td>
                      <td>{pdf.created_by}</td>
                      <td>{new Date(pdf.created_at).toLocaleString()}</td>
                      <td>
                        <OrbUIButton
                          onClick={() => handleDownload(pdf.download_url)}
                          variant="secondary"
                          className="orb-download-button"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-cloud-arrow-down-fill" viewBox="0 0 16 16">
                            <path d="M8 2a5.53 5.53 0 0 0-3.594 1.342c-.766.66-1.321 1.52-1.464 2.383C1.266 6.095 0 7.555 0 9.318 0 11.366 1.708 13 3.781 13h8.906C14.502 13 16 11.57 16 9.773c0-1.636-1.242-2.969-2.834-3.194C12.923 3.999 10.69 2 8 2m2.354 6.854-2 2a.5.5 0 0 1-.708 0l-2-2a.5.5 0 1 1 .708-.708L7.5 9.293V5.5a.5.5 0 0 1 1 0v3.793l1.146-1.147a.5.5 0 0 1 .708.708" />
                          </svg>
                          <span>Download</span>
                        </OrbUIButton>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="orb-pagination">
              <OrbUIButton
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                variant="outline"
              >
                Previous
              </OrbUIButton>

              <span className="orb-pagination-status">
                Page {currentPage} of {totalPages}
              </span>

              <OrbUIButton
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                variant="outline"
              >
                Next
              </OrbUIButton>
            </div>
          </>
        )}
      </Card>
    </div>
 
  );
};

export default PDFArchive;
