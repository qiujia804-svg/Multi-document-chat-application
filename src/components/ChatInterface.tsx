'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, AlertCircle, BookOpen, CheckCircle, Tag } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { AIModel } from '@/app/page';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
  model?: string;
}

interface ChatInterfaceProps {
  isReady: boolean;
  selectedModel: AIModel;
  filesCount: number;
}

// New section colors for strict citation mode
const sectionColors: Record<string, string> = {
  '📖 原文引用': 'border-blue-500 bg-blue-50 dark:bg-blue-900/20',
  '📖 相关内容': 'border-blue-500 bg-blue-50 dark:bg-blue-900/20',
  '💡 综合分析': 'border-amber-500 bg-amber-50 dark:bg-amber-900/20',
};

export function ChatInterface({ isReady, selectedModel, filesCount }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !isReady || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          model: selectedModel,
          history: messages.slice(-10).map(m => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        sources: data.sources,
        model: data.model,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError('获取回复失败，请重试');
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getModelDisplayName = (model: AIModel) => {
    const names: Record<AIModel, string> = {
      deepseek: 'DeepSeek',
      kimi: 'Kimi',
    };
    return names[model];
  };

  // Render structured response
  const renderStructuredResponse = (content: string) => {
    const sections = [
      '### 📖 原文引用',
      '### 📖 相关内容',
      '### 💡 综合分析',
    ];

    const hasStructure = sections.some(s => content.includes(s));

    if (!hasStructure) {
      return (
        <ReactMarkdown className="prose prose-sm dark:prose-invert max-w-none">
          {content}
        </ReactMarkdown>
      );
    }

    const parts: { title: string; content: string }[] = [];
    let currentSection = '';
    let currentContent = '';

    const lines = content.split('\n');

    for (const line of lines) {
      const sectionMatch = sections.find(s => line.startsWith(s));
      if (sectionMatch) {
        if (currentSection) {
          parts.push({ title: currentSection, content: currentContent.trim() });
        }
        currentSection = sectionMatch.replace('### ', '');
        currentContent = '';
      } else if (currentSection) {
        currentContent += line + '\n';
      }
    }

    if (currentSection) {
      parts.push({ title: currentSection, content: currentContent.trim() });
    }

    return (
      <div className="space-y-4">
        {parts.map((part, index) => (
          <div
            key={index}
            className={`border-l-4 rounded-r-lg p-4 ${sectionColors[part.title] || 'border-gray-300 bg-gray-50 dark:bg-gray-800'}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{part.title.split(' ')[0]}</span>
              <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                {part.title.split(' ').slice(1).join(' ')}
              </h4>
            </div>
            <div className="text-sm text-gray-700 dark:text-gray-300">
              <ReactMarkdown className="prose prose-sm dark:prose-invert max-w-none prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:bg-white prose-blockquote:dark:bg-gray-800 prose-blockquote:py-1 prose-blockquote:px-4 prose-blockquote:rounded">
                {part.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {!isReady ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 dark:text-gray-400">
            <Bot className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg font-medium">请先上传知识库文档</p>
            <p className="text-sm">上传 PDF 或 Word 文档后开始查询</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 dark:text-gray-400">
            <Bot className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg font-medium">知识库已就绪</p>
            <p className="text-sm">已加载 {filesCount} 个文档，使用 {getModelDisplayName(selectedModel)}</p>
            <div className="mt-4 text-left bg-gray-100 dark:bg-gray-700 rounded-lg p-4 max-w-md">
              <p className="text-sm font-medium mb-2">💡 试试这样问：</p>
              <ul className="text-xs space-y-1 text-gray-600 dark:text-gray-400">
                <li>• 关于XX的内容有哪些？</li>
                <li>• 文档中提到的XX方法是什么？</li>
                <li>• 帮我找出关于XX的原文</li>
              </ul>
            </div>
          </div>
        ) : (
          <>
            {messages.map(message => (
              <div
                key={message.id}
                className={`flex gap-3 message-enter ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === 'user'
                      ? 'bg-primary-500 text-white'
                      : 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
                  }`}
                >
                  {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-primary-500 text-white'
                      : 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 shadow-md'
                  }`}
                >
                  {message.role === 'assistant' ? (
                    <>
                      {renderStructuredResponse(message.content)}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-600">
                          <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                            <BookOpen className="w-3 h-3" />
                            来源: {message.sources.join(', ')}
                          </p>
                          {message.model && (
                            <p className="text-xs text-gray-400 mt-1">由 {message.model} 处理</p>
                          )}
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="text-sm">{message.content}</p>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-white dark:bg-gray-700 rounded-2xl px-4 py-3 shadow-md">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                    <span className="text-sm text-gray-500">正在检索知识库...</span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 mb-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isReady ? '输入问题，从知识库中查询...' : '请先上传文档'}
          disabled={!isReady || isLoading}
          className="flex-1 px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={!isReady || isLoading || !input.trim()}
          className="px-4 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
        </button>
      </form>
    </div>
  );
}
