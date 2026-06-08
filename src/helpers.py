import pandas as pd
import numpy as np

def get_rate(rates, date):
    '''Returns FED rate for a given date'''
    for idx, row in rates.iterrows():
        if idx == date:
            return row['rate']
    return None

def filter_options(options, snap, exp):
    ''' 
    Returns filtered options data
    None if data is empty
    '''
    data = options[(options['snapshot_date'] == snap) &
                   (options['exp_date'] == exp)
                   ]
    return None if data.empty else data

def get_dte(snap, exp):
    '''Returns DTE in days'''
    snap = pd.to_datetime(snap)
    exp = pd.to_datetime(exp)
    dte = (exp - snap).days
    return dte

def get_spot_price(spots, snap):
    '''
    Returns spot price
    None if price not found
    '''
    if snap not in spots.index:
        return None
    else:
        return spots.loc[snap, 'close']
    
def get_call_price(options, k):
    '''
    Returns call price
    None if filtered options data is empty
    None if either bid or ask is invalid
    '''
    data = options[(options['type'] == 'call') &
                   (options['strike'] == k)
                   ]
    if data.empty: # if no calls are found
        return None
    row = data.iloc[0]
    bid = row['bid']
    ask = row['ask']
    if pd.isna(bid) or pd.isna(ask) or bid <= 0 or ask <= 0 or bid >= ask: # invalid bid ask values
        return None
    return (row['bid'] + row['ask']) / 2
    
def get_put_price(options, k):
    '''
    Returns put price
    None if filtered options data is empty
    None if either bid or ask is invalid
    '''
    data = options[(options['type'] == 'put') &
                   (options['strike'] == k)
                   ]
    if data.empty: # if no puts are found
        return None
    row = data.iloc[0]
    bid = row['bid']
    ask = row['ask']
    if pd.isna(bid) or pd.isna(ask) or bid <= 0 or ask <= 0 or bid >= ask: # invalid bid ask values
        return None
    return (row['bid'] + row['ask']) / 2

def get_dividend(snap, exp, dividends, spots):
    """
    Calculate annualized dividend yield for QQQ between snapshot and expiration dates.
    
    Quarterly-based approach:
    - Finds all dividend ex-dates between snapshot and expiration
    - Sums actual dividend amounts to be paid
    - Computes annualized yield accounting for exact payment timing
    
    Methodology:
        - Paid yield = (Σ dividends paid) / (spot price)
        - Annualized = Paid yield * (365 / days_to_expiration)
        - This accounts for the exact number and timing of dividend payments
    
    Example:
        If snapshot='2024-01-15', expiration='2024-06-15'
        And QQQ pays $0.060 on 2024-03-18 (within period):
        - 1 dividend falls within period
        - 6-month implied yield ≈ 0.060/420 ≈ 0.143% for 6 months
        - Annualized ≈ 0.143% × (365/152) ≈ 0.34% ≈ 0.0034
    """
    
    snap_dt = pd.to_datetime(snap)
    exp_dt = pd.to_datetime(exp)
    dte = (exp_dt - snap_dt).days
    
    if dte <= 0:
        return 0.0  # Invalid date range
    
    # Find all dividends paid between snapshot (inclusive) and expiration (exclusive)
    # We use "ex-dividend date" logic: if ex-date is between snap and exp, dividend will be paid
    dividends_in_period = []
    
    for ex_date_str, dividend_amount in dividends.items():
        ex_dt = pd.to_datetime(ex_date_str)
        
        # Include dividend if ex-date falls within period
        # (shareholders own shares on ex-date, receive dividend)
        if snap_dt <= ex_dt < exp_dt:
            dividends_in_period.append({
                'ex_date': ex_dt,
                'amount': dividend_amount,
                'days_to_payment': (ex_dt - snap_dt).days
            })
    
    if not dividends_in_period:
        # No dividends in period: use historical average
        # Calculate average quarterly dividend from historical data
        if len(dividends) > 0:
            avg_dividend = np.mean(list(dividends.values()))
            # Estimate how many quarters in this period
            quarters = max(1, dte / 91.25)  # 91.25 = avg days per quarter
            total_expected = avg_dividend * quarters
        else:
            return 0.0
    else:
        # Sum all dividends that will be paid in this period
        total_expected = sum(div['amount'] for div in dividends_in_period)
    
    # Get approximate spot price for yield calculation
    # Use the SPOTS dataframe (available in notebook context)
    if snap in spots.index:
        spot_price = spots.loc[snap, 'close']
    else:
        # If exact date not available, use last available before snap
        available_dates = spots.index[spots.index <= snap]
        if len(available_dates) > 0:
            spot_price = spots.loc[available_dates[-1], 'close']
        else:
            return 0.0  # Can't calculate without spot price
    
    # Calculate yield for the period, then annualize
    period_yield = total_expected / spot_price
    annualized_yield = period_yield * (365 / dte)
    
    # Sanity checks
    if annualized_yield < 0 or annualized_yield > 0.30:  # Yield > 30% is unrealistic
        # Fall back to simple average if result seems wrong
        avg_div = np.mean(list(dividends.values()))
        annualized_yield = (avg_div / spot_price) * 4  # Assume 4 quarters/year
    
    return max(0.0, annualized_yield)  # Ensure non-negative