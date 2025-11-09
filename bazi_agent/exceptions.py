"""
异常处理模块
"""


class BaziAgentException(Exception):
    """基础异常类"""
    pass


class InvalidDateError(BaziAgentException):
    """日期不合法异常"""
    pass


class InvalidConfigError(BaziAgentException):
    """配置不合法异常"""
    pass


class LLMAPIError(BaziAgentException):
    """LLM API调用失败异常"""
    pass


class ConfigNotFoundError(BaziAgentException):
    """配置文件不存在异常"""
    pass


class CalculationError(BaziAgentException):
    """计算错误异常"""
    pass


class OutputError(BaziAgentException):
    """输出文件写入失败异常"""
    pass

