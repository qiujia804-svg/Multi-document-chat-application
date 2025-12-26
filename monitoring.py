import time
import psutil
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import sentry_sdk
import structlog
from datetime import datetime
import redis
import os

class Monitoring:
    """监控管理类，负责收集应用指标和错误追踪"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        
        # 初始化 Prometheus 指标
        self._init_metrics()
        
        # 初始化 Sentry
        self._init_sentry()
        
        # 初始化 Redis 连接
        self._init_redis()
        
        # 启动系统指标收集
        self._start_system_metrics()
    
    def _init_metrics(self):
        """初始化 Prometheus 指标"""
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        self.error_count = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type']
        )
        
        self.active_users = Gauge(
            'active_users',
            'Number of active users'
        )
        
        self.document_processing_time = Histogram(
            'document_processing_duration_seconds',
            'Time spent processing documents'
        )
        
        self.ai_response_time = Histogram(
            'ai_response_duration_seconds',
            'AI model response time',
            ['model']
        )
        
        self.vector_store_size = Gauge(
            'vector_store_size_bytes',
            'Size of vector store in bytes'
        )
    
    def _init_sentry(self):
        """初始化 Sentry 错误追踪"""
        sentry_dsn = os.getenv('SENTRY_DSN')
        if sentry_dsn:
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=0.1,
                environment=os.getenv('ENVIRONMENT', 'development')
            )
    
    def _init_redis(self):
        """初始化 Redis 连接用于指标缓存"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
        except Exception as e:
            self.logger.error("Failed to connect to Redis", error=str(e))
            self.redis_client = None
    
    def _start_system_metrics(self):
        """启动系统指标收集"""
        try:
            self.cpu_percent = Gauge('cpu_usage_percent', 'CPU usage percentage')
            self.memory_usage = Gauge('memory_usage_bytes', 'Memory usage in bytes')
            self.disk_usage = Gauge('disk_usage_bytes', 'Disk usage in bytes')
        except Exception as e:
            self.logger.error("Failed to initialize system metrics", error=str(e))
    
    def update_system_metrics(self):
        """更新系统指标"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent()
            self.cpu_percent.set(cpu_percent)
            
            # 内存使用
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.used)
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            self.disk_usage.set(disk.used)
            
            if self.redis_client:
                # 缓存指标到 Redis
                metrics = {
                    'cpu_percent': cpu_percent,
                    'memory_used': memory.used,
                    'disk_used': disk.used,
                    'timestamp': datetime.now().isoformat()
                }
                self.redis_client.hmset('system_metrics', metrics)
                
        except Exception as e:
            self.logger.error("Failed to update system metrics", error=str(e))
    
    def log_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录 HTTP 请求指标"""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def log_error(self, error_type: str, error_message: str):
        """记录错误指标"""
        self.error_count.labels(error_type=error_type).inc()
        self.logger.error("Error occurred", error_type=error_type, message=error_message)
        
        # 发送到 Sentry
        if os.getenv('SENTRY_DSN'):
            sentry_sdk.capture_exception(error_message)
    
    def log_document_processing(self, duration: float, file_size: int):
        """记录文档处理指标"""
        self.document_processing_time.observe(duration)
        self.logger.info(
            "Document processed",
            duration=duration,
            file_size=file_size
        )
    
    def log_ai_response(self, model: str, duration: float, token_count: int):
        """记录 AI 响应指标"""
        self.ai_response_time.labels(model=model).observe(duration)
        self.logger.info(
            "AI response received",
            model=model,
            duration=duration,
            token_count=token_count
        )
    
    def update_active_users(self, count: int):
        """更新活跃用户数"""
        self.active_users.set(count)
    
    def update_vector_store_size(self, size: int):
        """更新向量存储大小"""
        self.vector_store_size.set(size)
    
    def get_metrics(self) -> str:
        """获取所有 Prometheus 指标"""
        return generate_latest()
    
    def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        try:
            # 检查 Redis 连接
            if self.redis_client:
                self.redis_client.ping()
                status['checks']['redis'] = 'healthy'
            else:
                status['checks']['redis'] = 'disabled'
        except Exception as e:
            status['checks']['redis'] = f'unhealthy: {str(e)}'
            status['status'] = 'degraded'
        
        # 检查磁盘空间
        disk = psutil.disk_usage('/')
        free_percent = (disk.free / disk.total) * 100
        if free_percent < 10:
            status['checks']['disk'] = f'low space: {free_percent:.1f}% free'
            status['status'] = 'degraded'
        else:
            status['checks']['disk'] = f'{free_percent:.1f}% free'
        
        # 检查内存使用
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            status['checks']['memory'] = f'high usage: {memory.percent:.1f}%'
            status['status'] = 'degraded'
        else:
            status['checks']['memory'] = f'{memory.percent:.1f}% used'
        
        return status