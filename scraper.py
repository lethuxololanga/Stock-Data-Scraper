import csv
import html
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent

# Top 20 South African industries, ranked roughly by JSE market-cap weight.
# All tickers are JSE-listed and tradable on an EasyEquities ZAR account.
INDUSTRIES = {
    'Technology & Internet': ['NPN', 'PRX'],
    'Banking': ['SBK', 'FSR', 'ABG', 'NED', 'CPI'],
    'Diversified Mining': ['AGL', 'BHG', 'GLN', 'S32', 'KIO'],
    'Gold Mining': ['GFI', 'ANG', 'HAR', 'DRD'],
    'PGM Mining': ['IMP', 'VAL', 'NPH', 'SSW'],
    'Luxury & Tobacco': ['CFR', 'BTI'],
    'Telecommunications': ['MTN', 'VOD', 'TKG'],
    'Life Insurance': ['SLM', 'DSY', 'OMU', 'MTM'],
    'Short-term Insurance': ['SNT', 'OUT'],
    'Asset Management & Exchanges': ['NY1', 'CML', 'JSE'],
    'Food & Grocery Retail': ['SHP', 'PIK', 'SPP', 'BOX'],
    'Clothing & General Retail': ['MRP', 'TFG', 'TRU', 'PPH', 'WHL'],
    'Healthcare & Pharma': ['NTC', 'LHC', 'APN'],
    'Chemicals & Energy': ['SOL', 'OMN', 'AFE'],
    'Coal & Energy Minerals': ['EXX', 'TGA'],
    'Real Estate (REITs)': ['GRT', 'RDF', 'NRP', 'HYP', 'FFB'],
    'Food Producers': ['TBS', 'AVI', 'RCL', 'ARL'],
    'Paper & Packaging': ['MNP', 'SAP'],
    'Industrial & Logistics': ['BVT', 'KAP', 'MTH', 'SPG', 'GND'],
    'Construction & Materials': ['PPC', 'WBO', 'RLO'],
}

# Primary listing outside the JSE: Yahoo's market cap is the whole company's global value,
# which overstates their weight on the JSE. The dashboard can exclude them from weightings.
# ponytail: hand-maintained, update when listings change.
DUAL_LISTED = {'BHG', 'GLN', 'AGL', 'S32', 'BTI', 'CFR', 'PRX', 'MNP', 'ANG', 'NY1'}

# Popular ETFs on EasyEquities, grouped by what they hold.
ETFS = {
    'SA shares': ['STX40', 'CTOP50', 'ETFT40', 'STXDIV', 'STXRES', 'STXIND', 'STXFIN'],
    'SA property': ['STXPRO', 'CSPROP'],
    'Global shares': ['STX500', 'CSP500', 'SYG500', 'STXNDQ', 'ETF5IT', 'STXWDM', 'SYGWD', 'STXEMG', 'GLODIV'],
    'Commodities': ['GLD', 'ETFGLD', 'NGPLT'],
}

BENCHMARKS = {'J200': 'Top 40', 'J203': 'All Share'}

# Yahoo symbol → (label, unit). Trade on different days from the JSE, so history is stored separately.
MACRO = {
    'ZAR=X': ('Rand per US dollar', 'R'),
    'GC=F': ('Gold', '$/oz'),
    'PL=F': ('Platinum', '$/oz'),
    'PA=F': ('Palladium', '$/oz'),
    'BZ=F': ('Brent crude', '$/bbl'),
}

fieldnames = ['symbol', 'name', 'industry', 'yahoo_sector', 'yahoo_industry',
              'price', 'change_pct', 'market_cap', 'currency', 'pe', 'div_yield', 'beta']


def yahoo(symbol):
    return symbol if '=' in symbol else f'{symbol}.JO'


