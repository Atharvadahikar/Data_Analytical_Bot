import pandas as pd
import numpy as np
import plotly.express as px


def fig_to_json(fig):
    return fig.to_json()


def generate_charts(df, y_col=None):

    charts = []
    insights = []

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # Histogram
    if numeric_cols:

        col = numeric_cols[0]

        fig = px.histogram(
            df,
            x=col,
            nbins=30,
            title=f"Distribution of {col}"
        )

        charts.append({
            "title": f"Distribution of {col}",
            "json": fig_to_json(fig)
        })

        insights.append(
            f"{col} distribution generated successfully."
        )

    # Correlation Heatmap
    if len(numeric_cols) >= 2:

        corr = df[numeric_cols].corr()

        fig = px.imshow(
            corr,
            text_auto=True,
            title="Correlation Heatmap"
        )

        charts.append({
            "title": "Correlation Heatmap",
            "json": fig_to_json(fig)
        })

        insights.append(
            "Correlation analysis completed."
        )

    # Scatter Plot
    if len(numeric_cols) >= 2:

        x = numeric_cols[0]

        y = (
            y_col
            if y_col in numeric_cols
            else numeric_cols[1]
        )

        chart_df = df[[x, y]].dropna()

        fig = px.scatter(
            chart_df,
            x=x,
            y=y,
            title=f"{x} vs {y}"
        )

        charts.append({
            "title": f"{x} vs {y}",
            "json": fig_to_json(fig)
        })

        insights.append(
            f"Relationship analyzed between {x} and {y}."
        )

    # Boxplot
    if y_col and y_col in df.columns:

        if pd.api.types.is_numeric_dtype(df[y_col]):

            fig = px.box(
                df,
                y=y_col,
                title=f"Outlier Detection for {y_col}"
            )

            charts.append({
                "title": f"Outlier Detection for {y_col}",
                "json": fig_to_json(fig)
            })

            insights.append(
                f"Outlier analysis completed for {y_col}."
            )

    # Category Chart
    if categorical_cols:

        col = categorical_cols[0]

        vc = (
            df[col]
            .value_counts()
            .head(10)
            .reset_index()
        )

        vc.columns = [col, "count"]

        fig = px.bar(
            vc,
            x=col,
            y="count",
            title=f"Top Categories in {col}"
        )

        charts.append({
            "title": f"Top Categories in {col}",
            "json": fig_to_json(fig)
        })

        insights.append(
            f"Category distribution generated for {col}."
        )

    return charts, insights
