#!/usr/bin/env python3
"""
Prediction script for the gold price prediction system.
Provides command-line interface for making predictions.
"""

import argparse
import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from src.prediction.predictor import GoldPricePredictor
from src.visualization.charts import GoldPriceVisualizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_predictor(model_path, config_path=None):
    """Load the trained predictor."""
    logger.info(f"Loading predictor from {model_path}")

    predictor = GoldPricePredictor(
        model_path=model_path,
        config_path=config_path
    )

    # 检查模型路径是否存在
    if model_path and Path(model_path).exists():
        try:
            predictor.load_model(model_path)
        except Exception as e:
            logger.warning(f"Failed to load model: {e}")
            logger.info("Will use demo mode without pre-trained model")
    else:
        logger.warning(f"Model path {model_path} does not exist")
        logger.info("Will use demo mode without pre-trained model")

    return predictor


def make_single_prediction(predictor, horizon=1, data_period='1y'):
    """Make a single prediction."""
    logger.info(f"Making {horizon}-day prediction")
    
    # Get latest data
    data = predictor.data_collector.combine_data_sources(
        use_yahoo=True,
        period=data_period
    )
    
    if data.empty:
        raise ValueError("No data available for prediction")
    
    # Make prediction
    result = predictor.predict_single(data, horizon=horizon)
    
    return result, data


def make_multiple_predictions(predictor, data_period='1y'):
    """Make predictions for multiple horizons."""
    logger.info("Making multi-horizon predictions")
    
    # Get latest data
    data = predictor.data_collector.combine_data_sources(
        use_yahoo=True,
        period=data_period
    )
    
    if data.empty:
        raise ValueError("No data available for prediction")
    
    # Make predictions
    results = predictor.predict_multiple_horizons(data)
    
    return results, data


def make_uncertainty_prediction(predictor, n_samples=100, data_period='1y'):
    """Make prediction with uncertainty quantification."""
    logger.info(f"Making uncertainty prediction with {n_samples} samples")
    
    # Get latest data
    data = predictor.data_collector.combine_data_sources(
        use_yahoo=True,
        period=data_period
    )
    
    if data.empty:
        raise ValueError("No data available for prediction")
    
    # Make prediction with uncertainty
    result = predictor.predict_with_uncertainty(data, n_samples=n_samples)
    
    return result, data


def get_real_time_prediction(predictor):
    """Get real-time prediction."""
    logger.info("Getting real-time prediction")
    
    result = predictor.get_real_time_prediction()
    
    return result


def save_prediction_results(results, output_path, include_timestamp=True):
    """Save prediction results to file."""
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_path).parent / f"{Path(output_path).stem}_{timestamp}{Path(output_path).suffix}"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")
    return output_path


def create_prediction_visualization(results, data, output_dir):
    """Create visualization for prediction results."""
    logger.info("Creating prediction visualization")
    
    viz = GoldPriceVisualizer()
    
    # Create prediction chart
    if 'predictions' in results:
        pred_fig = viz.plot_predictions(data, results)
        pred_fig.write_html(Path(output_dir) / 'predictions.html')
    
    # Create uncertainty chart if available
    if 'confidence_intervals' in results:
        uncertainty_fig = viz.plot_prediction_uncertainty(results)
        uncertainty_fig.write_html(Path(output_dir) / 'uncertainty.html')
    
    # Create dashboard
    dashboard_path = Path(output_dir) / 'dashboard.html'
    viz.create_dashboard(data, results, str(dashboard_path))
    
    logger.info(f"Visualizations saved to {output_dir}")


