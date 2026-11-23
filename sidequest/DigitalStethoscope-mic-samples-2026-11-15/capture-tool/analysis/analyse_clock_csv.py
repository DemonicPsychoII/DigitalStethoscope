# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=2", "matplotlib>=3.9"]
# ///
"""Edges, periods, pulse widths and levels of Rigol DS1000Z CSV exports of a clock signal, with one picture per file.

Usage: analyse_clock_csv.py <output folder> <csv>...
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy
from matplotlib import pyplot

EXPECTED_BIT_CLOCK_HZ = 16000 * 2 * 32
BACKGROUND, PANEL, TEXT, GRID = "#0f1419", "#161c24", "#d7dde5", "#2a3340"
SIGNAL, MARK, LIMIT = "#7aa2f7", "#f7768e", "#9ece6a"

output_folder = Path(sys.argv[1])
for path in map(Path, sys.argv[2:]):
    lines = path.read_text().splitlines()
    start, increment = (float(value) for value in lines[1].split(",")[2:4])
    volts = numpy.array([float(line.split(",")[1]) for line in lines[2:] if line.strip()])
    times = start + increment * numpy.arange(len(volts))
    low_level, high_level = numpy.percentile(volts, 10), numpy.percentile(volts, 90)
    threshold = (low_level + high_level) / 2
    above = volts > threshold
    crossings = numpy.flatnonzero(above[1:] != above[:-1])
    # Interpolated crossing time between the two samples on either side of the threshold.
    fraction = (threshold - volts[crossings]) / (volts[crossings + 1] - volts[crossings])
    edge_times = times[crossings] + fraction * increment
    rising = above[crossings + 1]
    rising_times, falling_times = edge_times[rising], edge_times[~rising]
    periods = numpy.diff(rising_times)
    high_widths = [f - r for r in rising_times for f in falling_times[falling_times > r][:1]]
    print(f"==== {path.name}: {len(volts)} samples every {increment * 1e9:.0f} ns, {len(volts) * increment * 1e6:.1f} µs")
    print(f"  levels: low {low_level:.2f} V, high {high_level:.2f} V, min {volts.min():.2f} V, max {volts.max():.2f} V")
    print(f"  rising edges {len(rising_times)}, falling edges {len(falling_times)}")
    print(f"  period: mean {periods.mean() * 1e9:.1f} ns ({1 / periods.mean() / 1e6:.4f} MHz, expected "
          f"{EXPECTED_BIT_CLOCK_HZ / 1e6:.3f} MHz), min {periods.min() * 1e9:.1f} ns, max {periods.max() * 1e9:.1f} ns, "
          f"spread {periods.std() * 1e9:.1f} ns")
    print(f"  high time: mean {numpy.mean(high_widths) * 1e9:.1f} ns, duty {numpy.mean(high_widths) / periods.mean() * 100:.1f} %")
    print(f"  longest time without an edge: {numpy.diff(edge_times).max() * 1e9:.0f} ns")

    figure, axes = pyplot.subplots(2, 1, figsize=(12, 7.5), constrained_layout=True, facecolor=BACKGROUND,
                                   gridspec_kw={"height_ratios": (3, 2)})
    for axis in axes:
        axis.set_facecolor(PANEL)
        axis.tick_params(colors=TEXT)
        axis.grid(color=GRID, linewidth=0.5)
        for spine in axis.spines.values():
            spine.set_color(GRID)
    axes[0].plot(times * 1e6, volts, color=SIGNAL, linewidth=0.8)
    axes[0].axhline(threshold, color=MARK, linewidth=0.8, linestyle="--", label=f"threshold {threshold:.2f} V")
    axes[0].set_title(f"{path.name}: clock signal, {increment * 1e9:.0f} ns per sample", color=TEXT)
    axes[0].set_xlabel("Time from trigger (µs)", color=TEXT)
    axes[0].set_ylabel("Voltage (V)", color=TEXT)
    axes[0].legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT, loc="upper right")
    axes[1].plot(rising_times[1:] * 1e6, periods * 1e9, "o-", color=SIGNAL, markersize=4, linewidth=0.8)
    axes[1].axhline(1e9 / EXPECTED_BIT_CLOCK_HZ, color=LIMIT, linewidth=0.8, linestyle="--",
                    label=f"expected {1e9 / EXPECTED_BIT_CLOCK_HZ:.1f} ns (16 kHz × 64)")
    axes[1].set_ylim(0, 2.2e9 / EXPECTED_BIT_CLOCK_HZ)
    axes[1].set_title("Length of every clock period; a gap would show as a much longer period", color=TEXT)
    axes[1].set_xlabel("Time of the rising edge (µs)", color=TEXT)
    axes[1].set_ylabel("Period (ns)", color=TEXT)
    axes[1].legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT, loc="lower right")
    picture = output_folder / f"{path.stem}.png"
    figure.savefig(picture, dpi=100, facecolor=BACKGROUND)
    print("  picture:", picture)
