from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import markdown

from langchain.schema import BaseMessage, HumanMessage, AIMessage

class ConversationManager:
    """Manages conversation history and export functionality"""
    
    def __init__(self, config: dict):
        self.config = config
        self.max_history = config['conversation'].get('max_history', 20)
        self.context_window = config['conversation'].get('context_window', 4000)
        self.include_document_context = config['conversation'].get('include_document_context', True)
        
        # Initialize conversation history
        self.history: List[BaseMessage] = []
        self.metadata: Dict[str, Any] = {
            'created_at': datetime.now().isoformat(),
            'total_messages': 0,
            'document_sources': set()
        }
    
    def add_message(self, message: BaseMessage, source_documents: Optional[List] = None):
        """Add a message to conversation history"""
        self.history.append(message)
        self.metadata['total_messages'] += 1
        
        # Track document sources if provided
        if source_documents and self.include_document_context:
            for doc in source_documents:
                if 'source' in doc.metadata:
                    self.metadata['document_sources'].add(doc.metadata['source'])
        
        # Trim history if it exceeds max_history
        if len(self.history) > self.max_history * 2:  # *2 because we count both human and AI messages
            self.history = self.history[-self.max_history * 2:]
    
    def get_recent_messages(self, k: Optional[int] = None) -> List[BaseMessage]:
        """Get recent messages from history"""
        if k is None:
            k = self.max_history * 2  # Default to max_history pairs of messages
        return self.history[-k:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.history = []
        self.metadata = {
            'created_at': datetime.now().isoformat(),
            'total_messages': 0,
            'document_sources': set()
        }
    
    def get_context_summary(self) -> str:
        """Generate a summary of conversation context"""
        if not self.history:
            return "No conversation history yet."
        
        recent_messages = self.get_recent_messages(k=4)  # Get last 2 pairs of messages
        context = "\n".join([f"{msg.type}: {msg.content}" for msg in recent_messages])
        
        if self.include_document_context and self.metadata['document_sources']:
            sources = ", ".join(self.metadata['document_sources'])
            context += f"\n\nBased on documents: {sources}"
        
        return context
    
    def export_to_markdown(self, output_path: Optional[str] = None) -> str:
        """Export conversation to Markdown format"""
        markdown_content = []
        
        # Add metadata header
        markdown_content.append("# Conversation Export\n")
        metadata = {
            'Created At': self.metadata['created_at'],
            'Total Messages': self.metadata['total_messages'],
        }
        if self.metadata['document_sources']:
            metadata['Document Sources'] = ", ".join(self.metadata['document_sources'])
        
        for key, value in metadata.items():
            markdown_content.append(f"- {key}: {value}")
        
        markdown_content.append("\n---\n")
        
        # Add conversation content
        for msg in self.history:
            if isinstance(msg, HumanMessage):
                markdown_content.append(f"\n## User\n{msg.content}")
            else:
                markdown_content.append(f"\n## Assistant\n{msg.content}")
        
        result = "\n".join(markdown_content)
        
        # Save to file if path provided
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
        
        return result
    
    def export_to_json(self, output_path: Optional[str] = None) -> str:
        """Export conversation to JSON format"""
        export_data = {
            'metadata': {
                **self.metadata,
                'document_sources': list(self.metadata['document_sources'])
            },
            'messages': [
                {
                    'type': msg.type,
                    'content': msg.content,
                    'timestamp': datetime.now().isoformat()
                }
                for msg in self.history
            ]
        }
        
        result = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Save to file if path provided
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
        
        return result
    
    def export_to_txt(self, output_path: Optional[str] = None) -> str:
        """Export conversation to plain text format"""
        lines = []
        
        # Add metadata header
        lines.append("Conversation Export")
        lines.append("=" * 50)
        lines.append(f"Created At: {self.metadata['created_at']}")
        lines.append(f"Total Messages: {self.metadata['total_messages']}")
        if self.metadata['document_sources']:
            lines.append(f"Document Sources: {', '.join(self.metadata['document_sources'])}")
        lines.append("\n")
        
        # Add conversation content
        for msg in self.history:
            if isinstance(msg, HumanMessage):
                lines.append(f"User:\n{msg.content}\n")
            else:
                lines.append(f"Assistant:\n{msg.content}\n")
        
        result = "\n".join(lines)
        
        # Save to file if path provided
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
        
        return result
    
    def get_token_count(self) -> int:
        """Get estimated token count for conversation history"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            total_tokens = 0
            
            for msg in self.history:
                total_tokens += len(encoding.encode(msg.content))
            
            return total_tokens
        except:
            # Fallback estimation
            return sum(len(msg.content) // 4 for msg in self.history)
    
    def trim_to_token_limit(self):
        """Trim conversation history to fit within token limit"""
        if self.get_token_count() <= self.context_window:
            return
        
        # Remove oldest messages until within limit
        while self.get_token_count() > self.context_window and len(self.history) >= 2:
            # Remove in pairs to maintain conversation flow
            self.history = self.history[2:]
            self.metadata['total_messages'] -= 2