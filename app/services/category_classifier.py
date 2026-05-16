"""
Category classification service.
Analyzes channel text and videos to classify into distinct categories.
"""

import re
from collections import Counter
from typing import Any

class CategoryClassifier:
    """Heuristic keyword-based classifier for YouTube channel content."""

    CATEGORIES = {
        "Fitness": ["workout", "fitness", "gym", "muscle", "health", "diet", "protein", "training", "exercise", "bodybuilding", "crossfit", "yoga", "pilates"],
        "Travel": ["travel", "vlog", "explore", "journey", "trip", "vacation", "tour", "backpacking", "hotel", "resort", "destination", "adventure"],
        "Food": ["food", "recipe", "cook", "cooking", "eat", "tasting", "kitchen", "restaurant", "chef", "baking", "meal", "delicious", "vegan"],
        "Family": ["family", "kids", "parenting", "baby", "mom", "dad", "children", "toddler", "pregnancy", "vlog", "house", "home"],
        "Career": ["career", "job", "work", "resume", "interview", "office", "professional", "success", "productivity", "leadership", "management"],
        "Learning": ["learn", "education", "tutorial", "how to", "study", "science", "history", "math", "course", "skill", "knowledge", "explain"],
        "Beauty": ["beauty", "makeup", "skincare", "cosmetics", "hair", "fashion", "style", "grwm", "routine", "haul", "outfit", "glam"],
        "Gaming": ["gaming", "gameplay", "stream", "esports", "playthrough", "xbox", "playstation", "nintendo", "pc", "gamer", "multiplayer", "minecraft", "roblox"],
        "Tech": ["tech", "technology", "review", "gadget", "smartphone", "laptop", "computer", "software", "apple", "samsung", "unboxing", "setup"],
        "Finance": ["finance", "money", "invest", "stock", "crypto", "bitcoin", "wealth", "trading", "business", "economy", "budget", "passive income"],
        "Entertainment": ["comedy", "funny", "prank", "challenge", "reaction", "movie", "music", "song", "cover", "dance", "entertainment", "sketch"]
    }

    def __init__(self):
        # Compile regex patterns for performance
        self.compiled_categories = {}
        for category, keywords in self.CATEGORIES.items():
            pattern = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b'
            self.compiled_categories[category] = re.compile(pattern, re.IGNORECASE)

    def classify_text(self, text: str) -> list[str]:
        """Return a list of categories found in the given text."""
        if not text:
            return []
        
        matches = []
        for category, pattern in self.compiled_categories.items():
            if pattern.search(text):
                matches.append(category)
        return matches

    def analyze_profile_categories(self, profile: Any, posts: list[Any]) -> list[dict[str, Any]]:
        """
        Analyze a profile and its posts to generate a category distribution.
        Returns a list of dicts: {"category": "Fitness", "percentage": 60.0}
        """
        category_counts = Counter()
        
        # 1. Analyze profile bio (weight = 3x)
        bio_text = f"{profile.display_name or ''} {profile.bio or ''}"
        bio_cats = self.classify_text(bio_text)
        for cat in bio_cats:
            category_counts[cat] += 3
            
        # 2. Analyze posts (weight = 1x per post)
        for post in posts:
            post_text = f"{post.title or ''} {post.description or ''}"
            post_cats = self.classify_text(post_text)
            
            # Also extract hashtags which are strong indicators
            hashtags = re.findall(r"#(\w+)", post_text.lower())
            hashtag_text = " ".join(hashtags)
            hash_cats = self.classify_text(hashtag_text)
            
            # Combine post and hashtag matches for this post
            all_post_cats = set(post_cats + hash_cats)
            for cat in all_post_cats:
                category_counts[cat] += 1
                
        total = sum(category_counts.values())
        
        if total == 0:
            # Fallback if no categories matched
            return [{"category": "General", "percentage": 100.0}]
            
        # Convert to percentages
        results = []
        for cat, count in category_counts.most_common():
            pct = round((count / total) * 100, 1)
            results.append({
                "category": cat,
                "percentage": pct
            })
            
        return results

category_classifier = CategoryClassifier()
