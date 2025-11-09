# BaziAgent - 八字命理分析引擎

基于传统命理学的AI智能人物画像分析系统

**作者**：易晓白（花名）  
**版本**：1.0.0

## 📖 项目简介

BaziAgent 是一个基于传统八字命理学的智能分析系统，能够根据用户的出生信息自动排盘、进行多维度分析，并生成详细的人物画像报告。
但该项目的基础功能只能计算部分数据，如果需要更多数据，可查看下方规则库中所支持的内容。

### 主要功能

- 🔮 **自动排盘**：精确计算四柱八字，支持真太阳时校正
- 📊 **深度分析**：五行、十神、格局等多维度分析
- 🤖 **AI解读**：集成大语言模型，生成自然语言解读报告
- 💾 **数据导出**：结构化JSON输出，便于后续处理

### 解决的问题

1. **自动化八字排盘**：无需手动查表，自动计算准确的四柱八字
2. **多维度分析**：提供11个维度的深度分析（五行、十神、格局、性格、事业、财运、婚姻、健康、人际、大运、神煞）
3. **智能解读**：结合传统命理学规则和现代AI技术，生成易懂的分析报告
4. **标准化输出**：统一的JSON格式输出，便于集成到其他系统

## 📥 输入输出

### 输入

- **用户基本信息**：
  - 姓名
  - 性别（男/女）
  - 出生时间（年、月、日、时、分）
  - 出生地点（可选，用于真太阳时校正）

- **配置信息**：
  - LLM API配置（可选，用于AI解读）
  - 分析维度配置
  - 输出配置

### 输出

- **JSON格式的分析结果**，包含以下内容：
  - `user_basic_info`: 用户基本信息
  - `bazi_basic`: 八字基础信息（四柱、日主等）
  - `wuxing_analysis`: 五行分析（旺衰、喜忌、用神等）
  - `shishen_analysis`: 十神分析
  - `geju_analysis`: 格局分析
  - `personality_analysis`: 性格分析
  - `career_analysis`: 事业分析
  - `wealth_analysis`: 财运分析
  - `marriage_analysis`: 婚姻分析
  - `health_analysis`: 健康分析
  - `interpersonal_analysis`: 人际分析
  - `dayun_analysis`: 大运分析
  - `shensha_analysis`: 神煞分析
  - `liunian_analysis`: 流年分析
  - `llm_interpretation`: LLM解读（如果启用）

## 🚀 快速开始

### 安装

```bash
pip install bazi-agent
```

### 基本使用

#### 方法1：使用配置文件

1. **创建配置文件**

复制示例配置文件：
```bash
cp config.json.example config.json
cp user_config.json.example user_config.json
```

2. **编辑配置文件**

编辑 `user_config.json`，填入用户信息：
```json
{
  "name": "张三",
  "gender": "男",
  "birth": {
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 14,
    "minute": 30
  },
  "location": {
    "province": "北京市",
    "city": "北京市",
    "use_true_solar_time": true
  }
}
```

编辑 `config.json`，配置LLM API（可选）：
```json
{
  "llm": {
    "provider": "anthropic",
    "api_key": "your-api-key-here",
    "model": "claude-sonnet-4-20250514"
  }
}
```

3. **运行分析**

```bash
python run.py
```

#### 方法2：使用Python代码

```python
from bazi_agent import BaziAgent

# 创建实例
agent = BaziAgent(
    config_path="./config.json",
    user_config_path="./user_config.json"
)

# 执行分析
result = agent.analyze()

# 查看结果
print(result['bazi_basic']['sizhu'])
print(result['wuxing_analysis']['wuxing_most'])
```

#### 方法3：快速分析（无需配置文件）

```python
from bazi_agent import quick_analyze

result = quick_analyze(
    name="张三",
    gender="男",
    year=1990,
    month=5,
    day=15,
    hour=14,
    minute=30,
    api_key="your-api-key"  # 可选
)
```

## 📚 API 文档

### BaziAgent 类

#### `__init__(config_path, user_config_path, config_dict)`

初始化BaziAgent实例。

**参数：**
- `config_path` (str, 可选): 配置文件路径，默认为 `"./config.json"`
- `user_config_path` (str, 可选): 用户配置文件路径，默认为 `"./user_config.json"`
- `config_dict` (dict, 可选): 配置字典，如果提供则不读取文件

**示例：**
```python
agent = BaziAgent(config_path="./config.json", user_config_path="./user_config.json")
```

#### `analyze() -> Dict[str, Any]`

执行完整的八字分析。

**返回：**
- `Dict[str, Any]`: 包含所有分析结果的字典

**示例：**
```python
result = agent.analyze()
```

#### `get_bazi_basic() -> Dict[str, Any]`

获取八字基础信息（四柱、日主等）。

**返回：**
- `Dict[str, Any]`: 八字基础信息字典

**示例：**
```python
bazi = agent.get_bazi_basic()
print(bazi['sizhu'])  # 四柱
print(bazi['ri_zhu'])  # 日柱
```

#### `get_wuxing_analysis() -> Dict[str, Any]`

获取五行分析结果。

**返回：**
- `Dict[str, Any]`: 五行分析结果，包含：
  - `wuxing_most`: 最旺五行
  - `wuxing_missing`: 缺失五行
  - `rizhu_status`: 日主旺衰状态
  - `yongshen`: 用神列表

**示例：**
```python
wuxing = agent.get_wuxing_analysis()
print(wuxing['wuxing_most'])
print(wuxing['yongshen'])
```

