# JSE Dashboard

Pulls live data for JSE-listed companies tradable on EasyEquities, grouped into the top 20 South African industries, and saves them to a CSV with an industry summary.

Live dashboard: https://lethuxololanga.github.io/jse-dashboard/

## Requirements

- Python 3.x
- `yfinance`

```
pip install -r requirements.txt
```

## Usage

```
python scraper.py
```

- Writes `stockdata.csv` (overwritten each run): `symbol, name, industry, yahoo_sector, yahoo_industry, price, change_pct, market_cap, currency, pe, div_yield, beta`.
- Prints a summary ranked by industry: stock count, total market cap (Rand billions), average daily change %, tickers.
- Lists any tickers that failed (delisted, renamed).

## Web dashboard

Each run also writes `site/data.json` (quotes, fundamentals, a year of daily prices, ETFs, the Top 40 / All Share indices, rand and commodity prices), which `site/index.html` reads:

- **Time range:** 1D / 1W / 1M / 3M / YTD / 1Y. Everything on the page (headline, industries, movers, tables, portfolio) switches to that period.
- **Industries:** market value, trend line and average move per industry, with the Top 40 as a reference row. Select one to focus the dashboard.
- **Rand and commodities strip:** USD/ZAR, gold, platinum, palladium, Brent.
- **Company and ETF detail:** select a name for its price chart (hover or arrow keys to read values), 52-week range, P/E, dividend yield, beta and a business summary.
- **Screener:** filter by dividend yield and P/E; sort any column.
- **Watchlist and portfolio:** star companies, record shares held or import a CSV (a ticker column plus a shares/units/quantity column). Saved only in your browser.
- **Dual-listed toggle:** BHP, Glencore, BAT and others count at their full global value; untick to leave them out of value weightings.
- **Shareable links:** filters live in the URL, so "Copy link" reproduces your view. **Export CSV** downloads the current selection.

View locally:

```
python scraper.py
python -m http.server -d site
```

Then open http://localhost:8000.

### GitHub Pages

`.github/workflows/pages.yml` runs the scraper every weekday at 18:30 SAST (after JSE close) and deploys `site/` to GitHub Pages. One-time setup: repo **Settings → Pages → Source: GitHub Actions**. Trigger the first run manually from the **Actions** tab ("Run workflow").

**Daily email digest (optional):** add repo secrets `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` (an app password, e.g. for Gmail use `smtp.gmail.com` / `465`) and `MAIL_TO`. To list your own picks in the email, add a repo *variable* `WATCHLIST`, e.g. `SBK,NPN,STX40`. Without the secrets the email step is skipped.

GitHub pauses scheduled workflows after 60 days without repo activity. If the site stops updating, re-enable the workflow on the **Actions** tab.

## Notes

- Data comes from Yahoo Finance. EasyEquities has no public API.
- JSE prices are quoted in **ZAc (cents)**. Divide by 100 to get Rand. Market cap is already in Rand.

## Customisation

Edit the `INDUSTRIES` dict at the top of the script to add or remove industries and tickers. Use the plain JSE code (e.g. `NPN`); the `.JO` suffix is added automatically. ETFs live in `ETFS`, and companies with a primary listing outside the JSE in `DUAL_LISTED`.
