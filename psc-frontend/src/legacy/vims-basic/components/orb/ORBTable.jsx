
import { Card, Button } from "./OrbUI";
import { getItemNumber } from "../../hooks/orb/itemNumberUtils";

export default function ORBTable({
  entries,
  permissions = {},
  handlers = {},
  cardTitle = "Your Drafts",
  showTitle = null,
}) {
  if (!entries || entries.length === 0) {
    return <p>No Entries Found.</p>;
  }

  const {
    edit: canEdit = false,
    delete: canDelete = false,
    approve: canApprove = false,
    reject: canReject = false,
  } = permissions;

  const { onEdit, onDelete, onApprove, onReject } = handlers;

  const showActions = canEdit || canDelete || canApprove || canReject;

  const showCardTitle = showTitle !== null ? showTitle : showActions;

  const displayEntries = entries;

  return (
    <Card>
      <div className="orb-theme">
        {showCardTitle && <h1>{cardTitle}</h1>}
        <div style={{ overflowX: "auto", width: "100%", margin: "1rem 0" }}>
          <table
            className="orb-table"
            style={{ minWidth: "800px", width: "100%" }}
          >
            <thead>
              <tr>
                <th>Date</th>
                <th>Code</th>
                <th>Item No.</th>
                <th>Record of operations</th>
                {showActions && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {displayEntries.map((entry) => {
                const lines = (entry.record_of_operation || "")
                  .split("\n")
                  .filter((l) => l.trim() !== "");

                return lines.map((line, lineIdx) => {
                  const itemNo = getItemNumber(
                    entry.code,
                    line,
                    lineIdx,
                    entry.item_no,
                  );

                  const formatDate = (dateStr) =>
                    new Date(dateStr)
                      .toLocaleDateString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })
                      .toUpperCase()
                      .replace(/ /g, "-");

                  return (
                    <tr key={`${entry.id}-${lineIdx}`}>
                      <td>{lineIdx === 0 ? formatDate(entry.date) : ""}</td>
                      <td>{lineIdx === 0 ? entry.code : ""}</td>
                      <td>{itemNo}</td>
                      <td style={{ whiteSpace: "pre-line" }}>{line}</td>

                      {showActions && (
                        <td>
                          {lineIdx === 0 && showActions && (
                            <>
                              {canEdit && (
                                <button onClick={() => onEdit(entry.id)}>
                                  Edit
                                </button>
                              )}

                              {canDelete && (
                                <button onClick={() => onDelete(entry.id)}>
                                  Delete
                                </button>
                              )}

                              {canApprove && entry.status === "Pending" && (
                                <Button onClick={() => onApprove(entry.id)}>
                                  Approve
                                </Button>
                              )}

                              {canReject && entry.status === "Pending" && (
                                <Button onClick={() => onReject(entry.id)}>
                                  Reject
                                </Button>
                              )}
                            </>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                });
              })}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  );
}
