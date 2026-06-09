// src/components/CrewDashboard.jsx
import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { buildItemRows, groupEntriesByLogicalORBEntry, toRecordJSON } from "../../utils/orb/orbUtils";
import "../../styles/orb/CrewDashboard.css";
import "../../styles/orb/orb-theme.css";
import { Panel, Button, Card, Stack } from "../../components/orb/OrbUI";
import ORBHeader from "../../components/orb/AppHeader";
import ORBFooter from "../../components/orb/AppFooter";
import AppFooter from "../../components/orb/AppFooter";
import AppHeader from "../../components/orb/AppHeader";
import { WithPermission } from '../../utils/orb/permissionUtils'; // Import WithPermission
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { useAuth } from '../../hooks/auth/useAuth';

export default function CrewDashboard({ isChiefMode = false, onSubmit }) {
  const [codes, setCodes] = useState([]);

  const [formData, setFormData] = useState({
    code: "", details: {
      fuel_quantity: "",
      fuel_type: "",
      fuel_tanks: [],
      fuel_sulfur: "",
      fuel_quantities: [],
      fuel_current_contents: [],

      // Lubricating Oil
      lube_quantity: "",
      lube_type: "",
      lube_tanks: [],
      lube_quantities: [],
      lube_current_contents: [],

      // Bunkering
      place_of_bunkering: "",
      start_time: "",
      end_time: ""
    }
  });
  const [availableTanks, setAvailableTanks] = useState([]);
  const [currentVessel, setCurrentVessel] = useState(null);
  const [entries, setEntries] = useState([]);
  const [sludgeSummary, setSludgeSummary] = useState([]);
  const [showSludgeSummary, setShowSludgeSummary] = useState(false);
  const [lastApprovedEntries, setLastApprovedEntries] = useState([]);
  const [lastRejectedEntries, setLastRejectedEntries] = useState([]);
  const [lastDeletedEntries, setLastDeletedEntries] = useState([]);
  const [hasNewApproved, setHasNewApproved] = useState(false);
  const [hasNewRejected, setHasNewRejected] = useState(false);
  const [hasNewDeleted, setHasNewDeleted] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();
  const [errors, setErrors] = useState({});
  const [pendingFEntry, setPendingFEntry] = useState(null);
  const [editingEntryId, setEditingEntryId] = useState(null);

  const {user} = useAuth();       
  const vesselId = user?.vessel_id;

  const officer = user ? `${user.username} (${user.rank})` : "Unknown User";
  const [bunkeringType, setBunkeringType] = useState('');
  const [rawEntries, setRawEntries] = useState([]);





  // Format date to DD-MMM-YYYY : HH:MM HRS
  const formatToDisplay = (isoString) => {
    if (!isoString) return '';
    const d = new Date(isoString);
    const day = String(d.getDate()).padStart(2, '0');
    const month = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'][d.getMonth()];
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${day}-${month}-${year} : ${hours}:${minutes} HRS`;
  };

  // For input: format to YYYY-MM-DDTHH:mm (local, not UTC)
  const formatToDateTimeLocal = (date) => {
    const d = new Date(date);
    d.setSeconds(0, 0);

    // Shift to Local TimeZone
    const offset = d.getTimezoneOffset();
    const local = new Date(d.getTime() - offset * 60000);

    return local.toISOString().slice(0, 16); // "YYYY-MM-DDTHH:mm"
  };

  // Get yesterday at 00:00
  const yesterdayDate = () => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    d.setHours(0, 0, 0, 0);
    return d;
  };

  //  function for date formatting but not in use just defined for FallBack
  const formatDate = (isoDate) => {
    if (!isoDate) return '';
    const d = new Date(isoDate);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
      .toUpperCase()
      .replace(/ /g, '-');
  };

  //this function is defined to recognize the special place in ocean like red sae, dead sea or any other restricted area where discharge is not allowed
  // Recognizes special sea areas where discharge is not allowed
  const getSpecialAreaFromPosition = (pos) => {
    if (!pos) return null;

    const { latitude: lat, longitude: lon } = pos;

    // Mediterranean Sea
    if (lat >= 30 && lat <= 46 && lon >= -7 && lon <= 37) {
      return "Mediterranean Sea";
    }

    // Red Sea
    if (lat >= 12 && lat <= 28 && lon >= 32 && lon <= 44) {
      return "Red Sea";
    }

    // Baltic Sea
    if (lat >= 54 && lat <= 66 && lon >= 10 && lon <= 31) {
      return "Baltic Sea";
    }

    // Black Sea
    if (lat >= 41 && lat <= 47 && lon >= 27 && lon <= 42) {
      return "Black Sea";
    }

    // Dead Sea (highly restricted)
    if (lat >= 31 && lat <= 32 && lon >= 35 && lon <= 36) {
      return "Dead Sea";
    }

    // Antarctic Area (IMO: south of 60Â°S)
    if (lat <= -60) {
      return "Antarctic Area";
    }

    return null;
  };


  //just another funtion to refresh entries for fallback
  const checkForNewEntries = () => {
    // Compare current entries with last known entries
    // This is a simple approach; might want to use a more robust method like comparing IDs or timestamps
    const hasNewApproved = lastApprovedEntries.length > 0 && entries.some(entry => entry.status === 'Approved' && !lastApprovedEntries.some(lastEntry => lastEntry.id === entry.id));
    const hasNewRejected = lastRejectedEntries.length > 0 && entries.some(entry => entry.status === 'Rejected' && !lastRejectedEntries.some(lastEntry => lastEntry.id === entry.id));
    const hasNewDeleted = lastDeletedEntries.length > 0 && entries.some(entry => entry.is_deleted && !lastDeletedEntries.some(lastEntry => lastEntry.id === entry.id));

    setHasNewApproved(hasNewApproved);
    setHasNewRejected(hasNewRejected);
    setHasNewDeleted(hasNewDeleted);
  };

  // this function Initialize currentVessel from sessionStorage
  useEffect(() => {
    if (vesselId) {
      setCurrentVessel(vesselId); // This just stores the string from sessionStorage
      console.log("Loaded vesselId:", vesselId);
    }
  }, [vesselId]);

  // this function Fetch operations
  useEffect(() => {
    if (!vesselId) return;

    fetch(`http://localhost:8000/api/orb/api/operations/?vessel_id=${vesselId}&is_deleted=false&status=Pending`)
      .then((r) => r.json())
      .then((data) => {
        const ops = Array.isArray(data) ? data : data.results || [];
        console.log("Raw entries from API:", ops);

        const grouped = groupEntriesByLogicalORBEntry(ops);
        setEntries(grouped);

        //     // âœ… Only process if ops is valid
        // if (Array.isArray(ops)) {
        //   const summary = calculateSludgeSummary(ops);
        //   setSludgeSummary(summary);
        //   console.log("SLUDGE SUMMARY", summary)
        // }

      })
      .catch((err) => {
        console.error("Failed to load drafts:", err);
      });
  }, [vesselId]);




  // this function fetches all the codes from A to I with thier IDs and descriptions
