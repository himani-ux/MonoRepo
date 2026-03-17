
import { Card, Button } from './OrbUI';
import ORBTable from './ORBTable';




const ApprovedEntriesCard = ({ approved, vessel, onSavePDF, canAccessSavePDF }) => {
  return (
    <Card title="Approved Logbook Entries(Preview)">
      <div id="approved-entries">
        <ORBTable entries={approved} />
      </div>
    {canAccessSavePDF && (
      <div style={{ marginTop: 36, textAlign: "center" }}>
        <Button onClick={onSavePDF}>
          Save as PDF
        </Button>
      </div>
      )}
    </Card>
  );
};

export default ApprovedEntriesCard;

