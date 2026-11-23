"""Tables, figures and SUMMARY.md for bpm_evaluate.py."""
import csv
import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot
import numpy
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

from hfs import filters
from hfs.recordings import RECORDING_NAMES, STUDY_DIRECTORY

RESULTS_DIRECTORY = STUDY_DIRECTORY / "results"
FIGURES_DIRECTORY = RESULTS_DIRECTORY / "figures"
BACKGROUND = "#0f1419"
FOREGROUND = "#e6e6e6"
GRID = "#2a323c"
PALETTE = ["#4cc9f0", "#ff6b9a", "#ffd166", "#06d6a0", "#ff8c42", "#b388ff", "#90be6d", "#c0c0c0"]
BASELINE_IDENTIFIERS = ("raw", "butterworth_hp2_25_lp2_150", "butterworth_hp2_40_lp2_800")
BASELINE_NAMES = {"raw": "Raw (no filter)", "butterworth_hp2_25_lp2_150": "design BPM 25-150 Hz Butterworth 2+2",
                  "butterworth_hp2_40_lp2_800": "design Murmur 40-800 Hz Butterworth 2+2"}


def style_axes(axes):
    axes.set_facecolor(BACKGROUND)
    for spine in axes.spines.values():
        spine.set_color(GRID)
    axes.tick_params(colors=FOREGROUND, which="both")
    axes.xaxis.label.set_color(FOREGROUND)
    axes.yaxis.label.set_color(FOREGROUND)
    axes.title.set_color(FOREGROUND)
    axes.grid(True, color=GRID, linewidth=0.6)


def new_figure(width, height, rows=1, columns=1, **keywords):
    figure, axes = pyplot.subplots(rows, columns, figsize=(width, height), facecolor=BACKGROUND, **keywords)
    for single in numpy.atleast_1d(axes).ravel():
        style_axes(single)
    return figure, axes


def frequency_label(value, _position=None):
    if value >= 1000:
        return f"{value / 1000:g} kHz"
    return f"{value:g} Hz"


def format_frequency_axis(axes, low, high):
    axes.set_xscale("log")
    ticks = [value for value in (5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 8000) if low <= value <= high]
    axes.xaxis.set_major_locator(FixedLocator(ticks))
    axes.xaxis.set_major_formatter(FuncFormatter(frequency_label))
    axes.xaxis.set_minor_locator(NullLocator())
    axes.set_xlim(low, high)


def save(figure, name):
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURES_DIRECTORY / name, dpi=130, facecolor=BACKGROUND, bbox_inches="tight")
    pyplot.close(figure)


def write_csv(path, rows):
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: (f"{value:.4g}" if isinstance(value, float) else value) for key, value in row.items()})


def label_of(identifier, estimator_key):
    name = BASELINE_NAMES.get(identifier, identifier)
    return name if estimator_key == "default" else f"{name} [{estimator_key}]"


def number(value, digits=1):
    return "n/a" if value is None or (isinstance(value, float) and not numpy.isfinite(value)) else f"{value:.{digits}f}"


def percent(value):
    return "n/a" if value is None or not numpy.isfinite(value) else f"{100 * value:.0f} %"


