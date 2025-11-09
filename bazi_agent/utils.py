"""
工具函数模块
"""

from typing import Dict, Any, Optional, Tuple
from .core import BaziAgent
from .config import validate_config


def quick_analyze(
    name: str,
    gender: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    api_key: str = None,
    provider: str = "anthropic",
    model: str = "claude-sonnet-4-20250514"
) -> Dict[str, Any]:
    """
    快速分析，无需配置文件
    
    Args:
        name: 姓名
        gender: 性别 "男"/"女"
        year: 出生年份
        month: 出生月份
        day: 出生日期
        hour: 出生小时
        minute: 出生分钟（可选）
        api_key: LLM API密钥
        provider: LLM提供商
        model: 模型名称
        
    Returns:
        分析结果字典
    """
    config_dict = {
        "user": {
            "name": name,
            "gender": gender,
            "birth": {
                "year": year,
                "month": month,
                "day": day,
                "hour": hour,
                "minute": minute
            }
        },
        "llm": {
            "provider": provider,
            "api_key": api_key or "",
            "model": model
        },
        "analysis": {
            "include_llm_interpretation": bool(api_key)
        }
    }
    
    agent = BaziAgent(config_dict=config_dict)
    return agent.analyze()

