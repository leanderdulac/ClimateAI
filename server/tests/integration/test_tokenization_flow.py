import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# DATABASE_ENABLED will be disabled per-test using a fixture to avoid side effects

from models.schemas import EventoClimatico, EventoClimaticoTipo
from models.token_schemas import EventoToken
from services.tokenizacao_eventos_service import TokenizacaoEventosService
from services.tokenization_service import TokenizationService

@pytest.fixture(autouse=True)
def mock_db_disabled(monkeypatch):
    """Fixture that disables the database for these tests to avoid SQLAlchemy initialization issues"""
    monkeypatch.setenv("DATABASE_ENABLED", "false")

@pytest.fixture
def token_service():
    """Fixture that returns a TokenizacaoEventosService instance with a mocked Blockchain Service."""
    service = TokenizacaoEventosService()
    # Ensure we are using a mock for the blockchain part to avoid external calls during tests
    service.blockchain_service.mock_mode = True 
    return service

@pytest.mark.integration
class TestTokenizationFlow:
    
    @pytest.mark.asyncio
    async def test_complete_tokenization_flow(self, token_service):
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
        token = await token_service.gerar_token_evento(evento)
        
        assert isinstance(token, EventoToken)
        assert token.severity_level >= 4
        assert token.metadata["on_chain_status"] == "pending"
        assert token.metadata["tx_hash"] is None

        # 3. Mint the Token on Blockchain (Infrastructure)
        # Using a dummy Ethereum address
        dest_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        
        result = await token_service.mint_token_on_chain(token, dest_address)

        # 4. Verification
        assert result["status"] == "success"
        assert "tx_hash" in result

        # Check if the token object was updated in place
        assert token.metadata["on_chain_status"] == "minted"
        assert token.metadata["tx_hash"] == result["tx_hash"]
        # minted_value é definido pelo serviço (severity_level * 1000)
        assert "minted_value" in token.metadata or "minted_amount" in token.metadata
        minted_value = token.metadata.get("minted_value") or token.metadata.get("minted_amount", 0)
        assert minted_value > 0

        # Verify the amount logic (Severity * 1000 for ERC-3525 value)
        expected_value = token.severity_level * 1000
        assert minted_value == expected_value

    @pytest.mark.asyncio
    async def test_minting_failure_handling(self, token_service):
        """Test how the system handles blockchain failures."""

        # Force the blockchain service to raise an exception
        # Note: mocking an async method requires AsyncMock or a side_effect that returns a coroutine
        # However, for simplicity here, we'll mock the whole method to be async
        async def mock_mint_policy(*args, **kwargs):
            raise Exception("Connection Timeout")
            
        token_service.blockchain_service.mint_policy = mock_mint_policy

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

        token = await token_service.gerar_token_evento(evento)
        dest_address = "0x123..."

        result = await token_service.mint_token_on_chain(token, dest_address)

        assert result["status"] == "error"
        assert token.metadata["on_chain_status"] == "failed"
        assert "Connection Timeout" in token.metadata["error"]

    @pytest.mark.asyncio
    async def test_mock_mode_behavior(self):
        """Explicitly test that the underlying TokenizationService defaults to mock mode without config."""
        # Unset env vars just in case (though they shouldn't be set in test env usually)
        with patch.dict('os.environ', {}, clear=True):
            svc = TokenizationService()
            assert svc.mock_mode is True
            
            # Should still return a success-like receipt
            receipt = await svc.mint("0x123", 100)
            assert receipt["status"] == 1
            assert receipt["mock"] is True
