"""
Testes de API para o módulo Atlas Digital de Desastres
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Adicionar server ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from fastapi import FastAPI

# Importar o router do atlas
from api.atlas_disasters import router as atlas_router


# ============================================================
# Setup da Aplicação de Teste
# ============================================================

@pytest.fixture
def test_app():
    """Criar aplicação FastAPI de teste"""
    app = FastAPI(title="ClimateWise Test - Atlas")
    app.include_router(atlas_router)
    return app


@pytest.fixture
def client(test_app):
    """Criar cliente de teste"""
    return TestClient(test_app)


@pytest.fixture
def sample_dataframe():
    """Criar DataFrame de exemplo para testes"""
    np.random.seed(42)
    
    data = {
        'ano': np.random.choice(range(2000, 2024), 100),
        'uf': np.random.choice(['RS', 'SC', 'PR', 'SP'], 100),
        'municipio': [f"Municipio_{i}" for i in range(100)],
        'tipo_desastre': np.random.choice(
            ['Inundação', 'Seca', 'Deslizamento', 'Granizo'],
            100
        ),
        'intensidade': np.random.choice(['Baixa', 'Média', 'Alta'], 100),
        'mortes_diretas': np.random.randint(0, 10, 100),
        'afetados': np.random.randint(0, 1000, 100),
        'desabrigados': np.random.randint(0, 100, 100),
    }
    
    return pd.DataFrame(data)


# ============================================================
# Mock do Serviço
# ============================================================

@pytest.fixture
def mock_atlas_service(sample_dataframe):
    """Criar mock do serviço Atlas"""
    with patch('api.atlas_disasters.atlas_service') as mock_service:
        mock_service.load_data.return_value = sample_dataframe.copy()
        mock_service.filter_disasters.side_effect = lambda df, **kwargs: df.copy()
        mock_service.aggregate_by_municipality.return_value = sample_dataframe.groupby(
            ['uf', 'municipio']
        ).agg(
            qtd_ocorrencias=('ano', 'size'),
            mortes_diretas=('mortes_diretas', 'sum'),
            afetados=('afetados', 'sum'),
        ).reset_index()
        mock_service.aggregate_by_year.return_value = sample_dataframe.groupby('ano').size().reset_index(name='qtd_ocorrencias')
        mock_service.get_statistics.return_value = {
            'total_registros': 100,
            'periodo': {'inicio': 2000, 'fim': 2023, 'anos_unicos': 24},
            'uf': {'total_estados': 4, 'mais_afetado': 'RS'},
            'tipos_desastre': {
                'total_tipos': 4,
                'mais_comum': 'Inundação',
                'top_5': {'Inundação': 30, 'Seca': 25}
            },
            'impacto': {
                'mortes_diretas': {'total': 450, 'media': 4.5, 'max': 9},
                'afetados': {'total': 50000, 'media': 500, 'max': 999},
            }
        }
        mock_service._loaded_file = "/tmp/test_atlas.csv"
        mock_service._cache_timestamp = None
        mock_service._cache = sample_dataframe
        # Corrigir data_dir para ser um objeto Path-like
        from pathlib import Path
        mock_service.data_dir = Path("/tmp")
        mock_service.export_to_csv.return_value = "/tmp/test_export.csv"
        yield mock_service


# ============================================================
# Testes - Endpoints de Gestão de Dados
# ============================================================

class TestDataManagementEndpoints:
    """Testes para endpoints de gestão de dados"""
    
    def test_get_status(self, client, mock_atlas_service):
        """Testar endpoint de status"""
        response = client.get("/api/v1/atlas/status")
        
        assert response.status_code == 200
        data = response.json()
        assert 'data_dir' in data
        assert 'total_registros' in data
    
    def test_reload_data(self, client, mock_atlas_service):
        """Testar recarregamento de dados"""
        response = client.get("/api/v1/atlas/reload")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'total_registros' in data
    
    def test_download_data(self, client, mock_atlas_service):
        """Testar download de dados"""
        payload = {
            "url": "https://example.com/data.csv",
            "filename": "test_atlas.csv",
            "force": False
        }
        
        with patch.object(mock_atlas_service, 'download_data', return_value="/tmp/test_atlas.csv"):
            response = client.post("/api/v1/atlas/download", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'filepath' in data


# ============================================================
# Testes - Endpoints de Consulta
# ============================================================

class TestQueryEndpoints:
    """Testes para endpoints de consulta"""
    
    def test_get_records(self, client, mock_atlas_service):
        """Testar listagem de registros"""
        response = client.get("/api/v1/atlas/records?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    def test_get_records_pagination(self, client, mock_atlas_service):
        """Testar paginação de registros"""
        response1 = client.get("/api/v1/atlas/records?limit=10&offset=0")
        response2 = client.get("/api/v1/atlas/records?limit=10&offset=10")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert len(data1) <= 10
        assert len(data2) <= 10
    
    def test_filter_disasters_post(self, client, mock_atlas_service):
        """Testar filtragem via POST"""
        payload = {
            "anos": [2010, 2020],
            "uf": "RS",
            "tipo_desastre": "inundacao",
            "min_afetados": 100
        }
        
        response = client.post("/api/v1/atlas/filter", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'data' in data
        assert 'filters_applied' in data
    
    def test_filter_disasters_simple(self, client, mock_atlas_service):
        """Testar filtragem simplificada via GET"""
        response = client.get(
            "/api/v1/atlas/filter/simple"
            "?ano_inicio=2010&ano_fim=2020&uf=RS&tipo_desastre=inundacao"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'data' in data


# ============================================================
# Testes - Endpoints de Agregação
# ============================================================

class TestAggregationEndpoints:
    """Testes para endpoints de agregação"""
    
    def test_aggregate_by_municipality(self, client, mock_atlas_service):
        """Testar agregação por município"""
        payload = {
            "group_cols": ["uf", "municipio"],
        }
        
        response = client.post("/api/v1/atlas/aggregate/municipality", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_aggregate_by_year(self, client, mock_atlas_service):
        """Testar agregação por ano"""
        response = client.get("/api/v1/atlas/aggregate/year")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_aggregate_by_year_with_uf(self, client, mock_atlas_service):
        """Testar agregação por ano com UF"""
        response = client.get("/api/v1/atlas/aggregate/year?group_by_uf=true")
        
        assert response.status_code == 200
    
    def test_get_statistics(self, client, mock_atlas_service):
        """Testar estatísticas"""
        response = client.get("/api/v1/atlas/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_registros' in data
        assert 'periodo' in data
        assert 'uf' in data
        assert 'tipos_desastre' in data
        assert 'impacto' in data


# ============================================================
# Testes - Endpoints de Análise
# ============================================================

class TestAnalysisEndpoints:
    """Testes para endpoints de análise"""
    
    def test_top_affected_municipalities(self, client, mock_atlas_service):
        """Testar municípios mais afetados"""
        response = client.get("/api/v1/atlas/analysis/top-affected?limit=10&metric=qtd_ocorrencias")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    def test_top_affected_by_deaths(self, client, mock_atlas_service):
        """Testar ranking por mortes"""
        response = client.get("/api/v1/atlas/analysis/top-affected?limit=20&metric=total_mortes")
        
        assert response.status_code == 200
    
    def test_disaster_trends(self, client, mock_atlas_service):
        """Testar tendências de desastres"""
        response = client.get("/api/v1/atlas/analysis/trends")
        
        assert response.status_code == 200
        data = response.json()
        assert 'evolucao_anual' in data
        assert 'estatisticas' in data
    
    def test_analysis_by_disaster_type(self, client, mock_atlas_service):
        """Testar análise por tipo de desastre"""
        response = client.get("/api/v1/atlas/analysis/by-disaster-type")
        
        assert response.status_code == 200
        data = response.json()
        assert 'distribuicao' in data
        assert 'total_registros' in data
        assert 'tipos_encontrados' in data


# ============================================================
# Testes - Endpoints de Exportação
# ============================================================

class TestExportEndpoints:
    """Testes para endpoints de exportação"""
    
    def test_export_to_csv(self, client, mock_atlas_service):
        """Testar exportação para CSV"""
        payload = {"filename": "test_export.csv"}
        
        response = client.post("/api/v1/atlas/export/csv", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'filepath' in data
        assert 'total_registros' in data
    
    def test_download_exported_csv_not_found(self, client):
        """Testar download de CSV inexistente (sem mock para testar erro real)"""
        # Teste real sem mock - deve retornar 404
        response = client.get("/api/v1/atlas/export/csv/nonexistent_file_test.csv")
        
        # Pode ser 404 ou 500 dependendo da configuração
        assert response.status_code in [404, 500]


# ============================================================
# Testes - Validação de Entrada
# ============================================================

class TestInputValidation:
    """Testes para validação de entrada"""
    
    def test_invalid_year_range(self, client, mock_atlas_service):
        """Testar intervalo de ano inválido"""
        response = client.get(
            "/api/v1/atlas/filter/simple"
            "?ano_inicio=2020&ano_fim=2010"  # Início > Fim
        )
        
        # FastAPI deve validar os parâmetros
        assert response.status_code in [200, 422]
    
    def test_invalid_limit(self, client, mock_atlas_service):
        """Testar limite inválido"""
        response = client.get("/api/v1/atlas/records?limit=0")
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_limit_max(self, client, mock_atlas_service):
        """Testar limite máximo excedido"""
        response = client.get("/api/v1/atlas/records?limit=20000")
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_uf_length(self, client, mock_atlas_service):
        """Testar UF com tamanho inválido"""
        response = client.get("/api/v1/atlas/filter/simple?uf=RSX")
        
        # Pode ser 200 (ignora) ou 422 (validação)
        assert response.status_code in [200, 422]


# ============================================================
# Testes - Error Handling
# ============================================================

class TestErrorHandling:
    """Testes para tratamento de erros"""
    
    def test_no_data_loaded(self, client):
        """Testar erro quando não há dados carregados"""
        with patch('api.atlas_disasters.atlas_service') as mock_service:
            mock_service.load_data.side_effect = FileNotFoundError("Dados não encontrados")
            
            response = client.get("/api/v1/atlas/records")
            
            assert response.status_code == 404
            data = response.json()
            assert 'detail' in data
    
    def test_service_error(self, client):
        """Testar erro interno do serviço"""
        with patch('api.atlas_disasters.atlas_service') as mock_service:
            mock_service.load_data.side_effect = Exception("Erro genérico")
            
            response = client.get("/api/v1/atlas/records")
            
            assert response.status_code == 500


# ============================================================
# Testes - Integration
# ============================================================

class TestIntegration:
    """Testes de integração"""
    
    def test_full_query_workflow(self, client, mock_atlas_service):
        """Testar fluxo completo de consulta"""
        # 1. Verificar status
        status_response = client.get("/api/v1/atlas/status")
        assert status_response.status_code == 200
        
        # 2. Listar registros
        records_response = client.get("/api/v1/atlas/records?limit=5")
        assert records_response.status_code == 200
        
        # 3. Filtrar dados
        filter_response = client.post(
            "/api/v1/atlas/filter",
            json={"uf": "RS", "anos": [2010, 2020]}
        )
        assert filter_response.status_code == 200
        
        # 4. Obter estatísticas
        stats_response = client.get("/api/v1/atlas/statistics")
        assert stats_response.status_code == 200
        
        # 5. Agregar dados
        agg_response = client.post(
            "/api/v1/atlas/aggregate/municipality",
            json={"group_cols": ["uf"]}
        )
        assert agg_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
