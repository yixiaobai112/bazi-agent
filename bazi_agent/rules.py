"""
规则库数据加载模块
负责从bazi_rules文件夹加载所有规则数据
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger


class RulesLoader:
    """规则库加载器"""
    
    def __init__(self, rules_dir: str = "./bazi_rules"):
        """
        初始化规则库加载器
        
        Args:
            rules_dir: 规则库文件夹路径
        """
        self.rules_dir = Path(rules_dir)
        self._shengxiao_rules = None
        self._shensha_rules = None
        self._shishen_personality = None
        self._geju_career = None
        self._dayun_rules = None
        self._liunian_rules = None
        self._personality_scoring = None
    
    def load_all(self) -> Dict[str, Any]:
        """加载所有规则数据"""
        return {
            "shengxiao": self.load_shengxiao_rules(),
            "shensha": self.load_shensha_rules(),
            "shishen_personality": self.load_shishen_personality(),
            "geju_career": self.load_geju_career(),
            "dayun_rules": self.load_dayun_rules(),
            "liunian_rules": self.load_liunian_rules(),
            "personality_scoring": self.load_personality_scoring()
        }
    
    def load_shengxiao_rules(self) -> Dict[str, Any]:
        """加载生肖关系规则"""
        if self._shengxiao_rules is not None:
            return self._shengxiao_rules
        
        file_path = self.rules_dir / "01_生肖关系数据.md"
        if not file_path.exists():
            logger.warning(f"生肖关系数据文件不存在: {file_path}")
            return {}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # 解析三合关系
            sanhe = {}
            sanhe_match = re.search(r'### 三合关系表\s*\n\|.*\n\|.*\n((?:\|.*\n)+)', content)
            if sanhe_match:
                lines = sanhe_match.group(1).strip().split('\n')
                for line in lines[1:]:  # 跳过表头
                    if '|' in line:
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 3:
                            shengxiao_list = [s.strip() for s in parts[1].split('、')]
                            dizhi_list = [d.strip() for d in parts[2].split('、')]
                            for sx in shengxiao_list:
                                if sx not in sanhe:
                                    sanhe[sx] = []
                                sanhe[sx].extend([s for s in shengxiao_list if s != sx])
            
            # 解析六合关系
            liuhe = {}
            liuhe_match = re.search(r'### 六合关系表\s*\n\|.*\n\|.*\n((?:\|.*\n)+)', content)
            if liuhe_match:
                lines = liuhe_match.group(1).strip().split('\n')
                for line in lines[1:]:
                    if '|' in line:
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 2:
                            shengxiao_list = [s.strip() for s in parts[1].split('、')]
                            if len(shengxiao_list) == 2:
                                liuhe[shengxiao_list[0]] = shengxiao_list[1]
                                liuhe[shengxiao_list[1]] = shengxiao_list[0]
            
            # 解析相冲关系
            xiangchong = {}
            chong_match = re.search(r'### 相冲关系表\s*\n\|.*\n\|.*\n((?:\|.*\n)+)', content)
            if chong_match:
                lines = chong_match.group(1).strip().split('\n')
                for line in lines[1:]:
                    if '|' in line:
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 2:
                            shengxiao_list = [s.strip() for s in parts[1].split('、')]
                            if len(shengxiao_list) == 2:
                                xiangchong[shengxiao_list[0]] = shengxiao_list[1]
                                xiangchong[shengxiao_list[1]] = shengxiao_list[0]
            
            # 解析相害关系
            xianghai = {}
            hai_match = re.search(r'### 相害关系表\s*\n\|.*\n\|.*\n((?:\|.*\n)+)', content)
            if hai_match:
                lines = hai_match.group(1).strip().split('\n')
                for line in lines[1:]:
                    if '|' in line:
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 2:
                            shengxiao_list = [s.strip() for s in parts[1].split('、')]
                            if len(shengxiao_list) == 2:
                                xianghai[shengxiao_list[0]] = shengxiao_list[1]
                                xianghai[shengxiao_list[1]] = shengxiao_list[0]
            
            self._shengxiao_rules = {
                "sanhe": sanhe,
                "liuhe": liuhe,
                "xiangchong": xiangchong,
                "xianghai": xianghai
            }
            
            logger.info(f"已加载生肖关系规则: 三合{len(sanhe)}个, 六合{len(liuhe)}个, 相冲{len(xiangchong)}个, 相害{len(xianghai)}个")
            return self._shengxiao_rules
            
        except Exception as e:
            logger.error(f"加载生肖关系规则失败: {e}")
            return {}
    
    def load_shensha_rules(self) -> Dict[str, Any]:
        """加载神煞计算规则"""
        if self._shensha_rules is not None:
            return self._shensha_rules
        
        file_path = self.rules_dir / "02_神煞计算规则.md"
        if not file_path.exists():
            logger.warning(f"神煞计算规则文件不存在: {file_path}")
            return {}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # 解析天乙贵人 - 查找"计算规则表"部分
            tianyi_guiren = {}
            tianyi_match = re.search(r'### 计算规则表\s*\n\|.*\n\|.*\n((?:\|.*\n)+)', content)
            if tianyi_match:
                lines = tianyi_match.group(1).strip().split('\n')
                for line in lines[1:]:
                    if '|' in line and '日干' not in line and '天乙贵人' not in line:
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 2:
                            tiangan = parts[0]
                            dizhi_str = parts[1]
                            # 提取地支列表（可能包含"、")
                            dizhi_list = [d.strip() for d in dizhi_str.split('、') if d.strip()]
                            if dizhi_list:
                                tianyi_guiren[tiangan] = dizhi_list
            
            # 解析文昌贵人 - 查找"计算规则表"部分
            wenchang_guiren = {}
            # 先找到文昌贵人章节
            wenchang_section = re.search(r'## [三四].*文昌贵人.*?\n((?:.*\n)+?)(?=##|$)', content, re.MULTILINE | re.DOTALL)
            if wenchang_section:
                section_content = wenchang_section.group(1)
                wenchang_match = re.search(r'### 计算规则表\s*\n\|.*\n\|.*\n((?:\|.*\n)+)', section_content)
                if wenchang_match:
                    lines = wenchang_match.group(1).strip().split('\n')
                    for line in lines[1:]:
                        if '|' in line and '日干' not in line and '文昌贵人' not in line:
                            parts = [p.strip() for p in line.split('|') if p.strip()]
                            if len(parts) >= 2:
                                tiangan = parts[0]
                                dizhi = parts[1]
                                wenchang_guiren[tiangan] = dizhi
            
            # 解析红鸾天喜 - 分别解析红鸾和天喜
            hongluan_tianxi = {}
            # 解析红鸾星
            hongluan_section = re.search(r'## 五、红鸾星.*?\n((?:.*\n)+?)(?=##|$)', content, re.MULTILINE | re.DOTALL)
            if hongluan_section:
                section_content = hongluan_section.group(1)
                hongluan_match = re.search(r'\|.*年支.*红鸾.*\n\|.*\n((?:\|.*\n)+)', section_content)
                if hongluan_match:
                    lines = hongluan_match.group(1).strip().split('\n')
                    for line in lines:
                        if '|' in line and '年支' not in line:
                            parts = [p.strip() for p in line.split('|') if p.strip()]
                            if len(parts) >= 2:
                                nianzhi_str = parts[0]
                                # 提取年支（去掉括号内容）
                                nianzhi = re.sub(r'\([^)]*\)', '', nianzhi_str).strip()
                                hongluan = parts[1]
                                if nianzhi and hongluan:
                                    if nianzhi not in hongluan_tianxi:
                                        hongluan_tianxi[nianzhi] = {}
                                    hongluan_tianxi[nianzhi]["hongluan"] = hongluan
            
            # 解析天喜星
            tianxi_section = re.search(r'## 六、天喜星.*?\n((?:.*\n)+?)(?=##|$)', content, re.MULTILINE | re.DOTALL)
            if tianxi_section:
                section_content = tianxi_section.group(1)
                tianxi_match = re.search(r'\|.*年支.*天喜.*\n\|.*\n((?:\|.*\n)+)', section_content)
                if tianxi_match:
                    lines = tianxi_match.group(1).strip().split('\n')
                    for line in lines:
                        if '|' in line and '年支' not in line:
                            parts = [p.strip() for p in line.split('|') if p.strip()]
                            if len(parts) >= 2:
                                nianzhi_str = parts[0]
                                # 提取年支（去掉括号内容）
                                nianzhi = re.sub(r'\([^)]*\)', '', nianzhi_str).strip()
                                tianxi = parts[1]
                                if nianzhi and tianxi:
                                    if nianzhi not in hongluan_tianxi:
                                        hongluan_tianxi[nianzhi] = {}
                                    hongluan_tianxi[nianzhi]["tianxi"] = tianxi
            
            # 解析桃花(咸池) - 查找"计算规则表"部分
            taohua = {}
            taohua_section = re.search(r'## 七、咸池\(桃花\).*?\n((?:.*\n)+?)(?=##|$)', content, re.MULTILINE | re.DOTALL)
            if taohua_section:
                section_content = taohua_section.group(1)
                taohua_match = re.search(r'### 计算规则表\s*\n\|.*\n\|.*\n((?:\|.*\n)+)', section_content)
                if taohua_match:
                    lines = taohua_match.group(1).strip().split('\n')
                    for line in lines:
                        if '|' in line and '年支' not in line and '桃花' not in line:
                            parts = [p.strip() for p in line.split('|') if p.strip()]
                            if len(parts) >= 2:
                                nianzhi_str = parts[0]
                                # 提取年支列表（可能包含"、")
                                nianzhi_list = [d.strip() for d in nianzhi_str.split('、') if d.strip()]
                                taohua_dizhi = parts[1]
                                # 为每个年支创建映射
                                for nianzhi in nianzhi_list:
                                    if nianzhi not in taohua:
                                        taohua[nianzhi] = []
                                    if taohua_dizhi not in taohua[nianzhi]:
                                        taohua[nianzhi].append(taohua_dizhi)
            
            self._shensha_rules = {
                "tianyi_guiren": tianyi_guiren,
                "wenchang_guiren": wenchang_guiren,
                "hongluan_tianxi": hongluan_tianxi,
                "taohua": taohua
            }
            
            logger.info(f"已加载神煞计算规则: 天乙贵人{len(tianyi_guiren)}个, 文昌贵人{len(wenchang_guiren)}个, 红鸾天喜{len(hongluan_tianxi)}个, 桃花{len(taohua)}个")
            return self._shensha_rules
            
        except Exception as e:
            logger.error(f"加载神煞计算规则失败: {e}")
            return {}
    
    def load_shishen_personality(self) -> Dict[str, Any]:
        """加载十神性格特征"""
        if self._shishen_personality is not None:
            return self._shishen_personality
        
        file_path = self.rules_dir / "03_十神性格特征.md"
        if not file_path.exists():
            logger.warning(f"十神性格特征文件不存在: {file_path}")
            return {}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            personality = {}
            
            # 解析每个十神的性格特征
            shishen_list = ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"]
            
            for shishen in shishen_list:
                # 匹配格式: ### 1. 比肩 或 ### 比肩性格特征
                pattern = rf'### \d+\.\s*{shishen}.*?\n((?:.*\n)+?)(?=###|$)'
                match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
                if not match:
                    # 尝试另一种格式
                    pattern = rf'### {shishen}性格特征\s*\n((?:.*\n)+?)(?=###|$)'
                    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
                
                if match:
                    section = match.group(1)
                    # 从表格中提取正面性格和负面性格
                    zhengmian = []
                    fuminan = []
                    
                    # 查找表格中的所有行
                    table_lines = section.split('\n')
                    for line in table_lines:
                        if '|' in line and ('正面性格' in line or '负面性格' in line):
                            parts = [p.strip() for p in line.split('|') if p.strip()]
                            if len(parts) >= 2:
                                dimension = parts[0]
                                content = parts[1] if len(parts) > 1 else ""
                                
                                if '正面性格' in dimension:
                                    zhengmian = [s.strip() for s in content.split('、') if s.strip() and s.strip() != '**正面性格**']
                                elif '负面性格' in dimension:
                                    fuminan = [s.strip() for s in content.split('、') if s.strip() and s.strip() != '**负面性格**']
                    
                    # 如果表格解析失败，尝试直接文本匹配
                    if not zhengmian:
                        zhengmian_match = re.search(r'\*\*正面性格\*\*[：:]\s*([^\n\|]+)', section)
                        if not zhengmian_match:
                            zhengmian_match = re.search(r'正面性格[：:]\s*([^\n\|]+)', section)
                        if zhengmian_match:
                            zhengmian = [s.strip() for s in zhengmian_match.group(1).split('、') if s.strip()]
                    
                    if not fuminan:
                        fuminan_match = re.search(r'\*\*负面性格\*\*[：:]\s*([^\n\|]+)', section)
                        if not fuminan_match:
                            fuminan_match = re.search(r'负面性格[：:]\s*([^\n\|]+)', section)
                        if fuminan_match:
                            fuminan = [s.strip() for s in fuminan_match.group(1).split('、') if s.strip()]
                    
                    personality[shishen] = {
                        "zhengmian": zhengmian,
                        "fuminan": fuminan
                    }
            
            self._shishen_personality = personality
            logger.info(f"已加载十神性格特征: {len(personality)}个")
            return self._shishen_personality
            
        except Exception as e:
            logger.error(f"加载十神性格特征失败: {e}")
            return {}
    
    def load_geju_career(self) -> Dict[str, Any]:
        """加载格局职业倾向"""
        if self._geju_career is not None:
            return self._geju_career
        
        file_path = self.rules_dir / "04_格局职业倾向.md"
        if not file_path.exists():
            logger.warning(f"格局职业倾向文件不存在: {file_path}")
            return {}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            career = {}
            
            # 解析每个格局的职业倾向
            geju_list = ["正官格", "七杀格", "正财格", "偏财格", "正印格", "偏印格", "食神格", "伤官格"]
            
            for geju in geju_list:
                pattern = rf'### {geju}职业倾向\s*\n((?:.*\n)+?)(?=###|$)'
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    section = match.group(1)
                    # 提取适合职业
                    suitable_match = re.search(r'适合职业[：:]\s*([^\n]+)', section)
                    suitable = suitable_match.group(1).split('、') if suitable_match else []
                    
                    career[geju] = {
                        "suitable": [s.strip() for s in suitable]
                    }
            
            self._geju_career = career
            logger.info(f"已加载格局职业倾向: {len(career)}个")
            return self._geju_career
            
        except Exception as e:
            logger.error(f"加载格局职业倾向失败: {e}")
            return {}
    
    def load_dayun_rules(self) -> Dict[str, Any]:
        """加载大运计算规则"""
        if self._dayun_rules is not None:
            return self._dayun_rules
        
        file_path = self.rules_dir / "05_大运计算规则与代码.md"
        if not file_path.exists():
            logger.warning(f"大运计算规则文件不存在: {file_path}")
            return {}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # 提取规则信息
            rules = {
                "shunni_rules": {
                    "阳男": "顺排",
                    "阴女": "顺排",
                    "阴男": "逆排",
                    "阳女": "逆排"
                },
                "jieqi_names": [
                    "立春", "惊蛰", "清明", "立夏", "芒种", "小暑",
                    "立秋", "白露", "寒露", "立冬", "大雪", "小寒"
                ],
                "conversion": {
                    "3天": "1岁",
                    "1天": "4个月"
                }
            }
            
            self._dayun_rules = rules
            logger.info("已加载大运计算规则")
            return self._dayun_rules
            
        except Exception as e:
            logger.error(f"加载大运计算规则失败: {e}")
            return {}
    
    def load_liunian_rules(self) -> Dict[str, Any]:
        """加载流年分析规则"""
        if self._liunian_rules is not None:
            return self._liunian_rules
        
        file_path = self.rules_dir / "06_流年分析规则.md"
        if not file_path.exists():
            logger.warning(f"流年分析规则文件不存在: {file_path}")
            return {}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # 提取流年分析规则
            rules = {
                "yongshen_relations": {
                    "流年生用神": {"jixi": "大吉", "degree": 5},
                    "流年助用神": {"jixi": "吉", "degree": 4},
                    "流年泄用神": {"jixi": "小凶", "degree": 2},
                    "流年克用神": {"jixi": "大凶", "degree": 1}
                },
                "jishen_relations": {
                    "流年克忌神": {"jixi": "吉", "degree": 4},
                    "流年泄忌神": {"jixi": "小吉", "degree": 3},
                    "流年助忌神": {"jixi": "凶", "degree": 2},
                    "流年生忌神": {"jixi": "大凶", "degree": 1}
                }
            }
            
            self._liunian_rules = rules
            logger.info("已加载流年分析规则")
            return self._liunian_rules
            
        except Exception as e:
            logger.error(f"加载流年分析规则失败: {e}")
            return {}
    
    def load_personality_scoring(self) -> Dict[str, Any]:
        """加载性格维度评分规则"""
        if self._personality_scoring is not None:
            return self._personality_scoring
        
        file_path = self.rules_dir / "07_性格维度评分规则.md"
        if not file_path.exists():
            logger.warning(f"性格维度评分规则文件不存在: {file_path}")
            return {}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # 提取性格维度评分规则
            dimensions = [
                "外向性", "责任感", "情绪稳定性", "开放性", "宜人性",
                "执行力", "领导力", "创造力", "社交能力", "学习能力"
            ]
            
            scoring_rules = {}
            for dim in dimensions:
                pattern = rf'### \d+\. {dim}.*?\n((?:.*\n)+?)(?=###|$)'
                match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
                if match:
                    section = match.group(1)
                    rules = []
                    # 提取评分规则表格
                    table_match = re.search(r'\|.*\n\|.*\n((?:\|.*\n)+)', section)
                    if table_match:
                        lines = table_match.group(1).strip().split('\n')
                        for line in lines[1:]:
                            if '|' in line:
                                parts = [p.strip() for p in line.split('|') if p.strip()]
                                if len(parts) >= 3:
                                    condition = parts[0]
                                    score_str = parts[1]
                                    reason = parts[2] if len(parts) > 2 else ""
                                    # 解析分数范围
                                    score_match = re.search(r'(\d+)-(\d+)', score_str)
                                    if score_match:
                                        score_min = int(score_match.group(1))
                                        score_max = int(score_match.group(2))
                                        rules.append({
                                            "condition": condition,
                                            "score_range": [score_min, score_max],
                                            "reason": reason
                                        })
                    scoring_rules[dim] = rules
            
            self._personality_scoring = scoring_rules
            logger.info(f"已加载性格维度评分规则: {len(scoring_rules)}个维度")
            return self._personality_scoring
            
        except Exception as e:
            logger.error(f"加载性格维度评分规则失败: {e}")
            return {}


# 全局规则加载器实例
_rules_loader = None

def get_rules_loader(rules_dir: str = "./bazi_rules") -> RulesLoader:
    """获取规则加载器实例（单例模式）"""
    global _rules_loader
    if _rules_loader is None:
        _rules_loader = RulesLoader(rules_dir)
    return _rules_loader

