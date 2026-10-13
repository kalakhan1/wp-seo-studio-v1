import { useRef, useState } from "react";
import { ImagePlus, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { TextField } from "@/components/inputs/TextField";
import { mediaApi } from "@/services/mediaApi";
import { ApiError, NetworkError } from "@/types/errors";

interface MediaUploaderProps {
  connectionId: number;
  onUploaded: () => void;
}

export function MediaUploader({
  connectionId,
  onUploaded,
}: MediaUploaderProps): JSX.Element {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [altText, setAltText] = useState("");
  const [caption, setCaption] = useState("");
  const [description, setDescription] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handlePick = (f: File | null): void => {
    setFile(f);
    if (f && !title) {
      // Default title to the filename stem for convenience.
      const stem = f.name.replace(/\.[^.]+$/, "");
      setTitle(stem);
    }
  };

  const handleUpload = async (): Promise<void> => {
    if (!file) {
      toast.error("Choose a file first.");
      return;
    }
    setUploading(true);
    setProgress(0);
    try {
      const result = await mediaApi.upload({
        connectionId,
        file,
        title: title || undefined,
        altText: altText || undefined,
        caption: caption || undefined,
        description: description || undefined,
        onProgress: setProgress,
      });
      toast.success(`Uploaded "${result.media.filename}".`);
      // Reset form
      setFile(null);
      setTitle("");
      setAltText("");
      setCaption("");
      setDescription("");
      if (fileRef.current) fileRef.current.value = "";
      onUploaded();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`Upload failed: ${err.message}`);
      } else if (err instanceof NetworkError) {
        toast.error(`Network error: ${err.message}`);
      } else {
        toast.error("Upload failed.");
      }
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="rounded-lg border border-surface-border bg-white p-5">
      <h2 className="mb-4 text-base font-semibold text-slate-800">
        Upload New Media
      </h2>

      <div
        className="mb-4 cursor-pointer rounded-lg border-2 border-dashed border-surface-border bg-surface-muted p-6 text-center transition-colors hover:border-brand hover:bg-brand-light/30"
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
        }}
        onDrop={(e) => {
          e.preventDefault();
          const dropped = e.dataTransfer.files[0];
          if (dropped) handlePick(dropped);
        }}
      >
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          className="hidden"
          onChange={(e) => handlePick(e.target.files?.[0] ?? null)}
        />
        <ImagePlus className="mx-auto mb-2 h-8 w-8 text-slate-400" />
        {file ? (
          <>
            <p className="font-medium text-slate-800">{file.name}</p>
            <p className="text-xs text-slate-500">
              {(file.size / 1024).toFixed(1)} KB · {file.type || "unknown"}
            </p>
          </>
        ) : (
          <>
            <p className="font-medium text-slate-700">
              Drop an image here or click to choose
            </p>
            <p className="text-xs text-slate-500">
              JPEG, PNG, WebP, GIF · up to 10 MB
            </p>
          </>
        )}
      </div>

      {file ? (
        <>
          <TextField
            label="Title"
            value={title}
            onChange={setTitle}
            placeholder="Example: Herbal Hair Oil"
            help="WordPress media title."
          />
          <TextField
            label="Alt text"
            value={altText}
            onChange={setAltText}
            placeholder="Example: Bottle of herbal hair oil on a wooden table"
            help="Important for accessibility and SEO."
            maxLength={125}
            showCounter
          />
          <TextField
            label="Caption"
            value={caption}
            onChange={setCaption}
            placeholder="Example: Our best-selling hair oil."
            help="Shown below the image when inserted into content."
          />
          <TextField
            label="Description"
            value={description}
            onChange={setDescription}
            placeholder="Example: 100ml amber glass bottle with dropper cap."
            help="Full description of the media item."
          />
        </>
      ) : null}

      {uploading ? (
        <div className="mb-3">
          <div className="mb-1 flex justify-between text-xs text-slate-500">
            <span>Uploading…</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-surface-muted">
            <div
              className="h-full bg-brand transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : null}

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={() => {
            setFile(null);
            setTitle("");
            setAltText("");
            setCaption("");
            setDescription("");
            if (fileRef.current) fileRef.current.value = "";
          }}
          disabled={uploading || !file}
          className="rounded border border-surface-border px-4 py-2 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
        >
          Clear
        </button>
        <button
          type="button"
          onClick={() => void handleUpload()}
          disabled={uploading || !file}
          className="inline-flex items-center gap-2 rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {uploading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Uploading…
            </>
          ) : (
            "Upload to WordPress"
          )}
        </button>
      </div>
    </div>
  );
}