useEffect(() => {
  async function fetchCodes() {
    try {
      const res = await fetch("http://localhost:8000/api/orb/api/codes/");
      console.log("Fetch response in codes:", res);
      const data = await res.json();

      console.log("Fetched ORB codes:", data);

      // data itself is the array
      if (Array.isArray(data)) {
        setCodes(data);
      } else {
        setCodes([]);
      }
    } catch (err) {
      console.error("Failed to fetch ORB codes", err);
      setCodes([]);
    }
  }

  fetchCodes();
}, []);


  useEffect(() => {
    console.log("Codes state updated:", codes);
  }, [codes]);


  // Fetch available tanks dynamically
  useEffect(() => {
    if (!currentVessel || !formData.code) {
      console.log("Skipping fetch â€” missing vessel_id or code", currentVessel, formData.code);
      return;
    }

    const vesselParam =
      typeof currentVessel === "string" ? currentVessel : currentVessel.id;

    fetch(
      `http://localhost:8000/api/orb/api/tanks-for-orb/?vessel_id=${vesselParam}&orb_code=${formData.code}`
    )
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched tanks response:", data);
        setAvailableTanks(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error("Error fetching tanks:", err);
        setAvailableTanks([]);
      });
  }, [currentVessel, formData.code]);




  // Main handler for simple fields
  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      details: { ...prev.details, [field]: value }
    }));

    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };


  //  Reset bunkeringType when code changes
  useEffect(() => {
    if (formData.code !== 'H') {
      setBunkeringType('');
    }
  }, [formData.code]);

  // For sludge tank fields (C11.1, C11.2, C11.3)
  const handleTankChange = (index, field, value) => {
    const updatedTanks = [...(formData.details.tanks || [])];
    updatedTanks[index] = { ...updatedTanks[index], [field]: value };
    handleChange('tanks', updatedTanks);
  };

  // Add a new sludge tank row
  const addTank = () => {
    handleChange('tanks', [...(formData.details.tanks || []), {}]);
  };

  // Remove a sludge tank row
  const removeTank = (index) => {
    const updatedTanks = formData.details.tanks.filter((_, i) => i !== index);
    handleChange('tanks', updatedTanks);
  };



  const refreshEntries = async () => {
    
    if (!vesselId) return;

    try {
      // Fetch Pending entries (existing logic)
      const res = await fetch(`http://localhost:8000/api/orb/api/operations/?vessel_id=${vesselId}&is_deleted=false&status=Pending`);
      if (!res.ok) {
        console.error("Failed to load entries:", await res.text());
        return;
      }
      const data = await res.json();
      const ops = Array.isArray(data) ? data : data.results || [];
      const grouped = groupEntriesByLogicalORBEntry(ops);
      setEntries(grouped);

      // Fetch Approved entries
      const approvedRes = await fetch(`http://localhost:8000/api/orb/api/operations/?vessel_id=${vesselId}&is_deleted=false&status=Approved`);
      const approvedData = await approvedRes.json();
      const approvedOps = Array.isArray(approvedData) ? approvedData : approvedData.results || [];
      setLastApprovedEntries(approvedOps); // Store for comparison

      // Fetch Rejected entries
      const rejectedRes = await fetch(`http://localhost:8000/api/orb/api/operations/?vessel_id=${vesselId}&is_deleted=false&status=Rejected`);
      const rejectedData = await rejectedRes.json();
      const rejectedOps = Array.isArray(rejectedData) ? rejectedData : rejectedData.results || [];
      setLastRejectedEntries(rejectedOps); // Store for comparison

      // Fetch Deleted entries
      const deletedRes = await fetch(`http://localhost:8000/api/orb/api/operations/?vessel_id=${vesselId}&is_deleted=true`);
      const deletedData = await deletedRes.json();
      const deletedOps = Array.isArray(deletedData) ? deletedData : deletedData.results || [];
      setLastDeletedEntries(deletedOps); // Store for comparison

    } catch (err) {
      console.error('Failed to refresh entries:', err);
    }
  };





  useEffect(() => {
    refreshEntries();
    // Check for new entries after refreshing
    checkForNewEntries();
  }, [vesselId]);



  const calculateSludgeSummary = (entries) => {
    const summary = {};

    console.log("Processing entries for sludge summary:", entries); // âœ… Debug

    const codeCEntries = entries.filter(e => {
      if (e.code !== 'C') return false;
      if (e.is_deleted) return false;
      if (!e.details) {
        console.log("Entry missing details:", e);
        return false;
      }
      return true;
    });

    console.log("Filtered Code C entries:", codeCEntries); // âœ… Check if any match

    for (const entry of codeCEntries) {
      const { details } = entry;

      // âœ… Safely check operation_mode
      if (!details.operation_mode) continue;

      // Weekly Update â†’ Set current retained level
      if (details.operation_mode === 'weekly' && details.sludge_tank_id && details.sludge_before != null) {
        const tank = details.sludge_tank_id.trim();
        if (!tank) continue;

        if (!summary[tank]) {
          summary[tank] = {
            current: 0,
            capacity: parseFloat(details.sludge_tank_capacity) || 0
          };
        }

        const retained = parseFloat(details.sludge_before);
        if (!isNaN(retained)) {
          summary[tank].current = retained; // âœ… Override with latest weekly value
        }

        if (details.sludge_tank_capacity) {
          const capacity = parseFloat(details.sludge_tank_capacity);
          if (!isNaN(capacity)) {
            summary[tank].capacity = capacity;
          }
        }

        console.log(`[Weekly] Updated ${tank}: ${retained} mÂ³`);
      }

      // Manual Collection â†’ Add to source tank
      if (details.operation_mode === 'manual' && details.collection_source && details.manual_collection_m3) {
        const tank = details.collection_source.trim();
        if (!tank) continue;

        if (!summary[tank]) summary[tank] = { current: 0, capacity: 0 };

        const collected = parseFloat(details.manual_collection_m3);
        if (!isNaN(collected) && collected > 0) {
          summary[tank].current += collected;
          console.log(`[Manual] Added ${collected} mÂ³ to ${tank}`);
        }
      }

      // Disposal Methods â†’ Subtract from source
      if (['reception', 'transfer', 'incineration'].includes(details.disposal_method)) {
        let sourceTank = '';
        let qty = 0;

        if (details.disposal_method === 'reception') {
          sourceTank = details.source_tank?.trim();
          qty = parseFloat(details.quantity_m3);
        } else if (details.disposal_method === 'transfer') {
          sourceTank = details.transferred_from_tank_ids?.trim();
          qty = parseFloat(details.disposal_quantity_m3);
        } else if (details.disposal_method === 'incineration') {
          sourceTank = details.source_tank?.trim();
          qty = parseFloat(details.quantity_m3);
        }

        if (sourceTank && !isNaN(qty) && qty > 0) {
          if (!summary[sourceTank]) summary[sourceTank] = { current: 0, capacity: 0 };
          summary[sourceTank].current = Math.max(0, summary[sourceTank].current - qty);
          console.log(`[Disposal] Removed ${qty} mÂ³ from ${sourceTank}`);
        }
      }
    }

    const result = Object.entries(summary).map(([tank, data]) => ({
      tank,
      current: parseFloat(data.current.toFixed(2)),
      capacity: parseFloat(data.capacity.toFixed(2)),
      percent: data.capacity > 0 ? ((data.current / data.capacity) * 100).toFixed(1) : 0
    }));

    console.log("Final Sludge Summary:", result); // âœ… Final output
    return result;
  };


  const validateCodeA = (details, availableTanks) => {
    //   . 1. Operation Type
    if (!details.operation_type) {
      return "Please select Cleaning, Ballasting, or Both.";
    }

    //   . 2. Cleaning Section
    if (details.operation_type === "cleaning" || details.operation_type === "both") {
      if (!details.cleaned_since_last) {
        return "Please specify if tank was cleaned since last oil.";
      }

      if (details.cleaned_since_last === "no" && !details.previous_oil) {
        return "Please enter the type of previous oil.";
      }

      //  Cleaning Start/End Position Validation
      const startFields = [
        "cleaning_start_lat_deg",
        "cleaning_start_lat_min",
        "cleaning_start_lat_dir",
        "cleaning_start_lon_deg",
        "cleaning_start_lon_min",
        "cleaning_start_lon_dir",
      ];
      const endFields = [
        "cleaning_end_lat_deg",
        "cleaning_end_lat_min",
        "cleaning_end_lat_dir",
        "cleaning_end_lon_deg",
        "cleaning_end_lon_min",
        "cleaning_end_lon_dir",
      ];

      if (startFields.some(f => !details[f] && details[f] !== 0)) {
        return "Please enter complete Cleaning Start Position (Lat & Long).";
      }
      if (endFields.some(f => !details[f] && details[f] !== 0)) {
        return "Please enter complete Cleaning End Position (Lat & Long).";
      }




      if (details.cleaning_start && details.cleaning_end) {
        const start = new Date(details.cleaning_start);
        const end = new Date(details.cleaning_end);
        if (start >= end) {
          return "End time must be after start time.";
        }
      }

      if (!details.cleaning_method) {
        return "Please select a cleaning method (Rinsing, Steaming, Chemical).";
      }

      if (details.cleaning_method === "chemical") {
        if (!details.chemical_name) {
          return "Please specify the chemical name (e.g., TANK CLEANER X100).";
        }
        if (!details.chemicals_used || details.chemicals_used <= 0) {
          return "Chemical quantity must be greater than 0.";
        }
      }
    }

    //   . 3. Ballasting Section
    if (details.operation_type === "ballasting" || details.operation_type === "both") {
      if (!details.ballast_start) {
        return "Please enter ballast start time.";
      }

      if (!details.tank_identity) {
        return "Please select a tank from the list.";
      }

      if (!details.ballast_end) {
        return "Please enter ballast end time.";
      }

      // Ballast Start/End Position Validation
      const ballastStartFields = [
        "ballast_start_lat_deg",
        "ballast_start_lat_min",
        "ballast_start_lat_dir",
        "ballast_start_lon_deg",
        "ballast_start_lon_min",
        "ballast_start_lon_dir",
      ];
      const ballastEndFields = [
        "ballast_end_lat_deg",
        "ballast_end_lat_min",
        "ballast_end_lat_dir",
        "ballast_end_lon_deg",
        "ballast_end_lon_min",
        "ballast_end_lon_dir",
      ];

      if (ballastStartFields.some(f => !details[f] && details[f] !== 0)) {
        return "Please enter complete Ballast Start Position (Lat & Long).";
      }
      if (ballastEndFields.some(f => !details[f] && details[f] !== 0)) {
        return "Please enter complete Ballast End Position (Lat & Long).";
      }


      if (details.ballast_start && details.ballast_end) {
        const start = new Date(details.ballast_start);
        const end = new Date(details.ballast_end);
        if (start >= end) {
          return "Ballast end time must be after start time.";
        }
      }

      if (!details.ballast_qty || details.ballast_qty <= 0) {
        return "Ballast quantity must be greater than 0.";
      }

      const tank = availableTanks?.find(t => t.tank_name === details.tank_identity);
      if (tank && details.ballast_qty > tank.capacity) {
        return `Ballast quantity (${details.ballast_qty} mÂ³) exceeds tank capacity (${tank.capacity} mÂ³). Please check tank limits.`;
      }
    }

    //   . 3.3 Transfer to Slop Tank
    if (details.operation_type === "cleaning" || details.operation_type === "both") {
      if (!details.transfer_tank) {
        return "Slop tank is required.";
      }
      if (!details.transfer_qty || details.transfer_qty <= 0) {
        return "Transfer quantity must be greater than 0.";
      }

      const selectedTank = availableTanks?.find(t => t.tank_name === details.transfer_tank);
      if (selectedTank) {
        const capacity = parseFloat(selectedTank.capacity) || 0;
        const currentContent = parseFloat(selectedTank.current_content) || 0;
        const availableCapacity = capacity - currentContent;

        if (details.transfer_qty > availableCapacity) {
          return `Quantity exceeds available capacity (${availableCapacity.toFixed(2)} mÂ³) of ${details.transfer_tank}.`;
        }
      }

      //   . Tank chosen at 1 and 3.3 must be same
      if ((details.operation_type === "ballasting" || details.operation_type === "both")
        && details.tank_identity && details.transfer_tank) {
        const ballastTank = availableTanks.find(t => t.tank_name === details.tank_identity);
        const transferTank = availableTanks.find(t => t.tank_name === details.transfer_tank);

        // if (ballastTank && transferTank && ballastTank.id !== transferTank.id) {
        //   return `Selected transfer tank (${transferTank.tank_name}) must be the same as ballasting tank (${ballastTank.tank_name}).`;
        // }
      }
    }

    //  All valid
    return null;
  };


  const buildPosition = (latDeg, latMin, latDir, lonDeg, lonMin, lonDir) => {
    if (
      latDeg === "" || latMin === "" || !latDir ||
      lonDeg === "" || lonMin === "" || !lonDir
    ) return null;

    const latitude = (parseInt(latDeg) + parseInt(latMin) / 60) * (latDir === "S" ? -1 : 1);
    const longitude = (parseInt(lonDeg) + parseInt(lonMin) / 60) * (lonDir === "W" ? -1 : 1);

    return { latitude, longitude };
  };


  const validateCodeB = (details, allRawEntries, availableTanks) => {
    //   . Find most recent Code A entry with item_no = "1"
    const lastCodeAEntry = [...allRawEntries]
      .reverse()
      .find(entry => entry.code === "A" && entry.item_no === "1");

    if (!lastCodeAEntry) {
      return "No previous entry for Code A .";
    }

    const recordText = lastCodeAEntry.record_of_operation || "";

    //   . Extract tank identity from Code A
    const tankMatch = recordText.match(/TANK\(S\) BALLASTED:\s*([^\n]+)/i);
    if (!tankMatch) {
      return "Could not find tank identity in previous Code A entry.";
    }

    const extractedTank = tankMatch[1].trim();
    // 5. Tank ID(s)
    if (!details.tank_ids) {
      return "Tank ID(s) is required.";
    }

    const normalizedExtracted = (extractedTank || "")
      .replace(/\(FR:\d+-\d+\)/i, "")
      .trim()
      .toUpperCase();

    const normalizedInput = (details.tank_ids || "")
      .replace(/\(FR:\d+-\d+\)/i, "")
      .trim()
      .toUpperCase();

    if (normalizedExtracted !== normalizedInput) {
      return `Tank "${details.tank_ids}" must match the BALLASTED tank. Do you mean ${extractedTank} Tank`;
    }


    //   . 6. Position at Start (Lat/Lon)
    if (
      !details.pos_start_lat_deg ||
      !details.pos_start_lat_min ||
      !details.pos_start_lat_dir ||
      !details.pos_start_lon_deg ||
      !details.pos_start_lon_min ||
      !details.pos_start_lon_dir
    ) {
      return "Position at Start  is required: all latitude and longitude fields must be filled.";
    }

    //   . 7. Position at End (Lat/Lon)
    if (
      !details.pos_end_lat_deg ||
      !details.pos_end_lat_min ||
      !details.pos_end_lat_dir ||
      !details.pos_end_lon_deg ||
      !details.pos_end_lon_min ||
      !details.pos_end_lon_dir
    ) {
      return "Position at End  is required: all latitude and longitude fields must be filled.";
    }

    //   . 8. Ship's Speed
    // if (!details.ship_speeds) {
    //   return "Speed in Knots is required.";
    // }
    // const speed = parseFloat(details.ship_speeds);
    // if (isNaN(speed)) {
    //   return "Speed in Knots must be a valid number.";
    // }
    // if (details.method === '15ppm') {
    //   if (speed <= 0) {
    //     return "Speed in Knots must be > 0.";
    //   }
    // }
    // if (details.method === '15ppm') {
    //   if (speed >= 24) {
    //     return "Speed cannot be greater than 24 .";
    //   }
    // }

    // if (details.method === '15ppm' && !Number.isInteger(speed)) {
    //   return "For 15 ppm discharge, speed must be a whole number (no decimals).";
    // }

    //   . 10. Quantity Discharged
    if (!details.quantity_discharged_m3 || details.quantity_discharged_m3 <= 0) {
      return "Quantity Discharged (Item 10) must be > 0 MÂ³.";
    }

    //   . Extract ballast quantity from Code A
    const qtyMatch = recordText.match(/BALLAST QUANTITY:\s*([\d.]+)/i);
    const ballastedQty = qtyMatch ? parseFloat(qtyMatch[1]) : 0;

    // if (details.quantity_discharged_m3 > ballastedQty) {
    //   return `Discharge quantity (${details.quantity_discharged_m3} MÂ³) cannot exceed ballasted quantity (${ballastedQty} MÂ³).`;
    // }

    //   . Get tank capacity
    const tankCapacity = availableTanks?.find(t =>
      t.tank_name.toUpperCase() === details.tank_ids.toUpperCase()
    )?.capacity || 0;

    if (details.quantity_discharged_m3 > tankCapacity) {
      return `Discharge quantity (${details.quantity_discharged_m3} MÂ³) exceeds tank capacity (${tankCapacity} MÂ³).`;
    }


    if (details.method === "reception" && (!details.reception_port || !details.reception_port.trim())) {
      return "Port name is required for reception facility (Item 9.2).";
    }

    const posStart = buildPosition(
      details.pos_start_lat_deg,
      details.pos_start_lat_min,
      details.pos_start_lat_dir,
      details.pos_start_lon_deg,
      details.pos_start_lon_min,
      details.pos_start_lon_dir
    );

    const posEnd = buildPosition(
      details.pos_end_lat_deg,
      details.pos_end_lat_min,
      details.pos_end_lat_dir,
      details.pos_end_lon_deg,
      details.pos_end_lon_min,
      details.pos_end_lon_dir
    );

    if (!posStart) {
      errors.pos_start = "Position at Start is required";
    }
    if (!posEnd) {
      errors.pos_end = "Position at End is required";
    }

    // Special Area checks
    if (posStart) {
      const specialAreaStart = getSpecialAreaFromPosition(posStart);
      if (specialAreaStart) {
        errors.pos_start = `Discharge not allowed in Special Area: ${specialAreaStart}`;
      }
    }
    if (posEnd) {
      const specialAreaEnd = getSpecialAreaFromPosition(posEnd);
      if (specialAreaEnd) {
        errors.pos_end = `Discharge not allowed in Special Area: ${specialAreaEnd}`;
      }
    }


    //  All valid
    return null;
  };

  const validateCodeC = (details = {}, availableTanks = [], allRawEntries = []) => {
    // --- Helpers ---
    const norm = (s) => (s || "").toString().trim().toUpperCase();
    const toNumber = (v) => {
      if (v === null || v === undefined || v === "") return NaN;
      if (typeof v === "number") return v;
      return parseFloat(String(v).replace(",", "."));
    };

    const findTankByIdentifier = (identifier) => {
      if (!identifier) return null;
      const idNorm = norm(identifier);
      return (availableTanks || []).find((t) => {
        if (!t) return false;
        // match GUID/id exact
        if (t.id && norm(t.id) === idNorm) return true;
        // match tank_name exact
        if (t.tank_name && norm(t.tank_name) === idNorm) return true;
        // partial name matches (fallback)
        if (t.tank_name && norm(t.tank_name).includes(idNorm)) return true;
        if (idNorm.includes(norm(t.tank_name || ""))) return true;
        return false;
      }) || null;
    };

    // Improved retained quantity parser:
    // 1) look for numbers that are labeled with "RETAIN" or "RETAINED"
    // 2) then look for "X M3 RETAINED" patterns
    // 3) fallback to first M3 number or first number in text
    const parseRetainedFromRecord = (recordText) => {
      if (!recordText || typeof recordText !== "string") return NaN;
      const text = recordText.toUpperCase();

      // 1) Look for "RETAIN" keyword followed/following by a number
      // patterns like: "RETAINED 3.5 M3" OR "3.5 M3 RETAINED" OR "RETAIN: 3.5"
      const retainPatterns = [
        /RETAIN(?:ED|ING)?\s*[:]?\s*([0-9]+(?:[.,][0-9]+)?)/i,
        /([0-9]+(?:[.,][0-9]+)?)\s*(?:M(?:\u00B3|3))\s*(?:RETAIN(?:ED)?)/i,
        /([0-9]+(?:[.,][0-9]+)?)\s*(?:M(?:\u00B3|3))\s*RETAIN/i,
        /RETAIN(?:ED|ING)?\s*[:]?\s*([0-9]+(?:[.,][0-9]+)?)\s*(?:M(?:\u00B3|3))?/i
      ];
      for (const rx of retainPatterns) {
        const m = text.match(rx);
        if (m && m[1]) return toNumber(m[1]);
      }

      // 2) Look for first "X M3" occurrence (but try to avoid matching capacity lines if labeled 'CAPACITY')
      // we'll prefer M3 that are not immediately followed/preceded by the word CAPACITY
      const m3Regex = /([0-9]+(?:[.,][0-9]+)?)\s*(?:M(?:\u00B3|3))/gi;
      let m;
      while ((m = m3Regex.exec(text)) !== null) {
        const matchIndex = m.index;
        const surrounding = text.slice(Math.max(0, matchIndex - 20), matchIndex + m[0].length + 20);
        // If the surrounding text contains "CAPACITY" skip (likely tank design capacity)
        if (/CAPACITY/.test(surrounding)) continue;
        // Otherwise accept this M3 as probable retained value
        return toNumber(m[1]);
      }

      // 3) Fallback: first plain number (but avoid numbers next to "CAPACITY")
      const numRegex = /([0-9]+(?:[.,][0-9]+)?)/g;
      while ((m = numRegex.exec(text)) !== null) {
        const matchIndex = m.index;
        const surrounding = text.slice(Math.max(0, matchIndex - 20), matchIndex + m[0].length + 20);
        if (/CAPACITY/.test(surrounding)) continue; // skip capacity numbers
        return toNumber(m[1]);
      }

      return NaN;
    };

    // --- Basic checks ---
    if (!details || typeof details !== "object") return "Missing operation details.";
    if (!details.operation_mode) return "Please select an operation type (Weekly Update, Manual Operation, or Transfer/Disposal)";

    // --- Weekly & Manual (11.x) ---
    if (["weekly", "manual"].includes(details.operation_mode)) {
      const tankCapacity = toNumber(details.sludge_tank_capacity);
      if (!Number.isFinite(tankCapacity) || tankCapacity <= 0) {
        return "Total capacity must be > 0";
      }

      const tankObj = findTankByIdentifier(details.sludge_tank_id);
      // if (tankObj && Number.isFinite(toNumber(tankObj.capacity)) && tankCapacity > toNumber(tankObj.capacity)) {
      //   return `Capacity (${tankCapacity} mÂ³) cannot exceed tank's design capacity (${tankObj.capacity} mÂ³)`;
      // }

      const sludgeBefore = toNumber(details.sludge_before);
      if (Number.isFinite(sludgeBefore)) {
        if (sludgeBefore < 0) return "Retained quantity cannot be negative";
        if (sludgeBefore > tankCapacity) return `Retained quantity cannot exceed tank capacity (${tankCapacity} MÂ³)`;
      }
    }

    // --- Manual specific (11.4) ---
    if (details.operation_mode === "manual") {
      const manualCollection = toNumber(details.manual_collection_m3);
      if (!Number.isFinite(manualCollection) || manualCollection < 0) {
        return "Manual collection must be >= 0";
      }
      if (manualCollection > 0 && !details.collection_source) {
        return "Source tank is required when manual collection > 0";
      }
      //  Check: manual collection cannot exceed retained qty entered for that tank
      if (details.manual_collection_m3 > details.retained_quantity) {
        return `Manual Collection (${details.manual_collection_m3} MÂ³) cannot exceed Retained Quantity (${details.retained_quantity} MÂ³) for the selected tank.`;
      }

      // // Source and collection tanks must NOT be the same
      if (details.source_tank && details.transferred_to_Tank_ids) {
        if (details.source_tank === details.transferred_to_Tank_ids) {
          return "For Manual Collection, the Source Tank (11.1) and Collection Tank (11.4) cannot be the same.";
        }
      }


      // Get selected source tank details
      const sourceTank = availableTanks.find(
        (tank) => tank.tank_name === details.collection_source
      );

      if (sourceTank) {
        const manualQty = parseFloat(details.manual_collection_m3) || 0;
        const tankCapacity = parseFloat(sourceTank.capacity) || 0;

        //  Check: manual collection cannot exceed tank capacity
        if (manualQty > tankCapacity) {
          return `Manual Collection (${manualQty} mÂ³) cannot exceed Source Tank capacity (${tankCapacity} mÂ³).`;
        }

        //  Check: manual collection cannot be negative
        if (manualQty < 0) {
          return "Manual Collection quantity cannot be negative.";
        }


      }

    }

    // --- Transfer / Disposal (12.x) ---
    if (details.operation_mode === "transfer") {
      if (!details.disposal_method) return "Please select a disposal method (12.1, 12.2, 12.3, or 12.4)";
      const method = details.disposal_method;

      // Determine disposal quantity & source tank identifier for weekly-check
      let disposalQuantity = NaN;
      let sourceTankIdentifier = "";
      if (method === "reception") {
        disposalQuantity = toNumber(details.quantity_m3);
        sourceTankIdentifier = details.source_tank;
      } else if (method === "transfer") {
        disposalQuantity = toNumber(details.disposal_quantity_m3);
        sourceTankIdentifier = details.transferred_from_tank_ids;
      } else if (method === "incineration") {
        disposalQuantity = toNumber(details.quantity_m3);
        sourceTankIdentifier = details.source_tank;
      }

      // --- WEEKLY retained check (rigorous matching) ---
      if (Number.isFinite(disposalQuantity)) {
        if (!sourceTankIdentifier) return "Source tank is required for disposal.";

        // canonical source tank object (if available)
        const sourceTankObj = findTankByIdentifier(sourceTankIdentifier);
        const sourceNorm = norm(sourceTankIdentifier);

        const weeklyEntriesForTank = (allRawEntries || [])
          .filter((entry) => {
            if (!entry || entry.is_deleted) return false;
            // accept Approved or Pending weekly entries
            const statusOk = !entry.status || ["Approved", "Pending"].includes(entry.status);
            if (!statusOk) return false;
            if (entry.code !== "C") return false;

            // If entry has structured details
            if (entry.details && entry.details.operation_mode === "weekly" && entry.details.sludge_tank_id) {
              const entryTankObj = findTankByIdentifier(entry.details.sludge_tank_id);

              // 1. Exact ID match
              if (sourceTankObj && entryTankObj && sourceTankObj.id && entryTankObj.id) {
                if (norm(sourceTankObj.id) === norm(entryTankObj.id)) return true;
              }

              // 2. Exact tank_name match
              if (sourceTankObj && entryTankObj && sourceTankObj.tank_name && entryTankObj.tank_name) {
                if (norm(sourceTankObj.tank_name) === norm(entryTankObj.tank_name)) return true;
              }

              // 3. If only one is resolved, compare identifiers directly
              if (norm(entry.details.sludge_tank_id) === sourceNorm) return true;

              // 4. Last resort: partial match
              if (norm(entry.details.sludge_tank_id).includes(sourceNorm) || sourceNorm.includes(norm(entry.details.sludge_tank_id))) return true;
            }

            // Fallback: check item_no in 11.x and record_of_operation text for tank name
            const itemNo = (entry.item_no || "").toString().trim();
            if (itemNo.startsWith("11")) {
              if (entry.record_of_operation && norm(entry.record_of_operation).includes(sourceNorm)) return true;
              if (itemNo.startsWith("11.1")) return true;
            }

            // Last fallback: search the free-text record for tank name
            if (entry.record_of_operation && norm(entry.record_of_operation).includes(sourceNorm)) return true;

            return false;
          })
          // newest first
          .sort((a, b) => new Date(b.date || b.created_at || b.updated_at || 0) - new Date(a.date || a.created_at || a.updated_at || 0));

        if (!weeklyEntriesForTank.length) {
          return `No previous Weekly Update found for ${sourceTankIdentifier}. Please record one before disposal.`;
        }

        // latest weekly entry found -> extract retained (11.3)
        const latestWeekly = weeklyEntriesForTank[0];
        let retainedInLatestWeekly = NaN;

        // Prefer structured number in details.sludge_before
        if (latestWeekly.details && latestWeekly.details.sludge_before !== undefined && latestWeekly.details.sludge_before !== null) {
          retainedInLatestWeekly = toNumber(latestWeekly.details.sludge_before);
        } else if (latestWeekly.record_of_operation) {
          // parse retained quantity from free-text (prefer labeled retained)
          retainedInLatestWeekly = parseRetainedFromRecord(latestWeekly.record_of_operation);
        }

        if (!Number.isFinite(retainedInLatestWeekly)) {
          const dateInfo = latestWeekly.date ? ` on ${new Date(latestWeekly.date).toLocaleString()}` : "";
          return `Could not determine retained quantity from last weekly update for ${sourceTankIdentifier}${dateInfo}. Please ensure 11.3 is recorded.`;
        }



        if (disposalQuantity > retainedInLatestWeekly) {
          return `Disposal quantity  exceeds available sludge (${retainedInLatestWeekly} mÂ³) in ${sourceTankIdentifier} as per last weekly update.`;
        }
      }

      // --- method-specific checks (unchanged logic area) ---
      if (method === "reception") {
        const q = toNumber(details.quantity_m3);
        if (!Number.isFinite(q) || q <= 0) return "Disposal quantity (12.1) must be greater than 0.";
        if (!details.source_tank) return "Source tank is required for disposal method 12.1.";
        if (!Number.isFinite(toNumber(details.retained_quantity))) return "Retained quantity is required.";
        const tank = findTankByIdentifier(details.source_tank);
        if (tank && toNumber(details.retained_quantity) > toNumber(tank.capacity)) {
          return `Retained quantity (${details.retained_quantity} mÂ³) cannot exceed the capacity of ${tank.tank_name} (${tank.capacity} mÂ³).`;
        }
        if (!details.reception_vessel?.trim()) return "Reception vessel name is required.";
        if (!details.reception_port?.trim()) return "Reception port name is required.";
      }

      if (method === "transfer") {
        const q = toNumber(details.disposal_quantity_m3);
        if (!Number.isFinite(q) || q <= 0) return "Quantity Transferred (12.2) must be greater than 0.";
        if (!details.transferred_from_tank_ids) return "Source tank (12.2) is required.";
        if (!details.transferred_to_Tank_ids) return "Destination tank (12.2) is required.";
        if (norm(details.transferred_from_tank_ids) === norm(details.transferred_to_Tank_ids)) {
          return "Source and Destination tanks (12.2) cannot be the same.";
        }
        const sourceTank = findTankByIdentifier(details.transferred_from_tank_ids);
        const destTank = findTankByIdentifier(details.transferred_to_Tank_ids);
        if (details.retained_quantity !== undefined && details.retained_quantity !== null && details.retained_quantity !== "") {
          if (!Number.isFinite(toNumber(details.retained_quantity)) || toNumber(details.retained_quantity) < 0) {
            return "Retained Quantity (12.2) must be >= 0 if provided.";
          }
          if (sourceTank && toNumber(details.retained_quantity) > toNumber(sourceTank.capacity)) {
            return `Retained Quantity cannot exceed source tank capacity (${sourceTank.capacity} mÂ³).`;
          }
        }
        if (destTank && Number.isFinite(toNumber(destTank.capacity)) && q > toNumber(destTank.capacity)) {
          return `Transferred quantity (${q} mÂ³) cannot exceed destination tank capacity (${destTank.capacity} mÂ³).`;
        }
      }

      if (method === "incineration") {
        const q = toNumber(details.quantity_m3);
        if (!Number.isFinite(q) || q <= 0) return "Incinerated quantity (12.3) must be greater than 0.";
        if (!details.source_tank) return "Source tank (12.3) is required.";
        if (!Number.isFinite(toNumber(details.incineration_duration_hours)) || toNumber(details.incineration_duration_hours) <= 0) {
          return "Incineration duration must be greater than zero";
        }
        const sourceTank = findTankByIdentifier(details.source_tank);
        const retained = toNumber(details.retained_quantity);
        if (sourceTank && Number.isFinite(toNumber(sourceTank.capacity))) {
          const cap = toNumber(sourceTank.capacity);
          if (q > cap) return `Incinerated quantity (${q} mÂ³) cannot exceed source tank capacity (${cap} mÂ³).`;
          if (Number.isFinite(retained) && retained > cap) return `Retained quantity (${retained} mÂ³) cannot exceed source tank capacity (${cap} mÂ³).`;
          if (Number.isFinite(retained) && (q + retained) > cap) {
            return `Incinerated (${q} mÂ³) + Retained (${retained} mÂ³) cannot exceed source tank capacity (${cap} mÂ³).`;
          }
        }
      }

      if (method === "other") {
        if (!details.other_disposal_details?.trim()) return "Please describe the disposal method for 12.4 (Other).";
      }
    }

    // All checks passed
    return null;
  };


  // Main validation handler common for all the codes, but not in use anymore as individual handlers are being created per code
  const handleValidate = async () => {
    try {
      
      if (!vesselId) {
        alert("Vessel not selected");
        return false;
      }

      // ðŸ”¹ 1. Fetch raw entries
      const res = await fetch(`http://localhost:8000/api/orb/api/operations/?vessel_id=${vesselId}&is_deleted=false`);
      const data = await res.json();

      let allRawEntries = [];
      if (Array.isArray(data)) {
        allRawEntries = data;
      } else if (data && Array.isArray(data.results)) {
        allRawEntries = data.results;
      }
      console.log("Fetched raw entries:", allRawEntries);

      // ðŸ”¹ 2. Extract previous Code A entries
      const previousCodeAEntries = allRawEntries
        .filter(entry => entry.code === "A")
      console.log("Previous Code A Entries:", previousCodeAEntries);

      let isValid = true;
      if (formData.code === "B") {
        isValid = validateCodeB(
          formData.details,
          previousCodeAEntries,
          allRawEntries
        );
      }

      return isValid;
    } catch (err) {
      console.error("Validation failed", err);
      return false;
    }
  };


  // code D validation
  const validateCodeD = (details = {}, availableTanks = []) => {
    // helpers
    const toNumber = (v) => {
      if (v === null || v === undefined || v === "") return NaN;
      const s = String(v).replace(",", ".").trim();
      const n = Number(s);
      return Number.isFinite(n) ? n : NaN;
    };

    const findTankById = (id) => {
      if (id === null || id === undefined || id === "") return null;
      return (availableTanks || []).find(t => String(t.id) === String(id)) || null;
    };

    const findTankByName = (name) => {
      if (!name) return null;
      return (availableTanks || []).find(t => String(t.tank_name) === String(name)) || null;
    };

    const parseTimeMinutes = (timeStr) => {
      if (!timeStr) return NaN;
      const parts = String(timeStr).split(":");
      if (parts.length < 2) return NaN;
      const hh = parseInt(parts[0], 10);
      const mm = parseInt(parts[1], 10);
      if (!Number.isFinite(hh) || !Number.isFinite(mm)) return NaN;
      return hh * 60 + mm;
    };

    // --- basic source tank existence ---
    if (!details.source_tank_id) return "Source tank is required";
    const srcTank = findTankById(details.source_tank_id);

    // parse numeric fields
    const retainedQty = toNumber(details.source_tank_retained_m3);
    const dischargeQty = toNumber(details.quantity_discharged_m3);

    // retained negative check
    if (Number.isFinite(retainedQty) && retainedQty < 0) {
      return "Retained quantity cannot be negative";
    }

    // discharge must be provided and > 0
    if (!Number.isFinite(dischargeQty) || dischargeQty <= 0) {
      return "Quantity discharged must be > 0";
    }

    // if source tank known, validate against its capacity
    if (srcTank && Number.isFinite(toNumber(srcTank.capacity))) {
      const srcCap = toNumber(srcTank.capacity);

      if (dischargeQty > srcCap) {
        return `Discharge quantity (${dischargeQty} mÂ³) cannot exceed source tank capacity (${srcCap} mÂ³)`;
      }

      if (Number.isFinite(retainedQty) && retainedQty > srcCap) {
        return `Retained quantity (${retainedQty} mÂ³) cannot exceed source tank capacity (${srcCap} mÂ³)`;
      }

      // Combined check: discharge + retained must not exceed source capacity.
      // If retained not provided (NaN) we assume UI auto-fills it; but still check using 0 if missing.
      const retainedForCheck = Number.isFinite(retainedQty) ? retainedQty : 0;
      if ((dischargeQty + retainedForCheck) > srcCap) {
        return `Total (Discharge + Retained = ${dischargeQty + retainedForCheck} mÂ³) cannot exceed source tank capacity (${srcCap} mÂ³)`;
      }
    }

    // --- time checks (start/stop) ---
    if (!details.start_time) return "Start time is required";
    if (!details.stop_time) return "Stop time is required";

    const startMin = parseTimeMinutes(details.start_time);
    const stopMin = parseTimeMinutes(details.stop_time);

    if (!Number.isFinite(startMin)) return "Start time is invalid";
    if (!Number.isFinite(stopMin)) return "Stop time is invalid";

    if (stopMin <= startMin) {
      return "Stop time must be greater than Start time";
    }

    // --- method specific ---
    if (!details.method) return "Please select a method (15.1, 15.2, or 15.3)";

    // 15.1 Through 15 ppm Equipment: require full start & stop positions
    if (details.method === "15ppm" || details.method === "15.1") {
      // validate start
      if (
        !Number.isFinite(toNumber(details.ppm_start_lat_deg)) ||
        !Number.isFinite(toNumber(details.ppm_start_lat_min)) ||
        typeof details.ppm_start_lat_dir !== "string" || !["N", "S"].includes(String(details.ppm_start_lat_dir).toUpperCase()) ||
        !Number.isFinite(toNumber(details.ppm_start_lon_deg)) ||
        !Number.isFinite(toNumber(details.ppm_start_lon_min)) ||
        typeof details.ppm_start_lon_dir !== "string" || !["E", "W"].includes(String(details.ppm_start_lon_dir).toUpperCase())
      ) {
        return "Position at Start (lat/lon deg, min and direction) is required for 15.1 (15ppm).";
      }

      // validate stop
      if (
        !Number.isFinite(toNumber(details.ppm_end_lat_deg)) ||
        !Number.isFinite(toNumber(details.ppm_end_lat_min)) ||
        typeof details.ppm_end_lat_dir !== "string" || !["N", "S"].includes(String(details.ppm_end_lat_dir).toUpperCase()) ||
        !Number.isFinite(toNumber(details.ppm_end_lon_deg)) ||
        !Number.isFinite(toNumber(details.ppm_end_lon_min)) ||
        typeof details.ppm_end_lon_dir !== "string" || !["E", "W"].includes(String(details.ppm_end_lon_dir).toUpperCase())
      ) {
        return "Position at Stop (lat/lon deg, min and direction) is required for 15.1 (15ppm).";
      }
    }

    // 15.2 Reception: require port + receipt
    if (details.method === "reception" || details.method === "15.2") {
      if (!details.reception_port || !String(details.reception_port).trim()) {
        return "Port name is required for 15.2 (Reception Facility).";
      }
      // if (!details.reception_receipt_no || !String(details.reception_receipt_no).trim()) {
      //   return "Receipt number is required for 15.2 (Reception Facility).";
      // }
    }

    // 15.3 Holding: require destination tank + retained >0 and within dest capacity; destination must not be source
    if (details.method === "holding" || details.method === "15.3") {
      if (!details.holding_tank_ids) {
        return "Destination tank is required for 15.3 (Holding).";
      }

      const destTank = findTankByName(details.holding_tank_ids);
      // if (destTank && srcTank && String(destTank.id) === String(srcTank.id)) {
      //   return "Destination tank cannot be the same as the source tank.";
      // }

      const destRetained = toNumber(details.holding_tank_retained_m3);
      if (!Number.isFinite(destRetained) || destRetained <= 0) {
        return "Retained quantity (destination) is required and must be > 0 for 15.3.";
      }

      if (destTank && Number.isFinite(toNumber(destTank.capacity)) && destRetained > toNumber(destTank.capacity)) {
        return `Retained quantity (${destRetained} mÂ³) cannot exceed destination tank capacity (${destTank.capacity} mÂ³).`;
      }

      // ensure discharge > 0 (already checked) and does not exceed source capacity (already checked above).
    }

    // all good
    return null;
  };


  //  Code F validation
  const validateCodeF = (details) => {
    if (!details.failure_start_time) return "Failure start time is required";

    if (details.operation_mode === "failure") {
      if (!details.equipment_affected) return "Equipment affected is required";
      if (!details.failure_reason || details.failure_reason.trim().length === 0) {
        return "Description of failure is required";
      }
    } else if (details.operation_mode === "restoration") {
      if (!details.restored_time) return "Restored time is required";
      if (!details.failure_reason || details.failure_reason.trim().length === 0) {
        return "Description of restoration is required";
      }
    }

    return null;
  };

  //  Code G validation
  const validateCodeG = (details) => {
    if (!details.occurrence_time) return "Time of occurrence is required";
    // if (!details.position) return "Position is required";
    // if (!/^\d{1,2}Â°\d{1,2}'[NS]\s*\d{1,3}Â°\d{1,2}'[EW]$/.test(details.position)) {
    //   return "Position must be in Lat/Long format (e.g., 10Â°10'N 078Â°20'E)";
    // }

    if (details.quantity_m3 < 0 || details.quantity_m3 == null) return "Quantity must be >= 0";
    if (!details.oil_type) return "Oil type is required";
    if (!details.remarks || details.remarks.trim().length === 0) return "Circumstances and remarks are required";

    return null;
  };

  //  Code I validation
  const validateCodeI = (details) => {
    if (!details.remarks || details.remarks.trim().length === 0) return "Remarks are required";
    if (details.remarks.trim().length < 10) return "Remarks must be descriptive and at least 10 characters long";
    return null;

  };



  // constant function for building rows format wise
  const rows = buildItemRows(
    formData.code,
    formData.details,
    new Date().toISOString(),
    user,
    availableTanks
  );


  // Main function for handling submit for entries , cross checks all the validations , sends the payload to backend ,goes through all the validation codewise
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.code) {
      alert("Please select an operation code (A-I)");
      return;
    }

    
    if (!vesselId) {
      alert("Vessel not selected");
      return;
    }


    let latestEntryDate = null;
    try {
      const latestResponse = await fetch(`http://localhost:8000/api/orb/api/latest-entry-date/?vessel_id=${vesselId}`);
      if (!latestResponse.ok) {
        // If the endpoint doesn't exist yet or returns an error (e.g., no entries), handle gracefully
        // console.error("Error fetching latest entry date:", await latestResponse.text());
        // Assume no latest date constraint if the endpoint fails initially
        // Or handle specific status codes if needed
        if (latestResponse.status === 404) {
          // No entries found, this is acceptable, latestEntryDate remains null
          console.log("INFO: No previous entries found for vessel, date validation skipped.");
        } else {
          // Other error occurred
          throw new Error(`Failed to fetch latest entry date: ${latestResponse.status} - ${await latestResponse.text()}`);
        }
      } else {
        const latestData = await latestResponse.json();
        latestEntryDate = latestData.latest_date; // Assuming backend returns {"latest_date": "YYYY-MM-DDTHH:MM:SS.sssZ"}
        console.log("DEBUG: Fetched latest entry date from API:", latestEntryDate);
      }
    } catch (err) {
      console.error("Error fetching latest entry date for validation:", err);
      setError(`Error validating date: ${err.message}. Cannot save.`);
      alert(`Error validating date: ${err.message}. Cannot save.`);
      return; // Stop submission if validation fails due to network/api error
    }

    // Perform the date comparison
    if (latestEntryDate && formData.date) { // Ensure formData.date exists
      const formDateTime = new Date(formData.date);
      const latestDateTime = new Date(latestEntryDate);

      if (formDateTime < latestDateTime) {
        const errorMessage = `Entry date/time (${formData.date}) cannot be earlier than the latest existing entry date/time (${latestEntryDate}).`;
        setError(errorMessage);
        alert(errorMessage);
        return; // Stop submission if date is invalid
      } else {
        console.log("DEBUG: Form date is valid (>= latest). Proceeding with save.");
      }
    } else if (latestEntryDate && !formData.date) {
      // Should not happen if date is required, but good to check
      setError("Entry date is required.");
      alert("Entry date is required.");
      return;
    }


    if (!Array.isArray(availableTanks) || availableTanks.length === 0) {
      alert("Tank data not loaded. Please wait or refresh.");
      return;
    }
   
    const officerName = user?.UserName || "OFFICER-IN-CHARGE";

    // --- Get officer details from the user object ---
    // Use the keys that match your session storage structure (first_name, surname, rank_name)
    const officerFirstName = user?.first_name || "OFFICER-IN-CHARGE";
    const officerSurname = user?.surname || ""; // Can be empty if not available
    const officerFullName = `${officerFirstName} ${officerSurname}`.trim(); // Combine for full name
    const officerRank = user?.rank || "OFFICER"; // Use rank_name
    console.log("DEBUG: handleSubmit - Extracted Name: ", officerFullName, " Rank: ", officerRank);

    const orbCode = codes.find(c => c.code === formData.code);
    if (!orbCode) {
      alert("Invalid ORB Code selected");
      return;
    }




    //   . Fetch all raw entries for validation (e.g., for Code A)
    let allRawEntries = [];
    try {
      const res = await fetch(`http://localhost:8000/api/orb/api/operations/?vessel_id=${vesselId}&is_deleted=false`);
      const data = await res.json();
      allRawEntries = Array.isArray(data) ? data : data.results || [];
    } catch (err) {
      console.error("Failed to fetch raw entries for validation", err);
      allRawEntries = [];
    }



    try {
      //  Fetch ALL raw entries for validation
      
      const allRawEntriesResponse = await fetch(
        `http://localhost:8000/api/orb/api/operations/?vessel_id=${vesselId}&is_deleted=false`
      );
      const allRawEntries = await allRawEntriesResponse.json();
      console.log("allrawentries for c", allRawEntries)
      // Now validate
      let validationError = null;

      if (formData.code === 'C') {
        validationError = await validateCodeC(formData.details, availableTanks, allRawEntries);
      }
      console.log("validated C")
      // ... other codes

      if (validationError) {
        alert(`Validation Failed:\n\n${validationError}`);
        return;
      }

      //  Proceed with save
    } catch (err) {
      console.error("Submit error:", err);
      alert("Network error");
    }





    let validationError = null;

    if (formData.code === 'A') {
      validationError = validateCodeA(formData.details, availableTanks);
    } else if (formData.code === 'B') {
      validationError = validateCodeB(formData.details, allRawEntries, availableTanks);
    } else if (formData.code === 'C') {
      validationError = await validateCodeC(formData.details, availableTanks, allRawEntries);
    } else if (formData.code === 'D') {
      validationError = validateCodeD(formData.details, availableTanks);
    } else if (formData.code === 'F') {
      validationError = validateCodeF(formData.details);
    } else if (formData.code === 'G') {
      validationError = validateCodeG(formData.details, availableTanks);
    } else if (formData.code === 'I') {
      validationError = validateCodeI(formData.details);
    }

    if (validationError) {
      alert(`Validation Failed:\n\n${validationError}`);
      return;
    }
    // Build rows for display and save
    const rows = buildItemRows(
      formData.code,
      formData.details,
      new Date().toISOString(),
      user,
      availableTanks
    );

    if (!rows || rows.length === 0) {
      alert("No operation entries to save");
      return;
    }

    const fullRecord = rows.map(r => r.value).join('\n');
    const mainItemNo = rows[0]?.item || null;

    const payload = {
      vessel: vesselId,
      date: formData.date,
      code: formData.code,
      orb_code_id: orbCode.id,
      item_no: mainItemNo,
      record_of_operation: fullRecord,
      status: "Pending",
      created_by: officerFullName,
      submitted_by: officerFullName,  //  Auto-set
      submitted_at: new Date().toISOString(),
      is_deleted: false,
      approved_by: null,
      approved_at: null,
      rejected_by: null,
      rejected_at: null
    };


    //  If in Chief mode, use onSubmit and skip draft save
    if (isChiefMode && typeof onSubmit === 'function') {
      onSubmit(payload);
      return;
    }

    //  If in Chief mode, use onSubmit and skip draft save
    if (isChiefMode && typeof onSubmit === 'function') {
      onSubmit(payload); // 'payload' is defined here
      return;
    }
    // --- HANDLE EDITING (MODIFIED) ---
    if (editingEntryId) {
      console.log("DEBUG: Sending payload for update:", payload); // Add this line for debugging
      try {
        // Send the SINGLE 'payload' object (NOT wrapped in an array)
        const updateResponse = await fetch(`http://localhost:8000/api/orb/api/operations/${editingEntryId}/update-group/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            // Include authorization headers if required
          },
          body: JSON.stringify(payload), // <--- This is the fix! Remove the square brackets.
        });

        if (!updateResponse.ok) {
          const updateErrorData = await updateResponse.text();
          throw new Error(`Failed to update entry group: ${updateResponse.status} - ${updateErrorData}`);
        }

        const result = await updateResponse.json();
        console.log("Entry group updated successfully:", result);

        // Reset form state after successful edit
        setFormData({ code: "", details: {} });
        setEditingEntryId(null);
        refreshEntries();
        alert("ORB Entry Updated Successfully!");

      } catch (err) {
        console.error("Error updating entry group:", err);
        alert(`Error updating entry: ${err.message}`);
      }
      return;
    }
    // --- END HANDLE EDITING ---



    //   . Handle Code F â†’ Code I Mandatory Flow
    if (formData.code === 'F') {
      //   . Store F temporarily
      setPendingFEntry({
        ...payload,
        details: formData.details,
        officerName,
        rows
      });

      alert(" Now please add a mandatory Code I to save this entry.");
      setFormData({ code: 'I', details: { remarks: '' } });
      return; //   . Stop here
    }

    //   . Handle Code I after pending F
    if (formData.code === 'I' && pendingFEntry) {
      const validationError = validateCodeI(formData.details);
      if (validationError) {
        alert(`Validation Failed:\n\n${validationError}`);
        return;
      }

      try {
        //  Save Code F
        await fetch("http://localhost:8000/api/orb/api/operations/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(pendingFEntry)
        });

        //   . Save Code I
        await fetch("http://localhost:8000/api/orb/api/operations/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        alert(" Both Code F and Code I entries saved successfully.");

        //   . Reset
        setPendingFEntry(null);
        setFormData({ code: "", details: {} });
        refreshEntries();
        // ORBTable()
      } catch (err) {
        console.error("Save failed:", err);
        alert(" Save failed: " + err.message);
      }

      return;
    }

    //   . For all other codes (or Code I without pending F)
    try {
      const response = await fetch("http://localhost:8000/api/orb/api/operations/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        alert(" Save failed: " + JSON.stringify(data));
        return;
      }

      alert(" ORB Entry Saved");
      setFormData({ code: "", details: {} });
      if (payload.status === 'Approved') {
        setLastApprovedEntries(prev => [...prev, payload]);
      } else if (payload.status === 'Rejected') {
        setLastRejectedEntries(prev => [...prev, payload]);
      } else if (payload.is_deleted) {
        setLastDeletedEntries(prev => [...prev, payload]);
      }
      refreshEntries();

    } catch (err) {
      console.error("Save error:", err);
      alert(` Save failed: ${err.message}`);
    }
    refreshEntries();
  };



  // Main Function for EDIT functionality
  const handleEdit = (id) => {
    // Find the entry based on the clicked ID (assuming 'id' is the entry's ID)
    const entryToEdit = entries.find(entry => entry.id === id);

    if (!entryToEdit) {
      console.error("Entry to edit not found:", id);
      alert("Entry not found for editing.");
      return;
    }

    // Determine the code
    const code = entryToEdit.code;

    // Reconstruct details from the record_of_operation string
    // This is the reverse of buildItemRows and is complex.
    // For now, use the placeholder function or enhance your backend/fetch logic.
    let reconstructedDetails = parseRecordToDetails(code, entryToEdit.record_of_operation); // Pass the record_of_operation string

    if (!reconstructedDetails) {
      alert("Could not load entry details for editing. Please try again or contact support.");
      return;
    }

    // Set the form data to the details of the entry being edited
    setFormData({
      code: code,
      details: reconstructedDetails,
    });

    // Store the ID of the entry being edited
    setEditingEntryId(id);

    // Optionally, scroll or focus
    // window.scrollTo({ top: 0, behavior: 'smooth' });
  };



  const parseRecordToDetails = (code, recordText) => {
    if (!recordText) {
      console.warn("Empty recordText provided for code:", code);
      return {};
    }

    const lines = recordText.split('\n').map(l => l.trim()).filter(l => l !== '');
    // main entry code switch cases 
    switch (code) {
      case 'A':
        let detailsA = {};
        for (const line of lines) {
          // 1. TANK(S) BALLASTED
          if (line.startsWith('1.')) {
            const match = line.match(/TANK\(S\) BALLASTED:\s*(.+)/i);
            if (match) detailsA.tank_identity = match[1].trim();
          }
          // 2. TANK CLEANED SINCE LAST OIL / NOT CLEANED â€“ PREVIOUS OIL
          else if (line.startsWith('2.')) {
            if (line.includes('NOT CLEANED â€“ PREVIOUS OIL')) {
              detailsA.cleaned_since_last = 'no';
              const prevOilMatch = line.match(/NOT CLEANED â€“ PREVIOUS OIL:?\s*(.+)/i);
              if (prevOilMatch) detailsA.previous_oil = prevOilMatch[1].trim();
            } else if (line.includes('TANK CLEANED SINCE')) {
              detailsA.cleaned_since_last = 'yes';
            }
          }
          // 3.1 START/STOP Cleaning
          else if (line.startsWith('3.1')) {
            // Parsing positions is complex, might require more specific regex if needed
            // Example: "3.1 START POSITION (Lat/Long) (When cleaning started): 45Â° 30' N, 012Â° 45' E"
            const startMatch = line.match(/START POSITION \(Lat\/Long\) \(When cleaning started\):\s*(.+)/i);
            if (startMatch) {
              // Parsing lat/long is complex, store raw string or implement detailed parsing
              detailsA.cleaning_start_position_raw = startMatch[1].trim();
            }
            const stopMatch = line.match(/STOP POSITION \(Lat\/Long\) \(When cleaning stopped\):\s*(.+)/i);
            if (stopMatch) {
              detailsA.cleaning_end_position_raw = stopMatch[1].trim();
            }
          }
          // 3.2 METHOD USED
          else if (line.startsWith('3.2')) {
            if (line.includes('RINSING')) detailsA.cleaning_method = 'rinsing';
            else if (line.includes('STEAMING')) detailsA.cleaning_method = 'steaming';
            else if (line.includes('CHEMICAL')) {
              detailsA.cleaning_method = 'chemical';
              // Extract chemical name if present, often on the same line or next
              const chemNameMatch = line.match(/CHEMICAL:\s*(.+)/i);
              if (chemNameMatch) detailsA.chemical_name = chemNameMatch[1].trim();
            }
          }
          // 3.3 CLEANING WATER TO SLOP TANK
          else if (line.startsWith('3.3')) {
            const match = line.match(/CLEANING WATER TO SLOP TANK:\s*(.+)/i);
            if (match) detailsA.slop_tank_id = match[1].trim();
          }
          // 4.1 START BALLAST
          else if (line.startsWith('4.1')) {
            // Parse time and position - complex
            const match = line.match(/START BALLAST:\s*(.+)/i);
            if (match) detailsA.ballast_start_raw = match[1].trim();
          }
          // 4.2 BALLAST QUANTITY
          else if (line.startsWith('4.2')) {
            const match = line.match(/BALLAST QUANTITY:\s*([\d.]+)\s*MÂ³/i);
            if (match) detailsA.ballast_quantity = parseFloat(match[1]);
          }
        }
        return detailsA;

      case 'B':
        let detailsB = {};
        for (const line of lines) {
          // 6. POS START
          if (line.startsWith('6.')) {
            // Complex position parsing, store raw for now
            detailsB.pos_start_raw = line.substring(2).trim(); // Remove "6. "
          }
          // 7. POS END
          else if (line.startsWith('7.')) {
            detailsB.pos_end_raw = line.substring(2).trim(); // Remove "7. "
          }
          // 8. SHIP SPEEDS
          else if (line.startsWith('8.')) {
            const speedsMatch = line.match(/SHIP SPEEDS:\s*(.+)/i);
            if (speedsMatch) detailsB.ship_speeds = speedsMatch[1].trim();
          }
          // 9.1 THROUGH 15 PPM EQUIPMENT
          else if (line.startsWith('9.1')) {
            detailsB.method = '15ppm';
            // Quantity might be on this line or implied
          }
          // 9.2 TO RECEPTION FACILITIES
          else if (line.startsWith('9.2')) {
            detailsB.method = 'reception';
            // Reception details might follow
          }
          // 10. QUANTITY DISCHARGED
          else if (line.startsWith('10.')) {
            const match = line.match(/QUANTITY DISCHARGED:\s*([\d.]+)\s*MÂ³/i);
            if (match) detailsB.quantity_discharged_m3 = parseFloat(match[1]);
          }
        }
        return detailsB;

      case 'C':
        let detailsC = { operation_mode: '' }; // Default
        for (const line of lines) {
          // 11.1 Identity of tank(s) - Often starts with 11.1 or just contains the tank name after "Identity:"
          if (line.startsWith('11.1') || line.includes('Identity of tank(s):')) {
            const match = (line.startsWith('11.1') ? line.substring(4) : line.split('Identity of tank(s):')[1]).trim();
            detailsC.sludge_tank_id = match;
          }
          // 11.2, 11.3, 11.4 - Quantities and capacities
          else if (line.startsWith('11.2')) {
            // This is often the "Before" quantity for weekly updates
            const match = line.match(/BEFORE:\s*([\d.]+)\s*MÂ³/i);
            if (match) detailsC.sludge_before = parseFloat(match[1]);
          }
          else if (line.startsWith('11.3')) {
            // This could be "Manual Collection" quantity
            const match = line.match(/MANUAL COLLECTION:\s*([\d.]+)\s*MÂ³/i);
            if (match) detailsC.manual_collection_m3 = parseFloat(match[1]);
          }
          else if (line.startsWith('11.4')) {
            // This could be "Transfer/Disposal" details
            detailsC.disposal_details = line.substring(4).trim(); // Remove "11.4 "
          }
          // 12.1, 12.2, 12.3, 12.4 - Disposal methods
          else if (line.startsWith('12.1')) {
            detailsC.operation_mode = 'transfer';
            detailsC.disposal_method = 'reception_facility';
            detailsC.reception_details = line.substring(4).trim(); // Remove "12.1 "
          }
          else if (line.startsWith('12.2')) {
            detailsC.operation_mode = 'transfer';
            detailsC.disposal_method = 'transfer_tank';
            detailsC.transferred_to_Tank_ids = line.substring(4).trim(); // Remove "12.2 "
          }
          else if (line.startsWith('12.3')) {
            detailsC.operation_mode = 'transfer';
            detailsC.disposal_method = 'incineration';
            detailsC.incineration_details = line.substring(4).trim(); // Remove "12.3 "
          }
          else if (line.startsWith('12.4')) {
            detailsC.operation_mode = 'transfer';
            detailsC.disposal_method = 'other';
            detailsC.other_disposal_details = line.substring(4).trim(); // Remove "12.4 "
          }
        }
        // Determine operation_mode based on found fields
        if (!detailsC.operation_mode) {
          if (detailsC.sludge_before !== undefined) detailsC.operation_mode = 'weekly';
          else if (detailsC.manual_collection_m3 !== undefined) detailsC.operation_mode = 'manual';
        }
        return detailsC;

      case 'D':
        let detailsD = {};
        for (const line of lines) {
          // 13. SOURCE TANK INFO
          if (line.startsWith('13.')) {
            // This might just be the tank name or a line like "SOURCE TANK: ..."
            const match = line.match(/SOURCE TANK:\s*(.+)/i) || line.substring(3).trim();
            detailsD.source_tank_id = typeof match === 'string' ? match : match[1];
          }
          // 14. START TIME
          else if (line.startsWith('14.')) {
            detailsD.start_time = line.substring(3).trim(); // Remove "14. "
          }
          // 15.1 THROUGH 15 PPM EQUIPMENT
          else if (line.startsWith('15.1')) {
            detailsD.method = '15ppm';
          }
          // 15.2 TO PORT RECEPTION FACILITIES
          else if (line.startsWith('15.2')) {
            detailsD.method = 'reception';
            detailsD.reception_port = line.substring(4).trim(); // Remove "15.2 "
          }
          // 15.3 TRANSFERRED TO / RETAINED IN TANK
          else if (line.startsWith('15.3')) {
            detailsD.method = 'holding';
            // Parse destination tank and retained quantity
            const tankMatch = line.match(/TRANSFERRED TO\s+(.+?)\s+OR\s+RETAINED IN TANK\s+(.+?)\s+QUANTITY\s+([\d.]+)\s+mÂ³/i);
            if (tankMatch) {
              detailsD.holding_tank_ids = tankMatch[1].trim() || tankMatch[2].trim(); // Pick first non-empty
              detailsD.holding_tank_retained_m3 = parseFloat(tankMatch[3]);
            }
          }
          // Quantity discharged (often item 10 in B, but context might vary)
          else if (line.includes('QUANTITY DISCHARGED')) {
            const match = line.match(/QUANTITY DISCHARGED:\s*([\d.]+)\s*MÂ³/i);
            if (match) detailsD.quantity_discharged_m3 = parseFloat(match[1]);
          }
        }
        return detailsD;

      case 'F':
        let detailsF = {};
        for (const line of lines) {
          // 19. FAILURE STARTED
          if (line.startsWith('19.')) {
            // Parse time and date - complex, store raw
            detailsF.failure_start_raw = line.substring(3).trim(); // Remove "19. "
          }
          // 20. TIME OF FAILURE / EQUIPMENT
          else if (line.startsWith('20.')) {
            // Could be time or equipment description
            detailsF.time_of_failure = line.substring(4).trim(); // Remove "20. "
            // Or, if it contains equipment info:
            if (line.toLowerCase().includes('equipment')) {
              detailsF.equipment_details = line.substring(4).trim();
            }
          }
          // 21. DESCRIPTION OF FAILURE
          else if (line.startsWith('21.')) {
            detailsF.description_of_failure = line.substring(4).trim(); // Remove "21. "
          }
        }
        return detailsF;

      case 'G':
        let detailsG = {};
        for (const line of lines) {
          // 23. POSITION
          if (line.startsWith('23.')) {
            // Complex position parsing, store raw
            detailsG.position_raw = line.substring(3).trim(); // Remove "23. "
          }
          // 24. QUANTITY AND TYPE OF OILY MIXTURE
          else if (line.startsWith('24.')) {
            // Parse quantity and type - complex
            detailsG.quantity_type_raw = line.substring(3).trim(); // Remove "24. "
          }
          // 25. REMARKS
          else if (line.startsWith('25.')) {
            detailsG.remarks = line.substring(3).trim(); // Remove "25. "
          }
        }
        return detailsG;

      case 'H':
        let detailsH = {};
        for (const line of lines) {
          // 26.1 PLACE
          if (line.startsWith('26.1')) {
            const match = line.match(/PLACE:\s*(.+)/i);
            if (match) detailsH.place_of_bunkering = match[1].trim();
          }
          // 26.2 TIME
          else if (line.startsWith('26.2')) {
            // Parse start/end times - complex, store raw
            detailsH.bunkering_time_raw = line.substring(4).trim(); // Remove "26.2 "
          }
          // 26.3 FUEL OIL BUNKERED IN TANKS
          else if (line.startsWith('26.3')) {
            // Parse tanks and quantities - complex, often involves multiple lines in the original form
            detailsH.fuel_oil_details_raw = line.substring(4).trim(); // Remove "26.3"
          }
          // 26.4 LUBE BUNKERED IN TANKS
          else if (line.startsWith('26.4')) {
            detailsH.lube_oil_details_raw = line.substring(4).trim();
          }
        }
        return detailsH;

      case 'I':
        // Code I is usually just remarks.
        // It might span multiple lines or be a single block.
        // The function receives the full recordText, so join lines if needed or take the whole string.
        // Assuming the entire recordText (excluding item numbers if any are prepended by buildItemRows) is remarks.
        // Often, the first line might be just "22. REMARKS:" followed by the text.
        // A simple approach: strip item numbers and return the rest as remarks.
        let remarksText = recordText;
        // Remove lines that look like item numbers (e.g., "22. REMARKS: ...")
        remarksText = remarksText.replace(/^\d+(\.\d+)?\.\s*REMARKS:\s*/mi, '').trim();
        // Remove leading item numbers from other lines if they exist
        remarksText = remarksText.replace(/^\d+(\.\d+)?\.\s*/gm, '').trim();

        return { remarks: remarksText };

      default:
        console.warn("Parsing details for code", code, "is not implemented.");
        // Return an object with the raw recordText as a fallback
        return { raw_parsed_record: recordText };
    }
  };




  // Inside CrewDashboard.jsx, in the handleDelete function
  const handleDelete = async (id) => {
    // ... (ownership check, confirm dialog) ...
    try {
      // Send PATCH request to the main resource endpoint
      const response = await fetch(`http://localhost:8000/api/orb/api/operations/${id}/`, { // Correct endpoint
        method: 'PATCH', // Use PATCH
        headers: {
          'Content-Type': 'application/json',
          // Include authorization headers if required
        },
        body: JSON.stringify({ is_deleted: true }) // Send the flag
      });

      if (response.ok) {
        // Update local state
        setEntries(entries.filter(e => e.id !== id));
        alert("Draft deleted successfully");
      } else {
        // Handle error response
        const errorData = await response.json().catch(() => response.text());
        console.error("Delete failed:", errorData);
        alert(`Delete failed: ${JSON.stringify(errorData)}`);
      }
    } catch (err) {
      console.error("Network error:", err);
      alert("Network error: Unable to reach server");
    }
  };


  return (
    <>
      <div className="orb-theme" >
        <Stack>
          <Panel title=" ORB Entry ">
            <ORBEntryForm
              formData={formData}
              handleChange={handleChange}
              handleTankChange={handleTankChange}
              addTank={addTank}
              removeTank={removeTank}
              handleSubmit={handleSubmit}
              handleDelete={handleDelete}
              setFormData={setFormData}
              codes={codes}
              availableTanks={availableTanks}
              formatToDateTimeLocal={formatToDateTimeLocal}
              yesterdayDate={yesterdayDate}
              formatToDisplay={formatToDisplay}
              groupEntriesByLogicalORBEntry={groupEntriesByLogicalORBEntry}
              bunkeringType={bunkeringType}
              setBunkeringType={setBunkeringType}
              errors={errors}
              setShowSludgeSummary={setShowSludgeSummary}
            />


            {!isChiefMode && (

              <ORBTable entries={entries} onEdit={handleEdit} onDelete={handleDelete} />

            )}


          </Panel>
        </Stack>
      </div>
    </>
  );
}



