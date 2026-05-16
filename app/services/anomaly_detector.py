"""
Service for heuristic-based anomaly detection.
Detects viral spikes, fake followers, suspicious growth, and follower drops.
"""

import statistics
from typing import Any

from app.models.profile import Profile
from app.models.post import Post
from app.models.follower_growth import FollowerGrowth


class AnomalyDetector:
    def __init__(
        self,
        viral_multiplier: float = 3.0,
        suspicious_growth_pct: float = 15.0,
        drop_threshold_pct: float = 5.0,
    ):
        self.viral_multiplier = viral_multiplier
        self.suspicious_growth_pct = suspicious_growth_pct
        self.drop_threshold_pct = drop_threshold_pct

    # ── Viral Post Detection ──────────────────────────────────

    def detect_viral_posts(self, posts: list[Post]) -> list[dict]:
        if not posts:
            return []

        views = [p.views for p in posts if p.views > 0]
        if not views:
            return []

        median_views = statistics.median(views)
        if median_views == 0:
            return []

        viral_posts = []
        for p in posts:
            if p.views >= (median_views * self.viral_multiplier) and p.views > 1000:
                multiplier = p.views / median_views
                viral_posts.append({
                    "post_id": p.id,
                    "video_id": p.video_id,
                    "title": p.title,
                    "views": p.views,
                    "expected_views": int(median_views),
                    "multiplier": round(multiplier, 1),
                    "published_at": p.published_at.isoformat() if p.published_at else None,
                })

        viral_posts.sort(key=lambda x: x["multiplier"], reverse=True)
        return viral_posts

    # ── Suspicious Growth Spikes ──────────────────────────────

    def detect_suspicious_growth(self, growth_history: list[FollowerGrowth]) -> list[dict]:
        if len(growth_history) < 2:
            return []

        sorted_growth = sorted(growth_history, key=lambda x: x.date)

        spikes = []
        for i in range(1, len(sorted_growth)):
            prev = sorted_growth[i - 1]
            curr = sorted_growth[i]

            if prev.subscribers > 0:
                jump_pct = ((curr.subscribers - prev.subscribers) / prev.subscribers) * 100
                if jump_pct >= self.suspicious_growth_pct and curr.subscribers > 1000:
                    spikes.append({
                        "date": curr.date.isoformat(),
                        "old_subscribers": prev.subscribers,
                        "new_subscribers": curr.subscribers,
                        "percentage_jump": round(jump_pct, 2),
                    })

        return spikes

    # ── Follower Drop Detection ───────────────────────────────

    def detect_follower_drops(self, growth_history: list[FollowerGrowth]) -> list[dict]:
        """Detect days where followers dropped significantly.
        
        A drop is flagged when followers decrease by more than `drop_threshold_pct`
        in a single snapshot interval. Common causes: bot purges by the platform,
        controversy-driven unsubscribes, or purchased followers expiring.
        """
        if len(growth_history) < 2:
            return []

        sorted_growth = sorted(growth_history, key=lambda x: x.date)

        drops = []
        for i in range(1, len(sorted_growth)):
            prev = sorted_growth[i - 1]
            curr = sorted_growth[i]

            if prev.subscribers > 0:
                change_pct = ((curr.subscribers - prev.subscribers) / prev.subscribers) * 100
                lost = prev.subscribers - curr.subscribers
                # Only flag negative changes exceeding the threshold
                if change_pct <= -self.drop_threshold_pct and lost > 100:
                    drops.append({
                        "date": curr.date.isoformat(),
                        "old_subscribers": prev.subscribers,
                        "new_subscribers": curr.subscribers,
                        "lost_count": lost,
                        "percentage_drop": round(abs(change_pct), 2),
                    })

        drops.sort(key=lambda x: x["percentage_drop"], reverse=True)
        return drops

    # ── Fake Follower Heuristics ──────────────────────────────

    def detect_fake_followers(
        self,
        profile: Profile,
        growth_spikes: list[dict],
        follower_drops: list[dict],
        engagement_rate: float,
    ) -> dict:
        flags = []
        risk_level = "Low"

        # Rule 1: Very low engagement for channel size
        if profile.subscribers > 50000 and engagement_rate < 0.5:
            flags.append(
                f"Abnormally low engagement rate ({engagement_rate:.2f}%) for {profile.subscribers:,} subscribers."
            )
        elif profile.subscribers > 10000 and engagement_rate < 0.1:
            flags.append(f"Severely low engagement rate ({engagement_rate:.2f}%).")

        # Rule 2: Sudden massive growth spikes + low engagement
        if growth_spikes:
            flags.append(f"Detected {len(growth_spikes)} suspicious single-day follower spikes (>15%).")
            if engagement_rate < 1.0:
                flags.append("Suspicious growth combined with low engagement.")
                risk_level = "High"
            else:
                risk_level = "Medium"

        # Rule 3: Follower drops suggest bot purges
        if follower_drops:
            total_lost = sum(d["lost_count"] for d in follower_drops)
            flags.append(
                f"Detected {len(follower_drops)} follower drop event(s), "
                f"losing {total_lost:,} subscribers total — possible bot purge."
            )
            if growth_spikes:
                # Growth spikes followed by drops is classic bot behavior
                flags.append("Pattern detected: growth spikes followed by follower drops (buy-then-purge cycle).")
                risk_level = "High"

        # Final risk assessment
        if len(flags) >= 2 and risk_level != "High":
            risk_level = "Medium"

        if len(flags) >= 3:
            risk_level = "High"

        return {
            "risk_level": risk_level,
            "flags": flags,
        }

    # ── Main Analysis Entry Point ─────────────────────────────

    def analyze_profile(
        self,
        profile: Profile,
        posts: list[Post],
        growth_history: list[FollowerGrowth],
        engagement_rate: float,
    ) -> dict:
        viral_posts = self.detect_viral_posts(posts)
        growth_spikes = self.detect_suspicious_growth(growth_history)
        follower_drops = self.detect_follower_drops(growth_history)
        fake_follower_analysis = self.detect_fake_followers(
            profile, growth_spikes, follower_drops, engagement_rate
        )

        return {
            "viral_posts": viral_posts,
            "suspicious_growth_spikes": growth_spikes,
            "follower_drops": follower_drops,
            "fake_follower_risk": fake_follower_analysis["risk_level"],
            "fake_follower_flags": fake_follower_analysis["flags"],
        }


anomaly_detector = AnomalyDetector()

