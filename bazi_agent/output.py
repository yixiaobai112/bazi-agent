"""
输出管理模块
负责JSON格式的输出
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .exceptions import OutputError
from .config import OutputConfig


class OutputManager:
    """输出管理器"""
    
    def __init__(self, config: OutputConfig):
        """
        初始化输出管理器
        
        Args:
            config: 输出配置
        """
        self.config = config
    
    def save_results(self, results: Dict[str, Any]) -> Dict[str, str]:
        """
        保存分析结果
        
        Args:
            results: 分析结果字典
            
        Returns:
            保存的文件路径字典
        """
        saved_files = {}
        
        # 创建用户目录
        user_info = results.get("user_basic_info", {})
        user_name = user_info.get("name", "未知")
        birth_year = user_info.get("birth_year", 0)
        birth_month = user_info.get("birth_month", 0)
        birth_day = user_info.get("birth_day", 0)
        
        # 生成用户目录名: 用户姓名_生日
        user_dir_name = f"{user_name}_{birth_year}{birth_month:02d}{birth_day:02d}"
        user_dir = Path("output") / user_dir_name
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON
        if self.config.json.enabled:
            json_path = self._save_json(results, user_dir)
            saved_files["json"] = json_path
        
        return saved_files
    
    def _save_json(self, results: Dict[str, Any], user_dir: Path) -> str:
        """保存JSON文件"""
        try:
            # 使用用户目录
            filepath = user_dir / "result.json"
            
            # 添加元数据
            output_data = {
                **results,
                "metadata": {
                    "version": "1.0.0",
                    "timestamp": datetime.now().isoformat(),
                    "generated_by": "BaziAgent"
                }
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                if self.config.json.pretty:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(output_data, f, ensure_ascii=False)
            
            logger.info(f"JSON结果已保存: {filepath}")
            return str(filepath)
        
        except Exception as e:
            raise OutputError(f"保存JSON文件失败: {e}")

