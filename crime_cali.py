import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# Load dataset
df = pd.read_csv("california_crime_realistic_weapons.csv", parse_dates=["date_time"])
cities = sorted(df["city"].unique())
cities.insert(0, "All California")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

app.layout = dbc.Container(fluid=True, style={"backgroundColor": "#060606"}, children=[
    dbc.Row(html.H1("California Crime Dashboard", style={"color": "#fff", "textAlign": "center"}), className="my-4"),

    dbc.Row([
        dbc.Col(html.Label("Select City:", style={"color": "#fff", "marginRight": "10px"}), width="auto"),
        dbc.Col(dcc.Dropdown(id="city-dropdown",
                             options=[{"label": c, "value": c} for c in cities],
                             value="All California", clearable=False,
                             style={
                                 "width": "300px",
                                 "backgroundColor": "#FFFFFF",
                                 "color": "#000000",
                                 "borderRadius": "10px"
                             }), width="auto")
    ], justify="center", className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="case-closed-chart"), md=4),
        dbc.Col(dcc.Graph(id="race-chart"), md=4),
        dbc.Col(dcc.Graph(id="gender-chart"), md=4)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="hourly-graph"), md=5),
        dbc.Col(html.Div([
            dbc.Card([
                dbc.CardHeader("🔢 Total Crimes", className="bg-primary text-white"),
                dbc.CardBody(html.H2(id="total-crimes", className="text-center"))
            ], className="mb-3", style={"borderRadius": "15px", "boxShadow": "0 4px 8px rgba(0,0,0,0.3)"}),
            dbc.Card([
                dbc.CardHeader("🚨 Most Frequent Crime", className="bg-info text-white"),
                dbc.CardBody(html.Div(id="freq-crime", style={"fontSize": "1.2rem"}, className="text-center"))
            ], style={"borderRadius": "15px", "boxShadow": "0 4px 8px rgba(0,0,0,0.3)"})
        ]), md=2),
        dbc.Col(dcc.Graph(id="weapons-graph"), md=5)
    ], className="mb-4"),

    dbc.Row(dbc.Col(dcc.Graph(id="monthly-graph"), md=12), className="mb-4"),
    dbc.Row(dbc.Col(dcc.Graph(id="crime-map"), md=12), className="mb-4")
])


def style(fig):
    fig.update_layout(
        paper_bgcolor="#060606",
        plot_bgcolor="#060606",
        font=dict(color="#FFFFFF", size=14),
        title=dict(font=dict(size=20), x=0.5),
        legend_title_font=dict(size=14),
        margin=dict(t=50, b=40, l=20, r=20),
        hoverlabel=dict(bgcolor="black", font_size=13),
        uirevision="constant",  # ✅ Retain zoom/pan state
        dragmode="zoom",        # ✅ Enable zooming with mouse
    )
    return fig



@app.callback([
    Output("case-closed-chart", "figure"),
    Output("race-chart", "figure"),
    Output("gender-chart", "figure"),
    Output("hourly-graph", "figure"),
    Output("weapons-graph", "figure"),
    Output("monthly-graph", "figure"),
    Output("crime-map", "figure"),
    Output("total-crimes", "children"),
    Output("freq-crime", "children")
], [Input("city-dropdown", "value")])
def update(city):
    dff = df.copy() if city == "All California" else df[df.city == city].copy()

    case_df = dff["case_closed"].value_counts().reset_index()
    case_df.columns = ["status", "count"]
    fig_case = style(px.pie(case_df, names="status", values="count", hole=0.4, title="Case Closed",
                            color_discrete_sequence=px.colors.qualitative.Vivid))

    race_df = dff["race_ethnicity"].value_counts().reset_index()
    race_df.columns = ["race_ethnicity", "count"]
    fig_race = style(px.bar(race_df, x="race_ethnicity", y="count", title="Crimes by Race/Ethnicity",
                            color="race_ethnicity", color_discrete_sequence=px.colors.qualitative.Vivid))

    gender_df = dff["gender"].value_counts().reset_index()
    gender_df.columns = ["gender", "count"]
    fig_gender = style(px.pie(gender_df, names="gender", values="count", hole=0.4, title="Gender Analysis",
                              color_discrete_sequence=px.colors.qualitative.Vivid))

    hourly_df = dff.assign(hour=dff.date_time.dt.hour).groupby("hour").size().reset_index(name="crime_count")
    fig_hour = style(px.line(hourly_df, x="hour", y="crime_count", title="Hourly Crime Metrics", markers=True))

    weapon_df = dff.groupby("weapon").size().reset_index(name="usage_count")
    fig_weap = style(px.bar(weapon_df.sort_values("usage_count"), x="usage_count", y="weapon", orientation="h",
                            title="Top Weapons", color_discrete_sequence=px.colors.qualitative.Vivid))

    month_df = dff.assign(month=dff.date_time.dt.strftime("%b")).groupby("month").size().reset_index(name="crime_count")
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_df["month"] = pd.Categorical(month_df["month"], categories=month_order, ordered=True)
    fig_month = style(px.bar(month_df.sort_values("month"), x="month", y="crime_count",
                             title="Monthly Trends", color_discrete_sequence=px.colors.qualitative.Prism))

    # Map with additional hover info: crime type
    fig_map = style(px.scatter_map(
    data_frame=dff,
    lat="latitude",
    lon="longitude",
    color="city",
    zoom=5,
    hover_data=["crime_type", "weapon", "gender", "case_closed"],
    center={"lat": 36.7783, "lon": -119.4179},
    map_style="open-street-map",  # ✅ Note the new param name
    title="Crime Locations"
    ))



    total = f"{len(dff):,}"
    if not dff.empty and "crime_type" in dff.columns and dff["crime_type"].notna().any():
        vc = dff["crime_type"].dropna().astype(str).value_counts()
        freq = html.Span(f"{vc.idxmax()} ({vc.max()} crimes)")
    else:
        freq = html.Span("N/A")

    return fig_case, fig_race, fig_gender, fig_hour, fig_weap, fig_month, fig_map, total, freq


if __name__ == "__main__":
    app.run(debug=True)
