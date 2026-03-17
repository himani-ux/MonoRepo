// src/components/orb/forms/CodeFForm.jsx
import React from 'react';

export default function CodeFForm({ details, handleChange, formatToDateTimeLocal, errors = {} }) {
  return (
    <div className="card" style={{ width:'920px' }}>
      <h4>Condition of Oil Filtering Equipment (Code F)</h4>

      {/* Mode selector */}
      <div style={{ marginBottom:'20px', padding:'12px', border:'1px solid #ddd', borderRadius:'6px' }}>
        <label><strong>Select Operation Type:</strong></label>
        {[['failure','Failure of Equipment'],['restoration','Restoration of Operation']].map(([val, lbl]) => (
          <label key={val} style={{ display:'block', marginTop:'8px' }}>
            <input type="radio" name="f_operation_type" checked={details.operation_mode === val}
              onChange={() => handleChange('operation_mode', val)} style={{ width:'18px', height:'18px', cursor:'pointer' }} />
            {' '}{lbl}
          </label>
        ))}
      </div>

      {/* Failure mode */}
      {details.operation_mode === 'failure' && (
        <>
          <div>
            <label>19. Time of system failure *</label>
            <input type="time" value={details.failure_start_time || ''} style={{ width:'150px', borderColor: errors.failure_start_time ? 'red':'#ccc' }}
              onChange={e => handleChange('failure_start_time', e.target.value.toUpperCase())} />
            {errors.failure_start_time && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.failure_start_time}</span>}
          </div>
          <div>
            <label>20. Action Taken/Equipment Affected *</label>
            <textarea rows="2" value={details.equipment_affected || ''}
              onChange={e => handleChange('equipment_affected', e.target.value.toUpperCase())}
              placeholder="Name the Equipment or explain action taken"
              style={{ width:'100%', padding:'8px', borderColor: errors.equipment_affected ? 'red':'#ccc', borderRadius:'4px', resize:'vertical' }} />
            {errors.equipment_affected && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.equipment_affected}</span>}
          </div>
          <div>
            <label>21. Reasons for failure *</label>
            <textarea rows="3" value={details.failure_reason || ''} onChange={e => handleChange('failure_reason', e.target.value)}
              placeholder="Explain reason of failure" style={{ width:'100%', borderColor: errors.failure_reason ? 'red':'#ccc' }} />
            {errors.failure_reason && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.failure_reason}</span>}
          </div>
        </>
      )}

      {/* Restoration mode */}
      {details.operation_mode === 'restoration' && (
        <>
          <div>
            <label>19. Time of system failure *</label>
            <input type="datetime-local" value={details.failure_start_time || ''} max={formatToDateTimeLocal(new Date())}
              style={{ width:'200px', borderColor: errors.failure_start_time ? 'red':'#ccc' }}
              onChange={e => handleChange('failure_start_time', e.target.value)} />
            {errors.failure_start_time && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.failure_start_time}</span>}
          </div>
          <div>
            <label>20. Time when system has been made operational *</label>
            <input type="time" value={details.restored_time || ''} style={{ width:'150px', borderColor: errors.restored_time ? 'red':'#ccc' }}
              onChange={e => handleChange('restored_time', e.target.value.toUpperCase())} />
            {errors.restored_time && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.restored_time}</span>}
          </div>
          <div>
            <label>21. Reasons for failure *</label>
            <textarea rows="3" value={details.failure_reason || ''} onChange={e => handleChange('failure_reason', e.target.value)}
              placeholder="Explain reason of failure" style={{ width:'100%', borderColor: errors.failure_reason ? 'red':'#ccc' }} />
            {errors.failure_reason && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.failure_reason}</span>}
          </div>
        </>
      )}
    </div>
  );
}
