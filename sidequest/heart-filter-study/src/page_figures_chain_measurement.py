"""Figures for the page about the chain measurement of 22 November 2026: the three setups and where the results are usable.

Usage: python src/page_figures_chain_measurement.py
Writes page/figures/run2_chain_measurement_setups.png and page/figures/run2_chain_measurement_valid_ranges.png, each with
a caption fact file <name>.txt. Facts come from chain-measurement-reviews.md.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot
from matplotlib.patches import FancyBboxPatch, Patch, PathPatch, Rectangle, Wedge
from matplotlib.path import Path as DrawingPath
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, NullLocator

from page_figures import (AMBER, BACKGROUND, BLUE, MINT, RED, SECONDARY, SPINE, TEXT, apply_style,
                          hertz_label, save_figure)

BOARD_FACE = "#173326"
TUBE_COLOUR = "#b8433f"
METAL = "#9aa7aa"
DARK_METAL = "#4b5557"
CUSHION = "#6f6a66"
SOUND_COLOUR = AMBER


def draw_ear_cup(axis, centre_x, bottom_y):
    axis.add_patch(FancyBboxPatch((centre_x - 2.1, bottom_y), 4.2, 0.55, boxstyle="round,pad=0,rounding_size=0.25",
                                  facecolor=CUSHION, edgecolor="none"))
    axis.add_patch(Wedge((centre_x, bottom_y + 0.55), 1.95, 0, 180, facecolor="#1d2224", edgecolor=SPINE, linewidth=1.2))
    axis.plot([centre_x - 2.6, centre_x - 1.2], [bottom_y + 2.9, bottom_y + 2.2], color="#1d2224", linewidth=6,
              solid_capstyle="round")
    axis.text(centre_x, bottom_y + 1.25, "headphone\near cup", ha="center", va="center", fontsize=11, color=TEXT,
              linespacing=1.1)
    for offset in (-0.9, 0.0, 0.9):
        axis.annotate("", xy=(centre_x + offset, bottom_y - 0.75), xytext=(centre_x + offset, bottom_y - 0.05),
                      arrowprops={"arrowstyle": "-|>", "color": SOUND_COLOUR, "linewidth": 1.6})
    axis.text(centre_x - 1.15, bottom_y - 0.4, "test\nsound", ha="right", va="center", fontsize=10.5,
              color=SOUND_COLOUR, linespacing=1.05)


def draw_board_with_microphone(axis, left_x, top_y, width):
    axis.add_patch(Rectangle((left_x, top_y - 0.3), width, 0.3, facecolor=BOARD_FACE, edgecolor="#2f5a45", linewidth=1))
    microphone_x = left_x + 0.9
    axis.add_patch(Rectangle((microphone_x - 0.35, top_y), 0.7, 0.22, facecolor=METAL, edgecolor="none"))
    return microphone_x, top_y + 0.22


def draw_table(axis, left_x, right_x, y):
    axis.plot([left_x, right_x], [y, y], color=SECONDARY, linewidth=1.5)


def draw_chest_piece(axis, centre_x, table_y, side):
    """Side view of the chest-piece lying on the table; side is "membrane" or "bell" for the face turned up."""
    if side == "membrane":
        axis.add_patch(Rectangle((centre_x - 1.25, table_y), 2.5, 0.25, facecolor=DARK_METAL, edgecolor="none"))
        axis.add_patch(Rectangle((centre_x - 1.15, table_y + 0.25), 2.3, 0.45, facecolor=METAL, edgecolor="none"))
        axis.add_patch(Rectangle((centre_x - 1.25, table_y + 0.7), 2.5, 0.12, facecolor="#d9e2e3", edgecolor="none"))
        stem_y = table_y + 0.45
        face_y = table_y + 0.82
    else:
        axis.add_patch(Rectangle((centre_x - 1.25, table_y), 2.5, 0.2, facecolor=DARK_METAL, edgecolor="none"))
        axis.add_patch(Rectangle((centre_x - 0.55, table_y + 0.2), 1.1, 0.35, facecolor=METAL, edgecolor="none"))
        bell = DrawingPath([(centre_x - 0.45, table_y + 0.55), (centre_x - 0.85, table_y + 1.05),
                            (centre_x + 0.85, table_y + 1.05), (centre_x + 0.45, table_y + 0.55),
                            (centre_x - 0.45, table_y + 0.55)],
                           [DrawingPath.MOVETO, DrawingPath.LINETO, DrawingPath.LINETO, DrawingPath.LINETO,
                            DrawingPath.CLOSEPOLY])
        axis.add_patch(PathPatch(bell, facecolor=METAL, edgecolor="none"))
        axis.add_patch(Rectangle((centre_x - 0.65, table_y + 0.92), 1.3, 0.13, facecolor="#2a3133", edgecolor="none"))
        stem_y = table_y + 0.38
        face_y = table_y + 1.05
    axis.add_patch(Rectangle((centre_x + 1.15, stem_y - 0.08), 0.5, 0.16, facecolor=METAL, edgecolor="none"))
    return centre_x + 1.65, stem_y, face_y


def draw_tube(axis, start_x, start_y, end_x, end_y):
    path = DrawingPath([(start_x, start_y), (start_x + 1.0, start_y), (start_x + 1.3, start_y + 3.6),
                        (end_x - 0.2, end_y + 2.6), (end_x, end_y + 1.2), (end_x, end_y)],
                       [DrawingPath.MOVETO, DrawingPath.CURVE4, DrawingPath.CURVE4, DrawingPath.CURVE4,
                        DrawingPath.CURVE3, DrawingPath.CURVE3])
    axis.add_patch(PathPatch(path, facecolor="none", edgecolor=TUBE_COLOUR, linewidth=5, capstyle="round"))


def draw_setup(axis, offset_x, letter, caption, chest_piece_side=None):
    table_y = 0.0
    draw_table(axis, offset_x + 0.2, offset_x + 9.8, table_y)
    axis.text(offset_x + 5.0, 6.0, letter, ha="center", va="center", fontsize=22, color=MINT, weight="bold")
    if chest_piece_side is None:
        microphone_x, microphone_top = draw_board_with_microphone(axis, offset_x + 2.6, table_y + 0.3, 5.4)
        axis.add_patch(Rectangle((offset_x + 2.6, table_y), 0.25, 0.3, facecolor=BOARD_FACE, edgecolor="none"))
        axis.add_patch(Rectangle((offset_x + 7.75, table_y), 0.25, 0.3, facecolor=BOARD_FACE, edgecolor="none"))
        draw_ear_cup(axis, microphone_x + 0.2, microphone_top + 0.95)
        axis.text(microphone_x, -0.5, "microphone on the board", ha="center", va="center", fontsize=11,
                  color=SECONDARY)
    else:
        stem_x, stem_y, face_y = draw_chest_piece(axis, offset_x + 2.6, table_y, chest_piece_side)
        draw_ear_cup(axis, offset_x + 2.6, face_y + 0.95)
        microphone_x, microphone_top = draw_board_with_microphone(axis, offset_x + 6.9, table_y + 0.3, 2.8)
        axis.add_patch(Rectangle((offset_x + 6.9, table_y), 0.25, 0.3, facecolor=BOARD_FACE, edgecolor="none"))
        axis.add_patch(Rectangle((microphone_x - 0.28, microphone_top), 0.56, 0.4, facecolor="#e8e8e8",
                                 edgecolor="none"))
        draw_tube(axis, stem_x, stem_y, microphone_x, microphone_top + 0.4)
        side_text = "membrane side up" if chest_piece_side == "membrane" else "bell side up"
        axis.text(offset_x + 3.1, -0.5, f"chest-piece, {side_text}", ha="center", va="center", fontsize=11,
                  color=SECONDARY)
        axis.text(offset_x + 6.55, 4.55, "tube,\nabout 45 cm", ha="center", va="center", fontsize=11,
                  color=TUBE_COLOUR, linespacing=1.1)
        axis.text(microphone_x + 0.35, -0.5, "microphone", ha="center", va="center", fontsize=11, color=SECONDARY)
    axis.text(offset_x + 5.0, -1.4, caption, ha="center", va="center", fontsize=12.5, color=TEXT)


def figure_setups():
    figure, axis = pyplot.subplots(figsize=(15.5, 5.2))
    axis.set_xlim(0, 30)
    axis.set_ylim(-3.0, 6.6)
    axis.set_aspect("equal")
    axis.axis("off")
    setups = [("A", "microphone alone under the ear cup", None),
              ("B", "membrane side + tube + microphone", "membrane"),
              ("C", "bell side + tube + microphone", "bell")]
    for position, (letter, caption, side) in enumerate(setups):
        draw_setup(axis, position * 10.0, letter, caption, side)
        if position:
            axis.plot([position * 10.0, position * 10.0], [-0.8, 6.4], color=SPINE, linewidth=1.2)
    axis.text(15.0, -2.55, "membrane ÷ A and bell ÷ A were meant to give the chest-piece alone; "
              "bell ÷ membrane (C ÷ B) does not need A", ha="center", va="center", fontsize=13, color=AMBER)
    figure.suptitle("The table measurement of 22 November 2026: three arrangements", x=0.02, ha="left", fontsize=16)
    save_figure(figure, "run2_chain_measurement_setups", """
