import { type FC, useState, type MouseEvent } from 'react';
import { FileText, Image, AlertTriangle, Trash2, Upload } from 'lucide-react';
import { Card, CardContent, Button } from '@/components/ui';
import { ConfirmDialog } from '@/components/shared';
import { apiClient } from '@/lib/api/client';
import { EVIDENCE_TYPES } from '@/lib/utils/constants';
import { useDeleteEvidence } from '@/hooks/use-cars';
import type { Evidence } from '@/types';

export interface EvidenceSectionProps {
  evidence: Evidence[];
  carId?: string | number;
  onUpload?: () => void;
  className?: string;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isImage(mimeType: string): boolean {
  return mimeType.startsWith('image/');
}

function resolveEvidenceUrl(item: Evidence): string {
  const rawPath = item.preview_url || item.file_path;
  if (!rawPath) return '#';
  if (rawPath.startsWith('http://') || rawPath.startsWith('https://')) return rawPath;
  if (rawPath.startsWith('/')) return rawPath;
  return `/uploads/${rawPath.replace(/^\/+/, '')}`;
}

async function openEvidenceWithAuth(
  url: string,
  _fileName: string,
  mimeType: string
): Promise<void> {
  const previewTab = window.open('about:blank', '_blank');
  try {
    const response = await apiClient.get(url, { responseType: 'blob' });
    const typedBlob =
      response.data?.type || !mimeType
        ? response.data
        : new Blob([response.data], { type: mimeType });
    const blobUrl = URL.createObjectURL(typedBlob);

    if (previewTab && !previewTab.closed) {
      previewTab.location.href = blobUrl;
    } else {
      window.location.href = blobUrl;
    }
    setTimeout(() => URL.revokeObjectURL(blobUrl), 10 * 60_000);
  } catch {
    if (previewTab && !previewTab.closed) {
      previewTab.close();
    }
  }
}

interface EvidenceItemProps {
  item: Evidence;
  carId?: string | number;
}

const EvidenceItem: FC<EvidenceItemProps> = ({ item, carId }) => {
  const evidenceUrl = resolveEvidenceUrl(item);
  const deleteEvidence = useDeleteEvidence(carId ?? '');
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <>
      <div className="flex items-start gap-3 rounded-md border border-neutral-200 bg-white p-3">
        <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded bg-neutral-100">
          {isImage(item.mime_type) ? (
            <Image className="h-6 w-6 text-primary-500" />
          ) : (
            <FileText className="h-6 w-6 text-error-500" />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <a
            href={evidenceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="block truncate text-sm font-medium text-primary-600 hover:underline"
            onClick={(event: MouseEvent<HTMLAnchorElement>) => {
              event.preventDefault();
              void openEvidenceWithAuth(evidenceUrl, item.file_name, item.mime_type);
            }}
          >
            {item.file_name}
          </a>
          <p className="text-xs text-gray-500">{item.description}</p>
          <p className="mt-1 text-xs text-gray-400">
            {formatDate(item.uploaded_at)} &middot; {formatFileSize(item.file_size)}
          </p>
        </div>

        {carId && (
          <button
            type="button"
            onClick={() => setConfirmDelete(true)}
            aria-label={`Delete evidence ${item.file_name}`}
            className="flex-shrink-0 rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-error-500"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Delete Evidence"
        description={`Are you sure you want to delete "${item.file_name}"? This cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        confirmDisabled={deleteEvidence.isPending}
        onConfirm={async () => {
          await deleteEvidence.mutateAsync(item.id);
          setConfirmDelete(false);
        }}
      />
    </>
  );
};

export const EvidenceSection: FC<EvidenceSectionProps> = ({
  evidence,
  carId,
  onUpload,
  className,
}) => {
  const before = evidence.filter((e) => e.evidence_type === EVIDENCE_TYPES.BEFORE);
  const after = evidence.filter((e) => e.evidence_type === EVIDENCE_TYPES.AFTER);
  const other = evidence.filter((e) => e.evidence_type === EVIDENCE_TYPES.OTHER);

  const missingBefore = before.length === 0;
  const missingAfter = after.length === 0;
  const hasMissingEvidence = missingBefore || missingAfter;

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">EVIDENCE</h2>
          {onUpload && (
            <Button variant="outline" size="sm" onClick={onUpload}>
              <Upload className="mr-1 h-4 w-4" />
              Upload
            </Button>
          )}
        </div>

        {/* Missing evidence warning */}
        {hasMissingEvidence && (
          <div className="mb-3 flex items-center gap-2 rounded-md bg-warning-50 p-2 text-sm text-warning-700">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>
              Missing{' '}
              {missingBefore && missingAfter
                ? 'BEFORE and AFTER'
                : missingBefore
                  ? 'BEFORE'
                  : 'AFTER'}{' '}
              evidence (required for submission)
            </span>
          </div>
        )}

        {evidence.length === 0 ? (
          <p className="text-sm text-gray-500 italic">
            No evidence uploaded yet
          </p>
        ) : (
          <div className="space-y-4">
            {/* Before Evidence */}
            {before.length > 0 && (
              <div>
                <h3 className="mb-2 text-sm font-semibold text-gray-700">
                  BEFORE ({before.length})
                </h3>
                <div className="space-y-2">
                  {before.map((item) => (
                    <EvidenceItem key={item.id} item={item} carId={carId} />
                  ))}
                </div>
              </div>
            )}

            {/* After Evidence */}
            {after.length > 0 && (
              <div>
                <h3 className="mb-2 text-sm font-semibold text-gray-700">
                  AFTER ({after.length})
                </h3>
                <div className="space-y-2">
                  {after.map((item) => (
                    <EvidenceItem key={item.id} item={item} carId={carId} />
                  ))}
                </div>
              </div>
            )}

            {/* Other Evidence */}
            {other.length > 0 && (
              <div>
                <h3 className="mb-2 text-sm font-semibold text-gray-700">
                  OTHER ({other.length})
                </h3>
                <div className="space-y-2">
                  {other.map((item) => (
                    <EvidenceItem key={item.id} item={item} carId={carId} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
