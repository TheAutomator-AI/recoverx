from fastapi.testclient import TestClient
import pytest
from apps.api.database import Base, engine
from apps.api.main import app


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_demo_seed_endpoint(client):
    response = client.post("/api/demo/seed")
    assert response.status_code == 200
    data = response.json()
    assert "case_a_autonomous" in data
    assert "case_b_assisted" in data
    assert "case_c_escalated" in data


def test_dashboard_stats_endpoint(client):
    response = client.get("/api/stats/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "revenue_at_risk" in data
    assert "recovery_rate" in data
    assert "autonomy_distribution" in data
    assert "recent_activity" in data


def test_payments_list_and_journey(client):
    # List payments
    res = client.get("/api/payments")
    assert res.status_code == 200
    payments = res.json()
    assert len(payments) > 0

    first_id = payments[0]["id"]
    # Journey
    journey_res = client.get(f"/api/payments/{first_id}/journey")
    assert journey_res.status_code == 200
    journey = journey_res.json()
    assert "steps" in journey
    assert len(journey["steps"]) > 0


def test_communication_preview_endpoint(client):
    res = client.get("/api/payments")
    first_id = res.json()[0]["id"]

    preview_res = client.get(f"/api/communication/preview/{first_id}")
    assert preview_res.status_code == 200
    bundle = preview_res.json()
    assert "messages" in bundle
    assert len(bundle["messages"]) >= 9


def test_review_queue_and_action(client):
    queue_res = client.get("/api/review/queue")
    assert queue_res.status_code == 200
    items = queue_res.json()

    if len(items) > 0:
        pay_id = items[0]["payment_id"]
        action_res = client.post(
            f"/api/review/{pay_id}/action",
            json={
                "action": "APPROVE",
                "reason": "Approved by human operator after customer contact",
                "review_duration_seconds": 15.5,
            },
        )
        assert action_res.status_code == 200
        assert action_res.json()["reviewer_action"] == "APPROVE"


def test_promises_endpoints(client):
    # List promises
    p_res = client.get("/api/promises")
    assert p_res.status_code == 200
    promises = p_res.json()
    assert len(promises) > 0


def test_evaluations_run_endpoint(client):
    eval_res = client.post("/api/evaluations/run?dataset_size=15&random_seed=42")
    assert eval_res.status_code == 200
    report = eval_res.json()
    assert "strategies" in report
    assert "RECOVERX" in report["strategies"]
    assert "BASELINE_A" in report["strategies"]
    assert "BASELINE_B" in report["strategies"]
    assert "pareto_analysis" in report
    assert "automated_conclusion" in report

