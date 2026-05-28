import os
import uuid
import traceback
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"

print("ENV FILE =", env_path)



from utils.preprocessing import profile_dataset, basic_preprocess_for_eda
from utils.charts import generate_charts
from utils.ml_model import train_best_model
from agents.insight_agent import InsightAgent
from agents.model_agent import ModelImprovementAgent

load_dotenv(env_path)

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

os.makedirs("uploads", exist_ok=True)

DATASETS = {}
INSIGHTS = {}


def success(data=None, status=200):
    res = {"success": True}
    if data:
        res.update(data)
    return jsonify(res), status


def fail(message, status=400, details=None):
    res = {"success": False, "error": str(message)}
    if details:
        res["details"] = str(details)
    return jsonify(res), status


def get_df(dataset_id):
    if not dataset_id:
        return None, fail("dataset_id is required", 400)

    df = DATASETS.get(dataset_id)

    if df is None:
        return None, fail("Invalid dataset_id. Please upload dataset again.", 404)

    return df, None


@app.errorhandler(404)
def not_found(e):
    return fail("Route not found", 404)


@app.errorhandler(405)
def method_not_allowed(e):
    return fail("Method not allowed. Check frontend fetch method.", 405)


@app.errorhandler(Exception)
def server_error(e):
    app.logger.error(traceback.format_exc())
    return fail("Internal server error", 500, e)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file:
        return fail("CSV file is required", 400)

    if file.filename == "":
        return fail("No file selected", 400)

    if not file.filename.lower().endswith(".csv"):
        return fail("Only CSV files are supported", 400)

    try:
        df = pd.read_csv(file)
    except Exception as e:
        return fail("Could not read CSV", 400, e)

    if df.empty:
        return fail("CSV file is empty", 400)
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = df.select_dtypes(exclude=["number"]).columns.tolist()

    dataset_id = str(uuid.uuid4())
    DATASETS[dataset_id] = df

    INSIGHTS[dataset_id] = [
        f"Dataset uploaded with {df.shape[0]} rows and {df.shape[1]} columns."
    ]

    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

    return success({
        "message": "Dataset uploaded successfully",
        "dataset_id": dataset_id,
        "columns": df.columns.tolist(),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "profile": profile_dataset(df)
    })


@app.route("/api/preprocess", methods=["POST"])
def preprocess():
    payload = request.get_json(silent=True) or {}
    dataset_id = payload.get("dataset_id")

    df, error = get_df(dataset_id)
    if error:
        return error

    clean_df, report = basic_preprocess_for_eda(df)
    DATASETS[dataset_id] = clean_df

    INSIGHTS.setdefault(dataset_id, []).append(
        f"Preprocessing completed. Final shape is {clean_df.shape[0]} rows and {clean_df.shape[1]} columns."
    )

    return success({
    "message": "Preprocessing completed",
    "columns": clean_df.columns.tolist(),
    "numeric_columns": clean_df.select_dtypes(include=["number"]).columns.tolist(),
    "profile": report
    })


@app.route("/api/charts", methods=["POST"])
def charts():
    payload = request.get_json(silent=True) or {}
    dataset_id = payload.get("dataset_id")
    y_col = payload.get("y_col")

    df, error = get_df(dataset_id)
    if error:
        return error

    if y_col and y_col not in df.columns:
        return fail(f"Target column '{y_col}' not found", 400)

    chart_list, chart_insights = generate_charts(df, y_col)

    INSIGHTS.setdefault(dataset_id, []).extend(chart_insights)

    return success({
        "charts": chart_list,
        "insights": chart_insights
    })


@app.route("/api/train", methods=["POST"])
def train():
    payload = request.get_json(silent=True) or {}
    dataset_id = payload.get("dataset_id")
    x_cols = payload.get("x_cols", [])
    y_col = payload.get("y_col")

    df, error = get_df(dataset_id)
    if error:
        return error

    if not x_cols:
        return fail("Select at least one X feature", 400)

    if not y_col:
        return fail("Select Y target column", 400)

    if y_col in x_cols:
        return fail("Y target cannot be selected as X feature", 400)

    missing = [c for c in x_cols + [y_col] if c not in df.columns]
    if missing:
        return fail(f"Columns not found: {missing}", 400)
    model_df = df[x_cols + [y_col]].copy()

    for col in x_cols:
        if model_df[col].dtype == "object":
            model_df[col] = model_df[col].astype("category").cat.codes

    result = train_best_model(model_df, x_cols, y_col)
    
    suggestions = ModelImprovementAgent().suggest(df, result)

    best = result.get("best_model", {})
    INSIGHTS.setdefault(dataset_id, []).append(
        f"Best model is {best.get('model')} with score {best.get('score')}."
    )
    INSIGHTS.setdefault(dataset_id, []).extend(suggestions)

    return success({
        "result": result,
        "suggestions": suggestions
    })


@app.route("/api/summary", methods=["POST"])
def summary():
    payload = request.get_json(silent=True) or {}
    dataset_id = payload.get("dataset_id")

    df, error = get_df(dataset_id)
    if error:
        return error

    context = "\n".join(INSIGHTS.get(dataset_id, [])) or "No insights generated yet."
    summary_text = InsightAgent().summarize(context)

    return success({"summary": summary_text})


@app.route("/api/ask", methods=["POST"])
def ask():
    payload = request.get_json(silent=True) or {}
    dataset_id = payload.get("dataset_id")
    question = payload.get("question", "").strip()

    df, error = get_df(dataset_id)
    if error:
        return error

    if not question:
        return fail("Question is required", 400)

    context = "\n".join(INSIGHTS.get(dataset_id, [])) or "No insights generated yet."
    answer = InsightAgent().answer(question, context)

    return success({"answer": answer})


if __name__ == "__main__":
    app.run(debug=True)