"""
Configuration settings for Sliding Window LLM Pipeline
"""
import os
from typing import Optional

# vLLM Server Configuration
VLLM_HOST = os.getenv("VLLM_HOST", "127.0.0.1")
VLLM_PORT = os.getenv("VLLM_PORT", "8000")
VLLM_BASE_URL = f"http://{VLLM_HOST}:{VLLM_PORT}/v1"

# Model Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")

# API Configuration
OPENAI_BASE = VLLM_BASE_URL
MODEL = MODEL_NAME

# Window Configuration
DEFAULT_WINDOW_TOKENS = int(os.getenv("WINDOW_TOKENS", "5000"))
DEFAULT_OVERLAP_RATIO = float(os.getenv("OVERLAP_RATIO", "0.15"))
DEFAULT_MIN_TOKENS = int(os.getenv("MIN_TOKENS", "100"))

# Analysis Configuration
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.2"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "1200"))
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "120"))

# Log Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# File Paths
DEFAULT_LOG_PATH = os.getenv("DEFAULT_LOG_PATH", "./test_log.txt")
DEFAULT_OUTPUT_PATH = os.getenv("DEFAULT_OUTPUT_PATH", "./analysis_results.json")
REALTIME_LOG_PATH = os.getenv("REALTIME_LOG_PATH", "./realtime.log")

# Security Configuration
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
API_KEY = os.getenv("API_KEY")  # Optional API key for authentication

# Performance Configuration
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))

def get_vllm_url() -> str:
    """Get the vLLM server URL"""
    return VLLM_BASE_URL

def get_model_name() -> str:
    """Get the model name"""
    return MODEL_NAME

def is_development() -> bool:
    """Check if running in development mode"""
    return os.getenv("ENVIRONMENT", "development").lower() == "development"

def is_production() -> bool:
    """Check if running in production mode"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"

def get_allowed_hosts() -> list:
    """Get list of allowed hosts"""
    return ALLOWED_HOSTS

def validate_config() -> bool:
    """Validate configuration settings"""
    try:
        # Validate numeric values
        assert DEFAULT_WINDOW_TOKENS > 0, "WINDOW_TOKENS must be positive"
        assert 0 < DEFAULT_OVERLAP_RATIO < 1, "OVERLAP_RATIO must be between 0 and 1"
        assert DEFAULT_MIN_TOKENS > 0, "MIN_TOKENS must be positive"
        assert DEFAULT_TEMPERATURE >= 0, "TEMPERATURE must be non-negative"
        assert DEFAULT_MAX_TOKENS > 0, "MAX_TOKENS must be positive"
        assert DEFAULT_TIMEOUT > 0, "TIMEOUT must be positive"
        
        # Validate host format
        assert VLLM_HOST, "VLLM_HOST cannot be empty"
        assert VLLM_PORT.isdigit(), "VLLM_PORT must be numeric"
        
        return True
    except AssertionError as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Configuration Settings:")
    print(f"  vLLM URL: {VLLM_BASE_URL}")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Window Tokens: {DEFAULT_WINDOW_TOKENS}")
    print(f"  Overlap Ratio: {DEFAULT_OVERLAP_RATIO}")
    print(f"  Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"  Validation: {'✅ Passed' if validate_config() else '❌ Failed'}")
