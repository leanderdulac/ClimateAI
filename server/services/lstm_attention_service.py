"""
Advanced LSTM Attention Service for Climate Time Series Prediction
Implements the attention mechanism for climate data: 
h_t = LSTM(x_t, h_{t-1})
α_t = softmax(v^T tanh(W_h h_t + W_c c_t))
ŷ = Σ_t α_t · h_t
Where x_t = [temp_t, precip_t, pressão_t, índice_NAO, fase_ENSO]
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
import math

logger = logging.getLogger(__name__)

class ClimateAttentionLSTM(nn.Module):
    """
    LSTM with Attention mechanism for climate time series prediction
    Implements: h_t = LSTM(x_t, h_{t-1}), α_t = softmax(v^T tanh(W_h h_t + W_c c_t)), ŷ = Σ_t α_t · h_t
    """
    
    def __init__(self, input_size: int = 5, hidden_size: int = 64, num_layers: int = 2, 
                 output_size: int = 1, dropout: float = 0.2):
        super(ClimateAttentionLSTM, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        # LSTM layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Attention mechanism: context vector and weights
        self.W_h = nn.Linear(hidden_size, hidden_size)
        self.W_c = nn.Linear(hidden_size, hidden_size)
        self.v = nn.Linear(hidden_size, 1, bias=False)
        
        # Output layer
        self.output_layer = nn.Linear(hidden_size, output_size)
        
        # Dropout for regularization
        self.dropout = nn.Dropout(dropout)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights for better convergence"""
        for name, param in self.lstm.named_parameters():
            if 'weight' in name:
                nn.init.orthogonal_(param)
            elif 'bias' in name:
                nn.init.constant_(param, 0)
        
        nn.init.xavier_uniform_(self.W_h.weight)
        nn.init.xavier_uniform_(self.W_c.weight)
        nn.init.xavier_uniform_(self.v.weight)
        nn.init.xavier_uniform_(self.output_layer.weight)
    
    def attention(self, lstm_output, final_hidden):
        """
        Compute attention weights
        Args:
            lstm_output: LSTM outputs (batch_size, seq_len, hidden_size)
            final_hidden: Final hidden state (num_layers, batch_size, hidden_size)
        Returns:
            Attention weights and context vector
        """
        # Use last layer's hidden state as context
        # Shape: (batch_size, hidden_size)
        context = final_hidden[-1]  # Get last layer hidden state
        
        # Expand context to match sequence length
        # Shape: (batch_size, seq_len, hidden_size)
        context_expanded = context.unsqueeze(1).expand(-1, lstm_output.size(1), -1)
        
        # Compute attention scores: tanh(W_h * h_t + W_c * c_t)
        # Shape: (batch_size, seq_len, hidden_size)
        tanh_scores = torch.tanh(
            self.W_h(lstm_output) + self.W_c(context_expanded)
        )
        
        # Compute attention weights: v^T * tanh_scores
        # Shape: (batch_size, seq_len, 1)
        attention_scores = self.v(tanh_scores)
        
        # Apply softmax to get attention weights
        # Shape: (batch_size, seq_len, 1)
        attention_weights = F.softmax(attention_scores, dim=1)
        
        # Compute context vector: sum of attention_weights * lstm_output
        # Shape: (batch_size, hidden_size)
        context_vector = torch.sum(attention_weights * lstm_output, dim=1)
        
        return context_vector, attention_weights.squeeze(-1)
    
    def forward(self, x):
        """
        Forward pass of the model
        Args:
            x: Input tensor (batch_size, seq_len, input_size)
        Returns:
            Predictions and attention weights
        """
        batch_size, seq_len, _ = x.shape
        
        # LSTM forward pass
        lstm_output, (hidden, cell) = self.lstm(x)
        
        # Apply attention mechanism
        context_vector, attention_weights = self.attention(lstm_output, hidden)
        
        # Apply dropout to context vector
        context_vector = self.dropout(context_vector)
        
        # Generate final prediction
        output = self.output_layer(context_vector)
        
        return output, attention_weights

