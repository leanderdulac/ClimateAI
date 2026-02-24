import pytest
from unittest.mock import patch, MagicMock
from services.cemaden_service import CemadenService
import requests

@pytest.fixture
def cemaden_service():
    return CemadenService()

@patch('requests.Session.get')
def test_get_estacoes_mock(mock_get, cemaden_service):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = [{"codestacao": "123", "nome": "Test Station"}]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    # Call service
    estacoes = cemaden_service.get_estacoes()
    
    # Assertions
    assert len(estacoes) == 1
    assert estacoes[0]["codestacao"] == "123"
    assert estacoes[0]["nome"] == "Test Station"
    
    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    assert "pcds-cadastro/estacoes" in called_url

@patch('requests.Session.get')
def test_get_dados_recentes_mock(mock_get, cemaden_service):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = [{"codestacao": "123", "acumulado": 10.5}]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    # Call service
    dados = cemaden_service.get_dados_recentes()
    
    # Assertions
    assert len(dados) == 1
    assert dados[0]["acumulado"] == 10.5
    
    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    assert "pcds-acum/acumulados-recentes" in called_url

@pytest.mark.integration
def test_get_estacoes_real():
    """
    Test hitting the actual CEMADEN API.
    Verifies that the API returns valid data.
    """
    service = CemadenService()
    try:
        # Note: If SSL errors occur during CI/CD, skip or use session.verify = False inside the service
        estacoes = service.get_estacoes()
        assert isinstance(estacoes, list)
        if len(estacoes) > 0:
            assert isinstance(estacoes[0], dict)
            assert "nome" in estacoes[0] or "codestacao" in estacoes[0] or "municipio" in estacoes[0]
            print(f"Sample station returned: {estacoes[0]}")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"CEMADEN API is unreachable: {e}")

@pytest.mark.integration
def test_get_dados_recentes_real():
    """
    Test hitting the actual CEMADEN API for recent data.
    """
    service = CemadenService()
    try:
        dados = service.get_dados_recentes()
        assert isinstance(dados, list)
        print(f"Received {len(dados)} recent data points")
        if len(dados) > 0:
            assert isinstance(dados[0], dict)
    except requests.exceptions.RequestException as e:
        pytest.skip(f"CEMADEN API is unreachable: {e}")

@pytest.mark.integration
def test_get_dados_pcd_real():
    """
    Test hitting the actual CEMADEN API to get data for a specific PCD.
    We first get a station ID, then request its data.
    """
    service = CemadenService()
    try:
        estacoes = service.get_estacoes()
        if not estacoes:
            pytest.skip("No stations returned to test specific PCD")
        
        # Pick the first staton id available
        codestacao = estacoes[0].get("codestacao")
        if not codestacao:
            pytest.skip("Station data did not contain 'codestacao'")
        
        # Now fetch specific data for this station
        pcd_data = service.get_dados_pcd(codestacao)
        assert isinstance(pcd_data, list)
    except requests.exceptions.RequestException as e:
        pytest.skip(f"CEMADEN API is unreachable: {e}")

