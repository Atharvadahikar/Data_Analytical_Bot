# Data Analytical Bot

A Flask web app for uploading CSV files, profiling/cleaning data, generating Plotly charts, training simple scikit-learn models, and asking for AI-powered business insights with Groq.

## Features

- CSV upload with file size and column validation
- Dataset profile: rows, columns, missing values, duplicates, numeric/categorical columns
- Basic preprocessing for EDA
- Plotly charts for distributions, relationships, outliers, and top categories
- Automatic ML model comparison for classification/regression
- Groq-powered summary and Q&A

## Requirements

- Python 3.11+ recommended
- A Groq API key for AI summary/Q&A features

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
FLASK_DEBUG=false
CORS_ORIGINS=http://localhost:5000
```

Run locally:

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

## Production Notes

- Do not run with `FLASK_DEBUG=true` in production.
- Set `CORS_ORIGINS` to your real frontend/backend URL, for example `https://your-app.onrender.com`.
- The app currently stores uploaded datasets in memory. For production use, add persistent storage such as PostgreSQL, Redis, S3-compatible object storage, or temporary files with cleanup.
- This app uses CPU-heavy libraries like pandas and scikit-learn, so choose a host with enough RAM for your CSV sizes.

## Example Production Command

```bash
gunicorn app:app
```

## Useful Environment Variables

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
FLASK_DEBUG=false
CORS_ORIGINS=https://your-domain.com
```