def getData(symbol, industry, etf=False):

    """
    Retrieve quote and fundamentals for the given JSE symbol from Yahoo Finance.

    Arguments:
        symbol (str): The JSE code, without the .JO suffix.
        industry (str): The industry label from INDUSTRIES (or the ETF group).
        etf (bool): ETFs have no market cap or fundamentals.

    Returns:
        stock (dict): fieldnames plus 52-week range, summary and quote time.
    """

    info = yf.Ticker(yahoo(symbol)).info
    price = info.get('currentPrice') or info.get('regularMarketPrice')
    if price is None:
        raise ValueError('no price data (delisted or wrong ticker?)')
    stock = {
        'symbol': symbol,
        'name': info.get('longName') or info.get('shortName', ''),
        'industry': industry,
        'price': price,
        'change_pct': info.get('regularMarketChangePercent', ''),
        'currency': info.get('currency', ''),
        'low52': info.get('fiftyTwoWeekLow', ''),
        'high52': info.get('fiftyTwoWeekHigh', ''),
        'quote_time': info.get('regularMarketTime'),
    }
    if not etf:
        stock.update({
            'yahoo_sector': info.get('sector', ''),
            'yahoo_industry': info.get('industry', ''),
            'market_cap': info.get('marketCap', ''),
            'pe': round(info['trailingPE'], 1) if info.get('trailingPE') else '',
            'div_yield': info.get('dividendYield', ''),  # already a percentage
            'beta': info.get('beta', ''),
            'summary': (info.get('longBusinessSummary') or '')[:600],
            'website': info.get('website', ''),
            'dual_listed': symbol in DUAL_LISTED,
        })
    return stock


def getHistory(symbols):

    """One batch download of a year of daily closes. Returns {'dates': [...], 'series': {symbol: [...]}}."""

    closes = yf.download([yahoo(s) for s in symbols], period='1y', interval='1d',
                         auto_adjust=True, progress=False, threads=True)['Close']
    closes = closes.dropna(how='all').ffill()
    series = {}
    for s in symbols:
        col = closes.get(yahoo(s))
        if col is None or col.isna().all():
            continue
        series[s] = [None if math.isnan(v) else round(float(v), 4) for v in col]
    return {'dates': [d.strftime('%Y-%m-%d') for d in closes.index], 'series': series}


def summarise(rows):

    """Group rows by industry, in INDUSTRIES order, with count, total market cap and avg change."""

    groups = defaultdict(list)
    for row in rows:
        groups[row['industry']].append(row)

    summary = []
    for industry in INDUSTRIES:
        stocks = groups.get(industry, [])
        changes = [s['change_pct'] for s in stocks if s['change_pct'] != '']
        summary.append({
            'industry': industry,
            'count': len(stocks),
            'market_cap': sum(s['market_cap'] for s in stocks if s['market_cap'] != ''),
            'avg_change': sum(changes) / len(changes) if changes else None,
            'symbols': [s['symbol'] for s in stocks],
        })
    return summary


def weightedChange(rows, exclude_dual=False):

    """Market-cap-weighted average of today's change, optionally leaving out dual-listed companies."""

    priced = [r for r in rows if r['change_pct'] != '' and r['market_cap'] != ''
              and not (exclude_dual and r.get('dual_listed'))]
    cap = sum(r['market_cap'] for r in priced)
    return sum(r['change_pct'] * r['market_cap'] for r in priced) / cap if cap else None


def printSummary(summary):
    print(f"\n{'#':>2}  {'Industry':<30} {'Stocks':>6} {'Mkt cap (R bn)':>14} {'Avg chg %':>10}  Tickers")
    for rank, s in enumerate(summary, 1):
        avg = f"{s['avg_change']:.2f}" if s['avg_change'] is not None else '-'
        cap = f"{s['market_cap'] / 1e9:,.1f}"
        print(f"{rank:>2}  {s['industry']:<30} {s['count']:>6} {cap:>14} {avg:>10}  {', '.join(s['symbols'])}")


def writeDigest(rows, etfs, history, macro, watchlist):

    """Plain HTML email body for the daily digest (sent by the workflow when mail secrets exist)."""

    def pct(v):
        return '–' if v in ('', None) else f"{'+' if v > 0 else ''}{v:.2f}%"

    def dayChange(series):
        vals = [v for v in series if v is not None][-2:]
        return (vals[1] / vals[0] - 1) * 100 if len(vals) == 2 and vals[0] else None

    w = weightedChange(rows)
    up = sum(1 for r in rows if r['change_pct'] != '' and r['change_pct'] > 0)
    down = sum(1 for r in rows if r['change_pct'] != '' and r['change_pct'] < 0)
    priced = sorted((r for r in rows if r['change_pct'] != ''), key=lambda r: r['change_pct'])
    lines = [f"<p>The JSE's {len(rows)} leaders moved <b>{pct(w)}</b> today, weighted by value. "
             f"{up} rose and {down} fell.</p>"]

    bench = [f"{label} {pct(dayChange(history['series'][code]))}"
             for code, label in BENCHMARKS.items() if code in history['series']]
    if bench:
        lines.append(f"<p>{', '.join(bench)}.</p>")

    def table(title, items):
        cells = ''.join(f"<tr><td>{html.escape(r['name'])} ({r['symbol']})</td><td align='right'>{pct(r['change_pct'])}</td></tr>"
                        for r in items)
        return f"<h3>{title}</h3><table cellpadding='4'>{cells}</table>"

    lines.append(table('Biggest risers', priced[::-1][:5]))
    lines.append(table('Biggest fallers', priced[:5]))
    watched = [r for r in rows + etfs if r['symbol'] in watchlist]
    if watched:
        lines.append(table('Your watchlist', watched))
    rand = [f"{label} {pct(dayChange(macro['series'][sym]))}" for sym, (label, _) in MACRO.items() if sym in macro['series']]
    if rand:
        lines.append(f"<p>{', '.join(rand)}.</p>")
    lines.append("<p style='color:#666'>Prices from Yahoo Finance and may be delayed. This isn't financial advice.</p>")

    (HERE / 'digest.html').write_text('\n'.join(lines))
    (HERE / 'digest_subject.txt').write_text(f"JSE today: {pct(w)}, {up} up, {down} down")


