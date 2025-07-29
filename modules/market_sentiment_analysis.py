#!/usr/bin/env python3
"""
市场情绪分析模块
集成新闻情绪、社交媒体情绪和恐慌指数分析
"""

import numpy as np
import pandas as pd
import requests
import json
import re
from datetime import datetime, timedelta
from textblob import TextBlob
import yfinance as yf
from typing import Dict, List, Optional, Tuple
import logging
import time
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MarketSentimentAnalyzer:
    """市场情绪分析器"""
    
    def __init__(self):
        self.sentiment_cache = {}
        self.cache_duration = 300  # 5分钟缓存
        
        # 情绪权重配置
        self.sentiment_weights = {
            'news': 0.4,
            'social_media': 0.3,
            'fear_greed': 0.2,
            'vix': 0.1
        }
        
        # 关键词配置
        self.gold_keywords = [
            'gold', 'xauusd', 'precious metals', 'bullion',
            '黄金', '贵金属', 'inflation hedge', 'safe haven'
        ]
        
        self.sentiment_keywords = {
            'bullish': ['bullish', 'buy', 'long', 'positive', 'optimistic', 'rally', 'surge', 'boom'],
            'bearish': ['bearish', 'sell', 'short', 'negative', 'pessimistic', 'crash', 'dump', 'decline']
        }
        
        print("[情绪分析] 市场情绪分析模块初始化")
    
    def analyze_comprehensive_sentiment(self) -> Dict:
        """综合情绪分析"""
        try:
            print("[情绪分析] 开始综合情绪分析...")
            
            sentiment_data = {}
            
            # 1. 新闻情绪分析
            sentiment_data['news'] = self._analyze_news_sentiment()
            
            # 2. 社交媒体情绪（模拟）
            sentiment_data['social_media'] = self._analyze_social_sentiment()
            
            # 3. 恐慌贪婪指数
            sentiment_data['fear_greed'] = self._get_fear_greed_index()
            
            # 4. VIX波动率指数
            sentiment_data['vix'] = self._get_vix_sentiment()
            
            # 5. 计算综合情绪
            composite_sentiment = self._calculate_composite_sentiment(sentiment_data)
            
            # 6. 生成情绪信号
            sentiment_signal = self._generate_sentiment_signal(composite_sentiment)
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'individual_sentiments': sentiment_data,
                'composite_sentiment': composite_sentiment,
                'sentiment_signal': sentiment_signal,
                'confidence': self._calculate_sentiment_confidence(sentiment_data)
            }
            
            print(f"[情绪分析] 综合情绪分析完成")
            print(f"   综合情绪: {composite_sentiment['score']:.2f}")
            print(f"   情绪信号: {sentiment_signal['direction']}")
            
            return result
            
        except Exception as e:
            logger.error(f"综合情绪分析失败: {e}")
            return self._get_default_sentiment()
    
    def _analyze_news_sentiment(self) -> Dict:
        """新闻情绪分析"""
        try:
            # 检查缓存
            cache_key = 'news_sentiment'
            if self._is_cache_valid(cache_key):
                return self.sentiment_cache[cache_key]['data']
            
            # 模拟新闻数据（实际应用中应该从新闻API获取）
            news_headlines = self._get_simulated_news()
            
            sentiments = []
            for headline in news_headlines:
                sentiment = self._analyze_text_sentiment(headline)
                sentiments.append(sentiment)
            
            if sentiments:
                avg_sentiment = np.mean(sentiments)
                sentiment_std = np.std(sentiments)
            else:
                avg_sentiment = 0.0
                sentiment_std = 0.0
            
            # 转换为-1到1的范围
            normalized_sentiment = np.tanh(avg_sentiment)
            
            result = {
                'score': float(normalized_sentiment),
                'volatility': float(sentiment_std),
                'sample_size': len(sentiments),
                'raw_sentiments': sentiments[:5]  # 保存前5个原始情绪
            }
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"新闻情绪分析失败: {e}")
            return {'score': 0.0, 'volatility': 0.0, 'sample_size': 0, 'raw_sentiments': []}
    
    def _get_simulated_news(self) -> List[str]:
        """获取模拟新闻数据"""
        # 模拟新闻标题
        simulated_news = [
            "Gold prices surge as inflation concerns mount",
            "Central bank policies support precious metals outlook",
            "Economic uncertainty drives safe-haven demand for gold",
            "Technical analysis suggests gold breakout imminent",
            "Institutional investors increase gold allocations",
            "Dollar weakness boosts gold appeal",
            "Geopolitical tensions fuel gold rally",
            "Mining supply constraints support gold prices"
        ]
        
        # 随机选择一些新闻
        import random
        return random.sample(simulated_news, min(5, len(simulated_news)))
    
    def _analyze_text_sentiment(self, text: str) -> float:
        """分析文本情绪"""
        try:
            # 使用TextBlob进行情绪分析
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            # 检查黄金相关关键词
            text_lower = text.lower()
            gold_relevance = any(keyword in text_lower for keyword in self.gold_keywords)
            
            # 检查情绪关键词
            bullish_count = sum(1 for word in self.sentiment_keywords['bullish'] if word in text_lower)
            bearish_count = sum(1 for word in self.sentiment_keywords['bearish'] if word in text_lower)
            
            # 调整情绪分数
            if gold_relevance:
                polarity *= 1.2  # 增强黄金相关新闻的权重
            
            if bullish_count > bearish_count:
                polarity += 0.1
            elif bearish_count > bullish_count:
                polarity -= 0.1
            
            return float(polarity)
            
        except Exception as e:
            logger.error(f"文本情绪分析失败: {e}")
            return 0.0
    
    def _analyze_social_sentiment(self) -> Dict:
        """社交媒体情绪分析（模拟）"""
        try:
            # 检查缓存
            cache_key = 'social_sentiment'
            if self._is_cache_valid(cache_key):
                return self.sentiment_cache[cache_key]['data']
            
            # 模拟社交媒体数据
            social_posts = self._get_simulated_social_posts()
            
            sentiments = []
            for post in social_posts:
                sentiment = self._analyze_text_sentiment(post)
                sentiments.append(sentiment)
            
            if sentiments:
                avg_sentiment = np.mean(sentiments)
                sentiment_std = np.std(sentiments)
                
                # 计算情绪趋势
                recent_sentiments = sentiments[-3:] if len(sentiments) >= 3 else sentiments
                trend = np.mean(recent_sentiments) - np.mean(sentiments[:-3]) if len(sentiments) > 3 else 0
            else:
                avg_sentiment = 0.0
                sentiment_std = 0.0
                trend = 0.0
            
            result = {
                'score': float(np.tanh(avg_sentiment)),
                'volatility': float(sentiment_std),
                'trend': float(trend),
                'sample_size': len(sentiments)
            }
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"社交媒体情绪分析失败: {e}")
            return {'score': 0.0, 'volatility': 0.0, 'trend': 0.0, 'sample_size': 0}
    
    def _get_simulated_social_posts(self) -> List[str]:
        """获取模拟社交媒体数据"""
        simulated_posts = [
            "Gold looking strong today! 🚀 #XAUUSD #Gold",
            "Time to buy more gold? Inflation is getting crazy",
            "Gold breaking resistance levels, bullish setup",
            "Central banks buying gold, smart money knows",
            "Gold vs Bitcoin debate continues...",
            "Safe haven demand driving gold higher",
            "Technical analysis shows gold uptrend intact",
            "Dollar weakness = gold strength"
        ]
        
        import random
        return random.sample(simulated_posts, min(6, len(simulated_posts)))
    
    def _get_fear_greed_index(self) -> Dict:
        """获取恐慌贪婪指数"""
        try:
            # 检查缓存
            cache_key = 'fear_greed'
            if self._is_cache_valid(cache_key):
                return self.sentiment_cache[cache_key]['data']
            
            # 模拟恐慌贪婪指数（实际应用中应该从API获取）
            # 0-100的指数，50为中性
            import random
            fear_greed_value = random.randint(20, 80)
            
            # 转换为-1到1的情绪分数
            sentiment_score = (fear_greed_value - 50) / 50
            
            # 解释指数
            if fear_greed_value < 25:
                interpretation = "extreme_fear"
            elif fear_greed_value < 45:
                interpretation = "fear"
            elif fear_greed_value < 55:
                interpretation = "neutral"
            elif fear_greed_value < 75:
                interpretation = "greed"
            else:
                interpretation = "extreme_greed"
            
            result = {
                'score': float(sentiment_score),
                'raw_value': fear_greed_value,
                'interpretation': interpretation
            }
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"恐慌贪婪指数获取失败: {e}")
            return {'score': 0.0, 'raw_value': 50, 'interpretation': 'neutral'}
    
    def _get_vix_sentiment(self) -> Dict:
        """获取VIX波动率情绪"""
        try:
            # 检查缓存
            cache_key = 'vix_sentiment'
            if self._is_cache_valid(cache_key):
                return self.sentiment_cache[cache_key]['data']
            
            # 尝试获取VIX数据
            try:
                vix = yf.Ticker("^VIX")
                vix_data = vix.history(period="5d")
                
                if not vix_data.empty:
                    current_vix = float(vix_data['Close'].iloc[-1])
                    vix_change = float(vix_data['Close'].iloc[-1] - vix_data['Close'].iloc[-2]) if len(vix_data) > 1 else 0
                else:
                    current_vix = 20.0  # 默认值
                    vix_change = 0.0
            except:
                current_vix = 20.0  # 默认值
                vix_change = 0.0
            
            # VIX情绪解释
            # VIX高表示恐慌（对黄金有利），VIX低表示平静
            if current_vix > 30:
                vix_sentiment = 0.5  # 高恐慌对黄金有利
                interpretation = "high_fear"
            elif current_vix > 20:
                vix_sentiment = 0.2
                interpretation = "moderate_fear"
            elif current_vix > 15:
                vix_sentiment = 0.0
                interpretation = "low_fear"
            else:
                vix_sentiment = -0.2  # 极低恐慌对黄金不利
                interpretation = "complacency"
            
            result = {
                'score': float(vix_sentiment),
                'raw_value': current_vix,
                'change': vix_change,
                'interpretation': interpretation
            }
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"VIX情绪分析失败: {e}")
            return {'score': 0.0, 'raw_value': 20.0, 'change': 0.0, 'interpretation': 'neutral'}
    
    def _calculate_composite_sentiment(self, sentiment_data: Dict) -> Dict:
        """计算综合情绪"""
        try:
            weighted_score = 0.0
            total_weight = 0.0
            
            for sentiment_type, data in sentiment_data.items():
                if sentiment_type in self.sentiment_weights and 'score' in data:
                    weight = self.sentiment_weights[sentiment_type]
                    score = data['score']
                    
                    weighted_score += weight * score
                    total_weight += weight
            
            if total_weight > 0:
                composite_score = weighted_score / total_weight
            else:
                composite_score = 0.0
            
            # 计算情绪强度
            sentiment_values = [data.get('score', 0) for data in sentiment_data.values()]
            sentiment_volatility = np.std(sentiment_values) if sentiment_values else 0.0
            
            # 情绪一致性
            positive_count = sum(1 for score in sentiment_values if score > 0.1)
            negative_count = sum(1 for score in sentiment_values if score < -0.1)
            neutral_count = len(sentiment_values) - positive_count - negative_count
            
            consistency = max(positive_count, negative_count) / len(sentiment_values) if sentiment_values else 0.0
            
            return {
                'score': float(composite_score),
                'volatility': float(sentiment_volatility),
                'consistency': float(consistency),
                'positive_signals': positive_count,
                'negative_signals': negative_count,
                'neutral_signals': neutral_count
            }
            
        except Exception as e:
            logger.error(f"综合情绪计算失败: {e}")
            return {'score': 0.0, 'volatility': 0.0, 'consistency': 0.0, 'positive_signals': 0, 'negative_signals': 0, 'neutral_signals': 0}
    
    def _generate_sentiment_signal(self, composite_sentiment: Dict) -> Dict:
        """生成情绪信号"""
        try:
            score = composite_sentiment['score']
            consistency = composite_sentiment['consistency']
            volatility = composite_sentiment['volatility']
            
            # 基于分数确定方向
            if score > 0.2:
                direction = "bullish"
            elif score < -0.2:
                direction = "bearish"
            else:
                direction = "neutral"
            
            # 基于一致性和波动率确定强度
            if consistency > 0.7 and volatility < 0.3:
                strength = "strong"
            elif consistency > 0.5 and volatility < 0.5:
                strength = "moderate"
            else:
                strength = "weak"
            
            # 计算信号置信度
            confidence = consistency * (1 - volatility) * min(abs(score) * 2, 1.0)
            
            return {
                'direction': direction,
                'strength': strength,
                'confidence': float(confidence),
                'score': float(score)
            }
            
        except Exception as e:
            logger.error(f"情绪信号生成失败: {e}")
            return {'direction': 'neutral', 'strength': 'weak', 'confidence': 0.5, 'score': 0.0}
    
    def _calculate_sentiment_confidence(self, sentiment_data: Dict) -> float:
        """计算情绪分析置信度"""
        try:
            confidence_factors = []
            
            for sentiment_type, data in sentiment_data.items():
                if isinstance(data, dict):
                    # 基于样本大小的置信度
                    sample_size = data.get('sample_size', 1)
                    size_confidence = min(sample_size / 10, 1.0)
                    
                    # 基于波动率的置信度
                    volatility = data.get('volatility', 0.5)
                    volatility_confidence = 1.0 - min(volatility, 1.0)
                    
                    # 综合置信度
                    factor_confidence = (size_confidence + volatility_confidence) / 2
                    confidence_factors.append(factor_confidence)
            
            if confidence_factors:
                overall_confidence = np.mean(confidence_factors)
            else:
                overall_confidence = 0.5
            
            return float(overall_confidence)
            
        except Exception as e:
            logger.error(f"置信度计算失败: {e}")
            return 0.5
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.sentiment_cache:
            return False
        
        cache_time = self.sentiment_cache[cache_key]['timestamp']
        return (datetime.now() - cache_time).total_seconds() < self.cache_duration
    
    def _cache_result(self, cache_key: str, data: Dict):
        """缓存结果"""
        self.sentiment_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': data
        }
    
    def _get_default_sentiment(self) -> Dict:
        """获取默认情绪数据"""
        return {
            'timestamp': datetime.now().isoformat(),
            'individual_sentiments': {
                'news': {'score': 0.0, 'volatility': 0.0, 'sample_size': 0},
                'social_media': {'score': 0.0, 'volatility': 0.0, 'trend': 0.0, 'sample_size': 0},
                'fear_greed': {'score': 0.0, 'raw_value': 50, 'interpretation': 'neutral'},
                'vix': {'score': 0.0, 'raw_value': 20.0, 'change': 0.0, 'interpretation': 'neutral'}
            },
            'composite_sentiment': {'score': 0.0, 'volatility': 0.0, 'consistency': 0.0, 'positive_signals': 0, 'negative_signals': 0, 'neutral_signals': 0},
            'sentiment_signal': {'direction': 'neutral', 'strength': 'weak', 'confidence': 0.5, 'score': 0.0},
            'confidence': 0.5
        }
    
    def get_sentiment_prediction_signal(self, sentiment_data: Dict = None) -> Dict:
        """获取情绪预测信号"""
        if sentiment_data is None:
            sentiment_data = self.analyze_comprehensive_sentiment()
        
        signal = sentiment_data.get('sentiment_signal', {})
        composite = sentiment_data.get('composite_sentiment', {})
        
        return {
            'signal': signal.get('direction', 'neutral'),
            'confidence': signal.get('confidence', 0.5),
            'strength': composite.get('score', 0.0),
            'details': {
                'sentiment_score': composite.get('score', 0.0),
                'consistency': composite.get('consistency', 0.0),
                'volatility': composite.get('volatility', 0.0)
            }
        }


