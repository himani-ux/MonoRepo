// src/components/orb/forms/CodeHForm.jsx
import React from 'react';
import { Button } from './OrbUI';

/**
 * Reusable dynamic tank row list for bunkering (fuel or lube).
 */
function TankRowList({ tanks, quantities, currentContents, availableTanks, filterFn, onTankChange, onQtyChange, onContentsChange, onRemove, onAdd, maxRows = 7, tankLabel, qtyPlaceholder }) {
  const filtered = (availableTanks || []).filter(filterFn);
  return (
    <>
      {(tanks || []).map((tankId, i) => (
        <div key={i} style={{ display:'flex', gap:'10px', margin:'5px 0' }}>
          <select value={tankId || ''} onChange={e => onTankChange(i, e.target.value)} style={{ flex:1 }}>
            <option value="">Select {tankLabel}</option>
            {filtered.map(t => <option key={t.id} value={t.id}>{t.tank_name} ({t.capacity} m³)</option>)}
          </select>
          <input type="number" step="0.001" value={quantities?.[i] || ''} onChange={e => onQtyChange(i, parseFloat(e.target.value))} placeholder={qtyPlaceholder} style={{ width:'200px' }} />
          <input type="number"              value={currentContents?.[i] || ''} onChange={e => onContentsChange(i, parseFloat(e.target.value))} placeholder="Now Containing" style={{ width:'200px' }} />
          <button type="button" onClick={() => onRemove(i)} style={{ background:'#917ee4ff', color:'white', border:'none', padding:'4px 8px' }}>✖</button>
        </div>
      ))}
      {(tanks || []).length < maxRows && (
        <button type="button" variant="secondary" onClick={onAdd}>Add {tankLabel}</button>
      )}
    </>
  );
}

