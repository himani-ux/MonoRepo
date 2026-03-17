// src/components/orb/forms/CodeGForm.jsx
import React from 'react';
import PositionInput from './PositionInput';

export default function CodeGForm({ details, handleChange, errors = {} }) {
  return (
    <div className="card" style={{ width:'920px' }}>
      <h4>Accidental or Exceptional Discharges of Oil (Code G)</h4>

      {/* 22. Occurrence Time */}
      <div>
        <label>22. Time of Occurrence *</label>
        <input type="time" value={details.occurrence_time || ''} style={{ width:'150px', borderColor: errors.occurrence_time ? 'red':'#ccc' }}
          onChange={e => handleChange('occurrence_time', e.target.value)} required />
        {errors.occurrence_time && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.occurrence_time}</span>}
      </div>

      {/* 23A. Position Free Text */}
      <div>
        <label>23. Position *</label>
        <textarea rows="2" value={details.position_text || ''} style={{ width:'200px', borderColor: errors.position_text ? 'red':'#ccc' }}
          onChange={e => handleChange('position_text', e.target.value)} required />
        {errors.position_text && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.position_text}</span>}
      </div>

      {/* 23B. Position Lat/Lon selectors */}
      <PositionInput label="23. Position at Time of Occurrence *" prefix="position" details={details} handleChange={handleChange} error={errors.position} />

      {/* 24. Quantity */}
      <div>
        <label>24. Approximate Quantity *</label>
        <input type="number" step="0.01" value={details.quantity_m3 || ''} placeholder="Discharge Quantity from tank"
          style={{ width:'100%', borderColor: errors.quantity_m3 ? 'red':'#ccc' }}
          onChange={e => handleChange('quantity_m3', parseFloat(e.target.value))} />
        {errors.quantity_m3 && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.quantity_m3}</span>}
      </div>

      {/* 24. Oil Type */}
      <div>
        <label>24. Type of Oil *</label>
        <select value={details.oil_type || ''} style={{ width:'100%', borderColor: errors.oil_type ? 'red':'#ccc' }}
          onChange={e => handleChange('oil_type', e.target.value)}>
          <option value="">Select Oil Type</option>
          <option value="HFO">HFO (Heavy Fuel Oil)</option>
          <option value="MDO">MDO (Marine Diesel Oil)</option>
          <option value="LUB OIL">LUB OIL (Lubricating Oil)</option>
          <option value="SLUDGE">SLUDGE</option>
        </select>
        {errors.oil_type && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.oil_type}</span>}
      </div>

      {/* 25. Remarks */}
      <div>
        <label>25. Circumstances, Reasons and General Remarks *</label>
        <textarea rows="4" value={details.remarks || ''} style={{ width:'100%', borderColor: errors.remarks ? 'red':'#ccc' }}
          onChange={e => handleChange('remarks', e.target.value)} required />
        {errors.remarks && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.remarks}</span>}
      </div>
    </div>
  );
}
