from fastapi.testclient import TestClient

from src.heart.api import main
from src.heart.api.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "model_loaded" in body


def test_predict_without_model_returns_503():
    # ensure clean state
    main._set_model_state(model=None, model_version=None, run_id=None)  # type: ignore[attr-defined]
    client = TestClient(app)
    response = client.post("/predict", json=_sample_payload())
    assert response.status_code == 503


def test_predict_with_stub_model():
    class _StubModel:
        def predict(self, df):
            return [1]

        def predict_proba(self, df):
            return [[0.1, 0.9]]

    main._set_model_state(model=_StubModel(), model_version="v-test", run_id="run-123")  # type: ignore[attr-defined]
    client = TestClient(app)
    response = client.post("/predict", json=_sample_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] == 1
    assert body["probability"] == 0.9
    assert body["model_version"] == "v-test"
    assert body["run_id"] == "run-123"
    # reset for other tests
    main._set_model_state(model=None, model_version=None, run_id=None)  # type: ignore[attr-defined]


def test_metrics_endpoint():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "heart_api_requests_total" in response.text


def _sample_payload():
    return {
        "age": 54,
        "sex": 1,
        "cp": 0,
        "trestbps": 130,
        "chol": 246,
        "fbs": 0,
        "restecg": 1,
        "thalach": 150,
        "exang": 0,
        "oldpeak": 1.2,
        "slope": 2,
        "ca": 0,
        "thal": 2,
    }
