// ORBHeader.jsx
export default function ORBHeader({ vesselName, vesselId }) {
  return (
    <div style={{ fontFamily: 'Courier New, monospace', fontSize: '14px' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '10px' }}>
        <tbody>
          <tr>
            <td style={{ paddingBottom: '8px' }}>
              <strong>Name of ship</strong>
              <div style={{ marginTop: '4px' }}>{vesselName || "________________________"}</div>
            </td>
          </tr>
          <tr>
            <td style={{ paddingBottom: '8px' }}>
              <strong>Distinctive number or letters</strong>
              <div style={{ marginTop: '4px' }}>{vesselId || "__________"}</div>
            </td>
          </tr>
        </tbody>
      </table>

      <div style={{ marginTop: '12px', fontSize: '14px', fontWeight: 'bold' }}>
        Machinery Space Operations
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>Date</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>Code (Letter)</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>Item (Number)</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'left' }}>Record of operations/signature of officer in charge</th>
          </tr>
        </thead>
      </table>
    </div>
  );
}