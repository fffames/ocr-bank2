import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, X, AlertCircle } from 'lucide-react';
import { receiptService } from '../services/receiptService';

interface FileWithPreview {
  file: File;
  preview: string;
}

export default function UploadPage() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (fileList: FileList) => {
    const validFiles = Array.from(fileList).filter(file =>
      file.type.startsWith('image/')
    );

    if (validFiles.length === 0) {
      setError('Please select only image files');
      return;
    }

    const filesWithPreview: FileWithPreview[] = validFiles.map(file => ({
      file: file,
      preview: URL.createObjectURL(file)
    }))

    setFiles(prev => [...prev, ...filesWithPreview]);
    setError(null);
  };

  const removeFile = (index: number) => {
    setFiles(prev => {
      const newFiles = [...prev];
      URL.revokeObjectURL(newFiles[index].preview);
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  const clearAllFiles = () => {
    files.forEach(fw => URL.revokeObjectURL(fw.preview));
    setFiles([]);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // Extract just the File objects
      const filesToUpload = files.map(fw => fw.file);
      const response = await receiptService.uploadImages(filesToUpload);

      // Clean up previews
      files.forEach(fw => URL.revokeObjectURL(fw.preview));

      // Navigate to review page with uploaded receipts
      navigate('/review', { state: { receipts: response.receipts } });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload files. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Upload Receipts</h1>

      {/* Upload Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg text-gray-700 mb-2">
          Drag and drop receipt images here
        </p>
        <p className="text-sm text-gray-500 mb-4">
          Supports JPG, PNG, and other image formats
        </p>
        <label className="inline-block bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors cursor-pointer">
          Browse Files
          <input
            type="file"
            className="hidden"
            multiple
            accept="image/*"
            onChange={handleChange}
          />
        </label>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* File Preview List */}
      {files.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Selected Files ({files.length})
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {files.map((fileWithPreview, index) => (
              <div
                key={index}
                className="relative group bg-white border border-gray-200 rounded-lg overflow-hidden"
              >
                <img
                  src={fileWithPreview.preview}
                  alt={fileWithPreview.file.name}
                  className="w-full h-32 object-cover"
                />
                <div className="p-2">
                  <p className="text-sm text-gray-700 truncate">{fileWithPreview.file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(fileWithPreview.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="absolute top-2 right-2 bg-red-500 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>

          {/* Upload Button */}
          <div className="mt-6 flex justify-end gap-4">
            <button
              onClick={clearAllFiles}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Clear All
            </button>
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isUploading ? 'Processing...' : 'Upload & Process'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