def write_outputs(*, rows, final_ranked, stage_one_ranked, listening_rows, arrays_by_key, all_specs, best_configuration,
                  variant_gain, stage_three_configurations, provisional, reference_directory, bootstrap, ranking_key,
                  top_filters, build_candidate, estimator_cost):
    import bpm_evaluate as evaluation

    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    configuration_by_key = {}
    for (identifier, configuration) in rows:
        configuration_by_key[configuration.key()] = configuration
    write_csv(RESULTS_DIRECTORY / "bpm_filter_grid.csv", sorted(rows.values(), key=ranking_key))
    write_csv(RESULTS_DIRECTORY / "bpm_listening_filters_as_analysis.csv", sorted(listening_rows, key=ranking_key))

    best_row = final_ranked[0]
    per_window_keys = []
    for row in final_ranked:
        key = (row["identifier"], configuration_by_key[row["estimator"]])
        if key not in per_window_keys:
            per_window_keys.append(key)
        if len(per_window_keys) >= 20:
            break
    for identifier in BASELINE_IDENTIFIERS:
        for configuration in dict.fromkeys([evaluation.DEFAULT_ESTIMATOR, best_configuration]):
            if (identifier, configuration) in arrays_by_key and (identifier, configuration) not in per_window_keys:
                per_window_keys.append((identifier, configuration))
    per_window_rows = []
    for identifier, configuration in per_window_keys:
        arrays = arrays_by_key[(identifier, configuration)]
        for name in RECORDING_NAMES:
            data = arrays[name]
            for index in range(data["end_time"].size):
                per_window_rows.append({"identifier": identifier, "estimator": configuration.key(), "recording": name,
                                        "end_time_s": int(data["end_time"][index]), "reference_bpm": round(float(data["reference"][index]), 2),
                                        "reference_reliable": bool(data["reliable"][index]),
                                        "estimate": round(float(data["estimate"][index]), 2), "valid": bool(data["valid"][index]),
                                        "quality": round(float(data["quality"][index]), 4)})
    write_csv(RESULTS_DIRECTORY / "bpm_per_window.csv", per_window_rows)

    keys_ranked = [(row["identifier"], configuration_by_key[row["estimator"]]) for row in final_ranked]
    best_key = keys_ranked[0]
    bootstrap_keys = keys_ranked[:150]
    baseline_keys = [(identifier, configuration) for identifier in BASELINE_IDENTIFIERS
                     for configuration in dict.fromkeys([evaluation.DEFAULT_ESTIMATOR, best_configuration])
                     if (identifier, configuration) in arrays_by_key]
    intervals = bootstrap(arrays_by_key, best_key, list(dict.fromkeys(bootstrap_keys + baseline_keys)))
    indistinguishable = [key for key in bootstrap_keys if intervals[key][0] <= 0.0]

    def leave_one_out(candidate_keys, design_configuration):
        outcome = []
        for held_out in RECORDING_NAMES:
            training = [name for name in RECORDING_NAMES if name != held_out]
            scores = {key: evaluation.compute_metrics(arrays_by_key[key], training)["reliable_mae_bpm"] for key in candidate_keys}
            chosen = min(scores, key=scores.get)
            held_metrics = evaluation.compute_metrics(arrays_by_key[chosen], [held_out])
            oracle = min(candidate_keys, key=lambda key: evaluation.compute_metrics(arrays_by_key[key], [held_out])["reliable_mae_bpm"])
            design = evaluation.compute_metrics(arrays_by_key[("butterworth_hp2_25_lp2_150", design_configuration)], [held_out])
            outcome.append({"held_out": held_out, "chosen": label_of(chosen[0], chosen[1].key()),
                            "training_mae": scores[chosen], "held_out_mae": held_metrics["reliable_mae_bpm"],
                            "held_out_tolerance": held_metrics["reliable_within_tolerance_share"],
                            "oracle_mae": evaluation.compute_metrics(arrays_by_key[oracle], [held_out])["reliable_mae_bpm"],
                            "design_mae": design["reliable_mae_bpm"]})
        return outcome

    stage_one_keys = [(row["identifier"], evaluation.DEFAULT_ESTIMATOR) for row in stage_one_ranked]
    leave_one_out_filters = leave_one_out(stage_one_keys, evaluation.DEFAULT_ESTIMATOR)
    leave_one_out_final = leave_one_out(keys_ranked, best_configuration)
    every_key = [(row["identifier"], configuration_by_key[row["estimator"]]) for row in sorted(rows.values(), key=ranking_key)]
    leave_one_out_all = leave_one_out(every_key, best_configuration)

    draw_heatmap(rows, evaluation, best_configuration, "bpm_heatmap_edges.png")
    draw_heatmap(rows, evaluation, evaluation.DEFAULT_ESTIMATOR, "bpm_heatmap_edges_default_estimator.png")
    draw_family_order(rows, evaluation, best_configuration, "bpm_family_order.png")
    draw_family_order(rows, evaluation, evaluation.DEFAULT_ESTIMATOR, "bpm_family_order_default_estimator.png")
    draw_tracks(arrays_by_key, best_key, evaluation)
    distinct_best = list(dict.fromkeys(row["identifier"] for row in final_ranked if "limit" not in row["identifier"]))[:5]
    draw_responses(distinct_best, all_specs, build_candidate)

    write_summary(rows=rows, final_ranked=final_ranked, stage_one_ranked=stage_one_ranked, listening_rows=listening_rows,
                  best_configuration=best_configuration, variant_gain=variant_gain, provisional=provisional,
                  reference_directory=reference_directory, intervals=intervals, indistinguishable=indistinguishable,
                  leave_one_out_filters=leave_one_out_filters, leave_one_out_all=leave_one_out_all, leave_one_out_final=leave_one_out_final,
                  ranking_key=ranking_key, all_specs=all_specs, build_candidate=build_candidate,
                  stage_three_configurations=stage_three_configurations, evaluation=evaluation, arrays_by_key=arrays_by_key,
                  best_key=best_key, top_filters=top_filters, baseline_keys=baseline_keys)


