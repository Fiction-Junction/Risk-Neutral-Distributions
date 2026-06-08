import pandas as pd
from pathlib import Path

MODULE_DIR = Path(__file__).parent        # /path/to/src
PROJECT_DIR = MODULE_DIR.parent           # /path/to/project (root)
DATA_DIR = PROJECT_DIR / "data"           # /path/to/data

OPTIONS = pd.read_csv(DATA_DIR / "qqq_options_100.csv")

SPOTS = pd.read_csv(
    DATA_DIR / "qqq_daily_ohlcv_2024_2026.csv",
    skiprows=3,  # Skip the 3 header rows
    index_col=0,  # date becomes index
    names=['date', 'close', 'high', 'low', 'open', 'volume']
)
SPOTS.index.name = 'date'

RATES = pd.read_csv(
    DATA_DIR / "DFF.csv",
    index_col=0  # First column (date) becomes index
)
RATES.index.name = 'date'
RATES.rename(columns={'Rate': 'rate'}, inplace=True)

DIVIDENDS = {
    '2023-12-27': 0.061,  # Q4 2023
    '2024-03-18': 0.060,  # Q1 2024
    '2024-06-24': 0.061,  # Q2 2024
    '2024-09-23': 0.063,  # Q3 2024
    '2024-12-23': 0.054,  # Q4 2024
    '2025-03-24': 0.061,  # Q1 2025
    '2025-06-23': 0.053,  # Q2 2025
    '2025-09-22': 0.047,  # Q3 2025
    '2025-12-22': 0.045,  # Q4 2025
    '2026-03-23': 0.048,  # Q1 2026
    '2026-05-29': 0.038,  # Q2 2026
}