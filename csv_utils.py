"""
CSV handling: read uploads, detect text column, add sentiment and confidence, export.
"""

import io
from typing import Optional, List, Tuple

import pandas as pd

from sentiment import analyze_batch


# Common column names that likely contain review text
TEXT_CANDIDATES = (
    "review", "reviews", "text", "content", "comment", "comments",
    "feedback", "message", "body", "description", "review_text", "customer_review",
)


def detect_text_column(df: pd.DataFrame) -> Optional[str]:
    """Return the first column name that looks like review text, or None."""
    cols_lower = [c.lower().strip() for c in df.columns]
    for candidate in TEXT_CANDIDATES:
        for i, col in enumerate(cols_lower):
            if candidate in col or col in candidate:
                return df.columns[i]
    if len(df.columns) == 1:
        return df.columns[0]
    for col in df.columns:
        if df[col].dtype == object and df[col].astype(str).str.len().median() > 20:
            return col
    return None


def run_sentiment_on_df(
    df: pd.DataFrame,
    text_column: str,
) -> pd.DataFrame:
    """
    Add 'sentiment' and 'sentiment_confidence' columns using the given text column.
    Returns a new DataFrame.
    """
    texts = df[text_column].fillna("").astype(str).tolist()
    results = analyze_batch(texts)
    out = df.copy()
    out["sentiment"] = [r[0] for r in results]
    out["sentiment_confidence"] = [r[1] for r in results]
    return out


def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    """Read an uploaded Streamlit file (BytesIO) as CSV."""
    return pd.read_csv(io.BytesIO(uploaded_file.getvalue()))


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Export DataFrame to CSV as bytes for download."""
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf.getvalue()
