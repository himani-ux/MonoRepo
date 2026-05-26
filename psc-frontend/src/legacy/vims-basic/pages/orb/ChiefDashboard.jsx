// src/components/ChiefDashboard.jsx
import  { useEffect, useState } from "react";

import CrewDashboard from "./CrewDashboard";
import { buildItemRows, formatDate } from "../../utils/orb/orbUtils";

import "../../styles/orb/orb-theme.css";
import { Panel, Button, Card, Stack } from "../../components/orb/OrbUI";

import AppFooter from "../../components/orb/AppFooter";

import "../../styles/orb/ChiefDashboard.css";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable"
import { WithPermission } from '../../utils/orb/permissionUtils';
import { useAuth } from '../../hooks/auth/useAuth';

export default function ChiefDashboard() {
  const [pending, setPending] = useState([]);
  const [approved, setApproved] = useState([]);
  const [codes, setCodes] = useState([]);
  const [formData, setFormData] = useState({ code: "", details: {} });
  const [vessel, setVessel] = useState(null);
  const [showChiefForm, setShowChiefForm] = useState(false);
  const {user} = useAuth();
  const vesselId = user?.vessel_id;
  const chiefName = `${user?.username?.toUpperCase() || "CHIEF ENGINEER"} (${user?.rank?.toUpperCase() || "CHIEF"})`;
  const [reportData, setReportData] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [isReportVisible, setIsReportVisible] = useState(false);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const headerStyle = {
    fontFamily: 'Courier New, monospace',
    fontSize: '14px'
  };

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '10px',
    fontFamily: 'Courier New',
    overflow: "linebreak",
    fontSize: '12px'
  };

  const thStyle = {
    border: '1px solid #000',
    padding: '8px',
    textAlign: 'center',
    backgroundColor: '#f8f9fa',
    fontWeight: 'bold'
  };

  const tdStyle = {
    border: '1px solid #000',
    padding: '6px',
    fontFamily: 'Courier New'
  };

  const footerStyle = {
    marginTop: '3rem',
    textAlign: 'center',
    fontFamily: 'Courier New, monospace'
  };



  const refresh = async () => {
    try {
      const response = await fetch(
        `/api/orb/api/operations/?vessel_id=${vesselId}&is_deleted=false`
      );
      const data = await response.json();
      const ops = Array.isArray(data) ? data : data.results || [];

      // filter properly 
      const formattedPending = ops
        .filter(e => e.status === "Pending")
        .map(entry => ({
          ...entry,
          rows: buildItemRows(entry.code, entry.details, entry.date, entry.created_by)
        }))
        .sort((a, b) => {
          // First rule: A always comes before B (this is done for proper formatting in the print)
          if (a.code === "A" && b.code === "B") return -1;
          if (a.code === "B" && b.code === "A") return 1;

          // otherwise, sort by created_at
          return new Date(a.created_at) - new Date(b.created_at);
        });



      const exportedIds = JSON.parse(localStorage.getItem("exportedApprovedIds") || "[]");
      const formattedApproved = ops
        .filter(e => e.status === "Approved" && !exportedIds.includes(e.id))
        .map(entry => ({
          ...entry,
          rows: buildItemRows(entry.code, entry.details, entry.date, entry.created_by)
        }))
        .sort((a, b) => {
          if (a.code === "A" && b.code === "B") return -1;
          if (a.code === "B" && b.code === "A") return 1;

          return new Date(a.approved_at) - new Date(b.approved_at);
        });


      setPending(formattedPending);
      setApproved(formattedApproved);
    } catch (err) {
      console.error("Failed to load entries:", err);
    }
  };





  const handleReportPeriod = async (period) => {
    console.log("handleReportPeriod called with:", period);

    const vesselId = user?.vessel_id
    if (!vesselId) {
      alert("Vessel not selected");
      console.error("No vesselId in sessionStorage");
      return;
    }

    setSelectedPeriod(period);
    setIsReportVisible(true);
    setReportData([]); // Reseting function

    const today = new Date();
    let fromDate = new Date();

    switch (period) {
      case 'TM': // This Month
        fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
        break;
      case '1M':
        fromDate.setMonth(today.getMonth() - 1);
        break;
      case '6M':
        fromDate.setMonth(today.getMonth() - 6);
        break;
      case '1Y':
        fromDate.setFullYear(today.getFullYear() - 1);
        break;
      case '3Y':
        fromDate.setFullYear(today.getFullYear() - 3);
        break;
      default:
        fromDate = new Date(0);
    }

    console.log("📅 Date Range:", formatDate(fromDate), "to", formatDate(today));

    try {
      const url = `/api/orb/api/operations/?vessel_id=${vesselId}&status=Approved&is_deleted=false`;
      console.log("🔗 Fetching from:", url);

      const response = await fetch(url);
      if (!response.ok) {
        const text = await response.text();
        console.error("API Error:", response.status, text);
        alert("Failed to load  " + response.status);
        return;
      }

      const data = await response.json();
      console.log(" Raw API Response:", data);

      const ops = Array.isArray(data) ? data : data.results || [];
      console.log(" All Approved Entries:", ops);

      if (ops.length === 0) {
        alert("No approved entries found in the system.");
        return;
      }



      //this is the function to filtering date safely
      const filtered = ops.filter(entry => {
        if (!entry.date) {
          console.warn("Entry missing date:", entry);
          return false;
        }

        //  this is function to parse date safely
        const entryDate = new Date(entry.date);
        if (isNaN(entryDate)) {
          console.warn("Invalid date format:", entry.date, "for entry:", entry);
          return false;
        }

        const isValid = entryDate >= fromDate && entryDate <= today;
        console.log(`Entry ${entry.id} date:`, formatDate(entry.date), "Valid:", isValid);
        return isValid;
      });

      console.log(" Filtered Entries:", filtered);

      if (filtered.length === 0) {
        alert("No approved entries found in the selected period.");
        setReportData([]);
        return;
      }

      // function for formatting with rows
      const formatted = filtered.map(entry => {
        console.log("Entry before buildItemRows:", entry);
        try {
          return {
            ...entry,
            rows: buildItemRows(
              entry.code,
              entry.details,
              entry.date,
              entry.created_by,
              []
            )
          };
        } catch (err) {
          console.error("Failed to build rows for entry:", entry, err);
          return null;
        }
      }).filter(Boolean); //this is for removing nulls

      console.log("📊 Formatted Rows:", formatted);
      setReportData(formatted);

    } catch (err) {
      console.error(" Error in handleReportPeriod:", err);
      alert("Network error: Cannot load report. Check console.");
    }
  };


  useEffect(() => {
    if (vesselId) refresh();
  }, [vesselId]);




  // this is a useEffect to fetch the codes from A to I using thier IDs and Description
  useEffect(() => {
    const fetchCodes = async () => {
      try {
        const res = await fetch("/api/orb/api/codes/");
        const data = await res.json();
        const codeList = Array.isArray(data) ? data : data.results || [];
        setCodes(codeList);
      } catch (err) {
        console.error("Failed to fetch ORB codes", err);
        setCodes([]);
      }
    };

    fetchCodes();
  }, []);



  
