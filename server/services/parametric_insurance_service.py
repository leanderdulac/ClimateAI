"""
Parametric Insurance Payout Service
Implements Payout_t = K · I{Índice_t > Trigger} · min(Cap, Loss_t) with optimal trigger calculation
where Índice_t = f(dados_climáticos_t) includes wind, precipitation, and temperature indices
"""
import numpy as np
from scipy.optimize import minimize_scalar
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParametricInsuranceParams:
    """Parameters for parametric insurance contract"""
    trigger: float
    cap: float
    factor: float  # K in the formula
    basis_risk_weight: float  # λ in optimization

class ParametricInsuranceService:
    """
    Service for parametric insurance with optimal trigger calculation
    Implements: Payout_t = K · I{Índice_t > Trigger} · min(Cap, Loss_t)
    where Índice_t = f(dados_climáticos_t) includes wind, precipitation, temperature
    """
    
    def __init__(self):
        self.contracts = {}
        self.optimization_results = {}
    
    def calculate_wind_index(self, wind_speed_3s_gusts: List[float], 
                           threshold: float = 20.0) -> List[float]:
        """
        Calculate maximum sustained wind index (3-second gusts)
        
        Args:
            wind_speed_3s_gusts: List of 3-second wind gust speeds (m/s)
            threshold: Threshold for significant wind events (m/s)
            
        Returns:
            List of wind indices
        """
        # Calculate wind index as deviation above threshold
        wind_indices = []
        for gust in wind_speed_3s_gusts:
            if gust > threshold:
                # Use excess over threshold as index
                wind_indices.append(gust - threshold)
            else:
                wind_indices.append(0.0)
        
        return wind_indices
    
    def calculate_precipitation_index(self, precipitation_24h: List[float],
                                    threshold: float = 50.0) -> List[float]:
        """
        Calculate accumulated precipitation index (24h)
        
        Args:
            precipitation_24h: List of 24-hour accumulated precipitation (mm)
            threshold: Threshold for significant precipitation (mm)
            
        Returns:
            List of precipitation indices
        """
        # Calculate precipitation index as deviation above threshold
        precip_indices = []
        for precip in precipitation_24h:
            if precip > threshold:
                # Use excess above threshold as index, normalized by threshold
                precip_indices.append((precip - threshold) / threshold)
            else:
                precip_indices.append(0.0)
        
        return precip_indices
    
    def calculate_temperature_index(self, temperature_data: List[float],
                                  threshold: float = 35.0) -> List[float]:
        """
        Calculate consecutive high temperature index
        
        Args:
            temperature_data: List of temperature readings (°C)
            threshold: Temperature threshold for significant heat (°C)
            
        Returns:
            List of temperature indices based on consecutive days above threshold
        """
        temp_indices = []
        consecutive_days = 0
        
        for temp in temperature_data:
            if temp > threshold:
                consecutive_days += 1
            else:
                consecutive_days = 0
            
            # Temperature index increases with consecutive days above threshold
            temp_indices.append(consecutive_days * max(0, temp - threshold) / 5.0)
        
        return temp_indices
    
    def calculate_composite_index(self, wind_indices: List[float],
                                precip_indices: List[float],
                                temp_indices: List[float],
                                weights: Tuple[float, float, float] = (0.4, 0.4, 0.2)) -> List[float]:
        """
        Calculate composite climate index combining all three indices
        
        Args:
            wind_indices: Wind indices
            precip_indices: Precipitation indices
            temp_indices: Temperature indices
            weights: Weights for [wind, precipitation, temperature] components
            
        Returns:
            List of composite indices
        """
        if not all(len(lst) == len(wind_indices) for lst in [precip_indices, temp_indices]):
            raise ValueError("All index lists must have the same length")
        
        composite_indices = []
        for i in range(len(wind_indices)):
            composite = (weights[0] * wind_indices[i] + 
                        weights[1] * precip_indices[i] + 
                        weights[2] * temp_indices[i])
            composite_indices.append(composite)
        
        return composite_indices
    
    def calculate_payout(self, index_values: List[float],
                        losses: List[float],
                        trigger: float,
                        cap: float,
                        factor: float) -> List[float]:
        """
        Calculate parametric insurance payouts: Payout_t = K · I{Índice_t > Trigger} · min(Cap, Loss_t)
        
        Args:
            index_values: Climate index values (Índice_t)
            losses: Actual losses (Loss_t)
            trigger: Trigger threshold
            cap: Payout cap
            factor: Payout factor (K)
            
        Returns:
            List of calculated payouts
        """
        if not all(len(lst) == len(index_values) for lst in [losses]):
            raise ValueError("Index and loss lists must have the same length")
        
        payouts = []
        for idx, loss in zip(index_values, losses):
            # Indicator function I{Índice_t > Trigger}
            indicator = 1.0 if idx > trigger else 0.0
            
            # Min of Cap and Loss_t
            min_value = min(cap, loss)
            
            # Calculate payout
            payout = factor * indicator * min_value
            payouts.append(payout)
        
        return payouts
    
    def calculate_basis_risk(self, payouts: List[float], losses: List[float]) -> float:
        """
        Calculate basis risk as the mismatch between payouts and actual losses
        
        Args:
            payouts: Calculated payouts
            losses: Actual losses
            
        Returns:
            Basis risk measure (mean squared error)
        """
        if len(payouts) != len(losses):
            raise ValueError("Payout and loss lists must have same length")
        
        if len(payouts) == 0:
            return 0.0
        
        # Calculate mean squared error between payouts and losses
        mse = np.mean([(p - l)**2 for p, l in zip(payouts, losses)])
        return mse
    
    def optimize_trigger(self, index_values: List[float],
                        losses: List[float],
                        cap: float,
                        factor: float,
                        basis_risk_weight: float,
                        trigger_bounds: Tuple[float, float] = (0.0, None)) -> Dict[str, Any]:
        """
        Optimize trigger level: argmin_T [E[(Payout - Loss)²] + λ·BasisRisk]
        
        Args:
            index_values: Climate index values
            losses: Actual losses
            cap: Payout cap
            factor: Payout factor (K)
            basis_risk_weight: Weight for basis risk component (λ)
            trigger_bounds: Bounds for trigger optimization
            
        Returns:
            Optimal trigger and optimization results
        """
        if trigger_bounds[1] is None:
            # Set upper bound to max index value + 10%
            trigger_bounds = (trigger_bounds[0], max(index_values) * 1.1)
        
        def objective_function(trigger):
            # Calculate payouts for this trigger
            payouts = self.calculate_payout(index_values, losses, trigger, cap, factor)
            
            # Calculate payout-loss squared error
            squared_errors = [(p - l)**2 for p, l in zip(payouts, losses)]
            payout_loss_error = np.mean(squared_errors) if squared_errors else 0.0
            
            # Calculate basis risk
            basis_risk = self.calculate_basis_risk(payouts, losses)
            
            # Total objective: E[(Payout - Loss)²] + λ·BasisRisk
            total_cost = payout_loss_error + basis_risk_weight * basis_risk
            
            return total_cost
        
        # Optimize trigger
        try:
            result = minimize_scalar(objective_function, bounds=trigger_bounds, method='bounded')
            
            # Calculate payouts using optimal trigger
            optimal_payouts = self.calculate_payout(
                index_values, losses, result.x, cap, factor
            )
            
            return {
                'optimal_trigger': result.x,
                'optimal_cost': result.fun,
                'success': result.success,
                'message': result.message,
                'final_payouts': optimal_payouts,
                'basis_risk': self.calculate_basis_risk(optimal_payouts, losses),
                'payout_loss_error': np.mean([(p - l)**2 for p, l in zip(optimal_payouts, losses)])
            }
        except Exception as e:
            logger.error(f"Optimization error: {str(e)}")
            return {
                'optimal_trigger': np.mean(index_values),  # fallback
                'optimal_cost': float('inf'),
                'success': False,
                'message': str(e),
                'final_payouts': [0.0] * len(index_values),
                'basis_risk': 0.0,
                'payout_loss_error': 0.0
            }
    
    def calculate_parametric_insurance_contract(self, 
                                              wind_speed_3s_gusts: List[float],
                                              precipitation_24h: List[float],
                                              temperature_data: List[float],
                                              actual_losses: List[float],
                                              cap: float,
                                              factor: float,
                                              trigger: Optional[float] = None,
                                              basis_risk_weight: float = 0.1,
                                              wind_threshold: float = 20.0,
                                              precip_threshold: float = 50.0,
                                              temp_threshold: float = 35.0,
                                              index_weights: Tuple[float, float, float] = (0.4, 0.4, 0.2),
                                              optimize_trigger_flag: bool = True) -> Dict[str, Any]:
        """
        Complete parametric insurance contract calculation
        
        Args:
            wind_speed_3s_gusts: 3-second wind gust speeds (m/s)
            precipitation_24h: 24-hour accumulated precipitation (mm)
            temperature_data: Temperature readings (°C)
            actual_losses: Actual losses for the period
            cap: Payout cap
            factor: Payout factor (K)
            trigger: Trigger threshold (if None, will be optimized if optimize_trigger_flag=True)
            basis_risk_weight: Weight for basis risk in optimization
            wind_threshold: Wind speed threshold
            precip_threshold: Precipitation threshold
            temp_threshold: Temperature threshold
            index_weights: Weights for [wind, precipitation, temperature]
            optimize_trigger_flag: Whether to optimize the trigger
            
        Returns:
            Complete contract results including payouts and risk metrics
        """
        # Calculate individual indices
        wind_indices = self.calculate_wind_index(wind_speed_3s_gusts, wind_threshold)
        precip_indices = self.calculate_precipitation_index(precipitation_24h, precip_threshold)
        temp_indices = self.calculate_temperature_index(temperature_data, temp_threshold)
        
        # Calculate composite index
        composite_indices = self.calculate_composite_index(
            wind_indices, precip_indices, temp_indices, index_weights
        )
        
        # Determine trigger level
        if optimize_trigger_flag or trigger is None:
            # Optimize trigger
            opt_result = self.optimize_trigger(
                composite_indices, actual_losses, cap, factor, basis_risk_weight
            )
            optimal_trigger = opt_result['optimal_trigger']
            payouts = opt_result['final_payouts']
        else:
            # Use provided trigger
            optimal_trigger = trigger
            payouts = self.calculate_payout(
                composite_indices, actual_losses, trigger, cap, factor
            )
            opt_result = {
                'optimal_cost': 0.0,
                'success': True,
                'message': 'Trigger provided, not optimized',
                'basis_risk': self.calculate_basis_risk(payouts, actual_losses),
                'payout_loss_error': np.mean([(p - l)**2 for p, l in zip(payouts, actual_losses)])
            }
        
        # Calculate additional metrics
        total_payouts = sum(payouts)
        total_losses = sum(actual_losses)
        payout_ratio = total_payouts / total_losses if total_losses > 0 else 0.0
        
        # Count trigger events
        trigger_events = sum(1 for idx in composite_indices if idx > optimal_trigger)
        
        return {
            'contract_params': {
                'cap': cap,
                'factor': factor,
                'trigger': optimal_trigger,
                'basis_risk_weight': basis_risk_weight
            },
            'indices': {
                'wind_indices': wind_indices,
                'precipitation_indices': precip_indices,
                'temperature_indices': temp_indices,
                'composite_indices': composite_indices
            },
            'payouts': payouts,
            'actual_losses': actual_losses,
            'trigger_events_count': trigger_events,
            'total_payouts': total_payouts,
            'total_losses': total_losses,
            'payout_loss_ratio': payout_ratio,
            'basis_risk': opt_result['basis_risk'],
            'payout_loss_error': opt_result['payout_loss_error'],
            'optimization_result': opt_result,
            'metrics': {
                'mean_payout': np.mean(payouts) if payouts else 0.0,
                'std_payout': np.std(payouts) if len(payouts) > 1 else 0.0,
                'max_payout': max(payouts) if payouts else 0.0,
                'mean_loss': np.mean(actual_losses) if actual_losses else 0.0,
                'std_loss': np.std(actual_losses) if len(actual_losses) > 1 else 0.0,
                'max_loss': max(actual_losses) if actual_losses else 0.0
            }
        }

