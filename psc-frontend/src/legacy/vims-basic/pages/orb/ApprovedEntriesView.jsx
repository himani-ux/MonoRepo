// src/components/ApprovedEntriesView.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Panel, Button, Card, Stack } from "../../components/orb/OrbUI"; // Assuming these are your custom components
import { formatDate } from '../../utils/orb/orbUtils'; // Import your date formatting helper
import { useAuth } from '../../hooks/auth/useAuth'; // Import your authentication hook
import PageLayout from '../../components/layout/PageLayout'; // Import the PageLayout component

const ApprovedEntriesView = () => {
  const {user} = useAuth(); 
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [vesselId] = useState(user?.vessel_id); // Get vessel ID from user object
  // Add state for vessel name and imo number
  const [vessel, setVessel] = useState(null);

  // Function to fetch approved entries from the NEW independent backend API
  const fetchApprovedEntries = async (vesselId) => {
    if (!vesselId) {
      setError("Vessel not selected. Please select a vessel first.");
      return [];
    }

    setLoading(true);
    setError(null);
    try {
      // Call the NEW independent backend endpoint for approved entries
      const response = await fetch(`http://localhost:8000/api/orb/api/approved-entries/?vessel_id=${vesselId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Include authorization headers if required
        },
      });

      if (!response.ok) {
        const errorText = await response.text(); // Get error details
        throw new Error(`${response.status} - ${errorText}`);
      }

      const data = await response.json(); // Use .json() for JsonResponse from Django
      console.log("Fetched approved entries (independent API):", data);
      return data; // Return the array of entries

    } catch (err) {
      console.error("Error fetching approved entries (independent API):", err);
      setError(`Error fetching entries: ${err.message}`);
      return []; // Return an empty array on error
    } finally {
      setLoading(false); 
    }
  };

  // Function to load entries when component mounts or vesselId changes
  const loadEntries = useCallback(async () => {
    const fetchedEntries = await fetchApprovedEntries(vesselId);
    // No grouping needed here as the independent API returns flat list
    // The table logic below handles the line splitting and item number assignment
    setEntries(fetchedEntries); // Update state with fetched entries
  }, [vesselId]);

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
        // Handle both array and paginated Response
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
          alert(" Vessel not found. Please select a vessel.");
        }
      })
      .catch(err => {
        console.error(" Network error: Cannot load vessel data.", err);
        alert(" Network error: Cannot load vessel data. Check backend.");
      });
  }, [vesselId]); // Dependency: re-run if vesselId changes


  // Load entries when component mounts or vesselId changes
  useEffect(() => {
    loadEntries();
  }, [vesselId, loadEntries]); // Dependency: re-run if vesselId changes 

  // constant handler to refresh entries
  const handleRefresh = () => {
    loadEntries();
  };

  // Render loading state
  if (loading) {
    return (
      <div className="approved-entries-view orb-theme" style={{ padding: '20px' }}>
        <p>Loading approved entries...</p>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="approved-entries-view orb-theme" style={{ padding: '20px' }}>
        <p>Error: {error}</p>
      </div>
    );
  }

  // Render the table with entries using the specific format
  return (
      
    
    <div className="approved-entries-view orb-theme" style={{ padding: '20px' }}>
      <Card>
        <div className="p-card-title" style={{ backgroundColor: '#f0f0f0', padding: '10px', borderRadius: '4px 4px 0 0' }}>
          <h2 style={{ margin: 0, fontSize: '1.5em', fontWeight: 'bold', color: '#333' }}>Approved ORB Entries</h2>
        </div>
        <div className="p-card-content" style={{ padding: '20px' }}>
          {/* Refresh Button */}
          <div style={{ marginBottom: '1rem', textAlign: 'right' }}>
            <button
              className="p-button p-component" // Use PrimeReact button styles or your custom styles
              onClick={handleRefresh}
              disabled={loading} // Disable button while loading
              style={{
                padding: '8px 16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '14px',
              }}
            >
              Refresh
            </button>
          </div>

          {/* Vessel Name styling */}
          <div style={{
            marginBottom: '1rem',
            fontSize: '0.9em',
            color: '#495057',
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px',
            padding: '4px 0', 
            borderBottom: '1px dashed #ced4da', 
            paddingBottom: '6px'
          }}>
            <span style={{ fontSize: '1.1em' }}>* </span> 
            <span>
              {vessel ? `Vessel: ${vessel.vesselName || 'N/A'}` : 'Loading...'}
            </span>
          </div>

          {/* Entries Table - with the proper formatting */}
          <div style={{ overflowX: 'auto', width: '100%', margin: '1rem 0' }}>
            <table
              className="orb-table"
              style={{
                minWidth: '800px',
                width: '100%',
                borderCollapse: 'collapse',
                fontFamily: 'Courier New, monospace', // the same font is used in chief's dashboard
                fontSize: '12px',
              }}
            >
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
                  <th style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'left', fontWeight: 'bold' }}>Date</th>
                  <th style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'left', fontWeight: 'bold' }}>Code</th>
                  <th style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'left', fontWeight: 'bold' }}>Item No.</th>
                  <th style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'left', fontWeight: 'bold' }}>Record of operations/signature of officer in charge</th>
                  <th style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'left', fontWeight: 'bold' }}>Status</th>
                  <th style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'left', fontWeight: 'bold' }}>Approved By</th>
                  <th style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'left', fontWeight: 'bold' }}>Approved At</th>
                </tr>
              </thead>
              <tbody>
                {entries.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '20px', color: '#6c757d' }}>No approved entries found.</td>
                  </tr>
                ) : (
                  entries.map((entry) => { // Iterate through the flat list of entries
                    const lines = (entry.record_of_operation || '').split('\n').filter(line => line.trim() !== '');
                    const formattedDate = formatDate(entry.date);

                    return lines.map((line, lineIndex) => { // Iterate through lines of each entry
                      let itemNo = '';
                      let showDate = false;
                      let showCode = false;

                      // First line always shows Date, Code, and first item_no
                      if (lineIndex === 0) {
                        showDate = true;
                        showCode = true;
                        itemNo = entry.item_no || '';
                      } else {
                        // For subsequent lines, infer item_no based on order and content
                        // This logic is copied from the ORBTable component
                        switch (entry.code) {
                          case 'A':
                            // 1. Tank Identity
                            if (line.startsWith('TANK(S) BALLASTED')) itemNo = '1';

                            // 2. Cleaned Since Last Oil
                            else if (line.includes('TANK CLEANED SINCE') || line.includes('NOT CLEANED – PREVIOUS OIL')) itemNo = '2';

                            // 4.1 Ballast Start/End
                            if (line.startsWith('START BALLAST')) itemNo = '4.1';

                            // 3.1 Cleaning Start/Stop with Position
                            else if (((lineIndex == 2) || line.includes('HRS')) && line.includes('START') || line.includes('Stop')) itemNo = '3.1';

                            // 3.2 Method Used
                            if (line.includes('RINSING') || line.includes('STEAMING') || line.includes('CHEMICAL')) itemNo = '3.2';
                            // 3.3 Transfer to Slop
                            if (line.startsWith('CLEANING WATER TO')) itemNo = '3.3';

                            // 4.2 Ballast Quantity
                            else if (line.includes('BALLAST QUANTITY')) itemNo = '4.2';

                            break;

                          case 'B':
                            // Use line order after the first line
                            if (lineIndex === 1) itemNo = '6';  // pos_start
                            else if (lineIndex === 2) itemNo = '7';  // pos_end
                            // else if (lineIndex === 3) itemNo = '8';  // ship_speeds
                            else if (lineIndex === 3) {
                              // Use the stored method from details (most reliable)
                              // But since we only have record_of_operation, check content
                              if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
                                itemNo = '9.1';
                              } else {
                                // Assume it's 9.2 if not 9.1 and line is not quantity
                                itemNo = '9.2';
                              }
                            }
                            // Quantity is always 10, regardless of index
                            else if (line.includes('M³')) {
                              itemNo = '10';
                            }
                            break;

                          case 'C':
                            if (lineIndex === 0) {
                              itemNo = entry.item_no || '';
                            }
                            // 11.1 handled on first line
                            if (line.includes('M³') && !line.includes('COLLECTED') && !line.includes('RETAINED')) {
                              itemNo = '11.2';
                            }
                            if ((lineIndex === 2) && line.includes('M³')) {
                              itemNo = '11.3';
                            }
                            if (lineIndex === 3) {
                              itemNo = '11.4';
                            } else if (line.includes('RECEPTION FACILITY')) {
                              itemNo = '12.1';
                            } else if (line.includes('TRANSFERRED TO')) {
                              itemNo = '12.2';
                            } else if (line.includes('INCINERATED')) {
                              itemNo = '12.3';
                            } else if (lineIndex === 7) {
                              itemNo = '12.4';
                            }
                            break;

                          case 'D':
                            if (lineIndex === 1) itemNo = '14';
                            else if (line.includes('THROUGH 15 PPM EQUIPMENT')) itemNo = '15.1';
                            else if (line.includes('TO PORT RECEPTION FACILITIES OF')) {
                              itemNo = '15.2';
                            }
                            else if (line.includes('TRANSFERRED TO') || line.includes('RETAINED IN TANK')) itemNo = '15.3';
                            break;

                          case 'F':
                            if (line.includes('FAILURE STARTED')) {
                              itemNo = '19';
                            } else if ((lineIndex === 1) || line.includes('UNKNOWN')) {
                              itemNo = '20';
                            }
                            if (lineIndex === 2) {
                              itemNo = '21';
                            }
                            break;

                          case 'G':
                            if (lineIndex === 1) {
                              itemNo = '23'; // Position
                            } else if (lineIndex === 2) {
                              itemNo = '24'; // Quantity and Type
                            } else if (lineIndex === 3) {
                              itemNo = '25'; // Remarks
                            }
                            break;

                          case 'H':
                            if (lineIndex === 1) itemNo = '26.2';
                            else if (line.includes('FUEL OIL BUNKERED IN TANKS') && line.includes('FUEL')) itemNo = '26.3';
                            else if (line.includes('LUBE BUNKERED IN TANKS') && line.includes('LUB')) itemNo = '26.4';
                            break;

                          case 'I':
                            if (entry.code === 'I') {
                              if (lineIndex === 0) {
                                itemNo = '';
                              } else {
                                itemNo = ''; // All other lines in Code I have no item number
                              }
                            }
                            break; // Added break for case 'I'

                          default:
                            // Fallback for other codes
                            if (line.startsWith('START:')) itemNo = '26.2';
                            else if (line.includes('BUNKERED IN TANKS')) itemNo = line.includes('FUEL') ? '26.3' : '26.4';
                            else if (line.includes('TANK(S) BALLASTED')) itemNo = '1';
                            else if (line.includes('TANK CLEANED SINCE') || line.includes('NOT CLEANED – PREVIOUS OIL')) itemNo = '2';
                            else if (line.includes('START BALLAST')) itemNo = '4.1';
                            else if (line.includes('START') && !line.includes('BALLAST')) itemNo = '3.1';
                            else if (line.startsWith('METHOD USED')) itemNo = '3.2';
                            else if (line.startsWith('CLEANING WATER TO')) itemNo = '3.3';
                            else if (line.includes('BALLAST QUANTITY')) itemNo = '4.2';
                            else if (line.includes('THROUGH 15 PPM EQUIPMENT')) itemNo = '9.1';
                            else if (line.includes('RECEPTION')) itemNo = '9.2';
                            else if (line.includes('m³') || line.includes('M³')) itemNo = '10';
                            break;
                        }

                        // Always show SIGNED on its own line
                        if (line.startsWith('SIGNED:')) itemNo = '';
                      }

                      return (
                        <tr
                          key={`${entry.id}-${lineIndex}`}
                          style={{
                            backgroundColor: lineIndex % 2 === 0 ? '#ffffff' : '#f9f9f9', // Alternate row colors
                            // Hover effect could be added here if desired
                          }}
                        >
                          <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{showDate ? formattedDate : ''}</td>
                          <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{showCode ? entry.code : ''}</td>
                          <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{itemNo}</td>
                          <td style={{ padding: '6px', border: '1px solid #dee2e6', whiteSpace: 'pre-line' }}>{line}</td>
                          {/* Only show Status, Approved By, and Approved At on the first line of the entry */}
                          {lineIndex === 0 ? (
                            <>
                              <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{entry.status}</td> {/* Display status */}
                              <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{entry.approved_by || 'N/A'}</td> {/* Display approved by */}
                              <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{entry.approved_at ? formatDate(entry.approved_at) : 'N/A'}</td> {/* Display approved at */}
                            </>
                          ) : (
                            <>
                              <td style={{ padding: '6px', border: '1px solid #dee2e6' }}></td> {/* Empty cell for Status on subsequent lines */}
                              <td style={{ padding: '6px', border: '1px solid #dee2e6' }}></td> {/* Empty cell for Approved By on subsequent lines */}
                              <td style={{ padding: '6px', border: '1px solid #dee2e6' }}></td> {/* Empty cell for Approved At on subsequent lines */}
                            </>
                          )}
                        </tr>
                      );
                    });
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
    
  );
};

export default ApprovedEntriesView;
