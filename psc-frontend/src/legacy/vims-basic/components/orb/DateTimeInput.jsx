// src/components/orb/DateTimeInput.jsx
// Reusable datetime-local input with max=now, consistent styling, and error display.
import React from 'react';

/**
 * DateTimeInput
 * Props:
 *  id           – input id (for label htmlFor)
 *  label        – label text
 *  value        – current ISO datetime-local string
 *  onChange     – (value: string) => void
 *  max          – max datetime-local string (defaults to now)
 *  min          – min datetime-local string (optional)
 *  required     – boolean
 *  error        – error string to display
 *  style        – override styles for the <input>
 */
export default function DateTimeInput({
  id = 'datetime-input',
  label = 'Entry Date & Time *',
  value,
  onChange,
  max,
  min,
  required = false,
  error,
  style = {},
}) {
  return (
    <div className="form-row" style={{ marginBottom: '1rem' }}>
      <label htmlFor={id} style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
        {label}
      </label>
      <input
        id={id}
        type="datetime-local"
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        max={max}
        min={min}
        required={required}
        style={{
          width: '20%',
          padding: '10px',
          border: '2px solid #007bff',
          borderRadius: '4px',
          fontSize: '14px',
          backgroundColor: '#fff',
          color: '#333',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          transition: 'border-color 0.3s ease',
          ...style,
        }}
        onFocus={e  => (e.target.style.borderColor = '#0056b3')}
        onBlur={e   => (e.target.style.borderColor = '#007bff')}
      />
      {error && (
        <span style={{ color: 'red', fontSize: '12px', display: 'block', marginTop: '0.25rem' }}>
          {error}
        </span>
      )}
    </div>
  );
}
