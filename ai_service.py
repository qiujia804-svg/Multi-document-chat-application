from typing import Dict, Any, Optional
import os
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain.schema import BaseMessage
import openai

class AIServiceManager:
    """Manages different AI services and their configurations"""
    
    def __init__(self, config: dict):
        self.config = config
        self.services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all enabled AI services"""
        try:
            for service_name, service_config in self.config['ai_services'].items():
                if service_config.get('enabled', False):
                    self.services[service_name] = {
                        'config': service_config,
                        'model': None
                    }
        except Exception as e:
            raise ValueError(f"Error initializing AI services: {str(e)}")
    
    def _get_model(self, service_name: str) -> ChatOpenAI:
        """Get or create AI model instance"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} is not enabled")
        
        service = self.services[service_name]
        if service['model'] is None:
            config = service['config']
            
            # Common parameters
            kwargs = {
                'temperature': config.get('temperature', 0.7),
                'max_retries': config.get('max_retries', 3),
                'timeout': config.get('timeout', 30),
                'max_tokens': config.get('max_tokens', 4000)
            }
            
            # Service-specific configuration
            if service_name == 'openai':
                kwargs.update({
                    'model': config.get('model', 'gpt-3.5-turbo'),
                    'api_key': config.get('api_key') or os.getenv('OPENAI_API_KEY')
                })
            elif service_name == 'deepseek':
                kwargs.update({
                    'model': config.get('model', 'deepseek-chat'),
                    'base_url': config.get('base_url', "https://api.deepseek.com/v1"),
                    'api_key': config.get('api_key') or os.getenv('DEEPSEEK_API_KEY')
                })
            elif service_name == 'kimi':
                kwargs.update({
                    'model': config.get('model', 'moonshot-v1-8k'),
                    'base_url': config.get('base_url', "https://api.moonshot.cn/v1"),
                    'api_key': config.get('api_key') or os.getenv('KIMI_API_KEY')
                })
            
            service['model'] = ChatOpenAI(**kwargs)
        
        return service['model']
    
    def create_conversation_chain(
        self,
        service_name: str,
        vector_store,
        memory_type: str = "buffer",
        k: int = 4
    ) -> ConversationalRetrievalChain:
        """Create conversation chain with specified AI service"""
        model = self._get_model(service_name)
        
        # Configure memory type
        if memory_type == "window":
            memory = ConversationBufferWindowMemory(
                memory_key='chat_history',
                return_messages=True,
                k=self.config['conversation'].get('max_history', 20)
            )
        else:
            memory = ConversationBufferMemory(
                memory_key='chat_history',
                return_messages=True
            )
        
        # Create conversation chain
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=model,
            retriever=vector_store.as_retriever(search_kwargs={"k": k}),
            memory=memory,
            return_source_documents=True,
            verbose=self.config['app'].get('debug', False)
        )
        
        return conversation_chain
    
    def get_available_services(self) -> Dict[str, bool]:
        """Get status of all AI services"""
        status = {}
        for service_name in self.services:
            try:
                self._get_model(service_name)
                status[service_name] = True
            except Exception:
                status[service_name] = False
        return status
    
    async def test_service(self, service_name: str) -> bool:
        """Test if AI service is working"""
        try:
            model = self._get_model(service_name)
            # Send a simple test message
            response = await model.ainvoke("Test")
            return bool(response)
        except Exception as e:
            print(f"Service test failed for {service_name}: {str(e)}")
            return False
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} is not enabled")
        return self.services[service_name]['config']
    
    def update_service_config(self, service_name: str, updates: Dict[str, Any]) -> None:
        """Update configuration for a specific service"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} is not enabled")
        
        self.services[service_name]['config'].update(updates)
        # Reset model instance to apply new configuration
        self.services[service_name]['model'] = None
    
    def get_fallback_service(self, current_service: str) -> Optional[str]:
        """Get next available service for fallback"""
        services = list(self.services.keys())
        current_index = services.index(current_service) if current_service in services else -1
        
        # Try next service
        for i in range(1, len(services)):
            next_service = services[(current_index + i) % len(services)]
            if self.get_available_services().get(next_service, False):
                return next_service
        
        return None
    
    async def get_completion(
        self,
        service_name: str,
        messages: list[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Get completion from specified service"""
        model = self._get_model(service_name)
        
        if temperature is not None:
            model.temperature = temperature
        if max_tokens is not None:
            model.max_tokens = max_tokens
        
        response = await model.ainvoke(messages)
        return response.content