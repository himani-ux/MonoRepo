// src/components/AllEntriesView.jsx
import React, { useState, useEffect } from 'react';
import { Button, Card } from "../../components/orb/OrbUI";
import { formatDate } from '../../utils/orb/orbUtils'; 
import { useAuth } from '../../hooks/auth/useAuth';




const AllEntriesView = () => {

  const {user} = useAuth();
  
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [vesselId, setVesselId] = useState(user?.vessel_id);

  const fetchAllEntries = async (vesselId) => {
    if (!vesselId) {
      setError("Vessel not selected. Please select a vessel first.");
      return [];
    }

    setLoading(true);
    setError(null);
    try {
      // this is the independent endpoint for all the non deleted entries
      const response = await fetch(`http://localhost:8000/api/orb/api/non-deleted-entries/?vessel_id=${vesselId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text(); // Get error details
        throw new Error(`${response.status} - ${errorText}`);
      }

      const data = await response.json(); // Use .json() for JsonResponse from Django
      console.log("Fetched all non-deleted entries (independent API):", data);
      return data; // Return the array of entries

    } catch (err) {
      console.error("Error fetching all entries (independent API):", err);
      setError(`Error fetching entries: ${err.message}`);
      return []; // Return an empty array on error
    } finally {
      setLoading(false); // Stop loading indicator
    }
  };

  // Function to load entries when component mounts or vesselId changes
  const loadEntries = async () => {
    const fetchedEntries = await fetchAllEntries(vesselId);
   // no grouping required
    setEntries(fetchedEntries); // Update state with fetched entries
  };

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
    return <div className="all-entries-view orb-theme orb-page-status">Loading all entries...</div>;
  }

  // Render error state
  if (error) {
    return <div className="all-entries-view orb-theme orb-page-status">Error: {error}</div>;
  }

  // Render the table with entries using the specific format
  return (
   
    <div className="all-entries-view orb-theme orb-page">
      <Card title="All Non-Deleted ORB Entries">
        <div className="orb-toolbar">
          <div className="orb-meta">
            <strong>Vessel ID:</strong> <span>{vesselId}</span>
          </div>
          <div className="flex justify-end">
            <Button onClick={handleRefresh} disabled={loading}>
              Refresh
            </Button>
          </div>
        </div>

          {/* Entries Table - Using the specific format from ORBTable */}
          <div className="orb-table-shell">
            <table className="orb-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Code</th>
                  <th>Item No.</th>
                  <th>Record of operations/signature of officer in charge</th>
                  {/* No Actions needed here for non-deleted entries view, unless you want edit/delete for specific statuses */}
                </tr>
              </thead>
              <tbody>
                {entries.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="orb-empty">No entries found.</td>
                  </tr>
                ) : (
                  entries.map((entry) => { // Iterate through the flat list of entries
                    const lines = (entry.record_of_operation || '').split('\n').filter(line => line.trim() !== '');
                    const formattedDate = formatDate(entry.date);

                    return lines.map((line, idx) => { // Iterate through lines of each entry
                      let itemNo = '';
                      let showDate = false;
                      let showCode = false;

                      // First line always shows Date, Code, and first item_no
                      if (idx === 0) {
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
                            else if (line.includes('TANK CLEANED SINCE') || line.includes('NOT CLEANED â€“ PREVIOUS OIL')) itemNo = '2';

                            // 4.1 Ballast Start/End
                            if (line.startsWith('START BALLAST')) itemNo = '4.1';

                            // 3.1 Cleaning Start/Stop with Position
                            else if (((idx == 2) || line.includes('HRS')) && line.includes('START') || line.includes('Stop')) itemNo = '3.1';

                            // 3.2 Method Used
                            if (line.includes('RINSING') || line.includes('STEAMING') || line.includes('CHEMICAL')) itemNo = '3.2';
                            // 3.3 Transfer to Slop
                            if (line.startsWith('CLEANING WATER TO')) itemNo = '3.3';

                            // 4.2 Ballast Quantity
                            else if (line.includes('BALLAST QUANTITY')) itemNo = '4.2';

                            break;

                          case 'B':
                            // Use line order after the first line
                            if (idx === 1) itemNo = '6';  // pos_start
                            else if (idx === 2) itemNo = '7';  // pos_end
                            // else if (idx === 3) itemNo = '8';  // ship_speeds
                            else if (idx === 3) {
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
                            else if (line.includes('MÂ³')) {
                              itemNo = '10';
                            }
                            break;

                          case 'C':
                            if (idx === 0) {
                              itemNo = entry.item_no || '';
                            }
                            // 11.1 handled on first line
                            if (line.includes('MÂ³') && !line.includes('COLLECTED') && !line.includes('RETAINED')) {
                              itemNo = '11.2';
                            }
                            if ((idx === 2) && line.includes('MÂ³')) {
                              itemNo = '11.3';
                            }
                            if (idx === 3) {
                              itemNo = '11.4';
                            } else if (line.includes('RECEPTION FACILITY')) {
                              itemNo = '12.1';
                            } else if (line.includes('TRANSFERRED TO')) {
                              itemNo = '12.2';
                            } else if (line.includes('INCINERATED')) {
                              itemNo = '12.3';
                            } else if (idx === 7) {
                              itemNo = '12.4';
                            }
                            break;

                          case 'D':
                            if (idx === 1) itemNo = '14';
                            else if (line.includes('THROUGH 15 PPM EQUIPMENT')) itemNo = '15.1';
                            else if (line.includes('TO PORT RECEPTION FACILITIES OF')) {
                              itemNo = '15.2';
                            }
                            else if (line.includes('TRANSFERRED TO') || line.includes('RETAINED IN TANK')) itemNo = '15.3';
                            break;

                          case 'F':
                            if (line.includes('FAILURE STARTED')) {
                              itemNo = '19';
                            } else if ((idx === 1) || line.includes('UNKNOWN')) {
                              itemNo = '20';
                            }
                            if (idx === 2) {
                              itemNo = '21';
                            }
                            break;

                          case 'G':
                            if (idx === 1) {
                              itemNo = '23'; // Position
                            } else if (idx === 2) {
                              itemNo = '24'; // Quantity and Type
                            } else if (idx === 3) {
                              itemNo = '25'; // Remarks
                            }
                            break;

                          case 'H':
                            if (idx === 1) itemNo = '26.2';
                            else if (line.includes('FUEL OIL BUNKERED IN TANKS') && line.includes('FUEL')) itemNo = '26.3';
                            else if (line.includes('LUBE BUNKERED IN TANKS') && line.includes('LUB')) itemNo = '26.4';
                            break;

                          case 'I':
                            if (entry.code === 'I') {
                              if (idx === 0) {
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
                            else if (line.includes('TANK CLEANED SINCE') || line.includes('NOT CLEANED â€“ PREVIOUS OIL')) itemNo = '2';
                            else if (line.includes('START BALLAST')) itemNo = '4.1';
                            else if (line.includes('START') && !line.includes('BALLAST')) itemNo = '3.1';
                            else if (line.startsWith('METHOD USED')) itemNo = '3.2';
                            else if (line.startsWith('CLEANING WATER TO')) itemNo = '3.3';
                            else if (line.includes('BALLAST QUANTITY')) itemNo = '4.2';
                            else if (line.includes('THROUGH 15 PPM EQUIPMENT')) itemNo = '9.1';
                            else if (line.includes('RECEPTION')) itemNo = '9.2';
                            else if (line.includes('mÂ³') || line.includes('MÂ³')) itemNo = '10';
                            break;
                        }

                        // Always show SIGNED on its own line
                        if (line.startsWith('SIGNED:')) itemNo = '';
                      }

                      return (
                        <tr key={`${entry.id}-${idx}`}>
                          <td>{showDate ? formattedDate : ''}</td>
                          <td>{showCode ? entry.code : ''}</td>
                          <td>{itemNo}</td>
                          <td style={{ whiteSpace: 'pre-line' }}>{line}</td>
                          {/* No Actions column for this view */}
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

export default AllEntriesView;