useEffect(() => {
  const vesselId = user?.vessel_id;
  if (!vesselId) return;

  fetch("/api/orb/api/vessels/")
    .then(res => res.json())
    .then(data => {
      const vesselList = Array.isArray(data) ? data : data.results || [];
      // ✅ Use case-insensitive comparision
      const selectedVessel = vesselList.find(v => v.id.toLowerCase() === vesselId.toLowerCase());

      if (selectedVessel) {
        setVessel({
          vesselName: selectedVessel.vesselName,  //  matches DB column
          imoNumber: selectedVessel.imonumber       // matches DB column
        });
      } else {
        console.warn(" Vessel not found for ID:", vesselId);
      }
    })
    .catch(err => console.error("Failed to load vessels:", err));
}, []); // Empty dependency array if it's meant to run only once on mount


  useEffect(() => {
    const fetchCSRF = async () => {
      const response = await fetch("/api/orb/api/csrf/", {
        credentials: 'include'  //  this is required , if not used then permissions will b denied
      });
      const data = await response.json();
      window.csrfToken = data.csrfToken;
    };
    fetchCSRF();
  }, []);


  useEffect(() => {
    const handleClickOutside = () => {
      if (isFilterOpen) setIsFilterOpen(false);
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [isFilterOpen]);


  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    setFromDate(oneWeekAgo);
    setToDate(today);
  }, []);



  const handleCustomDateRange = async (from, to) => {
    const vesselId = user?.vessel_id
    if (!vesselId) {
      alert("Vessel not selected");
      return;
    }

    if (!from || !to) {
      alert("Please select both From and To dates.");
      return;
    }

    if (new Date(from) > new Date(to)) {
      alert("'From Date' cannot be after 'To Date'");
      return;
    }

    setIsReportVisible(true);
    setReportData([]);

    try {
      //  this is sends only the date part , crops the timing
      const url = `/api/orb/api/operations/?vessel_id=${vesselId}&status=Approved&is_deleted=false&from_date=${from}&to_date=${to}`;
      console.log("Fetching from:", url);

      const response = await fetch(url);

      if (!response.ok) {
        const text = await response.text();
        console.error("API Error:", response.status, text);
        alert(" Failed to load entries");
        return;
      }

      const data = await response.json();
      console.log("Recieved", data); //  Check if filtering worked

      if (data.length === 0) {
        alert("No entries found in the selected date range.");
        setReportData([]);
        return;
      }

      //  Sort by date (newest will appear first)
      const sorted = data.sort((a, b) => new Date(b.date) - new Date(a.date));

      //  Format with rows
      const formatted = sorted.map(entry => ({
        ...entry,
        rows: buildItemRows(
          entry.code,
          entry.details,
          entry.date,
          entry.created_by,

        )
      }));

      setReportData(formatted);
    } catch (err) {
      console.error("Error loading report:", err);
      alert("Network error: Cannot load entries. Check console.");
    }
  };





  const formatDate = (date) => {
    if (!date) return "";
    return new Date(date).toLocaleDateString("en-GB");
  };


  const SYSTEM_PRIVATE_IP = import.meta.env.VITE_PRIVATE_IP || "Unable to get IP";

  const saveAsPDF = async () => {
  if (!approved || approved.length === 0) {
    alert("No entries to save");
    return;
  }

  // ✅ Check if vessel details are loaded using the 'vessel' state
  if (!vessel || !vessel.vesselName || !vessel.imoNumber) {
    alert("Vessel details not loaded yet");
    return;
  }

  // this function Check User Rank (MTR) ---
  
  if (!user) {
    alert("User session not found. Cannot print.");
    return;
  }

  // ✅ Parse the user object from sessionStorage
  

  // Get rank and standardize case, also trim potential spaces
  const userRank = (user?.rank || user?.Rank)?.toUpperCase().trim(); // Use rank_name if that's the key
  const officerFirstName = user?.first_name || "UNKNOWN";
  const officerSurname = user?.surname || "";
  const officerFullName = `${officerFirstName} ${officerSurname}`.trim(); // Combine for full name

  console.log("DEBUG: saveAsPDF - userRank from sessionStorage:", userRank); // Debug log
  console.log("DEBUG: saveAsPDF - user object from sessionStorage:", user); // Debug log

  // Adjust the condition based on the exact value seen in the debug log
  // Example 1: If the value is exactly "MASTER" (after toUpperCase)
  const isMaster = userRank === 'MASTER' || userRank === 'CAPTAIN';

  if (!isMaster) {
    // this above condition Prevent non-Masters from printing and clearing the UI
    alert("Only the Master is authorized to print.");
    return; // Stop execution if not the Master
  }
  console.log(`✅ Print initiated by Master (${userRank}). Proceeding with print and potential UI clear.`);
  // --- End Check User Rank ---

  //Get vessel_id from sessionStorage (most reliable)
  const vesselId = user?.vessel_id;
  if (!vesselId) {
    alert("Vessel not selected. Cannot generate PDF.");
    return;
  }

  // ✅ Use vessel details from the 'vessel' state (already validated)
  const { vesselName, imoNumber } = vessel;
  console.log("Vessel object full:", vessel);

  try {
    // the below variable Fetch last page number from backend
    let lastPageNumber = 0;
    try {
      console.log("Fetching last page with vessel_id:", vesselId);
      const res = await fetch(`/api/get_last_page_number/?vessel_id=${vesselId}`);
      const data = await res.json();
      console.log("data : ", data);
      lastPageNumber = data.last_page || 0;
    } catch (err) {
      console.error("Error fetching last page:", err);
    }


    let serverLocalIP = 'Unknown IP';
    const printTimestamp = new Date();

    try {
      // Fetch the Django server's LOCAL IP address from your OWN backend endpoint
      // This endpoint now uses Python code to find the server's IP, not Node.js
      const ipResponse = await fetch('/api/orb/api/get-internal-ip/'); // Use your backend's URL
      if (!ipResponse.ok) {
        throw new Error(`Failed to get server's local IP: ${ipResponse.status} - ${await ipResponse.text()}`);
      }
      const ipData = await ipResponse.json();
      serverLocalIP = ipData.internal_ip; // Access the IP from the response JSON
      console.log("Django Server's Local IP address (from backend):", serverLocalIP);
    } catch (err) {
      console.error("Error fetching server's local IP from backend:", err);
      alert("Could not fetch server's local IP address. Using default value.");
      // Optionally, you could return here if the IP is critical
      // return;
    }

    const doc = new jsPDF("p", "mm", "a4");
    const columns = ["Date", "Code", "Item", "Record of operations/signature of officer in charge "];

    const rows = approved.flatMap((entry) => {
      const lines = (entry.record_of_operation || "")
        .split("\n")
        .filter((l) => l.trim() !== "");
      const formattedDate = formatDate(entry.date);

      return lines.map((line, idx) => {
        let itemNo = "";

        // First line item no
        if (idx === 0) itemNo = entry.item_no || "";

        // this Reset if SIGNED
        if (line.startsWith("SIGNED:")) itemNo = "";

        // this is dispaying logic for the entries achieved via switch cases
        switch (entry.code) {
          case "A":
            if (line.startsWith("TANK(S) BALLASTED")) itemNo = "1";
            else if (line.includes("TANK CLEANED SINCE") || line.includes("NOT CLEANED – PREVIOUS OIL")) itemNo = "2";
            else if (line.startsWith("START BALLAST")) itemNo = "4.1";
            else if (line.includes("START") && line.includes("HRS")) itemNo = "3.1";
            else if (line.includes("RINSING") || line.includes("STEAMING") || line.includes("CHEMICAL")) itemNo = "3.2";
            else if (line.startsWith("CLEANING WATER TO")) itemNo = "3.3";
            else if (line.includes("BALLAST QUANTITY")) itemNo = "4.2";
            break;

          case "B":
            if (idx === 1 || /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line)) itemNo = "6";
            else if (idx === 2 || /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line)) itemNo = "7";
            else if (line.includes("KNOTS")) itemNo = "8";
            else if (line.includes("THROUGH 15 PPM EQUIPMENT")) itemNo = "9.1";
            else if (line.includes("TO RECEPTION FACILITY")) itemNo = "9.2";
            else if (line.includes("M³")) itemNo = "10";
            break;

          case "C":
            if (idx === 1 && line.includes("M³")) itemNo = "11.2";
            else if (idx === 2 && line.includes("M³")) itemNo = "11.3";
            else if (line.includes("COLLECTED FROM")) itemNo = "11.4";
            else if (line.includes("RECEPTION FACILITY")) itemNo = "12.1";
            else if (line.includes("TRANSFERRED TO") && line.includes("TANK")) itemNo = "12.2";
            else if (line.includes("INCINERATED")) itemNo = "12.3";
            else if (line.includes("EVAPORATED") || line.includes("DRAINED")) itemNo = "12.4";
            break;

          case "D":
            if (idx === 0) itemNo = "13";
            if (idx === 1 && line.startsWith("START:")) itemNo = "14";
            else if (line.includes("THROUGH 15 PPM EQUIPMENT")) itemNo = "15.1";
            else if (line.includes("TO PORT RECEPTION FACILITIES OF")) itemNo = "15.2";
            else if (line.includes("TRANSFERRED TO") || line.includes("RETAINED IN TANK") && (idx === 2)) itemNo = "15.3";
            break;

          case "F":
            if ((idx === 0)) itemNo = "19";
            else if (idx === 1 || line.includes("HRS")) itemNo = "20";
            else if ((idx === 2) && (line.trim().length > 0)) itemNo = "21";
            break;

          case "G":
            if (idx === 0) itemNo = '22'
            if (idx === 1 || /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line)) itemNo = "23";
            if (idx === 2) itemNo = "24";
            else if (idx === 3) itemNo = "25";
            break;

          case "H":
            if (line.startsWith("PLACE:")) itemNo = "26.1";
            else if (
              line.startsWith("TIME:") ||
              line.includes("BUNKERING START") ||
              line.includes("BUNKERING END") ||
              line.includes("START") ||
              line.includes("END TIME")
            )
              itemNo = "26.2";
            else if (line.includes("FUEL OIL BUNKERED IN TANKS")) itemNo = "26.3";
            else if (line.includes("LUBE BUNKERED IN TANKS")) itemNo = "26.4";
            break;

          case "I":
            itemNo = "";
            break;

          default:
            if (line.includes("M³") || line.includes("MT")) itemNo = "10";
            break;
        }

        return [
          idx === 0 ? formattedDate : "",
          idx === 0 ? entry.code : "",
          itemNo,
          line,
        ];
      });
    });

    autoTable(doc, {
      head: [columns],
      body: rows,
      margin: { top: 50, bottom: 30 },
      theme: "grid",
      styles: {
        font: "Bookman Old Style",
        fontSize: 10,
        cellPadding: 2,
        overflow: "linebreak",
      },
      columnStyles: { 3: { cellWidth: 100 } },
      headStyles: { fillColor: [245, 245, 245], textColor: 0, fontStyle: "bold" },
      rowPageBreak: "avoid",
      didDrawPage: (data) => {
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();

        // Header
        doc.setFont("courier", "normal");
        doc.setFontSize(12);
        doc.text("Name of ship:", 10, 15);
        doc.text(vesselName || "__________________", 60, 15);
        doc.text("Distinctive number:", 10, 25);
        doc.text(imoNumber || "__________", 60, 25);

        doc.setFont("Bookman Old Style", "bold");
        doc.setFontSize(12);
        doc.text("Machinery Space Operations", 10, 40);

        //  Footer with continuous page numbering and IP/Timestamp
        const currentPage = lastPageNumber + doc.internal.getCurrentPageInfo().pageNumber;
        const currentDate = new Date().toLocaleDateString('en-GB', {
          day: '2-digit',
          month: 'short',
          year: 'numeric'
        }).toUpperCase().replace(/ /g, '-');
        doc.setFont("courier", "normal");
        doc.setFontSize(10); // Smaller font for footer details

        // --- THIS IS A SIGNATURE SECTION ---
        // Line 1: Digitally Signed by
        doc.setTextColor(0, 0, 255);
        const vesselNameForSignature = sessionStorage.getItem("selectedVesselName") || vesselName || "VESSEL_NAME_NOT_FOUND"; // Adjust 'selectedVesselName' key if different
        doc.text(`Digitally Signed by: ${officerFullName} (${userRank} OF ${vesselNameForSignature})`, pageWidth / 2, pageHeight - 25, { align: "center" });
        // doc.setTextColor(0, 0, 0); // Reset to black

        // Line 2: Signed on
        const formattedPrintTime = printTimestamp.toLocaleString('en-US', {
          day: '2-digit',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',

          hour12: true // This will give you "AM/PM"
        }).toUpperCase().replace(/ /g, ' '); // Replace spaces with single space
        // Extract the time part (e.g., "09:36 AM")
        const timePart = formattedPrintTime.split(', ')[1]; // This might not be reliable for all locales
        // A more robust way to get the time string in the desired format:
        const timeOptions = { hour: '2-digit', minute: '2-digit', hour12: true };
        const timeString = printTimestamp.toLocaleTimeString('en-US', timeOptions).toUpperCase();

        doc.text(`Signed on: ${printTimestamp.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase().replace(/ /g, ' ')} At ${timeString}`, pageWidth / 2, pageHeight - 20, { align: "center" });
        doc.setTextColor(0, 0, 255); // Set text color to blue
        doc.text(`IP Address: ${serverLocalIP}`, pageWidth / 2, pageHeight - 15, { align: "center" });
        doc.setTextColor(0, 0, 0); // Reset to black
        doc.text(`${currentPage}`, pageWidth / 2, pageHeight - 10, { align: "center" });
        doc.text(`Date: ${currentDate}`, pageWidth - 20, 15, { align: "right" });
      },

    });

    // Save PDF
    doc.save(`ORB-Approved-Entries-${new Date().toISOString().split("T")[0]}.pdf`);

    const pdfBlob = doc.output('blob');


    const filename = `ORB-Approved-Entries-${new Date().toISOString().split("T")[0]}.pdf`;
    const title = `Approved Logbook Entries - ${new Date().toISOString().split("T")[0]}`;
    const description = `PDF containing approved ORB entries for vessel ${vesselName} as of ${new Date().toISOString().split("T")[0]}.`;

    const pdfFile = new File([pdfBlob], filename, { type: 'application/pdf' });

    // --- NEW: Save PDF file and metadata ---
    try {
      const reader = new FileReader();
      reader.onloadend = async function () {
        const base64String = reader.result.split(',')[1]; // Remove data:application/pdf;base64, part

        // Prepare metadata including the   Filename (for path construction) and the base64 string
        const metadataPayload = {
          filename: filename, // The name of the file
          title: title,
          description: description,
          created_by: user?.UserName || user?.username || 'Master', // Use actual user name
          vessel_id: vesselId, // Use the vessel ID from session storage
          pdf_data: base64String // Include the base64 encoded PDF data
        };

        // Send metadata to backend (backend handles file saving)
        const metadataResponse = await fetch("/api/orb/api/save-pdf-metadata/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(metadataPayload),
        });

        if (!metadataResponse.ok) {
          const errorText = await metadataResponse.text();
          throw new Error(`Failed to save PDF metadata: ${metadataResponse.status} - ${errorText}`);
        }

        const result = await metadataResponse.json();
        console.log("PDF saved successfully:", result);

        // After successful PDF saving and metadata update, update the database for print status
        await updatePrintStatusInDB(serverLocalIP, printTimestamp);

        // --- CRITICAL: Clear the UI state only after successful print and DB update (Master only) ---
        setApproved([]); // Clear the approved entries state in the UI
        console.log("✅ UI state 'approved' cleared after Master's successful print and DB update.");

        alert("PDF saved and UI cleared by Master!");
      };
      reader.readAsDataURL(pdfBlob); // This triggers the onloadend function

    } catch (err) {
      console.error("Error saving PDF file or metadata:", err);
      alert("Failed to save PDF file or update print status.");
      // Do NOT clear the UI state if an error occurs during PDF saving or DB update.
    }
    //  Hide exported entries locally
    const exportedIds = JSON.parse(localStorage.getItem("exportedApprovedIds") || "[]");
    const newIds = approved.map((e) => e.id).filter((id) => !exportedIds.includes(id));
    localStorage.setItem("exportedApprovedIds", JSON.stringify([...exportedIds, ...newIds]));

    console.log("Sending entry IDs for print status update:", approved.map(entry => entry.id));
    // --- NEW: Update Database After PDF Generation ---
    await updatePrintStatusInDB(serverLocalIP, printTimestamp);
    // --- END NEW: Update Database ---

    // --- CRITICAL: Clear the UI state only after successful print and DB update (Master only) ---
    // This ensures the list is cleared only by the Master upon successful action.
    setApproved([]); // Clear the approved entries state in the UI
    console.log("✅ UI state 'approved' cleared after Master's successful print and DB update.");

    alert("PDF saved and UI cleared by Master!");
  } catch (err) {
    console.error("Error generating PDF or updating status:", err);
    alert("Failed to generate PDF or update print status.");
    // will NOT clear the UI state if an error occurs during PDF generation or DB update.
  }
};



  // this function updates print status in Database
  const updatePrintStatusInDB = async (ip, timestamp) => {
    const vesselId = sessionStorage.getItem("selectedVesselId");
    if (!vesselId) {
      console.error("Cannot update print status: No vessel ID.");
      return;
    }


    const entryIds = approved.map(entry => entry.id);

    // This is data which is sent to the backend
    const updateData = {
      entries: entryIds,
      ip: ip,
      master_print: timestamp.toISOString(), // this converts to the string for the purpose of saving in the backend 
    };

    try {
      const response = await fetch("/api/orb/api/update-print-status/", { // this is the backend endpoint(API)
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // The includes of AUTHORIZATION header.
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`${response.status} - ${errorText}`);
      }

      console.log("Print status updated successfully for entries:", entryIds);
      // Optionally, update the local 'approved' state to reflect the print status if needed elsewhere
      // This might involve refetching the data or updating the state optimistically.

    } catch (err) {
      console.error("Error updating print status in DB:", err);
      // this is to handle error appropriately by giving the "alerts"
      alert(`Failed to update print status in database: ${err.message}`);
    }
  };




  const doApprove = async (id) => {
    
    // Construct the approved_by string using the user's first_name, surname, and rank_name
    const approvedBy = `${user?.first_name || "UNKNOWN"} ${user?.surname || ""} (${user?.ran || "OFFICER"})`.trim();

    try {
      const response = await fetch(`/api/orb/api/operations/${id}/approve/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          // 'X-CSRFToken': window.csrfToken // Only CSRF is required
        },
        body: JSON.stringify({ approved_by: approvedBy }), // Send the constructed string
        // Remove Credentials : 'include' if not needed
        // credentials: 'include'  // Required for sessions
      });

      if (!response.ok) {
        const error = await response.json();
        alert(" Approve failed: " + JSON.stringify(error));
        return;
      }

      alert("Entry Approved");
      refresh();
    } catch (err) {
      console.error("Approve error:", err);
      alert("Network error: " + err.message);
    }
  };

  const doIncorrect = async (id) => {
    const user = JSON.parse(sessionStorage.getItem("currentUser"));
    // Construct the rejected_by string using the user's first_name, surname, and rank_name
    const rejectedBy = `${user?.first_name || "UNKNOWN"} ${user?.surname || ""} (${user?.rank || "OFFICER"})`.trim();

    try {
      const response = await fetch(`/api/orb/api/operations/${id}/reject/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          // 'X-CSRFToken': window.csrfToken // Only if CSRF is required
        },
        body: JSON.stringify({ rejected_by: rejectedBy }), // Send the constructed string
        // Remove credentials: 'include' if not needed
        // credentials: 'include'  // Required for session
      });

      if (!response.ok) {
        const error = await response.json();
        alert(" Reject failed: " + JSON.stringify(error));
        return;
      }

      alert(" Entry rejected");
      refresh();
    } catch (err) {
      console.error("Reject error:", err);
      alert(" Network error: " + err.message);
    }
  };


  // this function handles Chief submits entry
  const handleChiefEntry = async (entry) => {
    const payload = {
      ...entry,
      status: "Pending",
      approved_by: null,
      approved_at: new Date().toISOString(),
      created_by: chiefName,
      vessel: vesselId,
      is_deleted: false
    };

    try {
      const response = await fetch("/api/orb/api/operations/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        alert("Your entry has been saved as Pending, PLease approve it now");
        await refresh();
        window.location.reload();

      } else {
        const err = await response.json();
        alert("Save failed: " + JSON.stringify(err));
      }
    } catch (err) {
      alert("Network Error: " + err.message);
    }
  };



  //  Reuse ORBTable from CrewDashboard — same format, just change actions
  function ORBTable({ entries, onApprove, onReject }) {
    if (!entries || entries.length === 0) {
      return <p>No Entries Found.</p>;
    }

    const showActions = typeof onApprove === 'function' && typeof onReject === 'function';

    return (
      <table className="orb-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Code</th>
            <th>Item No.</th>
            <th>Record of operations/signature</th>
            {showActions && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {entries.map((entry, idx) => {
            const lines = (entry.record_of_operation || '').split('\n').filter(line => line.trim() !== '');
            const rows = entry.rows;
            const formattedDate = formatDate(entry.date);


            return lines.map((line, lineIdx) => {
              let itemNo = '';
              let showDate = false;
              let showCode = false;

              if (lineIdx === 0) {
                showDate = true;
                showCode = true;
                itemNo = entry.item_no || '';
              } else {
                switch (entry.code) {
                  case 'A':
                    if (line.startsWith('TANK(S) BALLASTED')) {
                      itemNo = '1';
                    } else if (line.includes('TANK CLEANED SINCE') || line.includes('NOT CLEANED – PREVIOUS OIL')) {
                      itemNo = '2';
                    } else if (line.startsWith('START BALLAST')) {
                      itemNo = '4.1';
                    } else if (line.includes('START') && line.includes('HRS')) {
                      itemNo = '3.1';
                    } else if (line.includes('RINSING') || line.includes('STEAMING') || line.includes('CHEMICAL')) {
                      itemNo = '3.2';
                    } else if (line.startsWith('CLEANING WATER TO')) {
                      itemNo = '3.3';

                    } else if (line.includes('BALLAST QUANTITY')) {
                      itemNo = '4.2';
                    }
                    break;

                  case 'B':
                    if ((lineIdx == 1)) {
                      itemNo = '6';
                    } else if ((lineIdx == 2)) {
                      itemNo = '7';
                    } else if (line.includes('KNOTS')) {
                      itemNo = '8';
                    } else if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
                      itemNo = '9.1';
                    } else if (line.includes('TO RECEPTION FACILITY')) {
                      itemNo = '9.2';
                    } else if (line.includes('M³')) {
                      itemNo = '10';
                    }
                    break;

                  case 'C':
                    // 11.1 is already set on first line
                    if (line.includes('M³')) {
                      itemNo = '11.2';
                    } if ((lineIdx == 2) && line.includes('M³')) {
                      itemNo = '11.3';
                    } if (line.includes('COLLECTED FROM')) {
                      itemNo = '11.4';
                    } if (line.includes('RECEPTION FACILITY')) {
                      itemNo = '12.1';
                    } else if (line.includes('TRANSFERRED TO') && line.includes('TANK')) {
                      itemNo = '12.2';
                    } else if (line.includes('INCINERATED')) {
                      itemNo = '12.3';
                    } else if (line.includes('EVAPORATED') || line.includes('DRAINED')) {
                      itemNo = '12.4';
                    }
                    break;

                  case 'D':
                    if ((lineIdx == 1) && line.startsWith('START:')) {
                      itemNo = '14';
                    } else if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
                      itemNo = '15.1';
                    } else if (line.includes('TO PORT RECEPTION FACILITIES OF')) {
                      itemNo = '15.2';
                    } else if (line.includes('TRANSFERRED TO') || line.includes('RETAINED IN TANK')) {
                      itemNo = '15.3';
                    }
                    break;

                  case 'F':
                    if (line.includes('FAILURE STARTED') || line.includes('FAILURE OF')) {
                      itemNo = '19';
                    } if ((lineIdx == 1) || line.includes('HRS')) {
                      itemNo = '20';
                    } else if (line.trim().length > 0) {
                      itemNo = '21';
                    }
                    break;

                  case 'G':
                    // 22. Time of occurrence
                    if (
                      line.toUpperCase().includes('OCCURRENCE') ||
                      line.toUpperCase().includes('TIME OF OCCURRENCE') ||
                      (line.toUpperCase().includes('TIME') &&
                        (line.includes(':') || line.includes('HRS'))) // e.g., "08:00 HRS"
                    ) {
                      itemNo = '22';
                    }
                    // 23. Position
                    else if ((lineIdx == 1) ||
                      line.toUpperCase().includes('POSITION') ||
                      line.toUpperCase().includes('PLACE OR POSITION') ||
                      // Match typical position format: digits, N/S, E/W (e.g., 12°15'N 079°30'E)
                      /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line)
                    ) {
                      itemNo = '23';
                    }
                    // 24. Quantity and type of oil
                    else if (
                      line.toUpperCase().includes('QUANTITY') ||
                      line.toUpperCase().includes('TYPE OF OIL') ||
                      (line.includes('M³') || line.includes('MT')) // Oil quantity
                    ) {
                      itemNo = '24';
                    }
                    // 25. Circumstances and remarks
                    else if (line.trim().length > 0) {
                      itemNo = '25';
                    }
                    break;

                  case 'H':
                    if (line.startsWith('PLACE:')) {
                      itemNo = '26.1';
                    } else if (line.startsWith('TIME:') ||
                      line.includes('BUNKERING START') ||
                      line.includes('BUNKERING END') ||
                      line.includes('START') ||
                      line.includes('END TIME')) {
                      itemNo = '26.2';
                    } else if (line.includes('FUEL OIL BUNKERED IN TANKS')) {
                      itemNo = '26.3';
                    } else if (line.includes('LUBE BUNKERED IN TANKS')) {
                      itemNo = '26.4';
                    }
                    break;

                  case 'I':
                    itemNo = '';
                    break;

                  default:
                    // Fallback for unknown codes
                    if (line.includes('M³') || line.includes('MT')) {
                      itemNo = '10';
                    } else if (line.startsWith('SIGNED:')) {
                      itemNo = '';
                    }
                    break;
                }
                if (line.startsWith('SIGNED:')) {
                  itemNo = '';
                }
              }

              return (
                <tr key={`${entry.id}-${lineIdx}`}>
                  <td>{showDate ? formattedDate : ''}</td>
                  <td>{showCode ? entry.code : ''}</td>
                  <td>{itemNo}</td>
                  <td style={{ whiteSpace: 'pre-line' }}>{line}</td>
                  {showActions && (
                    <td>
                      {lineIdx === 0 && entry.status === "Pending" && (
                        <>
                          <WithPermission id="PSC_P_040">
                            <Button variant="secondary" glow onClick={() => onApprove(entry.id)}>
                              Approve
                            </Button>
                          </WithPermission>
                          <WithPermission id="PSC_P_041">
                            <Button variant="secondary" onClick={() => onReject(entry.id)}>
                              Reject
                            </Button>
                          </WithPermission>
                        </>
                      )}
                    </td>
                  )}
                </tr>
              );
            });
          })}
        </tbody>
      </table>
    );
  }

  return (
    <div className="orb-theme">
      <CrewDashboard
        isChiefMode={true}
        onSubmit={handleChiefEntry}
        vesselId={vesselId}
      />

      <div onClick={e => e.stopPropagation()}></div>
      <div style={{ marginBottom: '1rem', position: 'relative', display: 'inline-block' }}>

        <div onClick={e => e.stopPropagation()}>
          <WithPermission id="PSC_P_039">
            <Button
              variant="primary"
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              style={{ padding: '10px 20px', fontSize: '16px' }}
            >
              Filter Report
            </Button>
          </WithPermission>
        </div>

        {/* <div style={{ marginBottom: '1rem', display: 'flex', gap: '10px', alignItems: 'center' }}>
  <div>
    <label>From Date:</label>
    <input
      type="date"
      value={fromDate}
      onChange={(e) => setFromDate(e.target.value)}
      style={{ marginLeft: '8px', padding: '4px' }}
    />
  
  </div>
  <div>
    <label>To Date:</label>
    <input
      type="date"
      value={toDate}
      onChange={(e) => setToDate(e.target.value)}
      style={{ marginLeft: '8px', padding: '4px' }}
    />
  </div>
  <button
    onClick={() => handleCustomDateRange(fromDate, toDate)}
    style={{
      padding: '6px 12px',
      background: '#007bff',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      cursor: 'pointer'
    }}
  >
     Load Entries
  </button>
</div> */}

        {isFilterOpen && (
          <div style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            backgroundColor: 'white',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            zIndex: 1000,
            minWidth: '200px'
          }}>
            {[
              { key: 'TM', label: 'This Month' },
              { key: '1M', label: 'Last Month' },
              { key: '6M', label: 'Last 6 Months' },
              { key: '1Y', label: 'Last Year' },
              { key: '3Y', label: 'Last 3 Years' }
            ].map(option => (
              <div
                key={option.key}
                onClick={() => {
                  handleReportPeriod(option.key);
                  setIsFilterOpen(false);
                }}
                style={{
                  padding: '10px 15px',
                  cursor: 'pointer',
                  borderBottom: '1px solid #eee',
                  display: 'flex',
                  alignItems: 'center'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#f5f5f5'}
                onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
              >
                {option.label}
              </div>
            ))}
          </div>
        )}


        {/* Close button if report is visible */}
        {isReportVisible && (
          <Button
            variant="secondary"
            onClick={() => {
              setIsReportVisible(false);
              setSelectedPeriod(null);
              setReportData([]);
            }}
            style={{ marginLeft: '10px', padding: '10px 20px', float: 'right' }}
          >
            🗙 Close Report
          </Button>
        )}
      </div>

      {isReportVisible && (
        <Card title={`Filtered Report (${selectedPeriod})`}>
          <ORBTable entries={reportData} />
        </Card>
      )}


      <WithPermission id="PSC_F_016">
        <Card title="Pending Crew Entries">
          <div style={{ overflowX: "auto" }}>
            <ORBTable
              entries={pending}
              onApprove={doApprove}
              onReject={doIncorrect}
            />
          </div>
        </Card>
      </WithPermission>

      <WithPermission id="PSC_F_017">
        <div className="orb-section-gap">
        <Card title="Approved Logbook Entries(Preview)">
          <div
            id="approved-entries"
            style={{
              fontFamily: 'Courier New, monospace',
              fontSize: '14px',
              width: '100%',
              borderCollapse: 'collapse',
              padding: '10px'
            }}
          >

            <ORBTable entries={approved} />
          </div>

          <div style={{ marginTop: 36, textAlign: "center" }}>
            <WithPermission id="PSC_P_042">
              <Button onClick={saveAsPDF} style={{ padding: '10px 20px', fontSize: '16px' }}>Save as PDF</Button>
            </WithPermission>
          </div>


          <div style={{ display: 'none' }}>
            <div id="pdf-content">
              <div style={headerStyle}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <tbody>
                    <tr>
                      <td style={{ paddingBottom: '8px' }}>
                        <strong>Name of ship</strong>
                        <div style={{ marginTop: '4px' }}>{vessel?.vesselName || "________________________"}</div>
                      </td>
                    </tr>
                    <tr>
                      <td style={{ paddingBottom: '8px' }}>
                        <strong>Distinctive number or letters</strong>
                        <div style={{ marginTop: '4px' }}>{vessel?.imoNumber || "__________"}</div>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div style={{ marginTop: '12px', fontSize: '14px', fontWeight: 'bold', textAlign: 'center' }}>
                  Machinery Space Operations
                </div>
              </div>

              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>Date</th>
                    <th style={thStyle}>Code (Letter)</th>
                    <th style={thStyle}>Item (Number)</th>
                    <th style={thStyle}>Record of operations / signature of officer in charge</th>
                  </tr>
                </thead>
                <tbody>
                  {approved.map((entry, idx) => {
                    const lines = (entry.record_of_operation || '').split('\n').filter(line => line.trim() !== '');
                    const formattedDate = formatDate(entry.date);

                    return lines.map((line, lineIdx) => {
                      let itemNo = '';
                      if (lineIdx === 0) {
                        itemNo = entry.item_no || '';
                      } else {
                        switch (entry.code) {
                          case 'A':
                            if (line.startsWith('TANK(S) BALLASTED')) {
                              itemNo = '1';
                            } else if (line.includes('TANK CLEANED SINCE') || line.includes('NOT CLEANED – PREVIOUS OIL')) {
                              itemNo = '2';
                            } else if (line.startsWith('START BALLAST')) {
                              itemNo = '4.1';
                            } else if (line.includes('START') && line.includes('HRS')) {
                              itemNo = '3.1';
                            } else if (line.startsWith('METHOD USED')) {
                              itemNo = '3.2';
                            } else if (line.startsWith('CLEANING WATER TO')) {
                              itemNo = '3.3';

                            } else if (line.includes('BALLAST QUANTITY')) {
                              itemNo = '4.2';
                            }
                            break;

                          case 'B':
                            if (
                              line.toUpperCase().includes('START') &&
                              (line.toUpperCase().includes('POSITION') ||
                                /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line))
                            ) {
                              itemNo = '6';
                            } else if (
                              line.toUpperCase().includes('END') &&
                              (line.toUpperCase().includes('POSITION') ||
                                /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line))
                            ) {
                              itemNo = '7';
                            } else if (line.includes('KNOTS')) {
                              itemNo = '8';
                            } else if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
                              itemNo = '9.1';
                            } else if (line.includes('TO RECEPTION FACILITY')) {
                              itemNo = '9.2';
                            } else if (line.includes('M³')) {
                              itemNo = '10';
                            }
                            break;

                          case 'C':
                            // 11.1 is already set on first line
                            if (line.includes('M³')) {
                              itemNo = '11.2';
                            } if (line.startsWith('RETAINED') && line.includes('M³')) {
                              itemNo = '11.3';
                            } if (line.includes('COLLECTED FROM')) {
                              itemNo = '11.4';
                            } if (line.includes('RECEPTION FACILITY')) {
                              itemNo = '12.1';
                            } else if (line.includes('TRANSFERRED TO') && line.includes('TANK')) {
                              itemNo = '12.2';
                            } else if (line.includes('INCINERATED')) {
                              itemNo = '12.3';
                            } else if (line.includes('EVAPORATED') || line.includes('DRAINED')) {
                              itemNo = '12.4';
                            }
                            break;

                          case 'D':
                            if (line.includes('START:') || line.includes('STOP:')) {
                              itemNo = '14';
                            } else if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
                              itemNo = '15.1';
                            } else if (line.includes('TO PORT RECEPTION FACILITIES OF')) {
                              itemNo = '15.2';
                            } else if (line.includes('TRANSFERRED TO') || line.includes('RETAINED IN TANK')) {
                              itemNo = '15.3';
                            }
                            break;

                          case 'F':
                            if (line.includes('FAILURE STARTED') || line.includes('FAILURE OF')) {
                              itemNo = '19';
                            } if ((idx == 1)) {
                              itemNo = '20';
                            } if (line.trim().length > 0) {
                              itemNo = '21';
                            }
                            break;

                          case 'G':
                            // 22. Time of occurrence
                            if (
                              line.toUpperCase().includes('OCCURRENCE') ||
                              line.toUpperCase().includes('TIME OF OCCURRENCE') ||
                              (line.toUpperCase().includes('TIME') &&
                                (line.includes(':') || line.includes('HRS'))) // e.g., "08:00 HRS"
                            ) {
                              itemNo = '22';
                            }
                            // 23. Position
                            else if (
                              line.toUpperCase().includes('POSITION') ||
                              line.toUpperCase().includes('PLACE OR POSITION') ||
                              // Match typical position format: digits, N/S, E/W (e.g., 12°15'N 079°30'E)
                              /(\d{1,3}°\d+'[NS])\s*(\d{1,3}°\d+'[EW])/.test(line)
                            ) {
                              itemNo = '23';
                            }
                            // 24. Quantity and type of oil
                            else if (
                              line.toUpperCase().includes('QUANTITY') ||
                              line.toUpperCase().includes('TYPE OF OIL') ||
                              (line.includes('M³') || line.includes('MT')) // Oil quantity
                            ) {
                              itemNo = '24';
                            }
                            // 25. Circumstances and remarks
                            else if (line.trim().length > 0) {
                              itemNo = '25';
                            }
                            break;

                          case 'H':
                            if (line.startsWith('PLACE:')) {
                              itemNo = '26.1';
                            } else if (line.startsWith('TIME:') ||
                              line.includes('BUNKERING START') ||
                              line.includes('BUNKERING END') ||
                              line.includes('START') ||
                              line.includes('END TIME')) {
                              itemNo = '26.2';
                            } else if (line.includes('FUEL OIL BUNKERED IN TANKS')) {
                              itemNo = '26.3';
                            } else if (line.includes('LUBE BUNKERED IN TANKS')) {
                              itemNo = '26.4';
                            }
                            break;

                          case 'I':
                            // Code I has no item numbers
                            itemNo = '';
                            break;

                          default:
                            // Fallback for unknown codes
                            if (line.includes('M³') || line.includes('MT')) {
                              itemNo = '10';
                            } else if (line.startsWith('SIGNED:')) {
                              itemNo = '';
                            }
                            break;
                        }
                        if (line.startsWith('SIGNED:')) {
                          itemNo = '';
                        }
                      }

                      return (
                        <tr key={`${entry.id}-${lineIdx}`}>
                          <td style={tdStyle}>{lineIdx === 0 ? formattedDate : ''}</td>
                          <td style={tdStyle}>{lineIdx === 0 ? entry.code : ''}</td>
                          <td style={tdStyle}>{itemNo}</td>
                          <td style={{ ...tdStyle, whiteSpace: 'pre-line' }}>{line}</td>
                        </tr>
                      );
                    });
                  })}
                </tbody>
              </table>

              <div style={footerStyle}>
                <strong>Signature of Master</strong><br></br>
                <div style={{ marginTop: '1rem', borderBottom: '1px solid #000', width: '300px', margin: '1rem auto' }}></div>
                <div style={{ fontSize: '12px', marginTop: '1rem' }} id="pdf-page-number"></div>
              </div>
            </div>
          </div>
        </Card>
        </div>
      </WithPermission>


      <AppFooter />
    </div>

  );
}
