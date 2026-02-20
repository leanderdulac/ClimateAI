"""
Integração com Google Gemini para análises complementares e assistência técnica
Utiliza a API do Gemini para tarefas de linguagem natural e análise de texto
que complementam o sistema especializado de IA climática do ClimateAI
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai

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
        from config.config import settings
        self.api_key = settings.GEMINI_API_KEY or ""

        if not self.api_key:
            logger.warning(
                "GEMINI_API_KEY não configurada. Funcionalidades do Gemini estarão desativadas."
            )
            self.initialized = False
            return

        try:
            genai.configure(api_key=self.api_key)
            # Usa modelo adequado para análise técnica
            self.model = genai.GenerativeModel(
                "gemini-flash-latest"
            )  # ou gemini-1.5-pro para mais capacidades
            self.initialized = True
            logger.info("Serviço Gemini integrado com sucesso")
        except Exception as e:
            logger.error(f"Falha ao inicializar Gemini: {str(e)}")
            self.initialized = False
            # Não levantar erro para permitir que o app inicie, mas logar
            logger.warning(
                "Continuando sem suporte Gemini devido a erro de inicialização"
            )

    async def chat_with_assistant(
        self,
        message: str,
        context: Dict[str, Any] = None,
        history: List[Dict[str, str]] = None,
    ) -> GeminiAnalysisResult:
        """
        Chat com o assistente climático
        """
        if not self.initialized:
            return GeminiAnalysisResult(
                analysis_text="O assistente não está disponível no momento (API Key inválida ou erro de conexão).",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to="chat",
            )

        # Tratamento extremamente defensivo de valores nulos
        try:
            # Garantir que context e history sejam objetos válidos em vez de None
            context = context if context is not None else {}
            history = history if history is not None else {}

            # Agora garantir que são dos tipos corretos
            if not isinstance(context, dict):
                context = {}
            if not isinstance(history, list):
                history = []
        except:
            # Se houver qualquer problema com os parâmetros, usar valores padrão
            context = {}
            history = []

        try:
            # Import service dinamicamente com tratamento de erro
            try:
                from .climate_premium_service import calculate_climate_inclusive_premium
            except ImportError:
                # Se não conseguir importar, continuar sem a funcionalidade de cálculo
                calculate_climate_inclusive_premium = None

            system_prompt = """Você é o Climate Assistant, um especialista em seguros climáticos e análise de risco agrícola do ClimateAI.

            DIRETRIZES CRÍTICAS:
            1. MEMÓRIA: Você TEM acesso ao histórico da conversa. NÃO pergunte coisas que o usuário JÁ respondeu.
            2. MICROCLIMAS: Você DEVE usar seu conhecimento sobre o MICROCLIMA específico da cidade selecionada (relevo, altitude, bioma local, proximidade de rios/mar) para refinar sua análise. NÃO dê respostas genéricas estaduais se a cidade for conhecida.
            3. PRÊMIOS: O valor de prêmio abaixo é uma BASE. Você DEVE ajustá-lo (para cima ou para baixo) explicando o porquê com base no microclima local (ex: "Devido ao microclima de vale em X, o risco de geada é maior, elevando o prêmio...").
            4. VERBOSIDADE: Seja conciso e direto. Evite introduções longas e repetitivas.
            5. CÁLCULOS: Apresente a estimativa de prêmio ajustada pelo seu conhecimento de microclima.
            6. CONTEXTO GEOGRÁFICO: Se a cidade for pequena, mencione cidades vizinhas maiores ou a região geográfica (ex: "Serra Gaúcha", "Vale do Jequitinhonha") para situar a análise.
            """

            context_str = ""
            estimated_premium_info = ""

            # Initialize variables that will be used later
            city = "Desconhecida"
            state = ""
            lat = None
            lon = None
            microclimate_type = "normal"
            microclimate_data = None

            # Verificar se context é válido antes de acessar
            if isinstance(context, dict) and context:
                # Handle nested location data
                location = context.get("location") or {}

                if isinstance(location, dict) and location:
                    city = location.get("city", "Desconhecida")
                    state = location.get("state", "")
                    lat = location.get("latitude")
                    lon = location.get("longitude")
                    context_str += f"\n📍 Localização do Cliente: {city}, {state}"
                    if lat and lon:
                        context_str += f" (Lat: {lat}, Lon: {lon})"
            elif (
                isinstance(context, dict) and context and "city" in context
            ):  # Fallback for flat structure
                city = context.get("city", "Desconhecida")
                state = context.get("state", "")
                lat = context.get("latitude")
                lon = context.get("longitude")
                context_str += f"\n📍 Localização do Cliente: {city}, {state}"
                if lat and lon:
                    context_str += f" (Lat: {lat}, Lon: {lon})"

                # Handle nested weather data
                weather = context.get("weather") or {}
                if isinstance(weather, dict) and weather:
                    temp = weather.get("temp", "N/A")
                    precip = weather.get("precip", "N/A")
                    humidity = weather.get("humidity", "N/A")
                    context_str += f"\n☁️ Dados Climáticos Atuais (Base): Temp {temp}°C, Precipitação {precip}mm, Umidade {humidity}%"

                    # Handle microclimate data if available
                    microclimate_data = context.get("microclimate") or {}
                    if isinstance(microclimate_data, dict) and microclimate_data:
                        microclimate_type = microclimate_data.get("type", "normal")
                        characteristics = microclimate_data.get("characteristics", [])
                        historical_data = microclimate_data.get("historicalData", {})

                        context_str += f"\n🌡️ MICROCLIMA DETECTADO: {microclimate_type}"

                        # Tratamento seguro de characteristics
                        if characteristics and isinstance(
                            characteristics, (list, tuple)
                        ):
                            context_str += f"\n   Características: {', '.join(str(c) for c in characteristics) if characteristics else 'Dados não disponíveis'}"
                        else:
                            context_str += (
                                f"\n   Características: Dados não disponíveis"
                            )

                        if isinstance(historical_data, dict) and historical_data:
                            context_str += f"\n   Dados Históricos: {historical_data.get('dryDays', 0)} dias secos, {historical_data.get('heavyRainDays', 0)} dias de chuva forte"
                            context_str += f", {historical_data.get('hotDays', 0)} dias quentes (>30°C), {historical_data.get('windyDays', 0)} dias ventosos"

                    # Calculate estimated premium based on context - enhanced with microclimate data
                    if (
                        calculate_climate_inclusive_premium
                    ):  # Só executa se a função estiver disponível
                        try:
                            # Simple heuristic for expected loss based on weather and microclimate data
                            base_loss = 1000.0
                            if isinstance(temp, (int, float)) and temp > 30:
                                base_loss *= 1.2
                            if isinstance(precip, (int, float)) and precip < 50:
                                base_loss *= 1.3

                            # Adjust for microclimate factors
                            if microclimate_type == "arid":
                                base_loss *= 1.4  # Higher risk for arid climates
                            elif microclimate_type == "humid":
                                base_loss *= (
                                    1.3  # Higher risk for humid climates (floods)
                                )
                            elif microclimate_type == "windy":
                                base_loss *= 1.2  # Higher risk for windy areas
                            elif microclimate_type == "montanha":
                                base_loss *= (
                                    1.25  # Higher risk for mountain areas (frost risk)
                                )

                            premium_result = calculate_climate_inclusive_premium(
                                expected_loss=base_loss, time_horizon_years=1.0
                            )

                            # Tratamento seguro de characteristics novamente
                            characteristics_str = "Dados não disponíveis"
                            if characteristics and isinstance(
                                characteristics, (list, tuple)
                            ):
                                characteristics_str = ", ".join(
                                    str(c) for c in characteristics
                                )

                            estimated_premium_info = f"""
                            💰 DADOS DE PRÊMIO BASE (Ajustado pelo Microclima):
                            - Prêmio Base Calculado: R$ {premium_result.premium:.2f}
                            - Perda Esperada Base: R$ {premium_result.expected_loss:.2f}
                            - Fator de Inflação Climática: {premium_result.climatic_inflation_factor:.4f}

                            ANÁLISE DO MICROCLIMA: {microclimate_type}
                            - Razão do ajuste: O microclima de {city}/{state} ({microclimate_type}) influencia o risco climático.
                            - Características: {characteristics_str}

                            INSTRUÇÃO DE CÁLCULO:
                            Use o valor acima como PONTO DE PARTIDA.
                            Ajuste-o baseado no microclima específico de {city}/{state} considerando os dados históricos.
                            Apresente o "Prêmio Final Ajustado pelo Microclima".
                            """
                        except Exception as e:
                            logger.warning(
                                f"Could not calculate estimated premium: {e}"
                            )

                elif (
                    isinstance(context, dict) and "climate_data" in context
                ):  # Fallback
                    context_str += f"\n☁️ Dados Climáticos: {context['climate_data']}"

            # Inject State Climate Data for cross-referencing
            state_risk_profiles = {
                "RS": {
                    "risk": "Alto",
                    "factors": ["Estiagem", "Granizo"],
                    "trend": "Aumento de variabilidade",
                },
                "SC": {
                    "risk": "Médio-Alto",
                    "factors": ["Enchentes", "Granizo"],
                    "trend": "Eventos extremos mais frequentes",
                },
                "PR": {
                    "risk": "Médio",
                    "factors": ["Geada", "Estiagem"],
                    "trend": "Estável",
                },
                "SP": {
                    "risk": "Médio",
                    "factors": ["Chuvas excessivas", "Seca ocasional"],
                    "trend": "Aumento de temperatura",
                },
                "MT": {
                    "risk": "Alto",
                    "factors": ["Atraso de chuvas", "Altas temperaturas"],
                    "trend": "Janela de plantio mais curta",
                },
                "MS": {
                    "risk": "Médio-Alto",
                    "factors": ["Estiagem", "Calor excessivo"],
                    "trend": "Aumento de evapotranspiração",
                },
                "GO": {
                    "risk": "Médio",
                    "factors": ["Veranico", "Altas temperaturas"],
                    "trend": "Aumento de temperatura",
                },
                "BA": {
                    "risk": "Alto",
                    "factors": ["Seca severa", "Irregularidade pluvial"],
                    "trend": "Desertificação em áreas",
                },
                "MG": {
                    "risk": "Médio",
                    "factors": ["Seca no norte", "Chuvas no sul"],
                    "trend": "Variabilidade espacial",
                },
                "MA": {
                    "risk": "Alto",
                    "factors": ["Variabilidade de chuvas"],
                    "trend": "Mudança no regime de chuvas",
                },
                "PI": {
                    "risk": "Alto",
                    "factors": ["Seca", "Altas temperaturas"],
                    "trend": "Aumento de aridez",
                },
                "TO": {
                    "risk": "Médio-Alto",
                    "factors": ["Veranico"],
                    "trend": "Aumento de temperatura",
                },
            }

            state_data = state_risk_profiles.get(
                state,
                {
                    "risk": "Genérico",
                    "factors": ["Variabilidade climática"],
                    "trend": "Incerteza",
                },
            )

            # Manipulação segura de fatores
            factors = state_data.get("factors", [])
            if factors and isinstance(factors, (list, tuple)):
                factors_str = ", ".join(str(f) for f in factors)
            else:
                factors_str = "Dados não disponíveis"

            context_str += f"""

            📊 DADOS CLIMÁTICOS ESTADUAIS ({state}):
            - Nível de Risco Regional: {state_data.get('risk', 'Desconhecido')}
            - Fatores Críticos: {factors_str}
            - Tendência Climática: {state_data.get('trend', 'Incerta')}

            INSTRUÇÃO DE CRUZAMENTO DE DADOS:
            Cruze os dados do MICROCLIMA local ({microclimate_type}) com estes dados ESTADUAIS.
            Exemplo: Se o estado tem risco de seca, mas a cidade tem microclima úmido, o risco local pode ser menor.
            Use essa lógica para ajustar o prêmio final.
            """

            # Format history com tratamento extremamente seguro
            history_str = ""
            if history and isinstance(history, list) and len(history) > 0:
                history_str = "\nHISTÓRICO DA CONVERSA (últimas 8 mensagens):\n"
                try:
                    # Pegar as últimas 8 mensagens de forma segura
                    recent_history = history[-8:] if len(history) > 8 else history
                    for msg in recent_history:
                        if isinstance(msg, dict):
                            role = (
                                "Usuário" if msg.get("role") == "user" else "Assistant"
                            )
                            content = msg.get("content", "")
                            history_str += f"{role}: {content}\n"
                except:
                    # Se qualquer erro ocorrer ao processar o histórico, continuar sem ele
                    history_str = ""

            # Create final prompt with improved structure to reduce verbosity
            full_prompt = f"""
            {system_prompt}

            {context_str}

            {estimated_premium_info}

            {history_str}

            INSTRUÇÃO FINAL:
            Responda de forma DIRETA e CONCISA, evitando repetir informações já fornecidas na conversa.
            Use os dados de microclima para fornecer uma análise mais precisa.
            Não faça introduções longas se o usuário já tiver uma localização definida.

            Usuário: {message}
            """

            response = self.model.generate_content(full_prompt)

            return GeminiAnalysisResult(
                analysis_text=response.text,
                confidence_level=0.9,
                processing_timestamp=datetime.now(),
                analysis_type="chat_response",
                sources_considered=[
                    "user_message",
                    "context",
                    "pricing_engine",
                    "history",
                    "microclimate_data",
                ],
                complementary_to="user_assistance",
            )
        except Exception as e:
            logger.error(f"Erro no chat: {str(e)}")
            return GeminiAnalysisResult(
                analysis_text=f"Desculpe, tive um problema ao processar sua mensagem: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to="chat",
            )

    async def analyze_climate_report(
        self, report_text: str, focus_area: str = "climate_risk"
    ) -> GeminiAnalysisResult:
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
                complementary_to="climate_risk_assessment",
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
                complementary_to="climate_risk_assessment",
            )

    async def explain_actuarial_decision(
        self,
        decision_factors: Dict[str, Any],
        decision_type: str = "premium_calculation",
    ) -> GeminiAnalysisResult:
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
            factors_text = "\n".join(
                [f"{key}: {value}" for key, value in decision_factors.items()]
            )

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
                complementary_to=decision_type,
            )
        except Exception as e:
            logger.error(f"Erro na explicação atuarial: {str(e)}")
            return GeminiAnalysisResult(
                analysis_text=f"Explicação não disponível devido a erro: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to=decision_type,
            )

    async def generate_mitigation_suggestions(
        self, risk_profile: Dict[str, Any], asset_type: str = "property"
    ) -> GeminiAnalysisResult:
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
            risk_text = "\n".join(
                [f"{key}: {value}" for key, value in risk_profile.items()]
            )

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
                complementary_to="mitigation_planning",
            )
        except Exception as e:
            logger.error(f"Erro na geração de mitigação: {str(e)}")
            return GeminiAnalysisResult(
                analysis_text=f"Sugestões não disponíveis devido a erro: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to="mitigation_planning",
            )

    async def analyze_policy_language(
        self, policy_text: str, focus_on: str = "climate_exclusions"
    ) -> GeminiAnalysisResult:
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
                complementary_to="policy_underwriting",
            )
        except Exception as e:
            logger.error(f"Erro na análise de linguagem de apólice: {str(e)}")
            return GeminiAnalysisResult(
                analysis_text=f"Análise não disponível devido a erro: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to="policy_underwriting",
            )

    async def summarize_climate_data(
        self,
        climate_variables: Dict[str, List[float]],
        analysis_period: str = "12_months",
    ) -> GeminiAnalysisResult:
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
                if isinstance(values, list) and len(values) > 0:
                    climate_summary.append(
                        f"{var_name}: média={sum(values)/len(values) if values else 0:.2f}, "
                        f"máximo={max(values) if values else 0:.2f}, "
                        f"mínimo={min(values) if values else 0:.2f}, "
                        f"tendência={'ascendente' if len(values) > 1 and values[-1] > values[0] else 'descendente'}"
                    )
                else:
                    climate_summary.append(f"{var_name}: sem dados")

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
                complementary_to="climate_analysis",
            )
        except Exception as e:
            logger.error(f"Erro na interpretação de dados climáticos: {str(e)}")
            return GeminiAnalysisResult(
                analysis_text=f"Interpretação não disponível devido a erro: {str(e)}",
                confidence_level=0.0,
                processing_timestamp=datetime.now(),
                analysis_type="error",
                sources_considered=[],
                complementary_to="climate_analysis",
            )


# Instância global do serviço
gemini_integration_service = GeminiIntegrationService()


# Funções de conveniência para API
async def analyze_climate_report(report_text: str, focus_area: str = "climate_risk"):
    """Função de conveniência para análise de relatórios"""
    return await gemini_integration_service.analyze_climate_report(
        report_text, focus_area
    )


async def explain_actuarial_decision(
    decision_factors: Dict[str, Any], decision_type: str = "premium_calculation"
):
    """Função de conveniência para explicação de decisões atuariais"""
    return await gemini_integration_service.explain_actuarial_decision(
        decision_factors, decision_type
    )


async def generate_mitigation_suggestions(
    risk_profile: Dict[str, Any], asset_type: str = "property"
):
    """Função de conveniência para geração de sugestões de mitigação"""
    return await gemini_integration_service.generate_mitigation_suggestions(
        risk_profile, asset_type
    )


async def analyze_policy_language(
    policy_text: str, focus_on: str = "climate_exclusions"
):
    """Função de conveniência para análise de linguagem de apólices"""
    return await gemini_integration_service.analyze_policy_language(
        policy_text, focus_on
    )


async def summarize_climate_data(
    climate_variables: Dict[str, List[float]], analysis_period: str = "12_months"
):
    """Função de conveniência para resumo de dados climáticos"""
    return await gemini_integration_service.summarize_climate_data(
        climate_variables, analysis_period
    )


async def chat_with_assistant(
    message: str, context: Dict[str, Any] = None, history: List[Dict[str, str]] = None
):
    """Função de conveniência para chat"""
    return await gemini_integration_service.chat_with_assistant(
        message, context, history
    )
