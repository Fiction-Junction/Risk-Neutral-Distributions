import math
import numpy as np
from scipy.signal import savgol_filter
from scipy.stats import gaussian_kde
from scipy.interpolate import PchipInterpolator

# Import from local module
from src.helpers import(filter_options,
                        get_spot_price,
                        get_call_price,
                        get_put_price,
                        get_dividend)
from src.validators import mono_convex

def build_grid(options, spots, snap, exp, dte, r, dividends):
    '''Returns a tuple of $(K, C)$ pairs which form the grid'''

    options_dte = filter_options(options, snap, exp)
    if options_dte is None: # empty filtered options data
        # print(f"No options data for snapshot date: {snap} and expiry date: {exp}")
        return

    t = dte / 365 # dte in trading days
    q = get_dividend(snap, exp, dividends, spots) # quarterly dividends

    strikes = sorted(options_dte['strike'].unique())
    grid = []

    for k in strikes:

        s = get_spot_price(spots, snap)
        c = get_call_price(options_dte, k)
        p = get_put_price(options_dte, k)
        f = s * math.exp((r - q) * t) # forward

        if s is None:
            print(f"Spot price not found on {snap}")
            continue 

        if r is None:
            print(f"Rate not found on {snap}")
            continue

        if k > s: # OTM call
            if c is None:
                if p is None:  # both call and puts do not exist
                    continue
                else: # put exists but call doesnt, use put call parity
                    final_c = p + math.exp(-r * t) * (f - k)
            else:    
                final_c = c

        else: # OTM put
            if p is None: 
                if c is None:  # both call and puts do not exist
                    continue
                else: # call exists but put doesnt, directly add call
                    final_c = c
            else: # put call parity for call price   
                c = p + math.exp(-r * t) * (f - k)
                final_c = c

        # no arbitrage: non-neg, > intrinsic value, <=s, 
        if final_c <= 0 or final_c < max(0, s - k) or final_c > s:
            continue # skip current iteration as arbitrage exists

        if mono_convex(grid, k, final_c): # pass monotonicity and convexity tests
            grid.append((k,final_c))
    
    if len(grid) < 8: # reject grids with less than 8 points
        return
    
    calls_arr = np.array([c for k, c in grid])
    
    # Determine appropriate window size for Savitzky-Golay based on grid size
    sg_window = min(11, len(calls_arr) - 1 if len(calls_arr) % 2 == 1 else len(calls_arr) - 2)
    sg_window = max(5, sg_window)
    if sg_window % 2 == 0:
        sg_window -= 1
    
    # Smooth the call curve with Savitzky-Golay (polyorder=2 preserves convexity)
    calls_smoothed = savgol_filter(calls_arr, window_length=sg_window, polyorder=2)
    
    # Calculate residuals: how far each point deviates from the smoothed trend
    residuals = calls_arr - calls_smoothed
    outlier_threshold = 1.5 * np.std(residuals)
    
    # Identify outliers: points with residuals > 1.5 standard deviations
    outlier_mask = np.abs(residuals) > outlier_threshold
    
    # Filter grid to remove outliers
    grid = [pair for i, pair in enumerate(grid) if not outlier_mask[i]]
    
    # Verify we still have minimum grid points after outlier removal
    if len(grid) < 8:
        return

    return grid


def func(grid):     
    '''Returns smoothened function C(K) with pre-filtering'''
    if len(grid) < 5: #. reject less than 5 points for Savitzky, window < data length
        return
    
    strikes = np.array([pair[0] for pair in grid])
    calls = np.array([pair[1] for pair in grid])

    # ensure sorted
    idx = np.argsort(strikes)
    strikes = strikes[idx]
    calls = calls[idx]

    #  window_length: must be odd and < len(calls)
    #  Use min(len(calls)-1, 7) to ensure odd, adapt to small grids
    #  polyorder: polynomial order for local fitting (2 or 3)
    #  Order 2 = quadratic, preserves convexity better
    
    if len(calls) >= 5:
        # ADAPTIVE WINDOW SIZING STRATEGY
        # Proportional window based on grid size to avoid over/under-smoothing
        
        if len(calls) < 8:
            # Very small grid (5-7 points): use minimal smoothing (window=5)
            # Reason: Can't afford to lose structure; risk of severe over-smoothing
            window = 5
        elif len(calls) < 20:
            # Small-medium grid (8-19 points): use proportional window
            # Aim for ~45% of data (0.45 coefficient balances smoothing vs structure preservation)
            window = int(len(calls) * 0.45)
        else:
            # Large grid (20+ points): use proportional smoothing
            # Aim for ~40% of data (0.40 coefficient allows more aggressive smoothing on larger datasets)
            window = int(len(calls) * 0.40)
        
        # Ensure window is odd (required by Savitzky-Golay filter)
        if window % 2 == 0:
            window -= 1
        
        # Ensure minimum window size of 3 (Savitzky-Golay requires at least polyorder+2)
        window = max(3, window)
        
        # polyorder must be strictly less than window_length
        # Dynamically adjust polyorder based on window size to avoid savgol_filter errors
        # Default to polyorder=3 if possible, otherwise reduce to fit within window constraint
        polyorder = min(3, window - 1)  # polyorder < window_length is required
        polyorder = max(1, polyorder)   # Ensure at least polyorder=1 (linear smoothing)
        
        calls_smoothed = savgol_filter(calls, window_length=window, polyorder=polyorder)
        
    else:
        # otherwise too few points
        calls_smoothed = calls
    
    # Interpolate through smoothed points, not raw points
    return PchipInterpolator(strikes, calls_smoothed, extrapolate=False)

def bl(grid, curve, rate, dte):
    '''
    Returns a tuple of (strikes, RND) based on Breeden-Litzenberger
    If curve does not exist, return None
    If density cannot be normalised, return None
    '''
    if curve is None:
        return 
    
    r = rate
    t = dte / 365

    strikes = [pair[0] for pair in grid]
    strikes = np.array(strikes) # convert to array

    # linearly spaced grid for plotting and integration
    linear_strikes = np.linspace(strikes.min(), strikes.max(), 250)

    second_order = curve(linear_strikes, 2) 
    
    if np.any(second_order < 0): # floor in case of negative second order
        second_order = np.maximum(second_order, 0)
    rnd = np.exp(r * t) * second_order # bl func

    total = np.trapezoid(rnd, linear_strikes) # normalise as intgeral = 1 since BL is a PDF
    if total <= 0: # cannot normalise
        return
    
    rnd = rnd / total
    
    rnd_weights = rnd / np.sum(rnd) # normalised RND to use as KDE weights
    
    # Create KDE object: uses Gaussian kernels centered at each strike point
    # Bandwidth ('scott') is the default method for determining optimal bandwith
    kde_obj = gaussian_kde(linear_strikes, weights=rnd_weights)
    
    # Evaluate KDE at all strike points to get smooth density
    rnd = kde_obj(linear_strikes)
    rnd = np.maximum(rnd, 0)  # Floor to zero (KDE can produce tiny negatives due to floating point)
    
    # Normalise again to ensure integral = 1 to maintain PDF property
    total = np.trapezoid(rnd, linear_strikes)
    if total <= 0:
        return
    rnd = rnd / total

    return (tuple(linear_strikes), tuple(rnd))