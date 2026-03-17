// src/components/orb/forms/CodeDForm.jsx
import React from 'react';
import PositionInput from './PositionInput';
import TankSelect from './TankSelect';

export default function CodeDForm({ details, handleChange, availableTanks, errors = {} }) {
  return (
    <div className="card" style={{ width:'920px' }}>
      <h4>Bilge Water Disposal (Code D)</h4>

      {/* 13. Source Tank */}
      <div>
        <label>13. Source Tank *</label>
        <select value={details.source_tank_id || ''}
          onChange={e => {
            const tank = availableTanks.find(t => t.id === e.target.value);
            handleChange('source_tank_id', e.target.value);
            handleChange('source_tank_capacity', tank?.capacity || 0);
            handleChange('source_tank_retained_m3', tank?.capacity || 0);
            handleChange('quantity_discharged_m3', 0);
          }}
          style={{ width:'100%', borderColor: errors.source_tank_id ? 'red' : '#ccc' }}>
          <option value="">Select Bilge Holding Tank</option>
          {availableTanks.map(tank => (
            <option key={tank.id} value={tank.id}>
              {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to}, {tank.capacity} m³)
            </option>
          ))}
        </select>
        {errors.source_tank_id && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.source_tank_id}</span>}
      </div>

      {/* 13.2 Retained */}
      <div>
        <label>13. Retained in Source Tank (m³) *</label>
        <input type="number" step="0.01" value={details.source_tank_retained_m3 || ''} placeholder="e.g., 5"
          style={{ width:'100%', borderColor: errors.source_tank_retained_m3 ? 'red' : '#ccc' }}
          onChange={e => handleChange('source_tank_retained_m3', parseFloat(e.target.value))} />
        {errors.source_tank_retained_m3 && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.source_tank_retained_m3}</span>}
      </div>

      {/* Discharge quantity with auto-retained calc */}
      <input type="number" step="0.01" value={details.quantity_discharged_m3 || ''} placeholder="Enter Disposal Quantity"
        style={{ width:'100%', borderColor: errors.quantity_discharged_m3 ? 'red' : '#ccc' }}
        onChange={e => {
          const discharged = parseFloat(e.target.value) || 0;
          const tank = availableTanks.find(t => t.id === details.source_tank_id);
          const capacity = tank?.capacity || 0;
          handleChange('quantity_discharged_m3', discharged);
          handleChange('source_tank_retained_m3', Math.max(0, capacity - discharged));
        }} />

      {/* 14. Start/Stop Time */}
      <div>
        <label>14. Start Time *</label>
        <input type="time" value={details.start_time || ''} style={{ width:'150px', borderColor: errors.start_time ? 'red':'#ccc' }}
          onChange={e => handleChange('start_time', e.target.value)} />
        {errors.start_time && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.start_time}</span>}
      </div>
      <div>
        <label>14. Stop Time *</label>
        <input type="time" value={details.stop_time || ''} style={{ width:'150px', borderColor: errors.stop_time ? 'red':'#ccc' }}
          onChange={e => handleChange('stop_time', e.target.value)} />
        {errors.stop_time && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.stop_time}</span>}
      </div>

      {/* 15.1 Through 15 ppm Equipment */}
      <div>
        <label>
          <input type="radio" checked={details.method === '15ppm'} onChange={() => handleChange('method','15ppm')} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
          {' '}15.1 Through 15 ppm Equipment
        </label>
        {details.method === '15ppm' && (
          <div style={{ marginLeft:'24px' }}>
            <PositionInput label="Position at Start *" prefix="ppm_start" details={details} handleChange={handleChange} />
            <PositionInput label="Position at Stop *"  prefix="ppm_end"   details={details} handleChange={handleChange} />
            <div style={{ marginTop:'16px', display:'grid', gap:'12px' }}>
              <div>
                <label>14. Start Time (UTC) *</label>
                <input type="time" value={details.ppm_start_time || ''} onChange={e => handleChange('ppm_start_time', e.target.value)}
                  style={{ width:'150px', padding:'6px', border:'1px solid #ccc', borderRadius:'4px' }} required />
              </div>
              <div>
                <label>14. Stop Time (UTC) *</label>
                <input type="time" value={details.ppm_stop_time || ''} onChange={e => handleChange('ppm_stop_time', e.target.value)}
                  style={{ width:'150px', padding:'6px', border:'1px solid #ccc', borderRadius:'4px' }} required />
              </div>
            </div>
            {details.ppm_start_time && details.ppm_stop_time &&
              new Date(`2000-01-01T${details.ppm_stop_time}`) < new Date(`2000-01-01T${details.ppm_start_time}`) && (
              <span style={{ color:'red', fontSize:'12px', display:'block', marginLeft:'24px' }}>
                ❌ Stop time cannot be before start time.
              </span>
            )}
          </div>
        )}
      </div>

      {/* 15.2 Reception */}
      <div>
        <label>
          <input type="radio" checked={details.method === 'reception'} onChange={() => handleChange('method','reception')} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
          {' '}15.2 To Reception Facility
        </label>
        {details.method === 'reception' && (
          <>
            <input type="text" value={details.reception_port || ''} onChange={e => handleChange('reception_port', e.target.value.toUpperCase())}
              placeholder="Port Name" style={{ marginLeft:'24px', width:'calc(100% - 24px)' }} />
            <input type="text" value={details.reception_receipt_no || ''} onChange={e => handleChange('reception_receipt_no', e.target.value)}
              placeholder="Receipt No." style={{ marginLeft:'24px', width:'calc(100% - 24px)' }} />
          </>
        )}
      </div>

      {/* 15.3 Holding */}
      <div>
        <label>
          <input type="radio" checked={details.method === 'holding'} onChange={() => handleChange('method','holding')} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
          {' '}15.3 To Bilge Holding Tank
        </label>
        {details.method === 'holding' && (
          <>
            <TankSelect label="Tank Name *" value={details.holding_tank_ids || ''} onChange={v => handleChange('holding_tank_ids',v)}
              availableTanks={availableTanks} error={errors.holding_tank_ids} />
            <div>
              <label>Retained Quantity (m³) *</label>
              <input type="number" step="0.01" value={details.holding_tank_retained_m3 || ''} placeholder="Enter Retained Quantity"
                style={{ width:'100%', borderColor: errors.holding_tank_retained_m3 ? 'red':'#ccc' }}
                onChange={e => handleChange('holding_tank_retained_m3', parseFloat(e.target.value))} />
              {errors.holding_tank_retained_m3 && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.holding_tank_retained_m3}</span>}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
