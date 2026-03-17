// src/components/orb/TankSelect.jsx
// Dropdown to select a single tank from availableTanks, with error display.
import React from 'react';

/**
 * TankSelect
 * Props:
 *  label          – label text
 *  value          – current selected value (tank_name string or tank.id string)
 *  onChange       – (value: string) => void
 *  availableTanks – array of tank objects: { id, tank_name, frame_from, frame_to, capacity }
 *  valueKey       – which tank field to use as <option value>: 'tank_name' (default) or 'id'
 *  placeholder    – placeholder option text
 *  error          – error string
 *  style          – extra style overrides for the <select>
 *  filter         – optional function (tank) => boolean to pre-filter the list
 */
export default function TankSelect({
  label,
  value,
  onChange,
  availableTanks = [],
  valueKey = 'tank_name',
  placeholder = 'Select Tank',
  error,
  style = {},
  filter,
}) {
  const tanks = filter ? availableTanks.filter(filter) : availableTanks;

  return (
    <div style={{ marginBottom: '8px' }}>
      {label && <label style={{ display: 'block', marginBottom: '4px' }}>{label}</label>}
      <select
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        style={{
          width: '100%',
          padding: '8px',
          borderColor: error ? 'red' : '#ccc',
          borderRadius: '4px',
          ...style,
        }}
      >
        <option value="">{placeholder}</option>
        {tanks.map(tank => (
          <option key={tank.id} value={tank[valueKey]}>
            {tank.tank_name} (FR:{tank.frame_from}-{tank.frame_to}
            {valueKey === 'id' ? `, ${tank.capacity} m³` : ''})
          </option>
        ))}
      </select>
      {error && (
        <span style={{ color: 'red', fontSize: '12px', display: 'block', marginTop: '4px' }}>
          {error}
        </span>
      )}
    </div>
  );
}
