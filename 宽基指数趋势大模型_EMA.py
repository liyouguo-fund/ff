"""
宽基指数趋势大模型 - EMA版本 - 逸飞ETF量化

指标计算（使用EMA指数移动平均）：
- 趋势线: (最高价 + 最低价) / 2 的20日指数移动平均(EMA)
- 偏离率: (现价 - 趋势线) / 趋势线 × 100%
- 强度排序: 按偏离率数值排序，数值最大=1（最强）

"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_stock_data(stock_code: str, days: int = 100, end_date: str = None) -> pd.DataFrame:
    """获取股票/指数数据"""
    bs.login()
    
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=days)).strftime('%Y-%m-%d')
    
    rs = bs.query_history_k_data_plus(
        stock_code,
        'date,code,open,high,low,close,volume',
        start_date=start_date,
        end_date=end_date,
        frequency='d'
    )
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    bs.logout()
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def calculate_indicators_ema(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    计算趋势线指标（使用EMA指数移动平均）
    
    公式：
    1. 均价 = (最高价 + 最低价) / 2
    2. 趋势线 = 均价的20日指数移动平均(EMA)
       EMA_t = alpha × price_t + (1-alpha) × EMA_{t-1}
       alpha = 2 / (period + 1) = 2/21 ≈ 0.0952
    """
    # 计算 (最高价 + 最低价) / 2
    df['hl2'] = (df['high'] + df['low']) / 2
    
    # 计算20日指数移动平均(EMA)
    # adjust=False 表示使用标准的递归 EMA 计算
    df['trend_line'] = df['hl2'].ewm(span=period, adjust=False).mean()
    
    # 计算偏离率
    df['deviation'] = (df['close'] - df['trend_line']) / df['trend_line'] * 100
    
    return df


def analyze_index(stock_code: str, period: int = 20) -> dict:
    """分析单只指数/股票"""
    try:
        df = get_stock_data(stock_code, days=period * 4)
        df = calculate_indicators_ema(df, period)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        today_change = (latest['close'] - prev['close']) / prev['close'] * 100
        
        change_5d = 0
        change_20d = 0
        if len(df) > 5:
            change_5d = (df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6] * 100
        if len(df) > 20:
            change_20d = (df['close'].iloc[-1] - df['close'].iloc[-21]) / df['close'].iloc[-21] * 100
        
        return {
            'code': stock_code,
            'current_price': latest['close'],
            'trend_line': latest['trend_line'],
            'deviation': latest['deviation'],
            'today_change': today_change,
            'change_5d': change_5d,
            'change_20d': change_20d,
        }
        
    except Exception as e:
        return {'code': stock_code, 'error': str(e)}


def display_analysis(results: list, output_file: str = None):
    """展示分析结果，可选择同时输出到文件
    
    Args:
        results: 分析结果列表
        output_file: 如果提供，将结果同时写入此文件
    """
    # 过滤掉有错误的结果
    valid_results = [r for r in results if 'current_price' in r]
    valid_results.sort(key=lambda x: x.get('deviation', 0), reverse=True)
    
    lines = []
    header = '=' * 90
    lines.append(header)
    lines.append('宽基指数趋势大模型 - EMA版本')
    lines.append('   日期: ' + datetime.now().strftime('%Y年%m月%d日'))
    lines.append(header)
    lines.append('{:<4} {:<10} {:>10} {:>8} {:>8} {:>9} {:>10} {:>8} {:<6}'.format(
        '强度', '指数', '现价', '今日涨跌', '5日涨跌', '20日涨跌', '趋势线', '偏离率', '信号'))
    lines.append('-' * 90)
    
    for i, r in enumerate(valid_results, 1):
        dev = r.get('deviation', 0)
        
        if dev > 5:
            signal = '极强'
        elif dev > 2:
            signal = '强势'
        elif dev > 0:
            signal = '偏强'
        elif dev > -2:
            signal = '偏弱'
        else:
            signal = '超卖'
        
        lines.append('{:<4} {:<10} {:>10.3f} {:>+7.2f}% {:>+7.2f}% {:>+8.2f}% {:>10.3f} {:>+7.2f}% {:<6}'.format(
            i, r['code'], r['current_price'], r['today_change'], 
            r['change_5d'], r['change_20d'], r['trend_line'], dev, signal))
    
    lines.append(header)
    lines.append('趋势线 = (最高价+最低价)/2 的20日指数移动平均(EMA)')
    lines.append('EMA alpha = 2/(period+1) = 2/21 ≈ 0.0952')
    lines.append('偏离率 = (现价-趋势线)/趋势线 × 100%')
    lines.append('强度排序按偏离率数值，数值越大=短期走势越强')
    lines.append('EMA相比SMA对近期数据更敏感，反应更灵敏')
    lines.append(header)
    
    # 打印到终端
    for line in lines:
        print(line)
    
    # 如果指定了输出文件，写入文件
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f'\n分析结果已保存至: {output_file}')



if __name__ == "__main__":
    import sys
    
    # 解析命令行参数：--output 指定输出文件路径
    output_file = None
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    indices = [
   # A股主要指数
    ('sh.000001', '上证指数'),
    ('sz.399001', '深证成指'),
    ('sz.399006', '创业板指'),
    # ('880823', '微盘指数'),      # 通达信专有指数，无交易所前缀
    # ('880801', '基金重仓'),      # 通达信专有指数，无交易所前缀
    # ('880003', '平均股价'),      # 通达信专有指数，无交易所前缀
    
    # 宽基ETF
    ('sh.510050', '上证50'),
    ('sh.510300', '沪深300'),
    ('sh.510500', '中证500'),
    ('sh.512100', '中证1000'),
    ('sh.563300', '国证2000'),   # 上交所跨市场ETF
    
    # 风格/策略ETF
    ('sz.159949', '创业板50'),
    ('sz.159967', '创成长'),
    ('sh.588000', '科创50'),
    ('sh.588220', '科创100'),
    ('sh.512890', '红利低波'),
    
    # 跨境ETF（QDII）
    ('sz.159920', '恒生ETF'),
    ('sh.513130', '恒生科技'),
    ('sh.513100', '纳指'),
    ('sh.513030', '德国'),
    ('sh.513520', '日经'),
    ('sh.513310', '中韩半导体'),
    ('sz.164824', '印度基金'),   # LOF，深市
    
    # 商品ETF
    ('sh.518880', '黄金'),
    ('sz.161226', '白银'),       # LOF，深市
    ('sz.159985', '豆粕'),
    ('sz.162411', '华宝油气'),   # LOF，深市
    
]
    
    print('\n正在获取数据（EMA版本）...\n')
    
    results = []
    for code, name in indices:
        try:
            result = analyze_index(code)
            result['code'] = name
            results.append(result)
            print('OK ' + name)
        except Exception as e:
            print('FAIL ' + name + ': ' + str(e))
    
    if results:
        display_analysis(results, output_file=output_file)
    
    print('\n分析完成!')

