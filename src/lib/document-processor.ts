// @ts-ignore - pdf-parse doesn't have type definitions
import pdf from 'pdf-parse';
import mammoth from 'mammoth';

// In-memory storage for vector data (will be replaced with proper vector DB in production)
interface TextChunk {
  id: string;
  text: string;
  metadata: {
    fileName: string;
    chunkIndex: number;
    totalChunks: number;
  };
  embedding?: number[];
}

// Global storage (in production, use a proper vector database)
const vectorStore: Map<string, TextChunk[]> = new Map();

/**
 * Process a document and extract text
 */
export async function processDocument(
  buffer: Buffer,
  fileName: string,
  mimeType: string
): Promise<{ text: string; chunks: TextChunk[] }> {
  let text = '';

  // Extract text based on file type
  if (mimeType === 'application/pdf') {
    const data = await pdf(buffer);
    text = data.text;
  } else if (
    mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
    mimeType === 'application/msword'
  ) {
    const result = await mammoth.extractRawText({ buffer });
    text = result.value;
  }

  // Clean up text
  text = text
    .replace(/\s+/g, ' ')
    .replace(/\n+/g, '\n')
    .trim();

  // Split into chunks
  const chunks = splitIntoChunks(text, fileName);

  return { text, chunks };
}

/**
 * Split text into overlapping chunks
 */
function splitIntoChunks(
  text: string,
  fileName: string,
  chunkSize: number = 1000,
  overlap: number = 200
): TextChunk[] {
  const chunks: TextChunk[] = [];
  let start = 0;
  let chunkIndex = 0;

  while (start < text.length) {
    let end = start + chunkSize;

    // Try to find a natural break point
    if (end < text.length) {
      const nextPeriod = text.indexOf('.', end - 50);
      const nextNewline = text.indexOf('\n', end - 50);
      // Also check for Chinese punctuation
      const nextChinesePeriod = text.indexOf('。', end - 50);

      const breakPoints = [nextPeriod, nextNewline, nextChinesePeriod]
        .filter(p => p !== -1 && p < end + 100);

      if (breakPoints.length > 0) {
        end = Math.min(...breakPoints) + 1;
      }
    }

    const chunkText = text.slice(start, end).trim();

    if (chunkText.length > 0) {
      chunks.push({
        id: `${fileName}-${chunkIndex}`,
        text: chunkText,
        metadata: {
          fileName,
          chunkIndex,
          totalChunks: 0, // Will be updated after
        },
      });
      chunkIndex++;
    }

    start = end - overlap;
  }

  // Update total chunks count
  chunks.forEach(chunk => {
    chunk.metadata.totalChunks = chunks.length;
  });

  return chunks;
}

/**
 * Add chunks to the vector store
 */
export async function addToVectorStore(chunks: TextChunk[], fileName: string): Promise<void> {
  // Store chunks (in production, compute embeddings and store in vector DB)
  vectorStore.set(fileName, chunks);
  console.log(`[VectorStore] Added ${chunks.length} chunks from ${fileName}`);
}

/**
 * Tokenize query for better Chinese support
 * Extracts both words (for English) and character n-grams (for Chinese)
 */
function tokenizeQuery(query: string): string[] {
  const tokens: Set<string> = new Set();
  const lowerQuery = query.toLowerCase();

  // Extract English words (2+ chars)
  const englishWords = lowerQuery.match(/[a-zA-Z]{2,}/g) || [];
  englishWords.forEach(w => tokens.add(w));

  // Extract Chinese characters and short phrases (2-4 chars)
  const chineseChars = lowerQuery.match(/[\u4e00-\u9fff]+/g) || [];
  chineseChars.forEach(phrase => {
    // Add the whole phrase
    if (phrase.length >= 2) {
      tokens.add(phrase);
    }
    // Add 2-gram and 3-gram for longer phrases
    for (let i = 0; i < phrase.length - 1; i++) {
      tokens.add(phrase.slice(i, i + 2)); // 2-gram
      if (i < phrase.length - 2) {
        tokens.add(phrase.slice(i, i + 3)); // 3-gram
      }
    }
  });

  // Also add numbers
  const numbers = lowerQuery.match(/\d+/g) || [];
  numbers.forEach(n => tokens.add(n));

  return Array.from(tokens);
}

/**
 * Calculate relevance score for a chunk
 */
function calculateScore(chunkText: string, tokens: string[]): number {
  const lowerChunk = chunkText.toLowerCase();
  let score = 0;

  for (const token of tokens) {
    // Count occurrences
    let index = 0;
    let count = 0;
    while ((index = lowerChunk.indexOf(token, index)) !== -1) {
      count++;
      index += token.length;
    }

    if (count > 0) {
      // Longer tokens are more valuable
      const tokenWeight = Math.min(token.length, 5);
      score += count * tokenWeight;
    }
  }

  return score;
}

/**
 * Search for relevant chunks with improved algorithm
 */
export async function searchVectorStore(
  query: string,
  topK: number = 5
): Promise<TextChunk[]> {
  const allChunks: TextChunk[] = [];

  vectorStore.forEach(chunks => {
    allChunks.push(...chunks);
  });

  if (allChunks.length === 0) {
    console.log('[Search] No documents in vector store');
    return [];
  }

  console.log(`[Search] Searching ${allChunks.length} chunks for: "${query}"`);

  // Tokenize query with Chinese support
  const tokens = tokenizeQuery(query);
  console.log(`[Search] Tokens: ${tokens.join(', ')}`);

  // Score all chunks
  const scoredChunks = allChunks.map(chunk => ({
    chunk,
    score: calculateScore(chunk.text, tokens),
  }));

  // Sort by score
  scoredChunks.sort((a, b) => b.score - a.score);

  // Get chunks with positive scores
  const matchedChunks = scoredChunks
    .filter(item => item.score > 0)
    .slice(0, topK);

  console.log(`[Search] Found ${matchedChunks.length} matching chunks`);

  // If we have matches, return them
  if (matchedChunks.length > 0) {
    return matchedChunks.map(item => item.chunk);
  }

  // FALLBACK: If no keyword matches, return the first few chunks from each document
  // This ensures the AI always has some context to work with
  console.log('[Search] No keyword matches, using fallback - returning document summaries');

  const fallbackChunks: TextChunk[] = [];
  const chunksPerDoc = Math.ceil(topK / vectorStore.size) || topK;

  vectorStore.forEach((chunks, fileName) => {
    // Get first chunks from each document (usually contains summary/intro)
    const docChunks = chunks.slice(0, chunksPerDoc);
    fallbackChunks.push(...docChunks);
    console.log(`[Search] Fallback: added ${docChunks.length} chunks from ${fileName}`);
  });

  return fallbackChunks.slice(0, topK);
}

/**
 * Get all stored documents
 */
export function getStoredDocuments(): string[] {
  return Array.from(vectorStore.keys());
}

/**
 * Get document chunk count
 */
export function getDocumentChunkCount(fileName: string): number {
  return vectorStore.get(fileName)?.length || 0;
}

/**
 * Get total chunks count
 */
export function getTotalChunksCount(): number {
  let total = 0;
  vectorStore.forEach(chunks => {
    total += chunks.length;
  });
  return total;
}

/**
 * Clear vector store
 */
export function clearVectorStore(): void {
  vectorStore.clear();
  console.log('[VectorStore] Cleared all documents');
}

/**
 * Remove document from vector store
 */
export function removeDocument(fileName: string): boolean {
  const result = vectorStore.delete(fileName);
  if (result) {
    console.log(`[VectorStore] Removed ${fileName}`);
  }
  return result;
}
