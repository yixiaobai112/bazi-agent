"""
流年分析模块
负责流年的计算和分析
"""

from typing import Dict, Any, List, Optional
from lunar_python import Solar
from loguru import logger

from .exceptions import CalculationError


class LiunianAnalyzer:
    """流年分析器"""
    
    def __init__(self):
        # 五行生克关系
        self.wuxing_shengke = {
            '生': {
                '木': '火', '火': '土', '土': '金', 
                '金': '水', '水': '木'
            },
            '克': {
                '木': '土', '火': '金', '土': '水',
                '金': '木', '水': '火'
            }
        }
        
        # 天干五行
        self.tiangan_wuxing = {
            '甲': '木', '乙': '木',
            '丙': '火', '丁': '火',
            '戊': '土', '己': '土',
            '庚': '金', '辛': '金',
            '壬': '水', '癸': '水'
        }
        
        # 地支五行
        self.dizhi_wuxing = {
            '子': '水', '亥': '水',
            '寅': '木', '卯': '木',
            '巳': '火', '午': '火',
            '申': '金', '酉': '金',
            '辰': '土', '戌': '土', '丑': '土', '未': '土'
        }
        
        # 六冲
        self.liuchong = {
            '子': '午', '午': '子',
            '丑': '未', '未': '丑',
            '寅': '申', '申': '寅',
            '卯': '酉', '酉': '卯',
            '辰': '戌', '戌': '辰',
            '巳': '亥', '亥': '巳'
        }
    
    def get_liunian_info(self, year: int) -> Dict[str, Any]:
        """获取流年信息"""
        try:
            solar = Solar.fromYmd(year, 1, 1)
            lunar = solar.getLunar()
            
            year_gan = lunar.getYearGan()
            year_zhi = lunar.getYearZhi()
            year_ganzhi = lunar.getYearInGanZhi()
            
            return {
                'year': year,
                'ganzhi': year_ganzhi,
                'gan': year_gan,
                'zhi': year_zhi,
                'gan_wuxing': self.tiangan_wuxing.get(year_gan, ''),
                'zhi_wuxing': self.dizhi_wuxing.get(year_zhi, '')
            }
        except Exception as e:
            logger.error(f"获取流年信息失败: {e}")
            raise CalculationError(f"获取流年信息失败: {e}")
    
    def analyze_liunian_yongshen(self, liunian_wuxing: str, yongshen_wuxing: str) -> Dict[str, Any]:
        """分析流年与用神关系"""
        # 判断生克关系
        if self.wuxing_shengke['生'].get(liunian_wuxing) == yongshen_wuxing:
            return {
                'relation': '流年生用神',
                'jixi': '大吉',
                'degree': 5,
                'description': '用神得力,运势极佳,贵人相助,事业顺利',
                'tags': ['运势极佳', '贵人相助', '事业顺利']
            }
        elif self.wuxing_shengke['克'].get(liunian_wuxing) == yongshen_wuxing:
            return {
                'relation': '流年克用神',
                'jixi': '大凶',
                'degree': 1,
                'description': '用神受制,运势低迷,事业受阻,易有灾祸',
                'tags': ['运势差', '多阻碍', '诸事不顺']
            }
        elif liunian_wuxing == yongshen_wuxing:
            return {
                'relation': '流年助用神',
                'jixi': '吉',
                'degree': 4,
                'description': '用神增强,运势上升,得朋友帮助',
                'tags': ['运势良好', '朋友相助']
            }
        elif self.wuxing_shengke['生'].get(yongshen_wuxing) == liunian_wuxing:
            return {
                'relation': '流年泄用神',
                'jixi': '小凶',
                'degree': 2,
                'description': '用神力量被泄,消耗较多,付出多收获少',
                'tags': ['消耗大', '付出多']
            }
        else:
            return {
                'relation': '无特殊关系',
                'jixi': '平',
                'degree': 3,
                'description': '运势平稳',
                'tags': ['运势平稳']
            }
    
    def check_chong(self, bazi_sizhu_zhi: List[str], liunian_zhi: str) -> List[Dict[str, Any]]:
        """检查流年是否冲命局"""
        chong_list = []
        positions = ['年柱', '月柱', '日柱', '时柱']
        
        logger.debug(f"检查冲关系: 命局四柱地支={bazi_sizhu_zhi}, 流年地支={liunian_zhi}")
        
        for i, zhi in enumerate(bazi_sizhu_zhi):
            chong_zhi = self.liuchong.get(zhi)
            if chong_zhi == liunian_zhi:
                importance = '最高' if i == 2 else ('高' if i == 1 else '中')
                logger.debug(f"发现冲: {positions[i]}({zhi}) 被流年({liunian_zhi})冲")
                chong_list.append({
                    'position': positions[i],
                    'chong_zhi': zhi,
                    'importance': importance,
                    'description': self._get_chong_description(positions[i])
                })
            else:
                logger.debug(f"无冲: {positions[i]}({zhi}) -> 冲支({chong_zhi}) != 流年({liunian_zhi})")
        
        if not chong_list:
            logger.debug(f"流年({liunian_zhi})与命局四柱无冲关系")
        
        return chong_list
    
    def _get_chong_description(self, position: str) -> str:
        """获取冲的描述"""
        descriptions = {
            '年柱': '父母、祖辈有变动,可能搬迁或家庭变化',
            '月柱': '工作变动、跳槽、升职降职、兄弟姐妹事',
            '日柱': '婚姻变动、离婚、结婚、配偶健康、搬家',
            '时柱': '子女事、生育、子女离家、晚年变动'
        }
        return descriptions.get(position, '')
    
    def analyze_liunian(self, year: int, bazi: Dict[str, Any], 
                       yongshen_wuxing: List[str], jishen_wuxing: List[str]) -> Dict[str, Any]:
        """
        综合分析流年
        
        参数:
        - year: 流年年份
        - bazi: 八字四柱 {'nian_zhu': {'dizhi': ''}, ...}
        - yongshen_wuxing: 用神五行列表
        - jishen_wuxing: 忌神五行列表
        """
        try:
            # 1. 获取流年信息
            liunian = self.get_liunian_info(year)
            
            # 2. 分析与用神关系(取第一个用神)
            yongshen_wx = yongshen_wuxing[0] if yongshen_wuxing else ''
            yongshen_result = self.analyze_liunian_yongshen(
                liunian['gan_wuxing'], 
                yongshen_wx
            ) if yongshen_wx else {
                'relation': '无特殊关系',
                'jixi': '平',
                'degree': 3,
                'description': '运势平稳',
                'tags': ['运势平稳']
            }
            
            # 3. 分析与忌神关系(取第一个忌神)
            jishen_wx = jishen_wuxing[0] if jishen_wuxing else ''
            jishen_relation = self.analyze_liunian_yongshen(
                liunian['gan_wuxing'],
                jishen_wx
            ) if jishen_wx else {
                'relation': '无特殊关系',
                'jixi': '平',
                'degree': 3,
                'description': '运势平稳',
                'tags': ['运势平稳']
            }
            
            # 忌神关系要反过来看
            if jishen_relation['jixi'] == '大吉':
                jishen_result = {
                    'relation': '流年生忌神',
                    'jixi': '凶',
                    'degree': 2,
                    'description': '忌神得力,运势差,易有灾祸',
                    'tags': ['运势差', '压力大']
                }
            elif jishen_relation['jixi'] == '大凶':
                jishen_result = {
                    'relation': '流年克忌神',
                    'jixi': '吉',
                    'degree': 4,
                    'description': '忌神受制,运势转好,困扰减少',
                    'tags': ['运势好转', '压力减轻']
                }
            else:
                jishen_result = jishen_relation
            
            # 4. 检查冲克
            bazi_sizhu_zhi = [
                bazi.get('nian_zhu', {}).get('dizhi', ''),
                bazi.get('yue_zhu', {}).get('dizhi', ''),
                bazi.get('ri_zhu', {}).get('dizhi', ''),
                bazi.get('shi_zhu', {}).get('dizhi', '')
            ]
            chong_list = self.check_chong(bazi_sizhu_zhi, liunian['zhi'])
            
            # 如果没有冲关系，返回一个明确的标识对象（保持数组结构）
            if not chong_list:
                chong_list = [{
                    'has_chong': False,
                    'status': 'no_chong',
                    'message': '流年与命局四柱无冲关系',
                    'liunian_zhi': liunian['zhi'],
                    'bazi_sizhu_zhi': bazi_sizhu_zhi
                }]
            
            # 5. 综合判断
            total_score = (yongshen_result['degree'] * 0.6 + 
                          jishen_result['degree'] * 0.4)
            
            if total_score >= 4:
                overall = '吉'
            elif total_score >= 3:
                overall = '平'
            else:
                overall = '凶'
            
            return {
                'liunian': liunian,
                'yongshen_analysis': yongshen_result,
                'jishen_analysis': jishen_result,
                'chong_analysis': chong_list,
                'total_score': round(total_score, 1),
                'overall': overall
            }
        except Exception as e:
            logger.error(f"流年分析失败: {e}")
            raise CalculationError(f"流年分析失败: {e}")

