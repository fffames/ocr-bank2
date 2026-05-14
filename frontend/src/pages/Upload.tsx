import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, X, AlertCircle, Loader2, FileText, CheckCircle } from 'lucide-react';
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
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4 sm:mb-6">Upload Receipts</h1>

      {/* Upload Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 sm:p-12 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto h-10 w-10 sm:h-12 sm:w-12 text-gray-400 mb-3 sm:mb-4" />
        <p className="text-base sm:text-lg text-gray-700 mb-2">
          Drag and drop receipt images here
        </p>
        <p className="text-xs sm:text-sm text-gray-500 mb-3 sm:mb-4">
          Supports JPG, PNG, and other image formats
        </p>
        <label className="inline-block bg-blue-600 text-white px-4 sm:px-6 py-2 rounded-md hover:bg-blue-700 transition-colors cursor-pointer text-sm sm:text-base">
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
        <div className="mt-3 sm:mt-4 p-3 sm:p-4 bg-red-50 border border-red-200 rounded-md flex items-center gap-2">
          <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-red-600 flex-shrink-0" />
          <p className="text-xs sm:text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* File Preview List */}
      {files.length > 0 && (
        <div className="mt-6 sm:mt-8">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3 sm:mb-4">
            Selected Files ({files.length})
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
            {files.map((fileWithPreview, index) => (
              <div
                key={index}
                className="relative group bg-white border border-gray-200 rounded-lg overflow-hidden"
              >
                <img
                  src={fileWithPreview.preview}
                  alt={fileWithPreview.file.name}
                  className="w-full h-24 sm:h-32 object-cover"
                />
                <div className="p-2">
                  <p className="text-xs sm:text-sm text-gray-700 truncate">{fileWithPreview.file.name}</p>
                  <p className="text-[10px] sm:text-xs text-gray-500">
                    {(fileWithPreview.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="absolute top-1 sm:top-2 right-1 sm:right-2 bg-red-500 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>

          {/* Upload Button */}
          <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row justify-end gap-2 sm:gap-4">
            <button
              onClick={clearAllFiles}
              className="px-4 sm:px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors text-sm sm:text-base"
            >
              Clear All
            </button>
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="px-4 sm:px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed text-sm sm:text-base"
            >
              {isUploading ? 'Processing...' : 'Upload & Process'}
            </button>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {isUploading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50 p-2 sm:p-4">
          <div className="bg-white rounded-lg shadow-xl p-4 sm:p-8 max-w-md w-full mx-2 sm:mx-4 max-h-[95vh] overflow-y-auto">
            {/* Animated Spinner */}
            <div className="flex flex-col items-center">
              <div className="relative mb-4 sm:mb-6">
                <Loader2 className="h-12 w-12 sm:h-16 sm:w-16 text-blue-600 animate-spin" />
                <div className="absolute inset-0 h-12 w-12 sm:h-16 sm:w-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
              </div>

              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Processing Receipts</h2>
              <p className="text-gray-600 text-center mb-4 sm:mb-6 text-sm sm:text-base">
                Analyzing {files.length} file{files.length > 1 ? 's' : ''} with OCR...
              </p>

              {/* File List */}
              <div className="w-full space-y-2 mb-4 sm:mb-6">
                <div className="flex items-center justify-between text-xs sm:text-sm text-gray-700 mb-2">
                  <span>Files to process:</span>
                  <span className="font-semibold">{files.length}</span>
                </div>

                {/* Animated Progress Bars */}
                {files.slice(0, 3).map((file, index) => (
                  <div key={index} className="flex items-center gap-2 sm:gap-3 p-2 bg-gray-50 rounded-md">
                    <FileText className="h-4 w-4 text-blue-600 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] sm:text-xs font-medium text-gray-700 truncate">
                        {file.file.name}
                      </p>
                      <div className="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-600 rounded-full animate-pulse"
                          style={{
                            width: '100%',
                            animationDelay: `${index * 0.2}s`,
                            animationDuration: '1.5s'
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}

                {files.length > 3 && (
                  <p className="text-[10px] sm:text-xs text-gray-500 text-center pt-2">
                    +{files.length - 3} more file{files.length - 3 > 1 ? 's' : ''}
                  </p>
                )}
              </div>

              {/* Processing Steps */}
              <div className="w-full space-y-2 sm:space-y-3 text-left">
                <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm text-gray-700">
                  <div className="h-4 w-4 sm:h-5 sm:w-5 rounded-full bg-blue-100 flex items-center justify-center">
                    <Loader2 className="h-2 w-2 sm:h-3 sm:w-3 text-blue-600 animate-spin" />
                  </div>
                  <span>Uploading images...</span>
                </div>
                <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm text-gray-700">
                  <div className="h-4 w-4 sm:h-5 sm:w-5 rounded-full bg-blue-100 flex items-center justify-center">
                    <Loader2 className="h-2 w-2 sm:h-3 sm:w-3 text-blue-600 animate-spin" style={{ animationDelay: '0.5s' }} />
                  </div>
                  <span>Detecting receipt template...</span>
                </div>
                <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm text-gray-700">
                  <div className="h-4 w-4 sm:h-5 sm:w-5 rounded-full bg-blue-100 flex items-center justify-center">
                    <Loader2 className="h-2 w-2 sm:h-3 sm:w-3 text-blue-600 animate-spin" style={{ animationDelay: '1s' }} />
                  </div>
                  <span>Extracting text with OCR...</span>
                </div>
                <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm text-gray-700">
                  <div className="h-4 w-4 sm:h-5 sm:w-5 rounded-full bg-green-100 flex items-center justify-center">
                    <CheckCircle className="h-2 w-2 sm:h-3 sm:w-3 text-green-600" />
                  </div>
                  <span>Classifying transaction...</span>
                </div>
              </div>

              <p className="text-[10px] sm:text-xs text-gray-500 text-center mt-4 sm:mt-6">
                This may take 10-30 seconds depending on the number of files
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
