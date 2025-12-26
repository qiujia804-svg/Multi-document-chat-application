from typing import Dict, Any, Optional
import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
        
    def _load_config(self):
        """Load configuration from YAML file and environment variables"""
        try:
            # Load environment variables
            load_dotenv()
            
            # Load YAML configuration
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # Override with environment variables if exists
            self._override_with_env()
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {str(e)}")
    
    def _override_with_env(self):
        """Override configuration values with environment variables"""
        env_overrides = {
            'documents.max_file_size': os.getenv('MAX_FILE_SIZE'),
            'documents.chunk_size': os.getenv('CHUNK_SIZE'),
            'documents.chunk_overlap': os.getenv('CHUNK_OVERLAP'),
            'ai_services.openai.api_key': os.getenv('OPENAI_API_KEY'),
            'ai_services.deepseek.api_key': os.getenv('DEEPSEEK_API_KEY'),
            'ai_services.kimi.api_key': os.getenv('KIMI_API_KEY'),
            'vector_store.type': os.getenv('VECTOR_DB_TYPE'),
            'vector_store.persist_directory': os.getenv('VECTOR_STORE_PATH'),
        }
        
        for key, value in env_overrides.items():
            if value is not None:
                self._set_nested_value(key, value)
    
    def _set_nested_value(self, key: str, value: Any):
        """Set nested configuration value using dot notation"""
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Convert string to appropriate type
        if isinstance(value, str):
            if value.replace('.', '').isdigit():
                value = float(value) if '.' in value else int(value)
            elif value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            
        current[keys[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        try:
            keys = key.split('.')
            current = self.config
            
            for k in keys:
                current = current[k]
            
            return current
        
        except (KeyError, TypeError):
            return default
    
    def get_ai_config(self, service_name: str) -> Dict[str, Any]:
        """Get AI service configuration"""
        ai_config = self.get(f'ai_services.{service_name}')
        if not ai_config or not ai_config.get('enabled', False):
            raise ValueError(f"AI service {service_name} is not enabled")
        
        # Add API key from environment if not present
        env_key = f"{service_name.upper()}_API_KEY"
        api_key = os.getenv(env_key)
        if api_key:
            ai_config['api_key'] = api_key
        
        return ai_config
    
    def validate_api_keys(self) -> None:
        """Validate required API keys are present"""
        required_keys = {
            'OPENAI_API_KEY': 'openai',
            'DEEPSEEK_API_KEY': 'deepseek',
            'KIMI_API_KEY': 'kimi'
        }
        
        missing_keys = []
        for env_key, service_name in required_keys.items():
            if not os.getenv(env_key) and self.get(f'ai_services.{service_name}.enabled'):
                missing_keys.append(f"{env_key} (for {service_name})")
        
        if missing_keys:
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        try:
            for key, value in updates.items():
                self._set_nested_value(key, value)
            
            # Save updated configuration
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        
        except Exception as e:
            raise RuntimeError(f"Failed to update configuration: {str(e)}")