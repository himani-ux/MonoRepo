// // src/hooks/usePDFGenerator.js
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { formatDate } from "../../utils/orb/orbUtils";
import { useSavePDFMetadataMutation, useUpdatePrintStatusMutation } from "../../services/orb/orbApi";
import { getItemNumber } from "./itemNumberUtils";

function buildFallbackPdf(doc, { vesselName, imoNumber, rows, userRank, officerFullName, serverLocalIP, printTimestamp }) {
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const left = 10;
  const right = pageWidth - 10;
  const bottom = pageHeight - 10;
  let y = 15;

  const addFooter = (pageNumber) => {
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.text(`${pageNumber}`, pageWidth / 2, bottom, { align: "center" });
    doc.text(`IP: ${serverLocalIP}`, left, bottom);
    doc.text(
      printTimestamp.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase(),
      right,
      bottom,
      { align: "right" }
    );
  };

  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.text("Machinery Space Operations", left, y);
  y += 8;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.text(`Name of ship: ${vesselName || "-"}`, left, y);
  y += 6;
  doc.text(`Distinctive number: ${imoNumber || "-"}`, left, y);
  y += 6;
  doc.text(`Signed by: ${officerFullName} (${userRank || "MASTER"})`, left, y);
  y += 10;

  rows.forEach((row) => {
    const line = `${row[0] || ""}  ${row[1] || ""}  ${row[2] || ""}  ${row[3] || ""}`.trim();
    const wrappedLines = doc.splitTextToSize(line, pageWidth - 20);

    if (y + wrappedLines.length * 5 > pageHeight - 20) {
      addFooter(doc.getNumberOfPages());
      doc.addPage();
      y = 15;
    }

    doc.text(wrappedLines, left, y);
    y += wrappedLines.length * 5 + 2;
  });

  addFooter(doc.getNumberOfPages());
}

