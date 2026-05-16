"""
Sentiment analysis service using HuggingFace Transformers.
Lazy-loads the model on first use to avoid startup delays.
"""

from typing import Any
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class SentimentAnalyzer:
    """Analyzes comment sentiment using a pre-trained DistilBERT model."""

    def __init__(self):
        self._pipeline = None
        self._enabled = settings.sentiment_enabled

    def _load_model(self):
        if self._pipeline is None and self._enabled:
            try:
                from transformers import pipeline
                logger.info(f"Loading sentiment model: {settings.sentiment_model}")
                self._pipeline = pipeline(
                    "sentiment-analysis", model=settings.sentiment_model,
                    truncation=True, max_length=512,
                )
                logger.info("Sentiment model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load sentiment model: {e}")
                self._enabled = False

    def analyze_batch(self, texts: list[str], batch_size: int = 32) -> list[dict[str, Any]]:
        """Analyze sentiment for a batch of texts."""
        neutral = {"label": "NEUTRAL", "score": 0.5}
        if not self._enabled or not texts:
            return [neutral] * len(texts)
        self._load_model()
        if self._pipeline is None:
            return [neutral] * len(texts)
        try:
            cleaned = [(t[:1000] if t else "neutral") for t in texts]
            cleaned = [t if t.strip() else "neutral" for t in cleaned]
            results = self._pipeline(cleaned, batch_size=batch_size)
            return [{"label": r["label"], "score": round(r["score"], 4)} for r in results]
        except Exception as e:
            logger.error(f"Batch sentiment error: {e}")
            return [neutral] * len(texts)

    def analyze_comments(self, comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add sentiment_score and sentiment_label to each comment dict."""
        if not comments:
            return comments
        texts = [c.get("text", "") for c in comments]
        results = self.analyze_batch(texts)
        for comment, result in zip(comments, results):
            comment["sentiment_label"] = result["label"]
            comment["sentiment_score"] = result["score"]
        return comments

    def get_sentiment_summary(self, comments: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate a sentiment summary from analyzed comments."""
        if not comments:
            return {"positive_count": 0, "negative_count": 0, "neutral_count": 0,
                    "positive_pct": 0.0, "negative_pct": 0.0, "neutral_pct": 0.0, "avg_score": 0.0}
        total = len(comments)
        pos = sum(1 for c in comments if c.get("sentiment_label") == "POSITIVE")
        neg = sum(1 for c in comments if c.get("sentiment_label") == "NEGATIVE")
        neu = total - pos - neg
        avg_score = sum(c.get("sentiment_score", 0.5) for c in comments) / total
        return {
            "positive_count": pos, "negative_count": neg, "neutral_count": neu,
            "positive_pct": round((pos / total) * 100, 1),
            "negative_pct": round((neg / total) * 100, 1),
            "neutral_pct": round((neu / total) * 100, 1),
            "avg_score": round(avg_score, 4),
        }


sentiment_analyzer = SentimentAnalyzer()
