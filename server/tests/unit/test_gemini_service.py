import os
import pytest
from unittest.mock import patch, MagicMock
from services.gemini_integration_service import GeminiIntegrationService, GeminiAnalysisResult

@pytest.fixture
def gemini_service():
    """Fixture to initialize GeminiIntegrationService in test mode"""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-dummy-gemini-key"}):
        # We need to mock genai.configure and genai.GenerativeModel during initialization
        with patch("google.generativeai.configure") as mock_configure, \
             patch("google.generativeai.GenerativeModel") as mock_model:
            service = GeminiIntegrationService()
            service.mock_model = mock_model
            return service

def test_gemini_service_initialization(gemini_service):
    """Test that Gemini service initializes successfully with dummy or configured key"""
    assert gemini_service.api_key in ["test-dummy-gemini-key", "AIzaSyDs3zJbiAa6d7Q8UoEtTtorKaxKBf6qBZ0"]
    assert gemini_service.initialized is True

def test_gemini_service_uninitialized():
    """Test that Gemini service handles missing key cleanly"""
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=True):
        # Need to clear from config settings too since it's instantiated at import or init
        from config.config import settings
        with patch.object(settings, "GEMINI_API_KEY", None):
            service = GeminiIntegrationService()
            assert service.initialized is False

@pytest.mark.asyncio
async def test_gemini_chat_with_assistant_success(gemini_service):
    """Test that chat_with_assistant successfully generates content using Gemini model"""
    # Mock GenerativeModel.generate_content
    mock_response = MagicMock()
    mock_response.text = "Here is your microclimate adjusted premium explanation..."
    gemini_service.model.generate_content.return_value = mock_response
    
    context = {
        "location": {
            "city": "Bento Gonçalves",
            "state": "RS",
            "latitude": -29.17,
            "longitude": -51.51
        },
        "weather": {
            "temp": 18.0,
            "precip": 12.0,
            "humidity": 80.0
        },
        "microclimate": {
            "type": "montanha",
            "characteristics": ["High altitude", "Frost risk"]
        }
    }
    
    result = await gemini_service.chat_with_assistant(
        message="Qual o prêmio recomendado?",
        context=context,
        history=[]
    )
    
    assert isinstance(result, GeminiAnalysisResult)
    assert result.analysis_type == "chat_response"
    assert "premium explanation" in result.analysis_text
    assert result.confidence_level > 0.8
    assert gemini_service.model.generate_content.called

@pytest.mark.asyncio
async def test_gemini_analyze_climate_report(gemini_service):
    """Test that analyze_climate_report parses technical reports correctly"""
    mock_response = MagicMock()
    mock_response.text = "{\"summary\": \"Executive Summary\", \"risks\": \"High flood risk\"}"
    gemini_service.model.generate_content.return_value = mock_response
    
    result = await gemini_service.analyze_climate_report(
        report_text="Severe drought conditions in the agricultural region...",
        focus_area="drought_assessment"
    )
    
    assert isinstance(result, GeminiAnalysisResult)
    assert result.analysis_type == "climate_report_analysis"
    assert "flood risk" in result.analysis_text

@pytest.mark.asyncio
async def test_gemini_explain_actuarial_decision(gemini_service):
    """Test that explain_actuarial_decision provides clear atuarial insight"""
    mock_response = MagicMock()
    mock_response.text = "This premium rate is derived from historical frequency models."
    gemini_service.model.generate_content.return_value = mock_response
    
    result = await gemini_service.explain_actuarial_decision(
        decision_factors={"frequency": 0.05, "severity": 200000},
        decision_type="premium_calculation"
    )
    
    assert isinstance(result, GeminiAnalysisResult)
    assert result.analysis_type == "actuarial_decision_explanation"
    assert "historical frequency" in result.analysis_text
