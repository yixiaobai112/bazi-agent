"""
核心引擎模块
BaziAgent主类
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

from .config import Config, ConfigLoader
from .calendar import CalendarCalc
from .analyzer import AlgoAnalyzer
from .llm import LLMGenerator
from .output import OutputManager
from .exceptions import InvalidDateError, InvalidConfigError, LLMAPIError


class BaziAgent:
    """八字命理分析引擎"""
    
    def __init__(
        self,
        config_path: str = "./config.json",
        user_config_path: str = "./user_config.json",
        config_dict: Optional[Dict[str, Any]] = None
    ):
        """
        初始化BaziAgent
        
        Args:
            config_path: 配置文件路径（LLM和分析配置）
            user_config_path: 用户配置文件路径（用户信息）
            config_dict: 配置字典（可选，如果提供则不读取文件）
        """
        # 加载配置
        if config_dict:
            self.config = ConfigLoader.load_from_dict(config_dict)
        else:
            # 检查环境变量
            env_config_path = os.getenv("BAZI_CONFIG_PATH")
            if env_config_path:
                config_path = env_config_path
            
            # 加载主配置（先加载为字典，不验证user字段）
            import json
            main_config_path_obj = Path(config_path)
            with open(main_config_path_obj, "r", encoding="utf-8") as f:
                main_config_dict = json.load(f)
            
            # 加载用户配置
            user_config_path_obj = Path(user_config_path)
            if user_config_path_obj.exists():
                with open(user_config_path_obj, "r", encoding="utf-8") as f:
                    user_config_dict = json.load(f)
                # 合并用户配置到主配置
                main_config_dict["user"] = user_config_dict
            elif "user" not in main_config_dict:
                # 如果既没有用户配置文件，主配置中也没有user字段，报错
                raise InvalidConfigError("缺少用户信息：请创建 user_config.json 文件或在 config.json 中包含 user 字段")
            
            # 验证并创建配置对象
            self.config = ConfigLoader.load_from_dict(main_config_dict)
        
        # 初始化日志
        self._setup_logging()
        
        # 初始化各模块
        self.calendar_calc = None
        self.analyzer = None
        self.llm_generator = None
        self.output_manager = None
    
    def _setup_logging(self) -> None:
        """设置日志"""
        from loguru import logger
        import sys
        
        # 移除默认handler
        logger.remove()
        
        # 添加控制台输出
        logger.add(
            sys.stderr,
            level=self.config.output.logging.level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        )
        
        # 添加文件输出
        log_file = Path(self.config.output.logging.filepath)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            level=self.config.output.logging.level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            rotation="10 MB",
            retention="7 days"
        )
    
    def analyze(self) -> Dict[str, Any]:
        """
        执行完整分析
        
        Returns:
            包含所有分析结果的字典
            
        Raises:
            InvalidDateError: 日期不合法
            InvalidConfigError: 配置不合法
            LLMAPIError: LLM调用失败
        """
        start_time = time.time()
        logger.info("开始八字分析")
        
        try:
            # 1. 历法计算（八字排盘）
            logger.info("开始八字排盘")
            self.calendar_calc = CalendarCalc(
                year=self.config.user.birth.year,
                month=self.config.user.birth.month,
                day=self.config.user.birth.day,
                hour=self.config.user.birth.hour,
                minute=self.config.user.birth.minute,
                longitude=self.config.user.location.longitude if self.config.user.location else None,
                latitude=self.config.user.location.latitude if self.config.user.location else None,
                province=self.config.user.location.province if self.config.user.location else None,
                city=self.config.user.location.city if self.config.user.location else None,
                use_true_solar_time=self.config.user.location.use_true_solar_time if self.config.user.location else False
            )
            
            bazi_basic = self.calendar_calc.get_bazi()
            lunar_info = self.calendar_calc.get_lunar_info()
            season_info = self.calendar_calc.get_season_info()
            
            logger.info(f"八字排盘完成: {bazi_basic['sizhu']['nian']} {bazi_basic['sizhu']['yue']} {bazi_basic['sizhu']['ri']} {bazi_basic['sizhu']['shi']}")
            
            # 2. 算法分析
            logger.info("开始算法分析")
            self.analyzer = AlgoAnalyzer(
                self.calendar_calc,
                gender=self.config.user.gender,
                birth_year=self.config.user.birth.year,
                birth_month=self.config.user.birth.month,
                birth_day=self.config.user.birth.day,
                birth_hour=self.config.user.birth.hour,
                birth_minute=self.config.user.birth.minute
            )
            analysis_results = self.analyzer.analyze_all()
            
            logger.info("算法分析完成")
            
            # 3. 构建用户基本信息
            user_basic_info = {
                "name": self.config.user.name,
                "gender": self.config.user.gender,
                "birth_year": self.config.user.birth.year,
                "birth_month": self.config.user.birth.month,
                "birth_day": self.config.user.birth.day,
                "birth_hour": self.config.user.birth.hour,
                "birth_minute": self.config.user.birth.minute,
                **lunar_info,
                **season_info
            }
            
            # 4. 构建八字基础信息
            bazi_basic_info = {
                **bazi_basic,
                "rizhu": f"{bazi_basic['ri_zhu']['tiangan']}{bazi_basic['ri_zhu']['dizhi']}",
                "rizhu_tiangan": bazi_basic["ri_zhu"]["tiangan"],
                "rizhu_wuxing": bazi_basic["ri_zhu"]["wuxing_tiangan"],
                "rizhu_yinyang": bazi_basic["ri_zhu"]["yinyang_tiangan"]
            }
            
            # 5. 整合所有结果
            results = {
                "user_basic_info": user_basic_info,
                "bazi_basic": bazi_basic_info,
                **analysis_results
            }
            
            # 6. LLM解读
            if self.config.analysis.include_llm_interpretation:
                logger.info("开始调用LLM生成解读")
                try:
                    self.llm_generator = LLMGenerator(self.config.llm, self.config.analysis)
                    llm_interpretation = self.llm_generator.generate_interpretation(results)
                    results["llm_interpretation"] = llm_interpretation
                    logger.info("LLM解读完成")
                except LLMAPIError as e:
                    logger.warning(f"LLM调用失败: {e}，继续使用算法结果")
                    results["llm_interpretation"] = {}
            
            # 7. 保存结果
            logger.info("开始保存结果")
            self.output_manager = OutputManager(self.config.output)
            saved_files = self.output_manager.save_results(results)
            logger.info(f"结果保存成功: {saved_files}")
            
            # 8. 添加执行时间
            execution_time = time.time() - start_time
            results["metadata"] = {
                "version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "execution_time": round(execution_time, 2)
            }
            
            logger.info(f"分析完成，总耗时: {execution_time:.2f}秒")
            
            return results
        
        except InvalidDateError as e:
            logger.error(f"日期错误: {e}")
            raise
        except InvalidConfigError as e:
            logger.error(f"配置错误: {e}")
            raise
        except Exception as e:
            logger.error(f"分析过程出错: {e}")
            raise
    
    def get_bazi_basic(self) -> Dict[str, Any]:
        """获取八字基础信息"""
        if not self.calendar_calc:
            self.analyze()
        return self.calendar_calc.get_bazi()
    
    def get_wuxing_analysis(self) -> Dict[str, Any]:
        """获取五行分析"""
        if not self.analyzer:
            self.analyze()
        return self.analyzer.analyze_wuxing()
    
    def get_shishen_analysis(self) -> Dict[str, Any]:
        """获取十神分析"""
        if not self.analyzer:
            self.analyze()
        return self.analyzer.analyze_shishen()
    
    def get_geju_analysis(self) -> Dict[str, Any]:
        """获取格局分析"""
        if not self.analyzer:
            self.analyze()
        return self.analyzer.analyze_geju()