def selfCheck():
    rows = [
        {'symbol': 'A', 'industry': 'Banking', 'change_pct': 1.0, 'market_cap': 10},
        {'symbol': 'B', 'industry': 'Banking', 'change_pct': 3.0, 'market_cap': ''},
    ]
    banking = next(s for s in summarise(rows) if s['industry'] == 'Banking')
    assert banking == {'industry': 'Banking', 'count': 2, 'market_cap': 10,
                       'avg_change': 2.0, 'symbols': ['A', 'B']}, banking
    assert len(summarise(rows)) == len(INDUSTRIES)

    rows = [{'change_pct': 2.0, 'market_cap': 30, 'dual_listed': True},
            {'change_pct': -1.0, 'market_cap': 10, 'dual_listed': False}]
    assert weightedChange(rows) == 1.25
    assert weightedChange(rows, exclude_dual=True) == -1.0
    assert yahoo('SBK') == 'SBK.JO' and yahoo('^J200') == '^J200.JO' and yahoo('ZAR=X') == 'ZAR=X'


if __name__ == '__main__':
    selfCheck()

    rows, etfs, failed = [], [], []
    for industry, symbols in INDUSTRIES.items():
        for symbol in symbols:
            print('Getting data for:', symbol)
            try:
                rows.append(getData(symbol, industry))
            except Exception as e:
                failed.append(symbol)
                print(f'  skipped {symbol}: {e}')

    # Don't overwrite good data (or deploy a half-empty site) if Yahoo blocked most requests.
    if len(failed) > len(rows):
        sys.exit(f'Only {len(rows)} of {len(rows) + len(failed)} tickers retrieved, nothing written.')

    for group, symbols in ETFS.items():
        for symbol in symbols:
            print('Getting data for:', symbol)
            try:
                etfs.append(getData(symbol, group, etf=True))
            except Exception as e:
                print(f'  skipped ETF {symbol}: {e}')

    # History is a nice-to-have: the dashboard falls back to today-only if it's missing.
    jse_symbols = [r['symbol'] for r in rows] + [e['symbol'] for e in etfs] + ['^' + b for b in BENCHMARKS]
    try:
        history = getHistory(jse_symbols)
        history['series'] = {k.lstrip('^'): v for k, v in history['series'].items()}
    except Exception as e:
        print('History download failed:', e)
        history = {'dates': [], 'series': {}}
    try:
        macro = getHistory(list(MACRO))
    except Exception as e:
        print('Macro download failed:', e)
        macro = {'dates': [], 'series': {}}
    macro['labels'] = {sym: {'label': label, 'unit': unit} for sym, (label, unit) in MACRO.items()}

    with open(HERE / 'stockdata.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    # Use the latest quote time, not the run time, so a holiday run doesn't relabel old prices.
    quote_times = [r['quote_time'] for r in rows if r['quote_time']]
    updated = datetime.fromtimestamp(max(quote_times), timezone.utc) if quote_times else datetime.now(timezone.utc)
    summary = summarise(rows)
    with open(HERE / 'site' / 'data.json', 'w') as f:
        json.dump({
            'updated': updated.isoformat(timespec='minutes'),
            'industries': summary,
            'stocks': rows,
            'etfs': etfs,
            'benchmarks': BENCHMARKS,
            'history': history,
            'macro': macro,
            'failed': failed,
        }, f, separators=(',', ':'))

    watchlist = {s.strip().upper() for s in os.environ.get('WATCHLIST', '').split(',') if s.strip()}
    writeDigest(rows, etfs, history, macro, watchlist)

    printSummary(summary)
    if failed:
        print('\nFailed tickers:', ', '.join(failed))