class ClimateAttentionService:
    """
    Service for LSTM attention-based climate prediction
    Implements: h_t = LSTM(x_t, h_{t-1}), α_t = softmax(v^T tanh(W_h h_t + W_c c_t)), ŷ = Σ_t α_t · h_t
    Where x_t = [temp_t, precip_t, pressão_t, índice_NAO, fase_ENSO]
    """
    
    def __init__(self):
        self.model = None
        self.optimizer = None
        self.criterion = nn.MSELoss()
        self.is_trained = False
        self.scaler = {'mean': None, 'std': None}  # For input normalization
    
    def prepare_climate_features(self, temperature: List[float], 
                               precipitation: List[float],
                               pressure: List[float],
                               nao_index: List[float],
                               enso_phase: List[float]) -> np.ndarray:
        """
        Prepare climate features in the format x_t = [temp_t, precip_t, pressão_t, índice_NAO, fase_ENSO]
        
        Args:
            temperature: Temperature values
            precipitation: Precipitation values
            pressure: Pressure values
            nao_index: North Atlantic Oscillation index values
            enso_phase: ENSO phase values (e.g., ONI index or categorical encoded as continuous)
            
        Returns:
            Feature matrix ready for model input
        """
        if not all(len(lst) == len(temperature) for lst in [precipitation, pressure, nao_index, enso_phase]):
            raise ValueError("All input series must have the same length")
        
        # Stack features into the required format
        features = np.column_stack([temperature, precipitation, pressure, nao_index, enso_phase])
        return features
    
    def normalize_features(self, features: np.ndarray) -> np.ndarray:
        """
        Normalize features using computed statistics
        """
        if self.scaler['mean'] is None:
            self.scaler['mean'] = np.mean(features, axis=0)
            self.scaler['std'] = np.std(features, axis=0)
            # Avoid division by zero
            self.scaler['std'] = np.where(self.scaler['std'] == 0, 1, self.scaler['std'])
        
        normalized = (features - self.scaler['mean']) / self.scaler['std']
        return normalized
    
    def create_sequences(self, features: np.ndarray, targets: np.ndarray, 
                        sequence_length: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Create sequences for training/prediction
        
        Args:
            features: Normalized feature matrix (n_samples, n_features)
            targets: Target values (n_samples,)
            sequence_length: Length of sequences to create
            
        Returns:
            Tensors for features and targets ready for model
        """
        X, y = [], []
        
        for i in range(len(features) - sequence_length):
            X.append(features[i:(i + sequence_length)])
            y.append(targets[i + sequence_length])
        
        return torch.FloatTensor(X), torch.FloatTensor(y)
    
    def build_model(self, input_size: int = 5, hidden_size: int = 64, 
                   num_layers: int = 2, dropout: float = 0.2) -> None:
        """
        Build the LSTM attention model
        
        Args:
            input_size: Number of input features (should be 5 for climate features)
            hidden_size: LSTM hidden size
            num_layers: Number of LSTM layers
            dropout: Dropout rate
        """
        self.model = ClimateAttentionLSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout
        )
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.is_trained = False
    
    def train_model(self, temperature: List[float],
                   precipitation: List[float], 
                   pressure: List[float],
                   nao_index: List[float],
                   enso_phase: List[float],
                   targets: List[float],
                   sequence_length: int = 10,
                   epochs: int = 100,
                   batch_size: int = 32,
                   validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train the LSTM attention model
        
        Args:
            temperature: Temperature values
            precipitation: Precipitation values
            pressure: Pressure values
            nao_index: North Atlantic Oscillation index values
            enso_phase: ENSO phase values
            targets: Target climate variable to predict
            sequence_length: Length of input sequences
            epochs: Number of training epochs
            batch_size: Training batch size
            validation_split: Fraction of data to use for validation
            
        Returns:
            Training metrics and history
        """
        if len(temperature) != len(targets):
            raise ValueError("Feature series and targets must have same length")
        
        # Prepare and normalize features
        features = self.prepare_climate_features(temperature, precipitation, 
                                               pressure, nao_index, enso_phase)
        normalized_features = self.normalize_features(features)
        
        # Create sequences
        X, y = self.create_sequences(normalized_features, np.array(targets), sequence_length)
        
        # Split into train and validation
        n_val = int(len(X) * validation_split)
        X_val, y_val = X[:n_val], y[:n_val]
        X_train, y_train = X[n_val:], y[n_val:]
        
        # Initialize model if not already built
        if self.model is None:
            self.build_model()
        
        # Training history
        train_losses = []
        val_losses = []
        
        # Training loop
        for epoch in range(epochs):
            self.model.train()
            
            # Shuffle training data
            train_indices = torch.randperm(len(X_train))
            X_train_shuffled = X_train[train_indices]
            y_train_shuffled = y_train[train_indices]
            
            epoch_loss = 0.0
            
            for i in range(0, len(X_train_shuffled), batch_size):
                batch_X = X_train_shuffled[i:i+batch_size]
                batch_y = y_train_shuffled[i:i+batch_size]
                
                # Forward pass
                predictions, _ = self.model(batch_X)
                predictions = predictions.squeeze()
                
                loss = self.criterion(predictions, batch_y)
                
                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                
                # Gradient clipping to prevent exploding gradients
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                self.optimizer.step()
                
                epoch_loss += loss.item()
            
            # Validation
            self.model.eval()
            with torch.no_grad():
                val_predictions, _ = self.model(X_val)
                val_predictions = val_predictions.squeeze()
                val_loss = self.criterion(val_predictions, y_val).item()
            
            avg_train_loss = epoch_loss / max(1, len(X_train_shuffled) // batch_size)
            train_losses.append(avg_train_loss)
            val_losses.append(val_loss)
            
            if epoch % 10 == 0:
                print(f'Epoch {epoch}, Train Loss: {avg_train_loss:.4f}, Val Loss: {val_loss:.4f}')
        
        self.is_trained = True
        
        return {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'final_train_loss': avg_train_loss,
            'final_val_loss': val_loss,
            'epochs': epochs,
            'sequence_length': sequence_length,
            'model_params': {
                'input_size': self.model.input_size,
                'hidden_size': self.model.hidden_size,
                'num_layers': self.model.num_layers
            }
        }
    
    def predict(self, temperature: List[float],
               precipitation: List[float],
               pressure: List[float],
               nao_index: List[float],
               enso_phase: List[float],
               sequence_length: int = 10,
               num_predictions: int = 1) -> Dict[str, Any]:
        """
        Make predictions using the trained model
        
        Args:
            temperature: Temperature values
            precipitation: Precipitation values
            pressure: Pressure values
            nao_index: North Atlantic Oscillation index values
            enso_phase: ENSO phase values
            sequence_length: Length of input sequences
            num_predictions: Number of future time steps to predict
            
        Returns:
            Predictions with attention weights and confidence intervals
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features
        features = self.prepare_climate_features(temperature, precipitation, 
                                               pressure, nao_index, enso_phase)
        normalized_features = self.normalize_features(features)
        
        # For prediction, we'll use the last sequence as input
        if len(features) < sequence_length:
            raise ValueError(f"Need at least {sequence_length} data points for prediction")
        
        # Use the last available sequence
        last_sequence = normalized_features[-sequence_length:]
        input_tensor = torch.FloatTensor(last_sequence).unsqueeze(0)  # Add batch dimension
        
        self.model.eval()
        with torch.no_grad():
            predictions = []
            attention_weights_history = []
            
            # For multi-step prediction, we'd need to implement a feedback mechanism
            # For now, predict one step and optionally repeat with updated context
            pred, attention_weights = self.model(input_tensor)
            predictions.append(pred.item())
            attention_weights_history.append(attention_weights[0].numpy())
        
        return {
            'predictions': predictions,
            'attention_weights': attention_weights_history,
            'sequence_length_used': sequence_length,
            'model_trained': self.is_trained
        }
    
    def predict_with_attention_visualization(self, temperature: List[float],
                                           precipitation: List[float],
                                           pressure: List[float],
                                           nao_index: List[float],
                                           enso_phase: List[float],
                                           targets: List[float],
                                           sequence_length: int = 10) -> Dict[str, Any]:
        """
        Make predictions and return detailed attention information for visualization
        
        Args:
            Same as predict function, plus targets for comparison
            
        Returns:
            Predictions, attention weights, and input features for analysis
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features
        features = self.prepare_climate_features(temperature, precipitation, 
                                               pressure, nao_index, enso_phase)
        normalized_features = self.normalize_features(features)
        
        # Create sequences
        X, y_actual = self.create_sequences(normalized_features, np.array(targets), sequence_length)
        
        self.model.eval()
        predictions = []
        attention_weights_list = []
        
        with torch.no_grad():
            for i in range(len(X)):
                pred, attention_weights = self.model(X[i:i+1])  # Add batch dimension
                predictions.append(pred.item())
                attention_weights_list.append(attention_weights[0].numpy())
        
        return {
            'predictions': predictions,
            'actual_values': y_actual.numpy().tolist(),
            'attention_weights': attention_weights_list,
            'input_sequences': X.numpy().tolist(),
            'sequence_length': sequence_length,
            'total_predictions': len(predictions)
        }

# Global instance
climate_attention_service = ClimateAttentionService()

# Convenience functions for API integration
def prepare_climate_features(temperature: List[float], 
                           precipitation: List[float],
                           pressure: List[float],
                           nao_index: List[float],
                           enso_phase: List[float]) -> np.ndarray:
    """Prepare climate features in the format x_t = [temp_t, precip_t, pressão_t, índice_NAO, fase_ENSO]"""
    return climate_attention_service.prepare_climate_features(
        temperature, precipitation, pressure, nao_index, enso_phase
    )

def train_lstm_attention_model(temperature: List[float],
                              precipitation: List[float], 
                              pressure: List[float],
                              nao_index: List[float],
                              enso_phase: List[float],
                              targets: List[float],
                              sequence_length: int = 10,
                              epochs: int = 100) -> Dict[str, Any]:
    """Train the LSTM attention model for climate prediction"""
    return climate_attention_service.train_model(
        temperature, precipitation, pressure, nao_index, enso_phase,
        targets, sequence_length, epochs
    )

def predict_with_lstm_attention(temperature: List[float],
                              precipitation: List[float],
                              pressure: List[float],
                              nao_index: List[float],
                              enso_phase: List[float],
                              sequence_length: int = 10) -> Dict[str, Any]:
    """Make predictions using the trained LSTM attention model"""
    return climate_attention_service.predict(
        temperature, precipitation, pressure, nao_index, enso_phase, sequence_length
    )

def predict_with_attention_visualization(temperature: List[float],
                                       precipitation: List[float],
                                       pressure: List[float],
                                       nao_index: List[float],
                                       enso_phase: List[float],
                                       targets: List[float],
                                       sequence_length: int = 10) -> Dict[str, Any]:
    """Make predictions and return detailed attention information for visualization"""
    return climate_attention_service.predict_with_attention_visualization(
        temperature, precipitation, pressure, nao_index, enso_phase,
        targets, sequence_length
    )