"""Support FAQ intent classification (v0.3.1)."""
from __future__ import annotations

from football_betting.support.augment import (
    AugmentStats,
    Augmenter,
    BacktranslationAugmenter,
    NoiseAugmenter,
    ParaphraseAugmenter,
    augment_dataset,
    build_marian_backtranslator,
    build_openai_paraphraser,
)
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
from football_betting.support.hierarchical import (
    HierarchicalIntentClassifier,
    HierarchicalPrediction,
)
from football_betting.support.intent_model import IntentClassifier, IntentPrediction
from football_betting.support.ood import OODSeed, build_ood_rows, get_seed_bank
from football_betting.support.reranker import CrossEncoderReranker
from football_betting.support.text import normalize
from football_betting.support.trainer import (
    train_all,
    train_embeddings_all,
    train_embeddings_one_language,
    train_hierarchical_all,
    train_hierarchical_one_language,
    train_one_language,
    train_transformer_all,
    train_transformer_one_language,
)

__all__ = [
    "AugmentStats",
    "Augmenter",
    "BacktranslationAugmenter",
    "CrossEncoderReranker",
    "DatasetSplit",
    "EmbeddingIntentRetriever",
    "EmbeddingPrediction",
    "HierarchicalIntentClassifier",
    "HierarchicalPrediction",
    "IntentClassifier",
    "IntentClusterer",
    "IntentPrediction",
    "NoiseAugmenter",
    "OODSeed",
    "ParaphraseAugmenter",
    "augment_dataset",
    "build_marian_backtranslator",
    "build_openai_paraphraser",
    "build_ood_rows",
    "get_seed_bank",
    "load_dataset",
    "normalize",
    "stratified_split",
    "train_all",
    "train_embeddings_all",
    "train_embeddings_one_language",
    "train_hierarchical_all",
    "train_hierarchical_one_language",
    "train_one_language",
    "train_transformer_all",
    "train_transformer_one_language",
]
