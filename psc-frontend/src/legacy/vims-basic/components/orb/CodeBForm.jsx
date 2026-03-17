// src/components/orb/forms/CodeBForm.jsx
import React from 'react';
import PositionInput from './PositionInput';
import TankSelect from './TankSelect';

export default function CodeBForm({ details, handleChange, availableTanks, errors = {} }) {
  return (
    <div className="card" style={{ width: '920px' }}>
      <TankSelect label="5. Tank ID(s) *" value={details.tank_ids || ''} onChange={v => handleChange('tank_ids', v)}
        availableTanks={availableTanks} error={errors.tank_ids} />

      <PositionInput label="6. Position at Start *" prefix="pos_start" details={details} handleChange={handleChange} error={errors.pos_start} />
      <PositionInput label="7. Position at End *"   prefix="pos_end"   details={details} handleChange={handleChange} error={errors.pos_end} />

      <div style={{ display:'flex', alignItems:'center', gap:'10px', marginBottom:'8px', marginTop:'2px' }}>
        <label>9.2 Discharged To Reception Facility *</label>
        <input type="text" value={details.reception_port || ''} placeholder="Enter Port Name" style={{ width:'200px', marginTop:'7px', borderColor: errors.reception_port ? 'red' : '#ccc' }}
          onChange={e => { handleChange('reception_port', e.target.value); handleChange('method','reception'); }} required />
      </div>
      {errors.reception_port && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.reception_port}</span>}

      <div>
        <label>10. Quantity Discharged (m³)</label>
        <input type="number" step="0.01" value={details.quantity_discharged_m3 || ''} placeholder="Enter discharge quantity"
          style={{ borderColor: errors.quantity_discharged_m3 ? 'red' : '#ccc' }}
          onChange={e => handleChange('quantity_discharged_m3', e.target.value === '' ? '' : parseFloat(e.target.value))} />
        {errors.quantity_discharged_m3 && <span style={{ color:'red', fontSize:'12px', display:'block', marginTop:'4px' }}>{errors.quantity_discharged_m3}</span>}
      </div>
    </div>
  );
}
