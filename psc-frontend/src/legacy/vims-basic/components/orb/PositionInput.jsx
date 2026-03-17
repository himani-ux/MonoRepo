// src/components/orb/PositionInput.jsx
// Reusable 6-field lat/lon position selector used across Code A, B, D, G forms.

import React from 'react';

/**
 * PositionInput
 * Renders a 6-column grid of selects for Lat Deg / Lat Min / Lat Dir / Lon Deg / Lon Min / Lon Dir.
 *
 * Props:
 *  label        – section label displayed above the grid
 *  prefix       – field name prefix, e.g. "cleaning_start" → reads details.cleaning_start_lat_deg etc.
 *  details      – the formData.details object (read-only)
 *  handleChange – (field, value) => void
 *  error        – optional error string to display below
 */
export default function PositionInput({ label, prefix, details, handleChange, error }) {
  const latDegKey = `${prefix}_lat_deg`;
  const latMinKey = `${prefix}_lat_min`;
  const latDirKey = `${prefix}_lat_dir`;
  const lonDegKey = `${prefix}_lon_deg`;
  const lonMinKey = `${prefix}_lon_min`;
  const lonDirKey = `${prefix}_lon_dir`;

  const borderStyle = (hasError) => ({ borderColor: hasError ? 'red' : '#ccc' });

  return (
    <div style={{ marginBottom: '12px' }}>
      {label && <label style={{ display: 'block', marginBottom: '4px' }}>{label}</label>}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'auto auto auto auto auto auto',
        gap: '8px',
        alignItems: 'center',
      }}>
        {/* Lat Deg */}
        <div>
          <label style={{ fontSize: '12px', display: 'block' }}>Lat Deg</label>
          <select
            value={details[latDegKey] ?? ''}
            onChange={e => handleChange(latDegKey, e.target.value === '' ? '' : parseInt(e.target.value, 10))}
            style={{ width: '70px', ...borderStyle(!!error) }}
          >
            <option value="">°</option>
            {[...Array(91)].map((_, i) => <option key={i} value={i}>{i}</option>)}
          </select>
        </div>

        {/* Lat Min */}
        <div>
          <label style={{ fontSize: '12px', display: 'block' }}>Min</label>
          <select
            value={details[latMinKey] ?? ''}
            onChange={e => handleChange(latMinKey, e.target.value === '' ? '' : parseInt(e.target.value, 10))}
            style={{ width: '70px', ...borderStyle(!!error) }}
          >
            <option value="">′</option>
            {[...Array(60)].map((_, i) => <option key={i} value={i}>{i}</option>)}
          </select>
        </div>

        {/* Lat Dir */}
        <div>
          <label style={{ fontSize: '12px', display: 'block' }}>Dir</label>
          <select
            value={details[latDirKey] || ''}
            onChange={e => handleChange(latDirKey, e.target.value)}
            style={{ width: '60px', ...borderStyle(!!error) }}
          >
            <option value="">N/S</option>
            <option value="N">N</option>
            <option value="S">S</option>
          </select>
        </div>

        {/* Lon Deg */}
        <div>
          <label style={{ fontSize: '12px', display: 'block' }}>Lon Deg</label>
          <select
            value={details[lonDegKey] ?? ''}
            onChange={e => handleChange(lonDegKey, e.target.value === '' ? '' : parseInt(e.target.value, 10))}
            style={{ width: '70px', ...borderStyle(!!error) }}
          >
            <option value="">°</option>
            {[...Array(181)].map((_, i) => <option key={i} value={i}>{i}</option>)}
          </select>
        </div>

        {/* Lon Min */}
        <div>
          <label style={{ fontSize: '12px', display: 'block' }}>Min</label>
          <select
            value={details[lonMinKey] ?? ''}
            onChange={e => handleChange(lonMinKey, e.target.value === '' ? '' : parseInt(e.target.value, 10))}
            style={{ width: '70px', ...borderStyle(!!error) }}
          >
            <option value="">′</option>
            {[...Array(60)].map((_, i) => <option key={i} value={i}>{i}</option>)}
          </select>
        </div>

        {/* Lon Dir */}
        <div>
          <label style={{ fontSize: '12px', display: 'block' }}>Dir</label>
          <select
            value={details[lonDirKey] || ''}
            onChange={e => handleChange(lonDirKey, e.target.value)}
            style={{ width: '60px', ...borderStyle(!!error) }}
          >
            <option value="">E/W</option>
            <option value="E">E</option>
            <option value="W">W</option>
          </select>
        </div>
      </div>

      {error && (
        <span style={{ color: 'red', fontSize: '12px', display: 'block', marginTop: '4px' }}>
          {error}
        </span>
      )}
    </div>
  );
}
