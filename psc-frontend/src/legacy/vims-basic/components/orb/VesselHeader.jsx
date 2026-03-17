// src/components/orb/VesselHeader.jsx
import React from 'react';

const VesselHeader = ({ vessel }) => {
  const headerStyle = {
    fontFamily: 'Courier New, monospace',
    fontSize: '14px'
  };

  if (!vessel) {
    return null;
  }

  return (
    <div style={headerStyle}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          <tr>
            <td style={{ paddingBottom: '8px' }}>
              <strong>Name of ship</strong>
              <div style={{ marginTop: '4px' }}>
                {vessel.vesselName || "________________________"}
              </div>
            </td>
          </tr>
          <tr>
            <td style={{ paddingBottom: '8px' }}>
              <strong>Distinctive number or letters</strong>
              <div style={{ marginTop: '4px' }}>
                {vessel.imoNumber || "__________"}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div style={{ marginTop: '12px', fontSize: '14px', fontWeight: 'bold', textAlign: 'center' }}>
        Machinery Space Operations
      </div>
    </div>
  );
};

export default VesselHeader;