def draw_heatmap(rows, evaluation, configuration_shown, file_name):
    highpass_edges = evaluation.HIGHPASS_EDGES
    lowpass_edges = evaluation.LOWPASS_EDGES
    values = numpy.full((len(highpass_edges), len(lowpass_edges)), numpy.nan)
    tolerance = numpy.full(values.shape, numpy.nan)
    for (identifier, configuration), row in rows.items():
        if configuration != configuration_shown or row["family"] not in ("butterworth", "raw") or row["input_limit"]:
            continue
        if row["family"] == "butterworth" and (row["highpass_order"] not in (0, 2) or row["lowpass_order"] not in (0, 2)):
            continue
        highpass = row["highpass_hz"] if row["highpass_hz"] != "" else None
        lowpass = row["lowpass_hz"] if row["lowpass_hz"] != "" else None
        if highpass not in highpass_edges or lowpass not in lowpass_edges:
            continue
        values[highpass_edges.index(highpass), lowpass_edges.index(lowpass)] = row["reliable_mae_bpm"]
        tolerance[highpass_edges.index(highpass), lowpass_edges.index(lowpass)] = row["reliable_within_tolerance_share"]
    figure, axes = new_figure(11, 6.2)
    image = axes.imshow(values, cmap="viridis_r", aspect="auto", origin="lower", vmin=numpy.nanmin(values),
                        vmax=min(numpy.nanmax(values), numpy.nanmin(values) * 6 + 1))
    axes.grid(False)
    for row_index in range(values.shape[0]):
        for column_index in range(values.shape[1]):
            if numpy.isfinite(values[row_index, column_index]):
                axes.text(column_index, row_index, f"{values[row_index, column_index]:.1f}\n{100 * tolerance[row_index, column_index]:.0f}%",
                          ha="center", va="center", fontsize=7, color="#0f1419" if values[row_index, column_index] < numpy.nanmedian(values) else FOREGROUND)
    axes.set_xticks(range(len(lowpass_edges)), ["none" if edge is None else frequency_label(edge) for edge in lowpass_edges])
    axes.set_yticks(range(len(highpass_edges)), ["none" if edge is None else frequency_label(edge) for edge in highpass_edges])
    axes.set_xlabel("low-pass edge (order 2)")
    axes.set_ylabel("high-pass edge (order 2)")
    axes.set_title(f"MAE (BPM) and share within tolerance, Butterworth 2+2, estimator [{configuration_shown.key()}], reliable windows", fontsize=9)
    colorbar = figure.colorbar(image, ax=axes)
    colorbar.set_label("MAE (BPM)", color=FOREGROUND)
    colorbar.ax.tick_params(colors=FOREGROUND)
    save(figure, file_name)


def draw_family_order(rows, evaluation, configuration_shown, file_name):
    order_pairs = evaluation.ORDER_PAIRS_OTHER_FAMILIES
    families = ["butterworth", "bessel", "chebyshev1", "chebyshev2", "elliptic", "decimated"]
    figure, axes = new_figure(11, 5.5)
    width = 0.13
    for family_index, family in enumerate(families):
        best_values, design_values = [], []
        for highpass_order, lowpass_order in order_pairs:
            matching = [row for (identifier, configuration), row in rows.items()
                        if configuration == configuration_shown and row["family"] == family and not row["input_limit"]
                        and row["highpass_order"] == highpass_order and row["lowpass_order"] == lowpass_order
                        and row["highpass_hz"] != "" and row["lowpass_hz"] != "" and 15 <= row["highpass_hz"] <= 60
                        and 100 <= row["lowpass_hz"] <= 300]
            best_values.append(min((row["reliable_mae_bpm"] for row in matching), default=numpy.nan))
            design = [row["reliable_mae_bpm"] for row in matching if row["highpass_hz"] == 25 and row["lowpass_hz"] == 150]
            design_values.append(design[0] if design else numpy.nan)
        positions = numpy.arange(len(order_pairs)) + (family_index - 2.5) * width
        axes.bar(positions, best_values, width * 0.9, color=PALETTE[family_index], label=f"{family}: best edges")
        axes.scatter(positions, design_values, color=FOREGROUND, marker="_", s=120, zorder=3,
                     label="at 25-150 Hz" if family_index == 0 else None)
    fir_rows = [row for row in rows.values() if row["family"] == "fir" and row["estimator"] == configuration_shown.key()]
    if fir_rows:
        axes.axhline(min(row["reliable_mae_bpm"] for row in fir_rows), color=PALETTE[7], linestyle="--",
                     label="best FIR (65-257 taps, any edges)")
    axes.set_xticks(range(len(order_pairs)), [f"HP {pair[0]} + LP {pair[1]}" for pair in order_pairs])
    axes.set_ylabel("MAE (BPM), reliable windows")
    axes.set_title(f"Best MAE per family and order (edges HP 15-60 Hz, LP 100-300 Hz), estimator [{configuration_shown.key()}]", fontsize=9)
    legend = axes.legend(facecolor=BACKGROUND, edgecolor=GRID, fontsize=8, ncol=2)
    for text in legend.get_texts():
        text.set_color(FOREGROUND)
    save(figure, file_name)


