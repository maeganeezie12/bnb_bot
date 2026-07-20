import io
import json
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

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
        label = name

        present = [d for d in dates if d in series]
        if len(present) >= 2:
            first_date, last_date = present[0], present[-1]
            days = (datetime.strptime(last_date, "%Y-%m-%d") - datetime.strptime(first_date, "%Y-%m-%d")).days
            if days > 0:
                rate = (series[last_date] - series[first_date]) / days
                label = f"{name} ({rate:+.2f}/day)"

        ax.plot(dates, y, marker="o", label=label, linewidth=2)
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


def _days_between(a: datetime, b: datetime) -> float:
    """Fractional day difference (b - a), so crossover math doesn't lose sub-day precision."""
    return (b - a).total_seconds() / 86400


def projection_chart(summaries, horizon_days=60, cap_days=365):
    """Dashed extrapolation of each person's growth rate, marking when they'd overtake the leader.

    Returns (image_buffer, crossovers) where crossovers is a list of
    {"name", "leader", "date", "days"} dicts — one per person mathematically projected
    to catch the leader, regardless of whether that date fits on the visible chart.
    """
    if len(summaries) < 2:
        return None, []

    user_series: dict[str, dict[datetime, int]] = {}
    for posted_at, snap_json in summaries:
        date = datetime.strptime(posted_at[:10], "%Y-%m-%d")
        for entry in json.loads(snap_json):
            user_series.setdefault(entry["username"], {})[date] = entry["trophies"]

    stats = {}
    for name, series in user_series.items():
        pts = sorted(series.items())
        (first_d, first_v), (last_d, last_v) = pts[0], pts[-1]
        days = _days_between(first_d, last_d)
        if days <= 0:
            continue
        stats[name] = {"rate": (last_v - first_v) / days, "last_date": last_d, "last_val": last_v}

    if len(stats) < 2:
        return None, []

    leader_name = max(stats, key=lambda n: stats[n]["last_val"])
    leader = stats[leader_name]
    overall_last_date = max(s["last_date"] for s in stats.values())

    # Compute every crossover exactly (uncapped) so the reported date is always accurate,
    # even if it falls beyond what we're willing to stretch the chart's x-axis to show.
    crossovers = []
    for name, s in stats.items():
        if name == leader_name:
            continue
        dt_leader = _days_between(leader["last_date"], s["last_date"])
        leader_val_at_t = leader["last_val"] + leader["rate"] * dt_leader
        gap = leader_val_at_t - s["last_val"]
        rate_diff = s["rate"] - leader["rate"]
        if rate_diff > 0 and gap > 0:
            days_to_catch = gap / rate_diff
            cross_date = s["last_date"] + timedelta(days=days_to_catch)
            crossovers.append({"name": name, "leader": leader_name, "date": cross_date, "days": days_to_catch})

    visible = [c for c in crossovers if c["days"] <= cap_days]
    horizon_end = overall_last_date + timedelta(days=horizon_days)
    if visible:
        horizon_end = max([horizon_end] + [c["date"] + timedelta(days=3) for c in visible])
        horizon_end = min(horizon_end, overall_last_date + timedelta(days=cap_days))

    fig, ax = plt.subplots(figsize=(max(6, len(stats) * 1.4), 5))

    for name, s in stats.items():
        pts = sorted(user_series[name].items())
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        line, = ax.plot(xs, ys, marker="o", linewidth=2)
        color = line.get_color()

        proj_end_val = s["last_val"] + s["rate"] * _days_between(s["last_date"], horizon_end)
        ax.plot([s["last_date"], horizon_end], [s["last_val"], proj_end_val],
                linestyle="--", linewidth=1.5, color=color, alpha=0.6)

        match = next((c for c in crossovers if c["name"] == name), None)
        if match and match["date"] <= horizon_end:
            cross_val = leader["last_val"] + leader["rate"] * _days_between(leader["last_date"], match["date"])
            ax.scatter([match["date"]], [cross_val], marker="*", s=180, color=color,
                       zorder=5, edgecolor="black", linewidth=0.5)
            label = f"{name} — catches up ~{match['date'].strftime('%b %d')}"
        elif match:
            label = f"{name} — catches up ~{match['date'].strftime('%b %d, %Y')} (off chart)"
        else:
            label = name
        line.set_label(label)

    ax.axvline(overall_last_date, color="gray", linestyle=":", linewidth=1, alpha=0.6)
    ax.set_ylabel("Trophies", fontsize=11)
    ax.set_title("Catch-Up Projection", fontsize=13, fontweight="bold", pad=14)
    ax.legend(fontsize=8, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    buf.seek(0)
    return buf, crossovers
