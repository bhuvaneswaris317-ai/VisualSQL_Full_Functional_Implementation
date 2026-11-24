import io
import time
from flask import Flask, jsonify, request, render_template, send_file
from werkzeug.exceptions import HTTPException

import database as db
import benchmark
import analyzer
import dataset_manager
import report_generator
import config
from recommendation import recommend
from query_validator import validate, format_sql, extract_candidate_columns, InvalidQuery

app = Flask(__name__)

# Ensure at least one dataset exists on startup
try:
    dataset_manager.ensure_initial_sample()
except Exception:
    pass


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/status")
def api_status():
    try:
        tables_meta = db.get_schema_info()
        total_rows = sum(t.get("row_count", 0) for t in tables_meta if t.get("is_benchmark_target"))
        return jsonify(
            backend=db.BACKEND,
            database=config.DB["database"] if db.BACKEND == "mysql" else "visualsql.db",
            tables_count=len(tables_meta),
            total_records=total_rows,
            status="healthy"
        )
    except Exception as e:
        return jsonify(
            backend=db.BACKEND,
            database="visualsql.db",
            tables_count=0,
            total_records=0,
            status="error",
            error=str(e)
        )


@app.get("/api/schema")
def api_schema():
    try:
        tables = db.get_schema_info()
        return jsonify(tables=tables)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.errorhandler(Exception)
def err(e):
    if isinstance(e, HTTPException):
        return jsonify(error=e.description), e.code
    code = 400 if isinstance(e, (InvalidQuery, ValueError)) else 500
    return jsonify(error=str(e)), code


@app.post("/api/validate")
def api_validate():
    body = request.get_json(silent=True) or {}
    raw_sql = body.get("sql", "")
    validated_sql = validate(raw_sql)
    formatted = format_sql(validated_sql)
    candidates = extract_candidate_columns(validated_sql, dataset_manager.COLS)
    return jsonify(
        valid=True,
        sql=formatted,
        candidate_indexes=candidates["suggested_indexes"],
        where_columns=candidates["where_columns"],
        order_columns=candidates["order_columns"]
    )


@app.post("/api/query")
def api_query():
    body = request.get_json(silent=True) or {}
    sql = validate(body.get("sql", ""))
    size = body.get("size", 1000)
    target_sql = benchmark.optimizer.table_for(sql, size)
    
    # Apply safety limit if not present
    limited = False
    if " limit " not in target_sql.lower():
        target_sql += " LIMIT 200"
        limited = True

    t_start = time.perf_counter()
    rows, columns = db.fetch(target_sql, with_columns=True)
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    return jsonify(
        columns=columns,
        rows=[[str(r.get(c, "")) for c in columns] for r in rows],
        row_count=len(rows),
        execution_time_ms=round(elapsed_ms, 2),
        limited=limited,
        executed_sql=target_sql
    )


@app.post("/api/explain")
def api_explain():
    body = request.get_json(silent=True) or {}
    raw_sql = validate(body.get("sql", ""))
    size = body.get("size", 1000)
    target_sql = benchmark.optimizer.table_for(raw_sql, size)
    plan = analyzer.explain(target_sql)
    return jsonify(plan)


@app.post("/api/benchmark")
def api_bench():
    j = request.get_json(silent=True) or {}
    name = (j.get("name") or "Untitled Benchmark").strip()
    raw_sql = j.get("sql", "")
    size = int(j.get("size", 1000))
    reps = min(max(int(j.get("reps", 5)), 1), 30)
    index_cols = j.get("index_cols") or None

    exp_id, results = benchmark.run(name, raw_sql, size, reps, index_cols)
    recs = recommend(results)

    best_r = min((r for r in results if r.get("status") == "ok"), key=lambda x: x["avg"], default=None)
    best_config = best_r["config"] if best_r else None

    return jsonify(
        experiment_id=exp_id,
        results=results,
        recommendations=recs,
        best_config=best_config
    )


