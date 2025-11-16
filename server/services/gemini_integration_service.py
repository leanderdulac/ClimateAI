"""
Integração com Google Gemini para análises complementares e assistência técnica
Utiliza a API do Gemini para tarefas de linguagem natural e análise de texto
que complementam o sistema especializado de IA climática do ClimateAI
"""
import google.generativeai as genai
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class GeminiAnalysisResult:
    """Resultado da análise do Gemini"""
    analysis_text: str
    confidence_level: float  # Estimativa de confiabilidade da resposta Gemini
    processing_timestamp: datetime
    analysis_type: str  # Tipo de análise realizada
    sources_considered: List[str]
    complementary_to: str  # Qual componente do ClimateAI esta análise complementa

class GeminiIntegrationService:
    """
    Serviço para integração com Google Gemini
    Fornece recursos de linguagem natural para complementar o sistema especializado
    """
    
    def __init__(self):
        # Configuração da API do Gemini
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada. Configure no arquivo .env")
        
        try:
            genai.configure(api_key=self.api_key)
            # Usa modelo adequado para análise técnica
            self.model = genai.GenerativeModel('gemini-pro')  # ou gemini-1.5-pro para mais capacidades
            self.initialized = True
            logger.info("Serviço Gemini integrado com sucesso")
        except Exception as e:
            logger.error(f"Falha ao inicializar Gemini: {str(e)}")
            self.initialized = False
            raise

    async def analyze_climate_report(self, 
                                   report_text: str,
                                   focus_area: str = "climate_risk") -> GeminiAnalysisResult:
        """
        Analisar relatórios técnicos climáticos com o Gemini
        
        Args:
            report_text: Texto do relatório técnico a analisar
            focus_area: Área de foco da análise (climate_risk, policy_language, mitigation_strategies)
            
        Returns:
            GeminiAnalysisResult com a análise
        """
        if not self.initialized:
            raise Exception("Serviço Gemini não inicializado")
        
        try:
            prompt = f"""
            Você é um especialista sênior em análise climática atuarial e risco climático.
            Analise o seguinte relatório técnico e forneça:
            
            1. Resumo executivo (máximo 150 palavras)
            2. Principais riscos identificados
            3. Implicações atuariais
            4. Recomendações de mitigação
            5. Classificação de severidade (baixa, média, alta, crítica)
            
            Foco específico: {focus_area}
            
            Relatório técnico:
            {report_text[:20000]}  # Limitar tamanho para contexto Gemini
            
            Formato da resposta: JSON estruturado com os campos acima.
            """
            
            response = self.model.generate_content(prompt)
            
            return GeminiAnalysisResult(
                analysis_text=response.text,
                confidence_level=0.85,  # Alta confiabilidade para análise textual
                processing_timestamp=datetime.now(),
                analysis_type="climate_report_analysis",
                sources_considered=["technical_report_text"],
                complementary_to="climate_risk_assessment"
            )
        except Exception as e:
            logger.error(f"Erro na análise do relatório: {str(e)}")
            # Retornar análise mock para manter a integridade do sistema
            return GeminiAnalysisResult(
                analysis_text=f"Análise não disponível devido a erro: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to="climate_risk_assessment"
            )

    async def explain_actuarial_decision(self, 
                                       decision_factors: Dict[str, Any],
                                       decision_type: str = "premium_calculation") -> GeminiAnalysisResult:
        """
        Explicar decisões atuariais em linguagem natural
        
        Args:
            decision_factors: Fatores que influenciaram a decisão
            decision_type: Tipo da decisão (premium_calculation, claim_assessment, risk_analysis)
            
        Returns:
            GeminiAnalysisResult com explicação em linguagem natural
        """
        if not self.initialized:
            raise Exception("Serviço Gemini não inicializado")
        
        try:
            # Converter fatores para texto legível
            factors_text = "\n".join([f"{key}: {value}" for key, value in decision_factors.items()])
            
            prompt = f"""
            Você é um atuário especialista em seguros climáticos.
            Explique em linguagem clara e profissional para stakeholders não-técnicos:
            
            DECISÃO ATUARIAL: {decision_type}
            FATORES CONSIDERADOS:
            {factors_text}
            
            Por favor, forneça:
            1. Explicação simplificada da decisão
            2. Por que esses fatores são importantes
            3. Como isso afeta a precificação/sinistro/risco
            4. Implicações comerciais
            
            Mantenha o tom profissional mas acessível.
            """
            
            response = self.model.generate_content(prompt)
            
            return GeminiAnalysisResult(
                analysis_text=response.text,
                confidence_level=0.90,  # Alta confiabilidade para explicações
                processing_timestamp=datetime.now(),
                analysis_type="actuarial_decision_explanation",
                sources_considered=["decision_factors"],
                complementary_to=decision_type
            )
        except Exception as e:
            logger.error(f"Erro na explicação atuarial: {str(e)}")
            return GeminiAnalysisResult(
                analysis_text=f"Explicação não disponível devido a erro: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to=decision_type
            )

    async def generate_mitigation_suggestions(self,
                                           risk_profile: Dict[str, Any],
                                           asset_type: str = "property") -> GeminiAnalysisResult:
        """
        Gerar sugestões de mitigação baseadas no perfil de risco
        
        Args:
            risk_profile: Perfil de risco do ativo/contrato
            asset_type: Tipo de ativo (property, infrastructure, agriculture, etc.)
            
        Returns:
            GeminiAnalysisResult com sugestões de mitigação
        """
        if not self.initialized:
            raise Exception("Serviço Gemini não inicializado")
        
        try:
            risk_text = "\n".join([f"{key}: {value}" for key, value in risk_profile.items()])
            
            prompt = f"""
            Você é um especialista em engenharia de risco climático e mitigação.
            Com base no seguinte perfil de risco, gere sugestões específicas de mitigação
            para um ativo do tipo: {asset_type}
            
            PERFIL DE RISCO:
            {risk_text}
            
            Por favor, forneça:
            1. Medidas de mitigação prioritárias (top 5)
            2. Custos estimados para cada medida
            3. Redução esperada de risco para cada medida
            4. Viabilidade técnica e prazo de implementação
            5. Recomendações de sequenciamento
            6. Indicadores de monitoramento
            
            Formato: Lista numerada com subtópicos para cada medida.
            """
            
            response = self.model.generate_content(prompt)
            
            return GeminiAnalysisResult(
                analysis_text=response.text,
                confidence_level=0.80,  # Boa confiabilidade para sugestões
                processing_timestamp=datetime.now(),
                analysis_type="mitigation_suggestions",
                sources_considered=["risk_profile"],
                complementary_to="mitigation_planning"
            )
        except Exception as e:
            logger.error(f"Erro na geração de mitigação: {str(e)}")
            return GeminiAnalysisResult(
                analysis_text=f"Sugestões não disponíveis devido a erro: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to="mitigation_planning"
            )

    async def analyze_policy_language(self, 
                                    policy_text: str,
                                    focus_on: str = "climate_exclusions") -> GeminiAnalysisResult:
        """
        Analisar linguagem de apólices para cláusulas climáticas
        
        Args:
            policy_text: Texto da apólice a analisar
            focus_on: Foco da análise (climate_exclusions, coverage_limits, definitions)
            
        Returns:
            GeminiAnalysisResult com análise da linguagem
        """
        if not self.initialized:
            raise Exception("Serviço Gemini não inicializado")
        
        try:
            prompt = f"""
            Você é um especialista em redação de apólices de seguro climático.
            Analise o seguinte texto de apólice com foco em: {focus_on}
            
            TEXTO DA APÓLICE:
            {policy_text[:15000]}  # Limitar para contexto Gemini
            
            Por favor, forneça:
            1. Análise das cláusulas relevantes
            2. Possíveis ambiguidades ou lacunas
            3. Recomendações de melhoria
            4. Alinhamento com práticas de mercado
            5. Questões regulatórias relevantes
            
            Formato: Análise estruturada com recomendações específicas.
            """
            
            response = self.model.generate_content(prompt)
            
            return GeminiAnalysisResult(
                analysis_text=response.text,
                confidence_level=0.88,  # Alta confiabilidade para análise jurídica
                processing_timestamp=datetime.now(),
                analysis_type="policy_language_analysis",
                sources_considered=["policy_text"],
                complementary_to="policy_underwriting"
            )
        except Exception as e:
            logger.error(f"Erro na análise de linguagem de apólice: {str(e)}")
            return GeminiAnalysisResult(
                analysis_text=f"Análise não disponível devido a erro: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to="policy_underwriting"
            )

    async def summarize_climate_data(self,
                                   climate_variables: Dict[str, List[float]],
                                   analysis_period: str = "12_months") -> GeminiAnalysisResult:
        """
        Resumir dados climáticos complexos em interpretação humana
        
        Args:
            climate_variables: Dados climáticos (temperatura, precipitação, etc.)
            analysis_period: Período de análise (12_months, 24_months, 36_months)
            
        Returns:
            GeminiAnalysisResult com interpretação dos dados
        """
        if not self.initialized:
            raise Exception("Serviço Gemini não inicializado")
        
        try:
            # Converter dados para formato textual
            climate_summary = []
            for var_name, values in climate_variables.items():
                climate_summary.append(f"{var_name}: média={sum(values)/len(values) if values else 0:.2f}, "
                                     f"máximo={max(values) if values else 0:.2f}, "
                                     f"mínimo={min(values) if values else 0:.2f}, "
                                     f"tendência={'ascendente' if len(values) > 1 and values[-1] > values[0] else 'descendente'}")
            
            climate_text = "\n".join(climate_summary)
            
            prompt = f"""
            Você é um climatologista atuarial especialista em interpretação de dados.
            Interprete os seguintes dados climáticos para fins atuariais:
            
            DADOS CLIMÁTICOS ({analysis_period}):
            {climate_text}
            
            Por favor, forneça:
            1. Interpretação das tendências climáticas
            2. Implicações para risco de seguros
            3. Potenciais impactos em diferentes tipos de cobertura
            4. Recomendações de monitoramento
            5. Alertas de risco baseados nos dados
            
            Formato: Análise técnica com implicações comerciais.
            """
            
            response = self.model.generate_content(prompt)
            
            return GeminiAnalysisResult(
                analysis_text=response.text,
                confidence_level=0.82,  # Boa confiabilidade para interpretação
                processing_timestamp=datetime.now(),
                analysis_type="climate_data_interpretation",
                sources_considered=["climate_variables"],
                complementary_to="climate_analysis"
            )
        except Exception as e:
            logger.error(f"Erro na interpretação de dados climáticos: {str(e)}")
            return GeminiAnalysisResult(
                analysis_text=f"Interpretação não disponível devido a erro: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to="climate_analysis"
            )