# Global instance
parametric_insurance_service = ParametricInsuranceService()

# Convenience functions for API integration
def calculate_wind_index(wind_speed_3s_gusts: List[float], 
                        threshold: float = 20.0) -> List[float]:
    """Calculate maximum sustained wind index (3-second gusts)"""
    return parametric_insurance_service.calculate_wind_index(wind_speed_3s_gusts, threshold)

def calculate_precipitation_index(precipitation_24h: List[float],
                                threshold: float = 50.0) -> List[float]:
    """Calculate accumulated precipitation index (24h)"""
    return parametric_insurance_service.calculate_precipitation_index(precipitation_24h, threshold)

def calculate_temperature_index(temperature_data: List[float],
                              threshold: float = 35.0) -> List[float]:
    """Calculate consecutive high temperature index"""
    return parametric_insurance_service.calculate_temperature_index(temperature_data, threshold)

def calculate_composite_index(wind_indices: List[float],
                            precip_indices: List[float],
                            temp_indices: List[float],
                            weights: Tuple[float, float, float] = (0.4, 0.4, 0.2)) -> List[float]:
    """Calculate composite climate index combining all three indices"""
    return parametric_insurance_service.calculate_composite_index(
        wind_indices, precip_indices, temp_indices, weights
    )

def calculate_payout(index_values: List[float],
                    losses: List[float],
                    trigger: float,
                    cap: float,
                    factor: float) -> List[float]:
    """Calculate parametric insurance payouts: Payout_t = K · I{Índice_t > Trigger} · min(Cap, Loss_t)"""
    return parametric_insurance_service.calculate_payout(
        index_values, losses, trigger, cap, factor
    )

def calculate_parametric_insurance_contract(
    wind_speed_3s_gusts: List[float],
    precipitation_24h: List[float],
    temperature_data: List[float],
    actual_losses: List[float],
    cap: float,
    factor: float,
    trigger: Optional[float] = None,
    basis_risk_weight: float = 0.1
) -> Dict[str, Any]:
    """Complete parametric insurance contract calculation"""
    return parametric_insurance_service.calculate_parametric_insurance_contract(
        wind_speed_3s_gusts, precipitation_24h, temperature_data,
        actual_losses, cap, factor, trigger, basis_risk_weight
    )