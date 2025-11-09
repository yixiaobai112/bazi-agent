"""
历法计算模块
负责八字排盘、农历转换、节气计算等
"""

from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from lunar_python import Solar, Lunar
from loguru import logger

from .exceptions import InvalidDateError, CalculationError


class CalendarCalc:
    """历法计算器"""
    
    # 天干
    TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    
    # 地支
    DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    # 天干五行
    TIAN_GAN_WUXING = {
        "甲": "木", "乙": "木",
        "丙": "火", "丁": "火",
        "戊": "土", "己": "土",
        "庚": "金", "辛": "金",
        "壬": "水", "癸": "水"
    }
    
    # 天干阴阳
    TIAN_GAN_YINYANG = {
        "甲": "阳", "乙": "阴",
        "丙": "阳", "丁": "阴",
        "戊": "阳", "己": "阴",
        "庚": "阳", "辛": "阴",
        "壬": "阳", "癸": "阴"
    }
    
    # 地支五行
    DI_ZHI_WUXING = {
        "子": "水", "丑": "土", "寅": "木", "卯": "木",
        "辰": "土", "巳": "火", "午": "火", "未": "土",
        "申": "金", "酉": "金", "戌": "土", "亥": "水"
    }
    
    # 地支藏干
    DI_ZHI_CANG_GAN = {
        "子": ["癸"],
        "丑": ["己", "癸", "辛"],
        "寅": ["甲", "丙", "戊"],
        "卯": ["乙"],
        "辰": ["戊", "乙", "癸"],
        "巳": ["丙", "戊", "庚"],
        "午": ["丁", "己"],
        "未": ["己", "丁", "乙"],
        "申": ["庚", "壬", "戊"],
        "酉": ["辛"],
        "戌": ["戊", "辛", "丁"],
        "亥": ["壬", "甲"]
    }
    
    # 生肖
    SHENG_XIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
    
    # 纳音五行表（简化版，实际需要根据年柱计算）
    NA_YIN = {
        "甲子": "海中金", "乙丑": "海中金",
        "丙寅": "炉中火", "丁卯": "炉中火",
        # ... 完整纳音表需要根据六十甲子循环计算
    }
    
    # 节气名称
    JIE_QI = [
        "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
        "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
        "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
        "立冬", "小雪", "大雪", "冬至", "小寒", "大寒"
    ]
    
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int = 0,
                 longitude: Optional[float] = None, latitude: Optional[float] = None,
                 province: Optional[str] = None, city: Optional[str] = None,
                 use_true_solar_time: bool = False):
        """
        初始化历法计算器
        
        Args:
            year: 出生年份
            month: 出生月份
            day: 出生日期
            hour: 出生小时
            minute: 出生分钟
            longitude: 经度（用于真太阳时）
            latitude: 纬度（用于真太阳时）
            province: 省份（用于查找经纬度）
            city: 城市（用于查找经纬度）
            use_true_solar_time: 是否使用真太阳时
        """
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.province = province
        self.city = city
        
        # 如果没有提供经纬度，尝试根据省市查找
        if longitude is None or latitude is None:
            if province or city:
                coords = self._get_coordinates_by_location(province, city)
                if coords:
                    longitude = coords[0]
                    latitude = coords[1]
                    logger.info(f"根据省市信息查找经纬度: {province}{city} -> ({longitude}, {latitude})")
        
        self.longitude = longitude or 120.0  # 默认北京时间
        self.latitude = latitude or 39.9
        self.use_true_solar_time = use_true_solar_time
        
        # 真太阳时校正
        if use_true_solar_time:
            self._correct_solar_time()
        
        # 验证日期
        try:
            # Solar类需要year, month, day, hour, minute, second参数
            self.solar = Solar(year, month, day, hour, minute, 0)
        except Exception as e:
            raise InvalidDateError(f"日期不合法: {e}")
        
        # 转换为农历
        self.lunar = self.solar.getLunar()
    
    def _get_coordinates_by_location(self, province: Optional[str], city: Optional[str]) -> Optional[tuple]:
        """根据省市名称查找经纬度（简化版，使用常见城市数据）"""
        # 常见城市经纬度数据库（简化版）
        city_coords = {
            "北京": (116.4074, 39.9042),
            "上海": (121.4737, 31.2304),
            "广州": (113.2644, 23.1291),
            "深圳": (114.0579, 22.5431),
            "杭州": (120.1551, 30.2741),
            "成都": (104.0668, 30.5728),
            "重庆": (106.5516, 29.5630),
            "西安": (108.9398, 34.3416),
            "南京": (118.7969, 32.0603),
            "昆明": (102.7123, 25.0406),  # 昆明市
            "昆明市": (102.7123, 25.0406),
            "云南省": (102.7123, 25.0406),  # 默认使用昆明市坐标
        }
        
        # 优先查找城市
        if city:
            for key, coords in city_coords.items():
                if city in key or key in city:
                    return coords
        
        # 其次查找省份
        if province:
            for key, coords in city_coords.items():
                if province in key or key in province:
                    return coords
        
        return None
    
    def _correct_solar_time(self) -> None:
        """真太阳时校正"""
        # 简化的真太阳时校正公式
        # 实际应该考虑时差、均时差等
        time_diff = (self.longitude - 120.0) * 4  # 每度4分钟
        total_minutes = self.hour * 60 + self.minute + time_diff
        
        if total_minutes < 0:
            total_minutes += 24 * 60
        elif total_minutes >= 24 * 60:
            total_minutes -= 24 * 60
        
        self.hour = total_minutes // 60
        self.minute = total_minutes % 60
        logger.debug(f"真太阳时校正: {self.hour}:{self.minute}")
    
    def get_bazi(self) -> Dict[str, Any]:
        """
        计算八字
        
        Returns:
            八字信息字典
        """
        # 计算年柱
        nian_zhu = self._get_nian_zhu()
        
        # 计算月柱
        yue_zhu = self._get_yue_zhu()
        
        # 计算日柱
        ri_zhu = self._get_ri_zhu()
        
        # 计算时柱
        shi_zhu = self._get_shi_zhu(ri_zhu["tiangan"])
        
        return {
            "nian_zhu": nian_zhu,
            "yue_zhu": yue_zhu,
            "ri_zhu": ri_zhu,
            "shi_zhu": shi_zhu,
            "sizhu": {
                "nian": f"{nian_zhu['tiangan']}{nian_zhu['dizhi']}",
                "yue": f"{yue_zhu['tiangan']}{yue_zhu['dizhi']}",
                "ri": f"{ri_zhu['tiangan']}{ri_zhu['dizhi']}",
                "shi": f"{shi_zhu['tiangan']}{shi_zhu['dizhi']}"
            }
        }
    
    def _get_nian_zhu(self) -> Dict[str, str]:
        """计算年柱"""
        # 根据立春确定年柱
        # 简化处理：以公历年份计算
        # 实际应该根据立春节气判断
        
        # 1900年为庚子年，以此为基准计算
        base_year = 1900
        base_tiangan = 6  # 庚
        base_dizhi = 0  # 子
        
        year_diff = self.year - base_year
        tiangan_index = (base_tiangan + year_diff) % 10
        dizhi_index = (base_dizhi + year_diff) % 12
        
        tiangan = self.TIAN_GAN[tiangan_index]
        dizhi = self.DI_ZHI[dizhi_index]
        
        return {
            "tiangan": tiangan,
            "dizhi": dizhi,
            "wuxing_tiangan": self.TIAN_GAN_WUXING[tiangan],
            "wuxing_dizhi": self.DI_ZHI_WUXING[dizhi],
            "yinyang_tiangan": self.TIAN_GAN_YINYANG[tiangan],
            "yinyang_dizhi": "阳" if dizhi_index % 2 == 0 else "阴",
            "cang_gan": self.DI_ZHI_CANG_GAN[dizhi]
        }
    
    def _get_yue_zhu(self) -> Dict[str, str]:
        """计算月柱"""
        # 根据节气确定月令
        # 简化处理：根据月份大致判断
        # 实际应该精确计算节气时刻
        
        # 月令地支（根据节气）
        yue_dizhi_map = {
            1: "寅", 2: "卯", 3: "辰", 4: "巳",
            5: "午", 6: "未", 7: "申", 8: "酉",
            9: "戌", 10: "亥", 11: "子", 12: "丑"
        }
        
        dizhi = yue_dizhi_map.get(self.month, "寅")
        dizhi_index = self.DI_ZHI.index(dizhi)
        
        # 年干推月干（五虎遁法）
        nian_zhu = self._get_nian_zhu()
        nian_tiangan = nian_zhu["tiangan"]
        nian_tiangan_index = self.TIAN_GAN.index(nian_tiangan)
        
        # 甲己之年丙作首，乙庚之年戊为头...
        yue_tiangan_map = {
            0: 2, 1: 4, 2: 6, 3: 8, 4: 0,  # 甲己丙，乙庚戊，丙辛庚，丁壬壬，戊癸甲
            5: 2, 6: 4, 7: 6, 8: 8, 9: 0
        }
        base_tiangan = yue_tiangan_map[nian_tiangan_index % 5]
        tiangan_index = (base_tiangan + dizhi_index) % 10
        tiangan = self.TIAN_GAN[tiangan_index]
        
        return {
            "tiangan": tiangan,
            "dizhi": dizhi,
            "wuxing_tiangan": self.TIAN_GAN_WUXING[tiangan],
            "wuxing_dizhi": self.DI_ZHI_WUXING[dizhi],
            "yinyang_tiangan": self.TIAN_GAN_YINYANG[tiangan],
            "yinyang_dizhi": "阳" if dizhi_index % 2 == 0 else "阴",
            "cang_gan": self.DI_ZHI_CANG_GAN[dizhi]
        }
    
    def _get_ri_zhu(self) -> Dict[str, str]:
        """计算日柱"""
        # 使用万年历算法计算日柱
        # 1900年1月1日为甲子日，以此为基准
        
        base_date = datetime(1900, 1, 1)
        target_date = datetime(self.year, self.month, self.day)
        days_diff = (target_date - base_date).days
        
        # 甲子日为基准（甲=0, 子=0）
        tiangan_index = days_diff % 10
        dizhi_index = days_diff % 12
        
        tiangan = self.TIAN_GAN[tiangan_index]
        dizhi = self.DI_ZHI[dizhi_index]
        
        return {
            "tiangan": tiangan,
            "dizhi": dizhi,
            "wuxing_tiangan": self.TIAN_GAN_WUXING[tiangan],
            "wuxing_dizhi": self.DI_ZHI_WUXING[dizhi],
            "yinyang_tiangan": self.TIAN_GAN_YINYANG[tiangan],
            "yinyang_dizhi": "阳" if dizhi_index % 2 == 0 else "阴",
            "cang_gan": self.DI_ZHI_CANG_GAN[dizhi]
        }
    
    def _get_shi_zhu(self, ri_tiangan: str) -> Dict[str, str]:
        """计算时柱（五鼠遁法）"""
        # 根据日干和时辰推算时干
        
        # 时辰地支
        shi_dizhi_map = {
            23: "子", 0: "子", 1: "丑", 2: "寅", 3: "卯",
            4: "辰", 5: "巳", 6: "午", 7: "未", 8: "申",
            9: "酉", 10: "戌", 11: "亥", 12: "子", 13: "丑",
            14: "寅", 15: "卯", 16: "辰", 17: "巳", 18: "午",
            19: "未", 20: "申", 21: "酉", 22: "戌"
        }
        
        dizhi = shi_dizhi_map.get(self.hour, "子")
        dizhi_index = self.DI_ZHI.index(dizhi)
        
        # 五鼠遁法：甲己还生甲，乙庚丙作初...
        ri_tiangan_index = self.TIAN_GAN.index(ri_tiangan)
        shi_tiangan_map = {
            0: 0, 1: 2, 2: 4, 3: 6, 4: 8,  # 甲己甲，乙庚丙，丙辛戊，丁壬庚，戊癸壬
            5: 0, 6: 2, 7: 4, 8: 6, 9: 8
        }
        base_tiangan = shi_tiangan_map[ri_tiangan_index % 5]
        tiangan_index = (base_tiangan + dizhi_index) % 10
        tiangan = self.TIAN_GAN[tiangan_index]
        
        return {
            "tiangan": tiangan,
            "dizhi": dizhi,
            "wuxing_tiangan": self.TIAN_GAN_WUXING[tiangan],
            "wuxing_dizhi": self.DI_ZHI_WUXING[dizhi],
            "yinyang_tiangan": self.TIAN_GAN_YINYANG[tiangan],
            "yinyang_dizhi": "阳" if dizhi_index % 2 == 0 else "阴",
            "cang_gan": self.DI_ZHI_CANG_GAN[dizhi]
        }
    
    def get_lunar_info(self) -> Dict[str, Any]:
        """获取农历信息"""
        # 获取闰月信息（尝试多种方法）
        is_leap_month = False
        try:
            # 尝试不同的方法名
            if hasattr(self.lunar, 'isLeap'):
                is_leap_month = self.lunar.isLeap()
            elif hasattr(self.lunar, 'isLeapMonth'):
                is_leap_month = self.lunar.isLeapMonth()
            elif hasattr(self.lunar, 'getLeapMonth'):
                # 如果月份大于12，可能是闰月
                month = self.lunar.getMonth()
                is_leap_month = month > 12
            else:
                # 默认值
                is_leap_month = False
        except Exception:
            is_leap_month = False
        
        return {
            "lunar_year": self.lunar.getYear(),
            "lunar_month": self.lunar.getMonth(),
            "lunar_day": self.lunar.getDay(),
            "is_leap_month": is_leap_month,
            "shengxiao": self.SHENG_XIAO[(self.lunar.getYear() - 1900) % 12],
            "constellation": self._get_constellation()
        }
    
    def _get_constellation(self) -> str:
        """获取星座"""
        constellations = [
            "摩羯座", "水瓶座", "双鱼座", "白羊座", "金牛座", "双子座",
            "巨蟹座", "狮子座", "处女座", "天秤座", "天蝎座", "射手座"
        ]
        month = self.month
        day = self.day
        
        if (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return constellations[0]
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return constellations[1]
        elif (month == 2 and day >= 19) or (month == 3 and day <= 20):
            return constellations[2]
        elif (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return constellations[3]
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return constellations[4]
        elif (month == 5 and day >= 21) or (month == 6 and day <= 21):
            return constellations[5]
        elif (month == 6 and day >= 22) or (month == 7 and day <= 22):
            return constellations[6]
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return constellations[7]
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return constellations[8]
        elif (month == 9 and day >= 23) or (month == 10 and day <= 23):
            return constellations[9]
        elif (month == 10 and day >= 24) or (month == 11 and day <= 22):
            return constellations[10]
        else:
            return constellations[11]
    
    def get_season_info(self) -> Dict[str, str]:
        """获取季节信息"""
        month = self.month
        if month in [3, 4, 5]:
            season = "春季"
        elif month in [6, 7, 8]:
            season = "夏季"
        elif month in [9, 10, 11]:
            season = "秋季"
        else:
            season = "冬季"
        
        return {
            "birth_season": season,
            "birth_jieqi": self._get_jieqi(),
            "month_order": self._get_yue_zhu()["dizhi"] + self.DI_ZHI_WUXING[self._get_yue_zhu()["dizhi"]]
        }
    
    def _get_jieqi(self) -> str:
        """获取节气信息（简化版）"""
        # 实际应该精确计算节气时刻
        jieqi_map = {
            1: "小寒后", 2: "立春后", 3: "惊蛰后", 4: "春分后",
            5: "立夏后", 6: "芒种后", 7: "小暑后", 8: "立秋后",
            9: "白露后", 10: "寒露后", 11: "立冬后", 12: "大雪后"
        }
        return jieqi_map.get(self.month, "立春后")

