"""
Validation script for multi-provider LLM implementation.

This script validates that the multi-provider architecture is correctly
implemented and that all components work together as expected.
"""

import os
import sys
import json
from unittest.mock import patch, Mock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def validate_imports():
    """Validate that all new modules can be imported correctly."""
    print("🔍 Validating imports...")
    
    try:
        from ai_api.services.base_llm_provider import BaseLLMProvider
        from ai_api.services.gemini_provider import GeminiProvider
        from ai_api.services.groq_provider import GroqProvider
        from ai_api.services.provider_factory import ProviderFactory
        from ai_api.services.llm_service import LLMService
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def validate_base_provider_interface():
    """Validate that the base provider interface is correctly implemented."""
    print("🔍 Validating base provider interface...")
    
    try:
        from ai_api.services.base_llm_provider import BaseLLMProvider
        
        # Check that BaseLLMProvider is an abstract base class
        assert hasattr(BaseLLMProvider, '__abstractmethods__')
        assert 'series_extract' in BaseLLMProvider.__abstractmethods__
        print("✅ Base provider interface correctly defined")
        return True
    except Exception as e:
        print(f"❌ Base provider validation error: {e}")
        return False

def validate_provider_implementations():
    """Validate that all providers implement the base interface correctly."""
    print("🔍 Validating provider implementations...")
    
    try:
        from ai_api.services.gemini_provider import GeminiProvider
        from ai_api.services.groq_provider import GroqProvider
        from ai_api.services.base_llm_provider import BaseLLMProvider
        
        # Check that providers inherit from BaseLLMProvider
        assert issubclass(GeminiProvider, BaseLLMProvider)
        assert issubclass(GroqProvider, BaseLLMProvider)
        
        # Check that providers implement the abstract method
        assert hasattr(GeminiProvider, 'series_extract')
        assert hasattr(GroqProvider, 'series_extract')
        
        print("✅ Provider implementations correct")
        return True
    except Exception as e:
        print(f"❌ Provider implementation error: {e}")
        return False

def validate_provider_factory():
    """Validate that the provider factory works correctly."""
    print("🔍 Validating provider factory...")
    
    try:
        from ai_api.services.provider_factory import ProviderFactory
        
        # Test available providers
        providers = ProviderFactory.get_available_providers()
        assert 'gemini' in providers
        assert 'groq' in providers
        
        # Test provider availability
        assert ProviderFactory.is_provider_available('gemini') is True
        assert ProviderFactory.is_provider_available('groq') is True
        assert ProviderFactory.is_provider_available('openai') is False
        
        print("✅ Provider factory validation successful")
        return True
    except Exception as e:
        print(f"❌ Provider factory error: {e}")
        return False

def validate_llm_service_integration():
    """Validate that LLMService integrates correctly with the provider pattern."""
    print("🔍 Validating LLM service integration...")
    
    try:
        from ai_api.services.llm_service import LLMService
        from ai_api.services.provider_factory import ProviderFactory
        
        # Check that LLMService uses ProviderFactory
        assert hasattr(LLMService, 'provider_factory')
        assert hasattr(LLMService, 'provider')
        
        print("✅ LLM service integration correct")
        return True
    except Exception as e:
        print(f"❌ LLM service integration error: {e}")
        return False

def validate_environment_configuration():
    """Validate that environment configuration is properly set up."""
    print("🔍 Validating environment configuration...")
    
    try:
        from _backend.settings import GROQ_API_KEY, GROQ_MODEL_NAME, LLM_PROVIDER
        
        # These should be None by default (not set in environment)
        assert GROQ_API_KEY is None
        assert GROQ_MODEL_NAME == 'llama3-8b-8192'  # Default value
        assert LLM_PROVIDER == 'gemini'  # Default value
        
        print("✅ Environment configuration correct")
        return True
    except Exception as e:
        print(f"❌ Environment configuration error: {e}")
        return False

def validate_settings_updates():
    """Validate that settings.py has been updated correctly."""
    print("🔍 Validating settings updates...")
    
    try:
        # Check that the required environment variables are defined
        required_vars = ['GROQ_API_KEY', 'GROQ_MODEL_NAME', 'LLM_PROVIDER']
        
        # Import settings to check if variables are accessible
        from _backend import settings
        
        for var in required_vars:
            assert hasattr(settings, var), f"Missing environment variable: {var}"
        
        print("✅ Settings updates correct")
        return True
    except Exception as e:
        print(f"❌ Settings validation error: {e}")
        return False

def run_validation():
    """Run all validation tests."""
    print("🚀 Starting multi-provider LLM implementation validation...\n")
    
    tests = [
        validate_imports,
        validate_base_provider_interface,
        validate_provider_implementations,
        validate_provider_factory,
        validate_llm_service_integration,
        validate_environment_configuration,
        validate_settings_updates,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()  # Add spacing between tests
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"📊 Validation Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validations passed! Multi-provider implementation is ready.")
        return True
    else:
        print("⚠️  Some validations failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)