def draw_tracks(arrays_by_key, best_key, evaluation):
    series = [(best_key, f"best: {best_key[0]}, final estimator", PALETTE[0], "-")]
    for index, identifier in enumerate(BASELINE_IDENTIFIERS):
        key = (identifier, best_key[1])
        if key != best_key:
            series.append((key, f"{BASELINE_NAMES[identifier]}, final estimator", PALETTE[index + 1], "-"))
    series.append((("raw", evaluation.DEFAULT_ESTIMATOR), "Raw (no filter), default estimator (highest peak)", PALETTE[4], ":"))
    for name in RECORDING_NAMES:
        figure, axes = new_figure(11, 4.5)
        reference_data = arrays_by_key[best_key][name]
        axes.plot(reference_data["end_time"], reference_data["reference"], color=FOREGROUND, linewidth=2.5, label="reference")
        unreliable = ~reference_data["reliable"]
        if unreliable.any():
            axes.scatter(reference_data["end_time"][unreliable], reference_data["reference"][unreliable], s=40,
                         facecolors="none", edgecolors=FOREGROUND, label="reference marked unreliable")
        for key, label, colour, line_style in series:
            data = arrays_by_key[key][name]
            axes.plot(data["end_time"], data["estimate"], line_style, color=colour, linewidth=1.2, label=label)
            axes.scatter(data["end_time"][data["valid"]], data["estimate"][data["valid"]], color=colour, s=10)
            axes.scatter(data["end_time"][~data["valid"]], data["estimate"][~data["valid"]], color=colour, s=28, marker="x")
        axes.set_xlabel("end of 8 s window (s from file start)")
        axes.set_ylabel("heart rate (BPM)")
        axes.set_title(f"{name}: reference and causal on-device estimates (x = estimator marked the window invalid)\n"
                       f"final estimator: {best_key[1].key()}", fontsize=10)
        legend = axes.legend(facecolor=BACKGROUND, edgecolor=GRID, fontsize=7, loc="best")
        for text in legend.get_texts():
            text.set_color(FOREGROUND)
        save(figure, f"bpm_tracks_{name}.png")


def draw_responses(identifiers, all_specs, build_candidate):
    frequencies = numpy.geomspace(5, 8000, 1500)
    figure, axes = new_figure(11, 5.5)
    shown = list(dict.fromkeys(identifiers + [identifier for identifier in BASELINE_IDENTIFIERS if identifier != "raw"]))
    for index, identifier in enumerate(shown):
        candidate = build_candidate(all_specs[identifier])
        response = filters.frequency_response(candidate, frequencies)
        magnitude = 20 * numpy.log10(numpy.maximum(numpy.abs(response), 1e-6))
        style = "--" if identifier in BASELINE_IDENTIFIERS else "-"
        axes.plot(frequencies, magnitude, style, color=PALETTE[index % len(PALETTE)], label=BASELINE_NAMES.get(identifier, identifier))
    format_frequency_axis(axes, 5, 8000)
    axes.set_ylim(-60, 5)
    axes.set_xlabel("frequency")
    axes.set_ylabel("magnitude (dB)")
    axes.set_title("Magnitude responses of the best BPM filters and the design baselines (float32 coefficients)")
    legend = axes.legend(facecolor=BACKGROUND, edgecolor=GRID, fontsize=8)
    for text in legend.get_texts():
        text.set_color(FOREGROUND)
    save(figure, "bpm_filter_responses.png")


def metrics_line(row):
    return (f"| {label_of(row['identifier'], row['estimator'])} | {number(row['reliable_mae_bpm'])} | "
            f"{number(row['reliable_median_absolute_error_bpm'])} | {number(row['reliable_bias_bpm'])} | "
            f"{percent(row['reliable_within_tolerance_share'])} | {row['reliable_gross_error_count']} | "
            f"{percent(row['reliable_valid_share'])} | {number(row['reliable_valid_mae_bpm'])} | "
            f"{number(row['all_mae_bpm'])} | {percent(row['all_within_tolerance_share'])} | "
            f"{row['multiplies_per_sample']} | {number(row['estimated_cpu_share_percent'], 2)} % |")


TABLE_HEADER = ("| candidate [estimator variant] | MAE | median AE | bias | within tolerance | gross errors | valid | MAE valid | "
                "MAE all windows | within tolerance all windows | filter multiplies per sample | est. CPU of one core |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")


