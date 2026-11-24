import pytest
import database as db
import analyzer
import optimizer
import benchmark
import dataset_manager
import report_generator
import app
from query_validator import validate, format_sql, extract_candidate_columns, InvalidQuery


@pytest.fixture(scope="module")
def client():
    app.app.config["TESTING"] = True
    with app.app.test_client() as client:
        yield client


def test_schema_and_status(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json
    assert data["status"] == "healthy"
    assert "backend" in data
    assert "total_records" in data

    res_schema = client.get("/api/schema")
    assert res_schema.status_code == 200
    tables = res_schema.json.get("tables", [])
    assert len(tables) > 0


def test_sql_validation_and_candidates():
    sql = "SELECT * FROM employees WHERE department = 'Engineering' AND city = 'Chennai' ORDER BY salary DESC"
    val = validate(sql)
    assert val.startswith("SELECT")
    
    formatted = format_sql(sql)
    assert "WHERE" in formatted
    
    candidates = extract_candidate_columns(sql)
    assert "department" in candidates["where_columns"]
    assert "city" in candidates["where_columns"]
    assert "salary" in candidates["order_columns"]
    assert len(candidates["suggested_indexes"]) > 0


def test_forbidden_queries():
    forbidden = [
        "DROP TABLE employees",
        "TRUNCATE TABLE employees",
        "INSERT INTO employees VALUES (1, 'A', 'B', 10, 'C')",
        "UPDATE employees SET salary = 99999",
        "SELECT * FROM employees; DROP TABLE employees",
        "SELECT SLEEP(5)"
    ]
    for q in forbidden:
        with pytest.raises(InvalidQuery):
            validate(q)


def test_explain_planner():
    sql = "SELECT * FROM employees_1000 WHERE department = 'Sales'"
    plan = analyzer.explain(sql)
    assert "health_score" in plan
    assert "verdict" in plan
    assert len(plan["steps"]) > 0
    step = plan["steps"][0]
    assert "access_type" in step
    assert "table" in step


def test_benchmark_flow():
    dataset_manager.ensure_initial_sample()
    exp_id, results = benchmark.run(
        "PyTest Unit Run",
        "SELECT * FROM employees WHERE department = 'Sales'",
        size=1000,
        reps=3,
        index_cols=["department"]
    )
    assert exp_id > 0
    assert len(results) >= 2

    baseline = next(r for r in results if r["config"] == "baseline")
    assert baseline["avg"] > 0
    assert baseline["rows"] > 0
    assert "median" in baseline
    assert "p95" in baseline

    # Test PDF report generation
    pdf = report_generator.pdf_bytes(exp_id)
    assert len(pdf) > 500
    assert pdf.startswith(b"%PDF")

    # Test CSV report generation
    csv_data = report_generator.csv_bytes(exp_id)
    assert len(csv_data) > 0


def test_custom_dataset_lifecycle(client):
    # Generate custom dataset
    res_gen = client.post("/api/datasets/generate", json={"size": 100, "name": "user_test_custom"})
    assert res_gen.status_code == 200
    assert res_gen.json["ok"] is True

    # Query it
    res_q = client.post("/api/query", json={"sql": "SELECT * FROM user_test_custom", "size": 100})
    assert res_q.status_code == 200
    assert res_q.json["row_count"] == 100

    # Delete it
    res_del = client.delete("/api/datasets/user_test_custom")
    assert res_del.status_code == 200
    assert res_del.json["ok"] is True


def test_api_endpoints(client):
    # Test Query Endpoint
    res_q = client.post("/api/query", json={"sql": "SELECT * FROM employees WHERE department = 'Sales'", "size": 1000})
    assert res_q.status_code == 200
    data_q = res_q.json
    assert "columns" in data_q
    assert "rows" in data_q
    assert data_q["execution_time_ms"] >= 0

    # Test Explain Endpoint
    res_e = client.post("/api/explain", json={"sql": "SELECT * FROM employees WHERE department = 'Sales'", "size": 1000})
    assert res_e.status_code == 200
    assert "health_score" in res_e.json

    # Test Summary Endpoint
    res_s = client.get("/api/summary")
    assert res_s.status_code == 200
    data_s = res_s.json
    assert data_s["experiments"] >= 1
    assert data_s["queries"] >= 1

    # Test Datasets Endpoint
    res_d = client.get("/api/datasets")
    assert res_d.status_code == 200
    assert len(res_d.json) >= 1

    # Test History Endpoint
    res_h = client.get("/api/history")
    assert res_h.status_code == 200
    assert len(res_h.json) >= 1

    # Test CSV report endpoint
    res_csv = client.get("/report/csv")
    assert res_csv.status_code == 200
    assert res_csv.mimetype == "text/csv"