export const usePDFGenerator = () => {
  const [savePDFMetadata] = useSavePDFMetadataMutation();
  const [updatePrintStatus] = useUpdatePrintStatusMutation();

  const generatePDF = async (approved, vessel, user, vesselId, onSuccess) => {
    if (!approved || approved.length === 0) {
      alert("No entries to save");
      return;
    }

    if (!vessel || !vessel.vesselName || !vessel.imoNumber) {
      alert("Vessel details not loaded yet");
      return;
    }

    if (!user) {
      alert("User session not found. Cannot print.");
      return;
    }

    // Treat vessel master role as the primary authorization check.
    const userRank = (user?.rank || '').toUpperCase().trim();
    const userRole = (user?.role || '').toUpperCase().trim();
    const isMaster =
      userRole === 'VESSEL_MASTER' ||
      userRank === 'MASTER' ||
      userRank === 'CAPTAIN';
   
    

    if (!isMaster) {
      alert("Only the Master is authorized to print.");
      return;
    }

    console.log(`✅ Print initiated by Master (${userRank}). Proceeding with print.`);

    if (!vesselId) {
      alert("Vessel not selected. Cannot generate PDF.");
      return;
    }

    const { vesselName, imoNumber } = vessel;

    try {
      // Fetch last page number, but don't block PDF download if it fails.
      let lastPageNumber = 0;
      try {
        const lastPageResponse = await fetch(
          `/api/orb/api/get_last_page_number/?vessel_id=${vesselId}`,
          { cache: "no-store" }
        );
        const raw = await lastPageResponse.text();

        console.log("📡 RAW get_last_page_number response:", raw);

        const lastPageData = JSON.parse(raw);
        lastPageNumber = lastPageData.last_page || 0;
      } catch (error) {
        console.error("Failed to fetch last page number. Continuing with page 0.", error);
      }

      // Fetch server IP
      let serverLocalIP = 'Unknown IP';
      try {
        const ipResponse = await fetch('/api/orb/api/get-internal-ip/');
        const ipData = await ipResponse.json();
        serverLocalIP = ipData.internal_ip;
        console.log("Django Server's Local IP address:", serverLocalIP);
      } catch (err) {
        console.error("Error fetching server's local IP:", err);
        alert("Could not fetch server's local IP address. Using default value.");
      }

      const printTimestamp = new Date();
      let pdfDoc = new jsPDF("p", "mm", "a4");
      const columns = ["Date", "Code", "Item", "Record of operations/signature of officer in charge"];
      const officerFirstName = user?.first_name || "UNKNOWN";
      const officerSurname = user?.surname || "";
      const officerFullName = `${officerFirstName} ${officerSurname}`.trim();

      // Build rows
      const rows = approved.flatMap((entry) => {
        const lines = (entry.record_of_operation || "")
          .split("\n")
          .filter((l) => l.trim() !== "");
        const formattedDate = formatDate(entry.date);

        return lines.map((line, idx) => {
          const itemNo = getItemNumber(entry.code, line, idx, entry.item_no);

          return [
            idx === 0 ? formattedDate : "",
            idx === 0 ? entry.code : "",
            itemNo,
            line,
          ];
        });
      });

      try {
        autoTable(pdfDoc, {
          head: [columns],
          body: rows,
          margin: { top: 50, bottom: 30 },
          theme: "grid",
          styles: {
            font: "helvetica",
            fontSize: 10,
            cellPadding: 2,
            overflow: "linebreak",
          },
          columnStyles: { 3: { cellWidth: 100 } },
          headStyles: { fillColor: [245, 245, 245], textColor: 0, fontStyle: "bold" },
          rowPageBreak: "avoid",
          didDrawPage: () => {
            const pageWidth = pdfDoc.internal.pageSize.getWidth();
            const pageHeight = pdfDoc.internal.pageSize.getHeight();
            const currentPageInfo = pdfDoc.internal.getCurrentPageInfo?.();
            const currentPage = lastPageNumber + (currentPageInfo?.pageNumber || pdfDoc.getNumberOfPages());
            const currentDate = new Date().toLocaleDateString('en-GB', {
              day: '2-digit',
              month: 'short',
              year: 'numeric'
            }).toUpperCase().replace(/ /g, '-');
            const vesselNameForSignature = sessionStorage.getItem("selectedVesselName") || vesselName || "VESSEL_NAME_NOT_FOUND";
            const timeOptions = { hour: '2-digit', minute: '2-digit', hour12: true };
            const timeString = printTimestamp.toLocaleTimeString('en-US', timeOptions).toUpperCase();

            pdfDoc.setFont("helvetica", "normal");
            pdfDoc.setFontSize(12);
            pdfDoc.setTextColor(0, 0, 0);
            pdfDoc.text("Name of ship:", 10, 15);
            pdfDoc.text(vesselName || "__________________", 60, 15);
            pdfDoc.text("Distinctive number:", 10, 25);
            pdfDoc.text(imoNumber || "__________", 60, 25);

            pdfDoc.setFont("helvetica", "bold");
            pdfDoc.text("Machinery Space Operations", 10, 40);

            pdfDoc.setFont("helvetica", "normal");
            pdfDoc.setFontSize(10);
            pdfDoc.setTextColor(0, 0, 255);
            pdfDoc.text(`Digitally Signed by: ${officerFullName} (${userRank} OF ${vesselNameForSignature})`, pageWidth / 2, pageHeight - 25, { align: "center" });
            pdfDoc.text(`Signed on: ${printTimestamp.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase().replace(/ /g, ' ')} At ${timeString}`, pageWidth / 2, pageHeight - 20, { align: "center" });
            pdfDoc.text(`IP Address: ${serverLocalIP}`, pageWidth / 2, pageHeight - 15, { align: "center" });

            pdfDoc.setTextColor(0, 0, 0);
            pdfDoc.text(`${currentPage}`, pageWidth / 2, pageHeight - 10, { align: "center" });
            pdfDoc.text(`Date: ${currentDate}`, pageWidth - 20, 15, { align: "right" });
          },
        });
      } catch (tableError) {
        console.error("AutoTable PDF generation failed. Falling back to plain PDF.", tableError);
        pdfDoc = new jsPDF("p", "mm", "a4");
        buildFallbackPdf(pdfDoc, {
          vesselName,
          imoNumber,
          rows,
          userRank,
          officerFullName,
          serverLocalIP,
          printTimestamp,
        });
      }

      // Save PDF
      const filename = `ORB-Approved-Entries-${new Date().toISOString().split("T")[0]}.pdf`;
      pdfDoc.save(filename);

      const pdfBlob = pdfDoc.output('blob');
      const title = `Approved Logbook Entries - ${new Date().toISOString().split("T")[0]}`;
      const description = `PDF containing approved ORB entries for vessel ${vesselName} as of ${new Date().toISOString().split("T")[0]}.`;

      // Persist archive metadata as a best-effort follow-up only.
      const reader = new FileReader();
      reader.onloadend = async function () {
        try {
          const result = reader.result;
          if (typeof result !== 'string') {
            throw new Error('Failed to read generated PDF blob');
          }

          const base64String = result.split(',')[1];
          const metadataPayload = {
            filename: filename,
            title: title,
            description: description,
            created_by: user?.UserName || user?.username || 'Master',
            vessel_id: vesselId,
            pdf_data: base64String
          };

          await savePDFMetadata(metadataPayload).unwrap();
          console.log("PDF saved successfully");

          const entryIds = approved.map(entry => entry.id);
          const updateData = {
            entries: entryIds,
            ip: serverLocalIP,
            master_print: printTimestamp.toISOString(),
          };

          await updatePrintStatus(updateData).unwrap();

          console.log("🧹 Clearing exportedApprovedIds after PDF generation...");
          localStorage.setItem("exportedApprovedIds", JSON.stringify([]));
          if (onSuccess) {
            onSuccess();
          }
        } catch (err) {
          console.error("PDF downloaded, but archive/status update failed:", err);
        }
      };

      reader.readAsDataURL(pdfBlob);

    } catch (err) {
      console.error("Error generating PDF:", err);
      alert("Failed to generate PDF.");
    }
  };

  return { generatePDF };
};

