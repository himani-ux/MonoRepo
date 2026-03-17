
import React from 'react';
import { Card } from './OrbUI';
import ORBTable from './ORBTable';

// const PendingEntriesCard = ({ pending, onApprove, onReject }) => {
//   return (
//     <Card title="Pending Crew Entries">
//       <ORBTable
//         entries={pending}
//         onApprove={onApprove}
//         onReject={onReject}
//       />
//     </Card>
//   );
// };

// export default PendingEntriesCard;


const PendingEntriesCard = ({
  pending,
  onApprove,
  onReject,
  canApprove,
  canReject,
}) => {
  return (
    <Card title="Pending Crew Entries">
      <ORBTable
        entries={pending}
        cardTitle="Pending Crew Entries"
        permissions={{
          approve: canApprove,
          reject: canReject,
        }}
        handlers={{
          onApprove,
          onReject,
        }}
      />
    </Card>
  );
};

export default PendingEntriesCard;

