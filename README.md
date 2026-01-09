# Sentiment Analysis Tool

Python-based sentiment analysis for customer reviews. Upload a CSV, get positive/neutral/negative labels and optional confidence. Runs locally with a pre-trained model; no training or deployment required.

## Setup

1. Create a virtual environment (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app (with the venv activated, or use the venv’s Python):

   ```bash
   streamlit run app.py
   ```

   If `streamlit` is not found, run:

   ```bash
   python -m streamlit run app.py
   ```

   Open the URL shown in the terminal (usually http://localhost:8501).

## Usage

1. **Upload CSV** — Use a CSV that has at least one column with review text (e.g. `review`, `text`, `comment`).
2. **Select text column** — Choose the column that contains the text to analyze.
3. **Run analysis** — Click “Run sentiment analysis”. The first run may download the model.
4. **View results** — See the summary (counts and chart), example positive/negative reviews, and confidence.
5. **Download** — Use “Download processed CSV” to get the same data with `sentiment` and `sentiment_confidence` columns.

## Input / output

- **Input:** CSV with a text column (headers like `review`, `text`, `content` are auto-detected).
- **Output:** Same CSV plus:
  - `sentiment`: `positive`, `neutral`, or `negative`
  - `sentiment_confidence`: score between 0 and 1

## Project layout

- `app.py` — Streamlit UI (upload, run, summary, examples, download).
- `admin_utils.py` — Visitor logging (python-ipware + ipinfo.io), save uploads.
- `sentiment.py` — Pre-trained model loading and prediction.
- `csv_utils.py` — CSV read, text column detection, sentiment run, export.
- `requirements.txt` — Python dependencies.

## License

**Private** — This project is private and not licensed for public or commercial use.
