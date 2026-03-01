"""
Atlas Disaster Visualization Service
Serviço para geração de visualizações e análises visuais dos dados do Atlas
"""

import logging
import os
import io
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Tentar importar bibliotecas de visualização
try:
    import matplotlib
    matplotlib.use('Agg')  # Backend não-interativo para servidores
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.colors import LinearSegmentedColormap
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib não disponível. Visualizações desabilitadas.")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.utils import PlotlyJSONEncoder
    import json
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly não disponível. Gráficos interativos desabilitados.")


class AtlasVisualizationService:
    """
    Serviço para geração de visualizações dos dados do Atlas de Desastres
    """

    # Paleta de cores para tipos de desastres
    DISASTER_COLORS = {
        'inundacao': '#1f77b4',
        'seca': '#ff7f0e',
        'deslizamento': '#2ca02c',
        'granizo': '#d62728',
        'vendaval': '#9467bd',
        'incendio': '#8c564b',
        'geada': '#e377c2',
        'aluviao': '#7f7f7f',
    }

    SEVERITY_COLORS = {
        'baixa': '#2ecc71',
        'media': '#f1c40f',
        'alta': '#e67e22',
        'muito_alta': '#e74c3c',
    }

    def __init__(self, output_dir: Optional[str] = None):
        """
        Inicializar serviço de visualização
        
        Args:
            output_dir: Diretório para salvar gráficos gerados
        """
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'data',
                'atlas',
                'visualizations'
            )
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AtlasVisualizationService initialized with output_dir: {self.output_dir}")

    def create_time_series_chart(
        self,
        df: pd.DataFrame,
        title: str = "Evolução Temporal de Desastres",
        y_column: str = "qtd_ocorrencias",
        group_by: Optional[str] = None,
        chart_type: str = "line",
        save_path: Optional[str] = None,
        return_base64: bool = False,
    ) -> Optional[str]:
        """
        Criar gráfico de série temporal
        
        Args:
            df: DataFrame com dados (deve ter coluna 'ano')
            title: Título do gráfico
            y_column: Coluna para eixo Y
            group_by: Agrupar por coluna (ex: 'uf', 'tipo_desastre')
            chart_type: Tipo de gráfico ('line', 'bar', 'area')
            save_path: Caminho para salvar (opcional)
            return_base64: Retornar imagem em base64
            
        Returns:
            Caminho do arquivo salvo ou string base64
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib não disponível")
            return None
        
        if 'ano' not in df.columns:
            raise ValueError("DataFrame deve conter coluna 'ano'")
        
        # Configurar figura
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if group_by and group_by in df.columns:
            # Agrupar por categoria
            grouped = df.groupby(['ano', group_by])[y_column].sum().unstack(fill_value=0)
            
            if chart_type == 'bar':
                grouped.plot(kind='bar', ax=ax, colormap='tab10')
            elif chart_type == 'area':
                grouped.plot(kind='area', ax=ax, colormap='tab10', alpha=0.7)
            else:  # line
                grouped.plot(kind='line', ax=ax, marker='o', colormap='tab10')
        else:
            # Série temporal simples
            yearly_data = df.groupby('ano')[y_column].sum()
            
            if chart_type == 'bar':
                yearly_data.plot(kind='bar', ax=ax, color='#2c3e50')
            else:  # line
                yearly_data.plot(kind='line', ax=ax, marker='o', linewidth=2, color='#2c3e50')
        
        ax.set_xlabel('Ano', fontsize=12)
        ax.set_ylabel(y_column.replace('_', ' ').title(), fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Rotacionar labels do eixo X
        if chart_type == 'bar':
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Salvar ou retornar base64
        if save_path:
            filepath = self.output_dir / save_path
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Gráfico salvo: {filepath}")
            return str(filepath)
        elif return_base64:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            return f"data:image/png;base64,{img_base64}"
        else:
            plt.close(fig)
            return None

    def create_map_chart(
        self,
        df: pd.DataFrame,
        color_column: str = "qtd_ocorrencias",
        title: str = "Distribuição Geográfica de Desastres",
        save_path: Optional[str] = None,
        return_base64: bool = False,
    ) -> Optional[str]:
        """
        Criar mapa de calor por UF
        
        Args:
            df: DataFrame com dados (deve ter coluna 'uf')
            color_column: Coluna para cor
            title: Título do gráfico
            save_path: Caminho para salvar
            return_base64: Retornar imagem em base64
            
        Returns:
            Caminho do arquivo ou string base64
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        if 'uf' not in df.columns:
            raise ValueError("DataFrame deve conter coluna 'uf'")
        
        # Agrupar por UF
        uf_data = df.groupby('uf')[color_column].sum().sort_values(ascending=False)
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Criar barras horizontais
        colors = plt.cm.OrRd(uf_data.values / uf_data.values.max())
        bars = ax.barh(uf_data.index, uf_data.values, color=colors)
        
        ax.set_xlabel(color_column.replace('_', ' ').title(), fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.invert_yaxis()  # UF com mais ocorrências no topo
        
        # Adicionar valores nas barras
        for i, (uf, value) in enumerate(uf_data.items()):
            ax.text(value, i, f' {value:,.0f}', va='center', fontsize=9)
        
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        if save_path:
            filepath = self.output_dir / save_path
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return str(filepath)
        elif return_base64:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            return f"data:image/png;base64,{img_base64}"
        else:
            plt.close(fig)
            return None

    def create_disaster_type_pie_chart(
        self,
        df: pd.DataFrame,
        title: str = "Distribuição por Tipo de Desastre",
        save_path: Optional[str] = None,
        return_base64: bool = False,
    ) -> Optional[str]:
        """
        Criar gráfico de pizza por tipo de desastre
        
        Args:
            df: DataFrame com dados (deve ter coluna 'tipo_desastre')
            title: Título do gráfico
            save_path: Caminho para salvar
            return_base64: Retornar base64
            
        Returns:
            Caminho ou string base64
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        if 'tipo_desastre' not in df.columns:
            raise ValueError("DataFrame deve conter coluna 'tipo_desastre'")
        
        # Contar por tipo
        type_counts = df['tipo_desastre'].value_counts()
        
        # Cores personalizadas
        colors = [
            self.DISASTER_COLORS.get(tipo.lower(), '#95a5a6')
            for tipo in type_counts.index
        ]
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(10, 10))
        
        wedges, texts, autotexts = ax.pie(
            type_counts.values,
            labels=type_counts.index,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 10},
        )
        
        # Melhorar formatação dos textos
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        if save_path:
            filepath = self.output_dir / save_path
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return str(filepath)
        elif return_base64:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            return f"data:image/png;base64,{img_base64}"
        else:
            plt.close(fig)
            return None

    def create_impact_analysis_chart(
        self,
        df: pd.DataFrame,
        metrics: List[str] = None,
        title: str = "Análise de Impacto de Desastres",
        save_path: Optional[str] = None,
        return_base64: bool = False,
    ) -> Optional[str]:
        """
        Criar gráfico de análise de impacto múltiplo
        
        Args:
            df: DataFrame com dados
            metrics: Lista de métricas para plotar
            title: Título do gráfico
            save_path: Caminho para salvar
            return_base64: Retornar base64
            
        Returns:
            Caminho ou string base64
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        if metrics is None:
            metrics = ['mortes_diretas', 'afetados', 'desabrigados', 'prejuizo_estimado']
        
        # Filtrar métricas existentes
        available_metrics = [m for m in metrics if m in df.columns]
        
        if not available_metrics:
            raise ValueError("Nenhuma métrica de impacto encontrada")
        
        # Agrupar por ano
        yearly_impact = df.groupby('ano')[available_metrics].sum()
        
        # Normalizar para visualização (0-100)
        normalized = (yearly_impact - yearly_impact.min()) / (yearly_impact.max() - yearly_impact.min()) * 100
        
        # Criar figura com múltiplos eixos
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        for idx, metric in enumerate(available_metrics[:4]):
            ax = axes[idx]
            
            # Plotar linha
            ax.plot(
                yearly_impact.index,
                normalized[metric],
                linewidth=2,
                color=self.SEVERITY_COLORS.get('alta', '#e74c3c'),
                marker='o',
                markersize=4
            )
            
            # Preencher área
            ax.fill_between(
                yearly_impact.index,
                normalized[metric],
                alpha=0.3,
                color=self.SEVERITY_COLORS.get('alta', '#e74c3c')
            )
            
            # Format title
            metric_title = metric.replace('_', ' ').title()
            ax.set_title(f"{metric_title} (Normalizado)", fontsize=12, fontweight='bold')
            ax.set_xlabel('Ano')
            ax.set_ylabel('Índice (0-100)')
            ax.grid(True, alpha=0.3)
        
        # Remover subplots vazios
        for idx in range(len(available_metrics), 4):
            fig.delaxes(axes[idx])
        
        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            filepath = self.output_dir / save_path
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return str(filepath)
        elif return_base64:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            return f"data:image/png;base64,{img_base64}"
        else:
            plt.close(fig)
            return None

    def create_interactive_map(
        self,
        df: pd.DataFrame,
        color_column: str = "qtd_ocorrencias",
        title: str = "Mapa Interativo de Desastres",
        save_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Criar mapa interativo com Plotly
        
        Args:
            df: DataFrame com dados (deve ter 'uf' e coordenadas ou centroide)
            color_column: Coluna para cor
            title: Título do gráfico
            save_path: Caminho para salvar HTML
            
        Returns:
            Caminho do arquivo HTML ou None
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        if 'uf' not in df.columns:
            raise ValueError("DataFrame deve conter coluna 'uf'")
        
        # Agrupar por UF
        uf_data = df.groupby('uf').agg({
            color_column: 'sum',
        }).reset_index()
        
        # Criar mapa coroplético do Brasil (simplificado)
        fig = px.choropleth(
            uf_data,
            locations='uf',
            color=color_column,
            color_continuous_scale='Reds',
            title=title,
            labels={color_column: 'Ocorrências'},
            locationmode='country-names',  # Nota: requer geojson do Brasil
        )
        
        fig.update_layout(
            font=dict(size=12),
            title_font_size=16,
        )
        
        if save_path:
            filepath = self.output_dir / save_path
            fig.write_html(str(filepath))
            logger.info(f"Mapa interativo salvo: {filepath}")
            return str(filepath)
        
        return None

    def create_summary_dashboard(
        self,
        df: pd.DataFrame,
        save_path: str = "dashboard_resumo.html",
    ) -> Optional[str]:
        """
        Criar dashboard resumo com múltiplas visualizações
        
        Args:
            df: DataFrame com dados
            save_path: Nome do arquivo HTML
            
        Returns:
            Caminho do arquivo HTML
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        from plotly.subplots import make_subplots
        
        # Criar figura com subplots
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "pie"}, {"type": "bar"}]],
            subplot_titles=[
                'Evolução Temporal',
                'Top 10 Municípios',
                'Distribuição por Tipo',
                'Impacto por Ano'
            ]
        )
        
        # 1. Evolução temporal
        yearly_data = df.groupby('ano').size().reset_index(name='count')
        fig.add_trace(
            go.Scatter(x=yearly_data['ano'], y=yearly_data['count'], mode='lines+markers', name='Ocorrências'),
            row=1, col=1
        )
        
        # 2. Top 10 municípios
        if 'municipio' in df.columns and 'uf' in df.columns:
            df['municipio_uf'] = df['municipio'] + ' - ' + df['uf']
            mun_data = df.groupby('municipio_uf').size().nlargest(10).reset_index(name='count')
            fig.add_trace(
                go.Bar(x=mun_data['count'], y=mun_data['municipio_uf'], orientation='h', name='Municípios'),
                row=1, col=2
            )
        
        # 3. Distribuição por tipo
        if 'tipo_desastre' in df.columns:
            type_data = df['tipo_desastre'].value_counts()
            fig.add_trace(
                go.Pie(labels=type_data.index, values=type_data.values, name='Tipos'),
                row=2, col=1
            )
        
        # 4. Impacto por ano (mortes)
        if 'mortes_diretas' in df.columns and 'ano' in df.columns:
            impact_data = df.groupby('ano')['mortes_diretas'].sum().reset_index()
            fig.add_trace(
                go.Bar(x=impact_data['ano'], y=impact_data['mortes_diretas'], name='Mortes'),
                row=2, col=2
            )
        
        fig.update_layout(
            height=800,
            showlegend=False,
            title_text="Dashboard Atlas de Desastres",
            title_font_size=20,
        )
        
        filepath = self.output_dir / save_path
        fig.write_html(str(filepath))
        logger.info(f"Dashboard salvo: {filepath}")
        
        return str(filepath)

    def generate_all_visualizations(
        self,
        df: pd.DataFrame,
        prefix: str = "atlas"
    ) -> Dict[str, str]:
        """
        Gerar todas as visualizações disponíveis
        
        Args:
            df: DataFrame com dados
            prefix: Prefixo para nomes de arquivo
            
        Returns:
            Dicionário com caminhos dos arquivos gerados
        """
        results = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Série temporal
        try:
            path = self.create_time_series_chart(
                df,
                title="Evolução Temporal de Desastres no Brasil",
                save_path=f"{prefix}_timeseries_{timestamp}.png"
            )
            if path:
                results['timeseries'] = path
        except Exception as e:
            logger.error(f"Erro ao criar série temporal: {e}")
        
        # Mapa por UF
        try:
            path = self.create_map_chart(
                df,
                title="Distribuição de Desastres por UF",
                save_path=f"{prefix}_map_{timestamp}.png"
            )
            if path:
                results['map'] = path
        except Exception as e:
            logger.error(f"Erro ao criar mapa: {e}")
        
        # Pizza por tipo
        try:
            path = self.create_disaster_type_pie_chart(
                df,
                title="Distribuição por Tipo de Desastre",
                save_path=f"{prefix}_pie_{timestamp}.png"
            )
            if path:
                results['pie_chart'] = path
        except Exception as e:
            logger.error(f"Erro ao criar gráfico de pizza: {e}")
        
        # Análise de impacto
        try:
            path = self.create_impact_analysis_chart(
                df,
                title="Análise de Impacto de Desastres",
                save_path=f"{prefix}_impact_{timestamp}.png"
            )
            if path:
                results['impact_analysis'] = path
        except Exception as e:
            logger.error(f"Erro ao criar análise de impacto: {e}")
        
        # Dashboard interativo
        try:
            path = self.create_summary_dashboard(
                df,
                save_path=f"{prefix}_dashboard_{timestamp}.html"
            )
            if path:
                results['dashboard'] = path
        except Exception as e:
            logger.error(f"Erro ao criar dashboard: {e}")
        
        logger.info(f"Visualizações geradas: {list(results.keys())}")
        return results
