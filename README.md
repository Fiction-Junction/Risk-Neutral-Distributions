# QQQ Risk-Neutral Density Distributions

## Overview

This project computes risk-neutral distributions from QQQ options market data, and is meant to supplement the accompanying main paper on risk-neutral measures and density distributions.

To compute the distributions, we use options pricing data, combined with spot prices and interest rates, to extract the market's implied probability distribution of future spot prices at different expiration dates.

## Project Structure

```
.
├── __main__.py  # Entry point - generates random RND example
├── requirements.txt   # Python dependencies
├── README.md  # This file
│
├── data/   # Input data files
│   ├── qqq_options_100.csv  # QQQ options data (first 100 snapshots from original 2 years worth)
│   ├── qqq_daily_ohlcv_2024_2026.csv   # QQQ spot price OHLCV data
│   └── DFF.csv    # Federal Funds effective rate data
│
├── notebooks/      # Jupyter notebooks
│   └── final notebook.ipynb  # Documents initial thought processes, albeit cleaned up to be somewhat presentable
│
├── src/     # Core Python modules
│  ├── data_loader.py    # Load and preprocess all input data
│  ├── dict_generator.py   # Generates RND dictionary
│  ├── pipeline.py   # Core RND extraction functions
│  ├── helpers.py  # Utility functions for data processing
│  └── validators.py  # Data validation functions
│
└── main_paper.pdf # main paper   
```

## Data Files

### Input Data

| File | Description | Source |
|------|-------------|--------|
| `qqq_options_100.csv` | Subset of options data (first 100 snapshot dates) | EODHD |
| `qqq_daily_ohlcv_2024_2026.csv` | QQQ daily OHLCV prices | Yahoo Finance |
| `DFF.csv` | Federal Funds effective rates | Federal Reserve Bank |

Additionally, quarterly dividends data from Macrotrends was directly inserted into the relevant files without the use of a ```csv``` file.

## Core Modules

### `data_loader.py`
Loads and preprocesses all input data:
- Reads options CSV with proper formatting
- Extracts spot prices aligned with snapshot dates
- Retrieves interest rates for risk-free rate calculations
- Manages quarterly dividend data hardcoded in the script

**Exports**:
- `OPTIONS`: DataFrame of options data
- `SPOTS`: DataFrame of spot prices
- `RATES`: DataFrame of interest rates
- `DIVIDENDS`: Dictionary of dividend amounts by date

### `dict_generator.py`
Main module that generates the RND dictionary:
- Iterates over snapshot dates and expiration dates
- Calls pipeline functions for each combination
- Filters for DTE (days to expiration) ≤ 64
- Returns dictionary with computed RNDs and metrics

**Key Function**:
```python
rnd_dict = gen(options, spots, rates, dividends, N)
```
Where `N` is the number of snapshot dates to process. Note that the maximum is 100 dates, but 90 were tested on for this project.

### `pipeline.py`
Core numerical functions for RND extraction:

**`build_grid(options, spots, snap, exp, dte, r, dividends)`**
- Extracts strike prices and call prices for a given snapshot-expiration pair
- Uses put-call parity to impute missing call prices from puts
- Applies forward price adjustments for cost-of-carry (rates and dividends)

**`func(grid)`**
- Smooths the call price function using PCHIP interpolation
- Creates a continuous representation of the option price surface

**`bl(grid, curve, r, dte)`**
- Implements the Breeden-Litzenberger formula
- Extracts risk-neutral probability density: $f(S_T) = e^{rT} \frac{\partial^2 C}{\partial K^2}$
- Returns (strikes, rnd)-tuple grid

### `helpers.py`
Utility functions:
- `filter_options()`: Filter options by snapshot-expiration date
- `get_spot_price()`: Retrieve spot price for a given date
- `get_call_price()`: Extract call price from options data
- `get_put_price()`: Extract put price from options data
- `get_dividend()`: Calculate dividend yield
- `get_dte()`: Calculate days to expiration
- `get_rate()`: Retrieve interest rate for a given date

### `validators.py`
Data validation:
- `mono_convex()`: Checks monotonicity and convexity of call price function
- Ensures no arbitrage in pricing

## Running main script

Generate a random RND distribution visualization:
```bash
python __main__.py
```

This will:
1. Load options, spot, rate, and dividend data
2. Generate RND data for first $N$ snapshot dates
3. Randomly select one distribution to plot
4. Includes snapshot and expiration dates, DTE and skew

## Dependencies

```
pandas>=1.5  
numpy>=1.23   
matplotlib>=3.6     
scipy>=1.9   # for interpolation and filters
jupyter>=1.0 # Jupyter notebooks
yfinance>=1.4.1 # Yahoo Finance
```

Install with:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `__main__.py` by changing $N$ for the number of snapshot dates  from which the generated distribution is randomly chosen from ($N \leq 100$)

## File Sizes

- `qqq_options_daily_anchors_2y.csv`: 195.1 MB (full dataset, not included)
- `qqq_options_100.csv`: 42.5 MB (first 100 snapshot dates)
- `qqq_daily_ohlcv_2024_2026.csv`: 46 KB (daily OHLCV)
- `DFF.csv`: 6 KB (daily rates)

## Notes

- Original full dataset containing ~2 years of options data (2024-2026) is not included due to Github standard repository limits of 100 MiB
- Reduced `qqq_options_100.csv` is used by default for faster processing
- Maximum DTE considered is 64 days
- Analysis is based on market data from 2024-2026 period
