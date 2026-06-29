import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useLanguage } from "../i18n/LanguageContext";

interface Props {
  onFilesSelected: (files: File[]) => void;
}

export default function UploadDropzone({ onFilesSelected }: Props) {
  const { t } = useLanguage();
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFilesSelected(acceptedFiles);
      }
    },
    [onFilesSelected],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/json": [".json"] },
  });

  return (
    <div
      {...getRootProps()}
      className={`flex h-64 w-full max-w-xl flex-col items-center justify-center gap-3 rounded-3xl border transition-all duration-200
        ${
          isDragActive
            ? "scale-[1.01] border-violet-400/60 bg-violet-500/10 shadow-lg shadow-violet-500/10"
            : "border-white/10 bg-white/[0.04] shadow-xl shadow-black/20 hover:bg-white/[0.06]"
        }`}
    >
      <input {...getInputProps()} />
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-violet-500/15 text-violet-300">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 16V4M12 4 7 9M12 4l5 5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <p className="text-lg font-medium text-white">{isDragActive ? t.dropzone.active : t.dropzone.idle}</p>
      <p className="text-sm text-white/40">{t.dropzone.hint}</p>
    </div>
  );
}
