"""
配置管理模块
负责加载、验证和管理配置文件
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from loguru import logger

from .exceptions import InvalidConfigError, ConfigNotFoundError


class BirthConfig(BaseModel):
    """出生信息配置"""
    year: int = Field(..., ge=1900, le=2100, description="出生年份")
    month: int = Field(..., ge=1, le=12, description="出生月份")
    day: int = Field(..., ge=1, le=31, description="出生日期")
    hour: int = Field(..., ge=0, le=23, description="出生小时")
    minute: int = Field(default=0, ge=0, le=59, description="出生分钟")


class LocationConfig(BaseModel):
    """地理位置配置"""
    province: Optional[str] = None
    city: Optional[str] = None
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    use_true_solar_time: bool = False
    
    class Config:
        # 允许字段缺失
        extra = "allow"


class UserConfig(BaseModel):
    """用户信息配置"""
    name: str
    gender: str = Field(..., pattern="^(男|女)$")
    birth: BirthConfig
    location: Optional[LocationConfig] = None


class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = Field(..., pattern="^(anthropic|openai|custom|yunwu)$")
    api_key: str
    model: str
    temperature: float = Field(default=0.7, ge=0, le=1)
    max_tokens: int = Field(default=4000, ge=1, le=100000)
    timeout: int = Field(default=60, ge=1)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: int = Field(default=2, ge=0)
    base_url: Optional[str] = None
    system_prompt: Optional[str] = None
    
    class Config:
        # 允许字段缺失（某些配置可能没有timeout等字段）
        extra = "allow"


class AnalysisConfig(BaseModel):
    """分析配置"""
    dimensions: Optional[list] = None
    include_llm_interpretation: bool = True
    llm_interpretation_level: str = Field(
        default="detailed",
        pattern="^(simple|normal|detailed|comprehensive)$"
    )


class JSONOutputConfig(BaseModel):
    """JSON输出配置"""
    enabled: bool = True
    filepath: str = "./output/result.json"
    pretty: bool = True
    include_raw_data: bool = True


class CSVOutputConfig(BaseModel):
    """CSV输出配置"""
    enabled: bool = True
    filepath: str = "./output/result.csv"
    encoding: str = "utf-8-sig"


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    filepath: str = "./logs/bazi_agent.log"


class OutputConfig(BaseModel):
    """输出配置"""
    json: JSONOutputConfig = Field(default_factory=JSONOutputConfig, alias="json")
    csv: CSVOutputConfig = CSVOutputConfig()
    logging: LoggingConfig = LoggingConfig()
    
    class Config:
        # 允许字段名与父类属性同名
        populate_by_name = True
        protected_namespaces = ()
        # 解决json字段警告
        json_encoders = {
            # 自定义JSON编码器
        }


class Config(BaseModel):
    """完整配置模型"""
    user: UserConfig
    llm: LLMConfig
    analysis: AnalysisConfig = AnalysisConfig()
    output: OutputConfig = OutputConfig()

    class Config:
        extra = "forbid"


class ConfigLoader:
    """配置加载器"""
    
    @staticmethod
    def load_from_file(config_path: str) -> Config:
        """
        从文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Config对象
            
        Raises:
            ConfigNotFoundError: 配置文件不存在
            InvalidConfigError: 配置格式错误
        """
        path = Path(config_path)
        if not path.exists():
            raise ConfigNotFoundError(f"配置文件不存在: {config_path}")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidConfigError(f"配置文件JSON格式错误: {e}")
        except Exception as e:
            raise InvalidConfigError(f"读取配置文件失败: {e}")
        
        return ConfigLoader.load_from_dict(config_dict)
    
    @staticmethod
    def load_from_dict(config_dict: Dict[str, Any]) -> Config:
        """
        从字典加载配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            Config对象
            
        Raises:
            InvalidConfigError: 配置格式错误
        """
        try:
            config = Config(**config_dict)
            ConfigLoader._validate(config)
            return config
        except Exception as e:
            raise InvalidConfigError(f"配置验证失败: {e}")
    
    @staticmethod
    def _validate(config: Config) -> None:
        """
        验证配置的合理性
        
        Args:
            config: 配置对象
        """
        # 验证日期合法性
        try:
            from datetime import datetime
            datetime(
                config.user.birth.year,
                config.user.birth.month,
                config.user.birth.day
            )
        except ValueError as e:
            raise InvalidConfigError(f"日期不合法: {e}")
        
        # 验证真太阳时配置
        if config.user.location and config.user.location.use_true_solar_time:
            if not config.user.location.longitude or not config.user.location.latitude:
                if not config.user.location.province and not config.user.location.city:
                    logger.warning("启用真太阳时但未提供经纬度或省市信息，将使用默认北京时间")
                else:
                    logger.info("启用真太阳时，将根据省市信息查找经纬度")
        
        # 验证输出目录
        if config.output.json.enabled:
            output_dir = Path(config.output.json.filepath).parent
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # 验证日志目录
        log_dir = Path(config.output.logging.filepath).parent
        log_dir.mkdir(parents=True, exist_ok=True)


def validate_config(config_path: str) -> Tuple[bool, Optional[str]]:
    """
    验证配置文件是否合法
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        (是否合法, 错误信息)
    """
    try:
        ConfigLoader.load_from_file(config_path)
        return True, None
    except Exception as e:
        return False, str(e)

