"""
Plotly chart generators for Evolutionary Market Lab:
- Responsive Plotly dark theme
- Clean margins and outside legends
- Uncluttered markers without overlapping labels
- Hover templates with clear definitions
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.formatting import get_asset_currency_info, format_currency


CHART_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(19, 29, 48, 0.4)",
    font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#94A3B8", size=12),
    hoverlabel=dict(bgcolor="#131D30", bordercolor="#263247", font=dict(color="#F1F5F9", size=12)),
    margin=dict(l=48, r=24, t=48, b=40),
)


def create_pareto_chart(
    summary_df: pd.DataFrame,
    selected_id: int,
    frozen_id: int,
) -> go.Figure:
    """
    Renders the Development vs Exploratory Test Pareto Frontier scatter chart.
    Uses marker-only mode to prevent text clutter.
    Legend is positioned cleanly at the top with generous margin to prevent title collision.
    """
    fig = go.Figure()

    # 1. Development Pareto points
    fig.add_trace(go.Scatter(
        x=summary_df["dev_mdd"] * 100.0,
        y=summary_df["dev_sharpe"],
        mode="markers",
        name="Development Pareto (GA Search)",
        marker=dict(size=9, color="#00D2D3", symbol="circle", opacity=0.85, line=dict(color="#0B1020", width=1)),
        customdata=summary_df[["id", "dev_trades", "dev_ret"]].to_numpy(),
        hovertemplate=(
            "<b>Strategy #%{customdata[0]} (Development)</b><br>"
            "Dev Max Drawdown: %{x:.2f}%<br>"
            "Dev Sharpe Ratio: %{y:.2f}<br>"
            "Dev Return: %{customdata[2]:.2%}<br>"
            "Completed Trades: %{customdata[1]}<extra></extra>"
        ),
    ))

    # 2. Exploratory Out-of-Sample Test points
    fig.add_trace(go.Scatter(
        x=summary_df["exploratory_test_mdd"] * 100.0,
        y=summary_df["exploratory_test_sharpe"],
        mode="markers",
        name="Exploratory OOS Test (All Candidates)",
        marker=dict(size=8, color="#64748B", symbol="diamond", opacity=0.7),
        customdata=summary_df[["id", "exploratory_test_trades", "exploratory_test_ret"]].to_numpy(),
        hovertemplate=(
            "<b>Strategy #%{customdata[0]} (Exploratory Test)</b><br>"
            "Test Max Drawdown: %{x:.2f}%<br>"
            "Test Sharpe Ratio: %{y:.2f}<br>"
            "Test Return: %{customdata[2]:.2%}<br>"
            "Completed Trades: %{customdata[1]}<extra></extra>"
        ),
    ))

    # 3. Highlight Frozen Representative Pick (Star / Ring)
    frozen_row = summary_df[summary_df["id"] == frozen_id]
    if not frozen_row.empty:
        frow = frozen_row.iloc[0]
        fig.add_trace(go.Scatter(
            x=[frow["dev_mdd"] * 100.0],
            y=[frow["dev_sharpe"]],
            mode="markers+text",
            name="Frozen Primary Strategy (Best Dev)",
            marker=dict(size=14, color="#10B981", symbol="star", line=dict(color="#FFFFFF", width=1.5)),
            text=[f"#{frozen_id}"],
            textposition="top center",
            textfont=dict(color="#10B981", size=11, family="sans-serif"),
            hovertemplate=(
                "<b>Primary Frozen Strategy #%{text}</b><br>"
                "Dev Max DD: %{x:.2f}%<br>"
                "Dev Sharpe: %{y:.2f}<br>"
                "<i>Frozen before test evaluation</i><extra></extra>"
            ),
        ))

    # 4. Highlight Currently Inspected Candidate if different from frozen
    if selected_id != frozen_id:
        sel_row = summary_df[summary_df["id"] == selected_id]
        if not sel_row.empty:
            srow = sel_row.iloc[0]
            fig.add_trace(go.Scatter(
                x=[srow["dev_mdd"] * 100.0],
                y=[srow["dev_sharpe"]],
                mode="markers+text",
                name=f"Inspecting #{selected_id}",
                marker=dict(size=13, color="#F59E0B", symbol="circle-open", line=dict(color="#F59E0B", width=2.5)),
                text=[f"#{selected_id}"],
                textposition="bottom center",
                textfont=dict(color="#FDE68A", size=11),
                hoverinfo="skip",
            ))

    layout_pareto = dict(CHART_LAYOUT_DEFAULTS)
    layout_pareto["margin"] = dict(l=50, r=40, t=30, b=45)

    fig.update_layout(
        **layout_pareto,
        xaxis=dict(
            title="Maximum Drawdown % (Lower is Safer)",
            gridcolor="#263247",
            zerolinecolor="#263247",
            showgrid=True,
        ),
        yaxis=dict(
            title="Annualized Sharpe Ratio (Higher is Better)",
            gridcolor="#263247",
            zerolinecolor="#263247",
            showgrid=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11),
        ),
        height=380,
    )
    return fig


def create_equity_drawdown_chart(
    detailed_sim: dict,
    ticker: str,
    test_df: pd.DataFrame,
) -> go.Figure:
    """
    Renders two-panel chart:
    Panel 1: Cumulative Portfolio Equity vs. Benchmark Buy & Hold
    Panel 2: Underwater Drawdown Profile (%)
    """
    dates = detailed_sim["dates"]
    equity = detailed_sim["equity"]
    benchmark_equity = detailed_sim["benchmark_equity"]
    strat_dd = detailed_sim["drawdowns"] * 100.0

    # Benchmark Drawdown
    close_prices = test_df["Close"].to_numpy(dtype=np.float64)
    b_peak = np.maximum.accumulate(close_prices)
    benchmark_dd = ((close_prices - b_peak) / (b_peak + 1e-8)) * 100.0

    sym, _ = get_asset_currency_info(ticker)
    curr_prefix = sym if sym else ""

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            f"Out-of-Sample Portfolio Equity Growth ({curr_prefix}100,000 Initial)",
            "Underwater Drawdown Profile (%)",
        ),
        row_heights=[0.68, 0.32],
    )

    # Panel 1: Strategy Equity
    fig.add_trace(go.Scatter(
        x=dates,
        y=equity,
        name="CI Strategy",
        line=dict(color="#00D2D3", width=2.0),
        hovertemplate="<b>CI Strategy</b><br>Date: %{x}<br>Equity: " + curr_prefix + "%{y:,.2f}<extra></extra>",
    ), row=1, col=1)

    # Panel 1: Benchmark Equity
    fig.add_trace(go.Scatter(
        x=dates,
        y=benchmark_equity,
        name=f"Buy & Hold ({ticker})",
        line=dict(color="#94A3B8", width=1.5, dash="dot"),
        hovertemplate="<b>Buy & Hold</b><br>Date: %{x}<br>Equity: " + curr_prefix + "%{y:,.2f}<extra></extra>",
    ), row=1, col=1)

    # Panel 2: Strategy Drawdown
    fig.add_trace(go.Scatter(
        x=dates,
        y=strat_dd,
        name="Strategy Drawdown",
        fill="tozeroy",
        fillcolor="rgba(244, 63, 94, 0.15)",
        line=dict(color="#F43F5E", width=1.4),
        hovertemplate="<b>Strategy DD</b>: %{y:.2f}%<extra></extra>",
    ), row=2, col=1)

    # Panel 2: Benchmark Drawdown
    fig.add_trace(go.Scatter(
        x=dates,
        y=benchmark_dd,
        name="Benchmark Drawdown",
        line=dict(color="#64748B", width=1.2, dash="dash"),
        hovertemplate="<b>Benchmark DD</b>: %{y:.2f}%<extra></extra>",
    ), row=2, col=1)

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11),
        ),
        height=480,
    )
    fig.update_yaxes(title_text=f"Portfolio ({curr_prefix})", gridcolor="#263247", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown %", gridcolor="#263247", row=2, col=1)
    fig.update_xaxes(gridcolor="#263247")
    return fig


def create_feature_importance_chart(imp_df: pd.DataFrame, total_features: int) -> go.Figure:
    """
    Renders horizontal bar chart of top LightGBM predictive features by split gain.
    Uses friendly display labels on the axis while preserving exact source feature IDs in hover.
    """
    from ui.metadata import FEATURE_FRIENDLY_NAMES

    top_df = imp_df.head(10).iloc[::-1].copy()  # Reverse for ascending order in horizontal bar
    top_df["friendly_label"] = top_df["feature"].map(lambda f: FEATURE_FRIENDLY_NAMES.get(f, f))

    fig = go.Figure(go.Bar(
        x=top_df["importance"],
        y=top_df["friendly_label"],
        customdata=top_df["feature"],
        orientation="h",
        marker=dict(
            color=top_df["importance"],
            colorscale=[[0, "#0EA5E9"], [1, "#00D2D3"]],
            line=dict(color="#0B1020", width=1),
        ),
        hovertemplate="<b>%{y}</b><br>Source Feature ID: <code>%{customdata}</code><br>Split Gain Importance: %{x:,.1f}<extra></extra>",
    ))

    layout_kwargs = dict(CHART_LAYOUT_DEFAULTS)
    layout_kwargs["margin"] = dict(l=140, r=24, t=30, b=40)

    fig.update_layout(
        **layout_kwargs,
        xaxis=dict(title="Importance (Split Gain)", gridcolor="#263247", showgrid=True),
        yaxis=dict(gridcolor="#263247"),
        height=350,
    )
    return fig
