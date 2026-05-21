interface SafetyHighSeverityPhotoUploadProps {
  error?: string | null;
  isUploading?: boolean;
  isRequired: boolean;
  onFileSelect: (file: File) => void;
  value: string;
}

export default function SafetyHighSeverityPhotoUpload({
  error,
  isUploading = false,
  isRequired,
  onFileSelect,
  value,
}: SafetyHighSeverityPhotoUploadProps) {
  return (
    <label className="block rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-slate-900">Photo evidence</div>
          <p className="mt-1 text-sm leading-6 text-slate-600">JPG, JPEG, or PNG. Maximum 3MB.</p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${
            isRequired ? "bg-rose-100 text-rose-800" : "bg-slate-100 text-slate-700"
          }`}
        >
          {isRequired ? "Required for HIGH" : "Optional"}
        </span>
      </div>
      <input
        accept="image/jpeg,image/jpg,image/png"
        aria-label="Photo evidence"
        className="mt-4 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 file:mr-4 file:rounded-full file:border-0 file:bg-emerald-900 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
        disabled={isUploading}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            onFileSelect(file);
          }
        }}
        type="file"
      />
      {value ? <p className="mt-3 text-sm font-medium text-emerald-700">Uploaded: {value}</p> : null}
      {isUploading ? <p className="mt-3 text-sm font-medium text-slate-600">Uploading photo...</p> : null}
      {error ? <p className="mt-3 text-sm font-medium text-rose-700">{error}</p> : null}
    </label>
  );
}
