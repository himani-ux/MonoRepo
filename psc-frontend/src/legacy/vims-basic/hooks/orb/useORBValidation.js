// src/hooks/useORBValidation.js
// All per-code validation functions extracted from CrewDashboard

export const useORBValidation = ({ availableTanks, getSpecialAreaFromPosition, buildPosition }) => {

  // ─── Code A ──────────────────────────────────────────────────────────────────
  const validateCodeA = (details) => {
    if (!details.operation_type) return 'Please select Cleaning, Ballasting, or Both.';

    if (['cleaning','both'].includes(details.operation_type)) {
      if (!details.cleaned_since_last) return 'Please specify if tank was cleaned since last oil.';
      if (details.cleaned_since_last === 'no' && !details.previous_oil) return 'Please enter the type of previous oil.';

      const startFields = ['cleaning_start_lat_deg','cleaning_start_lat_min','cleaning_start_lat_dir',
                           'cleaning_start_lon_deg','cleaning_start_lon_min','cleaning_start_lon_dir'];
      const endFields   = ['cleaning_end_lat_deg','cleaning_end_lat_min','cleaning_end_lat_dir',
                           'cleaning_end_lon_deg','cleaning_end_lon_min','cleaning_end_lon_dir'];

      if (startFields.some(f => !details[f] && details[f] !== 0))
        return 'Please enter complete Cleaning Start Position (Lat & Long).';
      if (endFields.some(f => !details[f] && details[f] !== 0))
        return 'Please enter complete Cleaning End Position (Lat & Long).';

      if (details.cleaning_start && details.cleaning_end) {
        if (new Date(details.cleaning_start) >= new Date(details.cleaning_end))
          return 'End time must be after start time.';
      }
      if (!details.cleaning_method) return 'Please select a cleaning method (Rinsing, Steaming, Chemical).';
      if (details.cleaning_method === 'chemical') {
        if (!details.chemical_name) return 'Please specify the chemical name (e.g., TANK CLEANER X100).';
        if (!details.chemicals_used || details.chemicals_used <= 0) return 'Chemical quantity must be greater than 0.';
      }
    }

    if (['ballasting','both'].includes(details.operation_type)) {
      if (!details.ballast_start) return 'Please enter ballast start time.';
      if (!details.tank_identity) return 'Please select a tank from the list.';
      if (!details.ballast_end)   return 'Please enter ballast end time.';

      const ballastStartFields = ['ballast_start_lat_deg','ballast_start_lat_min','ballast_start_lat_dir',
                                  'ballast_start_lon_deg','ballast_start_lon_min','ballast_start_lon_dir'];
      const ballastEndFields   = ['ballast_end_lat_deg','ballast_end_lat_min','ballast_end_lat_dir',
                                  'ballast_end_lon_deg','ballast_end_lon_min','ballast_end_lon_dir'];

      if (ballastStartFields.some(f => !details[f] && details[f] !== 0))
        return 'Please enter complete Ballast Start Position (Lat & Long).';
      if (ballastEndFields.some(f => !details[f] && details[f] !== 0))
        return 'Please enter complete Ballast End Position (Lat & Long).';

      if (details.ballast_start && details.ballast_end) {
        if (new Date(details.ballast_start) >= new Date(details.ballast_end))
          return 'Ballast end time must be after start time.';
      }
      if (!details.ballast_qty || details.ballast_qty <= 0) return 'Ballast quantity must be greater than 0.';

      const tank = availableTanks?.find(t => t.tank_name === details.tank_identity);
      if (tank && details.ballast_qty > tank.capacity)
        return `Ballast quantity (${details.ballast_qty} m³) exceeds tank capacity (${tank.capacity} m³).`;
    }

    if (['cleaning','both'].includes(details.operation_type)) {
      if (!details.transfer_tank) return 'Slop tank is required.';
      if (!details.transfer_qty || details.transfer_qty <= 0) return 'Transfer quantity must be greater than 0.';

      const selectedTank = availableTanks?.find(t => t.tank_name === details.transfer_tank);
      if (selectedTank) {
        const available = (parseFloat(selectedTank.capacity) || 0) - (parseFloat(selectedTank.current_content) || 0);
        if (details.transfer_qty > available)
          return `Quantity exceeds available capacity (${available.toFixed(2)} m³) of ${details.transfer_tank}.`;
      }
    }
    return null;
  };

  // ─── Code B ──────────────────────────────────────────────────────────────────
  const validateCodeB = (details, allRawEntries) => {
    const lastCodeAEntry = [...allRawEntries].reverse()
      .find(e => e.code === 'A' && e.item_no === '1');
    if (!lastCodeAEntry) return 'No previous entry for Code A.';

    const recordText = lastCodeAEntry.record_of_operation || '';
    const tankMatch  = recordText.match(/TANK\(S\) BALLASTED:\s*([^\n]+)/i);
    if (!tankMatch) return 'Could not find tank identity in previous Code A entry.';

    const norm = s => (s || '').replace(/\(FR:\d+-\d+\)/i,'').trim().toUpperCase();
    if (norm(tankMatch[1]) !== norm(details.tank_ids))
      return `Tank "${details.tank_ids}" must match the BALLASTED tank. Do you mean ${tankMatch[1].trim()} Tank`;

    if (!details.tank_ids) return 'Tank ID(s) is required.';

    const posFields = [
      ['pos_start_lat_deg','pos_start_lat_min','pos_start_lat_dir','pos_start_lon_deg','pos_start_lon_min','pos_start_lon_dir'],
      ['pos_end_lat_deg','pos_end_lat_min','pos_end_lat_dir','pos_end_lon_deg','pos_end_lon_min','pos_end_lon_dir'],
    ];
    if (posFields[0].some(f => !details[f])) return 'Position at Start is required.';
    if (posFields[1].some(f => !details[f])) return 'Position at End is required.';

    if (!details.quantity_discharged_m3 || details.quantity_discharged_m3 <= 0)
      return 'Quantity Discharged (Item 10) must be > 0 M³.';

    const tankCapacity = availableTanks?.find(t =>
      t.tank_name.toUpperCase() === (details.tank_ids || '').toUpperCase()
    )?.capacity || 0;
    if (details.quantity_discharged_m3 > tankCapacity)
      return `Discharge quantity (${details.quantity_discharged_m3} M³) exceeds tank capacity (${tankCapacity} M³).`;

    if (details.method === 'reception' && !details.reception_port?.trim())
      return 'Port name is required for reception facility (Item 9.2).';

    // Special area checks
    const posStart = buildPosition(
      details.pos_start_lat_deg, details.pos_start_lat_min, details.pos_start_lat_dir,
      details.pos_start_lon_deg, details.pos_start_lon_min, details.pos_start_lon_dir
    );
    const posEnd = buildPosition(
      details.pos_end_lat_deg, details.pos_end_lat_min, details.pos_end_lat_dir,
      details.pos_end_lon_deg, details.pos_end_lon_min, details.pos_end_lon_dir
    );
    if (posStart) {
      const area = getSpecialAreaFromPosition(posStart);
      if (area) return `Discharge not allowed in Special Area: ${area}`;
    }
    if (posEnd) {
      const area = getSpecialAreaFromPosition(posEnd);
      if (area) return `Discharge not allowed in Special Area: ${area}`;
    }
    return null;
  };

  // ─── Code C ──────────────────────────────────────────────────────────────────
  const validateCodeC = (details = {}, allRawEntries = []) => {
    const norm     = s  => (s || '').toString().trim().toUpperCase();
    const toNumber = v  => {
      if (v === null || v === undefined || v === '') return NaN;
      if (typeof v === 'number') return v;
      return parseFloat(String(v).replace(',', '.'));
    };

    const findTank = (identifier) => {
      if (!identifier) return null;
      const idNorm = norm(identifier);
      return (availableTanks || []).find(t => {
        if (!t) return false;
        if (t.id   && norm(t.id)        === idNorm) return true;
        if (t.tank_name && norm(t.tank_name) === idNorm) return true;
        if (t.tank_name && norm(t.tank_name).includes(idNorm)) return true;
        if (idNorm.includes(norm(t.tank_name || ''))) return true;
        return false;
      }) || null;
    };

    const parseRetained = (text) => {
      if (!text || typeof text !== 'string') return NaN;
      const t = text.toUpperCase();
      const patterns = [
        /RETAIN(?:ED|ING)?\s*[:]?\s*([0-9]+(?:[.,][0-9]+)?)/i,
        /([0-9]+(?:[.,][0-9]+)?)\s*(?:M(?:\u00B3|3))\s*(?:RETAIN(?:ED)?)/i,
        /([0-9]+(?:[.,][0-9]+)?)\s*(?:M(?:\u00B3|3))\s*RETAIN/i,
      ];
      for (const rx of patterns) { const m = t.match(rx); if (m?.[1]) return toNumber(m[1]); }
      const m3Regex = /([0-9]+(?:[.,][0-9]+)?)\s*(?:M(?:\u00B3|3))/gi;
      let m;
      while ((m = m3Regex.exec(t)) !== null) {
        const surr = t.slice(Math.max(0, m.index-20), m.index + m[0].length + 20);
        if (!/CAPACITY/.test(surr)) return toNumber(m[1]);
      }
      return NaN;
    };

    if (!details.operation_mode)
      return 'Please select an operation type (Weekly Update, Manual Operation, or Transfer/Disposal)';

    if (['weekly','manual'].includes(details.operation_mode)) {
      const cap = toNumber(details.sludge_tank_capacity);
      if (!Number.isFinite(cap) || cap <= 0) return 'Total capacity must be > 0';
      const before = toNumber(details.sludge_before);
      if (Number.isFinite(before)) {
        if (before < 0)   return 'Retained quantity cannot be negative';
        if (before > cap) return `Retained quantity cannot exceed tank capacity (${cap} M³)`;
      }
    }

    if (details.operation_mode === 'manual') {
      const mc = toNumber(details.manual_collection_m3);
      if (!Number.isFinite(mc) || mc < 0) return 'Manual collection must be >= 0';
      if (mc > 0 && !details.collection_source) return 'Source tank is required when manual collection > 0';
      if (details.manual_collection_m3 > details.retained_quantity)
        return `Manual Collection (${details.manual_collection_m3} M³) cannot exceed Retained Quantity (${details.retained_quantity} M³).`;
      if (details.source_tank && details.transferred_to_Tank_ids &&
          details.source_tank === details.transferred_to_Tank_ids)
        return 'Source Tank and Collection Tank cannot be the same.';
      const srcTank = availableTanks.find(t => t.tank_name === details.collection_source);
      if (srcTank) {
        if (mc > parseFloat(srcTank.capacity)) return `Manual Collection cannot exceed Source Tank capacity.`;
      }
    }

    if (details.operation_mode === 'transfer') {
      if (!details.disposal_method) return 'Please select a disposal method.';
      const method = details.disposal_method;
      let disposalQty = NaN, srcId = '';
      if (method === 'reception')   { disposalQty = toNumber(details.quantity_m3); srcId = details.source_tank; }
      if (method === 'transfer')    { disposalQty = toNumber(details.disposal_quantity_m3); srcId = details.transferred_from_tank_ids; }
      if (method === 'incineration'){ disposalQty = toNumber(details.quantity_m3); srcId = details.source_tank; }

      if (Number.isFinite(disposalQty)) {
        if (!srcId) return 'Source tank is required for disposal.';
        const srcNorm = norm(srcId);
        const weeklyEntries = (allRawEntries || []).filter(e => {
          if (!e || e.is_deleted) return false;
          if (!['Approved','Pending'].includes(e.status || 'Pending')) return false;
          if (e.code !== 'C') return false;
          if (e.details?.operation_mode === 'weekly' && e.details?.sludge_tank_id) {
            if (norm(e.details.sludge_tank_id) === srcNorm) return true;
            if (norm(e.details.sludge_tank_id).includes(srcNorm)) return true;
          }
          if (e.record_of_operation && norm(e.record_of_operation).includes(srcNorm)) return true;
          return false;
        }).sort((a,b) => new Date(b.date||b.created_at||0) - new Date(a.date||a.created_at||0));

        if (!weeklyEntries.length) return `No previous Weekly Update found for ${srcId}.`;

        const latest = weeklyEntries[0];
        let retained = latest.details?.sludge_before !== undefined
          ? toNumber(latest.details.sludge_before)
          : parseRetained(latest.record_of_operation);

        if (!Number.isFinite(retained)) return `Could not determine retained quantity from last weekly update.`;
        if (disposalQty > retained) return `Disposal quantity exceeds available sludge (${retained} m³).`;
      }

      if (method === 'reception') {
        if (!toNumber(details.quantity_m3) || toNumber(details.quantity_m3) <= 0) return 'Disposal quantity must be > 0.';
        if (!details.source_tank)  return 'Source tank required.';
        if (!details.reception_vessel?.trim()) return 'Reception vessel name is required.';
        if (!details.reception_port?.trim())   return 'Reception port name is required.';
      }
      if (method === 'transfer') {
        if (!toNumber(details.disposal_quantity_m3) || toNumber(details.disposal_quantity_m3) <= 0) return 'Quantity Transferred must be > 0.';
        if (!details.transferred_from_tank_ids) return 'Source tank required.';
        if (!details.transferred_to_Tank_ids)   return 'Destination tank required.';
        if (norm(details.transferred_from_tank_ids) === norm(details.transferred_to_Tank_ids))
          return 'Source and Destination tanks cannot be the same.';
      }
      if (method === 'incineration') {
        if (!toNumber(details.quantity_m3) || toNumber(details.quantity_m3) <= 0) return 'Incinerated quantity must be > 0.';
        if (!details.source_tank) return 'Source tank required.';
        if (!Number.isFinite(toNumber(details.incineration_duration_hours)) || toNumber(details.incineration_duration_hours) <= 0)
          return 'Incineration duration must be > 0.';
      }
      if (method === 'other') {
        if (!details.other_disposal_details?.trim()) return 'Please describe the other disposal method.';
      }
    }
    return null;
  };

  // ─── Code D ──────────────────────────────────────────────────────────────────
  const validateCodeD = (details = {}) => {
    const toNumber = v => { const n = Number(String(v||'').replace(',','.')); return Number.isFinite(n) ? n : NaN; };
    const parseTime = s => { if (!s) return NaN; const [h,m] = String(s).split(':'); return parseInt(h)*60+parseInt(m); };
    const findById  = id => (availableTanks||[]).find(t => String(t.id) === String(id)) || null;
    const findByName= n  => (availableTanks||[]).find(t => String(t.tank_name) === String(n)) || null;

    if (!details.source_tank_id) return 'Source tank is required';
    const retained = toNumber(details.source_tank_retained_m3);
    const discharged= toNumber(details.quantity_discharged_m3);
    if (Number.isFinite(retained) && retained < 0) return 'Retained quantity cannot be negative';
    if (!Number.isFinite(discharged) || discharged <= 0) return 'Quantity discharged must be > 0';
    const src = findById(details.source_tank_id);
    if (src) {
      const cap = toNumber(src.capacity);
      if (discharged > cap) return `Discharge (${discharged} m³) exceeds tank capacity (${cap} m³)`;
      if (Number.isFinite(retained) && retained > cap) return `Retained (${retained} m³) exceeds tank capacity (${cap} m³)`;
      const retCheck = Number.isFinite(retained) ? retained : 0;
      if (discharged + retCheck > cap) return `Discharge + Retained cannot exceed tank capacity (${cap} m³)`;
    }
    if (!details.start_time) return 'Start time is required';
    if (!details.stop_time)  return 'Stop time is required';
    const st = parseTime(details.start_time), et = parseTime(details.stop_time);
    if (!Number.isFinite(st)) return 'Start time is invalid';
    if (!Number.isFinite(et)) return 'Stop time is invalid';
    if (et <= st) return 'Stop time must be greater than Start time';
    if (!details.method) return 'Please select a method (15.1, 15.2, or 15.3)';

    if (['15ppm','15.1'].includes(details.method)) {
      const dirs = ['N','S'], dirl = ['E','W'];
      if (!Number.isFinite(toNumber(details.ppm_start_lat_deg)) || !Number.isFinite(toNumber(details.ppm_start_lat_min)) ||
          !dirs.includes(String(details.ppm_start_lat_dir||'').toUpperCase()) ||
          !Number.isFinite(toNumber(details.ppm_start_lon_deg)) || !Number.isFinite(toNumber(details.ppm_start_lon_min)) ||
          !dirl.includes(String(details.ppm_start_lon_dir||'').toUpperCase()))
        return 'Position at Start (lat/lon) is required for 15.1.';
      if (!Number.isFinite(toNumber(details.ppm_end_lat_deg)) || !Number.isFinite(toNumber(details.ppm_end_lat_min)) ||
          !dirs.includes(String(details.ppm_end_lat_dir||'').toUpperCase()) ||
          !Number.isFinite(toNumber(details.ppm_end_lon_deg)) || !Number.isFinite(toNumber(details.ppm_end_lon_min)) ||
          !dirl.includes(String(details.ppm_end_lon_dir||'').toUpperCase()))
        return 'Position at Stop (lat/lon) is required for 15.1.';
    }
    if (['reception','15.2'].includes(details.method)) {
      if (!details.reception_port?.trim()) return 'Port name is required for 15.2.';
    }
    if (['holding','15.3'].includes(details.method)) {
      if (!details.holding_tank_ids) return 'Destination tank is required for 15.3.';
      const destRetained = toNumber(details.holding_tank_retained_m3);
      if (!Number.isFinite(destRetained) || destRetained <= 0) return 'Retained quantity (destination) must be > 0 for 15.3.';
      const dest = findByName(details.holding_tank_ids);
      if (dest && destRetained > toNumber(dest.capacity))
        return `Retained (${destRetained} m³) exceeds destination tank capacity.`;
    }
    return null;
  };

  // ─── Code F ──────────────────────────────────────────────────────────────────
  const validateCodeF = (details) => {
    if (!details.failure_start_time) return 'Failure start time is required';
    if (details.operation_mode === 'failure') {
      if (!details.equipment_affected) return 'Equipment affected is required';
      if (!details.failure_reason?.trim()) return 'Description of failure is required';
    } else if (details.operation_mode === 'restoration') {
      if (!details.restored_time) return 'Restored time is required';
      if (!details.failure_reason?.trim()) return 'Description of restoration is required';
    }
    return null;
  };

  // ─── Code G ──────────────────────────────────────────────────────────────────
  const validateCodeG = (details) => {
    if (!details.occurrence_time) return 'Time of occurrence is required';
    if (details.quantity_m3 < 0 || details.quantity_m3 == null) return 'Quantity must be >= 0';
    if (!details.oil_type) return 'Oil type is required';
    if (!details.remarks?.trim()) return 'Circumstances and remarks are required';
    return null;
  };

  // ─── Code I ──────────────────────────────────────────────────────────────────
  const validateCodeI = (details) => {
    if (!details.remarks?.trim()) return 'Remarks are required';
    if (details.remarks.trim().length < 10) return 'Remarks must be at least 10 characters long';
    return null;
  };

  return {
    validateCodeA,
    validateCodeB,
    validateCodeC,
    validateCodeD,
    validateCodeF,
    validateCodeG,
    validateCodeI,
  };
};
