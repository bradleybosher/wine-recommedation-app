import React, { useState, useRef, useEffect } from 'react';
import { FILE_SIZE_LIMITS, ALLOWED_MIME_TYPES } from './constants';
import { Upload, FileText } from 'lucide-react';
import { INK, INK_SOFT, RULE } from '@/design/tokens';

interface FileUploaderProps {
  onFileChange: (file: File | null, previewUrl: string, base64: string, errorMsg: string) => void;
  file: File | null;
  previewUrl: string;
  error: string;
}

const FileUploader: React.FC<FileUploaderProps> = ({ onFileChange, file, previewUrl, error }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // When parent resets file to null (e.g. "New Search"), clear the DOM input so
  // re-selecting the same file fires onChange correctly.
  useEffect(() => {
    if (!file && fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [file]);

  const isImageFile = (file: File | null): boolean => {
    return !!file && file.type.startsWith('image/');
  };

  const getFileTypeDisplay = (file: File | null): string => {
    if (!file) return '';
    if (file.type.startsWith('image/')) return 'Image';
    if (file.type === 'application/pdf') return 'PDF Document';
    if (file.type.startsWith('text/')) return 'Text File';
    return 'File';
  };

  const handleFileChange = (file: File | null) => {
    if (!file) return;

    if (!ALLOWED_MIME_TYPES.includes(file.type)) {
      onFileChange(null, '', '', `Invalid file type. Please upload an image, PDF, or text file.`);
      return;
    }

    if (file.size > FILE_SIZE_LIMITS.MAX_BYTES) {
      onFileChange(null, '', '', 'File is too large. Please upload a file smaller than 10MB.');
      return;
    }

    if (file.size > FILE_SIZE_LIMITS.WARN_BYTES) {
      console.warn('File size is over 5MB. It might take longer to upload.');
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result;
      if (typeof result === 'string') {
        const base64Data = result.split(',')[1] || '';
        onFileChange(file, result, base64Data, '');
      } else {
        onFileChange(null, '', '', 'Failed to read file');
      }
    };
    reader.onerror = () => {
      onFileChange(null, '', '', `Couldn't read file. Try uploading again.`);
    };
    reader.readAsDataURL(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    const file = e.target.files?.[0] || null;
    handleFileChange(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileChange(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = 'copy';
  };

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const dropZoneStyle: React.CSSProperties = {
    border: `1px solid ${file ? INK : isDragOver ? INK_SOFT : RULE}`,
    padding: '28px 24px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'border-color 0.15s',
    background: isDragOver ? 'rgba(31,18,10,0.03)' : 'transparent',
  };

  const renderPreview = () => {
    if (!file) return null;
    if (isImageFile(file)) {
      return (
        <img src={previewUrl} alt="Preview" style={{ maxHeight: 160, margin: '0 auto 12px', display: 'block' }} />
      );
    }
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '8px 0' }}>
        <FileText style={{ width: 32, height: 32, color: INK_SOFT, marginBottom: 8 }} strokeWidth={1.5} />
        <div style={{ fontFamily: "'EB Garamond', serif", fontSize: 14, color: INK }}>{file.name}</div>
        <div style={{ fontFamily: "'EB Garamond', serif", fontSize: 12, color: INK_SOFT, marginTop: 2 }}>
          {getFileTypeDisplay(file)} · {Math.round(file.size / 1024)} KB
        </div>
      </div>
    );
  };

  const renderEmptyState = () => (
    <>
      <Upload style={{ width: 28, height: 28, color: INK_SOFT, margin: '0 auto 10px', display: 'block', opacity: 0.5 }} strokeWidth={1.5} />
      <div
        style={{
          fontFamily: "'Cormorant Garamond', serif",
          fontStyle: 'italic',
          fontSize: 10,
          letterSpacing: 3,
          textTransform: 'uppercase',
          color: INK_SOFT,
          marginBottom: 4,
        }}
      >
        Drop a file here or click to browse
      </div>
      <div style={{ fontFamily: "'EB Garamond', serif", fontSize: 12, color: INK_SOFT, opacity: 0.6 }}>
        JPG · PNG · PDF · TXT — max 10 MB
      </div>
    </>
  );

  return (
    <div>
      <div
        style={{
          fontFamily: "'Cormorant Garamond', serif",
          fontSize: 10,
          letterSpacing: 2,
          textTransform: 'uppercase',
          color: INK_SOFT,
          marginBottom: 8,
        }}
      >
        File
      </div>
      <div
        ref={dropZoneRef}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={dropZoneStyle}
      >
        <input
          type="file"
          accept=".jpg,.png,.webp,.gif,.pdf,.txt"
          onChange={handleFileSelect}
          ref={fileInputRef}
          style={{ display: 'none' }}
          id="wine-file-upload"
        />
        <label htmlFor="wine-file-upload" style={{ display: 'block', cursor: 'pointer' }}>
          {file ? renderPreview() : renderEmptyState()}
        </label>
      </div>
      {file && !error && (
        <div style={{ fontFamily: "'EB Garamond', serif", fontSize: 12, color: INK_SOFT, marginTop: 6 }}>
          {file.name} · {Math.round(file.size / 1024)} KB
        </div>
      )}
      {file && isImageFile(file) && !error && (
        <div style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: 12, color: INK_SOFT, marginTop: 2, opacity: 0.7 }}>
          Photo uploads use OCR — crop out glare and ensure text is sharp.
        </div>
      )}
    </div>
  );
};

export default FileUploader;
