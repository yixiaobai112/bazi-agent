"""
算法分析模块
负责五行、十神、格局等13个维度的分析
"""

from typing import Dict, Any, List, Optional
from collections import Counter
from loguru import logger

from .calendar import CalendarCalc
from .dayun import DayunCalculator
from .liunian import LiunianAnalyzer
from .rules import RulesLoader, get_rules_loader
from .exceptions import CalculationError


class AlgoAnalyzer:
    """算法分析器"""
    
    # 十神定义（以日主为中心）
    SHI_SHEN_MAP = {
        "比肩": {"relation": "同我", "yinyang": "同性"},
        "劫财": {"relation": "同我", "yinyang": "异性"},
        "食神": {"relation": "我生", "yinyang": "同性"},
        "伤官": {"relation": "我生", "yinyang": "异性"},
        "偏财": {"relation": "我克", "yinyang": "同性"},
        "正财": {"relation": "我克", "yinyang": "异性"},
        "七杀": {"relation": "克我", "yinyang": "同性"},
        "正官": {"relation": "克我", "yinyang": "异性"},
        "偏印": {"relation": "生我", "yinyang": "同性"},
        "正印": {"relation": "生我", "yinyang": "异性"}
    }
    
    # 五行生克关系
    WUXING_SHENG = {
        "木": "火", "火": "土", "土": "金", "金": "水", "水": "木"
    }
    
    WUXING_KE = {
        "木": "土", "土": "水", "水": "火", "火": "金", "金": "木"
    }
    
    def __init__(self, calendar_calc: CalendarCalc, gender: str = "男", birth_year: int = 1990,
                 birth_month: int = 1, birth_day: int = 1, birth_hour: int = 0, birth_minute: int = 0):
        """
        初始化分析器
        
        Args:
            calendar_calc: 历法计算器实例
            gender: 性别
            birth_year: 出生年份
            birth_month: 出生月份
            birth_day: 出生日期
            birth_hour: 出生小时
            birth_minute: 出生分钟
        """
        self.calc = calendar_calc
        self.bazi = calendar_calc.get_bazi()
        self.rizhu_tiangan = self.bazi["ri_zhu"]["tiangan"]
        self.rizhu_wuxing = self.bazi["ri_zhu"]["wuxing_tiangan"]
        self.yue_dizhi = self.bazi["yue_zhu"]["dizhi"]
        self.yue_wuxing = self.bazi["yue_zhu"]["wuxing_dizhi"]
        
        # 用户信息
        self.gender = gender
        self.birth_year = birth_year
        self.birth_month = birth_month
        self.birth_day = birth_day
        self.birth_hour = birth_hour
        self.birth_minute = birth_minute
        
        # 加载规则库
        self.rules_loader = get_rules_loader()
        self.rules = self.rules_loader.load_all()
        
        # 大运计算器
        self.dayun_calculator = DayunCalculator()
        
        # 流年分析器
        self.liunian_analyzer = LiunianAnalyzer()
    
    def analyze_all(self) -> Dict[str, Any]:
        """执行所有分析"""
        result = {
            "wuxing_analysis": self.analyze_wuxing(),
            "shishen_analysis": self.analyze_shishen(),
            "geju_analysis": self.analyze_geju(),
            "personality_analysis": self.analyze_personality(),
            "career_analysis": self.analyze_career(),
            "wealth_analysis": self.analyze_wealth(),
            "marriage_analysis": self.analyze_marriage(),
            "health_analysis": self.analyze_health(),
            "interpersonal_analysis": self.analyze_interpersonal(),
            "dayun_analysis": self.analyze_dayun(),
            "shensha_analysis": self.analyze_shensha(),
            "liunian_analysis": self.analyze_liunian()
        }
        return result
    
    def analyze_wuxing(self) -> Dict[str, Any]:
        """五行分析"""
        # 统计五行分布
        wuxing_count = Counter()
        wuxing_positions = {
            "金": [], "木": [], "水": [], "火": [], "土": []
        }
        
        # 统计天干地支的五行
        for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
            zhu = self.bazi[zhu_name]
            # 天干五行
            tg_wx = zhu["wuxing_tiangan"]
            wuxing_count[tg_wx] += 1
            wuxing_positions[tg_wx].append(f"{zhu_name}天干{zhu['tiangan']}")
            
            # 地支五行
            dz_wx = zhu["wuxing_dizhi"]
            wuxing_count[dz_wx] += 1
            wuxing_positions[dz_wx].append(f"{zhu_name}地支{zhu['dizhi']}")
            
            # 地支藏干五行
            for cg in zhu["cang_gan"]:
                cg_wx = self.calc.TIAN_GAN_WUXING.get(cg, "")
                if cg_wx:
                    wuxing_count[cg_wx] += 0.3  # 藏干权重较低
                    wuxing_positions[cg_wx].append(f"{zhu_name}藏干{cg}")
        
        total = sum(wuxing_count.values())
        wuxing_percent = {wx: round(count / total * 100, 2) if total > 0 else 0 
                         for wx, count in wuxing_count.items()}
        
        # 找出最旺和最弱
        wuxing_most = max(wuxing_count.items(), key=lambda x: x[1])[0] if wuxing_count else "无"
        wuxing_least = min(wuxing_count.items(), key=lambda x: x[1])[0] if wuxing_count else "无"
        # 判断缺失：完全为0或占比小于5%视为缺失/过弱
        wuxing_missing = []
        total_count = sum(wuxing_count.values())
        for wx in ["金", "木", "水", "火", "土"]:
            count = wuxing_count.get(wx, 0)
            if count == 0 or (total_count > 0 and (count / total_count) < 0.05):
                wuxing_missing.append(wx)
        
        # 判断日主旺衰
        wangshuai = self._judge_wangshuai()
        
        # 判断用神喜忌
        yongshen = self._judge_yongshen(wangshuai)
        
        return {
            "wuxing_distribution": dict(wuxing_count),
            "wuxing_percent": wuxing_percent,
            "wuxing_positions": wuxing_positions,
            "wuxing_most": wuxing_most,
            "wuxing_least": wuxing_least,
            "wuxing_missing": wuxing_missing,
            "rizhu_status": wangshuai["status"],
            "wangshuai_value": wangshuai["value"],
            "wangshuai_level": wangshuai["level"],
            "yongshen": yongshen["yongshen"],
            "xishen": yongshen["xishen"],
            "jishen": yongshen["jishen"],
            "choushen": yongshen.get("choushen", [])
        }
    
    def _judge_wangshuai(self) -> Dict[str, Any]:
        """判断日主旺衰"""
        # 得令：日主五行与月令五行的关系
        deling = self.rizhu_wuxing == self.yue_wuxing
        
        # 得地：日主在地支中的根基
        dedi = False
        for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
            zhu = self.bazi[zhu_name]
            if zhu["wuxing_dizhi"] == self.rizhu_wuxing:
                dedi = True
                break
            # 检查藏干
            for cg in zhu["cang_gan"]:
                if self.calc.TIAN_GAN_WUXING.get(cg) == self.rizhu_wuxing:
                    dedi = True
                    break
        
        # 得势：其他干支对日主的帮扶
        deshi = 0
        for zhu_name in ["nian_zhu", "yue_zhu", "shi_zhu"]:
            zhu = self.bazi[zhu_name]
            # 天干帮扶
            if zhu["wuxing_tiangan"] == self.rizhu_wuxing:
                deshi += 1
            # 地支帮扶
            if zhu["wuxing_dizhi"] == self.rizhu_wuxing:
                deshi += 1
        
        # 计算旺衰值（0-100，50为中和）
        wangshuai_value = 50
        if deling:
            wangshuai_value += 20
        if dedi:
            wangshuai_value += 15
        wangshuai_value += deshi * 5
        
        # 判断等级
        if wangshuai_value >= 80:
            level = "太旺"
            status = "身旺"
        elif wangshuai_value >= 65:
            level = "偏旺"
            status = "身旺"
        elif wangshuai_value >= 50:
            level = "中和"
            status = "中和"
        elif wangshuai_value >= 35:
            level = "偏弱"
            status = "身弱"
        else:
            level = "太弱"
            status = "身弱"
        
        return {
            "value": int(wangshuai_value),
            "level": level,
            "status": status,
            "deling": deling,
            "dedi": dedi,
            "deshi": deshi
        }
    
    def _judge_yongshen(self, wangshuai: Dict[str, Any]) -> Dict[str, List[str]]:
        """判断用神喜忌"""
        status = wangshuai["status"]
        rizhu_wx = self.rizhu_wuxing
        
        if status == "身旺":
            # 身旺：取克泄耗为用神
            yongshen = [self.WUXING_KE[rizhu_wx]]  # 克我者
            xishen = [self.WUXING_SHENG[rizhu_wx]]  # 我生者（泄）
            jishen = [rizhu_wx]  # 同我者
            # 仇神：生忌神的五行（忌神是日主本身，生日主的是印）
            choushen = [k for k, v in self.WUXING_SHENG.items() if v == rizhu_wx]
        elif status == "身弱":
            # 身弱：取生扶为用神
            # 找到生我者
            sheng_wo = [k for k, v in self.WUXING_SHENG.items() if v == rizhu_wx][0]
            yongshen = [sheng_wo, rizhu_wx]  # 生我者和我
            xishen = [sheng_wo]
            jishen = [self.WUXING_KE[rizhu_wx], self.WUXING_SHENG[rizhu_wx]]
            # 仇神：生忌神的五行（忌神是克我者和泄我者，生克我者的是财，生泄我者的是比劫）
            ke_wo = self.WUXING_KE[rizhu_wx]  # 克我者
            xie_wo = self.WUXING_SHENG[rizhu_wx]  # 泄我者
            # 生克我者的五行（我克者，即财）
            sheng_ke_wo = [k for k, v in self.WUXING_KE.items() if v == ke_wo]
            # 生泄我者的五行（同我者，即比劫）
            sheng_xie_wo = [k for k, v in self.WUXING_SHENG.items() if v == xie_wo]
            choushen = list(set(sheng_ke_wo + sheng_xie_wo))
        else:
            # 中和：平衡为主
            yongshen = []
            xishen = []
            jishen = []
            choushen = []
        
        return {
            "yongshen": yongshen,
            "xishen": xishen,
            "jishen": jishen,
            "choushen": choushen
        }
    
    def analyze_shishen(self) -> Dict[str, Any]:
        """十神分析"""
        shishen_count = Counter()
        shishen_positions = {}
        
        # 计算各柱的十神
        for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
            zhu = self.bazi[zhu_name]
            # 天干十神
            tg_shishen = self._get_shishen(zhu["tiangan"], zhu["wuxing_tiangan"])
            shishen_count[tg_shishen] += 1
            if tg_shishen not in shishen_positions:
                shishen_positions[tg_shishen] = []
            shishen_positions[tg_shishen].append(f"{zhu_name}天干{zhu['tiangan']}")
            
            # 地支本气十神（取第一个藏干）
            if zhu["cang_gan"]:
                cg = zhu["cang_gan"][0]
                cg_wx = self.calc.TIAN_GAN_WUXING.get(cg, "")
                if cg_wx:
                    dz_shishen = self._get_shishen(cg, cg_wx)
                    shishen_count[dz_shishen] += 0.5
                    if dz_shishen not in shishen_positions:
                        shishen_positions[dz_shishen] = []
                    shishen_positions[dz_shishen].append(f"{zhu_name}地支{zhu['dizhi']}")
        
        return {
            "shishen_distribution": dict(shishen_count),
            "shishen_positions": shishen_positions,
            "shishen_combinations": self._analyze_shishen_combinations(shishen_count)
        }
    
    def _get_shishen(self, tiangan: str, wuxing: str) -> str:
        """根据天干和五行计算十神"""
        if wuxing == self.rizhu_wuxing:
            # 同我
            if self.calc.TIAN_GAN_YINYANG[tiangan] == self.calc.TIAN_GAN_YINYANG[self.rizhu_tiangan]:
                return "比肩"
            else:
                return "劫财"
        elif wuxing == self.WUXING_SHENG[self.rizhu_wuxing]:
            # 我生
            if self.calc.TIAN_GAN_YINYANG[tiangan] == self.calc.TIAN_GAN_YINYANG[self.rizhu_tiangan]:
                return "食神"
            else:
                return "伤官"
        elif wuxing == self.WUXING_KE[self.rizhu_wuxing]:
            # 克我
            if self.calc.TIAN_GAN_YINYANG[tiangan] == self.calc.TIAN_GAN_YINYANG[self.rizhu_tiangan]:
                return "七杀"
            else:
                return "正官"
        elif self.WUXING_KE[wuxing] == self.rizhu_wuxing:
            # 我克
            if self.calc.TIAN_GAN_YINYANG[tiangan] == self.calc.TIAN_GAN_YINYANG[self.rizhu_tiangan]:
                return "偏财"
            else:
                return "正财"
        elif self.WUXING_SHENG[wuxing] == self.rizhu_wuxing:
            # 生我
            if self.calc.TIAN_GAN_YINYANG[tiangan] == self.calc.TIAN_GAN_YINYANG[self.rizhu_tiangan]:
                return "偏印"
            else:
                return "正印"
        return "未知"
    
    def _analyze_shishen_combinations(self, shishen_count: Counter) -> List[Dict[str, Any]]:
        """分析十神组合"""
        combinations = []
        
        # 官杀混杂
        if shishen_count.get("正官", 0) > 0 and shishen_count.get("七杀", 0) > 0:
            combinations.append({
                "name": "官杀混杂",
                "type": "凶",
                "description": "既有正官又有七杀，主压力大、是非多"
            })
        
        # 食伤泄秀
        if shishen_count.get("食神", 0) > 0 and shishen_count.get("伤官", 0) > 0:
            combinations.append({
                "name": "食伤泄秀",
                "type": "吉",
                "description": "才华外显，有表达能力"
            })
        
        return combinations
    
    def analyze_geju(self) -> Dict[str, Any]:
        """格局分析"""
        # 判断是否特殊格局
        special_geju = self._judge_special_geju()
        if special_geju:
            return special_geju
        
        # 判断普通格局（正格）
        normal_geju = self._judge_normal_geju()
        return normal_geju
    
    def _judge_special_geju(self) -> Optional[Dict[str, Any]]:
        """判断特殊格局"""
        wangshuai = self._judge_wangshuai()
        
        # 从格判断（日主极弱）
        if wangshuai["value"] < 30:
            # 检查是否满盘某一种五行
            wuxing_analysis = self.analyze_wuxing()
            wuxing_dist = wuxing_analysis["wuxing_distribution"]
            
            # 找出最旺的五行
            max_wx = max(wuxing_dist.items(), key=lambda x: x[1])[0]
            max_count = wuxing_dist[max_wx]
            total = sum(wuxing_dist.values())
            
            if max_count / total > 0.7:  # 某五行占比超过70%
                if max_wx == "金":
                    return {
                        "geju_type": "从革格",
                        "geju_category": "专旺格",
                        "geju_level": "中高",
                        "description": "满盘金，金专旺"
                    }
                elif max_wx == "木":
                    return {
                        "geju_type": "曲直格",
                        "geju_category": "专旺格",
                        "geju_level": "高",
                        "description": "满盘木，木专旺"
                    }
                # ... 其他专旺格
        
        return None
    
    def _judge_normal_geju(self) -> Dict[str, Any]:
        """判断普通格局"""
        # 以月令透出的十神为格局
        yue_zhu = self.bazi["yue_zhu"]
        yue_tiangan = yue_zhu["tiangan"]
        yue_shishen = self._get_shishen(yue_tiangan, yue_zhu["wuxing_tiangan"])
        
        geju_map = {
            "正官": "正官格",
            "七杀": "七杀格",
            "正财": "正财格",
            "偏财": "偏财格",
            "正印": "正印格",
            "偏印": "偏印格",
            "食神": "食神格",
            "伤官": "伤官格"
        }
        
        geju_type = geju_map.get(yue_shishen, "普通格局")
        
        return {
            "geju_type": geju_type,
            "geju_category": "正格",
            "geju_level": "中等",
            "description": f"月令透{yue_shishen}，为{geju_type}"
        }
    
    def analyze_personality(self) -> Dict[str, Any]:
        """性格分析"""
        shishen_analysis = self.analyze_shishen()
        shishen_dist = shishen_analysis["shishen_distribution"]
        wuxing_analysis = self.analyze_wuxing()
        
        # 加载十神性格特征
        shishen_personality = self.rules.get("shishen_personality", {})
        
        # 根据十神分布生成性格特征
        personality_traits = []
        strengths = []
        weaknesses = []
        
        # 根据十神分布生成性格特征
        for shishen_name, count in shishen_dist.items():
            if count > 0 and shishen_name in shishen_personality:
                personality = shishen_personality[shishen_name]
                zhengmian = personality.get("zhengmian", [])
                fuminan = personality.get("fuminan", [])
                
                if zhengmian:
                    personality_traits.extend(zhengmian)
                    strengths.extend(zhengmian[:2])  # 取前2个正面特征
                if fuminan:
                    weaknesses.extend(fuminan[:2])  # 取前2个负面特征
        
        # 性格维度评分
        personality_scores = self._calculate_personality_scores(shishen_dist, wuxing_analysis)
        
        return {
            "core_traits": list(set(personality_traits)),
            "strengths": list(set(strengths))[:5],
            "weaknesses": list(set(weaknesses))[:5],
            "personality_scores": personality_scores,
            "shishen_distribution": dict(shishen_dist)
        }
    
    def _calculate_personality_scores(self, shishen_dist: Dict[str, float], wuxing_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """计算性格维度评分"""
        personality_scoring = self.rules.get("personality_scoring", {})
        scores = {}
        
        # 获取用神信息
        yongshen = wuxing_analysis.get("yongshen", [])
        rizhu_status = wuxing_analysis.get("rizhu_status", "")
        
        # 计算每个维度的分数
        dimensions = ["外向性", "责任感", "情绪稳定性", "开放性", "宜人性",
                     "执行力", "领导力", "创造力", "社交能力", "学习能力"]
        
        for dim in dimensions:
            dim_rules = personality_scoring.get(dim, [])
            score = 5.0  # 默认5分
            
            # 遍历规则,找到第一个满足的条件
            for rule in dim_rules:
                condition = rule.get("condition", "")
                score_range = rule.get("score_range", [5, 5])
                
                if self._evaluate_personality_condition(condition, shishen_dist, yongshen, rizhu_status):
                    score = sum(score_range) / len(score_range)
                    break
            
            scores[dim] = {
                "score": round(score, 1),
                "level": self._get_score_level(score)
            }
        
        return scores
    
    def _evaluate_personality_condition(self, condition: str, shishen_dist: Dict[str, float],
                                       yongshen: List[str], rizhu_status: str) -> bool:
        """评估性格评分条件"""
        # 简化条件评估逻辑
        if "官杀旺且为用神" in condition:
            guansha_count = shishen_dist.get("正官", 0) + shishen_dist.get("七杀", 0)
            return guansha_count >= 2 and any(ys in ["正官", "七杀"] for ys in yongshen)
        elif "比劫旺且为用神" in condition:
            bijie_count = shishen_dist.get("比肩", 0) + shishen_dist.get("劫财", 0)
            return bijie_count >= 2 and any(ys in ["比肩", "劫财"] for ys in yongshen)
        elif "食伤旺且为用神" in condition:
            shishang_count = shishen_dist.get("食神", 0) + shishen_dist.get("伤官", 0)
            return shishang_count >= 2 and any(ys in ["食神", "伤官"] for ys in yongshen)
        elif "印星旺且为用神" in condition:
            yinxing_count = shishen_dist.get("正印", 0) + shishen_dist.get("偏印", 0)
            return yinxing_count >= 2 and any(ys in ["正印", "偏印"] for ys in yongshen)
        elif "财星旺且为用神" in condition:
            caixing_count = shishen_dist.get("正财", 0) + shishen_dist.get("偏财", 0)
            return caixing_count >= 2 and any(ys in ["正财", "偏财"] for ys in yongshen)
        elif "身弱" in condition:
            return rizhu_status == "身弱"
        elif "身旺" in condition or "身强" in condition:
            return rizhu_status == "身旺"
        
        return False
    
    def _get_score_level(self, score: float) -> str:
        """获取分数等级"""
        if score >= 8:
            return "非常突出"
        elif score >= 7:
            return "突出"
        elif score >= 6:
            return "良好"
        elif score >= 4:
            return "中等"
        else:
            return "较弱"
    
    def analyze_career(self) -> Dict[str, Any]:
        """事业分析"""
        geju_analysis = self.analyze_geju()
        shishen_analysis = self.analyze_shishen()
        geju_career = self.rules.get("geju_career", {})
        
        geju_type = geju_analysis.get("geju_type", "")
        suitable_fields = []
        
        # 根据格局获取职业倾向
        if geju_type in geju_career:
            suitable = geju_career[geju_type].get("suitable", [])
            suitable_fields.extend(suitable)
        
        # 根据十神分布补充职业
        shishen_dist = shishen_analysis["shishen_distribution"]
        if shishen_dist.get("正官", 0) > 0:
            if "政府机关/公职" not in suitable_fields:
                suitable_fields.append("政府机关/公职")
        if shishen_dist.get("七杀", 0) > 0:
            if "军警/执法" not in suitable_fields:
                suitable_fields.append("军警/执法")
        if shishen_dist.get("正财", 0) > 0:
            if "金融/会计" not in suitable_fields:
                suitable_fields.append("金融/会计")
        if shishen_dist.get("食神", 0) > 0 or shishen_dist.get("伤官", 0) > 0:
            if "教师/培训" not in suitable_fields:
                suitable_fields.append("教师/培训")
        
        return {
            "geju_type": geju_type,
            "suitable_fields": suitable_fields,
            "career_advice": "适合稳定工作，发挥执行力优势"
        }
    
    def analyze_wealth(self) -> Dict[str, Any]:
        """财运分析"""
        shishen_analysis = self.analyze_shishen()
        shishen_dist = shishen_analysis["shishen_distribution"]
        
        wealth_level = "中等"
        if shishen_dist.get("正财", 0) > 0:
            wealth_level = "中等偏上"
        elif shishen_dist.get("偏财", 0) > 0:
            wealth_level = "较好"
        
        return {
            "wealth_level": wealth_level,
            "main_source": "正财(工资)" if shishen_dist.get("正财", 0) > 0 else "其他",
            "advice": "踏实工作，争取加薪"
        }
    
    def analyze_marriage(self) -> Dict[str, Any]:
        """婚姻分析"""
        shishen_analysis = self.analyze_shishen()
        shishen_dist = shishen_analysis["shishen_distribution"]
        
        marriage_level = "中等"
        if shishen_dist.get("正财", 0) > 0:
            marriage_level = "中等偏上"
        
        return {
            "marriage_level": marriage_level,
            "best_age": "28-32岁",
            "advice": "选择性格温和、包容心强的伴侣"
        }
    
    def analyze_health(self) -> Dict[str, Any]:
        """健康分析"""
        wuxing_analysis = self.analyze_wuxing()
        wuxing_missing = wuxing_analysis["wuxing_missing"]
        
        risk_parts = []
        if "水" in wuxing_missing:
            risk_parts.append("肾脏")
        if "木" in wuxing_missing:
            risk_parts.append("肝胆")
        
        return {
            "constitution": "中等",
            "risk_parts": risk_parts,
            "advice": "注意养生，定期体检"
        }
    
    def analyze_interpersonal(self) -> Dict[str, Any]:
        """人际分析"""
        # 加载生肖关系规则
        shengxiao_rules = self.rules.get("shengxiao", {})
        
        # 获取用户生肖
        lunar_info = self.calc.get_lunar_info()
        user_shengxiao = lunar_info.get("shengxiao", "")
        
        # 查找三合、六合、相冲、相害关系
        sanhe = shengxiao_rules.get("sanhe", {})
        liuhe = shengxiao_rules.get("liuhe", {})
        xiangchong = shengxiao_rules.get("xiangchong", {})
        xianghai = shengxiao_rules.get("xianghai", {})
        
        # 三合贵人
        sanhe_guiren = sanhe.get(user_shengxiao, [])
        
        # 六合贵人
        liuhe_guiren = liuhe.get(user_shengxiao, "")
        
        # 相冲生肖
        xiangchong_shengxiao = xiangchong.get(user_shengxiao, "")
        
        # 相害生肖
        xianghai_shengxiao = xianghai.get(user_shengxiao, "")
        
        # 神煞分析中的贵人
        shensha_analysis = self.analyze_shensha()
        jishen_details = shensha_analysis.get("jishen_details", [])
        
        # 提取贵人属相
        guiren_shengxiao = []
        for js in jishen_details:
            dizhi = js.get("dizhi", "")
            # 根据地支查找生肖(简化,实际需要完整映射)
            dizhi_to_shengxiao = {
                "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔",
                "辰": "龙", "巳": "蛇", "午": "马", "未": "羊",
                "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪"
            }
            if dizhi in dizhi_to_shengxiao:
                guiren_shengxiao.append(dizhi_to_shengxiao[dizhi])
        
        return {
            "user_shengxiao": user_shengxiao,
            "sanhe_guiren": sanhe_guiren,
            "liuhe_guiren": [liuhe_guiren] if liuhe_guiren else [],
            "xiangchong_shengxiao": [xiangchong_shengxiao] if xiangchong_shengxiao else [],
            "xianghai_shengxiao": [xianghai_shengxiao] if xianghai_shengxiao else [],
            "guiren_shengxiao": list(set(guiren_shengxiao)),
            "social_ability": "中等",
            "advice": "多与贵人交往，避开小人"
        }
    
    def analyze_dayun(self) -> Dict[str, Any]:
        """大运分析"""
        try:
            # 使用大运计算器计算大运
            dayun_result = self.dayun_calculator.calculate_dayun(
                birth_year=self.birth_year,
                birth_month=self.birth_month,
                birth_day=self.birth_day,
                birth_hour=self.birth_hour,
                birth_minute=self.birth_minute,
                gender=self.gender
            )
            
            # 分析每个大运的吉凶
            wuxing_analysis = self.analyze_wuxing()
            yongshen = wuxing_analysis.get("yongshen", [])
            jishen = wuxing_analysis.get("jishen", [])
            
            dayun_list = []
            for dayun in dayun_result["dayun_list"]:
                # 分析大运与用神忌神的关系
                evaluation = self._evaluate_dayun(dayun, yongshen, jishen)
                dayun_list.append({
                    **dayun,
                    "evaluation": evaluation
                })
            
            return {
                "qiyun_age": dayun_result["qiyun_age"],
                "qiyun_months": dayun_result["qiyun_months"],
                "qiyun_date": dayun_result["qiyun_date"],
                "shunni": dayun_result["shunni"],
                "dayun_list": dayun_list,
                "current_dayun": dayun_list[0] if dayun_list else None
            }
        except Exception as e:
            logger.error(f"大运分析失败: {e}")
            return {
                "dayun_list": [],
                "current_dayun": None,
                "error": str(e)
            }
    
    def _evaluate_dayun(self, dayun: Dict[str, Any], yongshen: List[str], jishen: List[str]) -> str:
        """评估大运吉凶"""
        # 简化评估逻辑
        gan = dayun.get("gan", "")
        zhi = dayun.get("zhi", "")
        
        gan_wx = self.calc.TIAN_GAN_WUXING.get(gan, "")
        zhi_wx = self.calc.DI_ZHI_WUXING.get(zhi, "")
        
        # 判断与用神忌神的关系
        if gan_wx in yongshen or zhi_wx in yongshen:
            return "吉"
        elif gan_wx in jishen or zhi_wx in jishen:
            return "凶"
        else:
            return "平"
    
    def analyze_shensha(self) -> Dict[str, Any]:
        """神煞分析"""
        jishen = []
        xiongsha = []
        jishen_details = []
        xiongsha_details = []
        
        # 获取神煞规则
        shensha_rules = self.rules.get("shensha", {})
        
        # 计算凶煞：羊刃（日干的帝旺位）
        # 羊刃：甲见卯、乙见寅、丙见午、丁见巳、戊见午、己见巳、庚见酉、辛见申、壬见子、癸见亥
        yangren_map = {
            "甲": "卯", "乙": "寅", "丙": "午", "丁": "巳",
            "戊": "午", "己": "巳", "庚": "酉", "辛": "申",
            "壬": "子", "癸": "亥"
        }
        ri_tiangan = self.bazi["ri_zhu"]["tiangan"]
        if ri_tiangan in yangren_map:
            yangren_dizhi = yangren_map[ri_tiangan]
            for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if zhu["dizhi"] == yangren_dizhi:
                    if "羊刃" not in xiongsha:
                        xiongsha.append("羊刃")
                    xiongsha_details.append({
                        "name": "羊刃",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "刚烈冲动，易有血光，需注意安全"
                    })
                    break
        
        # 计算凶煞：劫煞（年支的劫煞位）
        # 劫煞：寅午戌见亥、巳酉丑见寅、申子辰见巳、亥卯未见申
        jiesha_map = {
            "寅": "亥", "午": "亥", "戌": "亥",
            "巳": "寅", "酉": "寅", "丑": "寅",
            "申": "巳", "子": "巳", "辰": "巳",
            "亥": "申", "卯": "申", "未": "申"
        }
        nian_zhi = self.bazi["nian_zhu"]["dizhi"]
        if nian_zhi in jiesha_map:
            jiesha_dizhi = jiesha_map[nian_zhi]
            for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if zhu["dizhi"] == jiesha_dizhi:
                    if "劫煞" not in xiongsha:
                        xiongsha.append("劫煞")
                    xiongsha_details.append({
                        "name": "劫煞",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "破财损失，易有意外支出，需谨慎理财"
                    })
                    break
        
        # 计算凶煞：灾煞（年支的灾煞位）
        # 灾煞：寅午戌见子、巳酉丑见卯、申子辰见午、亥卯未见酉
        zaisha_map = {
            "寅": "子", "午": "子", "戌": "子",
            "巳": "卯", "酉": "卯", "丑": "卯",
            "申": "午", "子": "午", "辰": "午",
            "亥": "酉", "卯": "酉", "未": "酉"
        }
        if nian_zhi in zaisha_map:
            zaisha_dizhi = zaisha_map[nian_zhi]
            for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if zhu["dizhi"] == zaisha_dizhi:
                    if "灾煞" not in xiongsha:
                        xiongsha.append("灾煞")
                    xiongsha_details.append({
                        "name": "灾煞",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "易有疾病灾难，注意健康安全"
                    })
                    break
        
        # 计算凶煞：孤辰寡宿（年支的孤辰寡宿位）
        # 孤辰：寅卯辰见巳、巳午未见申、申酉戌见亥、亥子丑见寅
        # 寡宿：寅卯辰见丑、巳午未见辰、申酉戌见未、亥子丑见戌
        guchen_map = {
            "寅": "巳", "卯": "巳", "辰": "巳",
            "巳": "申", "午": "申", "未": "申",
            "申": "亥", "酉": "亥", "戌": "亥",
            "亥": "寅", "子": "寅", "丑": "寅"
        }
        guasu_map = {
            "寅": "丑", "卯": "丑", "辰": "丑",
            "巳": "辰", "午": "辰", "未": "辰",
            "申": "未", "酉": "未", "戌": "未",
            "亥": "戌", "子": "戌", "丑": "戌"
        }
        if nian_zhi in guchen_map:
            guchen_dizhi = guchen_map[nian_zhi]
            for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if zhu["dizhi"] == guchen_dizhi:
                    if "孤辰" not in xiongsha:
                        xiongsha.append("孤辰")
                    xiongsha_details.append({
                        "name": "孤辰",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "性格孤僻，六亲缘薄，容易孤独"
                    })
                    break
        if nian_zhi in guasu_map:
            guasu_dizhi = guasu_map[nian_zhi]
            for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if zhu["dizhi"] == guasu_dizhi:
                    if "寡宿" not in xiongsha:
                        xiongsha.append("寡宿")
                    xiongsha_details.append({
                        "name": "寡宿",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "性格孤僻，六亲缘薄，容易孤独"
                    })
                    break
        
        # 天乙贵人
        ri_tiangan = self.bazi["ri_zhu"]["tiangan"]
        tianyi_guiren = shensha_rules.get("tianyi_guiren", {})
        if ri_tiangan in tianyi_guiren:
            dizhi_list = tianyi_guiren[ri_tiangan]
            for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if zhu["dizhi"] in dizhi_list:
                    jishen.append("天乙贵人")
                    jishen_details.append({
                        "name": "天乙贵人",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "逢凶化吉，遇难呈祥"
                    })
                    break
        
        # 文昌贵人
        wenchang_guiren = shensha_rules.get("wenchang_guiren", {})
        if ri_tiangan in wenchang_guiren:
            dizhi = wenchang_guiren[ri_tiangan]
            for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if zhu["dizhi"] == dizhi:
                    jishen.append("文昌贵人")
                    jishen_details.append({
                        "name": "文昌贵人",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "聪明智慧，利于学业"
                    })
                    break
        
        # 红鸾天喜 - 以年支查月、日、时柱（不包括年柱自身）
        nian_zhi = self.bazi["nian_zhu"]["dizhi"]
        hongluan_tianxi = shensha_rules.get("hongluan_tianxi", {})
        if nian_zhi in hongluan_tianxi:
            hongluan = hongluan_tianxi[nian_zhi].get("hongluan", "")
            tianxi = hongluan_tianxi[nian_zhi].get("tianxi", "")
            # 只检查月、日、时柱（不包括年柱）
            for zhu_name in ["yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if hongluan and zhu["dizhi"] == hongluan:
                    jishen.append("红鸾")
                    jishen_details.append({
                        "name": "红鸾",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "婚姻喜庆，利于结婚"
                    })
                if tianxi and zhu["dizhi"] == tianxi:
                    jishen.append("天喜")
                    jishen_details.append({
                        "name": "天喜",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "喜庆吉祥，有喜事"
                    })
        
        # 桃花(咸池) - 需要同时检查年支和日支
        taohua = shensha_rules.get("taohua", {})
        ri_zhi = self.bazi["ri_zhu"]["dizhi"]
        
        # 以年支查桃花
        if nian_zhi in taohua:
            dizhi_list = taohua[nian_zhi]
            for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if zhu["dizhi"] in dizhi_list:
                    jishen.append("桃花")
                    jishen_details.append({
                        "name": "桃花",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "异性缘，需谨慎"
                    })
                    break
        
        # 以日支查桃花（如果年支没有找到）
        if ri_zhi in taohua and "桃花" not in jishen:
            dizhi_list = taohua[ri_zhi]
            for zhu_name in ["nian_zhu", "yue_zhu", "ri_zhu", "shi_zhu"]:
                zhu = self.bazi[zhu_name]
                if zhu["dizhi"] in dizhi_list:
                    jishen.append("桃花")
                    jishen_details.append({
                        "name": "桃花",
                        "position": zhu_name,
                        "dizhi": zhu["dizhi"],
                        "description": "异性缘，需谨慎"
                    })
                    break
        
        return {
            "jishen": list(set(jishen)),
            "xiongsha": xiongsha,
            "jishen_details": jishen_details,
            "xiongsha_details": xiongsha_details
        }
    
    def analyze_liunian(self) -> Dict[str, Any]:
        """流年分析"""
        try:
            # 获取用神忌神
            wuxing_analysis = self.analyze_wuxing()
            yongshen = wuxing_analysis.get("yongshen", [])
            jishen = wuxing_analysis.get("jishen", [])
            
            # 获取当前年份和未来几年的流年分析
            current_year = self.birth_year
            liunian_list = []
            
            # 分析未来10年的流年
            for year in range(current_year, current_year + 10):
                liunian_result = self.liunian_analyzer.analyze_liunian(
                    year=year,
                    bazi=self.bazi,
                    yongshen_wuxing=yongshen,
                    jishen_wuxing=jishen
                )
                liunian_list.append(liunian_result)
            
            return {
                "liunian_list": liunian_list,
                "current_liunian": liunian_list[0] if liunian_list else None,
                "next_liunian": liunian_list[1] if len(liunian_list) > 1 else None
            }
        except Exception as e:
            logger.error(f"流年分析失败: {e}")
            return {
                "liunian_list": [],
                "current_liunian": None,
                "next_liunian": None,
                "error": str(e)
            }