//--------------------------------------------version 2 ----------------------------

// import jsPDF from "jspdf";
// import autoTable from "jspdf-autotable";
// import { formatDate } from "../../../utils/orb/orbUtils";
// import { useSavePDFMetadataMutation, useUpdatePrintStatusMutation } from "../../../services/orb/orbApi";

// export const usePDFGenerator = () => {
//   const [savePDFMetadata] = useSavePDFMetadataMutation();
//   const [updatePrintStatus] = useUpdatePrintStatusMutation();

//   const generatePDF = async (approved, vessel, user, vesselId, onSuccess) => {

//     if (!approved || approved.length === 0) {
//       alert("No entries to save");
//       return;
//     }

//     if (!vessel || !vessel.vesselName || !vessel.imoNumber) {
//       alert("Vessel details not loaded yet");
//       return;
//     }

//     if (!user) {
//       alert("User session not found. Cannot print.");
//       return;
//     }

//     const userRank = (user?.rank || user?.Rank)?.toUpperCase().trim();
//     const officerFirstName = user?.first_name || "UNKNOWN";
//     const officerSurname = user?.surname || "";
//     const officerFullName = `${officerFirstName} ${officerSurname}`.trim();

//     const isMaster = userRank === "MASTER" || userRank === "CAPTAIN";
//     if (!isMaster) {
//       alert("Only the Master is authorized to print.");
//       return;
//     }

//     const { vesselName, imoNumber } = vessel;

//     try {
//       // ✅ IMPORTANT — USE PROXY URL (OLD WORKING WAY)
//       let lastPageNumber = 0;
//       try {
//         const res = await fetch(`/api/orb/api/get_last_page_number/?vessel_id=${vesselId}`);
//         const data = await res.json();
//         lastPageNumber = data.last_page || 0;
//       } catch (err) {
//         console.error("Error fetching last page:", err);
//       }

//       let serverLocalIP = "Unknown IP";
//       const printTimestamp = new Date();

//       try {
//         const ipResponse = await fetch("/api/orb/api/get-internal-ip/");
//         const ipData = await ipResponse.json();
//         serverLocalIP = ipData.internal_ip;
//       } catch (err) {
//         console.error("Error fetching IP:", err);
//       }

//       const doc = new jsPDF("p", "mm", "a4");

//       const columns = ["Date", "Code", "Item", "Record of operations/signature of officer in charge"];

//       const rows = approved.flatMap((entry) => {
//         const lines = (entry.record_of_operation || "")
//           .split("\n")
//           .filter((l) => l.trim() !== "");

//         const formattedDate = formatDate(entry.date);

//         return lines.map((line, idx) => {

//           let itemNo = "";

//           if (idx === 0) itemNo = entry.item_no || "";
//           if (line.startsWith("SIGNED:")) itemNo = "";