Schematic side view of the three arrangements of the table measurement of 22 November 2026 (facts: chain-measurement-reviews.md,
photos C:/Users/nicop/audio-chain-measurements/2026-11-22/photos/). Drawn, not to scale.
A: a headphone ear cup (Beyerdynamic DT 770 PRO, playing a test sweep from 20 Hz to 8 kHz) lies cushion-down over the
bare microphone (INMP441) at the edge of the board. Caption: "microphone alone under the ear cup".
B: the ear cup lies over the chest-piece, membrane side up, on the table; the sound goes through the tube (about 45 cm,
inferred from the tube resonances) to the microphone held at the tube's end on the board. Caption: "membrane side + tube
+ microphone".
C: as B with the chest-piece turned to its bell side. Caption: "bell side + tube + microphone".
Below all three: "membrane ÷ A and bell ÷ A were meant to give the chest-piece alone; bell ÷ membrane (C ÷ B) does not
need A". The gap between cushion and chest-piece or tube was not sealed; there was no reference microphone.
""")


VALID_RANGE_ROWS = [
    ("membrane ÷ A", [(20, 400, "not usable", "arrangement A had its own dip"),
                      (400, 5500, "usable", ""),
                      (5500, 8000, "not usable", "")]),
    ("bell ÷ A", [(20, 400, "not usable", "arrangement A had its own dip"),
                  (400, 6000, "usable", ""),
                  (6000, 8000, "weak signal", "")]),
    ("bell ÷ membrane\n(C ÷ B, needs no A)", [(20, 25, "weak signal", ""),
                                              (25, 5500, "usable", ""),
                                              (5500, 6000, "doubtful", ""),
                                              (6000, 8000, "weak signal", "")]),
]
RANGE_STYLES = {"usable": {"facecolor": MINT, "alpha": 0.85},
                "not usable": {"facecolor": RED, "alpha": 0.75},
                "weak signal": {"facecolor": "#3a4446", "alpha": 1.0},
                "doubtful": {"facecolor": AMBER, "alpha": 0.7, "hatch": "//", "edgecolor": BACKGROUND}}


def figure_valid_ranges():
    figure, axis = pyplot.subplots(figsize=(13, 5.6))
    axis.set_xscale("log")
    axis.set_xlim(20, 8000)
    axis.set_ylim(-0.75, len(VALID_RANGE_ROWS) - 0.1)
    axis.axvspan(20, 150, color=BLUE, alpha=0.16, linewidth=0)
    axis.text(55, len(VALID_RANGE_ROWS) - 0.32, "where most heart-sound energy lies\nin the own recordings",
              ha="center", va="center", fontsize=11.5, color=BLUE, linespacing=1.1)
    labels = []
    for row_index, (label, segments) in enumerate(VALID_RANGE_ROWS):
        y = len(VALID_RANGE_ROWS) - 1 - row_index
        labels.append((y, label))
        for low, high, state, reason in segments:
            style = dict(RANGE_STYLES[state])
            hatch = style.pop("hatch", None)
            edge = style.pop("edgecolor", "none")
            axis.add_patch(Rectangle((low, y - 0.28), high - low, 0.4, linewidth=0, edgecolor=edge, hatch=hatch,
                                     **style))
            if reason:
                axis.text((low * high) ** 0.5, y - 0.08, reason, ha="center", va="center", fontsize=11,
                          color=BACKGROUND)
    axis.annotate("sound reached the microphone\nthrough the air, not the tube", xy=(6600, 2.13), xytext=(2600, 2.55),
                  ha="center", va="center", fontsize=10.5, color=RED, linespacing=1.1,
                  arrowprops={"arrowstyle": "-", "color": RED, "linewidth": 1})
    axis.annotate("the membrane side's air path\nmay affect this too", xy=(5750, 0.13), xytext=(2400, 0.55),
                  ha="center", va="center", fontsize=10.5, color=AMBER, linespacing=1.1,
                  arrowprops={"arrowstyle": "-", "color": AMBER, "linewidth": 1})
    axis.set_yticks([y for y, _ in labels])
    axis.set_yticklabels([label for _, label in labels], fontsize=12.5, color=TEXT)
    axis.tick_params(axis="y", length=0)
    ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 8000]
    axis.xaxis.set_major_locator(FixedLocator(ticks))
    axis.xaxis.set_major_formatter(FuncFormatter(hertz_label))
    axis.xaxis.set_minor_locator(NullLocator())
    axis.xaxis.set_minor_formatter(NullFormatter())
    axis.set_xlabel("Pitch")
    axis.grid(axis="y", visible=False)
    axis.spines["left"].set_visible(False)
    handles = [Patch(label=state, linewidth=0, **{key: value for key, value in RANGE_STYLES[state].items()})
               for state in ("usable", "not usable", "doubtful", "weak signal")]
    axis.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=4, frameon=False, fontsize=12)
    axis.set_title("Where the chain measurement of 22 November 2026 can be used\n(according to the two independent reviews)",
                   loc="left", fontsize=15)
    save_figure(figure, "run2_chain_measurement_valid_ranges", """
