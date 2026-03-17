// src/components/orb/forms/CodeAForm.jsx
import React from 'react';
import PositionInput from './PositionInput';
import TankSelect from './TankSelect';

export default function CodeAForm({ details, handleChange, availableTanks, formatToDateTimeLocal, errors = {} }) {
  return (
    <div className="card" style={{ width: '920px' }}>
      {/* Operation Type */}
      <div>
        <label>Operation Type *</label>
        <select value={details.operation_type || ''} onChange={e => handleChange('operation_type', e.target.value)}>
          <option value="">Select Operation</option>
          <option value="both">Cleaning & Ballasting</option>
        </select>
        {errors.operation_type && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.operation_type}</span>}
      </div>

      {/* 1. Tank(s) Ballasted */}
      {['ballasting','both'].includes(details.operation_type) && (
        <TankSelect label="1. Identity of Tank(s) Ballasted *" value={details.tank_identity || ''}
          onChange={v => handleChange('tank_identity', v)} availableTanks={availableTanks} error={errors.tank_identity} />
      )}

      {/* 2. Cleaned Since Last Oil */}
      {['cleaning','both'].includes(details.operation_type) && (
        <div>
          <label>2. Cleaned Since Last Oil Contents? *</label>
          <select value={details.cleaned_since_last || ''} onChange={e => handleChange('cleaned_since_last', e.target.value)}
            style={{ borderColor: errors.cleaned_since_last ? 'red' : '#ccc' }}>
            <option value="">Select</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
          {errors.cleaned_since_last && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.cleaned_since_last}</span>}
        </div>
      )}

      {/* 2. Previous Oil */}
      {details.cleaned_since_last === 'no' && ['cleaning','both'].includes(details.operation_type) && (
        <div>
          <label>2. Type of Previous Oil</label>
          <input type="text" value={details.previous_oil || ''} onChange={e => handleChange('previous_oil', e.target.value.toUpperCase())}
            placeholder="e.g., HFO" style={{ borderColor: errors.previous_oil ? 'red' : '#ccc' }} />
          {errors.previous_oil && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.previous_oil}</span>}
          <label>Density/Viscosity</label>
          <input type="text" value={details.oil_density || ''} onChange={e => handleChange('oil_density', e.target.value.replace(/[^0-9.]/g,''))} placeholder="e.g., 0.985 g/cm³" />
        </div>
      )}

      {/* 3.1 Cleaning Positions */}
      {['cleaning','both'].includes(details.operation_type) && (
        <>
          <PositionInput label="3.1 Start Position (Lat/Long) (When cleaning started)"
            prefix="cleaning_start" details={details} handleChange={handleChange} />
          <PositionInput label="3.1 End Position (Lat/Long) (When cleaning Completed)"
            prefix="cleaning_end" details={details} handleChange={handleChange} />
        </>
      )}

      {/* 3.2 Cleaning Method */}
      {['cleaning','both'].includes(details.operation_type) && (
        <>
          <TankSelect label="3.2 Tank(s) Cleaned *" value={details.method_tank || ''} onChange={v => handleChange('method_tank', v)}
            availableTanks={availableTanks} error={errors.method_tank} />
          <div>
            <label>3.2 Method Used *</label>
            <select value={details.cleaning_method || ''} onChange={e => { handleChange('cleaning_method', e.target.value); if (e.target.value !== 'chemical') { handleChange('chemical_name',''); handleChange('chemicals_used',''); } }}
              style={{ width:'100%', padding:'8px' }}>
              <option value="">Select Method</option>
              <option value="Rinsing">RINSING</option>
              <option value="Steaming">STEAMING</option>
              <option value="chemical">CHEMICAL</option>
            </select>
            {errors.cleaning_method && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.cleaning_method}</span>}
          </div>
          {details.cleaning_method === 'chemical' && (
            <>
              <div><label>3.2 Chemical Name *</label>
                <input type="text" value={details.chemical_name || ''} onChange={e => handleChange('chemical_name', e.target.value.toUpperCase())} placeholder="e.g., TANK CLEANER X100" />
                {errors.chemical_name && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.chemical_name}</span>}
              </div>
              <div><label>3.2 Chemicals Used (m³) *</label>
                <input type="number" step="0.01" value={details.chemicals_used || ''} onChange={e => handleChange('chemicals_used', parseFloat(e.target.value))} placeholder="e.g., 0.5" />
                {errors.chemicals_used && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.chemicals_used}</span>}
              </div>
            </>
          )}
          <TankSelect label="3.3 Transfer to Slop Tank *" value={details.transfer_tank || ''} onChange={v => handleChange('transfer_tank', v)}
            availableTanks={availableTanks} error={errors.transfer_tank} />
          <div><label>3.3 Quantity of Cleaning Water (m³) *</label>
            <input type="number" step="0.01" value={details.transfer_qty || ''} onChange={e => handleChange('transfer_qty', parseFloat(e.target.value))} placeholder="e.g., 5"
              style={{ borderColor: errors.transfer_qty ? 'red' : '#ccc' }} />
            {errors.transfer_qty && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.transfer_qty}</span>}
          </div>
        </>
      )}

      {/* 4.1 Ballast Times */}
      {['ballasting','both'].includes(details.operation_type) && (
        <>
          <div><label>4.1 Ballast Start Time *</label>
            <input type="time" value={details.ballast_start || ''} onChange={e => handleChange('ballast_start', e.target.value)}
              style={{ width:'150px', borderColor: errors.ballast_start ? 'red' : '#ccc' }} />
            {errors.ballast_start && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.ballast_start}</span>}
          </div>
          <div><label>4.1 Ballast End Time *</label>
            <input type="time" value={details.ballast_end || ''} onChange={e => handleChange('ballast_end', e.target.value)}
              min={details.ballast_start} style={{ width:'150px', borderColor: errors.ballast_end ? 'red' : '#ccc' }} />
            {errors.ballast_end && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.ballast_end}</span>}
          </div>
          <PositionInput label="4.1 Start Position (Lat/Long)" prefix="ballast_start" details={details} handleChange={handleChange} />
          <PositionInput label="4.1 End Position (Lat/Long)"   prefix="ballast_end"   details={details} handleChange={handleChange} />
          <div><label>4.2 Ballast Quantity (m³) *</label>
            <input type="number" step="0.01" value={details.ballast_qty || ''} onChange={e => handleChange('ballast_qty', parseFloat(e.target.value))} placeholder="e.g., 50"
              style={{ borderColor: errors.ballast_qty ? 'red' : '#ccc', width:'150px' }} />
            {errors.ballast_qty && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.ballast_qty}</span>}
          </div>
        </>
      )}
    </div>
  );
}