//           switch (entry.code) {
//             case "A":
//               if (line.startsWith("TANK(S) BALLASTED")) itemNo = "1";
//               else if (line.includes("TANK CLEANED SINCE") || line.includes("NOT CLEANED – PREVIOUS OIL")) itemNo = "2";
//               else if (line.startsWith("START BALLAST")) itemNo = "4.1";
//               else if (line.includes("START") && line.includes("HRS")) itemNo = "3.1";
//               else if (line.includes("RINSING") || line.includes("STEAMING") || line.includes("CHEMICAL")) itemNo = "3.2";
//               else if (line.startsWith("CLEANING WATER TO")) itemNo = "3.3";
//               else if (line.includes("BALLAST QUANTITY")) itemNo = "4.2";
//               break;
//           }

//           return [
//             idx === 0 ? formattedDate : "",
//             idx === 0 ? entry.code : "",
//             itemNo,
//             line,
//           ];
//         });
//       });

//       autoTable(doc, {
//         head: [columns],
//         body: rows,
//         margin: { top: 50, bottom: 30 },
//         theme: "grid",
//         styles: { font: "times", fontSize: 10, cellPadding: 2 },
//         columnStyles: { 3: { cellWidth: 100 } },
//         didDrawPage: () => {
//           const pageWidth = doc.internal.pageSize.getWidth();
//           const pageHeight = doc.internal.pageSize.getHeight();

//           doc.setFont("courier", "normal");
//           doc.text("Name of ship:", 10, 15);
//           doc.text(vesselName || "__________________", 60, 15);

//           doc.text("Distinctive number:", 10, 25);
//           doc.text(imoNumber || "__________", 60, 25);

//           doc.setFont("times", "bold");
//           doc.text("Machinery Space Operations", 10, 40);

//           const currentPage =
//             lastPageNumber + doc.internal.getCurrentPageInfo().pageNumber;

//           doc.setFont("courier", "normal");
//           doc.setFontSize(10);

//           const vesselNameForSignature =
//             sessionStorage.getItem("selectedVesselName") ||
//             vesselName ||
//             "VESSEL_NAME_NOT_FOUND";

//           doc.setTextColor(0, 0, 255);
//           doc.text(
//             `Digitally Signed by: ${officerFullName} (${userRank} OF ${vesselNameForSignature})`,
//             pageWidth / 2,
//             pageHeight - 25,
//             { align: "center" }
//           );

//           const timeOptions = { hour: "2-digit", minute: "2-digit", hour12: true };
//           const timeString = printTimestamp
//             .toLocaleTimeString("en-US", timeOptions)
//             .toUpperCase();

//           doc.text(
//             `Signed on: ${printTimestamp
//               .toLocaleDateString("en-GB", {
//                 day: "2-digit",
//                 month: "short",
//                 year: "numeric",
//               })
//               .toUpperCase()} At ${timeString}`,
//             pageWidth / 2,
//             pageHeight - 20,
//             { align: "center" }
//           );

//           doc.text(`IP Address: ${serverLocalIP}`, pageWidth / 2, pageHeight - 15, { align: "center" });

//           doc.setTextColor(0, 0, 0);
//           doc.text(`${currentPage}`, pageWidth / 2, pageHeight - 10, { align: "center" });
//         },
//       });

//       const filename = `ORB-Approved-Entries-${new Date().toISOString().split("T")[0]}.pdf`;
//       doc.save(filename);

//       const pdfBlob = doc.output("blob");

//       const reader = new FileReader();

//       reader.onloadend = async function () {
//         const base64String = reader.result.split(",")[1];

//         const metadataPayload = {
//           filename,
//           title: filename,
//           description: filename,
//           created_by: user?.UserName || user?.username || "Master",
//           vessel_id: vesselId,
//           pdf_data: base64String,
//         };

//         await savePDFMetadata(metadataPayload).unwrap();

//         const entryIds = approved.map((entry) => entry.id);

//         await updatePrintStatus({
//           entries: entryIds,
//           ip: serverLocalIP,
//           master_print: printTimestamp.toISOString(),
//         }).unwrap();

//         const exportedIds = JSON.parse(localStorage.getItem("exportedApprovedIds") || "[]");
//         const newIds = approved.map((e) => e.id).filter((id) => !exportedIds.includes(id));
//         localStorage.setItem("exportedApprovedIds", JSON.stringify([...exportedIds, ...newIds]));

//         if (onSuccess) onSuccess();

//         alert("PDF saved and UI cleared by Master!");
//       };

//       reader.readAsDataURL(pdfBlob);

//     } catch (err) {
//       console.error("Error generating PDF:", err);
//       alert("Failed to generate PDF.");
//     }
//   };

//   return { generatePDF };
// };

// export default usePDFGenerator;
