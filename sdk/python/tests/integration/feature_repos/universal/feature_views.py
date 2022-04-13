from datetime import timedelta
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

from feast import (
    Array,
    Feature,
    FeatureView,
    Field,
    Float32,
    Float64,
    Int32,
    OnDemandFeatureView,
    PushSource,
    ValueType,
)
from feast.data_source import DataSource, RequestSource
from feast.types import FeastType
from tests.integration.feature_repos.universal.entities import location


def driver_feature_view(
    data_source: DataSource,
    name="test_correctness",
    infer_features: bool = False,
    dtype: FeastType = Float32,
) -> FeatureView:
    return FeatureView(
        name=name,
        entities=["driver"],
        schema=None if infer_features else [Field(name="value", dtype=dtype)],
        ttl=timedelta(days=5),
        source=data_source,
    )


def global_feature_view(
    data_source: DataSource,
    name="test_entityless",
    infer_features: bool = False,
    value_type: ValueType = ValueType.INT32,
) -> FeatureView:
    return FeatureView(
        name=name,
        entities=[],
        # Test that Features still work for FeatureViews.
        features=None
        if infer_features
        else [Feature(name="entityless_value", dtype=value_type)],
        ttl=timedelta(days=5),
        source=data_source,
    )


def conv_rate_plus_100(features_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame()
    df["conv_rate_plus_100"] = features_df["conv_rate"] + 100
    df["conv_rate_plus_val_to_add"] = (
        features_df["conv_rate"] + features_df["val_to_add"]
    )
    df["conv_rate_plus_100_rounded"] = (
        df["conv_rate_plus_100"].astype("float").round().astype(pd.Int32Dtype())
    )
    return df


def conv_rate_plus_100_feature_view(
    sources: Dict[str, Union[RequestSource, FeatureView]],
    infer_features: bool = False,
    features: Optional[List[Feature]] = None,
) -> OnDemandFeatureView:
    # Test that positional arguments and Features still work for ODFVs.
    _features = features or [
        Feature(name="conv_rate_plus_100", dtype=ValueType.DOUBLE),
        Feature(name="conv_rate_plus_val_to_add", dtype=ValueType.DOUBLE),
        Feature(name="conv_rate_plus_100_rounded", dtype=ValueType.INT32),
    ]
    return OnDemandFeatureView(
        conv_rate_plus_100.__name__,
        [] if infer_features else _features,
        sources,
        conv_rate_plus_100,
    )


def similarity(features_df: pd.DataFrame) -> pd.DataFrame:
    if features_df.size == 0:
        # give hint to Feast about return type
        df = pd.DataFrame({"cos_double": [0.0]})
        df["cos_float"] = df["cos_double"].astype(np.float32)
        return df
    vectors_a = features_df["embedding_double"].apply(np.array)
    vectors_b = features_df["vector_double"].apply(np.array)
    dot_products = vectors_a.mul(vectors_b).apply(sum)
    norms_q = vectors_a.apply(np.linalg.norm)
    norms_doc = vectors_b.apply(np.linalg.norm)
    df = pd.DataFrame()
    df["cos_double"] = dot_products / (norms_q * norms_doc)
    df["cos_float"] = df["cos_double"].astype(np.float32)
    return df


def similarity_feature_view(
    sources: Dict[str, Union[RequestSource, FeatureView]],
    infer_features: bool = False,
    features: Optional[List[Feature]] = None,
) -> OnDemandFeatureView:
    _fields = [
        Field(name="cos_double", dtype=Float64),
        Field(name="cos_float", dtype=Float32),
    ]
    if features is not None:
        _fields = [Field.from_feature(feature) for feature in features]

    return OnDemandFeatureView(
        name=similarity.__name__,
        sources=sources,
        schema=[] if infer_features else _fields,
        udf=similarity,
    )


def create_conv_rate_request_source():
    return RequestSource(
        name="conv_rate_input", schema=[Field(name="val_to_add", dtype=Int32)],
    )


def create_similarity_request_source():
    return RequestSource(
        name="similarity_input",
        schema={
            "vector_double": ValueType.DOUBLE_LIST,
            "vector_float": ValueType.FLOAT_LIST,
        },
    )


def create_item_embeddings_feature_view(source, infer_features: bool = False):
    item_embeddings_feature_view = FeatureView(
        name="item_embeddings",
        entities=["item"],
        schema=None
        if infer_features
        else [
            Field(name="embedding_double", dtype=Array(Float64)),
            Field(name="embedding_float", dtype=Array(Float32)),
        ],
        batch_source=source,
        ttl=timedelta(hours=2),
    )
    return item_embeddings_feature_view


def create_driver_hourly_stats_feature_view(source, infer_features: bool = False):
    driver_stats_feature_view = FeatureView(
        name="driver_stats",
        entities=["driver"],
        schema=None
        if infer_features
        else [
            Field(name="conv_rate", dtype=Float32),
            Field(name="acc_rate", dtype=Float32),
            Field(name="avg_daily_trips", dtype=Int32),
        ],
        source=source,
        ttl=timedelta(hours=2),
    )
    return driver_stats_feature_view


def create_customer_daily_profile_feature_view(source, infer_features: bool = False):
    customer_profile_feature_view = FeatureView(
        name="customer_profile",
        entities=["customer_id"],
        schema=None
        if infer_features
        else [
            Field(name="current_balance", dtype=Float32),
            Field(name="avg_passenger_count", dtype=Float32),
            Field(name="lifetime_trip_count", dtype=Int32),
        ],
        source=source,
        ttl=timedelta(days=2),
    )
    return customer_profile_feature_view


def create_global_stats_feature_view(source, infer_features: bool = False):
    global_stats_feature_view = FeatureView(
        name="global_stats",
        entities=[],
        features=None
        if infer_features
        else [
            # Test that Features still work for FeatureViews.
            Feature(name="num_rides", dtype=ValueType.INT32),
            Feature(name="avg_ride_length", dtype=ValueType.FLOAT),
        ],
        source=source,
        ttl=timedelta(days=2),
    )
    return global_stats_feature_view


def create_order_feature_view(source, infer_features: bool = False):
    return FeatureView(
        name="order",
        entities=["driver", "customer_id"],
        schema=None
        if infer_features
        else [Field(name="order_is_success", dtype=Int32)],
        source=source,
        ttl=timedelta(days=2),
    )


def create_location_stats_feature_view(source, infer_features: bool = False):
    location_stats_feature_view = FeatureView(
        name="location_stats",
        entities=[location()],
        schema=None if infer_features else [Field(name="temperature", dtype=Int32)],
        source=source,
        ttl=timedelta(days=2),
    )
    return location_stats_feature_view


def create_field_mapping_feature_view(source):
    return FeatureView(
        name="field_mapping",
        entities=[],
        # Test that Features still work for FeatureViews.
        features=[Feature(name="feature_name", dtype=ValueType.INT32)],
        source=source,
        ttl=timedelta(days=2),
    )


def create_pushable_feature_view(batch_source: DataSource):
    push_source = PushSource(
        name="location_stats_push_source",
        schema={
            "location_id": ValueType.INT64,
            "temperature": ValueType.INT32,
            "timestamp": ValueType.UNIX_TIMESTAMP,
        },
        batch_source=batch_source,
    )
    return FeatureView(
        name="pushable_location_stats",
        entities=["location_id"],
        # Test that Features still work for FeatureViews.
        features=[Feature(name="temperature", dtype=ValueType.INT32)],
        ttl=timedelta(days=2),
        source=push_source,
    )
