import React, { useState, useRef } from 'react';
import { FILE_SIZE_LIMITS, ALLOWED_MIME_TYPES } from './constants';
import { Upload, FileText } from 'lucide-react';

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

  const isImageFile = (file: File | null): boolean => {
    return !!file && file.type.startsWith('image/');
  };

  const isTextFile = (file: File | null): boolean => {
    return !!file && (file.type.startsWith('text/') || file.type === 'application/pdf');
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

    // Validate MIME type
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
    
    // Use readAsDataURL for all file types (works for images, PDFs, and text files)
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

  const renderPreview = () => {
    if (!file) return null;
    
    if (isImageFile(file)) {
      return (
        <img src={previewUrl} alt="Preview" className="max-h-48 mx-auto rounded-md mb-4" />
      );
    } else {
      return (
        <div className="flex flex-col items-center justify-center p-4">
          <FileText className="mx-auto h-12 w-12 text-white/60" strokeWidth={1.5} />
          <p className="mt-2 text-sm font-medium text-white/90">{file.name}</p>
          <p className="text-xs text-white/50">{getFileTypeDisplay(file)} • {Math.round(file.size / 1024)} KB</p>
        </div>
      );
    }
  };

  const renderEmptyState = () => {
    return (
      <>
        <Upload className="mx-auto h-12 w-12 text-white/40" strokeWidth={1.5} />
        <p className="mt-2 text-sm text-white/80">Drag 'n' drop a file here, or click to select</p>
        <p className="text-xs text-white/50 mt-1">Accepted formats: JPG, PNG, WEBP, GIF, PDF, TXT (Max 10MB)</p>
      </>
    );
  };

  return (
    <div>
      <label className="block text-lg font-medium text-white/80 mb-2">Wine List File</label>
      <div
        ref={dropZoneRef}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors duration-200 bg-glass-surface backdrop-blur-glass ${file ? 'border-wine-gold/70' : isDragOver ? 'border-wine-rose/70 bg-wine-rose/5' : 'border-white/25'}`}
      >
        <input
          type="file"
          accept=".jpg,.png,.webp,.gif,.pdf,.txt"
          onChange={handleFileSelect}
          ref={fileInputRef}
          className="hidden"
          id="wine-file-upload"
        />
        <label htmlFor="wine-file-upload" className="block text-white/80 cursor-pointer">
          {file ? renderPreview() : renderEmptyState()}
        </label>
      </div>
      {file && !error && (
        <p className="text-sm text-white/60 mt-2">
          Selected: {file.name} ({getFileTypeDisplay(file)}, {Math.round(file.size / 1024)} KB)
        </p>
      )}
    </div>
  );
};

export default FileUploader;