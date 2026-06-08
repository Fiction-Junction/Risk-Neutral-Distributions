import matplotlib.pyplot as plt
import numpy as np
import random

# Import from modules
from src.data_loader import OPTIONS, SPOTS, RATES, DIVIDENDS
from src.dict_generator import gen

N = 5  # Choose the first N snapshot dates. Max is 100.

# Generate RND dictionary
rnd_dict = gen(OPTIONS, SPOTS, RATES, DIVIDENDS, N)

# Select random distribution
key = random.choice(list(rnd_dict.keys()))
snap_date, exp_date = key
entry = rnd_dict[key]

strikes_arr = np.array(entry['density'][0])
rnds_arr = np.array(entry['density'][1])

# Calculate skewness
rnd_mean = np.average(strikes_arr, weights=rnds_arr)
rnd_var = np.average((strikes_arr - rnd_mean)**2, weights=rnds_arr)
rnd_std = np.sqrt(rnd_var)
skewness = np.average((strikes_arr - rnd_mean)**3, weights=rnds_arr) / (rnd_std**3)
dte = entry['dte']

# Plot with professional colormap
color = plt.cm.viridis(0.6)
fig, ax = plt.subplots(figsize=(14, 7))

ax.plot(strikes_arr, rnds_arr, 
        color=color, 
        linewidth=2.5,
        alpha=0.9,
        label=f'DTE={dte}d → {exp_date} (Skew: {skewness:.3f})')

ax.fill_between(strikes_arr, rnds_arr, alpha=0.15, color=color)

# Auto-adjust x-axis based on strikes
strike_min, strike_max = np.min(strikes_arr), np.max(strikes_arr)
margin = (strike_max - strike_min) * 0.1
ax.set_xlim(left=strike_min - margin, right=strike_max + margin)

ax.set_xlabel('Terminal Spot Price at Expiration ($)', fontsize=15, fontweight='bold')
ax.set_ylabel('Risk-Neutral Density', fontsize=15, fontweight='bold')
ax.set_title(f'Randomly generated risk-neutral density distribution\n' +
             f'Snapshot: {snap_date} → Expiration: {exp_date}\n' +
             f'DTE: {dte}d, Skew: {skewness:.4f}',
             fontsize=15, fontweight='bold', pad=15)

ax.grid(True, alpha=0.25, linestyle=':', linewidth=0.8)

plt.tight_layout()
plt.show()


    
