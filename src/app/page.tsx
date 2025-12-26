'use client';

import { useState, useCallback } from 'react';
import { FileUpload } from '@/components/FileUpload';
import { ChatInterface } from '@/components/ChatInterface';
import { ModelSelector } from '@/components/ModelSelector';
import { FileText, MessageSquare, Brain, Sparkles, Target, Shield } from 'lucide-react';

export type AIModel = 'deepseek' | 'kimi';

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  chunks?: number;
}

export default function Home() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [selectedModel, setSelectedModel] = useState<AIModel>('deepseek');
  const [isProcessing, setIsProcessing] = useState(false);

  // Add new files to the list
  const handleFilesAdded = useCallback((newFiles: UploadedFile[]) => {
    setFiles(prev => [...prev, ...newFiles]);
    setIsProcessing(true);
  }, []);

  // Update existing file status
  const handleFileStatusChange = useCallback((fileId: string, status: UploadedFile['status'], chunks?: number) => {
    setFiles(prev =>
      prev.map(f => f.id === fileId ? { ...f, status, chunks: chunks ?? f.chunks } : f)
    );

    // Check if all files are done processing
    setFiles(prev => {
      const allDone = prev.every(f => f.status === 'ready' || f.status === 'error');
      if (allDone) {
        setIsProcessing(false);
      }
      return prev;
    });
  }, []);

  const handleRemoveFile = useCallback((fileId: string) => {
    setFiles(prev => {
      const newFiles = prev.filter(f => f.id !== fileId);
      return newFiles;
    });
  }, []);

  // Check if we have any ready files
  const readyFilesCount = files.filter(f => f.status === 'ready').length;
  const isReady = readyFilesCount > 0;

  return (
    <main className="min-h-screen">
      {/* Hero Header */}
      <header className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 text-white py-8 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center justify-center gap-3 mb-3">
            <Brain className="w-10 h-10" />
            <h1 className="text-3xl md:text-4xl font-bold">
              智能决策顾问
            </h1>
          </div>
          <p className="text-center text-blue-100 text-lg">
            你的私人商业智囊团 · 把100本书的精华变成随时可用的决策建议
          </p>

          {/* Value Props */}
          <div className="flex flex-wrap justify-center gap-6 mt-6">
            <div className="flex items-center gap-2 text-sm">
              <Target className="w-4 h-4 text-green-300" />
              <span>减少错误判断</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Sparkles className="w-4 h-4 text-yellow-300" />
              <span>提升决策效率</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Shield className="w-4 h-4 text-red-300" />
              <span>规避常见陷阱</span>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Model Selector */}
        <div className="mb-6">
          <ModelSelector
            selectedModel={selectedModel}
            onModelChange={setSelectedModel}
          />
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Knowledge Base Section */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <FileText className="w-5 h-5 text-blue-500" />
                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                  知识库
                </h2>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                上传销售、营销、直播技巧等书籍，构建你的专属知识库
              </p>
              <FileUpload
                files={files}
                onFilesAdded={handleFilesAdded}
                onFileStatusChange={handleFileStatusChange}
                onRemoveFile={handleRemoveFile}
                isProcessing={isProcessing}
              />
            </div>

            {/* Quick Tips */}
            {isReady && (
              <div className="mt-4 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  💡 使用技巧
                </h3>
                <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                  <li>• 描述具体场景获得针对性建议</li>
                  <li>• 追问"具体怎么做"获得行动步骤</li>
                  <li>• 问"有什么风险"提前避坑</li>
                </ul>
              </div>
            )}
          </div>

          {/* Chat Section */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 h-[650px] flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-purple-500" />
                  <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                    决策咨询
                  </h2>
                </div>
                {isReady && (
                  <span className="text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2 py-1 rounded-full">
                    知识库就绪
                  </span>
                )}
              </div>
              <ChatInterface
                isReady={isReady}
                selectedModel={selectedModel}
                filesCount={readyFilesCount}
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <p>支持 DeepSeek、Kimi 双模型切换</p>
            <p className="mt-1 text-xs">
              每次回答包含：原文引用 · 行动建议 · 案例参考 · 方法论 · 风险提示
            </p>
          </div>
        </footer>
      </div>
    </main>
  );
}
