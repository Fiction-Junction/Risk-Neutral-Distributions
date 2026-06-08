from src.helpers import get_dte, get_rate
from src.pipeline import build_grid, func, bl

def gen(options, spots, rates, dividends, N):
    # initialising options data
    snaps = sorted(options['snapshot_date'].unique())
    exps = sorted(options['exp_date'].unique())

    # Generate all keys for first N snapshots
    keys = []
    for snap in snaps[:N]:
        for exp in exps:
            dte = get_dte(snap, exp)
            if dte > 64:  # max dte of 64
                break
            keys.append((snap, exp))

    subkeys = ['dte', 'rate', 'grid', 'func', 'density']

    # initialise storage dict keys
    rnd_dict = {key: {subkey: None for subkey in subkeys}
                for key in keys}        
    # format: {(snap, exp): {dte:, rate:, grid:, spline:, density:}}

    print(f"Processing {len(keys)} snapshot-expiration combinations...")

    for snap, exp in keys:
        rnd_dict[(snap, exp)]['dte'] = get_dte(snap, exp)
        rnd_dict[(snap, exp)]['rate'] = get_rate(rates, snap)

    for i, (snap, exp) in enumerate(keys):
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(keys)} combinations...")
        
        entry = rnd_dict[(snap, exp)]
        r = entry['rate']
        dte = entry['dte']

        if r is None:
            continue

        # building grid of strike, call pairs
        grid = build_grid(options, spots, snap, exp, dte, r, dividends)
        if grid is None:
            continue
        else:
            entry['grid'] = grid

        # forming smoothened function
        curve = func(grid)
        entry['func'] = curve

        # BL function
        density = bl(grid, curve, r, dte)
        if density is None:
            continue
        entry['density'] = density

    # remove entries with None values in subdict
    rnd_dict = {
        key: subdict
        for key, subdict in rnd_dict.items()
        if None not in subdict.values()
    }

    return rnd_dict