#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BaziAgent 运行脚本
直接运行此脚本即可开始分析
"""

import sys
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from bazi_agent import BaziAgent
from loguru import logger


def main():
    """主函数"""
    print("=" * 60)
    print("BaziAgent - 八字命理分析系统")
    print("=" * 60)
    print()
    
    # 检查配置文件是否存在
    config_path = "./config.json"
    user_config_path = "./user_config.json"
    
    if not os.path.exists(config_path):
        print(f"❌ 错误: 配置文件不存在: {config_path}")
        print("请先创建 config.json 文件")
        return 1
    
    if not os.path.exists(user_config_path):
        print(f"⚠️  警告: 用户配置文件不存在: {user_config_path}")
        print("将使用 config.json 中的用户信息（如果存在）")
        print("建议创建 user_config.json 文件来单独管理用户信息")
        print()
    
    try:
        # 创建分析器实例
        print("📋 正在加载配置...")
        agent = BaziAgent(config_path=config_path, user_config_path=user_config_path)
        print("✅ 配置加载成功")
        print()
        
        # 显示用户信息
        user_info = agent.config.user
        print(f"👤 用户信息:")
        print(f"   姓名: {user_info.name}")
        print(f"   性别: {user_info.gender}")
        print(f"   出生时间: {user_info.birth.year}年{user_info.birth.month}月{user_info.birth.day}日 {user_info.birth.hour}:{user_info.birth.minute:02d}")
        if user_info.location:
            if user_info.location.province:
                print(f"   出生地: {user_info.location.province}{user_info.location.city or ''}")
            if user_info.location.use_true_solar_time:
                print(f"   真太阳时: 已启用")
        print()
        
        # 开始分析
        print("🔮 开始分析...")
        print("-" * 60)
        result = agent.analyze()
        print("-" * 60)
        print()
        
        # 显示分析结果摘要
        print("📊 分析结果摘要:")
        print(f"   八字: {result['bazi_basic']['sizhu']['nian']} {result['bazi_basic']['sizhu']['yue']} {result['bazi_basic']['sizhu']['ri']} {result['bazi_basic']['sizhu']['shi']}")
        print(f"   日主: {result['bazi_basic']['rizhu_tiangan']}")
        print(f"   生肖: {result['user_basic_info'].get('shengxiao', '未知')}")
        print(f"   最旺五行: {result['wuxing_analysis']['wuxing_most']}")
        if result['wuxing_analysis']['wuxing_missing']:
            print(f"   缺失五行: {', '.join(result['wuxing_analysis']['wuxing_missing'])}")
        print(f"   日主旺衰: {result['wuxing_analysis']['rizhu_status']}")
        print(f"   用神: {', '.join(result['wuxing_analysis']['yongshen']) if result['wuxing_analysis']['yongshen'] else '无'}")
        print(f"   格局: {result['geju_analysis']['geju_type']}")
        print()
        
        # 显示输出文件位置
        print("💾 结果已保存:")
        if agent.config.output.json.enabled:
            # 获取实际保存的文件路径
            user_info = result.get("user_basic_info", {})
            user_name = user_info.get("name", "未知")
            birth_year = user_info.get("birth_year", 0)
            birth_month = user_info.get("birth_month", 0)
            birth_day = user_info.get("birth_day", 0)
            user_dir_name = f"{user_name}_{birth_year}{birth_month:02d}{birth_day:02d}"
            json_path = f"./output/{user_dir_name}/result.json"
            print(f"   JSON: {json_path}")
        print()
        
        # 如果有LLM解读，显示提示
        if result.get('llm_interpretation') and result['llm_interpretation'].get('comprehensive_analysis'):
            print("🤖 LLM解读已生成，请查看输出文件获取详细内容")
            print()
        
        print("=" * 60)
        print("✅ 分析完成！")
        print("=" * 60)
        
        return 0
    
    except FileNotFoundError as e:
        print(f"❌ 错误: 文件未找到: {e}")
        return 1
    except Exception as e:
        print(f"❌ 错误: {e}")
        logger.exception("分析过程出错")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

