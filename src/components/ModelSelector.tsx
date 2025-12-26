'use client';

import { AIModel } from '@/app/page';
import { Check } from 'lucide-react';

interface ModelSelectorProps {
  selectedModel: AIModel;
  onModelChange: (model: AIModel) => void;
}

const models: { id: AIModel; name: string; description: string; icon: string }[] = [
  {
    id: 'deepseek',
    name: 'DeepSeek',
    description: '深度求索，高性价比首选',
    icon: '🔍',
  },
  {
    id: 'kimi',
    name: 'Kimi',
    description: 'Moonshot AI，中文理解优秀',
    icon: '🌙',
  },
];

export function ModelSelector({ selectedModel, onModelChange }: ModelSelectorProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
        选择 AI 模型
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {models.map((model) => (
          <button
            key={model.id}
            onClick={() => onModelChange(model.id)}
            className={`
              relative flex items-center gap-3 p-3 rounded-lg border-2 transition-all
              ${
                selectedModel === model.id
                  ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
              }
            `}
          >
            <span className="text-2xl">{model.icon}</span>
            <div className="text-left flex-1">
              <p className="font-medium text-gray-800 dark:text-white text-sm">
                {model.name}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {model.description}
              </p>
            </div>
            {selectedModel === model.id && (
              <Check className="w-5 h-5 text-purple-500 absolute top-2 right-2" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
