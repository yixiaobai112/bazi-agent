"""
大运计算模块
负责大运的计算和分析
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from lunar_python import Solar
from loguru import logger

from .exceptions import CalculationError


class DayunCalculator:
    """大运计算器"""
    
    def __init__(self):
        # 天干
        self.tiangan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        # 地支
        self.dizhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        # 阳年天干
        self.yang_gan = ['甲', '丙', '戊', '庚', '壬']
        # 十二节气(不含气)
        self.jieqi_names = [
            '立春', '惊蛰', '清明', '立夏', '芒种', '小暑',
            '立秋', '白露', '寒露', '立冬', '大雪', '小寒'
        ]
    
    def calculate_dayun(self, birth_year: int, birth_month: int, birth_day: int,
                        birth_hour: int, birth_minute: int, gender: str) -> Dict[str, Any]:
        """
        计算大运
        
        参数:
        - birth_year: 出生年(公历)
        - birth_month: 出生月(公历)
        - birth_day: 出生日(公历)
        - birth_hour: 出生时(0-23)
        - birth_minute: 出生分(0-59)
        - gender: 性别 ('男' or '女')
        
        返回:
        大运计算结果
        """
        try:
            # 1. 获取八字
            solar = Solar.fromYmdHms(birth_year, birth_month, birth_day,
                                     birth_hour, birth_minute, 0)
            lunar = solar.getLunar()
            bazi = lunar.getEightChar()
            
            # 获取年柱、月柱
            year_gan = bazi.getYearGan()  # 年干
            year_zhi = bazi.getYearZhi()  # 年支
            month_gan = bazi.getMonthGan()  # 月干
            month_zhi = bazi.getMonthZhi()  # 月支
            
            # 2. 判断顺排还是逆排
            is_yang_year = year_gan in self.yang_gan
            is_male = (gender == '男')
            
            # 阳男阴女顺排,阴男阳女逆排
            is_shun = (is_yang_year and is_male) or (not is_yang_year and not is_male)
            shunni = '顺排' if is_shun else '逆排'
            
            # 3. 获取节气表
            jieqi_table = lunar.getJieQiTable()
            
            # 4. 找到相邻的节气
            birth_datetime = datetime(birth_year, birth_month, birth_day,
                                     birth_hour, birth_minute)
            
            if is_shun:
                # 顺排: 找下一个节
                next_jie = self._find_next_jie(birth_datetime, jieqi_table)
            else:
                # 逆排: 找上一个节
                next_jie = self._find_prev_jie(birth_datetime, jieqi_table)
            
            # 5. 计算天数差
            if next_jie:
                jie_datetime = next_jie['datetime']
                days_diff = abs((jie_datetime - birth_datetime).total_seconds() / 86400)
                
                # 超过12小时算1天
                days = int(days_diff)
                hours = (days_diff - days) * 24
                if hours >= 12:
                    days += 1
                
                # 6. 换算起运年龄
                qiyun_years = days // 3  # 3天为1岁
                remain_days = days % 3
                qiyun_months = remain_days * 4  # 1天为4个月
                
                # 起运日期
                qiyun_date = birth_datetime + timedelta(days=days)
                qiyun_age = qiyun_years
            else:
                # 找不到节气,默认1岁起运
                qiyun_years = 1
                qiyun_months = 0
                qiyun_date = birth_datetime + timedelta(days=365)
                qiyun_age = 1
            
            # 7. 排大运
            dayun_list = self._arrange_dayun(
                month_gan, month_zhi, is_shun,
                qiyun_age, birth_year
            )
            
            return {
                'year_ganzhi': year_gan + year_zhi,
                'month_ganzhi': month_gan + month_zhi,
                'qiyun_age': qiyun_age,
                'qiyun_months': qiyun_months,
                'qiyun_date': qiyun_date.strftime('%Y-%m-%d'),
                'shunni': shunni,
                'dayun_list': dayun_list
            }
            
        except Exception as e:
            logger.error(f"大运计算失败: {e}")
            raise CalculationError(f"大运计算失败: {e}")
    
    def _find_next_jie(self, birth_datetime: datetime, jieqi_table: Dict) -> Optional[Dict]:
        """找到下一个节气(顺排用)"""
        result = None
        min_diff = float('inf')
        
        for jieqi_name in self.jieqi_names:
            if jieqi_name in jieqi_table:
                jie_solar = jieqi_table[jieqi_name]
                jie_datetime = datetime(
                    jie_solar.getYear(),
                    jie_solar.getMonth(),
                    jie_solar.getDay(),
                    jie_solar.getHour(),
                    jie_solar.getMinute(),
                    jie_solar.getSecond()
                )
                
                # 找到生日之后最近的节
                if jie_datetime > birth_datetime:
                    diff = (jie_datetime - birth_datetime).total_seconds()
                    if diff < min_diff:
                        min_diff = diff
                        result = {
                            'name': jieqi_name,
                            'datetime': jie_datetime
                        }
        
        return result
    
    def _find_prev_jie(self, birth_datetime: datetime, jieqi_table: Dict) -> Optional[Dict]:
        """找到上一个节气(逆排用)"""
        result = None
        min_diff = float('inf')
        
        for jieqi_name in self.jieqi_names:
            if jieqi_name in jieqi_table:
                jie_solar = jieqi_table[jieqi_name]
                jie_datetime = datetime(
                    jie_solar.getYear(),
                    jie_solar.getMonth(),
                    jie_solar.getDay(),
                    jie_solar.getHour(),
                    jie_solar.getMinute(),
                    jie_solar.getSecond()
                )
                
                # 找到生日之前最近的节
                if jie_datetime < birth_datetime:
                    diff = (birth_datetime - jie_datetime).total_seconds()
                    if diff < min_diff:
                        min_diff = diff
                        result = {
                            'name': jieqi_name,
                            'datetime': jie_datetime
                        }
        
        return result
    
    def _arrange_dayun(self, month_gan: str, month_zhi: str, is_shun: bool,
                       qiyun_age: int, birth_year: int) -> List[Dict[str, Any]]:
        """排大运"""
        dayun_list = []
        
        # 获取月柱天干地支的索引
        gan_index = self.tiangan.index(month_gan)
        zhi_index = self.dizhi.index(month_zhi)
        
        # 排10步大运(100年)
        for i in range(10):
            if is_shun:
                # 顺排
                new_gan_index = (gan_index + i + 1) % 10
                new_zhi_index = (zhi_index + i + 1) % 12
            else:
                # 逆排
                new_gan_index = (gan_index - i - 1) % 10
                new_zhi_index = (zhi_index - i - 1) % 12
            
            ganzhi = self.tiangan[new_gan_index] + self.dizhi[new_zhi_index]
            start_age = qiyun_age + i * 10
            end_age = start_age + 9
            start_year = birth_year + start_age
            end_year = birth_year + end_age
            
            dayun_list.append({
                'step': i + 1,
                'ganzhi': ganzhi,
                'gan': self.tiangan[new_gan_index],
                'zhi': self.dizhi[new_zhi_index],
                'start_age': start_age,
                'end_age': end_age,
                'start_year': start_year,
                'end_year': end_year,
                'age_range': f'{start_age}-{end_age}岁'
            })
        
        return dayun_list

