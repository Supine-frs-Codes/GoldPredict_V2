#!/usr/bin/env python3
"""
GoldPredict V2.0 模块包
包含高级功能模块
"""

# 版本信息
__version__ = "2.0.0"
__author__ = "GoldPredict Team"

# 导出主要类
try:
    from .advanced_technical_indicators import AdvancedTechnicalIndicators
    __all__ = ['AdvancedTechnicalIndicators']
except ImportError:
    __all__ = []

# 可选模块导入
try:
    from .deep_learning_models import DeepLearningEnsemble
    __all__.append('DeepLearningEnsemble')
except ImportError:
    pass

try:
    from .gpu_accelerated_computing import GPUAcceleratedComputing
    __all__.append('GPUAcceleratedComputing')
except ImportError:
    pass

try:
    from .market_sentiment_analysis import MarketSentimentAnalyzer
    __all__.append('MarketSentimentAnalyzer')
except ImportError:
    pass
