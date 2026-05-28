import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import (
    accuracy_score,
    r2_score
)

from sklearn.linear_model import (
    LogisticRegression,
    LinearRegression
)

from sklearn.tree import (
    DecisionTreeClassifier,
    DecisionTreeRegressor
)

from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor
)


def prepare_data(df, x_cols, y_col):

    data = df[x_cols + [y_col]].copy()

    data = data.dropna()

    X = data[x_cols]
    y = data[y_col]

    X = pd.get_dummies(
        X,
        drop_first=True
    )

    if y.dtype == "object":

        encoder = LabelEncoder()

        y = encoder.fit_transform(
            y.astype(str)
        )

    return X, y


def detect_problem_type(y):

    unique_values = len(
        pd.Series(y).unique()
    )

    if unique_values <= 20:
        return "classification"

    return "regression"


def train_best_model(df, x_cols, y_col):

    X, y = prepare_data(
        df,
        x_cols,
        y_col
    )

    if len(X) == 0:
        raise ValueError(
            "Dataset became empty after preprocessing."
        )

    problem_type = detect_problem_type(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    if problem_type == "classification":

        models = {
            "Logistic Regression":
                LogisticRegression(max_iter=1000),

            "Decision Tree":
                DecisionTreeClassifier(),

            "Random Forest":
                RandomForestClassifier(),

            "Gradient Boosting":
                GradientBoostingClassifier()
        }

    else:

        models = {
            "Linear Regression":
                LinearRegression(),

            "Decision Tree Regressor":
                DecisionTreeRegressor(),

            "Random Forest Regressor":
                RandomForestRegressor(),

            "Gradient Boosting Regressor":
                GradientBoostingRegressor()
        }

    results = []

    for name, model in models.items():

        try:

            model.fit(
                X_train,
                y_train
            )

            preds = model.predict(
                X_test
            )

            if problem_type == "classification":

                score = accuracy_score(
                    y_test,
                    preds
                )

            else:

                score = r2_score(
                    y_test,
                    preds
                )

            results.append({
                "model": name,
                "score": round(
                    float(score),
                    4
                )
            })

        except Exception as e:

            results.append({
                "model": name,
                "score": -999,
                "error": str(e)
            })

    valid = [
        r for r in results
        if r["score"] != -999
    ]

    if not valid:

        raise ValueError(
            "All models failed."
        )

    best_model = max(
        valid,
        key=lambda x: x["score"]
    )

    return {
        "problem_type": problem_type,
        "best_model": best_model,
        "models": results,
        "features_used": x_cols,
        "target": y_col
    }