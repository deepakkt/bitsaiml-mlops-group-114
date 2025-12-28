from sklearn.dummy import DummyClassifier

from src.heart import data, features


def test_feature_pipeline_fits_on_sample_data():
    df = data.load_sample()
    X, y = data.split_features_target(df)
    pipeline = features.build_model_pipeline(DummyClassifier(strategy="most_frequent"))
    pipeline.fit(X, y)
    preds = pipeline.predict(X)
    assert len(preds) == len(X)


def test_feature_names_contains_expected_fields():
    names = features.get_feature_names()
    assert "age" in names
    assert "thal" in names
    assert set(data.FEATURE_COLUMNS) == set(names)
