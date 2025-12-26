import { NextRequest, NextResponse } from 'next/server';
import { chat } from '@/lib/ai-service';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, model, history } = body;

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Get AI response
    const result = await chat(message, model || 'openai', history || []);

    return NextResponse.json({
      response: result.response,
      sources: result.sources,
      model: result.model,
    });
  } catch (error) {
    console.error('Chat error:', error);
    return NextResponse.json(
      { error: 'Failed to get response' },
      { status: 500 }
    );
  }
}
