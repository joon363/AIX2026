import numpy as np
import matplotlib.pyplot as plt
import os

layers = [0, 2, 4, 6, 8, 10, 12, 13, 14, 17]
PERCENTILE = 0.9999
NUM_BINS = 2048

# 폴더 생성
base_dir = "weight_analysis"
hist_orig_dir = os.path.join(base_dir, "hist_original")
hist_wo0_dir = os.path.join(base_dir, "hist_without0")
cdf_dir = os.path.join(base_dir, "cdf")

os.makedirs(hist_orig_dir, exist_ok=True)
os.makedirs(hist_wo0_dir, exist_ok=True)
os.makedirs(cdf_dir, exist_ok=True)

for layer in layers:
    filename = f"weight_layer_{layer}.txt"

    if not os.path.exists(filename):
        print(f"[Layer {layer}] file not found, skipping.")
        continue

    print(f"[Layer {layer}] processing...")

    weights = np.loadtxt(filename)

    counts, bin_edges = np.histogram(weights, bins=NUM_BINS)
    bin_values = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    total = np.sum(counts)
    cumulative = np.cumsum(counts)

    target = total * PERCENTILE
    idx = np.searchsorted(cumulative, target)
    percentile_value = bin_values[min(idx, len(bin_values)-1)]

    print(f"  Total samples: {int(total)}")
    print(f"  99.99% threshold ≈ {percentile_value}")

    # ---------- 원본 Histogram ----------
    plt.figure()
    plt.plot(bin_values, counts)
    plt.axvline(percentile_value, linestyle='--')
    plt.xlabel("Value")
    plt.ylabel("Count")
    plt.title(f"Weight Layer {layer} Histogram")
    out_img = os.path.join(hist_orig_dir, f"weight_hist_layer_{layer}.png")
    plt.savefig(out_img, dpi=300)
    plt.close()

    # ---------- 0번째 bin 제외 Histogram ----------
    bin_values_wo0 = bin_values[1:]
    counts_wo0 = counts[1:]

    plt.figure()
    plt.plot(bin_values_wo0, counts_wo0)
    plt.axvline(percentile_value, linestyle='--')
    plt.xlabel("Value")
    plt.ylabel("Count")
    plt.title(f"Weight Layer {layer} Histogram (without 0)")
    out_img_wo0 = os.path.join(hist_wo0_dir, f"weight_hist_layer_{layer}_without0.png")
    plt.savefig(out_img_wo0, dpi=300)
    plt.close()

    # ---------- CDF ----------
    plt.figure()
    plt.plot(bin_values, cumulative / total)
    plt.axhline(PERCENTILE, linestyle='--')
    plt.axvline(percentile_value, linestyle='--')
    plt.xlabel("Value")
    plt.ylabel("CDF")
    plt.title(f"Weight Layer {layer} CDF")
    out_cdf = os.path.join(cdf_dir, f"weight_cdf_layer_{layer}.png")
    plt.savefig(out_cdf, dpi=300)
    plt.close()

    print(f"  Saved images in weight_analysis/")

print("Done.")