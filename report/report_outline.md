# Report Outline (Part-9)

Use this outline to fill `report/Report.docx`. Each bullet should either embed a figure/table or reference a screenshot in `report/screenshots/` and figures in `report/figures/`.

1. Title page: project name, author, date, environment (Python 3.11, Minikube profile `mlops-assign1`).
2. Objective & Dataset: describe UCI Heart Disease goal, link to source, mention `data/raw/metadata.json` (timestamp + checksum), and note target column.
3. Data preparation: schema, train/test split strategy, seed=42, preprocessing via sklearn `ColumnTransformer` (impute/scale numeric, impute/one-hot categorical).
4. Exploratory Data Analysis: include plots from `report/figures/` (`target_balance.png`, `numeric_distributions.png`, `correlation_heatmap.png`, `missingness.png`) with short captions.
5. Modeling & Metrics: summarize models (Dummy, LogisticRegression tuned, RandomForest tuned), CV settings, and include a metrics table (accuracy/precision/recall/ROC-AUC). Call out best model/run_id.
6. MLflow Tracking: screenshot MLflow UI (experiment `heart-disease-uci`, run page showing metrics/artifacts/model), note artifact locations (`artifacts/plots/`, `artifacts/model/`).
7. API & Serving: FastAPI contract (`/health`, `/predict`, `/metrics`), include sample request `data/sample/request.json` and curl responses (from local run or docker).
8. Containerization: document `make docker-build && make docker-run`, include smoke test snippet from `scripts/smoke_test_api.sh`.
9. Kubernetes Deploy: steps run (`make k8s-up`, `make k8s-deploy`, `make k8s-smoke`), screenshot `kubectl get pods,svc` and curl via port-forward.
10. Monitoring: show Prometheus target UP (browser or `scripts/check_prometheus_target.sh` output) and Grafana dashboard (import `k8s/monitoring/grafana-dashboard.json` with request rate, p95 latency, error rate, pod CPU/mem panels).
11. CI/CD: screenshot of green GitHub Actions run from `.github/workflows/ci.yml` with lint/test/quick-train steps and artifacts list.
12. Verification Run: note that `make verify` succeeded, include key console snippets (docker smoke test, k8s smoke test, Prometheus scrape check).
13. Architecture Diagram: include rendered diagram (Mermaid acceptable); save image to `report/figures/architecture.png`.
14. Conclusion & Next Steps: brief reflection on model performance, ops robustness, and future improvements.

Evidence collection quick commands (after `make verify`):
- Local API: `./scripts/smoke_test_api.sh`
- Docker: `make docker-build && make docker-run && ./scripts/smoke_test_api.sh`
- K8s: `make k8s-up && make k8s-deploy && make k8s-smoke`
- Monitoring: `make monitor-up && make monitor-check`
- CI: trigger/pull latest run in GitHub Actions and screenshot the summary.