#### `get_shishen_analysis() -> Dict[str, Any]`

获取十神分析结果。

**返回：**
- `Dict[str, Any]`: 十神分析结果

**示例：**
```python
shishen = agent.get_shishen_analysis()
```

#### `get_geju_analysis() -> Dict[str, Any]`

获取格局分析结果。

**返回：**
- `Dict[str, Any]`: 格局分析结果，包含：
  - `geju_type`: 格局类型
  - `geju_level`: 格局层次

**示例：**
```python
geju = agent.get_geju_analysis()
print(geju['geju_type'])
```

### 工具函数

#### `quick_analyze(name, gender, year, month, day, hour, minute, api_key, provider, model) -> Dict[str, Any]`

快速分析，无需配置文件。

**参数：**
- `name` (str): 姓名
- `gender` (str): 性别，"男" 或 "女"
- `year` (int): 出生年份
- `month` (int): 出生月份
- `day` (int): 出生日期
- `hour` (int): 出生小时
- `minute` (int, 可选): 出生分钟，默认为0
- `api_key` (str, 可选): LLM API密钥
- `provider` (str, 可选): LLM提供商，默认为 "anthropic"
- `model` (str, 可选): 模型名称，默认为 "claude-sonnet-4-20250514"

**返回：**
- `Dict[str, Any]`: 分析结果字典

**示例：**
```python
from bazi_agent import quick_analyze

result = quick_analyze(
    name="张三",
    gender="男",
    year=1990,
    month=5,
    day=15,
    hour=14,
    minute=30
)
```

#### `validate_config(config_path) -> Tuple[bool, Optional[str]]`

验证配置文件是否合法。

**参数：**
- `config_path` (str): 配置文件路径

**返回：**
- `Tuple[bool, Optional[str]]`: (是否合法, 错误信息)

**示例：**
```python
from bazi_agent import validate_config

is_valid, error = validate_config("./config.json")
if not is_valid:
    print(f"配置错误: {error}")
```

## ⚙️ 配置说明

### 配置文件结构

#### config.json

主配置文件，包含LLM配置、分析配置和输出配置。

```json
{
  "llm": {
    "provider": "anthropic",
    "api_key": "your-api-key-here",
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 30
  },
  "analysis": {
    "dimensions": ["wuxing", "shishen", "geju", ...],
    "include_llm_interpretation": true,
    "llm_interpretation_level": "detailed"
  },
  "output": {
    "json": {
      "enabled": true,
      "filepath": "./output/result.json",
      "pretty": true
    },
    "logging": {
      "level": "INFO",
      "filepath": "./logs/bazi_agent.log"
    }
  }
}
```

#### user_config.json

用户信息配置文件。

```json
{
  "name": "张三",
  "gender": "男",
  "birth": {
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 14,
    "minute": 30
  },
  "location": {
    "province": "北京市",
    "city": "北京市",
    "use_true_solar_time": true
  }
}
```

### LLM 提供商支持

- `custom`: 自定义OpenAI兼容API

## 📝 输出结果说明

分析结果以JSON格式保存到 `output/{用户姓名}_{出生日期}/result.json`。

主要字段说明：

- **user_basic_info**: 用户基本信息
- **bazi_basic**: 八字基础信息
  - `sizhu`: 四柱（年柱、月柱、日柱、时柱）
  - `rizhu_tiangan`: 日主天干
  - `rizhu_wuxing`: 日主五行
- **wuxing_analysis**: 五行分析
  - `wuxing_most`: 最旺五行
  - `wuxing_missing`: 缺失五行
  - `rizhu_status`: 日主旺衰（身旺/身弱/从强/从弱等）
  - `yongshen`: 用神列表
- **geju_analysis**: 格局分析
  - `geju_type`: 格局类型
  - `geju_level`: 格局层次
- **llm_interpretation**: LLM解读（如果启用）
  - `comprehensive_analysis`: 综合分析报告

## ⚠️ 注意事项

### 规则库（bazi_rules 目录）

本项目支持可选的规则库功能，用于更精确的分析。规则库文件位于 `bazi_rules` 目录下，包含：
- 生肖关系数据
- 神煞计算规则
- 十神性格特征
- 格局职业倾向
- 大运计算规则
- 流年分析规则
- 性格维度评分规则

**注意**：本项目仅公开核心计算逻辑和方式，不提供 `bazi_rules` 目录，系统会使用默认规则继续工作，但某些高级分析功能可能会受限。如果需要完整功能，请联系作者获取 `bazi_rules` 规则库。

详细的功能对比说明请参考 [规则库使用对比说明](BAZI_RULES_COMPARISON.md)。

## 🔧 开发

### 安装开发依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
python run.py
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 👤 作者信息

**作者**：易晓白（花名）  
**项目**：BaziAgent - 八字命理分析引擎

## 💼 商业对接

### 商业合作

本项目支持商业合作，包括但不限于：

- **规则库授权**：获取完整的 `bazi_rules` 规则库，享受完整功能
- **定制开发**：根据业务需求定制开发功能模块
- **技术咨询**：提供八字命理算法相关的技术咨询服务
- **API服务**：提供云端API服务，支持高并发调用
- **私有化部署**：提供私有化部署方案和技术支持

### 合作方式

如有商业合作需求，请通过以下方式联系：

1. **微信(WeChat)**：yixiaobai-AI（请备注"商业合作"）
2. **邮箱**：799278912@qq.com（主题请注明"BaziAgent商业合作"）

我们会在收到您的咨询后尽快回复，并安排专人对接您的需求。 





