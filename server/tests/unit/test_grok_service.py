import os
import pytest
from unittest.mock import patch, MagicMock
from services.grok_integration_service import GrokIntegrationService, GrokAnalysisResult

@pytest.fixture
def grok_service():
    """Fixture to initialize GrokIntegrationService in test mode"""
    with patch.dict(os.environ, {"GROK_API_KEY": "test-dummy-grok-key"}):
        service = GrokIntegrationService()
        return service

def test_grok_service_initialization(grok_service):
    """Test that Grok service initializes with correct settings and falls back to mock under dummy key"""
    assert grok_service.api_key == "test-dummy-grok-key"
    assert grok_service.use_mock is True
    assert grok_service.base_url == "https://api.x.ai/v1"
    assert "Authorization" in grok_service.headers
    assert grok_service.headers["Authorization"] == "Bearer test-dummy-grok-key"

def test_grok_service_mock_climate_analysis(grok_service):
    """Test that mock climate analysis returns valid structure and text"""
    data = {
        "location": "São Paulo",
        "temperature": 27.5,
        "precipitation": 120.0
    }
    result = grok_service.analyze_climate_data(data, "parametric_insurance")
    assert isinstance(result, GrokAnalysisResult)
    assert result.analysis_type == "parametric_insurance"
    assert "VIABILIDADE DE SEGUROS PARAMÉTRICOS" in result.analysis_text
    assert result.confidence_level > 0.8

def test_grok_service_mock_insights(grok_service):
    """Test that mock insights returns valid regional observations"""
    result = grok_service.generate_climate_insights("São Paulo", "12_months")
    assert isinstance(result, GrokAnalysisResult)
    assert result.analysis_type == "climate_insights"
    assert "INSIGHTS CLIMÁTICOS ESPECIALIZADOS" in result.analysis_text
    assert "são paulo" in result.analysis_text.lower()

def test_grok_model_info(grok_service):
    """Test that model info endpoint returns correct capabilities and status"""
    info = grok_service.get_model_info()
    assert info["model_name"] == "Grok (xAI)"
    assert "grok-beta" in info["version"]
    assert "Análise climática" in info["capabilities"]

@patch("requests.post")
def test_grok_service_live_api_call(mock_post, grok_service):
    """Test that live API call is successfully executed when use_mock is False"""
    grok_service.use_mock = False
    
    # Mock requests response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Live Grok analysis text for agricultural risks under SUSEP Circular 591/2016."
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    data = {"location": "Mato Grosso", "crop": "soja"}
    result = grok_service.analyze_climate_data(data, "agricultural")
    
    assert isinstance(result, GrokAnalysisResult)
    assert result.analysis_type == "agricultural"
    assert "Live Grok" in result.analysis_text
    assert mock_post.called
