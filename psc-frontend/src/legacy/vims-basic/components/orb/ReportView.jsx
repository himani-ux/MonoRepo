// src/components/orb/ReportView.jsx
import React from 'react';
import { Card } from './OrbUI';
import ORBTable from './ORBTable';

const ReportView = ({ isVisible, selectedPeriod, reportData }) => {
  if (!isVisible) {
    return null;
  }

  return (
    <Card title={`Filtered Report (${selectedPeriod})`}>
      <ORBTable entries={reportData} />
    </Card>
  );
};

export default ReportView;
