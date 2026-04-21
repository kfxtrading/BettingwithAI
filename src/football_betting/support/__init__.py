"""Support FAQ intent classification (v0.3.1)."""
from __future__ import annotations

from football_betting.support.dataset import (
    DatasetSplit,
    load_dataset,
    stratified_split,
)
from football_betting.support.cluster import IntentClusterer
from football_betting.support.embedding_model import (
    EmbeddingIntentRetriever,
    EmbeddingPrediction,
)
from football_betting.support.intent_model import IntentClassifier, IntentPrediction
from football_betting.support.reranker import CrossEncoderReranker
from football_betting.support.text import normalize
from football_betting.support.trainer import (
    train_all,
    train_embeddings_all,
    train_embeddings_one_language,
    train_one_language,
)

__all__ = [
    "CrossEncoderReranker",
    "DatasetSplit",
    "EmbeddingIntentRetriever",
    "EmbeddingPrediction",
    "IntentClassifier",
    "IntentClusterer",
    "IntentPrediction",
    "load_dataset",
    "normalize",
    "stratified_split",
    "train_all",
    "train_embeddings_all",
    "train_embeddings_one_language",
    "train_one_language",
]
