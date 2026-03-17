// src/components/orb/forms/CodeIForm.jsx
import React from 'react';

export default function CodeIForm({ details, handleChange, errors = {} }) {
  return (
    <div className="card" style={{ width:'920px' }}>
      <h4>Additional Operational Procedures and General Remarks (Code I)</h4>
      <div>
        <label>Enter your remarks or operational details *</label>
        <textarea rows="6" value={details.remarks || ''}
          onChange={e => handleChange('remarks', e.target.value)}
          style={{ width:'100%', borderColor: errors.remarks ? 'red':'#ccc', fontFamily:'monospace', padding:'8px' }}
          required />
        {errors.remarks && <span style={{ color:'red', fontSize:'12px', display:'block' }}>{errors.remarks}</span>}
      </div>
      <div style={{ marginTop:'8px', fontSize:'12px', color:'#666' }}>
        <strong>Tip:</strong> Be clear, factual, and include quantities and tank names where possible.
      </div>
    </div>
  );
}