Band chart over pitch (20 Hz to 8 kHz, spaced by ratio) of where the results of the chain measurement of 22 November 2026
are usable according to the two independent reviews (chain-measurement-reviews.md).
membrane ÷ A (B/A): not usable below about 400 Hz (arrangement A had its own dip of about 13 dB at 220 Hz from the ear cushion
resting on the board edge; dividing by A adds about 10-13 dB to the 250 Hz peak); usable 400 Hz to 5.5 kHz; not usable
above about 5.5 kHz (sound reached the microphone through the air 0.5-1 ms before the tube signal).
bell ÷ A (C/A): not usable below about 400 Hz (same reason); usable 400 Hz to about 6 kHz; above about 6 kHz weak signal
(signal-to-noise about 27-68 dB only from 25 Hz to about 6 kHz at -12 dBFS).
bell ÷ membrane (C/B, needs no A): usable with good signal from about 25 Hz to about 6 kHz; the band 5.5-6 kHz is marked
doubtful because the membrane measurement above 5.5 kHz contains the air path (a reading of the reviews by the figure
author, not stated by them for C/B); below 25 Hz and above 6 kHz weak signal.
Blue band 20-150 Hz: where most heart-sound energy lies in the own recordings.
Seat spread (bell and membrane seats 3 and 4 about 2 dB lower broadband, up to 6 dB below 315 Hz) is not shown.
""")


def main():
    apply_style()
    figure_setups()
    figure_valid_ranges()


if __name__ == "__main__":
    main()
