// src/utils/orbUtils.js

// ---------- formatting ----------
export const formatDate = (isoOrDate) => {
  const d = new Date(isoOrDate);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })
    .toUpperCase()
    .replace(/ /g, "-");
};
export const formatDateTime = (isoOrDate) => {
  const d = new Date(isoOrDate);
  return d.toLocaleString("en-GB", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false
  }).toUpperCase().replace(",", "").replace(/ /g, " ");
};

export const formatPosition = (pos) => {
  if (!pos || typeof pos !== 'string') return 'UNKNOWN POSITION';

  // Ensure consistent degree symbol and spacing
  return pos
    .replace(/°/g, '°') // Normalize degree symbol
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim();
};

// ---------- helpers ----------
export const toUpperDeep = (val) => {
  if (val == null) return val;
  if (Array.isArray(val)) return val.map(toUpperDeep);
  if (typeof val === "object") {
    const out = {};
    Object.keys(val).forEach(k => { out[k] = toUpperDeep(val[k]); });
    return out;
  }
  return String(val).toUpperCase();
};

// Required items per code (minimal legal set)
export const REQUIRED = {
  A: ["1", "2", "3.1", "3.2", "3.3", "4.1", "4.2"],
  B: ["5", "6", "7", "8", /* one of 9.1 or 9.2 is required */ "10"],
  C: ["11.1", "11.2", "11.3", /* 11.4 optional */ /* one of 12.1-12.4 */],
  D: ["13", "14", /* one of 15.1–15.3 */],
  E: [/* at least one of 16,17,18 */],
  F: ["19", "20", "21"],
  G: ["22", "23", "24", "25"],
  H: ["26.1", "26.2", "26.3" /* 26.4 optional */],
  I: ["27"],
};

// Validate per code (returns error string or null)
export function validateCodePayload(code, items) {
  const i = items || {};

  const hasAny = (...keys) => keys.some(k => i[k] && String(i[k]).trim() !== "");
  const all = (keys) => keys.every(k => i[k] && String(i[k]).trim() !== "");

  switch (code) {
    // case "A": if (!all(REQUIRED.A)) return "CODE A REQUIRES 1,2,3.1,3.2,3.3,4.1,4.2"; break;
    case "B":
      if (!all(["5", "6", "7", "8", "10"]) || !hasAny("9.1", "9.2"))
        return "CODE B REQUIRES 5,6,7,8,10 AND ONE OF 9.1/9.2";
      break;
    case "C":
      if (!all(["11.1", "11.2", "11.3"]) || !hasAny("12.1", "12.2", "12.3", "12.4"))
        return "CODE C REQUIRES 11.1,11.2,11.3 AND ONE OF 12.1–12.4";
      break;
    case "D":
      if (!all(["13", "14"]) || !hasAny("15.1", "15.2", "15.3"))
        return "CODE D REQUIRES 13,14 AND ONE OF 15.1–15.3";
      break;
    case "E":
      if (!hasAny("16", "17", "18"))
        return "CODE E REQUIRES AT LEAST ONE OF 16/17/18";
      break;
    case "F": if (!all(REQUIRED.F)) return "CODE F REQUIRES 19,20,21"; break;
    case "G": if (!all(REQUIRED.G)) return "CODE G REQUIRES 22,23,24,25"; break;
    case "H": if (!all(["26.1", "26.2", "26.3"])) return "CODE H REQUIRES 26.1,26.2,26.3"; break;
    case "I": if (!all(REQUIRED.I)) return "CODE I REQUIRES 27.1"; break;
    default: return "UNKNOWN CODE";
  }
  return null;
}






// ✅ Put this at the top of your buildItemRows.js (or utils.js if shared)
const formatTankWithFrames = (tankName, availableTanks) => {
  const tank = availableTanks.find(t => t.tank_name === tankName);
  if (!tank) return tankName || '';
  const { frame_from, frame_to } = tank;
  return `${tank.tank_name} ${frame_from && frame_to ? `(FR:${frame_from}-${frame_to})` : ''}`;
};


