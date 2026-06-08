# QQQ Risk-Neutral Density Distributions

## Overview

This project computes risk-neutral distributions from QQQ (Nasdaq-100) options market data, and is meant to supplement the accompanying main paper on risk-neutral measures and density distributions.

This project uses options pricing data combined with spot prices and interest rates to extract the market's implied probability distribution of future spot prices at different expiration dates.

## Key Features

- **Risk-Neutral Density Extraction**: Converts options call prices into RND distributions using the Breeden-Litzenberger (BL) methodology
- **Multi-horizon Analysis**: Analyzes distributions across multiple expiration dates and snapshot dates
- **Statistical Metrics**: Computes skewness, kurtosis, and other distribution characteristics
- **Visualization**: Generates publication-quality plots of RND distributions
- **Data Curation**: Handles missing data, applies put-call parity when needed, and validates monotonicity/convexity

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
| `qqq_options_100.csv` | Subset of options data (first 100 snapshot dates) | Derived from full dataset |
| `qqq_daily_ohlcv_2024_2026.csv` | QQQ daily OHLCV prices | Yahoo Finance / Market data |
| `DFF.csv` | Federal Funds effective rates | Federal Reserve data |

### Key Data Fields

**Options Data**:
- `snapshot_date`: Date when options were observed
- `exp_date`: Expiration date of the option
- `strike`: Strike price (K)
- `call_bid`, `call_ask`: Call option bid/ask prices
- `put_bid`, `put_ask`: Put option bid/ask prices
- `call_iv`, `put_iv`: Implied volatility for calls/puts

**Spot Prices**:
- `date`, `open`, `high`, `low`, `close`, `volume`

**Interest Rates**:
- `date`, `rate`: Federal Funds effective rate (%)

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
Main orchestration module that generates the RND dictionary:
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
- Extracts strike prices and call prices for a given snapshot/expiration pair
- Uses put-call parity to impute missing call prices from puts
- Applies forward price adjustments for cost-of-carry (rates and dividends)

**`func(grid)`**
- Smooths the call price function using PCHIP interpolation
- Creates a continuous representation of the option price surface

**`bl(grid, curve, r, dte)`**
- Implements the Breeden-Litzenberger formula
- Extracts risk-neutral probability density: $f(S_T) = e^{rT} \frac{\partial^2 C}{\partial K^2}$
- Returns (strikes, rnd) tuple representing the density distribution

### `helpers.py`
Utility functions:
- `filter_options()`: Filter options by snapshot/expiration date
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

## Usage

### Running the Main Script
Generate a random RND distribution visualization:
```bash
python __main__.py
```

This will:
1. Load options, spot, rate, and dividend data
2. Generate RND for first N snapshot dates
3. Randomly select one distribution
4. Compute skewness and other metrics
5. Plot the RND

## Technical Approach

### Risk-Neutral Density Extraction

The Breeden-Litzenberger formula extracts RND from call prices:

$$f(S_T) = e^{rT} \frac{\partial^2 C(S, t; K)}{\partial K^2}$$

Where:
- $C(K)$ = call price at strike K
- $S$ = spot price
- $T$ = time to expiration
- $r$ = risk-free rate
- $S_T$ = spot price at expiration

**Steps**:
1. Extract call prices for a range of strikes
2. Fit smooth curve to call prices (PCHIP interpolation)
3. Compute second derivative with respect to strike
4. Discount by $e^{-rT}$ to get probability density

### Cost-of-Carry Adjustments
- Accounts for dividends: $q$ (quarterly dividend yield)
- Forward price: $F = S \cdot e^{(r-q)T}$
- Used to adjust strike prices in currency of the underlying

### Data Quality Controls
- **Put-Call Parity**: Uses $C = P + Se^{-qT} - Ke^{-rT}$ to impute missing calls
- **Monotonicity Check**: Ensures call prices are monotonically decreasing in strike
- **Convexity Check**: Ensures second derivative is positive (no arbitrage)

## Dependencies

```
pandas>=1.5          # Data manipulation
numpy>=1.23         # Numerical computing
matplotlib>=3.6     # Visualization
scipy>=1.9          # Scientific computing (interpolation, filters)
jupyter>=1.0        # Jupyter notebooks
yfinance>=1.4.1     # Historical market data
```

Install with:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `__main__.py` to:
- Change `N` for number of snapshot dates to process
- Modify visualization parameters

## File Sizes

- `qqq_options_daily_anchors_2y.csv`: ~50+ MB (full dataset)
- `qqq_options_100.csv`: ~1.7 MB (first 100 snapshot dates)
- `qqq_daily_ohlcv_2024_2026.csv`: Small (daily OHLCV)

## Notes

- Original full dataset containing ~2 years of options data (2024-2026) is not included due to Github constraints
- Reduced `qqq_options_100.csv` is used by default for faster processing
- Maximum DTE considered is 64 days
- Analysis is based on market data from 2024-2026 period
