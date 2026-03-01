import numpy as np
import matplotlib.pyplot as plt
import os

# 자동 처리할 레이어 목록
layers = [0, 2, 4, 6, 8, 10, 12, 13, 14, 17]

PERCENTILE = 0.9999

for layer in layers:
    filename = f"hist_layer_{layer}.txt"

    if not os.path.exists(filename):
        print(f"[Layer {layer}] file not found, skipping.")
        continue

    print(f"[Layer {layer}] processing...")

    data = np.loadtxt(filename)
    bin_values = data[:, 0]
    counts = data[:, 1]

    total = np.sum(counts)
    cumulative = np.cumsum(counts)

    # percentile threshold 계산
    target = total * PERCENTILE
    idx = np.searchsorted(cumulative, target)
    percentile_value = bin_values[min(idx, len(bin_values)-1)]

    print(f"  Total samples: {int(total)}")
    print(f"  99.99% threshold ≈ {percentile_value}")

    # ---------- Histogram (without first bin) ----------
    bin_values_wo_first = bin_values[1:]
    counts_wo_first = counts[1:]

    plt.figure()
    plt.plot(bin_values_wo_first, counts_wo_first)
    plt.axvline(percentile_value, linestyle='--')
    plt.xlabel("Value")
    plt.ylabel("Count")
    plt.title(f"Layer {layer} Histogram (without 0)")
    plt.savefig(f"hist_layer_{layer}_without0.png")
    plt.close()

    out_img = f"hist_layer_{layer}.png"
    plt.savefig(out_img, dpi=300)
    plt.close()

    # ---------- CDF ----------
    plt.figure()
    plt.plot(bin_values, cumulative / total)
    plt.axhline(PERCENTILE, linestyle='--')
    plt.axvline(percentile_value, linestyle='--')
    plt.xlabel("Value")
    plt.ylabel("CDF")
    plt.title(f"Layer {layer} CDF")

    out_cdf = f"cdf_layer_{layer}.png"
    plt.savefig(out_cdf, dpi=300)
    plt.close()

    print(f"  Saved: {out_img}, {out_cdf}")

print("Done.")