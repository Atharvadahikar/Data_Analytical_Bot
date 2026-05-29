import pandas as pd
import numpy as np


def profile_dataset(df):

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_values": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_columns": df.select_dtypes(include=np.number).columns.tolist(),
        "categorical_columns": df.select_dtypes(exclude=np.number).columns.tolist()
    }


def clean_special_values(df):

    special_values = [
        "",
        " ",
        "-",
        "--",
        "?",
        "NA",
        "N/A",
        "null",
        "None"
    ]

    return df.replace(special_values, np.nan)


def remove_duplicate_rows(df):

    before = len(df)

    df = df.drop_duplicates()

    removed = before - len(df)

    return df, removed


def remove_high_missing_columns(df, threshold=0.70):

    missing_ratio = df.isnull().mean()

    cols_to_drop = (
        missing_ratio[missing_ratio > threshold]
        .index
        .tolist()
    )

    df = df.drop(
        columns=cols_to_drop,
        errors="ignore"
    )

    return df, cols_to_drop


def fill_missing_values(df):

    for col in df.columns:

        if pd.api.types.is_numeric_dtype(df[col]):

            df[col] = df[col].fillna(
                df[col].median()
            )

        else:

            mode = df[col].mode()

            fill_value = (
                mode.iloc[0]
                if not mode.empty
                else "Unknown"
            )

            df[col] = df[col].fillna(
                fill_value
            )

    return df


def detect_outliers(df):

    outliers = {}

    numeric_cols = (
        df.select_dtypes(include=np.number)
        .columns
    )

    for col in numeric_cols:

        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)

        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        count = len(
            df[
                (df[col] < lower) |
                (df[col] > upper)
            ]
        )

        outliers[col] = int(count)

    return outliers


def basic_preprocess_for_eda(df):

    clean_df = df.copy()

    original_rows = clean_df.shape[0]
    original_cols = clean_df.shape[1]

    clean_df = clean_special_values(clean_df)

    clean_df, duplicates_removed = (
        remove_duplicate_rows(clean_df)
    )

    clean_df, dropped_cols = (
        remove_high_missing_columns(clean_df)
    )

    clean_df = fill_missing_values(clean_df)

    outlier_summary = detect_outliers(clean_df)

    report = {
        "original_rows": int(original_rows),
        "original_columns": int(original_cols),
        "final_rows": int(clean_df.shape[0]),
        "final_columns": int(clean_df.shape[1]),
        "duplicates_removed": int(duplicates_removed),
        "remaining_missing_values": int(
            clean_df.isnull().sum().sum()
        ),
        "dropped_columns": dropped_cols,
        "outlier_summary": outlier_summary
    }

    return clean_df, report