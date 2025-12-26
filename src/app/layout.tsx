import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Ask Multiple PDFs - AI Document Chat',
  description: 'Chat with multiple PDFs and Word documents using AI powered by OpenAI, DeepSeek, and Kimi',
  keywords: ['PDF', 'AI', 'Chat', 'Document', 'OpenAI', 'DeepSeek', 'Kimi'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
          {children}
        </div>
      </body>
    </html>
  );
}