def main():
    """测试函数"""
    print("市场情绪分析模块测试")
    print("=" * 40)

    # 创建情绪分析器
    analyzer = MarketSentimentAnalyzer()

    try:
        # 执行综合情绪分析
        print("🔍 执行综合情绪分析...")
        sentiment_result = analyzer.analyze_comprehensive_sentiment()

        print("✅ 情绪分析完成")

        # 显示结果
        composite = sentiment_result['composite_sentiment']
        signal = sentiment_result['sentiment_signal']

        print(f"\n📊 综合情绪结果:")
        print(f"   情绪分数: {composite['score']:.3f}")
        print(f"   一致性: {composite['consistency']:.3f}")
        print(f"   波动率: {composite['volatility']:.3f}")

        print(f"\n🎯 情绪信号:")
        print(f"   方向: {signal['direction']}")
        print(f"   强度: {signal['strength']}")
        print(f"   置信度: {signal['confidence']:.3f}")

        print(f"\n📈 各项情绪:")
        for name, data in sentiment_result['individual_sentiments'].items():
            score = data.get('score', 0)
            print(f"   {name}: {score:.3f}")

        # 获取预测信号
        pred_signal = analyzer.get_sentiment_prediction_signal(sentiment_result)
        print(f"\n🔮 预测信号:")
        print(f"   信号: {pred_signal['signal']}")
        print(f"   置信度: {pred_signal['confidence']:.3f}")
        print(f"   强度: {pred_signal['strength']:.3f}")

        print("\n✅ 市场情绪分析测试完成!")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
