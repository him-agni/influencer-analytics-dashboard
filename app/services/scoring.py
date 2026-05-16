"""
Influence scoring service.
Computes a composite score (0-100) from multiple weighted factors.
"""

from typing import Any
from app.core.logging import logger


class InfluenceScorer:
    """
    Computes a composite Influence Score (0-100) weighted across:
    - Subscriber count (20%)
    - Engagement rate (30%)
    - Growth rate (20%)
    - Content consistency (15%)
    - Sentiment ratio (15%)
    """

    # Benchmark thresholds for normalization
    BENCHMARKS = {
        "subscribers": {"low": 1_000, "high": 1_000_000},
        "engagement_rate": {"low": 0.5, "high": 10.0},
        "growth_rate": {"low": -5.0, "high": 20.0},
        "posts_per_month": {"low": 1, "high": 30},
        "sentiment_pct": {"low": 30.0, "high": 95.0},
    }

    WEIGHTS = {
        "subscribers": 0.20,
        "engagement_rate": 0.30,
        "growth_rate": 0.20,
        "consistency": 0.15,
        "sentiment": 0.15,
    }

    @staticmethod
    def _normalize(value: float, low: float, high: float) -> float:
        """Normalize a value to 0-100 range using min-max scaling."""
        if high <= low:
            return 50.0
        score = ((value - low) / (high - low)) * 100
        return max(0.0, min(100.0, score))

    def compute_score(
        self,
        subscribers: int = 0,
        engagement_rate: float = 0.0,
        growth_rate: float = 0.0,
        posts_per_month: float = 0.0,
        positive_sentiment_pct: float = 50.0,
    ) -> dict[str, Any]:
        """
        Compute the composite influence score.

        Returns dict with overall score and per-factor breakdown.
        """
        b = self.BENCHMARKS
        sub_score = self._normalize(subscribers, b["subscribers"]["low"], b["subscribers"]["high"])
        eng_score = self._normalize(engagement_rate, b["engagement_rate"]["low"], b["engagement_rate"]["high"])
        growth_score = self._normalize(growth_rate, b["growth_rate"]["low"], b["growth_rate"]["high"])
        consistency_score = self._normalize(posts_per_month, b["posts_per_month"]["low"], b["posts_per_month"]["high"])
        sentiment_score = self._normalize(positive_sentiment_pct, b["sentiment_pct"]["low"], b["sentiment_pct"]["high"])

        w = self.WEIGHTS
        overall = (
            sub_score * w["subscribers"]
            + eng_score * w["engagement_rate"]
            + growth_score * w["growth_rate"]
            + consistency_score * w["consistency"]
            + sentiment_score * w["sentiment"]
        )

        result = {
            "overall_score": round(overall, 1),
            "breakdown": {
                "subscribers": {"score": round(sub_score, 1), "weight": w["subscribers"], "raw_value": subscribers},
                "engagement_rate": {"score": round(eng_score, 1), "weight": w["engagement_rate"], "raw_value": engagement_rate},
                "growth_rate": {"score": round(growth_score, 1), "weight": w["growth_rate"], "raw_value": growth_rate},
                "consistency": {"score": round(consistency_score, 1), "weight": w["consistency"], "raw_value": posts_per_month},
                "sentiment": {"score": round(sentiment_score, 1), "weight": w["sentiment"], "raw_value": positive_sentiment_pct},
            },
            "tier": self._get_tier(overall),
        }

        logger.info(f"Influence score computed: {overall:.1f} ({result['tier']})")
        return result

    @staticmethod
    def _get_tier(score: float) -> str:
        if score >= 80:
            return "Elite"
        elif score >= 60:
            return "Rising Star"
        elif score >= 40:
            return "Growing"
        elif score >= 20:
            return "Emerging"
        else:
            return "New"


influence_scorer = InfluenceScorer()
