import {
  useState,
  useRef,
  useCallback,
  type FC,
  type DragEvent,
  type KeyboardEvent as ReactKeyboardEvent,
} from 'react';
import { Upload, X, FileText, Image, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui';
import { MAX_FILE_SIZE_BYTES, ALLOWED_FILE_TYPES } from '@/lib/utils/constants';

/**
 * File upload component with drag & drop
 * per CLAUDE.md Business Rules:
 * - PDF/JPG/JPEG only
 * - Max 3MB per file
 */

export interface FileUploadProps {
  /** Currently selected file */
  value?: File | null;
  /** Change handler */
  onChange?: (file: File | null) => void;
  /** Accept specific file types (defaults to PDF/JPG/JPEG) */
  accept?: string;
  /** Max file size in bytes (defaults to 3MB) */
  maxSize?: number;
  /** Show error state */
  error?: boolean;
  /** Error message to display */
  errorMessage?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Additional class names */
  className?: string;
  /** Placeholder text */
  placeholder?: string;
}

const ACCEPT_STRING = ALLOWED_FILE_TYPES.join(',');

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(file: File) {
  if (file.type === 'application/pdf') {
    return <FileText className="h-8 w-8 text-error-500" />;
  }
  return <Image className="h-8 w-8 text-primary-500" />;
}

function validateFile(
  file: File,
  accept: string,
  maxSize: number
): { valid: boolean; error?: string } {
  // Check file type
  const allowedTypes = accept.split(',').map((t) => t.trim().toLowerCase());
  const fileType = file.type.toLowerCase();
  const fileExt = `.${file.name.split('.').pop()?.toLowerCase()}`;

  const isValidType = allowedTypes.some(
    (type) =>
      type === fileType ||
      type === fileExt ||
      (type.endsWith('/*') && fileType.startsWith(type.replace('/*', '/')))
  );

  if (!isValidType) {
    return {
      valid: false,
      error: 'Invalid file type. Only PDF and JPG/JPEG files are allowed.',
    };
  }

  // Check file size
  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File size must not exceed ${formatFileSize(maxSize)}.`,
    };
  }

  return { valid: true };
}

export const FileUpload: FC<FileUploadProps> = ({
  value,
  onChange,
  accept = ACCEPT_STRING,
  maxSize = MAX_FILE_SIZE_BYTES,
  error,
  errorMessage,
  disabled,
  className,
  placeholder = 'Drag & drop file here or click to browse',
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      const validation = validateFile(file, accept, maxSize);
      if (!validation.valid) {
        setValidationError(validation.error || 'Invalid file');
        return;
      }
      setValidationError(null);
      onChange?.(file);
    },
    [accept, maxSize, onChange]
  );

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragOver(false);

      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [disabled, handleFile]
  );

  const handleDragOver = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (!disabled) {
        setIsDragOver(true);
      }
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleClick = () => {
    if (!disabled) {
      inputRef.current?.click();
    }
  };

  const handleKeyDown = (e: ReactKeyboardEvent<HTMLDivElement>) => {
      if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
    // Reset input value so same file can be selected again
    e.target.value = '';
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    setValidationError(null);
    onChange?.(null);
  };

  const displayError = errorMessage || validationError;
  const hasError = error || !!validationError;

  return (
    <div className={cn('space-y-2', className)}>
      <div
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        role={!value ? 'button' : undefined}
        tabIndex={!disabled && !value ? 0 : -1}
        aria-disabled={disabled}
        aria-label={!value ? 'Upload file' : undefined}
        className={cn(
          'relative flex min-h-[120px] flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors duration-200',
          !disabled && !value && 'cursor-pointer',
          disabled
            ? 'cursor-not-allowed border-neutral-200 bg-neutral-50'
            : isDragOver
              ? 'border-primary-500 bg-primary-50'
              : hasError
                ? 'border-error-500 bg-error-50 hover:border-error-600'
                : 'border-neutral-300 bg-white hover:border-primary-400 hover:bg-neutral-50'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleInputChange}
          onClick={(e) => e.stopPropagation()}
          disabled={disabled}
          className={cn(
            'absolute opacity-0',
            !value && !disabled
              ? 'inset-0 h-full w-full cursor-pointer'
              : 'h-0 w-0 overflow-hidden'
          )}
        />

        {value ? (
          <div className="flex items-center gap-3">
            {getFileIcon(value)}
            <div className="flex-1 text-left">
              <p className="text-sm font-medium text-neutral-800 line-clamp-1">
                {value.name}
              </p>
              <p className="text-xs text-neutral-500">
                {formatFileSize(value.size)}
              </p>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleRemove}
              disabled={disabled}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Remove file</span>
            </Button>
          </div>
        ) : (
          <>
            <Upload
              className={cn(
                'mb-2 h-8 w-8',
                disabled ? 'text-neutral-300' : 'text-neutral-400'
              )}
            />
            <p
              className={cn(
                'text-center text-sm',
                disabled ? 'text-neutral-400' : 'text-neutral-600'
              )}
            >
              {placeholder}
            </p>
            <p className="mt-1 text-center text-xs text-neutral-400">
              Accepted: PDF, JPG, JPEG (max {formatFileSize(maxSize)})
            </p>
          </>
        )}
      </div>

      {displayError && (
        <div className="flex items-center gap-1.5 text-sm text-error-500">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{displayError}</span>
        </div>
      )}
    </div>
  );
};
