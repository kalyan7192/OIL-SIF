import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_analyze_endpoint(client):
    payload = {
        "text": "Technician started maintenance before 415V electrical breaker was locked out and tagged.",
        "site": "Moran GGS-1",
        "report_type": "Near Miss"
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["sif_potential"] is True
    assert data["life_saving_rule_id"] == "ENERGY_ISOLATION"
    assert "activity" in data["precursor"]

def test_create_and_fetch_and_delete_report(client):
    payload = {
        "description": "Electrician was working near energized 415V busbar without LOTO isolation.",
        "site": "Duliajan Central Workshop",
        "location": "Substation",
        "activity": "Electrical Maintenance",
        "report_type": "Near Miss"
    }
    res_create = client.post("/api/reports", json=payload)
    assert res_create.status_code == 200
    created = res_create.json()
    report_id = created["report_id"]

    # Fetch report
    res_get = client.get(f"/api/reports/{report_id}")
    assert res_get.status_code == 200
    assert res_get.json()["report_id"] == report_id

    # Delete single report
    res_del = client.delete(f"/api/reports/{report_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "success"

    # Verify deleted
    res_get_after = client.get(f"/api/reports/{report_id}")
    assert res_get_after.status_code == 404

def test_batch_delete_reports(client):
    # Create 2 reports
    rep1 = client.post("/api/reports", json={
        "description": "Test report 1 for batch deletion",
        "site": "Moran GGS-1",
        "report_type": "Near Miss"
    }).json()["report_id"]

    rep2 = client.post("/api/reports", json={
        "description": "Test report 2 for batch deletion",
        "site": "Digboi Production Facility",
        "report_type": "Unsafe Act"
    }).json()["report_id"]

    # Batch delete
    res_batch = client.post("/api/reports/delete-batch", json={"report_ids": [rep1, rep2]})
    assert res_batch.status_code == 200
    assert res_batch.json()["deleted_count"] >= 2

def test_dashboard_summary_dynamic(client):
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_reports" in data
    assert "overall_sif_density" in data