function ORBEntryForm(
  { formData,
    handleChange,
    handleTankChange,
    addTank,
    removeTank,
    handleSubmit,
    handleDelete,
    setFormData,
    codes,
    availableTanks,
    formatToDateTimeLocal,
    yesterdayDate,
    formatDate,
    groupEntriesByLogicalORBEntry,
    bunkeringType,
    setBunkeringType,
    errors,
    setShowSludgeSummary,
    setErrors }

) {
  useEffect(() => {
    console.log('codes in orb form : ', codes)
  }, [codes])

  const renderFields = () => {
    const { code, details } = formData;


    const dateInputSection = (
      <div className="form-row" style={{ marginBottom: '1rem' }}>
        <label htmlFor="entry-date" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Entry Date & Time *
        </label>
        <input
          id="entry-date"
          type="datetime-local"
          value={formData.date || ""}
          onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
          max={formatToDateTimeLocal(new Date())}
          required
          style={{
            width: '20%',
            padding: '10px',
            border: '2px solid #007bff',
            borderRadius: '4px',
            fontSize: '14px',
            backgroundColor: '#fff',
            color: '#333',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            transition: 'border-color 0.3s ease',
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#0056b3';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#007bff';
          }}
        />
        {errors.date && (
          <span style={{ color: 'red', fontSize: '12px', display: 'block', marginTop: '0.25rem' }}>
            {errors.date}
          </span>
        )}
      </div>
    );

    switch (code) {

      case 'A':
        return (

          <div className="card" style={{ width: "920px" }}>
            {dateInputSection}
            {/* Operation Type */}
            <div>
              <label>Operation Type *</label>
              <select
                value={details.operation_type || ""}
                onChange={(e) => handleChange('operation_type', e.target.value)}
              >
                <option value="">Select Operation</option>
                {/* <option value="cleaning">Cleaning Only</option>
                <option value="ballasting">Ballasting Only</option> */}
                <option value="both">Cleaning & Ballasting</option>
              </select>
              {errors.operation_type && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.operation_type}
                </span>
              )}
            </div>

            {/* 1. Tank(s) Ballasted */}
            {(details.operation_type === "ballasting" || details.operation_type === "both") && (
              <div>
                <label>1. Identity of Tank(s) Ballasted *</label>
                <select
                  value={details.tank_identity || ""}
                  onChange={(e) => handleChange('tank_identity', e.target.value)}
                  style={{ borderColor: errors.tank_identity ? 'red' : '#ccc' }}
                >
                  <option value="">Select Tank</option>
                  {availableTanks

                    .map(tank => (
                      <option key={tank.id} value={tank.tank_name}>
                        {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                      </option>
                    ))
                  }
                </select>
                {errors.tank_identity && (
                  <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                    {errors.tank_identity}
                  </span>
                )}
              </div>
            )}

            {/* 2. Cleaned Since Last Oil */}
            {(details.operation_type === "cleaning" || details.operation_type === "both") && (
              <div>
                <label>2. Cleaned Since Last Oil Contents? *</label>
                <select
                  value={details.cleaned_since_last || ""}
                  onChange={(e) => handleChange('cleaned_since_last', e.target.value)}
                  style={{ borderColor: errors.cleaned_since_last ? 'red' : '#ccc' }}
                >
                  <option value="">Select</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
                {errors.cleaned_since_last && (
                  <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                    {errors.cleaned_since_last}
                  </span>
                )}
              </div>
            )}

            {/* 2. Previous Oil (if not cleaned) */}
            {details.cleaned_since_last === "no" && (details.operation_type === "cleaning" || details.operation_type === "both") && (
              <div>
                <label>2. Type of Previous Oil</label>
                <input
                  type="text"
                  value={details.previous_oil || ""}
                  onChange={(e) => handleChange('previous_oil', e.target.value.toUpperCase())}
                  placeholder="e.g., HFO"
                  style={{ borderColor: errors.previous_oil ? 'red' : '#ccc' }}
                />
                {errors.previous_oil && (
                  <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                    {errors.previous_oil}
                  </span>
                )}
                <label>Density/Viscosity</label>
                <input
                  type="text"
                  value={details.oil_density || ""}
                  onChange={(e) => {
                    const onlyNumbersAndDot = e.target.value.replace(/[^0-9.]/g, ""); // allow digits + dot
                    handleChange("oil_density", onlyNumbersAndDot);
                  }}
                  placeholder="e.g., 0.985 g/cmÂ³"
                />
              </div>
            )}

            {/* 3.1 Cleaning Start/End & Position */}
            {(details.operation_type === "cleaning" || details.operation_type === "both") && (
              <>
                {/* 3.1 Start Position */}
                <div>
                  <label>3.1 Start Position (Lat/Long) (When cleaning started)</label>
                  <div style={{ display: "grid", gridTemplateColumns: "auto auto auto auto auto auto", gap: "8px", marginTop: "4px", alignItems: "center" }}>
                    {/* Lat Deg */}
                    <div>
                      <label>Lat Deg</label>
                      <select
                        value={details.cleaning_start_lat_deg || ""}
                        onChange={(e) =>
                          handleChange(
                            "cleaning_start_lat_deg",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">Â°</option>
                        {[...Array(91)].map((_, i) => (
                          <option key={i} value={i}>{i}</option>
                        ))}
                      </select>
                    </div>

                    {/* Lat Min */}
                    <div>
                      <label>Min</label>
                      <select
                        value={details.cleaning_start_lat_min || ""}
                        onChange={(e) =>
                          handleChange(
                            "cleaning_start_lat_min",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">â€²</option>
                        {[...Array(60)].map((_, i) => (
                          <option key={i} value={i}>{i}</option>
                        ))}
                      </select>
                    </div>

                    {/* Lat Dir */}
                    <div>
                      <label>Dir</label>
                      <select
                        value={details.cleaning_start_lat_dir || ""}
                        onChange={(e) => handleChange("cleaning_start_lat_dir", e.target.value)}
                        style={{ width: "60px" }}
                      >
                        <option value="">N/S</option>
                        <option value="N">N</option>
                        <option value="S">S</option>
                      </select>
                    </div>

                    {/* Lon Deg */}
                    <div>
                      <label>Lon Deg</label>
                      <select
                        value={details.cleaning_start_lon_deg || ""}
                        onChange={(e) =>
                          handleChange(
                            "cleaning_start_lon_deg",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">Â°</option>
                        {[...Array(181)].map((_, i) => (
                          <option key={i} value={i}>{i}</option>
                        ))}
                      </select>
                    </div>

                    {/* Lon Min */}
                    <div>
                      <label>Min</label>
                      <select
                        value={details.cleaning_start_lon_min || ""}
                        onChange={(e) =>
                          handleChange(
                            "cleaning_start_lon_min",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">â€²</option>
                        {[...Array(60)].map((_, i) => (
                          <option key={i} value={i}>{i}</option>
                        ))}
                      </select>
                    </div>

                    {/* Lon Dir */}
                    <div>
                      <label>Dir</label>
                      <select
                        value={details.cleaning_start_lon_dir || ""}
                        onChange={(e) => handleChange("cleaning_start_lon_dir", e.target.value)}
                        style={{ width: "60px" }}
                      >
                        <option value="">E/W</option>
                        <option value="E">E</option>
                        <option value="W">W</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* 3.1 End Position */}
                <div style={{ marginTop: "16px" }}>
                  <label>3.1 End Position (Lat/Long) (When cleaning Completed)</label>
                  <div style={{ display: "grid", gridTemplateColumns: "auto auto auto auto auto auto", gap: "8px", marginTop: "4px", alignItems: "center" }}>
                    {/* Lat Deg */}
                    <div>
                      <label>Lat Deg</label>
                      <select
                        value={details.cleaning_end_lat_deg || ""}
                        onChange={(e) =>
                          handleChange(
                            "cleaning_end_lat_deg",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">Â°</option>
                        {[...Array(91)].map((_, i) => (
                          <option key={i} value={i}>{i}</option>
                        ))}
                      </select>
                    </div>

                    {/* Lat Min */}
                    <div>
                      <label>Min</label>
                      <select
                        value={details.cleaning_end_lat_min || ""}
                        onChange={(e) =>
                          handleChange(
                            "cleaning_end_lat_min",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">â€²</option>
                        {[...Array(60)].map((_, i) => (
                          <option key={i} value={i}>{i}</option>
                        ))}
                      </select>
                    </div>

                    {/* Lat Dir */}
                    <div>
                      <label>Dir</label>
                      <select
                        value={details.cleaning_end_lat_dir || ""}
                        onChange={(e) => handleChange("cleaning_end_lat_dir", e.target.value)}
                        style={{ width: "60px" }}
                      >
                        <option value="">N/S</option>
                        <option value="N">N</option>
                        <option value="S">S</option>
                      </select>
                    </div>

                    {/* Lon Deg */}
                    <div>
                      <label>Lon Deg</label>
                      <select
                        value={details.cleaning_end_lon_deg || ""}
                        onChange={(e) =>
                          handleChange(
                            "cleaning_end_lon_deg",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">Â°</option>
                        {[...Array(181)].map((_, i) => (
                          <option key={i} value={i}>{i}</option>
                        ))}
                      </select>
                    </div>

                    {/* Lon Min */}
                    <div>
                      <label>Min</label>
                      <select
                        value={details.cleaning_end_lon_min || ""}
                        onChange={(e) =>
                          handleChange(
                            "cleaning_end_lon_min",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">â€²</option>
                        {[...Array(60)].map((_, i) => (
                          <option key={i} value={i}>{i}</option>
                        ))}
                      </select>
                    </div>

                    {/* Lon Dir */}
                    <div>
                      <label>Dir</label>
                      <select
                        value={details.cleaning_end_lon_dir || ""}
                        onChange={(e) => handleChange("cleaning_end_lon_dir", e.target.value)}
                        style={{ width: "60px" }}
                      >
                        <option value="">E/W</option>
                        <option value="E">E</option>
                        <option value="W">W</option>
                      </select>
                    </div>
                  </div>
                </div>
              </>

            )}

            {/* 3.2 Method Used */}
            {(details.operation_type === "cleaning" || details.operation_type === "both") && (
              <>
                <div>
                  <label>3.2 Tank(s) Cleaned *</label>
                  <select
                    value={details.method_tank || ""}
                    onChange={(e) => handleChange('method_tank', e.target.value)}
                    style={{ width: '100%', padding: '8px' }}
                  >
                    <option value="">Select Tank</option>
                    {availableTanks
                      .map(tank => (
                        <option key={tank.id} value={tank.tank_name}>
                          {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                        </option>
                      ))
                    }
                  </select>
                  {errors.method_tank && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.method_tank}
                    </span>
                  )}
                </div>

                <div>
                  <label>3.2 Method Used *</label>
                  <select
                    value={details.cleaning_method || ""}
                    onChange={(e) => {
                      handleChange('cleaning_method', e.target.value);
                      if (e.target.value !== 'chemical') {
                        handleChange('chemical_name', '');
                        handleChange('chemicals_used', '');
                      }
                    }}
                    style={{ width: '100%', padding: '8px' }}
                  >
                    <option value="">Select Method</option>
                    <option value="Rinsing">RINSING</option>
                    <option value="Steaming">STEAMING</option>
                    <option value="chemical">CHEMICAL</option>
                  </select>
                  {errors.cleaning_method && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.cleaning_method}
                    </span>
                  )}
                </div>

                {/* 3.2 Chemical Name & Quantity */}
                {details.cleaning_method === 'chemical' && (
                  <>
                    <div>
                      <label>3.2 Chemical Name *</label>
                      <input
                        type="text"
                        value={details.chemical_name || ""}
                        onChange={(E) => handleChange('chemical_name', E.target.value.toUpperCase())}
                        placeholder="e.g., TANK CLEANER X100"
                        style={{ width: '100%' }}
                      />
                      {errors.chemical_name && (
                        <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                          {errors.chemical_name}
                        </span>
                      )}
                    </div>
                    <div>
                      <label>3.2 Chemicals Used (mÂ³) *</label>
                      <input
                        type="number"
                        step="0.01"
                        value={details.chemicals_used || ""}
                        onChange={(E) => handleChange('chemicals_used', parseFloat(E.target.value))}
                        placeholder="e.g., 0.5"
                        style={{ width: '100%' }}
                      />
                      {errors.chemicals_used && (
                        <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                          {errors.chemicals_used}
                        </span>
                      )}
                    </div>
                  </>
                )}
              </>
            )}

            {/* 3.3 Transfer to Slop Tank */}
            {(details.operation_type === "cleaning" || details.operation_type === "both") && (
              <div>
                <label>3.3 Transfer to Slop Tank *</label>
                <select
                  value={details.transfer_tank || ""}
                  onChange={(e) => handleChange('transfer_tank', e.target.value)}
                  style={{ borderColor: errors.transfer_tank ? 'red' : '#ccc' }}
                >
                  <option value="">Select Tank</option>
                  {availableTanks
                    .map(tank => (
                      <option key={tank.id} value={tank.tank_name}>
                        {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                      </option>
                    ))
                  }
                </select>
                {errors.transfer_tank && (
                  <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                    {errors.transfer_tank}
                  </span>
                )}
              </div>
            )}

            {/* 3.3 Quantity of Cleaning Water */}
            {(details.operation_type === "cleaning" || details.operation_type === "both") && (
              <div>
                <label>3.3 Quantity of Cleaning Water (mÂ³) *</label>
                <input
                  type="number"
                  step="0.01"
                  value={details.transfer_qty || ""}
                  onChange={(e) => handleChange('transfer_qty', parseFloat(e.target.value))}
                  placeholder="e.g., 5"
                  style={{ borderColor: errors.transfer_qty ? 'red' : '#ccc' }}
                />
                {errors.transfer_qty && (
                  <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                    {errors.transfer_qty}
                  </span>
                )}
              </div>
            )}

            {/* 4.1 Ballast Start/End */}
            {(details.operation_type === "ballasting" || details.operation_type === "both") && (
              <>
                <div>
                  <label>4.1 Ballast Start Time *</label>
                  <input
                    type="time"
                    value={details.ballast_start || ""}
                    onChange={(e) => handleChange('ballast_start', e.target.value)}
                    max={formatToDateTimeLocal(new Date())}
                    style={{ borderColor: errors.ballast_start ? 'red' : '#ccc', width: "150px" }}
                  />
                  {errors.ballast_start && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.ballast_start}
                    </span>
                  )}
                </div>

                <div>
                  <label>4.1 Ballast End Time *</label>
                  <input
                    type="time"
                    value={details.ballast_end || ""}
                    onChange={(e) => handleChange('ballast_end', e.target.value)}
                    min={details.ballast_start}
                    style={{ borderColor: errors.ballast_end ? 'red' : '#ccc', width: "150px" }}
                  />
                  {errors.ballast_end && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.ballast_end}
                    </span>
                  )}
                </div>

                {/* 4.1 Start Position */}
                <div>
                  <label>4.1 Start Position (Lat/Long)</label>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "auto auto auto auto auto auto",
                      gap: "8px",
                      marginTop: "4px",
                      alignItems: "center",
                    }}
                  >
                    {/* Lat Deg */}
                    <div>
                      <label>Lat Deg</label>
                      <select
                        value={details.ballast_start_lat_deg || ""}
                        onChange={(e) =>
                          handleChange(
                            "ballast_start_lat_deg",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">Â°</option>
                        {[...Array(91)].map((_, i) => (
                          <option key={i} value={i}>
                            {i}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Lat Min */}
                    <div>
                      <label>Min</label>
                      <select
                        value={details.ballast_start_lat_min || ""}
                        onChange={(e) =>
                          handleChange(
                            "ballast_start_lat_min",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">â€²</option>
                        {[...Array(60)].map((_, i) => (
                          <option key={i} value={i}>
                            {i}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Lat Dir */}
                    <div>
                      <label>Dir</label>
                      <select
                        value={details.ballast_start_lat_dir || ""}
                        onChange={(e) => handleChange("ballast_start_lat_dir", e.target.value)}
                        style={{ width: "60px" }}
                      >
                        <option value="">N/S</option>
                        <option value="N">N</option>
                        <option value="S">S</option>
                      </select>
                    </div>

                    {/* Lon Deg */}
                    <div>
                      <label>Lon Deg</label>
                      <select
                        value={details.ballast_start_lon_deg || ""}
                        onChange={(e) =>
                          handleChange(
                            "ballast_start_lon_deg",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">Â°</option>
                        {[...Array(181)].map((_, i) => (
                          <option key={i} value={i}>
                            {i}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Lon Min */}
                    <div>
                      <label>Min</label>
                      <select
                        value={details.ballast_start_lon_min || ""}
                        onChange={(e) =>
                          handleChange(
                            "ballast_start_lon_min",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">â€²</option>
                        {[...Array(60)].map((_, i) => (
                          <option key={i} value={i}>
                            {i}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Lon Dir */}
                    <div>
                      <label>Dir</label>
                      <select
                        value={details.ballast_start_lon_dir || ""}
                        onChange={(e) => handleChange("ballast_start_lon_dir", e.target.value)}
                        style={{ width: "60px" }}
                      >
                        <option value="">E/W</option>
                        <option value="E">E</option>
                        <option value="W">W</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* 4.1 End Position */}
                <div style={{ marginTop: "16px" }}>
                  <label>4.1 End Position (Lat/Long)</label>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "auto auto auto auto auto auto",
                      gap: "8px",
                      marginTop: "4px",
                      alignItems: "center",
                    }}
                  >
                    {/* Lat Deg */}
                    <div>
                      <label>Lat Deg</label>
                      <select
                        value={details.ballast_end_lat_deg || ""}
                        onChange={(e) =>
                          handleChange(
                            "ballast_end_lat_deg",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">Â°</option>
                        {[...Array(91)].map((_, i) => (
                          <option key={i} value={i}>
                            {i}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Lat Min */}
                    <div>
                      <label>Min</label>
                      <select
                        value={details.ballast_end_lat_min || ""}
                        onChange={(e) =>
                          handleChange(
                            "ballast_end_lat_min",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">â€²</option>
                        {[...Array(60)].map((_, i) => (
                          <option key={i} value={i}>
                            {i}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Lat Dir */}
                    <div>
                      <label>Dir</label>
                      <select
                        value={details.ballast_end_lat_dir || ""}
                        onChange={(e) => handleChange("ballast_end_lat_dir", e.target.value)}
                        style={{ width: "60px" }}
                      >
                        <option value="">N/S</option>
                        <option value="N">N</option>
                        <option value="S">S</option>
                      </select>
                    </div>

                    {/* Lon Deg */}
                    <div>
                      <label>Lon Deg</label>
                      <select
                        value={details.ballast_end_lon_deg || ""}
                        onChange={(e) =>
                          handleChange(
                            "ballast_end_lon_deg",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">Â°</option>
                        {[...Array(181)].map((_, i) => (
                          <option key={i} value={i}>
                            {i}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Lon Min */}
                    <div>
                      <label>Min</label>
                      <select
                        value={details.ballast_end_lon_min || ""}
                        onChange={(e) =>
                          handleChange(
                            "ballast_end_lon_min",
                            e.target.value === "" ? "" : parseInt(e.target.value, 10)
                          )
                        }
                        style={{ width: "70px" }}
                      >
                        <option value="">â€²</option>
                        {[...Array(60)].map((_, i) => (
                          <option key={i} value={i}>
                            {i}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Lon Dir */}
                    <div>
                      <label>Dir</label>
                      <select
                        value={details.ballast_end_lon_dir || ""}
                        onChange={(e) => handleChange("ballast_end_lon_dir", e.target.value)}
                        style={{ width: "60px" }}
                      >
                        <option value="">E/W</option>
                        <option value="E">E</option>
                        <option value="W">W</option>
                      </select>
                    </div>
                  </div>
                </div>

              </>
            )}

            {/* 4.2 Ballast Quantity */}
            {(details.operation_type === "ballasting" || details.operation_type === "both") && (
              <div>
                <label>4.2 Ballast Quantity (mÂ³) *</label>
                <input
                  type="number"
                  step="0.01"
                  value={details.ballast_qty || ""}
                  onChange={(e) => handleChange('ballast_qty', parseFloat(e.target.value))}
                  placeholder="e.g., 50"
                  style={{ borderColor: errors.ballast_qty ? 'red' : '#ccc', width: "150px" }}
                />
                {errors.ballast_qty && (
                  <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                    {errors.ballast_qty}
                  </span>
                )}
              </div>
            )}
          </div>

        );

      case 'B':
        return (

          <div className="card" style={{ width: '920px' }}>
            {dateInputSection}
            {/* 5. Tank ID(s) */}
            <div>
              <label>5. Tank ID(s) *</label>
              <select
                value={details.tank_ids || ""}
                onChange={(e) => handleChange('tank_ids', e.target.value)}
                style={{ width: '100%', padding: '8px' }}
              >
                <option value="">Select Tank</option>
                {availableTanks

                  .map(tank => (
                    <option key={tank.id} value={tank.tank_name}>
                      {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                    </option>
                  ))
                }
              </select>
              {errors.tank_ids && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.tank_ids}
                </span>
              )}
            </div>

            {/* 6. Position at Start */}
            <div>
              <label>6. Position at Start *</label>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto auto auto auto auto auto",
                  gap: "8px",
                  marginTop: "4px",
                  alignItems: "center",
                }}
              >
                {/* Lat Deg */}
                <div>
                  <label>Lat Deg</label>
                  <select
                    value={details.pos_start_lat_deg || ""}
                    onChange={(e) =>
                      handleChange(
                        "pos_start_lat_deg",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px" }}
                  >
                    <option value="">Â°</option>
                    {[...Array(91)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lat Min */}
                <div>
                  <label>Min</label>
                  <select
                    value={details.pos_start_lat_min || ""}
                    onChange={(e) =>
                      handleChange(
                        "pos_start_lat_min",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px" }}
                  >
                    <option value="">â€²</option>
                    {[...Array(60)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lat Dir */}
                <div>
                  <label>Dir</label>
                  <select
                    value={details.pos_start_lat_dir || ""}
                    onChange={(e) => handleChange("pos_start_lat_dir", e.target.value)}
                    style={{ width: "60px" }}
                  >
                    <option value="">N/S</option>
                    <option value="N">N</option>
                    <option value="S">S</option>
                  </select>
                </div>

                {/* Lon Deg */}
                <div>
                  <label>Lon Deg</label>
                  <select
                    value={details.pos_start_lon_deg || ""}
                    onChange={(e) =>
                      handleChange(
                        "pos_start_lon_deg",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px" }}
                  >
                    <option value="">Â°</option>
                    {[...Array(181)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lon Min */}
                <div>
                  <label>Min</label>
                  <select
                    value={details.pos_start_lon_min || ""}
                    onChange={(e) =>
                      handleChange(
                        "pos_start_lon_min",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px" }}
                  >
                    <option value="">â€²</option>
                    {[...Array(60)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lon Dir */}
                <div>
                  <label>Dir</label>
                  <select
                    value={details.pos_start_lon_dir || ""}
                    onChange={(e) => handleChange("pos_start_lon_dir", e.target.value)}
                    style={{ width: "60px" }}
                  >
                    <option value="">E/W</option>
                    <option value="E">E</option>
                    <option value="W">W</option>
                  </select>
                </div>
              </div>
              {errors.pos_start && (
                <span style={{ color: "red", fontSize: "12px", display: "block" }}>
                  {errors.pos_start}
                </span>
              )}
            </div>

            {/* 7. Position at End */}
            <div style={{ marginTop: "16px" }}>
              <label>7. Position at End *</label>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto auto auto auto auto auto",
                  gap: "8px",
                  marginTop: "4px",
                  alignItems: "center",
                }}
              >
                {/* Lat Deg */}
                <div>
                  <label>Lat Deg</label>
                  <select
                    value={details.pos_end_lat_deg || ""}
                    onChange={(e) =>
                      handleChange(
                        "pos_end_lat_deg",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px" }}
                  >
                    <option value="">Â°</option>
                    {[...Array(91)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lat Min */}
                <div>
                  <label>Min</label>
                  <select
                    value={details.pos_end_lat_min || ""}
                    onChange={(e) =>
                      handleChange(
                        "pos_end_lat_min",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px" }}
                  >
                    <option value="">â€²</option>
                    {[...Array(60)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lat Dir */}
                <div>
                  <label>Dir</label>
                  <select
                    value={details.pos_end_lat_dir || ""}
                    onChange={(e) => handleChange("pos_end_lat_dir", e.target.value)}
                    style={{ width: "60px" }}
                  >
                    <option value="">N/S</option>
                    <option value="N">N</option>
                    <option value="S">S</option>
                  </select>
                </div>

                {/* Lon Deg */}
                <div>
                  <label>Lon Deg</label>
                  <select
                    value={details.pos_end_lon_deg || ""}
                    onChange={(e) =>
                      handleChange(
                        "pos_end_lon_deg",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px" }}
                  >
                    <option value="">Â°</option>
                    {[...Array(181)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lon Min */}
                <div>
                  <label>Min</label>
                  <select
                    value={details.pos_end_lon_min || ""}
                    onChange={(e) =>
                      handleChange(
                        "pos_end_lon_min",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px" }}
                  >
                    <option value="">â€²</option>
                    {[...Array(60)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lon Dir */}
                <div>
                  <label>Dir</label>
                  <select
                    value={details.pos_end_lon_dir || ""}
                    onChange={(e) => handleChange("pos_end_lon_dir", e.target.value)}
                    style={{ width: "60px" }}
                  >
                    <option value="">E/W</option>
                    <option value="E">E</option>
                    <option value="W">W</option>
                  </select>
                </div>
              </div>
              {errors.pos_end && (
                <span style={{ color: "red", fontSize: "12px", display: "block" }}>
                  {errors.pos_end}
                </span>
              )}
            </div>


            {/* 8. Ship's Speed(s) */}
            {/* <div>
              <label>8. Ship's Speed(s) During Discharge</label>
              <input
                type="text"
                value={details.ship_speeds || ''}
                onChange={(e) => handleChange('ship_speeds', e.target.value)}
                placeholder="e.g., 12 knots"
              />
              {errors.ship_speeds && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.ship_speeds}
                </span>
              )}
            </div> */}



            {/* 9.1 Discharged via 15 ppm Equipment */}
            {/* <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <label>9.1 Discharged via 15 ppm Equipment</label>
              <input
                type="checkbox"
                checked={details.method === '15ppm'}
                onChange={() => handleChange('method', details.method === '15ppm' ? '' : '15ppm')}
                style={{ width: "18px", height: "18px", cursor: "pointer" }}
              />
            </div> */}

            {/* 9.2 To Reception Facility */}
            {/* <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <label>9.2 Discharged To Reception Facility</label>
              <input
                type="checkbox"
                value={details.method === 'reception'}
                onChange={() => handleChange('method', details.method === 'reception' ? '' : 'reception')}
                style={{ width: "200px" }}
              />
              
                <input
                  type="text"
                  value={details.reception_port || ''}
                  onChange={(e) => handleChange('reception_port', e.target.value)}
                  placeholder="e.g., ROTTERDAM"

                />
              
              {errors.reception_port && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.reception_port}
                </span>
              )}
            </div> */}




            {/* 9.2 To Reception Facility */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                marginBottom: "8px",
                marginTop: '2px'
              }}
            >
              <label>9.2 Discharged To Reception Facility *</label>
              <input
                type="text"
                value={details.reception_port || ""}
                onChange={(e) => {
                  handleChange("reception_port", e.target.value);
                  handleChange("method", "reception"); // âœ… always set method
                }}
                placeholder="Enter Port Name"
                style={{ width: '200px', marginTop: '7px', borderColor: errors.reception_port ? "red" : "#ccc" }}
                required
              />
            </div>

            {/* Validation error */}
            {errors.reception_port && (
              <span style={{ color: "red", fontSize: "12px", display: "block" }}>
                {errors.reception_port}
              </span>
            )}


            {/* 10. Quantity Discharged (mÂ³) */}
            <div>
              <label>10. Quantity Discharged (mÂ³)</label>
              <input
                type="number"
                step="0.01"
                value={details.quantity_discharged_m3 || ''}
                onChange={(e) => {
                  const value = e.target.value === '' ? '' : parseFloat(e.target.value);
                  handleChange('quantity_discharged_m3', value);
                }}
                placeholder="Enter discharge qauntity"
                style={{
                  borderColor: errors.quantity_discharged_m3 ? 'red' : '#ccc'
                }}
              />
              {errors.quantity_discharged_m3 && (
                <span style={{
                  color: 'red',
                  fontSize: '12px',
                  display: 'block',
                  marginTop: '4px'
                }}>
                  {errors.quantity_discharged_m3}
                </span>
              )}
            </div>
          </div>

        );


      case 'C':
        return (

          <div className="card" style={{ width: '920px' }}>
            {dateInputSection}

            {/* Step 1: Select Operation Type */}
            <div style={{ marginBottom: '20px', padding: '12px', border: '1px solid #ddd', borderRadius: '6px' }}>
              <label><strong>Select Operation Type:</strong></label>
              <div>
                <label style={{ display: 'block', marginTop: '8px' }}>
                  <input
                    type="radio"
                    name="c_operation_type"
                    checked={details.operation_mode === 'weekly'}
                    onChange={() => handleChange('operation_mode', 'weekly')}
                    style={{ width: "18px", height: "18px", cursor: "pointer" }}
                  />
                  Weekly Update
                </label>

                <label style={{ display: 'block', marginTop: '8px' }}>
                  <input
                    type="radio"
                    name="c_operation_type"
                    checked={details.operation_mode === 'manual'}
                    onChange={() => handleChange('operation_mode', 'manual')}
                    style={{ width: "18px", height: "18px", cursor: "pointer" }}
                  />
                  Manual Collection
                </label>

                <label style={{ display: 'block', marginTop: '8px' }}>
                  <input
                    type="radio"
                    name="c_operation_type"
                    checked={details.operation_mode === 'transfer'}
                    onChange={() => handleChange('operation_mode', 'transfer')}
                    style={{ width: "18px", height: "18px", cursor: "pointer" }}
                  />
                  Transfer/Disposal of Sludge
                </label>
              </div>
            </div>

            {/* Conditionally Render Based on Mode */}
            {details.operation_mode === 'weekly' && (
              <>
                {/* 11.1 Sludge Tank */}
                <div>
                  <label>11.1 Identity of tank(s) *</label>
                  <select
                    value={details.sludge_tank_id || ""}
                    onChange={(e) => {
                      const selectedTank = availableTanks.find(
                        tank => tank.tank_name === e.target.value
                      );
                      // update both tank_id and capacity when user selects
                      handleChange('sludge_tank_id', e.target.value);
                      if (selectedTank) {
                        handleChange('sludge_tank_capacity', selectedTank.capacity);
                      }
                    }}
                    style={{ width: '100%', padding: '8px', borderColor: errors.sludge_tank_id ? 'red' : '#ccc' }}
                  >
                    <option value="">Select Sludge Tank</option>
                    {availableTanks
                      .map(tank => (
                        <option key={tank.id} value={tank.tank_name}>
                          {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                        </option>
                      ))
                    }
                  </select>
                  {errors.sludge_tank_id && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.sludge_tank_id}
                    </span>
                  )}
                </div>

                {/* 11.2 Total Capacity */}
                <div>
                  <label>11.2 Total Capacity (mÂ³) *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={details.sludge_tank_capacity || ""}
                    onChange={(e) => handleChange('sludge_tank_capacity', parseFloat(e.target.value))}
                    placeholder="Select the tank first Quantity will be autofilled "
                    style={{ width: '100%', borderColor: errors.sludge_tank_capacity ? 'red' : '#ccc' }}
                    disabled={true}
                  />
                  {errors.sludge_tank_capacity && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.sludge_tank_capacity}
                    </span>
                  )}
                </div>

                {/* 11.3 Sludge Before Collection */}
                <div>
                  <label>11.3 total quantity of retention (mÂ³) *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={details.sludge_before ?? ""}
                    onChange={(e) => handleChange('sludge_before', parseFloat(e.target.value))}
                    placeholder="Enter Retained Quantity"
                    style={{ width: '100%', borderColor: errors.sludge_before ? 'red' : '#ccc' }}
                  />
                  {errors.sludge_before && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.sludge_before}
                    </span>
                  )}
                </div>
              </>
            )}

            {details.operation_mode === 'manual' && (
              <>
                {/* 11.1 â€“ 11.3 (Same as Weekly) */}
                <div>
                  <label>11.1 Identity of tank(s)*</label>
                  <select
                    value={details.sludge_tank_id || ""}
                    onChange={(e) => {
                      const selectedTank = availableTanks.find(
                        tank => tank.tank_name === e.target.value
                      );
                      // update both tank_id and capacity when user selects
                      handleChange('sludge_tank_id', e.target.value);
                      if (selectedTank) {
                        handleChange('sludge_tank_capacity', selectedTank.capacity);
                      }
                    }}
                    style={{ width: '100%', padding: '8px', borderColor: errors.sludge_tank_id ? 'red' : '#ccc' }}
                  >
                    <option value="">Select Sludge Tank</option>
                    {availableTanks
                      .map(tank => (
                        <option key={tank.id} value={tank.tank_name}>
                          {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                        </option>
                      ))
                    }
                  </select>
                  {errors.sludge_tank_id && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.sludge_tank_id}
                    </span>
                  )}
                </div>

                <div>
                  <label>11.2 Total Capacity (mÂ³) *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={details.sludge_tank_capacity || ""}
                    onChange={(e) => handleChange('sludge_tank_capacity', parseFloat(e.target.value))}
                    placeholder="Select the tank first Quantity will be autofilled"
                    style={{ width: '100%', borderColor: errors.sludge_tank_capacity ? 'red' : '#ccc' }}
                    disabled={true}
                  />
                  {errors.sludge_tank_capacity && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.sludge_tank_capacity}
                    </span>
                  )}
                </div>

                <div>
                  <label>11.3 Total quantity of retention (mÂ³) *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={details.sludge_before ?? ""}
                    onChange={(e) => handleChange('sludge_before', parseFloat(e.target.value))}
                    placeholder="Enter Retained Quantity"
                    style={{ width: '100%', borderColor: errors.sludge_before ? 'red' : '#ccc' }}
                  />
                  {errors.sludge_before && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.sludge_before}
                    </span>
                  )}
                </div>

                {/* 11.4 Manual Collection */}
                <div>
                  <label>11.4 Manual Collection (mÂ³) *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={details.manual_collection_m3 || ""}
                    onChange={(e) => handleChange('manual_collection_m3', parseFloat(e.target.value))}
                    placeholder="Quantity of Manual Collection"
                    style={{ width: '100%', borderColor: errors.manual_collection_m3 ? 'red' : '#ccc' }}
                  />
                  <label>11.4 Source Tank *</label>
                  {/* Updated Select for Source Tank with "Other" option */}
                  <select
                    value={details.collection_source || ""}
                    onChange={(e) => {
                      const selectedValue = e.target.value;
                      // If "Other" is selected, clear the specific tank field
                      // and potentially set a flag or clear the manual_collection_m3 if needed
                      // For now, just update the collection_source field
                      handleChange('collection_source', selectedValue);

                      // Optional: Clear the manual collection amount if switching away from a specific tank
                      // and the user hasn't manually entered a value yet, or clear it when selecting "Other"
                      // if that's the desired UX. This part depends on specific requirements.
                      // Example: if (selectedValue === 'OTHER' && !details.manual_collection_m3) { handleChange('manual_collection_m3', ''); }
                    }}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderColor: errors.collection_source ? 'red' : '#ccc',
                      borderRadius: '4px',
                      marginTop: '4px'
                    }}
                  >
                    <option value="">Select Source Tank</option>
                    {availableTanks
                      .map(tank => (
                        <option key={tank.id} value={tank.tank_name}>
                          {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                        </option>
                      ))
                    }
                    {/* Add the "Other" option */}
                    <option value="OTHER">Other (Specify Manually)</option>
                  </select>
                  {errors.collection_source && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.collection_source}
                    </span>
                  )}
                  {/* Conditional Free-Text Input for "Other" */}
                  {details.collection_source === 'OTHER' && (
                    <div style={{ marginTop: '8px' }}>
                      <label htmlFor="custom-collection-source">Specify Source Tank:</label>
                      <input
                        type="text"
                        id="custom-collection-source" // Unique ID for accessibility
                        value={details.custom_collection_source || ""} // Use a new state field for the custom input
                        onChange={(e) => handleChange('custom_collection_source', e.target.value)} // Update state with custom value
                        placeholder="Enter tank name/identifier"
                        style={{
                          width: '100%',
                          padding: '8px',
                          border: '1px solid #ccc',
                          borderRadius: '4px',
                          marginTop: '2px'
                        }}
                      />
                      {/* Optional: Add error display for custom input if needed */}
                      {/* {errors.custom_collection_source && (
                         <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                           {errors.custom_collection_source}
                         </span>
                       )} */}
                    </div>
                  )}
                </div>
              </>
            )}

            {details.operation_mode === 'transfer' && (
              <>
                <hr style={{ margin: '16px 0', borderColor: '#ccc' }} />

                {/* 12.1 To Reception Facility */}
                <div>
                  <label>
                    <input
                      type="radio"
                      checked={details.disposal_method === 'reception'}
                      onChange={() => handleChange('disposal_method', 'reception')}
                      style={{ width: "18px", height: "18px", cursor: "pointer" }}
                    />
                    12.1 To Reception Facility
                  </label>
                  {details.disposal_method === 'reception' && (
                    <>
                      <input
                        type="number"
                        step="0.01"
                        value={details.quantity_m3 || ""}
                        onChange={(e) => handleChange('quantity_m3', parseFloat(e.target.value))}
                        placeholder="Disposal Quantity"
                      />

                      <select
                        value={details.source_tank || ""}
                        onChange={(e) => handleChange('source_tank', e.target.value)}
                        style={{
                          width: '100%',
                          padding: '8px',
                          borderColor: errors.source_tank ? 'red' : '#ccc',
                          borderRadius: '4px',
                          marginTop: '4px'
                        }}
                      >
                        <option value="">Select Source Tank</option>
                        {availableTanks

                          .map(tank => (
                            <option key={tank.id} value={tank.tank_name}>
                              {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                            </option>
                          ))
                        }
                      </select>
                      {errors.source_tank && (
                        <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                          {errors.source_tank}
                        </span>
                      )}
                      <input
                        type="number"
                        step="0.01"
                        value={details.retained_quantity || ""}
                        onChange={(E) => handleChange('retained_quantity', parseFloat(E.target.value))}
                        placeholder="Retained quantity"
                      />
                      <input
                        type="text"
                        value={details.reception_vessel || ""}
                        onChange={(E) => handleChange('reception_vessel', E.target.value)}
                        placeholder="Reception vessel"
                      />
                      <input
                        type="text"
                        value={details.reception_port || ""}
                        onChange={(E) => handleChange('reception_port', E.target.value)}
                        placeholder="Port Name"
                      />
                      <input
                        type="text"
                        value={details.reception_receipt_no || ""}
                        onChange={(E) => handleChange('reception_receipt_no', E.target.value)}
                        placeholder="Reciept no/ Certificate no. "
                      />
                    </>

                  )}
                </div>

                {/* 12.2 Transfer to Another Tank */}
                <div>
                  <label>
                    <input
                      type="radio"
                      checked={details.disposal_method === 'transfer'}
                      onChange={() => handleChange('disposal_method', 'transfer')}
                      style={{ width: "18px", height: "18px", cursor: "pointer" }}
                    />
                    12.2 Transfer to Another Tank
                  </label>

                  {details.disposal_method === 'transfer' && (
                    <>
                      <label>Quantity Transferred (mÂ³) *</label>
                      <input
                        type="number"
                        step="0.01"
                        value={details.disposal_quantity_m3 || ""}
                        onChange={(e) => handleChange('disposal_quantity_m3', parseFloat(e.target.value))}
                        placeholder="e.g., 1"
                        style={{ width: '100%', borderColor: errors.disposal_quantity_m3 ? 'red' : '#ccc' }}
                      />
                      {errors.disposal_quantity_m3 && (
                        <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                          {errors.disposal_quantity_m3}
                        </span>
                      )}

                      {/* Transferred From Tank */}
                      <label>Transferred From Tank *</label>
                      <select
                        value={details.transferred_from_tank_ids || ""}
                        onChange={(e) => handleChange('transferred_from_tank_ids', e.target.value)}
                        style={{
                          width: '100%',
                          padding: '8px',
                          borderColor: errors.transferred_from_tank_ids ? 'red' : '#ccc',
                          borderRadius: '4px'
                        }}
                      >
                        <option value="">Select Source Tank</option>
                        {availableTanks

                          .map(tank => (
                            <option key={tank.id} value={tank.tank_name}>
                              {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                            </option>
                          ))
                        }
                      </select>
                      {errors.transferred_from_tank_ids && (
                        <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                          {errors.transferred_from_tank_ids}
                        </span>
                      )}

                      <label>Retained Quantity (mÂ³)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={details.retained_quantity || ""}
                        onChange={(e) => handleChange('retained_quantity', parseFloat(e.target.value))}
                        placeholder="e.g., 3"
                        style={{ width: '100%' }}
                      />

                      {/* Transferred To Tank */}
                      <label>Transferred To Tank *</label>
                      <select
                        value={details.transferred_to_Tank_ids || ""}
                        onChange={(e) => handleChange('transferred_to_Tank_ids', e.target.value)}
                        style={{
                          width: '100%',
                          padding: '8px',
                          borderColor: errors.transferred_to_Tank_ids ? 'red' : '#ccc',
                          borderRadius: '4px'
                        }}
                      >
                        <option value="">Select Destination Tank</option>
                        {availableTanks

                          .map(tank => (
                            <option key={tank.id} value={tank.tank_name}>
                              {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                            </option>
                          ))
                        }
                      </select>
                      {errors.transferred_to_Tank_ids && (
                        <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                          {errors.transferred_to_Tank_ids}
                        </span>
                      )}
                    </>
                  )}
                </div>
                {/* 12.3 Incineration */}
                <div>
                  <label>
                    <input
                      type="radio"
                      checked={details.disposal_method === 'incineration'}
                      onChange={() => handleChange('disposal_method', 'incineration')}
                      style={{ width: "18px", height: "18px", cursor: "pointer" }}
                    />
                    12.3 Incineration
                  </label>
                  {details.disposal_method === 'incineration' && (
                    <>
                      <input
                        type="number"
                        step="0.01"
                        value={details.quantity_m3 || ""}
                        onChange={(e) => handleChange('quantity_m3', parseFloat(e.target.value))}
                        placeholder="Incinerated Quantity"
                      />
                      {/* Source Tank Dropdown */}
                      <label>Source Tank *</label>
                      <select
                        value={details.source_tank || ""}
                        onChange={(e) => handleChange('source_tank', e.target.value)}
                        style={{
                          width: '100%',
                          padding: '8px',
                          borderColor: errors.source_tank ? 'red' : '#ccc',
                          borderRadius: '4px'
                        }}
                      >
                        <option value="">Select Source Tank</option>
                        {availableTanks
                          .map(tank => (
                            <option key={tank.id} value={tank.tank_name}>
                              {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                            </option>
                          ))
                        }
                      </select>
                      {errors.source_tank && (
                        <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                          {errors.source_tank}
                        </span>
                      )}

                      <input
                        type="number"
                        step="0.01"
                        value={details.retained_quantity || ""}
                        onChange={(e) => handleChange('retained_quantity', parseFloat(e.target.value))}
                        placeholder="Retained Quantity"
                      />
                      <input
                        type="number"
                        step="0.01"
                        value={details.incineration_duration_hours || ""}
                        onChange={(e) => handleChange('incineration_duration_hours', parseFloat(e.target.value))}
                        placeholder="Duration (hours)"
                      />
                    </>

                  )}
                </div>

                {/* 12.4 Other Disposal */}
                <div>
                  <label>
                    <input
                      type="radio"
                      checked={details.disposal_method === 'other'}
                      onChange={() => handleChange('disposal_method', 'other')}
                      style={{ width: "18px", height: "18px", cursor: "pointer" }}
                    />
                    12.4 Other Disposal(Evaporation)
                  </label>
                  {details.disposal_method === 'other' && (
                    <textarea
                      rows="2"
                      value={details.other_disposal_details || ""}
                      onChange={(e) => handleChange('other_disposal_details', e.target.value)}
                      placeholder="explain the disposal method"
                      style={{ width: '100%', marginLeft: '24px', marginTop: '4px' }}
                    />
                  )}
                </div>
              </>
            )}
          </div>

        );


      case 'D':
        return (

          <div className="card" style={{ width: '920px' }}>
            {dateInputSection}
            <h4>Bilge Water Disposal (Code D)</h4>

            {/* 13. Source Tank Info */}
            <div>
              <label>13. Source Tank *</label>
              <select
                value={details.source_tank_id || ""}
                onChange={(e) => {
                  const tank = availableTanks.find(t => t.id === e.target.value);
                  handleChange("source_tank_id", e.target.value);
                  handleChange("source_tank_capacity", tank?.capacity || 0);

                  // Reset retained = full capacity, discharged = 0
                  handleChange("source_tank_retained_m3", tank?.capacity || 0);
                  handleChange("quantity_discharged_m3", 0);
                }}
                style={{ width: "100%", borderColor: errors.source_tank_id ? "red" : "#ccc" }}
              >

                <option value="">Select Bilge Holding Tank</option>
                {availableTanks
                  .map(tank => (
                    <option key={tank.id} value={tank.id}>
                      {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to}, {tank.capacity} mÂ³)
                    </option>
                  ))
                }
              </select>
              {errors.source_tank_id && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.source_tank_id}
                </span>
              )}
            </div>

            {/* 13.2 Retained Quantity */}
            <div>
              <label>13. Retained in Source Tank (mÂ³) *</label>
              <input
                type="number"
                step="0.01"
                value={details.source_tank_retained_m3 || ""}
                onChange={(e) => handleChange('source_tank_retained_m3', parseFloat(e.target.value))}
                placeholder="e.g., 5"
                style={{ width: '100%', borderColor: errors.source_tank_retained_m3 ? 'red' : '#ccc' }}
              />
              {errors.source_tank_retained_m3 && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.source_tank_retained_m3}
                </span>
              )}
            </div>

            <input
              type="number"
              step="0.01"
              value={details.quantity_discharged_m3 || ""}
              onChange={(e) => {
                const discharged = parseFloat(e.target.value) || 0;
                const tank = availableTanks.find(t => t.id === details.source_tank_id);
                const capacity = tank?.capacity || 0;

                // Auto-calc retained = capacity - discharged
                const retained = capacity - discharged >= 0 ? capacity - discharged : 0;

                handleChange("quantity_discharged_m3", discharged);
                handleChange("source_tank_retained_m3", retained);
              }}
              placeholder="Enter Disposal Quantity"
              style={{ width: "100%", borderColor: errors.quantity_discharged_m3 ? "red" : "#ccc" }}
            />

            {/* 14. Start & Stop Time */}
            <div>
              <label>14. Start Time *</label>
              <input
                type="time"
                value={details.start_time || ""}
                onChange={(e) => handleChange('start_time', e.target.value)}
                style={{ width: "150px", borderColor: errors.start_time ? 'red' : '#ccc' }}
              />
              {errors.start_time && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.start_time}
                </span>
              )}
            </div>

            <div>
              <label>14. Stop Time *</label>
              <input
                type="time"
                value={details.stop_time || ""}
                onChange={(e) => handleChange('stop_time', e.target.value)}
                style={{ width: "150px", borderColor: errors.stop_time ? 'red' : '#ccc' }}
              />
              {errors.stop_time && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.stop_time}
                </span>
              )}
            </div>



            {/* 15. Method of Discharge */}
            <div>
              <label>
                <input
                  type="radio"
                  checked={details.method === '15ppm'}
                  onChange={() => handleChange('method', '15ppm')}
                  style={{ width: "18px", height: "18px", cursor: "pointer" }}
                />
                15.1 Through 15 ppm Equipment
              </label>
              {details.method === '15ppm' && (
                <>
                  {/* Position at Start */}
                  <div style={{ marginLeft: '24px', marginTop: '12px' }}>
                    <label><strong>Position at Start *</strong></label>

                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'auto auto auto auto auto auto',
                      gap: '8px',
                      marginTop: '4px',
                      alignItems: 'center'
                    }}>
                      {/* Latitude Deg */}
                      <div>
                        <label>Lat Deg</label>
                        <select
                          value={details.ppm_start_lat_deg || ""}
                          onChange={(e) => handleChange('ppm_start_lat_deg', parseInt(e.target.value))}
                          style={{ width: '70px' }}
                        >
                          <option value="">Â°</option>
                          {[...Array(91)].map((_, i) => (
                            <option key={i} value={i}>{i}</option>
                          ))}
                        </select>
                      </div>

                      {/* Latitude Min */}
                      <div>
                        <label>Min</label>
                        <select
                          value={details.ppm_start_lat_min || ""}
                          onChange={(e) => handleChange('ppm_start_lat_min', parseInt(e.target.value))}
                          style={{ width: '70px' }}
                        >
                          <option value="">â€²</option>
                          {[...Array(60)].map((_, i) => (
                            <option key={i} value={i}>{i}</option>
                          ))}
                        </select>
                      </div>

                      {/* Latitude Dir */}
                      <div>
                        <label>Dir</label>
                        <select
                          value={details.ppm_start_lat_dir || ""}
                          onChange={(e) => handleChange('ppm_start_lat_dir', e.target.value)}
                          style={{ width: '60px' }}
                        >
                          <option value="">N/S</option>
                          <option value="N">N</option>
                          <option value="S">S</option>
                        </select>
                      </div>

                      {/* Longitude Deg */}
                      <div>
                        <label>Lon Deg</label>
                        <select
                          value={details.ppm_start_lon_deg || ""}
                          onChange={(e) => handleChange('ppm_start_lon_deg', parseInt(e.target.value))}
                          style={{ width: '70px' }}
                        >
                          <option value="">Â°</option>
                          {[...Array(181)].map((_, i) => (
                            <option key={i} value={i}>{i}</option>
                          ))}
                        </select>
                      </div>

                      {/* Longitude Min */}
                      <div>
                        <label>Min</label>
                        <select
                          value={details.ppm_start_lon_min || ""}
                          onChange={(e) => handleChange('ppm_start_lon_min', parseInt(e.target.value))}
                          style={{ width: '70px' }}
                        >
                          <option value="">â€²</option>
                          {[...Array(60)].map((_, i) => (
                            <option key={i} value={i}>{i}</option>
                          ))}
                        </select>
                      </div>

                      {/* Longitude Dir */}
                      <div>
                        <label>Dir</label>
                        <select
                          value={details.ppm_start_lon_dir || ""}
                          onChange={(e) => handleChange('ppm_start_lon_dir', e.target.value)}
                          style={{ width: '60px' }}
                        >
                          <option value="">E/W</option>
                          <option value="E">E</option>
                          <option value="W">W</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Position at Stop */}
                  <div style={{ marginLeft: '24px', marginTop: '12px' }}>
                    <label><strong>Position at Stop *</strong></label>

                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'auto auto auto auto auto auto',
                      gap: '8px',
                      marginTop: '4px',
                      alignItems: 'center'
                    }}>
                      {/* Lat Deg */}
                      <div>
                        <label>Lat Deg</label>
                        <select
                          value={details.ppm_end_lat_deg || ""}
                          onChange={(e) => handleChange('ppm_end_lat_deg', parseInt(e.target.value))}
                          style={{ width: '70px' }}
                        >
                          <option value="">Â°</option>
                          {[...Array(91)].map((_, i) => (
                            <option key={i} value={i}>{i}</option>
                          ))}
                        </select>
                      </div>

                      {/* Lat Min */}
                      <div>
                        <label>Min</label>
                        <select
                          value={details.ppm_end_lat_min || ""}
                          onChange={(e) => handleChange('ppm_end_lat_min', parseInt(e.target.value))}
                          style={{ width: '70px' }}
                        >
                          <option value="">â€²</option>
                          {[...Array(60)].map((_, i) => (
                            <option key={i} value={i}>{i}</option>
                          ))}
                        </select>
                      </div>

                      {/* Lat Dir */}
                      <div>
                        <label>Dir</label>
                        <select
                          value={details.ppm_end_lat_dir || ""}
                          onChange={(e) => handleChange('ppm_end_lat_dir', e.target.value)}
                          style={{ width: '60px' }}
                        >
                          <option value="">N/S</option>
                          <option value="N">N</option>
                          <option value="S">S</option>
                        </select>
                      </div>

                      {/* Lon Deg */}
                      <div>
                        <label>Lon Deg</label>
                        <select
                          value={details.ppm_end_lon_deg || ""}
                          onChange={(e) => handleChange('ppm_end_lon_deg', parseInt(e.target.value))}
                          style={{ width: '70px' }}
                        >
                          <option value="">Â°</option>
                          {[...Array(181)].map((_, i) => (
                            <option key={i} value={i}>{i}</option>
                          ))}
                        </select>
                      </div>

                      {/* Lon Min */}
                      <div>
                        <label>Min</label>
                        <select
                          value={details.ppm_end_lon_min || ""}
                          onChange={(e) => handleChange('ppm_end_lon_min', parseInt(e.target.value))}
                          style={{ width: '70px' }}
                        >
                          <option value="">â€²</option>
                          {[...Array(60)].map((_, i) => (
                            <option key={i} value={i}>{i}</option>
                          ))}
                        </select>
                      </div>

                      {/* Lon Dir */}
                      <div>
                        <label>Dir</label>
                        <select
                          value={details.ppm_end_lon_dir || ""}
                          onChange={(e) => handleChange('ppm_end_lon_dir', e.target.value)}
                          style={{ width: '60px' }}
                        >
                          <option value="">E/W</option>
                          <option value="E">E</option>
                          <option value="W">W</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* âœ… NEW: Start & Stop Time with UTC */}
                  <div style={{ marginLeft: '24px', marginTop: '16px', display: 'grid', gap: '12px' }}>

                    {/* Start Time */}
                    <div>
                      <label>14. Start Time (UTC) *</label>
                      <input
                        type="time"
                        value={details.ppm_start_time || ""}
                        onChange={(e) => handleChange('ppm_start_time', e.target.value)}
                        style={{
                          width: '150px',
                          padding: '6px',
                          border: '1px solid #ccc',
                          borderRadius: '4px'
                        }}
                        required
                      />
                    </div>

                    {/* Stop Time */}
                    <div>
                      <label>14. Stop Time (UTC) *</label>
                      <input
                        type="time"
                        value={details.ppm_stop_time || ""}
                        onChange={(e) => handleChange('ppm_stop_time', e.target.value)}
                        style={{
                          width: '150px',
                          padding: '6px',
                          border: '1px solid #ccc',
                          borderRadius: '4px'
                        }}
                        required
                      />
                    </div>
                  </div>

                  {/* âœ… Validation Message */}
                  {details.ppm_start_time && details.ppm_stop_time && (
                    new Date(`2000-01-01T${details.ppm_stop_time}`) < new Date(`2000-01-01T${details.ppm_start_time}`) && (
                      <span style={{ color: 'red', fontSize: '12px', marginLeft: '24px', display: 'block' }}>
                        âŒ Stop time cannot be before start time.
                      </span>
                    )
                  )}

                </>

              )}
            </div>

            <div>
              <label>
                <input
                  type="radio"
                  checked={details.method === 'reception'}
                  onChange={() => handleChange('method', 'reception')}
                  style={{ width: "18px", height: "18px", cursor: "pointer" }}
                />
                15.2 To Reception Facility
              </label>
              {details.method === 'reception' && (
                <>
                  <input
                    type="text"
                    value={details.reception_port || ""}
                    onChange={(e) => handleChange('reception_port', e.target.value.toUpperCase())}
                    placeholder="Port Name"
                    style={{ marginLeft: '24px', width: 'calc(100% - 24px)' }}
                  />
                  <input
                    type="text"
                    value={details.reception_receipt_no || ""}
                    onChange={(e) => handleChange('reception_receipt_no', e.target.value)}
                    placeholder="Receipt No."
                    style={{ marginLeft: '24px', width: 'calc(100% - 24px)' }}
                  />
                </>
              )}
            </div>

            <div>
              <label>
                <input
                  type="radio"
                  checked={details.method === 'holding'}
                  onChange={() => handleChange('method', 'holding')}
                  style={{ width: "18px", height: "18px", cursor: "pointer" }}
                />
                15.3 To Bilge Holding Tank
              </label>
              {details.method === 'holding' && (
                <>
                  <div>
                    <label>Tank Name *</label>
                    <select
                      value={details.holding_tank_ids || ""}
                      onChange={(e) => handleChange('holding_tank_ids', e.target.value)}
                      style={{ width: '100%', borderColor: errors.holding_tank_ids ? 'red' : '#ccc' }}
                    >
                      <option value="">Select Tank</option>
                      {availableTanks
                        .map(tank => (
                          <option key={tank.id} value={tank.tank_name}>
                            {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to})
                          </option>
                        ))
                      }
                    </select>
                    {errors.holding_tank_ids && (
                      <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                        {errors.holding_tank_ids}
                      </span>
                    )}
                  </div>

                  {/* Retained Quantity */}
                  <div>
                    <label>Retained Quantity (mÂ³) *</label>
                    <input
                      type="number"
                      step="0.01"
                      value={details.holding_tank_retained_m3 || ""}
                      onChange={(e) => handleChange('holding_tank_retained_m3', parseFloat(e.target.value))}
                      placeholder="Enter Retained Quantity"
                      style={{ width: '100%', borderColor: errors.holding_tank_retained_m3 ? 'red' : '#ccc' }}
                    />
                    {errors.holding_tank_retained_m3 && (
                      <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                        {errors.holding_tank_retained_m3}
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

        );


      case 'E':
        return (
          <Panel>
            <div className="card" style={{ width: '920px' }}>
              <div>
                <label>16.1 Auto Start Time & Position</label>
                <input
                  type="text"
                  value={details.auto_start_time || ''}
                  onChange={(e) => handleChange('auto_start_time', e.target.value)}
                  placeholder="e.g., 09:00 HRS"
                />
                <input
                  type="text"
                  value={details.auto_start_pos || ''}
                  onChange={(e) => handleChange('auto_start_pos', e.target.value)}
                  placeholder="Position"
                />
              </div>
              <div>
                <label>17. To Holding Tank Start</label>
                <input
                  type="text"
                  value={details.auto_to_holding_start_time || ''}
                  onChange={(e) => handleChange('auto_to_holding_start_time', e.target.value)}
                  placeholder="e.g., 10:30 HRS"
                />
                <input
                  type="text"
                  value={details.holding_tank_id || ''}
                  onChange={(e) => handleChange('holding_tank_id', e.target.value)}
                  placeholder="Tank ID"
                />
              </div>
              <div>
                <label>18. Manual Operation Time</label>
                <input
                  type="text"
                  value={details.manual_operation_time || ''}
                  onChange={(e) => handleChange('manual_operation_time', e.target.value)}
                  placeholder="e.g., 1.5 HRS"
                />
              </div>
            </div>
          </Panel>
        );


      case 'F':
        return (

          <div className="card" style={{ width: '920px' }}>
            {dateInputSection}
            <h4>Condition of Oil Filtering Equipment (Code F)</h4>

            {/* Step 1: Select Operation Type */}
            <div style={{ marginBottom: '20px', padding: '12px', border: '1px solid #ddd', borderRadius: '6px' }}>
              <label><strong>Select Operation Type:</strong></label>
              <div>
                <label style={{ display: 'block', marginTop: '8px' }}>
                  <input
                    type="radio"
                    name="f_operation_type"
                    checked={details.operation_mode === 'failure'}
                    onChange={() => handleChange('operation_mode', 'failure')}
                    style={{ width: "18px", height: "18px", cursor: "pointer" }}
                  />
                  Failure of Equipment
                </label>

                <label style={{ display: 'block', marginTop: '8px' }}>
                  <input
                    type="radio"
                    name="f_operation_type"
                    checked={details.operation_mode === 'restoration'}
                    onChange={() => handleChange('operation_mode', 'restoration')}
                    style={{ width: "18px", height: "18px", cursor: "pointer" }}
                  />
                  Restoration of Operation
                </label>
              </div>
            </div>

            {/* Conditionally Render Based on Mode */}
            {details.operation_mode === 'failure' && (
              <>
                {/* 19. Failure Start Time */}
                <div>
                  <label>19. Time of system failure *</label>
                  <input
                    type="time"
                    value={details.failure_start_time || ""}
                    onChange={(e) => handleChange('failure_start_time', e.target.value.toUpperCase())}
                    placeholder="e.g., 09:00 HRS"
                    style={{ width: "150px", borderColor: errors.failure_start_time ? 'red' : '#ccc' }}
                  />
                  {errors.failure_start_time && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.failure_start_time}
                    </span>
                  )}
                </div>

                {/* Equipment Affected - Manual Entry */}
                <div>
                  <label>20. Action Taken/Equipment Affected *</label>
                  <textarea
                    rows="2"
                    value={details.equipment_affected || ""}
                    onChange={(e) => handleChange('equipment_affected', e.target.value.toUpperCase())}
                    placeholder="Name the Equipment which got effected due to failure or Explain If any action was Taken "
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderColor: errors.equipment_affected ? 'red' : '#ccc',
                      borderRadius: '4px',
                      resize: 'vertical'
                    }}
                    required
                  />
                  {errors.equipment_affected && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.equipment_affected}
                    </span>
                  )}
                </div>

                {/* 21. Failure Reason */}
                <div>
                  <label>21. Reasons for failure*</label>
                  <textarea
                    rows="3"
                    value={details.failure_reason || ""}
                    onChange={(e) => handleChange('failure_reason', e.target.value)}
                    placeholder="Explain Reason of failure"
                    style={{ width: '100%', borderColor: errors.failure_reason ? 'red' : '#ccc' }}
                  />
                  {errors.failure_reason && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.failure_reason}
                    </span>
                  )}
                </div>
              </>
            )}

            {details.operation_mode === 'restoration' && (
              <>
                <div>
                  <label>19. Time of system failure *</label>
                  <input
                    type="datetime-local"
                    value={details.failure_start_time || ""}
                    onChange={(e) => handleChange('failure_start_time', e.target.value)}
                    max={formatToDateTimeLocal(new Date())}
                    style={{ width: "200px", borderColor: errors.failure_start_time ? 'red' : '#ccc' }}
                  />
                  {errors.failure_start_time && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.failure_start_time}
                    </span>
                  )}
                </div>

                {/* 20. Restored Time */}
                <div>
                  <label>20. Time when system has been made operational. *</label>
                  <input
                    type="time"
                    value={details.restored_time || ""}
                    onChange={(e) => handleChange('restored_time', e.target.value.toUpperCase())}
                    placeholder="e.g., 13:00 HRS"
                    style={{ width: "150px", borderColor: errors.restored_time ? 'red' : '#ccc' }}
                  />
                  {errors.restored_time && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.restored_time}
                    </span>
                  )}
                </div>

                {/* 21. Description of Failure */}
                <div>
                  <label>21. Reasons for failure*</label>
                  <textarea
                    rows="3"
                    value={details.failure_reason || ""}
                    onChange={(e) => handleChange('failure_reason', e.target.value)}
                    placeholder="Explain reason of failure"
                    style={{ width: '100%', borderColor: errors.failure_reason ? 'red' : '#ccc' }}
                  />
                  {errors.failure_reason && (
                    <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                      {errors.failure_reason}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>

        );


      case 'G':
        return (

          <div className="card" style={{ width: '920px' }}>
            {dateInputSection}
            <h4>Accidental or Exceptional Discharges of Oil (Code G)</h4>

            {/* 22. Occurrence Time */}
            <div>
              <label>22. Time of Occurrence *</label>
              <input
                type="time"
                value={details.occurrence_time || ""}
                onChange={(e) => handleChange('occurrence_time', e.target.value)}
                style={{ width: "150px", borderColor: errors.occurrence_time ? 'red' : '#ccc' }}
                required
              />
              {errors.occurrence_time && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.occurrence_time}
                </span>
              )}
            </div>

            {/* 23A. Position (Free Text) */}
            <div>
              <label>23. Position *</label>
              <textarea
                rows="2"
                value={details.position_text || ""}
                onChange={(e) => handleChange("position_text", e.target.value)}
                style={{
                  width: "200px",
                  borderColor: errors.position_text ? "red" : "#ccc"
                }}
                required
              />
              {errors.position_text && (
                <span style={{ color: "red", fontSize: "12px", display: "block" }}>
                  {errors.position_text}
                </span>
              )}
            </div>

            {/* 23. Position */}
            {/* 23. Position at Time of Occurrence */}
            <div>
              <label>23. Position at Time of Occurrence *</label>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto auto auto auto auto auto",
                  gap: "8px",
                  marginTop: "4px",
                  alignItems: "center",
                }}
              >

                {/* Lat Deg */}
                <div>
                  <label>Lat Deg</label>
                  <select
                    value={details.position_lat_deg || ""}
                    onChange={(e) =>
                      handleChange(
                        "position_lat_deg",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px", borderColor: errors.position ? "red" : "#ccc" }}
                    required
                  >
                    <option value="">Â°</option>
                    {[...Array(91)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lat Min */}
                <div>
                  <label>Min</label>
                  <select
                    value={details.position_lat_min || ""}
                    onChange={(e) =>
                      handleChange(
                        "position_lat_min",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px", borderColor: errors.position ? "red" : "#ccc" }}
                    required
                  >
                    <option value="">â€²</option>
                    {[...Array(60)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lat Dir */}
                <div>
                  <label>Dir</label>
                  <select
                    value={details.position_lat_dir || ""}
                    onChange={(e) => handleChange("position_lat_dir", e.target.value)}
                    style={{ width: "60px", borderColor: errors.position ? "red" : "#ccc" }}
                    required
                  >
                    <option value="">N/S</option>
                    <option value="N">N</option>
                    <option value="S">S</option>
                  </select>
                </div>

                {/* Lon Deg */}
                <div>
                  <label>Lon Deg</label>
                  <select
                    value={details.position_lon_deg || ""}
                    onChange={(e) =>
                      handleChange(
                        "position_lon_deg",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px", borderColor: errors.position ? "red" : "#ccc" }}
                    required
                  >
                    <option value="">Â°</option>
                    {[...Array(181)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lon Min */}
                <div>
                  <label>Min</label>
                  <select
                    value={details.position_lon_min || ""}
                    onChange={(e) =>
                      handleChange(
                        "position_lon_min",
                        e.target.value === "" ? "" : parseInt(e.target.value, 10)
                      )
                    }
                    style={{ width: "70px", borderColor: errors.position ? "red" : "#ccc" }}
                    required
                  >
                    <option value="">â€²</option>
                    {[...Array(60)].map((_, i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Lon Dir */}
                <div>
                  <label>Dir</label>
                  <select
                    value={details.position_lon_dir || ""}
                    onChange={(e) => handleChange("position_lon_dir", e.target.value)}
                    style={{ width: "60px", borderColor: errors.position ? "red" : "#ccc" }}
                    required
                  >
                    <option value="">E/W</option>
                    <option value="E">E</option>
                    <option value="W">W</option>
                  </select>
                </div>
              </div>

              {/* Validation error */}
              {errors.position && (
                <span style={{ color: "red", fontSize: "12px", display: "block" }}>
                  {errors.position}
                </span>
              )}
            </div>

            {/* 24. Quantity and Type of Oil */}
            <div>
              <label>24. Approximate Quantity *</label>
              <input
                type="number"
                step="0.01"
                value={details.quantity_m3 || ""}
                onChange={(e) => handleChange('quantity_m3', parseFloat(e.target.value))}
                placeholder="Discharge Quantity from tank"
                style={{ width: '100%', borderColor: errors.quantity_m3 ? 'red' : '#ccc' }}
              />
              {errors.quantity_m3 && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.quantity_m3}
                </span>
              )}
            </div>

            <div>
              <label>24. Type of Oil *</label>
              <select
                value={details.oil_type || ""}
                onChange={(e) => handleChange('oil_type', e.target.value)}
                style={{ width: '100%', borderColor: errors.oil_type ? 'red' : '#ccc' }}
              >
                <option value="">Select Oil Type</option>
                <option value="HFO">HFO (Heavy Fuel Oil)</option>
                <option value="MDO">MDO (Marine Diesel Oil)</option>
                <option value="LUB OIL">LUB OIL (Lubricating Oil)</option>
                <option value="SLUDGE">SLUDGE</option>
              </select>
              {errors.oil_type && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.oil_type}
                </span>
              )}
            </div>

            {/* 25. Circumstances and Remarks */}
            <div>
              <label>25. Circumstances, Reasons and General Remarks *</label>
              <textarea
                rows="4"
                value={details.remarks || ""}
                onChange={(e) => handleChange('remarks', e.target.value)}
                // placeholder="e.g., Pipeline rupture during bunkering, immediate action taken, no environmental impact"
                style={{ width: '100%', borderColor: errors.remarks ? 'red' : '#ccc' }}
                required
              />
              {errors.remarks && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.remarks}
                </span>
              )}
            </div>
          </div>

        );


      case 'H':

        const validateBunkering = () => {
          //  Safely get arrays, default to []
          const fuelTanks = Array.isArray(details.fuel_tanks) ? details.fuel_tanks : [];
          const lubeTanks = Array.isArray(details.lube_tanks) ? details.lube_tanks : [];

          // Fuel oil check (26.3)
          if (details.fuel_quantity || fuelTanks.length > 0) {
            if (!details.fuel_quantity || isNaN(details.fuel_quantity)) {
              alert("Fuel oil quantity must be entered in METRIC TONNES (MT).");
              return false;
            }
            if (!details.fuel_type) {
              alert("Fuel oil type must be specified (e.g., ISO-F-RMG 380).");
              return false;
            }

            const sulfurValue = details.fuel_sulfur?.trim();
            if (!sulfurValue) {
              alert("Please enter sulfur percentage (e.g., 2.7)");
              return false;
            }

            const sulfurNum = parseFloat(sulfurValue);
            if (isNaN(sulfurNum)) {
              alert("Sulfur percentage must be a valid number (e.g., 2.7)");
              return false;
            }

            if (fuelTanks.length === 0 || fuelTanks.every(tank => !tank)) {
              alert("At least one Fuel oil TANK must be selected.");
              return false;
            }

            if (details.lube_quantity || details.lube_type || (lubeTanks && lubeTanks.length > 0)) {
              alert("You cannot enter fuel oil (26.3) and lubricating oil (26.4) in the same record. Please create SEPARATE entries.");
              return false;
            }

            //  Validate total quantity
            const totalEntered = (details.fuel_quantities?.reduce((sum, q) => sum + (q || 0), 0) || 0);
            if (Math.abs(totalEntered - details.fuel_quantity) > 0.01) {
              alert(`Total quantity (${totalEntered} MT) does not match total (${details.fuel_quantity} MT).`);
              return false;
            }

            //  Validate fuel tanks
            for (let i = 0; i < fuelTanks.length; i++) {
              const tankId = fuelTanks[i];
              const qty = parseFloat(details.fuel_quantities?.[i] || 0);
              const currentContents = parseFloat(details.fuel_current_contents?.[i] || 0);

              if (!tankId) continue;

              const tank = availableTanks?.find(t => t.id === tankId);
              if (!tank) continue;

              const tankCapacity = parseFloat(tank.capacity) || 0;
              const maxMT = tankCapacity * 0.9;

              //  90% rule for bunkered qty
              if (qty > maxMT) {
                alert(`"${tank.tank_name}" capacity is ${tankCapacity} MT (90% = ${maxMT.toFixed(2)} MT). You entered ${qty} MT.`);
                return false;
              }

              //  Now containing cannot exceed full capacity
              if (currentContents > tankCapacity) {
                alert(`"${tank.tank_name}" now containing (${currentContents} MT) exceeds tank capacity (${tankCapacity} m3).`);
                return false;
              }

              //  Now containing cannot exceed full capacity
              if (currentContents < qty) {
                alert(`"${tank.tank_name}" now containing (${currentContents} MT) can't be less than tank capacity (${qty} MT).`);
                return false;
              }


              // Combined (bunkered + now containing) cannot exceed capacity
              if (currentContents > tankCapacity) {
                alert(`"${tank.tank_name}" total (Bunkered ${qty} + Now Containing ${currentContents}) exceeds tank capacity (${tankCapacity} m3).`);
                return false;
              }
            }


            //  Prevent duplicate fuel tanks
            const fuelTankIds = fuelTanks.filter(Boolean); //  Safe: fuelTanks is []
            const fuelDuplicates = new Set(fuelTankIds).size !== fuelTankIds.length;
            if (fuelDuplicates) {
              alert("You cannot select the same fuel oil tank twice.");
              return false;
            }
          }

          // Lubricating oil check (26.4)
          if (details.lube_quantity || details.lube_type || lubeTanks.length > 0) {
            if (!details.lube_quantity || isNaN(details.lube_quantity)) {
              alert("Lubricating oil quantity must be entered in METRIC TONNES (MT).");
              return false;
            }
            if (!details.lube_type) {
              alert("Lubricating oil type must be specified .");
              return false;
            }

            if (lubeTanks.length === 0 || lubeTanks.every(tank => !tank)) {
              alert("At least one Lubricating oil TANK must be selected.");
              return false;
            }

            //  Prevent duplicate lube tanks
            const lubeTankIds = lubeTanks.filter(Boolean);
            const lubeDuplicates = new Set(lubeTankIds).size !== lubeTankIds.length;
            if (lubeDuplicates) {
              alert("You cannot select the same lubricating oil tank twice.");
              return false;
            }

            //  Validate lube tanks
            for (let i = 0; i < lubeTanks.length; i++) {
              const tankId = lubeTanks[i];
              const qty = parseFloat(details.lube_quantities?.[i] || 0);
              const currentContents = parseFloat(details.lube_current_contents?.[i] || 0);

              if (!tankId) continue;

              const tank = availableTanks?.find(t => t.id === tankId);
              if (!tank) continue;

              const tankCapacity = parseFloat(tank.capacity) || 0;
              const maxMT = tankCapacity * 0.9;

              if (qty > maxMT) {
                alert(`"${tank.tank_name}" capacity is ${tankCapacity} MT (90% = ${maxMT.toFixed(2)} MT). You entered ${qty} MT.`);
                return false;
              }

              if (currentContents > tankCapacity) {
                alert(`"${tank.tank_name}" now containing (${currentContents} MT) exceeds tank capacity (${tankCapacity} MT).`);
                return false;
              }

              if (currentContents < qty) {
                alert(`"${tank.tank_name}" now containing (${currentContents} MT) can't be less than tank capacity (${qty} MT).`);
                return false;
              }

              if (currentContents > tankCapacity) {
                alert(`"${tank.tank_name}" total (Bunkered ${qty} + Now Containing ${currentContents}) exceeds tank capacity (${tankCapacity} MT).`);
                return false;
              }
            }

            //  Validate total lube quantity
            const totalEntered = (details.lube_quantities?.reduce((sum, q) => sum + (q || 0), 0) || 0);
            if (Math.abs(totalEntered - details.lube_quantity) > 0.01) {
              alert(`Total lube oil quantity (${totalEntered} MT) does not match total (${details.lube_quantity} MT).`);
              return false;
            }
          }
          console.log("Max allowed:", formatToDateTimeLocal(new Date()));
          console.log("Min allowed:", details.start_time);


          return true;
        };



        return (

          <div className="card" style={{ width: "920px" }}>
            {dateInputSection}
            {/* Place of Bunkering */}
            <div>
              <label>26.1 Place of Bunkering *</label>
              <input
                type="text"
                value={details.place_of_bunkering || ''}
                onChange={(e) => {
                  const onlyChars = e.target.value.replace(/[^A-Za-z\s]/g, ""); // allow only letters + spaces
                  handleChange("place_of_bunkering", onlyChars.toUpperCase());
                }}
                required
              />
            </div>

            {/* Time of Bunkering */}
            <div>
              <label>26.2 Time of Bunkering *</label>

              <div>
                <label>Start Time</label>
                <input
                  type="datetime-local"
                  value={details.start_time || ''}
                  onChange={(e) => handleChange('start_time', e.target.value)}
                  max={formatToDateTimeLocal(new Date())}
                  required
                  style={{ width: "200px" }}
                />
              </div>

              <div>
                <label>End Time</label>
                <input
                  type="datetime-local"
                  value={details.end_time || ''}
                  onChange={(e) => handleChange('end_time', e.target.value)}
                  min={details.start_time}
                  max={formatToDateTimeLocal(new Date())}
                  required
                  style={{ width: "200px" }}
                />
              </div>


              {/* Validation Messages */}
              {details.start_time && details.end_time && new Date(details.end_time) < new Date(details.start_time) && (
                <p style={{ color: 'red', fontSize: '0.85rem' }}>
                  End time cannot be before start time.
                </p>
              )}

              {details.start_time && new Date(details.start_time) < yesterdayDate() && (
                <p style={{ color: 'red', fontSize: '0.85rem' }}>
                  Start time cannot be earlier than yesterday 00:00.
                </p>
              )}
            </div>
            {/* Choose Bunkering Type */}
            <div style={{ margin: '15px 0' }}>
              <label>What are you bunkering? *</label>
              <div style={{ display: 'flex', gap: '20px', marginTop: '5px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <input
                    type="radio"
                    value="fuel"
                    checked={bunkeringType === 'fuel'}
                    onChange={(e) => setBunkeringType(e.target.value)}
                    style={{ width: "18px", height: "18px", cursor: "pointer" }}
                  />
                  Fuel Oil (26.3)
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <input
                    type="radio"
                    value="lube"
                    checked={bunkeringType === 'lube'}
                    onChange={(e) => setBunkeringType(e.target.value)}
                    style={{ width: "18px", height: "18px", cursor: "pointer" }}
                  />
                  Lubricating Oil (26.4)
                </label>
              </div>
            </div>


            {/* 26.3 Fuel Oil */}
            {bunkeringType === 'fuel' && (
              <fieldset>
                <legend>26.3 Fuel Oil (one grade per entry)</legend>

                {/* Total Quantity & Type */}
                <input
                  type="number"
                  step="0.001"
                  value={details.fuel_quantity || ''}
                  onChange={(e) => handleChange('fuel_quantity', parseFloat(e.target.value))}
                  placeholder="Enter Total Fuel Qauntity Bunkered"
                  style={{ gap: '20px', margin: '5px', marginTop: '6px' }}
                />
                <input
                  type="text"
                  value={details.fuel_type || ''}
                  onChange={(e) => handleChange('fuel_type', e.target.value.toUpperCase())}
                  placeholder="Enter Fuel Type as per BDN"
                  style={{ gap: '20px', margin: '5px', marginTop: '6px' }}
                />

                <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
                  <input
                    type="text"
                    value={details.fuel_sulfur || ''}
                    onChange={(e) => {
                      //   . Allow only numbers and decimal
                      const val = e.target.value;
                      if (val === '' || /^\d*\.?\d*$/.test(val)) {
                        handleChange('fuel_sulfur', val);
                      }
                    }}
                    placeholder="e.g., 2.7"
                    style={{ gap: '20px', margin: '5px', marginTop: '6px' }}
                  />
                  <span style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: '#999',
                    pointerEvents: 'none'
                  }}>
                    %S
                  </span>
                </div>
                {/* Dynamic Tank Rows */}
                {(details.fuel_tanks || []).map((tankId, index) => (
                  <div key={index} style={{ display: 'flex', gap: '10px', margin: '5px 0' }}>
                    <select
                      value={tankId || ""}
                      onChange={(e) => {
                        const newTanks = [...(details.fuel_tanks || [])];
                        newTanks[index] = e.target.value;
                        handleChange('fuel_tanks', newTanks);
                      }}
                      style={{ flex: 1 }}
                    >
                      <option value="">Select Fuel Oil Tank</option>
                      {(availableTanks || [])
                        .filter(t =>
                          t.tank_name?.toUpperCase().includes("F.O") ||
                          t.tank_name?.toUpperCase().includes("M.D.O") ||
                          t.tank_name?.toUpperCase().includes("FUEL")
                        )
                        .map(tank => (
                          <option key={tank.id} value={tank.id}>
                            {tank.tank_name} ({tank.capacity} mÂ³)
                          </option>
                        ))}
                    </select>

                    <input
                      type="number"
                      step="0.001"
                      value={details.fuel_quantities?.[index] || ''}
                      onChange={(e) => {
                        const newQuantities = [...(details.fuel_quantities || [])];
                        newQuantities[index] = parseFloat(e.target.value);
                        handleChange('fuel_quantities', newQuantities);
                      }}
                      placeholder="Quantity(MT)"
                      style={{ width: '200px' }}
                    />

                    <input
                      type="number"

                      value={details.fuel_current_contents?.[index] || ''}
                      onChange={(e) => {
                        const newContents = [...(details.fuel_current_contents || [])];
                        newContents[index] = parseFloat(e.target.value);
                        handleChange('fuel_current_contents', newContents);
                      }}
                      placeholder="Now Containing"
                      style={{ width: '200px' }}
                    />

                    <button
                      type="button"
                      onClick={() => {
                        const newTanks = (details.fuel_tanks || []).filter((_, i) => i !== index);
                        const newQuantities = (details.fuel_quantities || []).filter((_, i) => i !== index);
                        const newContents = (details.fuel_current_contents || []).filter((_, i) => i !== index);
                        handleChange('fuel_tanks', newTanks);
                        handleChange('fuel_quantities', newQuantities);
                        handleChange('fuel_current_contents', newContents);
                      }}
                      style={{ background: '#917ee4ff', color: 'white', border: 'none', padding: '4px 8px' }}
                    >
                      âœ–
                    </button>
                  </div>
                ))}

                {/* Add Tank Button */}
                {(details.fuel_tanks || []).length < 7 && (
                  <button
                    type="button"

                    variant="secondary"
                    onClick={() => {
                      const newTanks = details.fuel_tanks ? [...details.fuel_tanks, ""] : [""];
                      const newQuantities = details.fuel_quantities ? [...details.fuel_quantities, 0] : [0];
                      const newContents = details.fuel_current_contents ? [...details.fuel_current_contents, 0] : [0];
                      handleChange('fuel_tanks', newTanks);
                      handleChange('fuel_quantities', newQuantities);
                      handleChange('fuel_current_contents', newContents);
                    }}

                  >
                    Add Fuel Tank
                  </button>
                )}
              </fieldset>
            )}

            {/* 26.4 Lubricating Oil (bulk only) */}
            {bunkeringType === 'lube' && (
              <fieldset>
                <legend>26.4 Lubricating Oil (bulk only)</legend>

                {/* Total Quantity & Type */}
                <input
                  type="number"
                  step="0.001"
                  value={details.lube_quantity || ''}
                  onChange={(e) => handleChange('lube_quantity', parseFloat(e.target.value))}
                  placeholder="Enter Total Lube Qauntity Bunkered"
                  style={{ gap: '20px', margin: '5px', marginTop: '6px' }}
                />
                <input
                  type="text"
                  value={details.lube_type || ''}
                  onChange={(e) => handleChange('lube_type', e.target.value.toUpperCase())}
                  placeholder="Enter Lube grade as per BDN "
                  style={{ gap: '20px', margin: '5px', marginTop: '6px' }}
                />

                {/* Dynamic Tank Rows */}
                {(details.lube_tanks || []).map((tankId, index) => (
                  <div key={index} style={{ display: 'flex', gap: '10px', margin: '5px 0' }}>
                    <select
                      value={tankId || ""}
                      onChange={(e) => {
                        const newTanks = [...(details.lube_tanks || [])];
                        newTanks[index] = e.target.value;
                        handleChange('lube_tanks', newTanks);
                      }}
                      style={{ flex: 1 }}
                    >
                      <option value="">Select Lube Oil Tank</option>
                      {(availableTanks || [])
                        .filter(t =>
                          t.tank_name?.toUpperCase().includes("LUBE") ||
                          t.tank_name?.toUpperCase().includes("L.O") ||
                          t.tank_name?.toUpperCase().includes("LUB")
                        )
                        .map(tank => (
                          <option key={tank.id} value={tank.id}>
                            {tank.tank_name} ({tank.capacity} mÂ³)
                          </option>
                        ))}
                    </select>

                    <input
                      type="number"
                      step="0.001"
                      value={details.lube_quantities?.[index] || ''}
                      onChange={(e) => {
                        const newQuantities = [...(details.lube_quantities || [])];
                        newQuantities[index] = parseFloat(e.target.value);
                        handleChange('lube_quantities', newQuantities);
                      }}
                      placeholder="Quantity (MT)"
                      style={{ width: '200px' }}
                    />

                    <input
                      type="number"
                      step="0.001"
                      value={details.lube_current_contents?.[index] || ''}
                      onChange={(e) => {
                        const newContents = [...(details.lube_current_contents || [])];
                        newContents[index] = parseFloat(e.target.value);
                        handleChange('lube_current_contents', newContents);
                      }}
                      placeholder="Now Containing"
                      style={{ width: '200px' }}
                    />


                    <button
                      type="button"
                      onClick={() => {
                        const newTanks = (details.lube_tanks || []).filter((_, i) => i !== index);
                        const newQuantities = (details.lube_quantities || []).filter((_, i) => i !== index);
                        const newContents = (details.lube_current_contents || []).filter((_, i) => i !== index);
                        handleChange('lube_tanks', newTanks);
                        handleChange('lube_quantities', newQuantities);
                        handleChange('lube_current_contents', newContents);
                      }}
                      style={{ background: '#917ee4ff', color: 'white', border: 'none', padding: '4px 8px' }}
                    >
                      âœ–
                    </button>
                  </div>



                ))}

                {/* Add Tank Button */}
                {(details.lube_tanks || []).length < 7 && (
                  <button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      const newTanks = details.lube_tanks ? [...details.lube_tanks, ""] : [""];
                      const newQuantities = details.lube_quantities ? [...details.lube_quantities, 0] : [0];
                      const newContents = details.lube_current_contents ? [...details.lube_current_contents, 0] : [0];
                      handleChange('lube_tanks', newTanks);
                      handleChange('lube_quantities', newQuantities);
                      handleChange('lube_current_contents', newContents);
                    }}

                  >
                    Add Lube Tank
                  </button>
                )}
              </fieldset>
            )}
            {/* Validate on submit */}
            <Button
              type="submit"
              onClick={(e) => {
                if (!validateBunkering()) e.preventDefault();
              }}
            >
              Save Draft
            </Button>
          </div>





        );


      case 'I':
        return (

          <div className="card" style={{ width: '920px' }}>
            {dateInputSection}
            <h4>Additional Operational Procedures and General Remarks (Code I)</h4>

            {/* Free Text Entry */}
            <div>
              <label>Enter your remarks or operational details *</label>
              <textarea
                rows="6"
                value={details.remarks || ""}
                onChange={(e) => handleChange('remarks', e.target.value)}
                // placeholder={`e.g., Drained 15 litres of water from No.1 F.O. settling tank (P) to bilge well.\n\nOR\n\nTransferred 200 litres of MDO from storage tank to service tank for generator testing.\n\nOR\n\nWeekly check of sludge tank levels: WASTE OIL TANK (FR:24-27) - 38 mÂ³`}
                style={{
                  width: '100%',
                  borderColor: errors.remarks ? 'red' : '#ccc',
                  fontFamily: 'monospace',
                  padding: '8px'
                }}
                required
              />
              {errors.remarks && (
                <span style={{ color: 'red', fontSize: '12px', display: 'block' }}>
                  {errors.remarks}
                </span>
              )}
            </div>

            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
              <strong>Tip:</strong> Be clear, factual, and include quantities and tank names where possible.
            </div>
          </div>

        );

      default:
        return <p>Select a code to begin.</p>;
    }
  };

  const codeOptions = (codes || []).map((c) => (
    <option key={c.id} value={c.code}>
      {c.code} â€“ {c.description}
    </option>
  ));

  return (

    <Card>
      <form onSubmit={handleSubmit} className="orb-form">
        <WithPermission id="PSC_F_014">
          <div className="form-row">
            <label>Select Code *</label>
            <select
              value={formData?.code || ""}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  code: e.target.value,
                  details: {},
                }))
              }
            >
              <option value="">Select Code</option>

              {codeOptions}
            </select>


          </div>
        </WithPermission>

        {formData.code && (
          <div style={{ marginTop: "1.5rem" }}>
            {renderFields()}
          </div>
        )}

        {/*   . Move the button inside the form */}
        {/* Only show the default Save Draft button if NOT Code H */}
        {formData.code !== 'H' && (
          <div style={{ marginTop: '1.5rem', textAlign: 'right' }}>
            <button
              type="submit"
              className="btn-submit"
              style={{
                border: 'none',
                padding: '0.7rem 1.5rem',
                borderRadius: '12px',
                background: 'linear-gradient(90deg, #8a6cf3, #5a6ef5)',
                color: 'white',
                fontWeight: '700',
                fontSize: '0.92rem',
                cursor: 'pointer',
                boxShadow: '0 10px 24px rgba(90, 110, 245, 0.35)',
                transition: 'filter 0.2s'
              }}
              onMouseOver={(e) => e.target.style.filter = 'brightness(1.05)'}
              onMouseOut={(e) => e.target.style.filter = 'none'}
            >
              Save Draft
            </button>

          </div>
        )}
      </form>
    </Card>


  );
}


//   . ORB Table
function ORBTable({ entries, onEdit, onDelete }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
      .toUpperCase()
      .replace(/ /g, '-');
  };

  return (
    <Card>
      <WithPermission id="PSC_F_015">
        <div className="orb-theme">
          <h1>Your Drafts</h1>
          <div style={{ overflowX: 'auto', width: '100%', margin: '1rem 0' }}>
            <table className="orb-table" style={{ minWidth: '800px', width: '100%' }}>
              <thead>
                <tr>

                  <th>Date</th>
                  <th>Code</th>
                  <th>Item No.</th>
                  <th>Record of operations/signature of officer in charge</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {entries.filter(obj => obj.status == 'Pending').map((entry) => {
                  const lines = (entry.record_of_operation || '').split('\n').filter(line => line.trim() !== '');
                  const formattedDate = formatDate(entry.date);



                  return lines.map((line, idx) => {
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
                            //   . Use the stored method from details (most reliable)
                            // But since we only have record_of_operation, check content
                            if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
                              itemNo = '9.1';
                            } else {
                              //   . Assume it's 9.2 if not 9.1 and line is not quantity
                              itemNo = '9.2';
                            }
                          }
                          //   . Quantity is always 10, regardless of index
                          else if (line.includes('MÂ³')) {
                            itemNo = '10';
                          }
                          break;

                        case 'C':
                          if (idx === 0) {
                            itemNo = entry.item_no || '';
                          } case 'C':
                          // 11.1 handled on first line
                          if (line.includes('MÂ³') && !line.includes('COLLECTED') && !line.includes('RETAINED')) {
                            itemNo = '11.2';;
                          } if ((idx === 2) && line.includes('MÂ³')) {
                            itemNo = '11.3';
                          } if (idx === 3) {
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
                          if (line.includes('HRS') && (idx === 0)) {
                            itemNo = '19';
                          } else if ((idx === 1)) {
                            itemNo = '20';
                          } if (idx === 2) {
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
                        <td>
                          {idx === 0 && ( // Show buttons only on the first line of the group
                            <>
                              <WithPermission id="PSC_P_037">
                                <button onClick={() => onEdit(entry.id)}>Edit</button> {/* Edit button */}
                              </WithPermission>
                              <WithPermission id="PSC_P_038">
                                <button onClick={() => onDelete(entry.id)}>Delete</button> {/* Delete button */}
                              </WithPermission>
                            </>
                          )}
                        </td>
                      </tr>
                    );
                  });
                })}
              </tbody>
            </table>

          </div>
        </div>
      </WithPermission>
    </Card>
  );
}