@app.get("/api/summary")
def api_summary():
    try:
        # Robust query that never crashes on empty table
        exp_cnt = db.fetch("SELECT COUNT(*) as cnt FROM benchmark_experiments")[0]["cnt"]
        qry_cnt = db.fetch("SELECT COUNT(DISTINCT sql_text) as cnt FROM benchmark_experiments")[0]["cnt"]
        res_stats = db.fetch("SELECT AVG(avg_ms) as avg_ms, MAX(improvement_pct) as best_improvement FROM benchmark_results")[0]
        best_rows = db.fetch(
            "SELECT c.name FROM benchmark_results r "
            "JOIN optimization_configurations c ON c.id=r.config_id "
            "ORDER BY r.improvement_pct DESC LIMIT 1"
        )
        tables_meta = db.get_schema_info()
        total_rows = sum(t.get("row_count", 0) for t in tables_meta if t.get("is_benchmark_target"))

        avg_val = res_stats.get("avg_ms")
        best_imp = res_stats.get("best_improvement")

        return jsonify(
            experiments=int(exp_cnt or 0),
            queries=int(qry_cnt or 0),
            avg_ms=round(float(avg_val), 2) if avg_val is not None else None,
            best_improvement=round(float(best_imp), 1) if best_imp is not None else None,
            best_config=best_rows[0]["name"] if best_rows else None,
            total_datasets=len([t for t in tables_meta if t.get("is_benchmark_target")]),
            total_records=total_rows
        )
    except Exception as e:
        return jsonify(
            experiments=0,
            queries=0,
            avg_ms=None,
            best_improvement=None,
            best_config=None,
            total_datasets=0,
            total_records=0,
            error=str(e)
        )


@app.get("/api/datasets")
def api_datasets():
    return jsonify(db.fetch("SELECT table_name, row_count, source, created_at FROM datasets ORDER BY row_count ASC", admin=True))


@app.post("/api/datasets/setup")
def api_setup():
    dataset_manager.setup_samples()
    return jsonify(ok=True, message="Benchmark datasets (1k, 10k, 50k, 100k) successfully generated.")


@app.post("/api/datasets/generate")
def api_generate():
    body = request.get_json(silent=True) or {}
    size = int(body.get("size", 1000))
    table_name = body.get("name") or f"employees_{size}"
    df = dataset_manager.generate_csv(size)
    dataset_manager.load_dataframe(df, table_name, "custom_generator")
    return jsonify(ok=True, table=table_name, rows=size)


@app.delete("/api/datasets/<name>")
def api_delete_dataset(name):
    dataset_manager.delete_dataset(name)
    return jsonify(ok=True)


@app.post("/api/datasets/preview")
def api_preview():
    file = request.files.get("file")
    if not file or not file.filename:
        raise InvalidQuery("A CSV file is required for preview.")
    return jsonify(rows=dataset_manager.preview(file))


@app.post("/api/datasets/upload")
def api_upload():
    dataset_manager.import_upload(request.files["file"], request.form["name"])
    return jsonify(ok=True)


@app.get("/api/history")
def api_history():
    return jsonify(db.fetch(
        "SELECT id, query_name, dataset_size, repetitions, status, created_at "
        "FROM benchmark_experiments ORDER BY id DESC LIMIT 100"
    ))


@app.delete("/api/history/<int:exp_id>")
def api_delete_history(exp_id):
    db.execute("DELETE FROM benchmark_experiments WHERE id=%s", (exp_id,))
    return jsonify(ok=True)


@app.post("/api/history/clear")
def api_clear_history():
    db.execute("DELETE FROM benchmark_results")
    db.execute("DELETE FROM benchmark_experiments")
    return jsonify(ok=True)


@app.get("/api/results")
def api_results():
    exp_id = request.args.get("experiment", type=int)
    return jsonify(report_generator.rows(exp_id))


@app.get("/report/csv")
def csv_report():
    exp_id = request.args.get("experiment", type=int)
    data = report_generator.csv_bytes(exp_id)
    return send_file(
        io.BytesIO(data),
        "text/csv",
        as_attachment=True,
        download_name=f"visualsql_{exp_id or 'all'}.csv"
    )


@app.get("/report/pdf/<int:exp>")
def pdf_report(exp):
    data = report_generator.pdf_bytes(exp)
    return send_file(
        io.BytesIO(data),
        "application/pdf",
        as_attachment=True,
        download_name=f"visualsql_experiment_{exp}.pdf"
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
