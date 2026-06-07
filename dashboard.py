import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

from add_season import load_sales_data

df = load_sales_data()
min_date = df["Date"].min()
max_date = df["Date"].max()
product_options = ["ALL"] + sorted(df["Product_ID"].unique())
regions_sorted = sorted(df["Region"].unique())

THEME = {
    "text": "#f1f5f9",
    "text_muted": "#94a3b8",
    "primary": "#3b82f6",
    "primary_dark": "#1d4ed8",
    "primary_light": "#60a5fa",
    "accent": "#38bdf8",
    "bg_card": "rgba(15, 23, 42, 0.9)",
    "bg_panel": "rgba(15, 23, 42, 0.95)",
    "border": "rgba(59, 130, 246, 0.3)",
    "plot_bg": "rgba(15, 23, 42, 0.6)",
    "grid": "rgba(148, 163, 184, 0.15)",
    "hover_bg": "#1e293b",
}

REGION_COLORS = {
    "North": "#06b6d4",
    "South": "#f43f5e",
    "East": "#eab308",
    "West": "#8b5cf6",
}

SEASON_COLORS = {
    "Winter": "#38bdf8",
    "Summer": "#facc15",
    "Rainy": "#22c55e",
    "Autumn": "#f97316",
}

FORECAST_COLORS = {"actual": "#06b6d4", "forecast": "#f43f5e"}

CHART_HEIGHT = 380
TRANSITION = {"duration": 400, "easing": "cubic-in-out"}