# Instância global do serviço
gemini_integration_service = GeminiIntegrationService()

# Funções de conveniência para API
async def analyze_climate_report(report_text: str, focus_area: str = "climate_risk"):
    """Função de conveniência para análise de relatórios"""
    return await gemini_integration_service.analyze_climate_report(report_text, focus_area)

async def explain_actuarial_decision(decision_factors: Dict[str, Any], decision_type: str = "premium_calculation"):
    """Função de conveniência para explicação de decisões atuariais"""
    return await gemini_integration_service.explain_actuarial_decision(decision_factors, decision_type)

async def generate_mitigation_suggestions(risk_profile: Dict[str, Any], asset_type: str = "property"):
    """Função de conveniência para geração de sugestões de mitigação"""
    return await gemini_integration_service.generate_mitigation_suggestions(risk_profile, asset_type)

async def analyze_policy_language(policy_text: str, focus_on: str = "climate_exclusions"):
    """Função de conveniência para análise de linguagem de apólices"""
    return await gemini_integration_service.analyze_policy_language(policy_text, focus_on)

async def summarize_climate_data(climate_variables: Dict[str, List[float]], analysis_period: str = "12_months"):
    """Função de conveniência para resumo de dados climáticos"""
    return await gemini_integration_service.summarize_climate_data(climate_variables, analysis_period)