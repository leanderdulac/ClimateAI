"""
Serviço para previsões climáticas
"""

import random
from datetime import datetime, timedelta
from typing import List

import numpy as np

from models.schemas import ClimaData, PrevisaoClima
from services.clima_service import ClimaService
from services.dynamical_climate_service import (
    dynamical_climate_service,
    predict_climate_dynamics,
)


class PrevisaoService:
    def __init__(self):
        self.clima_service = ClimaService()
        self.dynamical_climate_service = dynamical_climate_service

    def obter_previsao_clima(
        self, latitude: float, longitude: float, dias: int
    ) -> PrevisaoClima:
        """
        Obter previsão climática para uma localização específica
        Incorporates dynamical systems modeling for improved accuracy
        """
        data_inicio = datetime.now()
        data_fim = data_inicio + timedelta(days=dias)

        # Get historical data to initialize dynamical system
        historico_inicio = data_inicio - timedelta(
            days=30
        )  # Use last 30 days for initialization
        historico = self.clima_service.obter_historico(
            latitude=latitude,
            longitude=longitude,
            data_inicio=historico_inicio,
            data_fim=data_inicio,
        )

        # Initialize dynamical system model with historical data
        initial_conditions = self._prepare_initial_conditions(historico, latitude)

        # Generate dynamical systems prediction to enhance forecast
        dynamical_prediction = predict_climate_dynamics(
            initial_conditions=initial_conditions,
            n_steps=dias,
            model_type="lorenz",
            parameters={"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0},
        )

        variaveis = []
        for i in range(dias):
            data_atual = data_inicio + timedelta(days=i)

            # Simular confiança decrescente com o tempo
            confianca = max(0.5, 1.0 - (i * 0.05))

            # Incorporate dynamical systems prediction
            if (
                "trajectory" in dynamical_prediction
                and len(dynamical_prediction["trajectory"]) > i
            ):
                dynamical_data = dynamical_prediction["trajectory"][i]
                # Map dynamical system outputs to climate variables
                temperatura_dynamical = dynamical_data[
                    0
                ]  # First dimension represents temperature
                precipitacao_dynamical = max(
                    0, dynamical_data[1]
                )  # Second dimension represents precipitation
                pressao_dynamical = dynamical_data[
                    2
                ]  # Third dimension represents pressure
            else:
                # Fallback to original simulation if dynamical system fails
                temperatura_dynamical = self.clima_service._gerar_temperatura_simulada(
                    latitude, data_atual
                )
                precipitacao_dynamical = (
                    self.clima_service._gerar_precipitacao_simulada(data_atual)
                )
                pressao_dynamical = random.uniform(980, 1040)

            # Blend dynamical systems prediction with traditional simulation
            temperatura_trad = self.clima_service._gerar_temperatura_simulada(
                latitude, data_atual
            )
            precipitacao_trad = (
                self.clima_service._gerar_precipitacao_simulada(data_atual) * confianca
            )
            temperatura = 0.7 * temperatura_dynamical + 0.3 * temperatura_trad
            precipitacao = (
                0.7 * precipitacao_dynamical + 0.3 * precipitacao_trad * confianca
            )

            umidade = self.clima_service._gerar_umidade_simulada(
                temperatura
            ) + random.uniform(-5, 5)

            dado = ClimaData(
                latitude=latitude,
                longitude=longitude,
                data=data_atual,
                temperatura=temperatura,
                precipitacao=precipitacao,
                umidade=umidade,
                vento_velocidade=random.uniform(0, 20) * confianca,
                vento_direcao=random.uniform(0, 360),
                pressao=pressao_dynamical,
                indice_spi=self.clima_service._calcular_spi(precipitacao, i),
                fonte="previsao_dinamica_hibrida",  # Updated to indicate hybrid approach
            )
            variaveis.append(dado)

        # Calculate enhanced confidence based on dynamical system properties
        lyapunov_exp = dynamical_prediction.get("max_lyapunov_exponent", 0.9)
        chaos_level = dynamical_prediction.get("chaos_level", "medium")

        # Lower confidence for highly chaotic systems
        if chaos_level == "high" and lyapunov_exp > 0.5:
            confianca_final = 0.6
        elif chaos_level == "medium":
            confianca_final = 0.75
        else:
            confianca_final = 0.85  # Higher confidence for less chaotic systems

        return PrevisaoClima(
            latitude=latitude,
            longitude=longitude,
            data_inicio=data_inicio,
            data_fim=data_fim,
            variaveis=variaveis,
            metodo="dynamical_ensemble_hybrid",
            confianca=confianca_final,
        )

    def _prepare_initial_conditions(self, historico, latitude):
        """
        Prepare initial conditions for dynamical system based on historical data
        """
        if not historico:
            # Default initial conditions if no historical data
            return [20.0 + latitude * 0.1, 10.0, 1013.0]  # [temp, precip, pressure]

        # Extract recent climate data for initial conditions
        recent_data = historico[-3:]  # Use last 3 days of data
        if len(recent_data) >= 3:
            # Calculate average temperature, precipitation, and pressure from recent history
            temps = [d.temperatura for d in recent_data if d.temperatura is not None]
            precip = [d.precipitacao for d in recent_data if d.precipitacao is not None]
            press = [d.pressao for d in recent_data if d.pressao is not None]

            avg_temp = np.mean(temps) if temps else 20.0
            avg_precip = np.mean(precip) if precip else 5.0
            avg_press = np.mean(press) if press else 1013.0
        else:
            # Use simulated values based on latitude
            avg_temp = self.clima_service._gerar_temperatura_simulada(
                latitude, datetime.now()
            )
            avg_precip = self.clima_service._gerar_precipitacao_simulada(datetime.now())
            avg_press = random.uniform(980, 1040)

        # Add small perturbations to initial conditions to represent current state
        initial_conditions = [
            avg_temp + random.uniform(-1, 1),
            avg_precip + random.uniform(-2, 2),
            avg_press + random.uniform(-5, 5),
        ]

        return initial_conditions

    def obter_previsao_eventos(
        self, latitude: float, longitude: float, dias: int
    ) -> List[str]:
        """
        Obter previsão de eventos climáticos extremos
        Enhances traditional probability models with dynamical systems chaos analysis
        """
        eventos = []

        # Get dynamical systems prediction to identify extreme events
        historico_inicio = datetime.now() - timedelta(days=30)
        historico = self.clima_service.obter_historico(
            latitude=latitude,
            longitude=longitude,
            data_inicio=historico_inicio,
            data_fim=datetime.now(),
        )

        initial_conditions = self._prepare_initial_conditions(historico, latitude)

        # Generate longer-term prediction to detect extreme events
        dynamical_prediction = predict_climate_dynamics(
            initial_conditions=initial_conditions,
            n_steps=dias,
            model_type="rossler",  # Using Rössler for oscillation detection
            parameters={"a": 0.2, "b": 0.2, "c": 5.7},
        )

        for i in range(dias):
            data = datetime.now() + timedelta(days=i)

            # Get values from dynamical system prediction
            if (
                "trajectory" in dynamical_prediction
                and len(dynamical_prediction["trajectory"]) > i
            ):
                dyn_data = dynamical_prediction["trajectory"][i]
                temp = dyn_data[0]
                precip = max(0, dyn_data[1])
                pressure = dyn_data[2]
            else:
                # Fallback to traditional simulation
                temp = self.clima_service._gerar_temperatura_simulada(latitude, data)
                precip = self.clima_service._gerar_precipitacao_simulada(data)
                pressure = random.uniform(980, 1040)

            # Calculate traditional probabilities
            prob_seca_trad = max(0, min(1, (25 - precip) * 0.02)) if temp > 25 else 0
            prob_enchente_trad = max(0, min(1, precip * 0.01)) if precip > 20 else 0
            prob_onda_calor_trad = max(0, min(1, (temp - 30) * 0.1)) if temp > 30 else 0

            # Enhance probabilities based on dynamical systems properties
            chaos_level = dynamical_prediction.get("chaos_level", "medium")
            lyapunov_exp = dynamical_prediction.get("max_lyapunov_exponent", 0.9)

            # Increase probability of extreme events in highly chaotic regimes
            if chaos_level == "high" and lyapunov_exp > 0.5:
                prob_seca = min(1.0, prob_seca_trad * 1.5)
                prob_enchente = min(1.0, prob_enchente_trad * 1.5)
                prob_onda_calor = min(1.0, prob_onda_calor_trad * 1.5)
            else:
                prob_seca = prob_seca_trad
                prob_enchente = prob_enchente_trad
                prob_onda_calor = prob_onda_calor_trad

            # Detect extreme behavior in dynamical system trajectory
            extreme_temp = abs(temp) > 35  # Extreme temperature in dynamical system
            extreme_precip = precip > 50  # Extreme precipitation event
            pressure_anomaly = (
                abs(pressure - 1013) > 50
            )  # Pressure anomaly indicating storm

            # Adicionar eventos com base nas probabilidades ajustadas
            if (
                random.random() < prob_seca or extreme_precip < 2
            ):  # Very low precipitation
                eventos.append(
                    f"Seca potencial em {data.strftime('%Y-%m-%d')} (confiança aprimorada por dinâmica)"
                )
            if random.random() < prob_enchente or extreme_precip > 40:
                eventos.append(
                    f"Risco de enchente em {data.strftime('%Y-%m-%d')} (confiança aprimorada por dinâmica)"
                )
            if random.random() < prob_onda_calor or extreme_temp:
                eventos.append(
                    f"Onda de calor prevista em {data.strftime('%Y-%m-%d')} (confiança aprimorada por dinâmica)"
                )

            # Add events based on pressure anomalies (storms)
            if pressure_anomaly and random.random() < 0.3:
                eventos.append(
                    f"Condicoes de tempestade previstas em {data.strftime('%Y-%m-%d')} (detectado por dinâmica)"
                )

        return eventos
