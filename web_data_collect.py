#!/usr/bin/env python3
"""
Web界面专用的数据收集脚本
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

from src.data.data_collector import GoldDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """数据收集主函数"""
    print("[数据] 开始数据收集...")

    try:
        # 创建数据收集器
        collector = GoldDataCollector()

        # 获取数据 - 处理API限制
        print("[网络] 从Yahoo Finance获取数据...")
        try:
            data = collector.combine_data_sources(use_yahoo=True, period='1y')
        except Exception as e:
            print(f"[警告] API请求失败: {e}")
            # 检查是否有现有数据
            latest_data_file = Path("results/data/latest_gold_data.csv")
            if latest_data_file.exists():
                print("[信息] 使用现有数据文件...")
                data = pd.read_csv(latest_data_file)
                data['date'] = pd.to_datetime(data['date'])
                print("[成功] 已加载现有数据")
            else:
                print("[错误] 无现有数据文件，无法继续")
                return False
        
        if data.empty:
            print("[错误] 数据获取失败")
            return False
        
        print(f"[成功] 成功获取 {len(data)} 条数据记录")
        print(f"   时间范围: {data['date'].min()} 到 {data['date'].max()}")
        print(f"   当前价格: ${data['close'].iloc[-1]:.2f}")
        
        # 保存数据
        output_dir = Path("results/data")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"gold_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        data.to_csv(output_file, index=False)
        
        # 也保存为最新数据
        latest_file = output_dir / "latest_gold_data.csv"
        data.to_csv(latest_file, index=False)
        
        print(f"[成功] 数据已保存:")
        print(f"   详细数据: {output_file}")
        print(f"   最新数据: {latest_file}")
        
        # 显示数据摘要
        print(f"\n[上涨] 数据摘要:")
        print(f"   最高价: ${data['high'].max():.2f}")
        print(f"   最低价: ${data['low'].min():.2f}")
        print(f"   平均价: ${data['close'].mean():.2f}")
        print(f"   总成交量: {data['volume'].sum():,.0f}")
        
        return True
        
    except Exception as e:
        print(f"[错误] 数据收集失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