def write_summary(*, rows, final_ranked, stage_one_ranked, listening_rows, best_configuration, variant_gain, provisional,
                  reference_directory, intervals, indistinguishable, leave_one_out_filters, leave_one_out_all, leave_one_out_final, ranking_key,
                  all_specs, build_candidate, stage_three_configurations, evaluation, arrays_by_key, best_key, top_filters, baseline_keys):
    best_row = final_ranked[0]
    best_candidate = build_candidate(all_specs[best_row["identifier"]])
    lines = [f"# BPM filter evaluation: summary", "",
             f"Generated {datetime.datetime.now().isoformat(timespec='minutes')} by `src/bpm_evaluate.py --reference {reference_directory.name}`.", ""]
    if provisional:
        lines += ["> **PROVISIONAL REFERENCE.** These numbers use `cache/provisional_reference/`, a zero-phase 25-150 Hz envelope",
                  "> autocorrelation that shares the method under test. It favours 25-150 Hz filters. Do not draw conclusions.", ""]
    else:
        lines += [f"Reference: `{reference_directory}` (independent beat reference, other agent). "
                  "Metrics are on windows the reference marks `reliable` unless a column says \"all windows\".", ""]
    reliable_count = best_row["reliable_window_count"]
    all_count = best_row["all_window_count"]
    lines += [f"Windows: {all_count} (8 s, ending at each full second 10-60 s, 5 recordings), {reliable_count} marked reliable. "
              "Windows overlap by 7 s: about 7 independent windows per recording, 35 in total.", "",
              "Ranking metric: mean absolute error (MAE) of the raw per-window estimate on reliable windows, validity ignored; "
              "ties broken by the share within tolerance max(5 BPM, 10 %). Gross error: more than 20 % off.", ""]

    lines += ["## Answer", ""]
    design_row = rows[("butterworth_hp2_25_lp2_150", evaluation.DEFAULT_ESTIMATOR)]
    design_best = rows.get(("butterworth_hp2_25_lp2_150", best_configuration))
    lines += [f"Best combination: **{label_of(best_row['identifier'], best_row['estimator'])}**, MAE {number(best_row['reliable_mae_bpm'])} BPM, "
              f"{percent(best_row['reliable_within_tolerance_share'])} within tolerance, {best_row['reliable_gross_error_count']} gross errors, "
              f"{percent(best_row['reliable_valid_share'])} valid.",
              f"Final estimator [{best_configuration.key()}] chosen as the stage-3 configuration with the lowest mean MAE over the top "
              f"{len(top_filters)} filters and the 3 baselines (then fewest gross errors), then run over all filters (stage 4).",
              f"Design candidate BPM 25-150 Hz Butterworth 2+2 with the default estimator: MAE {number(design_row['reliable_mae_bpm'])} BPM, "
              f"{percent(design_row['reliable_within_tolerance_share'])} within tolerance"
              + (f"; with the best estimator variant: MAE {number(design_best['reliable_mae_bpm'])} BPM, "
                 f"{percent(design_best['reliable_within_tolerance_share'])} within tolerance." if design_best else "."),
              f"Candidates statistically indistinguishable from the best (moving-block bootstrap, 8-window blocks, 95 % interval of the "
              f"MAE difference includes 0, among the top 150 rows): **{len(indistinguishable)}**.", ""]
    cheapest = min((rows[key_pair] for key_pair in [(identifier, configuration) for identifier, configuration in indistinguishable]),
                   key=lambda row: (row["multiplies_per_sample"], row["reliable_mae_bpm"]))
    lines += [f"Cheapest candidate within noise of the best: **{label_of(cheapest['identifier'], cheapest['estimator'])}**, "
              f"{cheapest['multiplies_per_sample']} multiplies per sample, MAE {number(cheapest['reliable_mae_bpm'])} BPM.", "",
              "Bootstrap 95 % interval of MAE(candidate) - MAE(best) in BPM for the baselines (interval above 0 = worse than the best beyond noise):", "",
              "| baseline | MAE | interval |", "| --- | --- | --- |"]
    for key_pair in baseline_keys:
        low, high = intervals[key_pair]
        lines.append(f"| {label_of(key_pair[0], key_pair[1].key())} | {number(rows[key_pair]['reliable_mae_bpm'], 2)} | {low:+.2f} ... {high:+.2f} |")
    lines += ["", "Quality threshold (normalised autocorrelation peak) versus valid share and accuracy on valid windows (reliable windows):", "",
              "| candidate | threshold | valid share | MAE valid | within tolerance valid | gross errors valid |", "| --- | --- | --- | --- | --- | --- |"]
    for key_pair in [best_key, ("butterworth_hp2_25_lp2_150", evaluation.DEFAULT_ESTIMATOR), ("raw", evaluation.DEFAULT_ESTIMATOR)]:
        data = arrays_by_key[key_pair]
        reference_values = numpy.concatenate([data[name]["reference"][data[name]["reliable"]] for name in RECORDING_NAMES])
        estimate_values = numpy.concatenate([data[name]["estimate"][data[name]["reliable"]] for name in RECORDING_NAMES])
        quality_values = numpy.concatenate([data[name]["quality"][data[name]["reliable"]] for name in RECORDING_NAMES])
        for threshold in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
            accepted = quality_values >= threshold
            error = numpy.abs(estimate_values - reference_values)[accepted]
            reference_accepted = reference_values[accepted]
            lines.append(f"| {label_of(key_pair[0], key_pair[1].key())} | {threshold:.1f} | {percent(accepted.mean())} | "
                         f"{number(error.mean() if error.size else float('nan'))} | "
                         f"{percent((error <= numpy.maximum(5, 0.1 * reference_accepted)).mean() if error.size else float('nan'))} | "
                         f"{int(numpy.count_nonzero(error > 0.2 * reference_accepted))} |")
        lines.append(f"| (quality range {quality_values.min():.2f}-{quality_values.max():.2f}, median {numpy.median(quality_values):.2f}) | | | | | |")

    raw_default = rows[("raw", evaluation.DEFAULT_ESTIMATOR)]
    raw_final = rows[("raw", best_configuration)]
    design_final = rows[("butterworth_hp2_25_lp2_150", best_configuration)]
    murmur_final = rows[("butterworth_hp2_40_lp2_800", best_configuration)]
    final_values = numpy.array([row["reliable_mae_bpm"] for row in final_ranked])
    final_all_values = numpy.array([row["all_mae_bpm"] for row in final_ranked])
    lines += ["## Findings in plain words", "",
              f"1. **The estimator matters more than the filter.** The default estimator (highest autocorrelation peak) picks the "
              f"sub-harmonic (half rate, the peak at two cycles) in a few windows; the half-lag check plus a smoother envelope "
              f"(two cascaded one-pole low-passes at 5 Hz) leaves no gross error on the reliable windows for "
              f"{sum(1 for row in final_ranked if row['reliable_gross_error_count'] == 0)} of {len(final_ranked)} filters; the exceptions all have a "
              f"high-pass at {', '.join(sorted({f'{row[chr(104) + "ighpass_hz"]:g} Hz' for row in final_ranked if row['reliable_gross_error_count'] > 0}))}"
              f" (worst: {max(final_ranked, key=lambda row: row['reliable_mae_bpm'])['identifier']}, MAE "
              f"{number(max(row['reliable_mae_bpm'] for row in final_ranked), 2)} BPM). "
              f"Design BPM filter: MAE {number(design_row['reliable_mae_bpm'], 2)} -> {number(design_final['reliable_mae_bpm'], 2)} BPM; "
              f"Raw: {number(raw_default['reliable_mae_bpm'], 2)} -> {number(raw_final['reliable_mae_bpm'], 2)} BPM.",
              f"2. **With the final estimator the BPM filter choice is within noise on reliable windows.** Median MAE over all filters "
              f"{numpy.median(final_values):.2f} BPM, 10th-90th percentile {numpy.percentile(final_values, 10):.2f}-{numpy.percentile(final_values, 90):.2f} BPM; "
              f"{len(indistinguishable)} of the top 150 rows are inside the bootstrap noise of the best. The best filters, the design filters and even Raw meet the "
              f"project targets (MAE <= 5 BPM, >= 90 % valid, each window within max(5 BPM, 10 %)) on these recordings.",
              f"3. **What does separate filters is the artefact windows** (movement in rest-1 at 39-40 s, start of elevated-1), which the "
              f"reference marks unreliable. On all windows Raw has MAE {number(raw_final['all_mae_bpm'], 2)} BPM, the design BPM filter "
              f"{number(design_final['all_mae_bpm'], 2)}, the design Murmur filter {number(murmur_final['all_mae_bpm'], 2)}, the best "
              f"{number(best_row['all_mae_bpm'], 2)} (median over filters {numpy.median(final_all_values):.2f}). A high-pass of about 25-40 Hz, "
              f"preferably steeper (order 3-4 at 30 Hz), rejects the low-frequency movement energy; the low-pass edge (60 Hz to none) hardly matters. "
              f"This rests on two artefact events, so it is a plausible mechanism, not a proven ranking.",
              "4. Robust: Raw fails on artefact windows; a steep high-pass at 60 Hz or above causes half-rate errors (it removes most of the "
              "low-frequency S1 energy); square and Shannon-energy rectification are worse than "
              "absolute value; comb peak choice as implemented is harmful; holding 8 s of filtered audio instead of the envelope buys nothing "
              "(`results/bpm_window_representation.md`). Within noise: family (Butterworth, Bessel, Chebyshev I/II, elliptic), orders, "
              "low-pass edge, input limiters, envelope rate 50-200 Hz.",
              "5. Caveats: one person, five recordings, 35 roughly independent windows; the reference marks beats on a 25-150 Hz Hilbert "
              "envelope, so it is not fully independent of 25-150 Hz analysis filters; the quality threshold 0.3 was set from a noise "
              "argument (about 4 standard deviations of the normalised autocorrelation of a non-periodic envelope with about 200 independent "
              "samples in 8 s), not tuned, and no window fell below it with the final estimator, so the validity rule is untested here.", ""]
    lines += [f"## Top 20 filters with the final estimator [{best_configuration.key()}]", "", TABLE_HEADER]
    lines += [metrics_line(row) for row in final_ranked[:20]]
    lines += ["", f"## Top 10 filters with the final estimator ranked on all windows, including the windows the reference marks unreliable "
              "(artefacts, movement, fast rate change)", "", TABLE_HEADER]
    lines += [metrics_line(row) for row in sorted(final_ranked, key=lambda row: (row["all_mae_bpm"], -row["all_within_tolerance_share"]))[:10]]
    lines += ["", "## Top 10 over all rows (any estimator variant)", "", TABLE_HEADER]
    lines += [metrics_line(row) for row in sorted(rows.values(), key=ranking_key)[:10]]
    lines += ["", "## Baselines", "", TABLE_HEADER]
    for identifier in BASELINE_IDENTIFIERS:
        for configuration in dict.fromkeys([evaluation.DEFAULT_ESTIMATOR, best_configuration]):
            if (identifier, configuration) in rows:
                lines.append(metrics_line(rows[(identifier, configuration)]))
    lines += ["", "## Listening filters as analysis filters", "", TABLE_HEADER]
    lines += [metrics_line(row) for row in sorted(listening_rows, key=ranking_key)]

    lines += ["", "## Per-recording MAE (reliable windows) of the top 10 and the baselines", "",
              "| candidate | " + " | ".join(RECORDING_NAMES) + " | spread (max-min) |", "| --- |" + " --- |" * (len(RECORDING_NAMES) + 1)]
    spread_rows = final_ranked[:10] + [rows[key_pair] for key_pair in baseline_keys]
    for row in spread_rows:
        values = [row.get(f"reliable_{name}_mae_bpm", numpy.nan) for name in RECORDING_NAMES]
        lines.append(f"| {label_of(row['identifier'], row['estimator'])} | " + " | ".join(number(value) for value in values)
                     + f" | {number(numpy.nanmax(values) - numpy.nanmin(values))} |")

    for title, outcome in (("Leave-one-recording-out, filter sweep with the default estimator (clean: nothing tuned on the held-out recording)", leave_one_out_filters),
                           ("Leave-one-recording-out, filter sweep with the final estimator (the estimator itself was chosen on all five)", leave_one_out_final),
                           ("Leave-one-recording-out over all rows (estimator variants were staged on all five recordings, so this is optimistic)", leave_one_out_all)):
        lines += ["", f"## {title}", "", "| held out | chosen on the other four | MAE on the four | MAE held out | within tolerance held out | best possible held out | design BPM filter held out |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for entry in outcome:
            lines.append(f"| {entry['held_out']} | {entry['chosen']} | {number(entry['training_mae'])} | {number(entry['held_out_mae'])} | "
                         f"{percent(entry['held_out_tolerance'])} | {number(entry['oracle_mae'])} | {number(entry['design_mae'])} |")
        lines.append(f"\nMean held-out MAE: {number(numpy.mean([entry['held_out_mae'] for entry in outcome]))} BPM; design BPM filter: "
                     f"{number(numpy.mean([entry['design_mae'] for entry in outcome]))} BPM.")

    stage_two_identifiers = list(dict.fromkeys(top_filters + list(BASELINE_IDENTIFIERS)))
    lines += ["", f"## Estimator variants (stage 2): change of MAE versus the default over the top {len(top_filters)} filters and the 3 baselines", "",
              "| variant | mean MAE change (BPM) | median MAE change (BPM) | gross errors summed over these filters |", "| --- | --- | --- | --- |"]
    for configuration, gain in sorted(variant_gain.items(), key=lambda item: item[1]["mean"]):
        lines.append(f"| {configuration.key()} | {gain['mean']:+.2f} | {gain['median']:+.2f} | {gain['gross_errors']} |")
    lines += ["", "## Estimator configurations of stage 3 over the same filters", "",
              "| estimator | mean MAE | worst filter MAE | gross errors summed | MAE of the design BPM filter | MAE of Raw |", "| --- | --- | --- | --- | --- | --- |"]
    for configuration in stage_three_configurations:
        values = [rows[(identifier, configuration)] for identifier in stage_two_identifiers if (identifier, configuration) in rows]
        if len(values) != len(stage_two_identifiers):
            continue
        lines.append(f"| {configuration.key()} | {number(numpy.mean([row['reliable_mae_bpm'] for row in values]), 2)} | "
                     f"{number(max(row['reliable_mae_bpm'] for row in values), 2)} | {sum(row['reliable_gross_error_count'] for row in values)} | "
                     f"{number(rows[('butterworth_hp2_25_lp2_150', configuration)]['reliable_mae_bpm'], 2)} | "
                     f"{number(rows[('raw', configuration)]['reliable_mae_bpm'], 2)} |")
    lines += ["", "Input limiter before the filter (stage 2, default estimator, top 10 filters and baselines):", "",
              "| candidate | MAE | within tolerance | gross errors |", "| --- | --- | --- | --- |"]
    limiter_rows = sorted([row for row in rows.values() if row["input_limit"]], key=ranking_key)
    for row in limiter_rows[:12]:
        lines.append(f"| {row['identifier']} | {number(row['reliable_mae_bpm'])} | {percent(row['reliable_within_tolerance_share'])} | {row['reliable_gross_error_count']} |")

    family_lines = ["", "## Best per family", "", "| family | estimator | best candidate | MAE | within tolerance | gross errors | multiplies per sample |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for ranked, estimator_name in ((stage_one_ranked, "default"), (final_ranked, "final")):
        for family in ("raw", "butterworth", "bessel", "chebyshev1", "chebyshev2", "elliptic", "fir", "decimated"):
            family_rows = [row for row in ranked if row["family"] == family and not row["input_limit"]]
            if family_rows:
                row = family_rows[0]
                family_lines.append(f"| {family} | {estimator_name} | {row['identifier']} | {number(row['reliable_mae_bpm'])} | "
                                    f"{percent(row['reliable_within_tolerance_share'])} | {row['reliable_gross_error_count']} | {row['multiplies_per_sample']} |")
    lines += family_lines

    cost_values = evaluation.estimator_cost(best_configuration, best_candidate.output_rate_hz, filters.cost(best_candidate))
    filter_cost = filters.cost(best_candidate)
    lines += ["", "## Final best candidate: realisation", "",
              f"- Filter: `{best_candidate.identifier}`: {best_candidate.description}.",
              f"- Estimator: `{best_configuration.key()}` (see `src/hfs/bpm_estimator.py`).",
              f"- Filter cost: {filter_cost['multiplies_per_sample']} multiplies per sample, {filter_cost['state_bytes']} state bytes, "
              f"{filter_cost['coefficient_bytes']} coefficient bytes.",
              f"- Estimator: window {cost_values['window_bytes']} bytes (PSRAM), total estimator RAM {cost_values['estimator_ram_bytes']} bytes, "
              f"{cost_values['autocorrelation_multiplies_per_update']} multiplies per update.",
              f"- Estimated CPU share of one 240 MHz core: {cost_values['estimated_cpu_share_percent']:.2f} % "
              f"(ESTIMATE, not measured: {evaluation.CYCLES_PER_FILTER_MULTIPLY:g} cycles per filter multiply including loads and the "
              f"dependency chain of a biquad, {evaluation.CYCLES_PER_CORRELATION_MULTIPLY:g} cycles per autocorrelation multiply-accumulate, "
              f"{evaluation.CYCLES_PER_LOGARITHM:g} cycles per logf; autocorrelation burst about "
              f"{cost_values['estimated_autocorrelation_milliseconds_per_update']:.1f} ms per update on the BPM worker thread).",
              ""]
    if best_candidate.second_order_sections is not None:
        lines += ["Second-order sections (float32; b0 b1 b2 a0 a1 a2" + (", at 1 kHz after decimation" if best_candidate.family == "decimated" else "") + "):", "", "```"]
        for section in best_candidate.second_order_sections:
            lines.append("{" + ", ".join(f"{value:.9g}f" for value in section) + "},")
        lines += ["```"]
    if best_candidate.fir_coefficients is not None:
        lines += [f"FIR taps: {len(best_candidate.fir_coefficients)} (float32), listed in `results/best_fir_taps.txt`."]
        (RESULTS_DIRECTORY / "best_fir_taps.txt").write_text("\n".join(f"{value:.9g}" for value in best_candidate.fir_coefficients))

    lines += ["", "## Staging and pruning", "",
              f"1. Filter sweep with the default estimator: {len([row for row in rows.values() if row['stage'].startswith('1')])} filters. "
              "Butterworth 2+2 over every high-pass edge (none, 10-80 Hz) x every low-pass edge (60-800 Hz, none) with LP >= 1.5 x HP; "
              "Butterworth full order cross 1-4 x 1-4 on HP 15-60 Hz x LP 80-600 Hz; Bessel, Chebyshev I (0.5 dB), Chebyshev II (40 dB, "
              "edge moved to the -3 dB point) and elliptic (0.5/40 dB) with orders 1+1, 2+2, 4+4, 2+4, 4+2 on HP 15-60 Hz x LP 100-300 Hz; "
              "FIR (Hamming window) 65/129/257 taps; decimated design (64-tap anti-alias FIR, decimation to 1 kHz, Butterworth there).",
              "   Pruned: edge pairs closer than 1.5:1 (pass band too narrow for heart sounds), 3rd-order other families, "
              "other families at 10 Hz and LP > 300 Hz (Butterworth covers those edges).",
              f"2. Estimator variants (one change at a time) and input limiters on the top {len(top_filters)} filters plus the baselines.",
              f"3. Joint confirmation: the improving variants and their pairwise combinations ({len(stage_three_configurations)} configurations) on the same filters.",
              "", "FIR note: at 16 kHz a Hamming-window FIR resolves about 3.3 x 16000 / N Hz of transition width (about 800 Hz at 65 taps, "
              "200 Hz at 257 taps), so a 25 Hz high-pass edge is not realisable with these lengths; the FIR rows behave like low-pass "
              "filters with a weak, wide high-pass, at N multiplies per sample.", ""]
    (RESULTS_DIRECTORY / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
