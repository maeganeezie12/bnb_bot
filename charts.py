import io
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker

RANK_COLORS = ["#FFD700", "#C0C0C0", "#CD7F32"]
DEFAULT_COLOR = "#8B9BB4"


def bar_chart(standings) -> io.BytesIO | None:
    """Bar chart of current standings with catch-up % annotations."""
    if not standings:
        return None

    names = [r[1] for r in standings]
    counts = [r[2] for r in standings]
    leader = counts[0]

    colors = [RANK_COLORS[i] if i < 3 else DEFAULT_COLOR for i in range(len(standings))]

    fig, ax = plt.subplots(figsize=(max(6, len(names) * 1.4), 5))
    bars = ax.bar(names, counts, color=colors, edgecolor="white", linewidth=0.6, zorder=3)

    for i, (bar, row) in enumerate(zip(bars, standings)):
        trophies = row[2]
        if i == 0:
            label = f"{trophies}\n👑"
        else:
            gap = leader - trophies
            pct = gap / leader * 100
            label = f"{trophies}\n-{pct:.1f}%"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(counts) * 0.015,
            label,
            ha="center", va="bottom", fontsize=9, fontweight="bold",
        )

    ax.set_ylabel("Trophies", fontsize=11)
    ax.set_title("Current Standings", fontsize=13, fontweight="bold", pad=14)
    ax.set_ylim(0, max(counts) * 1.22)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=10)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)

    legend_patches = [
        mpatches.Patch(color=RANK_COLORS[0], label="1st"),
        mpatches.Patch(color=RANK_COLORS[1], label="2nd"),
        mpatches.Patch(color=RANK_COLORS[2], label="3rd"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", fontsize=8)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    buf.seek(0)
    return buf


def trend_chart(summaries) -> io.BytesIO | None:
    """Line chart of trophy counts across the last N summaries. Needs >= 2 data points."""
    if len(summaries) < 2:
        return None

    dates = [s[0][:10] for s in summaries]
    user_series: dict[str, dict[str, int]] = {}

    for posted_at, snap_json in summaries:
        date = posted_at[:10]
        for entry in json.loads(snap_json):
            name = entry["username"]
            user_series.setdefault(name, {})[date] = entry["trophies"]

    fig, ax = plt.subplots(figsize=(max(6, len(user_series) * 1.4), 5))

    for name, series in user_series.items():
        y = [series.get(d) for d in dates]
        ax.plot(dates, y, marker="o", label=name, linewidth=2)
        # annotate last point
        last_y = y[-1]
        if last_y is not None:
            ax.annotate(str(last_y), (dates[-1], last_y),
                        textcoords="offset points", xytext=(6, 0),
                        fontsize=8, va="center")

    ax.set_ylabel("Trophies", fontsize=11)
    ax.set_title("Trophy Trends", fontsize=13, fontweight="bold", pad=14)
    ax.legend(fontsize=9, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=10, integer=True, prune="both"))
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    buf.seek(0)
    return buf
