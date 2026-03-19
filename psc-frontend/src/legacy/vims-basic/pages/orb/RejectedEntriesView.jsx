// src/components/RejectedEntriesView.jsx
import React, { useState, useEffect } from 'react';
import { Button, Card } from "../../components/orb/OrbUI";
import { formatDate } from '../../utils/orb/orbUtils'; 
import { useAuth } from '../../hooks/auth/useAuth'; 
import PageLayout from '../../components/layout/PageLayout'; // Import the PageLayout component

const RejectedEntriesView = () => {
  const { user } = useAuth(); // Get user info from auth context
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [vesselId, setVesselId] = useState(user?.vessel_id || ''); // Use vessel_id from user context
  const [vessel, setVessel] = useState(null);

  // Function to fetch rejected entries from the NEW independent backend API
  const fetchRejectedEntries = async (vesselId) => {
    if (!vesselId) {
      setError("Vessel not selected. Please select a vessel first.");
      return [];
    }

    setLoading(true);
    setError(null);

    try {
      // Call the NEW independent backend endpoint for rejected entries
      const response = await fetch(`http://localhost:8000/api/orb/api/rejected-entries/?vessel_id=${vesselId}`, {
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
      console.log("Fetched rejected entries (independent API):", data);
      return data; // Return the array of entries

    } catch (err) {
      console.error("Error fetching rejected entries (independent API):", err);
      setError(`Error fetching entries: ${err.message}`);
      return []; // Return an empty array on error
    } finally {
      setLoading(false); // Stop loading indicator
    }
  };

  // Function to load entries when component mounts or vesselId changes
  const loadEntries = async () => {
    const fetchedEntries = await fetchRejectedEntries(vesselId);
    // No grouping needed here as the independent API returns flat list
    // The table logic below handles the line splitting and item number assignment
    setEntries(fetchedEntries); // Update state with fetched entries
  };

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
        // ✅ Handle both array and paginated response
        const vesselList = Array.isArray(data) ? data : (data.results || []);

        // ✅ Find the selected vessel (case-insensitive comparison)
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
  }, [vesselId]); // Dependency: re-run if vesselId changes

  // Handler to refresh entries
  const handleRefresh = () => {
    loadEntries();
  };

  // Render loading state
  if (loading) {
    return <div className="rejected-entries-view orb-theme orb-page-status">Loading rejected entries...</div>;
  }

  // Render error state
  if (error) {
    return <div className="rejected-entries-view orb-theme orb-page-status">Error: {error}</div>;
  }

  // Render the table with entries using the specific format
  return (
    
    <div className="rejected-entries-view orb-theme orb-page">
      <Card title="Rejected ORB Entries">
          {/* Refresh Button */}
          <div className="orb-toolbar">
            <div className="orb-meta">
              <strong>Vessel:</strong>
              <span>{vessel ? vessel.vesselName || 'N/A' : 'Loading...'}</span>
            </div>
            <Button onClick={handleRefresh} disabled={loading}>
              Refresh
            </Button>
          </div>

          {/* Entries Table */}
          <div className="orb-table-shell">
            <table className="orb-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Code</th>
                  <th>Item No.</th>
                  <th>Record of operations/signature of officer in charge</th>
                  <th>Status</th> {/* Add Status column */}
                  <th>Rejected By</th> {/* Add Rejected By column */}
                  <th>Rejected At</th> {/* Add Rejected At column */}
                </tr>
              </thead>
              <tbody>
                {entries.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="orb-empty">No rejected entries found.</td>
                  </tr>
                ) : (
                  entries.map((entry, entryIndex) => {
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
                          <tr key={`${entry.id}-${lineIndex}`}>
                            <td>{showDate ? formattedDate : ''}</td>
                            <td>{showCode ? entry.code : ''}</td>
                            <td>{itemNo}</td>
                            <td style={{ whiteSpace: 'pre-line' }}>{line}</td>
                            {/* Only show Status, Rejected By, and Rejected At on the first line of the entry */}
                            {lineIndex === 0 ? (
                              <>
                                <td>{entry.status}</td> {/* Display status */}
                                <td>{entry.rejected_by || 'N/A'}</td> {/* Display rejected by */}
                                <td>{entry.rejected_at ? formatDate(entry.rejected_at) : 'N/A'}</td> {/* Display rejected at */}
                              </>
                            ) : (
                              <>
                                <td></td> {/* Empty cell for Status on subsequent lines */}
                                <td></td> {/* Empty cell for Rejected By on subsequent lines */}
                                <td></td> {/* Empty cell for Rejected At on subsequent lines */}
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
      </Card>
    </div>
   
  );
};

export default RejectedEntriesView;
