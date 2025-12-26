'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { UploadedFile } from '@/app/page';
import { v4 as uuidv4 } from 'uuid';

interface FileUploadProps {
  files: UploadedFile[];
  onFilesAdded: (files: UploadedFile[]) => void;
  onFileStatusChange: (fileId: string, status: UploadedFile['status'], chunks?: number) => void;
  onRemoveFile: (fileId: string) => void;
  isProcessing: boolean;
}

export function FileUpload({
  files,
  onFilesAdded,
  onFileStatusChange,
  onRemoveFile,
  isProcessing
}: FileUploadProps) {
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);

    // Create file entries with unique IDs
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      id: uuidv4(),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading' as const,
    }));

    // Add files to state immediately (only once)
    onFilesAdded(newFiles);

    // Upload each file to the API
    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      const uploadedFile = newFiles[i];

      try {
        // Update status to processing
        onFileStatusChange(uploadedFile.id, 'processing');

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Upload failed');
        }

        const result = await response.json();

        // Update file status to ready with chunks count
        onFileStatusChange(uploadedFile.id, 'ready', result.chunks);
      } catch (error) {
        console.error('Upload error:', error);
        onFileStatusChange(uploadedFile.id, 'error');
      }
    }

    setUploading(false);
  }, [onFilesAdded, onFileStatusChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: uploading || isProcessing,
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'ready':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusText = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return '上传中...';
      case 'processing':
        return '处理中...';
      case 'ready':
        return '就绪';
      case 'error':
        return '失败';
    }
  };

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          upload-area cursor-pointer
          ${isDragActive ? 'active border-primary-500 bg-primary-50' : ''}
          ${uploading || isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        {isDragActive ? (
          <p className="text-primary-600 font-medium">释放文件以上传</p>
        ) : (
          <>
            <p className="text-gray-600 dark:text-gray-300 font-medium">
              拖拽文件到这里，或点击选择文件
            </p>
            <p className="text-sm text-gray-400 mt-2">
              支持 PDF、Word 文档 (最大 10MB)
            </p>
          </>
        )}
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            已上传文件 ({files.length})
          </h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {files.map(file => (
              <div
                key={file.id}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <File className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatFileSize(file.size)}
                      {file.status === 'ready' && file.chunks && ` • ${file.chunks} 文本块`}
                      {(file.status === 'uploading' || file.status === 'processing') &&
                        ` • ${getStatusText(file.status)}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(file.status)}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveFile(file.id);
                    }}
                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                    disabled={file.status === 'uploading' || file.status === 'processing'}
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