export default function CodeHForm({ details, handleChange, availableTanks, formatToDateTimeLocal, yesterdayDate, errors = {}, handleSubmit }) {
  const validateBunkering = () => {
    const fuelTanks = Array.isArray(details.fuel_tanks) ? details.fuel_tanks : [];
    const lubeTanks = Array.isArray(details.lube_tanks) ? details.lube_tanks : [];

    if (details.fuel_quantity || fuelTanks.length > 0) {
      if (!details.fuel_quantity || isNaN(details.fuel_quantity)) { alert('Fuel oil quantity must be entered in MT.'); return false; }
      if (!details.fuel_type) { alert('Fuel oil type must be specified.'); return false; }
      const sulfurNum = parseFloat(details.fuel_sulfur?.trim());
      if (!details.fuel_sulfur?.trim()) { alert('Please enter sulfur percentage.'); return false; }
      if (isNaN(sulfurNum)) { alert('Sulfur percentage must be a valid number.'); return false; }
      if (fuelTanks.length === 0 || fuelTanks.every(t => !t)) { alert('At least one Fuel oil TANK must be selected.'); return false; }
      if (details.lube_quantity || details.lube_type || lubeTanks.length > 0) { alert('Cannot enter fuel oil and lubricating oil in the same record.'); return false; }
      const totalEntered = (details.fuel_quantities?.reduce((s, q) => s + (q||0), 0) || 0);
      if (Math.abs(totalEntered - details.fuel_quantity) > 0.01) { alert(`Total quantity mismatch.`); return false; }
      for (let i = 0; i < fuelTanks.length; i++) {
        const tankId = fuelTanks[i]; if (!tankId) continue;
        const tank = availableTanks?.find(t => t.id === tankId); if (!tank) continue;
        const cap = parseFloat(tank.capacity) || 0, maxMT = cap * 0.9;
        const qty = parseFloat(details.fuel_quantities?.[i] || 0);
        const cur = parseFloat(details.fuel_current_contents?.[i] || 0);
        if (qty > maxMT) { alert(`"${tank.tank_name}" 90% capacity = ${maxMT.toFixed(2)} MT. You entered ${qty} MT.`); return false; }
        if (cur > cap) { alert(`"${tank.tank_name}" now containing (${cur} MT) exceeds capacity (${cap} m³).`); return false; }
        if (cur < qty) { alert(`"${tank.tank_name}" now containing (${cur} MT) can't be less than bunkered (${qty} MT).`); return false; }
      }
      const fuelDuplicates = new Set(fuelTanks.filter(Boolean)).size !== fuelTanks.filter(Boolean).length;
      if (fuelDuplicates) { alert('Cannot select the same fuel oil tank twice.'); return false; }
    }

    if (details.lube_quantity || details.lube_type || lubeTanks.length > 0) {
      if (!details.lube_quantity || isNaN(details.lube_quantity)) { alert('Lubricating oil quantity must be entered in MT.'); return false; }
      if (!details.lube_type) { alert('Lubricating oil type must be specified.'); return false; }
      if (lubeTanks.length === 0 || lubeTanks.every(t => !t)) { alert('At least one Lube oil TANK must be selected.'); return false; }
      const lubeDuplicates = new Set(lubeTanks.filter(Boolean)).size !== lubeTanks.filter(Boolean).length;
      if (lubeDuplicates) { alert('Cannot select the same lubricating oil tank twice.'); return false; }
      for (let i = 0; i < lubeTanks.length; i++) {
        const tankId = lubeTanks[i]; if (!tankId) continue;
        const tank = availableTanks?.find(t => t.id === tankId); if (!tank) continue;
        const cap = parseFloat(tank.capacity) || 0, maxMT = cap * 0.9;
        const qty = parseFloat(details.lube_quantities?.[i] || 0);
        const cur = parseFloat(details.lube_current_contents?.[i] || 0);
        if (qty > maxMT) { alert(`"${tank.tank_name}" 90% capacity = ${maxMT.toFixed(2)} MT.`); return false; }
        if (cur > cap) { alert(`"${tank.tank_name}" now containing (${cur}) exceeds capacity (${cap}).`); return false; }
        if (cur < qty) { alert(`"${tank.tank_name}" now containing (${cur}) less than bunkered (${qty}).`); return false; }
      }
      const totalEntered = (details.lube_quantities?.reduce((s, q) => s + (q||0), 0) || 0);
      if (Math.abs(totalEntered - details.lube_quantity) > 0.01) { alert('Total lube oil quantity mismatch.'); return false; }
    }
    return true;
  };

  const makeTankHandlers = (prefix) => ({
    onTankChange:    (i, v) => { const a = [...(details[`${prefix}_tanks`]||[])]; a[i]=v; handleChange(`${prefix}_tanks`, a); },
    onQtyChange:     (i, v) => { const a = [...(details[`${prefix}_quantities`]||[])]; a[i]=v; handleChange(`${prefix}_quantities`, a); },
    onContentsChange:(i, v) => { const a = [...(details[`${prefix}_current_contents`]||[])]; a[i]=v; handleChange(`${prefix}_current_contents`, a); },
    onRemove:        (i)    => {
      handleChange(`${prefix}_tanks`,            (details[`${prefix}_tanks`]||[]).filter((_,j)=>j!==i));
      handleChange(`${prefix}_quantities`,       (details[`${prefix}_quantities`]||[]).filter((_,j)=>j!==i));
      handleChange(`${prefix}_current_contents`, (details[`${prefix}_current_contents`]||[]).filter((_,j)=>j!==i));
    },
    onAdd: () => {
      handleChange(`${prefix}_tanks`,            [...(details[`${prefix}_tanks`]||[]), '']);
      handleChange(`${prefix}_quantities`,       [...(details[`${prefix}_quantities`]||[]), 0]);
      handleChange(`${prefix}_current_contents`, [...(details[`${prefix}_current_contents`]||[]), 0]);
    },
  });

  return (
    <div className="card" style={{ width:'920px' }}>
      {/* 26.1 Place */}
      <div>
        <label>26.1 Place of Bunkering *</label>
        <input type="text" value={details.place_of_bunkering || ''}
          onChange={e => handleChange('place_of_bunkering', e.target.value.replace(/[^A-Za-z\s]/g,'').toUpperCase())} required />
      </div>

      {/* 26.2 Time */}
      <div>
        <label>26.2 Time of Bunkering *</label>
        <div>
          <label>Start Time</label>
          <input type="datetime-local" value={details.start_time || ''} max={formatToDateTimeLocal(new Date())}
            style={{ width:'200px' }} onChange={e => handleChange('start_time', e.target.value)} required />
        </div>
        <div>
          <label>End Time</label>
          <input type="datetime-local" value={details.end_time || ''} min={details.start_time} max={formatToDateTimeLocal(new Date())}
            style={{ width:'200px' }} onChange={e => handleChange('end_time', e.target.value)} required />
        </div>
        {details.start_time && details.end_time && new Date(details.end_time) < new Date(details.start_time) &&
          <p style={{ color:'red', fontSize:'0.85rem' }}>End time cannot be before start time.</p>}
        {/* {details.start_time && new Date(details.start_time) < yesterdayDate() &&
          <p style={{ color:'red', fontSize:'0.85rem' }}>Start time cannot be earlier than yesterday 00:00.</p>} */}
      </div>

      {/* Bunkering Type */}
      <div style={{ margin:'15px 0' }}>
        <label>What are you bunkering? *</label>
        <div style={{ display:'flex', gap:'20px', marginTop:'5px' }}>
          {[['fuel','Fuel Oil (26.3)'],['lube','Lubricating Oil (26.4)']].map(([val,lbl]) => (
            <label key={val} style={{ display:'flex', alignItems:'center', gap:'5px' }}>
              <input type="radio" value={val} checked={details.bunkering_type === val}
                onChange={e => handleChange('bunkering_type', e.target.value)} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
              {lbl}
            </label>
          ))}
        </div>
      </div>

      {/* 26.3 Fuel Oil */}
      {details.bunkering_type === 'fuel' && (
        <fieldset>
          <legend>26.3 Fuel Oil (one grade per entry)</legend>
          <input type="number" step="0.001" value={details.fuel_quantity || ''} onChange={e => handleChange('fuel_quantity', parseFloat(e.target.value))} placeholder="Enter Total Fuel Quantity Bunkered" style={{ gap:'20px', margin:'5px', marginTop:'6px' }} />
          <input type="text" value={details.fuel_type || ''} onChange={e => handleChange('fuel_type', e.target.value.toUpperCase())} placeholder="Enter Fuel Type as per BDN" style={{ gap:'20px', margin:'5px', marginTop:'6px' }} />
          <div style={{ position:'relative', display:'inline-block', width:'100%' }}>
            <input type="text" value={details.fuel_sulfur || ''} placeholder="e.g., 2.7" style={{ gap:'20px', margin:'5px', marginTop:'6px' }}
              onChange={e => { if (e.target.value === '' || /^\d*\.?\d*$/.test(e.target.value)) handleChange('fuel_sulfur', e.target.value); }} />
            <span style={{ position:'absolute', right:'10px', top:'50%', transform:'translateY(-50%)', color:'#999', pointerEvents:'none' }}>%S</span>
          </div>
          <TankRowList tanks={details.fuel_tanks} quantities={details.fuel_quantities} currentContents={details.fuel_current_contents}
            availableTanks={availableTanks} filterFn={t => t.tank_name?.toUpperCase().match(/F\.O|M\.D\.O|FUEL/)}
            tankLabel="Fuel Oil Tank" qtyPlaceholder="Quantity(MT)" {...makeTankHandlers('fuel')} />
        </fieldset>
      )}

      {/* 26.4 Lube Oil */}
      {details.bunkering_type === 'lube' && (
        <fieldset>
          <legend>26.4 Lubricating Oil (bulk only)</legend>
          <input type="number" step="0.001" value={details.lube_quantity || ''} onChange={e => handleChange('lube_quantity', parseFloat(e.target.value))} placeholder="Enter Total Lube Quantity Bunkered" style={{ gap:'20px', margin:'5px', marginTop:'6px' }} />
          <input type="text" value={details.lube_type || ''} onChange={e => handleChange('lube_type', e.target.value.toUpperCase())} placeholder="Enter Lube grade as per BDN" style={{ gap:'20px', margin:'5px', marginTop:'6px' }} />
          <TankRowList tanks={details.lube_tanks} quantities={details.lube_quantities} currentContents={details.lube_current_contents}
            availableTanks={availableTanks} filterFn={t => t.tank_name?.toUpperCase().match(/LUBE|L\.O|LUB/)}
            tankLabel="Lube Oil Tank" qtyPlaceholder="Quantity (MT)" {...makeTankHandlers('lube')} />
        </fieldset>
      )}

      <Button type="submit" onClick={e => { if (!validateBunkering()) e.preventDefault(); }}>Save Draft</Button>
    </div>
  );
}
