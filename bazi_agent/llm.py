"""
LLM集成模块
负责调用大语言模型生成解读报告
"""

import time
from typing import Dict, Any, Optional, List
from loguru import logger

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .exceptions import LLMAPIError
from .config import LLMConfig, AnalysisConfig


class LLMGenerator:
    """LLM生成器"""
    
    def __init__(self, llm_config: LLMConfig, analysis_config: AnalysisConfig = None):
        """
        初始化LLM生成器
        
        Args:
            llm_config: LLM配置
            analysis_config: 分析配置（可选）
        """
        self.llm_config = llm_config
        self.analysis_config = analysis_config or AnalysisConfig()
        self.client = self._create_client()
    
    def _create_client(self):
        """创建LLM客户端"""
        if self.llm_config.provider == "anthropic":
            if Anthropic is None:
                raise LLMAPIError("anthropic库未安装，请运行: pip install anthropic")
            return Anthropic(api_key=self.llm_config.api_key)
        
        elif self.llm_config.provider in ["openai", "yunwu", "custom"]:
            # yunwu和custom都使用OpenAI兼容的API格式
            if OpenAI is None:
                raise LLMAPIError("openai库未安装，请运行: pip install openai")
            client_kwargs = {
                "api_key": self.llm_config.api_key,
                "timeout": self.llm_config.timeout
            }
            if self.llm_config.base_url:
                client_kwargs["base_url"] = self.llm_config.base_url
            logger.debug(f"创建OpenAI客户端: base_url={self.llm_config.base_url}, timeout={self.llm_config.timeout}")
            return OpenAI(**client_kwargs)
        
        else:
            raise LLMAPIError(f"不支持的LLM提供商: {self.llm_config.provider}")
    
    def generate_interpretation(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成解读报告
        
        Args:
            analysis_data: 分析结果数据
            
        Returns:
            包含LLM解读的字典
        """
        if not self.analysis_config.include_llm_interpretation:
            return {}
        
        try:
            # 构建提示词
            prompt = self._build_prompt(analysis_data)
            
            # 调用LLM
            response = self._call_llm_with_retry(prompt)
            
            # 解析响应
            interpretation = self._parse_response(response)
            
            return {
                "comprehensive_analysis": interpretation.get("comprehensive", ""),
                "detailed_interpretation": interpretation.get("detailed", {}),
                "suggestions": interpretation.get("suggestions", [])
            }
        
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            if self.llm_config.max_retries > 0:
                raise LLMAPIError(f"LLM调用失败，已重试{self.llm_config.max_retries}次: {e}")
            return {}
    
    def _build_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """构建提示词"""
        user_info = analysis_data.get("user_basic_info", {})
        bazi_info = analysis_data.get("bazi_basic", {})
        wuxing = analysis_data.get("wuxing_analysis", {})
        shishen = analysis_data.get("shishen_analysis", {})
        geju = analysis_data.get("geju_analysis", {})
        
        prompt = f"""你是一位资深的命理分析专家，请根据以下八字信息，生成一份专业的命理分析报告。

用户信息：
姓名：{user_info.get('name', '')}
性别：{user_info.get('gender', '')}
出生时间：{user_info.get('birth_year', '')}年{user_info.get('birth_month', '')}月{user_info.get('birth_day', '')}日

八字信息：
年柱：{bazi_info.get('nian_zhu', {}).get('tiangan', '')}{bazi_info.get('nian_zhu', {}).get('dizhi', '')}
月柱：{bazi_info.get('yue_zhu', {}).get('tiangan', '')}{bazi_info.get('yue_zhu', {}).get('dizhi', '')}
日柱：{bazi_info.get('ri_zhu', {}).get('tiangan', '')}{bazi_info.get('ri_zhu', {}).get('dizhi', '')}
时柱：{bazi_info.get('shi_zhu', {}).get('tiangan', '')}{bazi_info.get('shi_zhu', {}).get('dizhi', '')}

五行分析：
最旺五行：{wuxing.get('wuxing_most', '')}
缺失五行：{wuxing.get('wuxing_missing', [])}
日主旺衰：{wuxing.get('rizhu_status', '')}
用神：{wuxing.get('yongshen', [])}

格局分析：
格局类型：{geju.get('geju_type', '')}
格局层次：{geju.get('geju_level', '')}

请生成一份{self.analysis_config.llm_interpretation_level}的命理分析报告，包括：
1. 综合分析（性格、能力、运势）
2. 各维度详细解读（事业、财运、婚姻、健康等）
3. 个性化建议

要求：
- 语言专业但易懂
- 内容积极正面
- 避免绝对化表述
- 提供实用建议
"""
        return prompt
    
    def _call_llm_with_retry(self, prompt: str) -> str:
        """调用LLM，带重试机制"""
        last_error = None
        
        for attempt in range(self.llm_config.max_retries + 1):
            try:
                if self.llm_config.provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.llm_config.model,
                        max_tokens=self.llm_config.max_tokens,
                        temperature=self.llm_config.temperature,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    return response.content[0].text
                
                elif self.llm_config.provider in ["openai", "yunwu", "custom"]:
                    # yunwu和custom都使用OpenAI兼容的API格式
                    logger.debug(f"调用LLM API: provider={self.llm_config.provider}, model={self.llm_config.model}, base_url={self.llm_config.base_url}")
                    logger.debug(f"请求参数: max_tokens={self.llm_config.max_tokens}, temperature={self.llm_config.temperature}")
                    
                    response = self.client.chat.completions.create(
                        model=self.llm_config.model,
                        max_tokens=self.llm_config.max_tokens,
                        temperature=self.llm_config.temperature,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }],
                        timeout=self.llm_config.timeout
                    )
                    logger.debug(f"LLM调用成功，响应长度: {len(response.choices[0].message.content) if response.choices else 0}")
                    return response.choices[0].message.content
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)
                
                # 详细的错误信息
                logger.error(f"LLM调用失败 (尝试 {attempt + 1}/{self.llm_config.max_retries + 1})")
                logger.error(f"错误类型: {error_type}")
                logger.error(f"错误信息: {error_msg}")
                logger.error(f"API配置: provider={self.llm_config.provider}, base_url={self.llm_config.base_url}, model={self.llm_config.model}")
                
                # 检查是否是连接错误
                if "Connection" in error_type or "getaddrinfo" in error_msg or "Failed to resolve" in error_msg:
                    logger.error("⚠️  网络连接问题：")
                    logger.error("   1. 请检查网络连接")
                    logger.error("   2. 请检查 base_url 是否正确")
                    logger.error("   3. 请检查是否需要代理")
                    logger.error(f"   4. 尝试访问: {self.llm_config.base_url}")
                
                # 打印更详细的错误信息
                if hasattr(e, 'response'):
                    logger.error(f"响应状态码: {getattr(e.response, 'status_code', 'N/A')}")
                    logger.error(f"响应内容: {getattr(e.response, 'text', 'N/A')}")
                
                if attempt < self.llm_config.max_retries:
                    wait_time = self.llm_config.retry_delay * (attempt + 1)
                    logger.warning(f"LLM调用失败，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.llm_config.max_retries + 1})")
                    time.sleep(wait_time)
                else:
                    raise LLMAPIError(f"LLM调用失败: {error_type}: {error_msg}")
        
        raise LLMAPIError(f"LLM调用失败，已重试{self.llm_config.max_retries}次: {last_error}")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        # 简化处理，直接返回文本
        # 实际可以解析结构化内容
        return {
            "comprehensive": response,
            "detailed": {},
            "suggestions": []
        }