app = Dash(__name__)
app.title = "Retail Sales Dashboard"

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            * { box-sizing: border-box; }
            body { margin: 0; background: #0f172a; }
            .app-shell { min-height: 100vh; padding: 24px 28px; font-family: 'Inter', sans-serif; }
            .brand-title { font-size: 2rem; font-weight: 700; color: #f1f5f9; text-align: center; margin-bottom: 4px; }
            .brand-tag { text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 20px; }
            .panel {
                background: rgba(15,23,42,0.95);
                border: 1px solid rgba(59,130,246,0.25);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
            }
            .chart-wrap {
                background: rgba(15,23,42,0.9);
                border: 1px solid rgba(59,130,246,0.2);
                border-radius: 12px;
                padding: 8px;
                margin-bottom: 14px;
            }
            .kpi-card {
                flex: 1; min-width: 160px;
                background: linear-gradient(135deg, #1e40af, #3b82f6);
                border-radius: 12px; padding: 18px 20px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            }
            .reset-btn {
                background: #2563eb; color: white; border: none;
                border-radius: 8px; padding: 10px 20px; font-weight: 600;
                cursor: pointer; font-family: 'Inter', sans-serif;
            }
            .reset-btn:hover { background: #1d4ed8; }
            .view-tabs .tab { font-family: 'Inter', sans-serif !important; font-weight: 600 !important; border-radius: 8px !important; }
            .view-tabs .tab--selected { background: #2563eb !important; color: white !important; }
            .Select-control, .DateRangeInput_input {
                background: #0f172a !important;
                border-color: rgba(59,130,246,0.35) !important;
                color: #f1f5f9 !important;
                border-radius: 8px !important;
            }
            .Select-menu-outer { background: #1e293b !important; }
            .Select-option { background: #1e293b !important; color: #f1f5f9 !important; }
            label { color: #94a3b8 !important; font-family: 'Inter', sans-serif !important; font-weight: 500 !important; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>"""

FILTER_STYLE = {"width": "22%", "display": "inline-block", "margin": "0 1%", "verticalAlign": "top"}
GRAPH_CFG = {"displayModeBar": False, "responsive": True}


def _filter_data(regions, seasons, products, start, end):
    out = df.copy()
    if products and "ALL" not in products:
        out = out[out["Product_ID"].isin(products)]
    if regions:
        out = out[out["Region"].isin(regions)]
    if seasons:
        out = out[out["Season"].isin(seasons)]
    if start:
        out = out[out["Date"] >= pd.to_datetime(start)]
    if end:
        out = out[out["Date"] <= pd.to_datetime(end)]
    return out


def _kpi_card(label, value):
    return html.Div(className="kpi-card", children=[
        html.Div(label, style={"fontSize": "12px", "color": "rgba(255,255,255,0.8)", "fontWeight": "600", "marginBottom": "6px"}),
        html.Div(value, style={"fontSize": "24px", "fontWeight": "700", "color": "#fff"}),
    ])


def _compare_kpi(label, val_a, val_b, kind="money"):
    if kind == "money":
        fa, fb = f"${val_a:,.0f}", f"${val_b:,.0f}"
    elif kind == "pct":
        fa, fb = f"{val_a:.1f}%", f"{val_b:.1f}%"
    else:
        fa, fb = f"{val_a:,.0f}", f"{val_b:,.0f}"
    delta = ((val_b - val_a) / val_a * 100) if val_a else 0
    return html.Div(className="kpi-card", children=[
        html.Div(label, style={"fontSize": "12px", "color": "rgba(255,255,255,0.8)", "fontWeight": "600", "marginBottom": "8px"}),
        html.Div([html.Span(fa), html.Span(" vs ", style={"opacity": 0.6}), html.Span(fb)],
                 style={"fontSize": "18px", "fontWeight": "700", "color": "#fff"}),
        html.Div(f"{'+' if delta > 0 else ''}{delta:.1f}%", style={"fontSize": "13px", "marginTop": "6px", "color": "#93c5fd"}),
    ])


def _insight_text(filtered, compare=False, region_a=None, region_b=None):
    if compare and region_a and region_b:
        da = filtered[filtered["Region"] == region_a]
        db = filtered[filtered["Region"] == region_b]
        if da.empty or db.empty:
            return "Select two regions that have data in the current filter range."
        ra, rb = da["Revenue"].sum(), db["Revenue"].sum()
        leader = region_b if rb >= ra else region_a
        pct = abs(rb - ra) / max(ra, rb, 1) * 100
        return f"{leader} leads on revenue by {pct:.1f}% (${max(ra, rb):,.0f} vs ${min(ra, rb):,.0f})"
    if filtered.empty:
        return "No data for selected filters. Try widening your selection."
    top_r = filtered.groupby("Region")["Revenue"].sum().idxmax()
    top_s = filtered.groupby("Season")["Revenue"].sum().idxmax()
    return (
        f"Top region: {top_r} (${filtered.groupby('Region')['Revenue'].sum().max():,.0f}) · "
        f"Best season: {top_s} · Total revenue: ${filtered['Revenue'].sum():,.0f}"
    )


def _base_layout(fig, title=None):
    t = title or (fig.layout.title.text if fig.layout.title else "")
    fig.update_layout(
        title=dict(text=t, font=dict(size=14, color=THEME["text"])),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=THEME["plot_bg"],
        font=dict(family="Inter", color=THEME["text_muted"], size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=THEME["text"])),
        margin=dict(t=48, b=40, l=48, r=20),
        height=CHART_HEIGHT,
        transition=TRANSITION,
        hoverlabel=dict(bgcolor=THEME["hover_bg"], font_color=THEME["text"]),
        uirevision="retail-dash",
    )
    return fig


def _cartesian_layout(fig, title=None):
    fig = _base_layout(fig, title)
    fig.update_xaxes(gridcolor=THEME["grid"], linecolor=THEME["grid"], zerolinecolor=THEME["grid"])
    fig.update_yaxes(gridcolor=THEME["grid"], linecolor=THEME["grid"], zerolinecolor=THEME["grid"])
    return fig


def _empty_figure(msg):
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=msg, font=dict(color=THEME["text_muted"])),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=THEME["plot_bg"],
        height=CHART_HEIGHT,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def _build_forecast(data):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    try:
        ts = data.groupby("Date")["Revenue"].sum().sort_index().resample("ME").sum()
        if ts.isna().any():
            ts = ts.ffill()
        if len(ts) < 3:
            return _empty_figure("Not enough data for forecast")

        try:
            fit = ExponentialSmoothing(ts, trend="add", seasonal="add", seasonal_periods=min(4, len(ts) - 1)).fit()
        except Exception:
            fit = ExponentialSmoothing(ts, trend="add", seasonal=None).fit()

        forecast = fit.forecast(4)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts.index, y=ts.values, mode="lines+markers", name="Actual",
            line=dict(color=FORECAST_COLORS["actual"], width=2),
            marker=dict(size=5, color=FORECAST_COLORS["actual"]),
        ))
        fig.add_trace(go.Scatter(
            x=forecast.index, y=forecast.values, mode="lines+markers", name="Forecast",
            line=dict(color=FORECAST_COLORS["forecast"], width=2, dash="dash"),
            marker=dict(size=6, color=FORECAST_COLORS["forecast"]),
        ))
        return _cartesian_layout(fig, "Revenue Forecast (Next 4 Months)")
    except Exception:
        return _empty_figure("Forecast unavailable")


def _build_radar(region_a, region_b, data):
    da = data[data["Region"] == region_a]
    db = data[data["Region"] == region_b]
    if da.empty or db.empty:
        return _empty_figure("Both regions need data")

    metrics = ["Revenue", "Units", "Discount", "Orders"]
    vals_a = [da["Revenue"].sum(), da["Units_Sold"].sum(), da["Discount"].mean(), len(da)]
    vals_b = [db["Revenue"].sum(), db["Units_Sold"].sum(), db["Discount"].mean(), len(db)]
    maxes = [max(vals_a[i], vals_b[i], 1) for i in range(4)]
    norm_a = [v / m * 100 for v, m in zip(vals_a, maxes)]
    norm_b = [v / m * 100 for v, m in zip(vals_b, maxes)]

    fig = go.Figure()
    color_a = REGION_COLORS.get(region_a, "#06b6d4")
    color_b = REGION_COLORS.get(region_b, "#f43f5e")
    fig.add_trace(go.Scatterpolar(
        r=norm_a + [norm_a[0]], theta=metrics + [metrics[0]],
        fill="toself", name=region_a,
        line=dict(color=color_a),
        fillcolor="rgba(6, 182, 212, 0.25)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=norm_b + [norm_b[0]], theta=metrics + [metrics[0]],
        fill="toself", name=region_b,
        line=dict(color=color_b),
        fillcolor="rgba(244, 63, 94, 0.2)",
    ))
    fig.update_layout(
        title=dict(text=f"{region_a} vs {region_b}", font=dict(size=14, color=THEME["text"])),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=THEME["plot_bg"],
        height=CHART_HEIGHT,
        font=dict(family="Inter", color=THEME["text_muted"]),
        legend=dict(font=dict(color=THEME["text"])),
        polar=dict(
            bgcolor=THEME["plot_bg"],
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=THEME["grid"], color=THEME["text_muted"]),
            angularaxis=dict(gridcolor=THEME["grid"], color=THEME["text_muted"]),
        ),
        margin=dict(t=48, b=40, l=60, r=60),
        uirevision="retail-dash",
    )
    return fig


def _overview_charts(filtered):
    if filtered.empty:
        e = _empty_figure("No data for selected filters")
        return e, e, e, e, e, e

    rev = filtered.groupby(["Season", "Region"], as_index=False)["Revenue"].sum()
    units = filtered.groupby(["Season", "Region"], as_index=False)["Units_Sold"].sum()
    disc = filtered.groupby("Season", as_index=False)["Discount"].mean()

    fig1 = px.bar(rev, x="Season", y="Revenue", color="Region", barmode="group",
                  title="Revenue by Season", color_discrete_map=REGION_COLORS)
    fig2 = px.bar(units, x="Season", y="Units_Sold", color="Region", barmode="group",
                  title="Units Sold by Season", color_discrete_map=REGION_COLORS)

    trend = filtered.groupby(["Date", "Region"], as_index=False)["Revenue"].sum()
    fig3 = px.line(trend, x="Date", y="Revenue", color="Region",
                   title="Sales Trend Over Time", color_discrete_map=REGION_COLORS, markers=True)
    fig3.update_traces(line=dict(width=2))

    fig4 = px.pie(disc, names="Season", values="Discount", hole=0.4,
                  title="Average Discount by Season", color="Season",
                  color_discrete_map=SEASON_COLORS)
    fig4.update_traces(textinfo="label+percent", textfont_size=11)

    fig5 = _build_forecast(filtered)

    fig6 = px.box(filtered, x="Season", y="Units_Sold", color="Region",
                  title="Units Sold Distribution", color_discrete_map=REGION_COLORS)

    return (
        _cartesian_layout(fig1),
        _cartesian_layout(fig2),
        _cartesian_layout(fig3),
        _base_layout(fig4),
        fig5,
        _cartesian_layout(fig6),
    )


def _compare_charts(filtered, region_a, region_b):
    da = filtered[filtered["Region"] == region_a]
    db = filtered[filtered["Region"] == region_b]
    if da.empty or db.empty:
        e = _empty_figure("Both regions need data in filter range")
        return e, e, e

    sa = da.groupby("Season", as_index=False)["Revenue"].sum()
    sa["Region"] = region_a
    sb = db.groupby("Season", as_index=False)["Revenue"].sum()
    sb["Region"] = region_b
    combined = pd.concat([sa, sb], ignore_index=True)

    fig1 = px.bar(combined, x="Season", y="Revenue", color="Region", barmode="group",
                  title="Revenue by Season", color_discrete_map=REGION_COLORS)

    fig2 = _build_radar(region_a, region_b, filtered)

    ta = da.groupby("Date", as_index=False)["Revenue"].sum()
    ta["Region"] = region_a
    tb = db.groupby("Date", as_index=False)["Revenue"].sum()
    tb["Region"] = region_b
    trends = pd.concat([ta, tb], ignore_index=True)
    fig3 = px.line(trends, x="Date", y="Revenue", color="Region",
                   title="Revenue Trend Comparison", markers=True,
                   color_discrete_map=REGION_COLORS)
    fig3.update_traces(line=dict(width=2))

    return _cartesian_layout(fig1), fig2, _cartesian_layout(fig3)


def _graph(id_):
    return html.Div(className="chart-wrap", children=[
        dcc.Loading(dcc.Graph(id=id_, config=GRAPH_CFG), type="default", color=THEME["primary"]),
    ])


app.layout = html.Div(className="app-shell", children=[
    html.Div("Retail Sales Dashboard", className="brand-title"),
    html.P("Interactive analytics with filtering and regional comparison", className="brand-tag"),

    html.Div(id="insight_bar", className="panel",
             style={"textAlign": "center", "color": THEME["text"], "fontSize": "14px"}),

    html.Div(className="panel", children=[
        html.Div([
            html.Div([html.Label("Region"), dcc.Dropdown(
                id="region_filter",
                options=[{"label": r, "value": r} for r in regions_sorted],
                multi=True, placeholder="All regions",
            )], style=FILTER_STYLE),
            html.Div([html.Label("Season"), dcc.Dropdown(
                id="season_filter",
                options=[{"label": s, "value": s} for s in sorted(df["Season"].unique())],
                multi=True, placeholder="All seasons",
            )], style=FILTER_STYLE),
            html.Div([html.Label("Product"), dcc.Dropdown(
                id="product_filter",
                options=[{"label": p, "value": p} for p in product_options],
                multi=True, placeholder="All products",
            )], style=FILTER_STYLE),
            html.Div([html.Label("Date Range"), dcc.DatePickerRange(
                id="date_filter",
                min_date_allowed=min_date, max_date_allowed=max_date,
                start_date=min_date, end_date=max_date,
                display_format="YYYY-MM-DD",
            )], style=FILTER_STYLE),
        ]),
        html.Div(style={"textAlign": "center", "marginTop": "12px"}, children=[
            html.Button("Reset Filters", id="reset_btn", n_clicks=0, className="reset-btn"),
        ]),
    ]),

    dcc.Tabs(id="view_tabs", value="overview", className="view-tabs", children=[
        dcc.Tab(label="Overview", value="overview"),
        dcc.Tab(label="Compare Regions", value="compare"),
    ], style={"marginBottom": "14px"}),

    html.Div(id="compare_controls", style={"display": "none"}, className="panel", children=[
        html.Div(style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}, children=[
            html.Div(style={"flex": "1", "minWidth": "200px"}, children=[
                html.Label("Region A"),
                dcc.Dropdown(id="region_a", options=[{"label": r, "value": r} for r in regions_sorted], value=regions_sorted[0]),
            ]),
            html.Div(style={"flex": "1", "minWidth": "200px"}, children=[
                html.Label("Region B"),
                dcc.Dropdown(id="region_b",
                             options=[{"label": r, "value": r} for r in regions_sorted],
                             value=regions_sorted[1] if len(regions_sorted) > 1 else regions_sorted[0]),
            ]),
        ]),
    ]),

    html.Div(id="kpi_row", style={"display": "flex", "gap": "14px", "marginBottom": "16px", "flexWrap": "wrap"}),

    html.Div(id="overview_section", children=[
        html.Div(style={"display": "flex", "gap": "14px", "flexWrap": "wrap"}, children=[
            html.Div(style={"flex": "1", "minWidth": "420px"}, children=[_graph("revenue_by_season")]),
            html.Div(style={"flex": "1", "minWidth": "420px"}, children=[_graph("units_by_season")]),
        ]),
        html.Div(style={"display": "flex", "gap": "14px", "flexWrap": "wrap"}, children=[
            html.Div(style={"flex": "1", "minWidth": "420px"}, children=[_graph("sales_trend")]),
            html.Div(style={"flex": "1", "minWidth": "420px"}, children=[_graph("discount_pie")]),
        ]),
        html.Div(style={"display": "flex", "gap": "14px", "flexWrap": "wrap"}, children=[
            html.Div(style={"flex": "1", "minWidth": "420px"}, children=[_graph("forecast_chart")]),
            html.Div(style={"flex": "1", "minWidth": "420px"}, children=[_graph("seasonal_fluctuations")]),
        ]),
    ]),

    html.Div(id="compare_section", style={"display": "none"}, children=[
        html.Div(style={"display": "flex", "gap": "14px", "flexWrap": "wrap"}, children=[
            html.Div(style={"flex": "1", "minWidth": "420px"}, children=[_graph("compare_bar")]),
            html.Div(style={"flex": "1", "minWidth": "420px"}, children=[_graph("compare_radar")]),
        ]),
        _graph("compare_trend"),
    ]),
])


@app.callback(
    [Output("overview_section", "style"), Output("compare_section", "style"), Output("compare_controls", "style")],
    Input("view_tabs", "value"),
)
def switch_view(tab):
    if tab == "compare":
        return {"display": "none"}, {"display": "block"}, {"display": "block", "marginBottom": "14px"}
    return {"display": "block"}, {"display": "none"}, {"display": "none"}


@app.callback(
    [Output("region_filter", "value"), Output("season_filter", "value"),
     Output("product_filter", "value"), Output("date_filter", "start_date"),
     Output("date_filter", "end_date")],
    Input("reset_btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_):
    return None, None, None, min_date, max_date


@app.callback(
    [Output("kpi_row", "children"), Output("insight_bar", "children")],
    [Input("region_filter", "value"), Input("season_filter", "value"),
     Input("product_filter", "value"), Input("date_filter", "start_date"),
     Input("date_filter", "end_date"), Input("view_tabs", "value"),
     Input("region_a", "value"), Input("region_b", "value")],
)
def update_kpis(regions, seasons, products, start, end, view, region_a, region_b):
    filtered = _filter_data(regions, seasons, products, start, end)
    compare = view == "compare"
    insight = _insight_text(filtered, compare, region_a, region_b)

    if compare:
        if not region_a or not region_b or region_a == region_b:
            return [html.Div("Pick two different regions.", style={"color": THEME["text_muted"], "padding": "12px"})], insight
        da = filtered[filtered["Region"] == region_a]
        db = filtered[filtered["Region"] == region_b]
        if da.empty or db.empty:
            return [_kpi_card("No data", "—")], insight
        return [
            _compare_kpi("Revenue", da["Revenue"].sum(), db["Revenue"].sum()),
            _compare_kpi("Units", da["Units_Sold"].sum(), db["Units_Sold"].sum(), kind="int"),
            _compare_kpi("Discount", da["Discount"].mean(), db["Discount"].mean(), kind="pct"),
        ], insight

    if filtered.empty:
        return [_kpi_card("No data", "—")], insight
    return [
        _kpi_card("Total Revenue", f"${filtered['Revenue'].sum():,.0f}"),
        _kpi_card("Units Sold", f"{filtered['Units_Sold'].sum():,.0f}"),
        _kpi_card("Avg Discount", f"{filtered['Discount'].mean():.1f}%"),
        _kpi_card("Transactions", f"{len(filtered):,}"),
    ], insight


@app.callback(
    [Output("revenue_by_season", "figure"), Output("units_by_season", "figure"),
     Output("sales_trend", "figure"), Output("discount_pie", "figure"),
     Output("forecast_chart", "figure"), Output("seasonal_fluctuations", "figure")],
    [Input("region_filter", "value"), Input("season_filter", "value"),
     Input("product_filter", "value"), Input("date_filter", "start_date"),
     Input("date_filter", "end_date")],
)
def update_overview(regions, seasons, products, start, end):
    return _overview_charts(_filter_data(regions, seasons, products, start, end))


@app.callback(
    [Output("compare_bar", "figure"), Output("compare_radar", "figure"), Output("compare_trend", "figure")],
    [Input("region_filter", "value"), Input("season_filter", "value"),
     Input("product_filter", "value"), Input("date_filter", "start_date"),
     Input("date_filter", "end_date"), Input("region_a", "value"), Input("region_b", "value")],
)
def update_compare(regions, seasons, products, start, end, region_a, region_b):
    if not region_a or not region_b or region_a == region_b:
        e = _empty_figure("Select two different regions")
        return e, e, e
    return _compare_charts(_filter_data(regions, seasons, products, start, end), region_a, region_b)


if __name__ == "__main__":
    app.run(debug=True)
