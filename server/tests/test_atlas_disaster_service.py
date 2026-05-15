"""
Testes unitários para o módulo Atlas Digital de Desastres
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Adicionar server ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.atlas_disaster_service import AtlasDisasterService
from models.schemas import AtlasFilterRequest


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_data_dir():
    """Criar diretório temporário para dados de teste"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_dataframe():
    """Criar DataFrame de exemplo para testes"""
    np.random.seed(42)
    
    data = {
        'ano': np.random.choice(range(2000, 2024), 100),
        'uf': np.random.choice(['RS', 'SC', 'PR', 'SP', 'RJ', 'MG', 'BA'], 100),
        'municipio': [f"Municipio_{i}" for i in range(100)],
        'tipo_desastre': np.random.choice(
            ['Inundação', 'Seca', 'Deslizamento', 'Granizo', 'Vendaval'],
            100
        ),
        'intensidade': np.random.choice(['Baixa', 'Média', 'Alta', 'Muito Alta'], 100),
        'mortes_diretas': np.random.randint(0, 10, 100),
        'afetados': np.random.randint(0, 1000, 100),
        'desabrigados': np.random.randint(0, 100, 100),
        'prejuizo_estimado': np.random.uniform(1000, 100000, 100),
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def atlas_service(temp_data_dir):
    """Criar instância do serviço com diretório temporário"""
    return AtlasDisasterService(data_dir=temp_data_dir)


# ============================================================
# Testes - Download e Carregamento de Dados
# ============================================================

class TestDownloadAndLoad:
    """Testes para download e carregamento de dados"""
    
    def test_download_invalid_url(self, atlas_service):
        """Testar download com URL padrão (que deve ser tratada como não configurada)"""
        with pytest.raises(ValueError, match="URL de dados não configurada"):
            atlas_service.download_data(atlas_service.DEFAULT_DATA_URL)
    
    def test_download_nonexistent_url(self, atlas_service):
        """Testar download com URL que não existe"""
        with patch('services.atlas_disaster_service.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            with pytest.raises(Exception):
                atlas_service.download_data("https://example.com/nonexistent_file.csv")
    
    def test_load_nonexistent_file(self, atlas_service):
        """Testar carregamento de arquivo inexistente"""
        with pytest.raises(FileNotFoundError):
            atlas_service.load_data(filepath="/nonexistent/path/file.csv")
    
    def test_load_csv_file(self, atlas_service, sample_dataframe, temp_data_dir):
        """Testar carregamento de arquivo CSV"""
        # Salvar DataFrame como CSV (usando separador padrão)
        csv_path = os.path.join(temp_data_dir, "test_data.csv")
        sample_dataframe.to_csv(csv_path, index=False, sep=';')
        
        # Carregar dados
        df = atlas_service.load_data(filepath=csv_path)
        
        assert len(df) == 100
        assert 'ano' in df.columns
        assert 'uf' in df.columns
    
    def test_load_excel_file(self, atlas_service, sample_dataframe, temp_data_dir):
        """Testar carregamento de arquivo Excel (pulando se openpyxl não instalado)"""
        try:
            # Salvar DataFrame como Excel
            xlsx_path = os.path.join(temp_data_dir, "test_data.xlsx")
            sample_dataframe.to_excel(xlsx_path, index=False)
            
            # Carregar dados
            df = atlas_service.load_data(filepath=xlsx_path)
            
            assert len(df) == 100
            assert 'ano' in df.columns
        except ImportError:
            pytest.skip("openpyxl não instalado")
    
    def test_cache_functionality(self, atlas_service, sample_dataframe, temp_data_dir):
        """Testar funcionalidade de cache"""
        # Salvar e carregar dados
        csv_path = os.path.join(temp_data_dir, "test_data.csv")
        sample_dataframe.to_csv(csv_path, index=False)
        
        # Primeira carga (sem cache)
        df1 = atlas_service.load_data(filepath=csv_path, use_cache=True)
        cache_timestamp = atlas_service._cache_timestamp
        
        # Segunda carga (com cache)
        df2 = atlas_service.load_data(filepath=csv_path, use_cache=True)
        
        assert atlas_service._cache is not None
        assert cache_timestamp == atlas_service._cache_timestamp
        pd.testing.assert_frame_equal(df1, df2)
    
    def test_clear_cache(self, atlas_service, sample_dataframe, temp_data_dir):
        """Testar limpeza de cache"""
        # Salvar e carregar dados
        csv_path = os.path.join(temp_data_dir, "test_data.csv")
        sample_dataframe.to_csv(csv_path, index=False)
        atlas_service.load_data(filepath=csv_path)
        
        # Limpar cache
        atlas_service.clear_cache()
        
        assert atlas_service._cache is None
        assert atlas_service._cache_timestamp is None


# ============================================================
# Testes - Filtragem de Dados
# ============================================================

class TestFiltering:
    """Testes para filtragem de dados"""
    
    def test_filter_by_year(self, atlas_service, sample_dataframe):
        """Testar filtro por ano"""
        df_filtered = atlas_service.filter_disasters(
            df=sample_dataframe,
            anos=(2010, 2015)
        )
        
        assert all((df_filtered['ano'] >= 2010) & (df_filtered['ano'] <= 2015))
        assert len(df_filtered) <= len(sample_dataframe)
    
    def test_filter_by_uf(self, atlas_service, sample_dataframe):
        """Testar filtro por UF"""
        df_filtered = atlas_service.filter_disasters(
            df=sample_dataframe,
            uf="RS"
        )
        
        assert all(df_filtered['uf'] == 'RS')
    
    def test_filter_by_municipio(self, atlas_service, sample_dataframe):
        """Testar filtro por município (busca parcial)"""
        df_filtered = atlas_service.filter_disasters(
            df=sample_dataframe,
            municipio="Municipio_1"
        )
        
        # Deve encontrar Municipios com "1" no nome
        assert len(df_filtered) > 0
        # Verificar se todos contêm "1" no nome (case insensitive)
        assert all(df_filtered['municipio'].str.contains('1', case=False))
    
    def test_filter_by_disaster_type(self, atlas_service, sample_dataframe):
        """Testar filtro por tipo de desastre"""
        df_filtered = atlas_service.filter_disasters(
            df=sample_dataframe,
            tipo_desastre="inundacao"
        )
        
        # Deve encontrar "Inundação" (case insensitive)
        assert len(df_filtered) > 0
        assert all(df_filtered['tipo_desastre'].str.upper().str.contains('INundação'.upper()))
    
    def test_filter_by_min_affected(self, atlas_service, sample_dataframe):
        """Testar filtro por mínimo de afetados"""
        min_affected = 500
        df_filtered = atlas_service.filter_disasters(
            df=sample_dataframe,
            min_afetados=min_affected
        )
        
        assert all(df_filtered['afetados'] >= min_affected)
    
    def test_filter_by_min_deaths(self, atlas_service, sample_dataframe):
        """Testar filtro por mínimo de mortes"""
        min_deaths = 5
        df_filtered = atlas_service.filter_disasters(
            df=sample_dataframe,
            min_mortes=min_deaths
        )
        
        assert all(df_filtered['mortes_diretas'] >= min_deaths)
    
    def test_combined_filters(self, atlas_service, sample_dataframe):
        """Testar combinação de filtros"""
        df_filtered = atlas_service.filter_disasters(
            df=sample_dataframe,
            anos=(2005, 2015),
            uf="RS",
            tipo_desastre="seca",
            min_afetados=100
        )
        
        assert all((df_filtered['ano'] >= 2005) & (df_filtered['ano'] <= 2015))
        assert all(df_filtered['uf'] == 'RS')
        assert all(df_filtered['afetados'] >= 100)


# ============================================================
# Testes - Agregação de Dados
# ============================================================

class TestAggregation:
    """Testes para agregação de dados"""
    
    def test_aggregate_by_municipality(self, atlas_service, sample_dataframe):
        """Testar agregação por município"""
        df_agg = atlas_service.aggregate_by_municipality(
            df=sample_dataframe,
            group_cols=['uf', 'municipio']
        )
        
        assert 'qtd_ocorrencias' in df_agg.columns
        assert 'mortes_diretas' in df_agg.columns
        assert 'afetados' in df_agg.columns
        assert len(df_agg) <= len(sample_dataframe)
    
    def test_aggregate_by_year(self, atlas_service, sample_dataframe):
        """Testar agregação por ano"""
        df_agg = atlas_service.aggregate_by_year(df=sample_dataframe)
        
        assert 'ano' in df_agg.columns
        assert 'qtd_ocorrencias' in df_agg.columns
        assert df_agg['ano'].is_monotonic_increasing
    
    def test_aggregate_by_year_with_uf(self, atlas_service, sample_dataframe):
        """Testar agregação por ano e UF"""
        df_agg = atlas_service.aggregate_by_year(
            df=sample_dataframe,
            group_by_uf=True
        )
        
        assert 'ano' in df_agg.columns
        assert 'uf' in df_agg.columns
    
    def test_aggregation_sorting(self, atlas_service, sample_dataframe):
        """Testar ordenação na agregação"""
        df_agg = atlas_service.aggregate_by_municipality(df=sample_dataframe)
        
        # Verificar se está ordenado por qtd_ocorrencias (decrescente)
        qtd_values = df_agg['qtd_ocorrencias'].values
        assert all(qtd_values[i] >= qtd_values[i+1] for i in range(len(qtd_values)-1))


# ============================================================
# Testes - Estatísticas
# ============================================================

class TestStatistics:
    """Testes para cálculo de estatísticas"""
    
    def test_get_statistics_structure(self, atlas_service, sample_dataframe):
        """Testar estrutura das estatísticas"""
        stats = atlas_service.get_statistics(df=sample_dataframe)
        
        assert 'total_registros' in stats
        assert 'periodo' in stats
        assert 'uf' in stats
        assert 'tipos_desastre' in stats
        assert 'impacto' in stats
    
    def test_get_statistics_total_records(self, atlas_service, sample_dataframe):
        """Testar total de registros nas estatísticas"""
        stats = atlas_service.get_statistics(df=sample_dataframe)
        
        assert stats['total_registros'] == 100
    
    def test_get_statistics_period(self, atlas_service, sample_dataframe):
        """Testar período nas estatísticas"""
        stats = atlas_service.get_statistics(df=sample_dataframe)
        
        assert 'inicio' in stats['periodo']
        assert 'fim' in stats['periodo']
        assert stats['periodo']['inicio'] >= 2000
        assert stats['periodo']['fim'] <= 2023
    
    def test_get_statistics_impact(self, atlas_service, sample_dataframe):
        """Testar impacto nas estatísticas"""
        stats = atlas_service.get_statistics(df=sample_dataframe)
        
        assert 'mortes_diretas' in stats['impacto']
        assert 'total' in stats['impacto']['mortes_diretas']
        assert 'media' in stats['impacto']['mortes_diretas']
        assert 'max' in stats['impacto']['mortes_diretas']


# ============================================================
# Testes - Exportação
# ============================================================

class TestExport:
    """Testes para exportação de dados"""
    
    def test_export_to_csv(self, atlas_service, sample_dataframe, temp_data_dir):
        """Testar exportação para CSV"""
        filepath = atlas_service.export_to_csv(
            df=sample_dataframe,
            filename="test_export.csv",
            include_timestamp=False
        )
        
        assert os.path.exists(filepath)
        assert filepath.endswith("test_export.csv")
        
        # Verificar conteúdo
        df_loaded = pd.read_csv(filepath)
        pd.testing.assert_frame_equal(df_loaded, sample_dataframe)
    
    def test_export_with_timestamp(self, atlas_service, sample_dataframe):
        """Testar exportação com timestamp no nome"""
        filepath = atlas_service.export_to_csv(
            df=sample_dataframe,
            filename="test_export.csv",
            include_timestamp=True
        )
        
        # Verificar se contém timestamp
        assert "_20" in filepath  # Ano no formato YYYYMMDD_HHMMSS
        assert filepath.endswith(".csv")


# ============================================================
# Testes - Schema Validation
# ============================================================

class TestSchemaValidation:
    """Testes para validação de schemas"""
    
    def test_filter_request_valid(self):
        """Testar requisição de filtro válida"""
        filters = AtlasFilterRequest(
            anos=(2000, 2020),
            uf="RS",
            tipo_desastre="inundacao",
            min_afetados=100
        )
        
        assert filters.anos == (2000, 2020)
        assert filters.uf == "RS"
        assert filters.tipo_desastre == "inundacao"
        assert filters.min_afetados == 100
    
    def test_filter_request_optional(self):
        """Testar requisição com todos os campos opcionais"""
        filters = AtlasFilterRequest()
        
        assert filters.anos is None
        assert filters.uf is None
        assert filters.municipio is None
        assert filters.tipo_desastre is None
        assert filters.min_afetados is None
        assert filters.min_mortes is None


# ============================================================
# Testes - Edge Cases
# ============================================================

class TestEdgeCases:
    """Testes para casos extremos"""
    
    def test_empty_dataframe(self, atlas_service):
        """Testar operações com DataFrame vazio"""
        df_empty = pd.DataFrame()
        
        # Filtragem deve retornar DataFrame vazio
        df_filtered = atlas_service.filter_disasters(df=df_empty, uf="RS")
        assert len(df_filtered) == 0
    
    def test_single_record(self, atlas_service):
        """Testar operações com único registro"""
        df_single = pd.DataFrame({
            'ano': [2020],
            'uf': ['RS'],
            'municipio': ['Porto Alegre'],
            'tipo_desastre': ['Inundação'],
            'afetados': [100],
        })
        
        stats = atlas_service.get_statistics(df=df_single)
        assert stats['total_registros'] == 1
    
    def test_missing_columns(self, atlas_service):
        """Testar operações com colunas faltantes"""
        df_incomplete = pd.DataFrame({
            'ano': [2020, 2021],
            'uf': ['RS', 'SC'],
        })
        
        # Filtragem por coluna inexistente não deve quebrar
        df_filtered = atlas_service.filter_disasters(
            df=df_incomplete,
            tipo_desastre="inundacao"  # Coluna não existe
        )
        assert len(df_filtered) == 2  # Retorna todos (filtro ignorado)
    
    def test_special_characters_in_municipio(self, atlas_service, sample_dataframe):
        """Testar filtro com caracteres especiais em município"""
        sample_dataframe.loc[0, 'municipio'] = "São José dos Campos"
        
        df_filtered = atlas_service.filter_disasters(
            df=sample_dataframe,
            municipio="São José"
        )
        
        assert len(df_filtered) >= 1


# ============================================================
# Testes - Integration
# ============================================================

class TestIntegration:
    """Testes de integração"""
    
    def test_full_workflow(self, atlas_service, sample_dataframe, temp_data_dir):
        """Testar fluxo completo: salvar, carregar, filtrar, agregar, exportar"""
        # 1. Salvar dados
        csv_path = os.path.join(temp_data_dir, "workflow_test.csv")
        sample_dataframe.to_csv(csv_path, index=False, sep=';')
        
        # 2. Carregar dados
        df = atlas_service.load_data(filepath=csv_path)
        assert len(df) == 100
        
        # 3. Filtrar
        df_filtered = atlas_service.filter_disasters(
            df=df,
            uf="RS",
            anos=(2010, 2020)
        )
        
        # 4. Agregar (usando apenas colunas que existem)
        if len(df_filtered) > 0:
            df_agg = atlas_service.aggregate_by_municipality(
                df=df_filtered,
                group_cols=['municipio']
            )
            
            # 5. Estatísticas
            stats = atlas_service.get_statistics(df=df_filtered)
            
            # 6. Exportar
            export_path = atlas_service.export_to_csv(
                df=df_agg,
                filename="workflow_result.csv",
                include_timestamp=False
            )
            
            assert os.path.exists(export_path)
            assert stats['total_registros'] == len(df_filtered)
        else:
            pytest.skip("Nenhum dado filtrado para RS no período")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
