"""
Streamlit UI for sentiment analysis on uploaded CSV files.
Admin panel: open https://your-app.streamlit.app/?admin=YOUR_SECRET (no button; direct URL).
"""

from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

import streamlit as st
import pandas as pd

from csv_utils import (
    read_uploaded_csv,
    detect_text_column,
    run_sentiment_on_df,
    to_csv_bytes,
)
from admin_utils import (
    log_visitor,
    save_upload,
    get_visitor_log,
    get_uploaded_files,
)


def _admin_secret():
    try:
        return st.secrets.get("ADMIN_SECRET", "")
    except Exception:
        pass
    import os
    return os.environ.get("ADMIN_SECRET", "")


def _render_admin():
    """Admin panel: visitor log (IP, city, timestamp) and downloadable uploads."""
    st.title("Admin panel")
    st.caption("Visitor log and uploaded files from the deployed app.")

    st.subheader("Visitor log (IP, city, timestamp)")
    visitors = get_visitor_log()
    if not visitors:
        st.info("No visitor entries yet.")
    else:
        st.dataframe(pd.DataFrame(visitors), width="stretch", hide_index=True)
        import io
        buf = io.BytesIO()
        pd.DataFrame(visitors).to_csv(buf, index=False)
        st.download_button("Download visitor log as CSV", data=buf.getvalue(), file_name="visitor_log.csv", mime="text/csv")

    st.subheader("Uploaded files (CSV or any)")
    files = get_uploaded_files()
    if not files:
        st.info("No uploaded files saved yet.")
    else:
        for i, (name, path) in enumerate(files):
            data = path.read_bytes()
            st.download_button(label=f"Download {name}", data=data, file_name=name, mime="application/octet-stream", key=f"dl_upload_{i}_{path.name}")


# Page config must be first Streamlit command
st.set_page_config(page_title="Sentiment Analysis", layout="wide")

# Admin route: /?admin=SECRET — no button; go to https://your-app.streamlit.app/?admin=YOUR_SECRET
try:
    q = st.query_params
    admin_param = q.get("admin") or ""
except Exception:
    try:
        q = st.experimental_get_query_params()
        admin_param = (q.get("admin") or [""])[0]
    except Exception:
        admin_param = ""
secret = _admin_secret()
if secret and admin_param == secret:
    _render_admin()
    st.stop()

# Main app: log visitor once per session, then show sentiment UI
if "visitor_logged" not in st.session_state:
    try:
        log_visitor()
        st.session_state["visitor_logged"] = True
    except Exception:
        st.session_state["visitor_logged"] = True

st.title("Customer review sentiment analysis")
st.markdown("Upload a CSV with a text column (e.g. reviews). We assign **positive**, **neutral**, or **negative** and optional confidence.")

uploaded = st.file_uploader("Upload CSV", type=["csv"])
if not uploaded:
    st.info("Upload a CSV file to start.")
    st.stop()

# Save copy for admin (any upload)
try:
    save_upload(uploaded, uploaded.name)
except Exception:
    pass

df = read_uploaded_csv(uploaded)
detected = detect_text_column(df)
text_col = st.selectbox(
    "Column containing review text",
    options=df.columns.tolist(),
    index=df.columns.tolist().index(detected) if detected and detected in df.columns else 0,
)

if st.button("Run sentiment analysis"):
    with st.spinner("Running sentiment analysis…"):
        result = run_sentiment_on_df(df, text_col)
    st.session_state["result_df"] = result
    st.session_state["text_col"] = text_col

if "result_df" not in st.session_state:
    st.stop()

result = st.session_state["result_df"]
text_col = st.session_state["text_col"]

st.subheader("Summary")
counts = result["sentiment"].value_counts()
cols = st.columns(3)
for i, (label, count) in enumerate(counts.items()):
    cols[i].metric(label.capitalize(), int(count))
st.bar_chart(counts)

st.subheader("Example positive reviews")
pos = result[result["sentiment"] == "positive"].head(5)
if pos.empty:
    st.caption("No positive examples.")
else:
    for _, row in pos.iterrows():
        st.caption(f"Confidence: {row['sentiment_confidence']}")
        st.write(row[text_col][:300] + ("…" if len(str(row[text_col])) > 300 else ""))

st.subheader("Example negative reviews")
neg = result[result["sentiment"] == "negative"].head(5)
if neg.empty:
    st.caption("No negative examples.")
else:
    for _, row in neg.iterrows():
        st.caption(f"Confidence: {row['sentiment_confidence']}")
        st.write(row[text_col][:300] + ("…" if len(str(row[text_col])) > 300 else ""))

st.subheader("Download")
st.download_button(
    label="Download processed CSV",
    data=to_csv_bytes(result),
    file_name="reviews_with_sentiment.csv",
    mime="text/csv",
)
