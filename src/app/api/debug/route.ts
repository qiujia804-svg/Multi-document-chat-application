import { NextRequest, NextResponse } from 'next/server';
import { searchVectorStore, getStoredDocuments, getTotalChunksCount } from '@/lib/document-processor';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

// Debug endpoint to see what's being retrieved
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query } = body;

    if (!query) {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 });
    }

    const documents = getStoredDocuments();
    const totalChunks = getTotalChunksCount();
    const chunks = await searchVectorStore(query, 8);

    return NextResponse.json({
      query,
      documents,
      totalChunks,
      retrievedChunks: chunks.length,
      chunks: chunks.map((chunk, index) => ({
        index: index + 1,
        source: chunk.metadata.fileName,
        text: chunk.text,
        preview: chunk.text.substring(0, 200) + '...',
      })),
    });
  } catch (error) {
    console.error('Debug error:', error);
    return NextResponse.json({ error: 'Debug failed' }, { status: 500 });
  }
}
