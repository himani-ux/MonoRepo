// src/components/DeletedEntriesView.jsx
import React, { useState, useEffect } from 'react';
import { Panel, Button, Card, Stack } from "../../components/orb/OrbUI";
import { formatDate } from '../../utils/orb/orbUtils'; // Import your date formatting helper
import { useAuth } from '../../hooks/auth/useAuth'; // Import the useAuth hook to get user info
import PageLayout from '../../components/layout/PageLayout'; // Import the PageLayout component

const DeletedEntriesView = () => {
  const { user } = useAuth(); // Get user info from auth context
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [vesselId, setVesselId] = useState(user?.vessel_id || ''); // Get vessel ID from user info or set to empty
  const [vessel, setVessel] = useState(null);

  // Function to fetch deleted entries from the NEW independent backend API
  const fetchDeletedEntries = async (vesselId) => {
    if (!vesselId) {
      setError("Vessel not selected. Please select a vessel first.");
      return [];
    }

    setLoading(true);
    setError(null); 
    try {
      // Call the NEW independent backend endpoint for deleted entries
      const response = await fetch(`http://localhost:8000/api/orb/api/deleted-entries/?vessel_id=${vesselId}`, {
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
      console.log("Fetched deleted entries (independent API):", data);
      return data; // Return the array of entries

    } catch (err) {
      console.error("Error fetching deleted entries (independent API):", err);
      setError(`Error fetching entries: ${err.message}`);
      return []; // Return an empty array on error
    } finally {
      setLoading(false); // Stop loading indicator
    }
  };

  // Function to load entries when component mounts or vesselId changes
  const loadEntries = async () => {
    const fetchedEntries = await fetchDeletedEntries(vesselId);
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
    return <div className="deleted-entries-view">Loading deleted entries...</div>;
  }

  // Render error state
  if (error) {
    return <div className="deleted-entries-view">Error: {error}</div>;
  }

  // Render the table with entries using the specific format
  return (
  
    
    <div className="deleted-entries-view orb-theme"> {/* Apply your theme class if needed */}
      <Card>
        <div className="p-card-title">
          <h2>Deleted ORB Entries</h2>
        </div>
        <div className="p-card-content">
          {/* Refresh Button */}
          <div style={{ marginBottom: '1rem', textAlign: 'right' }}>
            <button
              className="p-button p-component" // Use PrimeReact button styles or your custom styles
              onClick={handleRefresh}
              disabled={loading} // Disable button while loading
            >
              Refresh
            </button>
          </div>

          {/* Display current vessel name (using the fetched vessel object) - STYLING APPLIED HERE */}
          <div style={{
            marginBottom: '1rem',
            fontSize: '0.9em',
            color: '#495057', // Slightly darker for better readability
            display: 'flex', // Use flex for icon alignment
            alignItems: 'center', // Vertically align icon and text
            gap: '6px', // Space between icon and text
            padding: '4px 0', // Small vertical padding if needed
            borderBottom: '1px dashed #ced4da', // Optional subtle underline
            paddingBottom: '6px'
          }}>

            <span>
              {vessel ? `Vessel: ${vessel.vesselName || 'N/A'}` : 'Loading...'}
            </span>
          </div>

          {/* Entries Table */}
          <div style={{ overflowX: 'auto', width: '100%', margin: '1rem 0' }}>
            <table className="orb-table" style={{ minWidth: '800px', width: '100%' }}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Code</th>
                  <th>Item No.</th>
                  <th>Record of operations/signature of officer in charge</th>
                  <th>Status</th> {/* Add Status column */}
                  <th>Is Deleted</th> {/* Add Is Deleted column */}
                  <th>Updated By (Deletion)</th> {/* Add Updated By column */}
                  <th>Updated At (Deletion)</th> {/* Add Updated At column */}
                </tr>
              </thead>
              <tbody>
                {entries.length === 0 ? (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center' }}>No deleted entries found.</td>
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
                            {/* Only show Status, Is Deleted, Updated By, and Updated At on the first line of the entry */}
                            {lineIndex === 0 ? (
                              <>
                                <td>{entry.status}</td> {/* Display status */}
                                <td>{entry.is_deleted ? 'Yes' : 'No'}</td> {/* Display deletion status */}
                                <td>{entry.updated_by || 'N/A'}</td> {/* Display who updated (likely triggered deletion) */}
                                <td>{entry.updated_at ? formatDate(entry.updated_at) : 'N/A'}</td> {/* Display when updated (deletion time) */}
                              </>
                            ) : (
                              <>
                                <td></td> {/* Empty cell for Status on subsequent lines */}
                                <td></td> {/* Empty cell for Is Deleted on subsequent lines */}
                                <td></td> {/* Empty cell for Updated By on subsequent lines */}
                                <td></td> {/* Empty cell for Updated At on subsequent lines */}
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

export default DeletedEntriesView;
