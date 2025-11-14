# backend/recommender.py
from __future__ import annotations
import threading
import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class _SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Recommender(metaclass=_SingletonMeta):
    """
    Expert: owns course data and TF-IDF model.
    Implements a Singleton so the app creates one shared instance.
    """

    def __init__(self, csv_path: str, text_fields=None):
        self.csv_path = csv_path
        self.df = None
        self.vectorizer = None
        self.tfidf_matrix = None
        self.text_fields = text_fields
        self.url_col = None
        self.rating_col = None
        self.mapping = {}
        self._load_data()

    def _clean_text(self, s: str) -> str:
        if pd.isna(s):
            return ""
        s = str(s).lower()
        s = re.sub(r"[^a-z0-9 ]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _detect_columns(self, df: pd.DataFrame) -> dict:
        """
        Try to detect common column names for title, url, rating, and description/headline.
        Returns a mapping like {'title': 'Course Title', 'url': 'Link', ...}
        """
        cols = {c.lower(): c for c in df.columns}
        mapping = {}

        for cand in ("title", "course_title", "course name", "name"):
            if cand in cols:
                mapping["title"] = cols[cand]
                break

        for cand in ("url", "course_url", "link", "course link"):
            if cand in cols:
                mapping["url"] = cols[cand]
                break

        for cand in ("rating", "avg_rating", "avg rating", "reviews"):
            if cand in cols:
                mapping["rating"] = cols[cand]
                break

        # description-like columns
        descs = [c for c in df.columns if "desc" in c.lower() or "headline" in c.lower() or "subtitle" in c.lower()]
        if descs:
            mapping["desc"] = descs[0]

        return mapping

    def _load_data(self):
        # Read CSV (if encoding errors happen, you can pass encoding='utf-8' or encoding='latin1')
        df = pd.read_csv(self.csv_path)
        mapping = self._detect_columns(df)

        # store mapping for debugging/inspection
        self.mapping = mapping

        # Choose columns (fall back to first column for title if nothing found)
        title_col = mapping.get("title") or df.columns[0]
        url_col = mapping.get("url")
        rating_col = mapping.get("rating")
        desc_col = mapping.get("desc")

        # ensure we have a title string column
        df["__title__"] = df[title_col].astype(str)

        # Build a combined text field for TF-IDF (title + description/headline if available)
        combined = df["__title__"].fillna("")
        if desc_col:
            combined = combined + " " + df[desc_col].astype(str).fillna("")

        combined = combined.map(self._clean_text)

        # Save references
        self.df = df.reset_index(drop=True)
        self.url_col = url_col
        self.rating_col = rating_col

        # Build TF-IDF
        # If the dataset is small, reduce max_features to avoid overfitting; 20000 is safe for larger datasets
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=20000)
        self.tfidf_matrix = self.vectorizer.fit_transform(combined)

    def recommend(self, query: str, top_n: int = 4):
        """
        Return top_n recommendations for the query: list of dicts {title, rating, url, score}
        Uses cosine similarity via linear_kernel for efficiency.
        """
        q = self._clean_text(query)
        if not q:
            return []

        q_vec = self.vectorizer.transform([q])
        cosine_similarities = linear_kernel(q_vec, self.tfidf_matrix).flatten()
        if len(cosine_similarities) == 0:
            return []

        top_n = max(1, int(top_n))
        # get top indices
        top_idx = np.argpartition(-cosine_similarities, range(min(top_n, len(cosine_similarities))))[:top_n]
        top_idx = top_idx[np.argsort(-cosine_similarities[top_idx])]

        results = []
        for idx in top_idx:
            row = self.df.iloc[int(idx)]
            res = {
                "title": row.get("__title__", ""),
                "score": float(cosine_similarities[idx]),
                "rating": float(row[self.rating_col]) if (self.rating_col and not pd.isna(row[self.rating_col])) else None,
                "url": row[self.url_col] if self.url_col else None,
            }
            results.append(res)

        return results


def create_recommender(csv_path: str) -> Recommender:
    """Factory to create or return the singleton recommender."""
    return Recommender(csv_path)
