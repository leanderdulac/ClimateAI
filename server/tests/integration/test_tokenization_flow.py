import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from models.schemas import EventoClimatico, EventoClimaticoTipo
from models.token_schemas import EventoToken
from services.tokenizacao_eventos_service import TokenizacaoEventosService
from services.tokenization_service import TokenizationService

@pytest.fixture
def token_service():
    """Fixture that returns a TokenizacaoEventosService instance with a mocked Blockchain Service."""
    service = TokenizacaoEventosService()
    # Ensure we are using a mock for the blockchain part to avoid external calls during tests
    # forcing mock mode logic or using unittest.mock
    service.blockchain_service.mock_mode = True 
    return service

@pytest.mark.integration
class TestTokenizationFlow:
    
    def test_complete_tokenization_flow(self, token_service):
        """
        Tests the full lifecycle:
        1. Event Data -> Token Structure Generation
        2. Token Structure -> Blockchain Minting (Mocked)
        3. Verification of Metadata updates
        """
        # 1. Create a simulated climate event (High Severity Flood)
        evento = EventoClimatico(
            tipo=EventoClimaticoTipo.ENCHENTE,
            latitude=-23.5505,
            longitude=-46.6333,
            data_inicio=datetime.now(),
            data_fim=datetime.now() + timedelta(days=2),
            intensidade=4.8,  # High intensity
            probabilidade=0.95,
            descricao="Severe flooding in Sao Paulo metropolitan area",
            nivel_alerta=5
        )

        # 2. Generate the Token Structure (Business Logic)
        token = token_service.gerar_token_evento(evento)
        
        assert isinstance(token, EventoToken)
        assert token.severity_level >= 4
        assert token.metadata["on_chain_status"] == "pending"
        assert token.metadata["tx_hash"] is None

        # 3. Mint the Token on Blockchain (Infrastructure)
        # Using a dummy Ethereum address
        dest_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        
        result = token_service.mint_token_on_chain(token, dest_address)

        # 4. Verification
        assert result["status"] == "success"
        assert "tx_hash" in result
        
        # Check if the token object was updated in place
        assert token.metadata["on_chain_status"] == "minted"
        assert token.metadata["tx_hash"] == result["tx_hash"]
        assert token.metadata["minted_amount"] > 0
        
        # Verify the amount logic (Severity * 10)
        expected_amount = token.severity_level * 10
        assert token.metadata["minted_amount"] == expected_amount

    def test_minting_failure_handling(self, token_service):
        """Test how the system handles blockchain failures."""
        
        # Force the blockchain service to raise an exception
        token_service.blockchain_service.mint = MagicMock(side_effect=Exception("Connection Timeout"))
        
        evento = EventoClimatico(
            tipo=EventoClimaticoTipo.SECA,
            latitude=0.0,
            longitude=0.0,
            data_inicio=datetime.now(),
            intensidade=3.0,
            probabilidade=0.8,
            descricao="Test Drought",
            nivel_alerta=3
        )
        
        token = token_service.gerar_token_evento(evento)
        dest_address = "0x123..."
        
        result = token_service.mint_token_on_chain(token, dest_address)
        
        assert result["status"] == "error"
        assert token.metadata["on_chain_status"] == "failed"
        assert "Connection Timeout" in token.metadata["error"]

    def test_mock_mode_behavior(self):
        """Explicitly test that the underlying TokenizationService defaults to mock mode without config."""
        # Unset env vars just in case (though they shouldn't be set in test env usually)
        with patch.dict('os.environ', {}, clear=True):
            svc = TokenizationService()
            assert svc.mock_mode is True
            
            # Should still return a success-like receipt
            receipt = svc.mint("0x123", 100)
            assert receipt["status"] == 1
            assert receipt["mock"] is True
