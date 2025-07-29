#!/usr/bin/env python3
"""
Main training script for the gold price prediction system.
Supports GPU/multi-core CPU training optimization.
"""

import argparse
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
import torch
import warnings
warnings.filterwarnings('ignore')

from src.data.data_collector import GoldDataCollector
from src.data.data_preprocessor import GoldDataPreprocessor
from src.features.technical_indicators import calculate_all_indicators
from src.models.deep_learning_models import LSTMModel, GRUModel, TransformerModel
from src.models.model_ensemble import ModelEnsemble, create_ensemble_models
from src.visualization.charts import GoldPriceVisualizer
from src.utils.gpu_utils import GPUManager, setup_gpu_environment, check_rtx_50_compatibility

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_device():
    """Setup and return the best available device with RTX 50 series optimization."""
    # Check RTX 50 series compatibility
    check_rtx_50_compatibility()

    # Setup optimal GPU environment
    device, gpu_settings = setup_gpu_environment()

    # Initialize GPU manager for detailed info
    gpu_manager = GPUManager()
    gpu_manager.print_gpu_info()

    return device, gpu_settings


def load_and_prepare_data(config):
    """Load and prepare training data."""
    logger.info("Loading and preparing data...")
    
    # Initialize data collector
    collector = GoldDataCollector()
    
    # Collect data
    data = collector.combine_data_sources(
        use_yahoo=True,
        period=config['data']['period']
    )
    
    if data.empty:
        raise ValueError("No data collected")
    
    logger.info(f"Collected {len(data)} data points")
    
    # Add technical indicators
    if config['features']['use_technical_indicators']:
        data = calculate_all_indicators(data)
        logger.info("Technical indicators calculated")
    
    # Initialize preprocessor
    preprocessor = GoldDataPreprocessor(
        scaler_type=config['preprocessing']['scaler_type']
    )
    
    # Clean and prepare data
    cleaned_data = preprocessor.clean_data(data)
    feature_data = preprocessor.create_features(cleaned_data)
    
    # Prepare sequences
    X, y = preprocessor.prepare_sequences(
        feature_data,
        sequence_length=config['model']['sequence_length'],
        target_column='close'
    )
    
    logger.info(f"Prepared {len(X)} sequences with shape {X.shape}")
    
    # Split data
    split_ratio = config['training']['train_split']
    split_idx = int(len(X) * split_ratio)
    
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Scale data
    X_train_scaled, X_test_scaled, y_train_scaled, y_test_scaled = preprocessor.scale_data(
        X_train, X_test, y_train, y_test
    )
    
    logger.info(f"Training set: {len(X_train_scaled)} samples")
    logger.info(f"Test set: {len(X_test_scaled)} samples")
    
    return {
        'X_train': X_train_scaled,
        'X_test': X_test_scaled,
        'y_train': y_train_scaled,
        'y_test': y_test_scaled,
        'preprocessor': preprocessor,
        'feature_data': feature_data
    }


def create_models(config, input_size, device, gpu_settings):
    """Create models for ensemble with GPU optimization."""
    logger.info("Creating models with GPU optimization...")

    models = {}
    gpu_manager = GPUManager()

    # LSTM model
    if 'lstm' in config['models']['types']:
        model = LSTMModel(
            input_size=input_size,
            hidden_size=config['models']['lstm']['hidden_size'],
            num_layers=config['models']['lstm']['num_layers'],
            dropout=config['models']['lstm']['dropout'],
            bidirectional=config['models']['lstm']['bidirectional']
        )
        models['lstm'] = gpu_manager.optimize_model_for_gpu(model)

    # GRU model
    if 'gru' in config['models']['types']:
        model = GRUModel(
            input_size=input_size,
            hidden_size=config['models']['gru']['hidden_size'],
            num_layers=config['models']['gru']['num_layers'],
            dropout=config['models']['gru']['dropout'],
            bidirectional=config['models']['gru']['bidirectional']
        )
        models['gru'] = gpu_manager.optimize_model_for_gpu(model)

    # Transformer model
    if 'transformer' in config['models']['types']:
        model = TransformerModel(
            input_size=input_size,
            d_model=config['models']['transformer']['d_model'],
            nhead=config['models']['transformer']['nhead'],
            num_layers=config['models']['transformer']['num_layers'],
            dropout=config['models']['transformer']['dropout']
        )
        models['transformer'] = gpu_manager.optimize_model_for_gpu(model)

    logger.info(f"Created {len(models)} models with GPU optimization: {list(models.keys())}")
    return models


def train_ensemble(models, data, config, device, gpu_settings):
    """Train the model ensemble with GPU optimization."""
    logger.info("Training ensemble with GPU optimization...")

    # Create ensemble
    ensemble = ModelEnsemble(
        ensemble_method=config['ensemble']['method'],
        device=device
    )

    # Add models to ensemble
    for name, model in models.items():
        ensemble.add_model(name, model, model_type='pytorch')

    # Use GPU-optimized batch size if available
    batch_size = gpu_settings.get('max_batch_size', config['training']['batch_size'])
    logger.info(f"Using optimized batch size: {batch_size}")

    # Train all models in parallel
    training_results = ensemble.train_all_parallel(
        X_train=data['X_train'],
        y_train=data['y_train'],
        X_val=data['X_test'],
        y_val=data['y_test'],
        n_jobs=config['training']['n_jobs'],
        epochs=config['training']['epochs'],
        batch_size=batch_size,
        learning_rate=config['training']['learning_rate'],
        patience=config['training']['early_stopping_patience']
    )

    # Print memory stats after training
    gpu_manager = GPUManager()
    memory_stats = gpu_manager.get_memory_stats()
    if memory_stats:
        logger.info(f"GPU memory usage after training: {memory_stats}")

    logger.info("Training completed")
    return ensemble, training_results


