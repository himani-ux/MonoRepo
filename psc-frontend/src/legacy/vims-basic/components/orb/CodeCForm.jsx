// src/components/orb/forms/CodeCForm.jsx
import React from 'react';
import TankSelect from './TankSelect';

export default function CodeCForm({ details, handleChange, availableTanks, errors = {} }) {
  /** Shared 11.1 – 11.3 Weekly/Manual top section */
  const renderWeeklyManualTopSection = () => (
    <>
      <TankSelect
        label="11.1 Identity of tank(s)*"
        value={details.sludge_tank_id || ''}
        onChange={v => {
          const tank = availableTanks.find(t => t.tank_name === v);
          handleChange('sludge_tank_id', v);
          if (tank) handleChange('sludge_tank_capacity', tank.capacity);
        }}
        availableTanks={availableTanks}
        error={errors.sludge_tank_id}
      />
      <div>
        <label>11.2 Total Capacity (m³) *</label>
        <input type="number" step="0.01" value={details.sludge_tank_capacity || ''}
          onChange={e => handleChange('sludge_tank_capacity', parseFloat(e.target.value))}
          placeholder="Auto-filled after tank selection" style={{ width:'100%' }} disabled />
        {errors.sludge_tank_capacity && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.sludge_tank_capacity}</span>}
      </div>
      <div>
        <label>11.3 Total quantity of retention (m³) *</label>
        <input type="number" step="0.01" value={details.sludge_before ?? ''} placeholder="Enter Retained Quantity"
          style={{ width:'100%', borderColor: errors.sludge_before ? 'red' : '#ccc' }}
          onChange={e => handleChange('sludge_before', parseFloat(e.target.value))} />
        {errors.sludge_before && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.sludge_before}</span>}
      </div>
    </>
  );

  return (
    <div className="card" style={{ width:'920px' }}>
      {/* Operation Mode selector */}
      <div style={{ marginBottom:'20px', padding:'12px', border:'1px solid #ddd', borderRadius:'6px' }}>
        <label><strong>Select Operation Type:</strong></label>
        {[['weekly','Weekly Update'],['manual','Manual Collection'],['transfer','Transfer/Disposal of Sludge']].map(([val, lbl]) => (
          <label key={val} style={{ display:'block', marginTop:'8px' }}>
            <input type="radio" name="c_operation_type" checked={details.operation_mode === val}
              onChange={() => handleChange('operation_mode', val)} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
            {' '}{lbl}
          </label>
        ))}
      </div>

      {/* Weekly */}
      {details.operation_mode === 'weekly' && renderWeeklyManualTopSection()}

      {/* Manual */}
      {details.operation_mode === 'manual' && (
        <>
          {renderWeeklyManualTopSection()}
          <div>
            <label>11.4 Manual Collection (m³) *</label>
            <input type="number" step="0.01" value={details.manual_collection_m3 || ''}
              placeholder="Quantity of Manual Collection"
              style={{ width:'100%', borderColor: errors.manual_collection_m3 ? 'red' : '#ccc' }}
              onChange={e => handleChange('manual_collection_m3', parseFloat(e.target.value))} />
            <label>11.4 Source Tank *</label>
            <select value={details.collection_source || ''}
              onChange={e => handleChange('collection_source', e.target.value)}
              style={{ width:'100%', padding:'8px', borderColor: errors.collection_source ? 'red' : '#ccc', borderRadius:'4px', marginTop:'4px' }}>
              <option value="">Select Source Tank</option>
              {availableTanks.map(t => (
                <option key={t.id} value={t.tank_name}>{t.tank_name} (FR:{t.frame_from}-{t.frame_to})</option>
              ))}
              <option value="OTHER">Other (Specify Manually)</option>
            </select>
            {errors.collection_source && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.collection_source}</span>}
            {details.collection_source === 'OTHER' && (
              <div style={{ marginTop:'8px' }}>
                <label>Specify Source Tank:</label>
                <input type="text" value={details.custom_collection_source || ''}
                  onChange={e => handleChange('custom_collection_source', e.target.value)}
                  placeholder="Enter tank name/identifier"
                  style={{ width:'100%', padding:'8px', border:'1px solid #ccc', borderRadius:'4px', marginTop:'2px' }} />
              </div>
            )}
          </div>
        </>
      )}

      {/* Transfer/Disposal */}
      {details.operation_mode === 'transfer' && (
        <>
          <hr style={{ margin:'16px 0', borderColor:'#ccc' }} />

          {/* 12.1 Reception */}
          <div>
            <label>
              <input type="radio" checked={details.disposal_method === 'reception'} onChange={() => handleChange('disposal_method','reception')} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
              {' '}12.1 To Reception Facility
            </label>
            {details.disposal_method === 'reception' && (
              <>
                <input type="number" step="0.01" value={details.quantity_m3 || ''} onChange={e => handleChange('quantity_m3', parseFloat(e.target.value))} placeholder="Disposal Quantity" />
                <TankSelect label="" value={details.source_tank || ''} onChange={v => handleChange('source_tank',v)} availableTanks={availableTanks} placeholder="Select Source Tank" error={errors.source_tank} />
                <input type="number" step="0.01" value={details.retained_quantity || ''} onChange={e => handleChange('retained_quantity', parseFloat(e.target.value))} placeholder="Retained quantity" />
                <input type="text"   value={details.reception_vessel || ''} onChange={e => handleChange('reception_vessel', e.target.value)} placeholder="Reception vessel" />
                <input type="text"   value={details.reception_port   || ''} onChange={e => handleChange('reception_port',   e.target.value)} placeholder="Port Name" />
                <input type="text"   value={details.reception_receipt_no || ''} onChange={e => handleChange('reception_receipt_no', e.target.value)} placeholder="Receipt/Certificate no." />
              </>
            )}
          </div>

          {/* 12.2 Transfer */}
          <div>
            <label>
              <input type="radio" checked={details.disposal_method === 'transfer'} onChange={() => handleChange('disposal_method','transfer')} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
              {' '}12.2 Transfer to Another Tank
            </label>
            {details.disposal_method === 'transfer' && (
              <>
                <label>Quantity Transferred (m³) *</label>
                <input type="number" step="0.01" value={details.disposal_quantity_m3 || ''} placeholder="e.g., 1"
                  style={{ width:'100%', borderColor: errors.disposal_quantity_m3 ? 'red':'#ccc' }}
                  onChange={e => handleChange('disposal_quantity_m3', parseFloat(e.target.value))} />
                <TankSelect label="Transferred From Tank *" value={details.transferred_from_tank_ids || ''} onChange={v => handleChange('transferred_from_tank_ids',v)} availableTanks={availableTanks} placeholder="Select Source Tank" error={errors.transferred_from_tank_ids} />
                <label>Retained Quantity (m³)</label>
                <input type="number" step="0.01" value={details.retained_quantity || ''} onChange={e => handleChange('retained_quantity', parseFloat(e.target.value))} placeholder="e.g., 3" style={{ width:'100%' }} />
                <TankSelect label="Transferred To Tank *" value={details.transferred_to_Tank_ids || ''} onChange={v => handleChange('transferred_to_Tank_ids',v)} availableTanks={availableTanks} placeholder="Select Destination Tank" error={errors.transferred_to_Tank_ids} />
              </>
            )}
          </div>

          {/* 12.3 Incineration */}
          <div>
            <label>
              <input type="radio" checked={details.disposal_method === 'incineration'} onChange={() => handleChange('disposal_method','incineration')} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
              {' '}12.3 Incineration
            </label>
            {details.disposal_method === 'incineration' && (
              <>
                <input type="number" step="0.01" value={details.quantity_m3 || ''} onChange={e => handleChange('quantity_m3', parseFloat(e.target.value))} placeholder="Incinerated Quantity" />
                <TankSelect label="Source Tank *" value={details.source_tank || ''} onChange={v => handleChange('source_tank',v)} availableTanks={availableTanks} placeholder="Select Source Tank" error={errors.source_tank} />
                <input type="number" step="0.01" value={details.retained_quantity || ''} onChange={e => handleChange('retained_quantity', parseFloat(e.target.value))} placeholder="Retained Quantity" />
                <input type="number" step="0.01" value={details.incineration_duration_hours || ''} onChange={e => handleChange('incineration_duration_hours', parseFloat(e.target.value))} placeholder="Duration (hours)" />
              </>
            )}
          </div>

          {/* 12.4 Other */}
          <div>
            <label>
              <input type="radio" checked={details.disposal_method === 'other'} onChange={() => handleChange('disposal_method','other')} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
              {' '}12.4 Other Disposal (Evaporation)
            </label>
            {details.disposal_method === 'other' && (
              <textarea rows="2" value={details.other_disposal_details || ''} onChange={e => handleChange('other_disposal_details', e.target.value)}
                placeholder="Explain the disposal method" style={{ width:'100%', marginLeft:'24px', marginTop:'4px' }} />
            )}
          </div>
        </>
      )}
    </div>
  );
}