const formatORBDate = (isoString) => {
  if (!isoString) return 'UNKNOWN TIME';

  const d = new Date(isoString);
  if (isNaN(d.getTime())) return 'INVALID DATE';

  const day = String(d.getDate()).padStart(2, '0');
  const month = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
    'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'][d.getMonth()];
  const year = d.getFullYear();
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');

  return `${day}-${month}-${year} : ${hours}:${minutes} HRS`;
};


const formatToDisplay = (time) => {
  if (!time) return '';
  const [hours, minutes] = time.split(':');
  return `${hours}:${minutes} HRS`;
};


// const user = sessionStorage.getItem("currentUser")
//   ? JSON.parse(sessionStorage.getItem("currentUser"))
//   : null;

// const officerName = user?.UserName || "OFFICER-IN-CHARGE";
// const officerRank = user?.Rank || "RANK";

// Build display rows (ItemNo, Text) in legal order + SIGNED line
// Build display rows (ItemNo, Text) in legal order + SIGNED line
export function buildItemRows(code, items, dateISO, officer, availableTanks = []) {
  const rows = [];
  const i = items || {};

  // The debug log shows first_name, surname, rank_name
  const officerFirstName = officer?.first_name || "OFFICER-IN-CHARGE";
  const officerSurname = officer?.surname || ""; // Can be empty if not available
  const officerFullName = `${officerFirstName} ${officerSurname}`.trim(); // Combine for full name
  const officerRank = officer?.rank_name || "RANK"; // Use rank_name

  // console.log("DEBUG: buildItemRows - officer param:", officer); // Debug log
  // console.log(`DEBUG: buildItemRows - Extracted Name: '${officerFullName}', Rank: '${officerRank}'`); // Debug log


  const formatFrameRange = (from, to) => {
    if (from != null && to != null) {
      return ` (FR:${from}-${to})`;
    }
    return '';
  };



  // ✅ Add function to safely push rows
  const add = (no, txt) => {
    if (txt && String(txt).trim() !== "") {
      rows.push({ item: no, value: String(txt) });
    }
  };

  switch (code) {
    case "A":

      if (i.operation_type === "ballasting" || i.operation_type === "both") {
        // 1. Tank Identity
        if (i.tank_identity) {
          add("1", `TANK(S) BALLASTED: ${formatTankWithFrames(i.tank_identity, availableTanks)}`);
        }
      }
      if (i.operation_type === "cleaning" || i.operation_type === "both") {

        // 2. Cleaned Since Last Oil
        if (i.cleaned_since_last === "yes") {
          add("2", "TANK CLEANED SINCE LAST OIL CONTENTS");
        } else if (i.cleaned_since_last === "no") {
          add("2", `NOT CLEANED – PREVIOUS OIL: ${i.previous_oil}, DENSITY/VISCOSITY: ${i.oil_density}`);
        }


        // 3.1 Cleaning Start
        if (i.cleaning_start_lat_deg && i.cleaning_start_lon_deg) {
          const startPos = `${i.cleaning_start_lat_deg}°${i.cleaning_start_lat_min}'${i.cleaning_start_lat_dir} x ${i.cleaning_start_lon_deg}°${i.cleaning_start_lon_min}'${i.cleaning_start_lon_dir}`;
          add("3.1", `${startPos} - START ${i.cleaning_start_time || ''}HRS`);
        }

        // 3.1 Cleaning End
        if (i.cleaning_end_lat_deg && i.cleaning_end_lon_deg) {
          const endPos = `${i.cleaning_end_lat_deg}°${i.cleaning_end_lat_min}'${i.cleaning_end_lat_dir} x ${i.cleaning_end_lon_deg}°${i.cleaning_end_lon_min}'${i.cleaning_end_lon_dir}`;
          add("  ", `${endPos} - STOP ${i.cleaning_end_time || ''}HRS`);
        }

        // 3.2 Method Used
        if (i.method_tank && i.cleaning_method) {
          let methodText = `${formatTankWithFrames(i.method_tank, availableTanks)}, ${i.cleaning_method}`;
          if (i.cleaning_method === "chemical" && i.chemical_name && i.chemicals_used) {
            methodText += `, CHEMICAL USED: ${i.chemical_name}, QUANTITY: ${i.chemicals_used} m³`;
          } else if (i.chemicals_used) {
            methodText += `, CHEMICALS: ${i.chemicals_used} m³`;
          }
          add("3.2", methodText);
        }

        // 3.3 Transfer to Slop
        if (i.transfer_tank && i.transfer_qty) {
          add("3.3", `CLEANING WATER TO ${formatTankWithFrames(i.transfer_tank, availableTanks)}, QUANTITY ${i.transfer_qty} m³`);
        }
      }

      // 4.1 Ballast Start
      if (i.ballast_start_lat_deg && i.ballast_start_lon_deg) {
        const startPos = `${i.ballast_start_lat_deg}°${i.ballast_start_lat_min}'${i.ballast_start_lat_dir} x ${i.ballast_start_lon_deg}°${i.ballast_start_lon_min}'${i.ballast_start_lon_dir}`;
        add("4.1", `START BALLAST ${startPos} AT ${i.ballast_start || ''} HRS`);
      }

      // 4.1 Ballast End
      if (i.ballast_end_lat_deg && i.ballast_end_lon_deg) {
        const endPos = `${i.ballast_end_lat_deg}°${i.ballast_end_lat_min}'${i.ballast_end_lat_dir} x ${i.ballast_end_lon_deg}°${i.ballast_end_lon_min}'${i.ballast_end_lon_dir}`;
        add(" ", `END BALLAST ${endPos} AT ${i.ballast_end || ''} HRS`);
      }

      // 4.2 Ballast Quantity

      if (i.cleaned_since_last === "no") {
        if (i.ballast_qty != null && i.ballast_qty !== "") {
          add("4.2", `BALLAST QUANTITY: ${parseFloat(i.ballast_qty).toFixed(2)} M³`);
        }
      }

      add("", `SIGNED: (${officerFullName.toUpperCase()}, ${officerRank.toUpperCase()}) ${formatDate(dateISO)}`);
      break;

    case "B":
      // 5. Tank ID(s)
      if (i.tank_ids) {
        add("5", `${formatTankWithFrames(i.tank_ids, availableTanks)}`);
      }

      // 6. Position at Start (with time if available)
      const hasStartPos = i.pos_start_lat_deg && i.pos_start_lat_min && i.pos_start_lat_dir &&
        i.pos_start_lon_deg && i.pos_start_lon_min && i.pos_start_lon_dir;
      const hasStartTime = i.start_time;

      if (hasStartPos) {
        const startPos = `${i.pos_start_lat_deg}°${i.pos_start_lat_min}'${i.pos_start_lat_dir} x ${i.pos_start_lon_deg}°${i.pos_start_lon_min}'${i.pos_start_lon_dir}`;
        const startLabel = hasStartTime ? `${startPos} - START ${i.start_time}` : startPos;
        add("6", startLabel);
      }

      // 7. Position at End (with time if available)
      const hasEndPos = i.pos_end_lat_deg && i.pos_end_lat_min && i.pos_end_lat_dir &&
        i.pos_end_lon_deg && i.pos_end_lon_min && i.pos_end_lon_dir;
      const hasEndTime = i.end_time;

      if (hasEndPos) {
        const endPos = `${i.pos_end_lat_deg}°${i.pos_end_lat_min}'${i.pos_end_lat_dir} x ${i.pos_end_lon_deg}°${i.pos_end_lon_min}'${i.pos_end_lon_dir}`;
        const endLabel = hasEndTime ? `${endPos} - STOP ${i.end_time}` : endPos;
        add("6", endLabel);
      }

      // 8. Ship's Speed(s)
      // if (i.ship_speeds) {
      //   add("8", `${i.ship_speeds} KNOTS`);
      // }

      // // 9. Method of Discharge
      // if (i.method === '15ppm') {
      //   add("9.1", "THROUGH 15 PPM EQUIPMENT");
      // }
      if (i.method === 'reception' && i.reception_port) {
        add("9.2", `TO RECEPTION FACILITY AT ${i.reception_port}`);
      }

      // 10. Quantity Discharged
      if (i.quantity_discharged_m3 || i.quantity_discharged_m3 === 0) {
        add("10", `${i.quantity_discharged_m3} M³`);
      }

      //  SIGNED line
      add("", `SIGNED: (${officerFullName.toUpperCase()}, ${officerRank.toUpperCase()}) ${formatDate(dateISO)}`);
      break;


    case "C":
      // 11.1 Sludge Tank
      if (i.sludge_tank_id) {
        add("11.1", `${formatTankWithFrames(i.sludge_tank_id, availableTanks)}`);
      }

      // 11.2 Total Capacity
      if (i.sludge_tank_capacity) {
        add("11.2", `${i.sludge_tank_capacity} M³`);
      }

      // 11.3 Sludge Before Collection
      if (i.sludge_before) {
        add("11.3", `${i.sludge_before} M³`);
      }
      // 11.4 Manual Collection
      if (i.manual_collection_m3 && i.collection_source) {
        let sourceTankDisplay;
        if (i.collection_source === 'OTHER' && i.custom_collection_source) {
          // Use the manually entered tank name if "Other" was selected
          sourceTankDisplay = i.custom_collection_source.trim();
        } else {
          // Use the tank name from the dropdown and format it with frames
          sourceTankDisplay = formatTankWithFrames(i.collection_source, availableTanks);
        }
        // Add the formatted line to the output array/string
        add("11.4", `${i.manual_collection_m3} M³ COLLECTED FROM ${sourceTankDisplay}`);
      }
      // 12.1 To Reception Facility
      if (i.disposal_method === 'reception' && i.reception_port) {
        add("12.1", `${i.quantity_m3} M³ SLUDGE FROM ${formatTankWithFrames(i.source_tank, availableTanks)}  ${i.retained_quantity} M³ RETAINED, TO "${i.reception_vessel}" DURING PORT STAY AT ${i.reception_port} RECEIPT NO: ${i.reception_receipt_no || 'N/A'}`);
      }

      // 12.2 Transfer to Another Tank
      if (i.disposal_method === 'transfer' && i.transferred_from_tank_ids && i.disposal_quantity_m3) {
        add(
          "12.2",
          `${i.disposal_quantity_m3} M³ SLUDGE TRANSFERRED FROM ${formatTankWithFrames(i.transferred_from_tank_ids, availableTanks)}, ${i.retained_quantity || 'UNKNOWN'} M³ RETAINED TO ${formatTankWithFrames(i.transferred_to_Tank_ids, availableTanks)}`
        );
      }

      if (i.disposal_method === 'incineration' && i.incineration_duration_hours) {
        add(
          "12.3",
          `${i.quantity_m3 || 'Unknown'} M³ SLUDGE FROM ${formatTankWithFrames(i.source_tank, availableTanks)} , ${i.retained_quantity || '0'} M³ RETAINED`
        );
        add("  ", `BURNED IN INCINERATOR FOR ${i.incineration_duration_hours} HOURS`);
      }

      //  12.4 Other Disposal
      if (i.disposal_method === 'other' && i.other_disposal_details) {
        add("12.4", `OTHER DISPOSAL: ${i.other_disposal_details}`);
      }



      // SIGNED
      add("", `SIGNED: (${officerFullName.toUpperCase()}, ${officerRank.toUpperCase()}) ${formatDate(dateISO)}`);
      break;




    case "D":
      const sourceTank = availableTanks.find(t => t.id === i.source_tank_id);
      const sourceTankName = sourceTank?.tank_name || 'UNKNOWN TANK';
      const frameRange = sourceTank ? `(FR:${sourceTank.frame_from}-${sourceTank.frame_to})` : '';
      const capacity = sourceTank?.capacity || 0;

      add(
        "13",
        `${i.quantity_discharged_m3} M³ BILGE WATER FROM ${sourceTankName} ${frameRange} OF CAPACITY ${capacity} M³, ${i.source_tank_retained_m3} M³ RETAINED IN TANK`
      );
      // 14. Time
      if (i.method === 'reception' || i.method === 'holding')
        add("14", `START: ${formatToDisplay(i.start_time)}, STOP: ${formatToDisplay(i.stop_time)}`);
      if (i.method === '15ppm')
        add("14", `START: ${formatToDisplay(i.start_time)}, STOP: ${formatToDisplay(i.stop_time)} / UTC:-  START: ${formatToDisplay(i.ppm_start_time)}, STOP: ${formatToDisplay(i.ppm_stop_time)}`)

      // 15.1 Through 15 ppm Equipment
      if (i.method === '15ppm') {
        add("15.1", "THROUGH 15 PPM EQUIPMENT");

        // Format: 49°56'N, 30°00'E
        const startLat = `${i.ppm_start_lat_deg}°${i.ppm_start_lat_min}'${i.ppm_start_lat_dir}`;
        const startLon = `${i.ppm_start_lon_deg}°${i.ppm_start_lon_min}'${i.ppm_start_lon_dir}`;
        add("", `POSITION AT START: ${startLat}, ${startLon}`);

        const endLat = `${i.ppm_end_lat_deg}°${i.ppm_end_lat_min}'${i.ppm_end_lat_dir}`;
        const endLon = `${i.ppm_end_lon_deg}°${i.ppm_end_lon_min}'${i.ppm_end_lon_dir}`;
        add("", `POSITION AT STOP: ${endLat}, ${endLon}`);
      } else if (i.method === 'reception') {
        add("15.2", `TO PORT RECEPTION FACILITIES OF ${i.reception_port} RECEIPT NO:${i.reception_receipt_no || 'N/A'}`);
      } else if (i.method === 'holding') {
        add(
          "15.3",
          `TRANSFERRED TO ${i.holding_tank_ids}, ${i.holding_tank_retained_m3} M³ RETAINED IN TANK`
        );
      }
      // SIGNED
      add("", `SIGNED: (${officerFullName.toUpperCase()}, ${officerRank.toUpperCase()}) ${formatDate(dateISO)}`);
      break;


    case "E":
      if (i["16"]) add("16", i["16"]);
      if (i["17"]) add("17", i["17"]);
      if (i["18"]) add("18", i["18"]);
      break;

    case "F": {
      // Use the 'i' object directly (which is 'items' or an empty object)
      const { operation_mode, failure_start_time, restored_time, equipment_affected, failure_reason } = i || {};

      // Helper to extract time from a datetime string (e.g., "2026-01-27T16:04")
      const extractTime = (dateTimeStr) => {
        if (!dateTimeStr) return "";
        try {
          const dt = new Date(dateTimeStr);
          if (isNaN(dt.getTime())) return dateTimeStr; // Return original if invalid
          const hours = String(dt.getHours()).padStart(2, '0');
          const minutes = String(dt.getMinutes()).padStart(2, '0');
          return `${hours}:${minutes}`;
        } catch (e) {
          // console.error("Error extracting time:", e);
          return dateTimeStr; // Fallback to raw string
        }
      };

      let item19, item20, item21;

      if (operation_mode === 'failure') {
        // ✅ Item 19: Time of system failure (from time input)
        item19 = failure_start_time || "UNKNOWN TIME";

        // ✅ Item 20: Directly the user's input from "Action Taken/Equipment Affected"
        // This is free text, not a time. Do NOT modify it.
        item20 = equipment_affected || "NO ACTION TAKEN";

        // ✅ Item 21: Directly the user's input from "Reasons for failure"
        item21 = failure_reason || "NO REASON PROVIDED";
      } else if (operation_mode === 'restoration') {
        // ✅ Item 19: Time of system failure (extract time from datetime-local input)
        item19 = extractTime(failure_start_time) || "UNKNOWN TIME";

        // ✅ Item 20: Time when system has been made operational (from time input)
        item20 = restored_time || "UNKNOWN TIME";

        // ✅ Item 21: Directly the user's input from "Reasons for failure"
        item21 = failure_reason || "NO REASON PROVIDED";
      } else {
        // Fallback
        item19 = "UNKNOWN TIME";
        item20 = "UNKNOWN";
        item21 = "DATA MISSING";
      }

      // Add the lines exactly as they should appear in the ORB record.
      add("19", item19);
      add("20", item20);
      add("21", item21);

      // SIGNED line
      add("", `SIGNED: (${officerFullName.toUpperCase()}, ${officerRank.toUpperCase()}) ${formatDate(dateISO)}`);

      break;
    }

    case "G":
      add("22", (`${i.occurrence_time} HRS`));

      // Position (Lat/Lon + Free Text)
      if (
        i.position_lat_deg &&
        i.position_lat_min &&
        i.position_lat_dir &&
        i.position_lon_deg &&
        i.position_lon_min &&
        i.position_lon_dir
      ) {
        const lat = `${i.position_lat_deg}°${i.position_lat_min}'${i.position_lat_dir}`;
        const lon = `${i.position_lon_deg}°${i.position_lon_min}'${i.position_lon_dir}`;
        let position = `${lat} x ${lon}`;

        if (i.position_text && i.position_text.trim() !== "") {
          position += ` (${i.position_text.trim()})`;
        }

        add("23", position);
      } else if (i.position_text && i.position_text.trim() !== "") {
        add("23", i.position_text.trim());
      }

      // 24. Quantity and Type
      if (i.quantity_m3 > 0 && i.oil_type) {
        add("24", `${i.quantity_m3} M³ OF ${i.oil_type}`);
      }
      if (i.quantity_m3 === 0) {
        add("24", `TRACES OF ${i.oil_type}`);
      }

      add("25", i.remarks);

      add("", `SIGNED: (${officerFullName.toUpperCase()}, ${officerRank.toUpperCase()}) ${formatDate(dateISO)}`);

      break; // ✅ Add this break statement here

    case "H":
      if (i.place_of_bunkering) {
        add("26.1", i.place_of_bunkering.toUpperCase());
      }

      const startDisplay = i.start_time ? formatORBDate(i.start_time) : 'UNKNOWN TIME';
      const endDisplay = i.end_time ? formatORBDate(i.end_time) : 'UNKNOWN TIME';
      add("26.2", `START: ${startDisplay}, STOP: ${endDisplay}`);

      // 26.3 Fuel Oil
      if (i.fuel_quantity && i.fuel_type && i.fuel_tanks && i.fuel_tanks.length > 0) {
        const total = parseFloat(i.fuel_quantity);

        // Main record
        add("26.3", `${total} MT OF ${i.fuel_type.toUpperCase()}  ${i.fuel_sulfur || '0.40'} %S FUEL OIL BUNKERED IN TANKS`);

        i.fuel_tanks.forEach((id, index) => {
          const tank = availableTanks?.find(t => t.id === id);
          const qty = i.fuel_quantities?.[index] || 0;
          const currentContent = i.fuel_current_contents?.[index] || 0;

          if (!tank) {
            add("", `${qty} MT ADDED TO UNKNOWN TANK`);
            return;
          }

          const tankName = tank.tank_name.toUpperCase();

          //  Format frame range
          const frameRange = tank.frame_from != null && tank.frame_to != null
            ? ` (FR:${tank.frame_from}-${tank.frame_to})`
            : '';

          const nowContentText = currentContent > 0 ? ` NOW CONTAINING ${currentContent} MT` : '';

          //  Combine all parts
          add("", `${qty} MT ADDED TO ${tankName}${frameRange}${nowContentText}`);
        });
      }

      // 26.4 Lubricating Oil
      if (i.lube_quantity && i.lube_type && i.lube_tanks && i.lube_tanks.length > 0) {
        add("26.4", `${i.lube_quantity} MT OF ${i.lube_type.toUpperCase()} LUBE BUNKERED IN TANKS`);

        i.lube_tanks.forEach((id, index) => {
          const tank = availableTanks?.find(t => t.id === id);
          const qty = i.lube_quantities?.[index] || 0;
          const currentContent = i.lube_current_contents?.[index] || 0;

          if (!tank) {
            add("", `${qty} MT ADDED TO UNKNOWN TANK`);
            return;
          }

          const tankName = tank.tank_name.toUpperCase();
          const frameRange = tank.frame_from != null && tank.frame_to != null
            ? ` (FR:${tank.frame_from}-${tank.frame_to})`
            : '';
          const nowContentText = currentContent > 0 ? ` NOW CONTAINING ${currentContent} MT` : '';

          add("", `${qty} MT ADDED TO ${tankName}${frameRange}${nowContentText}`);
        });
      }
      // Signature line
      add("", `SIGNED: (${officerFullName.toUpperCase()}, ${officerRank.toUpperCase()}) ${formatDate(dateISO)}`);
      break;


    case "I":


      // Add the user's remarks (split into lines if needed)
      if (i.remarks) {
        const lines = i.remarks.split('\n');
        lines.forEach(line => {
          if (line.trim()) {
            add("", line.trim().toUpperCase());
          }
        });
      }

      // Add signature
      add("", `SIGNED: (${officerFullName.toUpperCase()}, ${officerRank.toUpperCase()}) ${formatDate(dateISO)}`);
      break;

    default:
      add("", "OPERATION RECORDED");
      break;
  }

  return rows;
}
// this is JSON blob to store all the operations in uppercase 
export function toRecordJSON(code, items, officer, status = "PENDING") {
  const upperItems = toUpperDeep(items);
  return {
    code: code.toUpperCase(),
    items: upperItems,
    status: status.toUpperCase(),
    signed: `SIGNED: ${officer.toUpperCase()}`,
    date: formatDate(new Date().toISOString()),
  };
}


export const groupEntriesByLogicalORBEntry = (entries) => {
  const grouped = [];
  let currentGroup = [];

  // Sort by date
  const sorted = [...entries]
    .filter(e => !e.is_deleted)
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  for (const entry of sorted) {
    // Only process H code entries
    if (entry.code !== 'H') {
      if (currentGroup.length > 0) {
        grouped.push(currentGroup);
        currentGroup = [];
      }
      grouped.push([entry]);
      continue;
    }

    // If it's 26.1, start new group
    if (entry.item_no === '26.1' || entry.item_no === 26.1) {
      if (currentGroup.length > 0) {
        grouped.push(currentGroup);
      }
      currentGroup = [entry];
    }
    // If it's continuation line, add to current group
    else if (['26.2', '26.3', '26.4'].includes(entry.item_no) ||
      !entry.item_no) {
      if (currentGroup.length > 0) {
        currentGroup.push(entry);
      } else {
        currentGroup = [entry]; // Fallback
      }
    } else {
      if (currentGroup.length > 0) {
        grouped.push(currentGroup);
      }
      currentGroup = [entry];
    }
  }

  if (currentGroup.length > 0) {
    grouped.push(currentGroup);
  }

  //  Return flat array of all entries
  return grouped.flat();
};