def evaluate_ensemble(ensemble, data, config):
    """Evaluate the trained ensemble."""
    logger.info("Evaluating ensemble...")
    
    # Make predictions
    predictions = ensemble.predict(data['X_test'])
    
    # Inverse transform predictions
    y_pred_original = data['preprocessor'].inverse_transform_target(predictions)
    y_test_original = data['preprocessor'].inverse_transform_target(data['y_test'])
    
    # Calculate metrics
    metrics = ensemble.evaluate(data['X_test'], data['y_test'])
    
    logger.info(f"Evaluation metrics: {metrics}")
    
    return {
        'metrics': metrics,
        'predictions': y_pred_original,
        'actual': y_test_original
    }


def save_results(ensemble, training_results, evaluation_results, config, output_dir):
    """Save training results and models."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save ensemble
    ensemble.save_ensemble(output_path / 'ensemble')
    
    # Save training results
    with open(output_path / 'training_results.json', 'w') as f:
        # Convert numpy types to native Python types for JSON serialization
        serializable_results = {}
        for model_name, results in training_results.items():
            serializable_results[model_name] = {
                k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                for k, v in results.items()
                if k != 'history'  # Skip complex history object
            }
        json.dump(serializable_results, f, indent=2)
    
    # Save evaluation results
    eval_results_serializable = {
        'metrics': {k: float(v) for k, v in evaluation_results['metrics'].items()},
        'predictions_sample': evaluation_results['predictions'][:10].tolist(),
        'actual_sample': evaluation_results['actual'][:10].tolist()
    }
    
    with open(output_path / 'evaluation_results.json', 'w') as f:
        json.dump(eval_results_serializable, f, indent=2)
    
    # Save configuration
    with open(output_path / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")


def create_visualizations(data, evaluation_results, output_dir):
    """Create and save visualizations."""
    logger.info("Creating visualizations...")
    
    viz = GoldPriceVisualizer()
    
    # Create price history chart
    price_fig = viz.plot_price_history(data['feature_data'])
    price_fig.write_html(Path(output_dir) / 'price_history.html')
    
    # Create technical indicators chart
    tech_fig = viz.plot_technical_indicators(data['feature_data'])
    tech_fig.write_html(Path(output_dir) / 'technical_indicators.html')
    
    logger.info(f"Visualizations saved to {output_dir}")


def load_config(config_path):
    """Load configuration from file."""
    default_config = {
        'data': {
            'period': '2y'
        },
        'features': {
            'use_technical_indicators': True
        },
        'preprocessing': {
            'scaler_type': 'standard'
        },
        'model': {
            'sequence_length': 60
        },
        'models': {
            'types': ['lstm', 'gru', 'transformer'],
            'lstm': {
                'hidden_size': 128,
                'num_layers': 2,
                'dropout': 0.2,
                'bidirectional': False
            },
            'gru': {
                'hidden_size': 128,
                'num_layers': 2,
                'dropout': 0.2,
                'bidirectional': False
            },
            'transformer': {
                'd_model': 128,
                'nhead': 8,
                'num_layers': 4,
                'dropout': 0.1
            }
        },
        'ensemble': {
            'method': 'weighted_average'
        },
        'training': {
            'train_split': 0.8,
            'epochs': 100,
            'batch_size': 32,
            'learning_rate': 0.001,
            'early_stopping_patience': 20,
            'n_jobs': -1
        }
    }
    
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            user_config = json.load(f)
        
        # Deep merge configurations
        def deep_merge(default, user):
            for key, value in user.items():
                if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                    deep_merge(default[key], value)
                else:
                    default[key] = value
        
        deep_merge(default_config, user_config)
    
    return default_config


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description='Train gold price prediction models')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--output', type=str, default='./models', help='Output directory')
    parser.add_argument('--device', type=str, choices=['auto', 'cpu', 'cuda'], 
                       default='auto', help='Device to use for training')
    parser.add_argument('--visualize', action='store_true', help='Create visualizations')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup device with GPU optimization
    if args.device == 'auto':
        device, gpu_settings = setup_device()
    else:
        device = args.device
        gpu_settings = {}

    logger.info(f"Starting training with device: {device}")
    if gpu_settings:
        logger.info(f"GPU optimization settings: {gpu_settings}")
    
    try:
        # Load and prepare data
        data = load_and_prepare_data(config)
        
        # Create models with GPU optimization
        input_size = data['X_train'].shape[-1]
        models = create_models(config, input_size, device, gpu_settings)

        # Train ensemble with GPU optimization
        ensemble, training_results = train_ensemble(models, data, config, device, gpu_settings)
        
        # Evaluate ensemble
        evaluation_results = evaluate_ensemble(ensemble, data, config)
        
        # Save results
        save_results(ensemble, training_results, evaluation_results, config, args.output)
        
        # Create visualizations if requested
        if args.visualize:
            create_visualizations(data, evaluation_results, args.output)
        
        logger.info("Training pipeline completed successfully!")
        
        # Print summary
        print("\n" + "="*50)
        print("TRAINING SUMMARY")
        print("="*50)
        print(f"Models trained: {list(models.keys())}")
        print(f"Training samples: {len(data['X_train'])}")
        print(f"Test samples: {len(data['X_test'])}")
        print(f"Best model performance: {evaluation_results['metrics']}")
        print(f"Results saved to: {args.output}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