def print_prediction_summary(results):
    """Print a summary of prediction results."""
    print("\n" + "="*60)
    print("GOLD PRICE PREDICTION SUMMARY")
    print("="*60)
    
    if 'predictions' in results:
        predictions = results['predictions']
        print(f"Timestamp: {results.get('timestamp', 'N/A')}")
        print()
        
        for horizon, pred_data in predictions.items():
            if pred_data is None:
                continue
            
            horizon_days = horizon.replace('_day', '')
            print(f"{horizon_days}-Day Prediction:")
            print(f"  Current Price: ${pred_data['current_price']:.2f}")
            print(f"  Predicted Price: ${pred_data['prediction']:.2f}")
            print(f"  Price Change: ${pred_data['price_change']:.2f} ({pred_data['price_change_pct']:.2f}%)")
            print(f"  Confidence: {pred_data['confidence']:.2f}")
            print()
    
    elif 'prediction' in results:
        # Single prediction or uncertainty prediction
        pred_data = results['prediction']
        print(f"Timestamp: {results.get('timestamp', 'N/A')}")
        print()
        
        if 'mean' in pred_data:
            # Uncertainty prediction
            print("Prediction with Uncertainty:")
            print(f"  Current Price: ${pred_data['current_price']:.2f}")
            print(f"  Mean Prediction: ${pred_data['mean']:.2f}")
            print(f"  Standard Deviation: ${pred_data['std']:.2f}")
            print(f"  Price Change: ${pred_data['price_change']:.2f} ({pred_data['price_change_pct']:.2f}%)")
            print()
            
            if 'confidence_intervals' in results:
                print("Confidence Intervals:")
                for conf_level, interval in results['confidence_intervals'].items():
                    print(f"  {conf_level}: ${interval['lower']:.2f} - ${interval['upper']:.2f}")
                print()
        else:
            # Single prediction
            print("Single Prediction:")
            print(f"  Current Price: ${pred_data['current_price']:.2f}")
            print(f"  Predicted Price: ${pred_data['prediction']:.2f}")
            print(f"  Price Change: ${pred_data['price_change']:.2f} ({pred_data['price_change_pct']:.2f}%)")
            print(f"  Confidence: {pred_data['confidence']:.2f}")
            print()
    
    if 'model_info' in results:
        model_info = results['model_info']
        print("Model Information:")
        print(f"  Ensemble Method: {model_info.get('ensemble_method', 'N/A')}")
        print(f"  Number of Models: {model_info.get('model_count', 'N/A')}")
        print(f"  Models: {', '.join(model_info.get('model_names', []))}")
        print()
    
    if 'market_info' in results:
        market_info = results['market_info']
        print("Market Information:")
        print(f"  Market Open: {'Yes' if market_info.get('is_market_open') else 'No'}")
        print(f"  Current Time: {market_info.get('current_time', 'N/A')}")
        print()
    
    print("="*60)


def main():
    """Main prediction function."""
    parser = argparse.ArgumentParser(description='Make gold price predictions')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--mode', type=str, choices=['single', 'multiple', 'uncertainty', 'realtime'], 
                       default='multiple', help='Prediction mode')
    parser.add_argument('--horizon', type=int, default=1, help='Prediction horizon in days (for single mode)')
    parser.add_argument('--samples', type=int, default=100, help='Number of samples for uncertainty estimation')
    parser.add_argument('--period', type=str, default='1y', help='Data period to use')
    parser.add_argument('--output', type=str, help='Output file path for results')
    parser.add_argument('--visualize', action='store_true', help='Create visualizations')
    parser.add_argument('--output-dir', type=str, default='./predictions', help='Output directory')
    
    args = parser.parse_args()
    
    try:
        # Load predictor
        predictor = load_predictor(args.model, args.config)
        
        # Make predictions based on mode
        if args.mode == 'single':
            results, data = make_single_prediction(predictor, args.horizon, args.period)
        elif args.mode == 'multiple':
            results, data = make_multiple_predictions(predictor, args.period)
        elif args.mode == 'uncertainty':
            results, data = make_uncertainty_prediction(predictor, args.samples, args.period)
        elif args.mode == 'realtime':
            results = get_real_time_prediction(predictor)
            data = None  # Real-time mode handles data internally
        else:
            raise ValueError(f"Unknown mode: {args.mode}")
        
        # Print summary
        print_prediction_summary(results)
        
        # Save results if output path specified
        if args.output:
            save_prediction_results(results, args.output)
        
        # Create visualizations if requested
        if args.visualize and data is not None:
            Path(args.output_dir).mkdir(parents=True, exist_ok=True)
            create_prediction_visualization(results, data, args.output_dir)
        
        logger.info("Prediction completed successfully!")
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise


if __name__ == "__main__":
    main()
