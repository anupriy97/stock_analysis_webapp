import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go


def plot_price_volume_chart(df: pd.DataFrame):
    date_col = 'date'
    primary_y_col = 'close'
    secondary_y_col = 'volume'

    secondary_ylim = df[secondary_y_col].max() * 4

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Line(x=df[date_col], y=df[primary_y_col], name="Daily Closing Price"),
        secondary_y=False, # Explicitly assign to primary Y-axis
    )

    fig.add_trace(
        go.Bar(x=df[date_col], y=df[secondary_y_col], name="Daily Volume"),
        secondary_y=True, # Assign to secondary Y-axis
    )


    fig.update_yaxes(title_text="Price (in ₹)", secondary_y=False)
    fig.update_yaxes(title_text="Volume", range=[0, secondary_ylim], secondary_y=True)

    return fig
