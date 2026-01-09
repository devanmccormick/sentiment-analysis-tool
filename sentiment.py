"""
Sentiment analysis using a pre-trained NLP model.
Maps model output to positive, neutral, or negative with optional confidence.
Falls back to VADER if the transformer pipeline cannot be loaded (e.g. torch version).
"""

from typing import List, Tuple

_pipeline = None
_use_vader = None


def _get_pipeline():
    """Load the pre-trained sentiment pipeline once, or None to use VADER fallback."""
    global _pipeline, _use_vader
    if _use_vader is False and _pipeline is not None:
        return _pipeline
    if _use_vader is True:
        return None
    try:
        from transformers import pipeline
        _pipeline = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            top_k=None,
        )
        _use_vader = False
        return _pipeline
    except Exception:
        _use_vader = True
        return None


def _analyze_vader(text: str) -> Tuple[str, float]:
    """Use VADER for sentiment when transformer is unavailable."""
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    if not hasattr(_analyze_vader, "_analyzer"):
        _analyze_vader._analyzer = SentimentIntensityAnalyzer()
    compound = _analyze_vader._analyzer.polarity_scores(str(text).strip()[:512])["compound"]
    if compound >= 0.05:
        return "positive", round(min(1.0, 0.5 + compound / 2), 4)
    if compound <= -0.05:
        return "negative", round(min(1.0, 0.5 + abs(compound) / 2), 4)
    return "neutral", round(0.5 + (0.5 - abs(compound)), 4)


def analyze_text(text: str) -> Tuple[str, float]:
    """
    Analyze a single text and return (label, confidence).
    Label is one of: positive, neutral, negative.
    """
    if not text or not str(text).strip():
        return "neutral", 0.0
    pipe = _get_pipeline()
    if pipe is None:
        return _analyze_vader(text)
    result = pipe(str(text).strip()[:512])[0]
    if isinstance(result, list):
        by_label = {r["label"].lower(): r["score"] for r in result}
    else:
        by_label = {result["label"].lower(): result["score"]}
    label = max(by_label, key=by_label.get)
    confidence = by_label[label]
    normalized = _normalize_label(label)
    return normalized, round(confidence, 4)


def _normalize_label(label: str) -> str:
    """Map model labels to positive, neutral, negative."""
    label = label.lower()
    if label in ("positive", "pos"):
        return "positive"
    if label in ("negative", "neg"):
        return "negative"
    return "neutral"


def analyze_batch(texts: List[str]) -> List[Tuple[str, float]]:
    """Analyze a list of texts; returns list of (label, confidence)."""
    return [analyze_text(t) for t in texts]
