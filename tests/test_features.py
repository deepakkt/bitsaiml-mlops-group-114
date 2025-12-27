from src.heart import features


def test_feature_names_contains_expected_fields():
    names = features.get_feature_names()
    assert "age" in names
    assert "thal" in names
    assert len(names) >= 10
