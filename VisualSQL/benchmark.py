import json
import time
import statistics
import database as db
import optimizer
import analyzer
from query_validator import validate


def improvement(orig, opt):
    """Calculates percentage improvement of optimized query over baseline."""
    return 0.0 if not orig or orig <= 0 else (orig - opt) / orig * 100


def time_query(sql, reps, warmup=2):
    """
    Executes a query with warm-up runs and measures wall-clock execution times,
    computing mean, median, min, max, p95, and standard deviation.
    """
    c = db.conn()
    cur = c.cursor()
    times = []
    rows = 0
    try:
        # Warmup passes to stabilize database buffer cache
        for _ in range(warmup):
            cur.execute(db._sqlite_sql(sql) if db.BACKEND == "sqlite" else sql)
            cur.fetchall()

        for _ in range(reps):
            t_start = time.perf_counter()
            cur.execute(db._sqlite_sql(sql) if db.BACKEND == "sqlite" else sql)
            res = cur.fetchall()
            t_elapsed = (time.perf_counter() - t_start) * 1000.0
            rows = len(res)
            times.append(t_elapsed)
    finally:
        c.close()

    sorted_times = sorted(times)
    p95_idx = int(0.95 * len(sorted_times))
    p95_val = sorted_times[min(p95_idx, len(sorted_times) - 1)]

    return {
        "avg": statistics.mean(times) if times else 0.0,
        "median": statistics.median(times) if times else 0.0,
        "min": min(times) if times else 0.0,
        "max": max(times) if times else 0.0,
        "p95": p95_val,
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "rows": rows,
        "iterations": [round(t, 3) for t in times]
    }


def ensure_config_exists(cfg_name):
    """Guarantees optimization_configurations table contains the specified configuration."""
    rows = db.fetch("SELECT id FROM optimization_configurations WHERE name=%s", (cfg_name,))
    if rows:
        return rows[0]["id"]
    # Insert new configuration dynamically
    technique = "indexing" if "index" in cfg_name else ("query rewrite" if "rewrite" in cfg_name else "none")
    desc = f"Optimization configuration: {cfg_name}"
    return db.execute(
        "INSERT INTO optimization_configurations(name,technique,description) VALUES(%s,%s,%s)",
        (cfg_name, technique, desc)
    )


def run(name, sql, size, reps=5, index_cols=None):
    """
    Executes multi-configuration benchmarking comparing baseline, rewritten,
    and indexed query variants against specified dataset size.
    """
    sql = validate(sql)
    size = int(size)
    if size not in db.SIZES:
        raise ValueError(f"Invalid dataset size: {size}. Supported sizes: {db.SIZES}")
    reps = int(reps)
    if reps < 1 or reps > 30:
        raise ValueError("Repetitions must be between 1 and 30.")

    table = f"employees_{size}"
    ds = db.fetch("SELECT id FROM datasets WHERE table_name=%s", (table,))
    if not ds:
        # Check if table exists in SQLite schema directly
        import dataset_manager
        dataset_manager.setup_samples()
        ds = db.fetch("SELECT id FROM datasets WHERE table_name=%s", (table,))

    dataset_id = ds[0]["id"] if ds else None

    exp = db.execute(
        "INSERT INTO benchmark_experiments(query_name,sql_text,dataset_id,dataset_size,repetitions,status) "
        "VALUES(%s,%s,%s,%s,%s,'running')",
        (name, sql, dataset_id, size, reps)
    )

    plan = optimizer.generate_benchmark_plan(sql, index_cols)
    results = []
    base_metric = None
    overall_status = "completed"

    for cfg, q, idx in plan:
        full_sql = optimizer.table_for(q, size)
        idx_name = None
        status_row = "ok"

        try:
            if idx:
                idx_name = optimizer.create_index(table, idx)

            t_metrics = time_query(full_sql, reps)
            p_plan = analyzer.explain(full_sql)

            if base_metric is None:
                base_metric = t_metrics

            if t_metrics["rows"] != base_metric["rows"]:
                status_row = "row-count mismatch"

            imp = improvement(base_metric["avg"], t_metrics["avg"])
            cid = ensure_config_exists(cfg)

            step = p_plan["steps"][0] if p_plan["steps"] else {}
            access_type = step.get("access_type") or ("INDEX" if idx else "SCAN")

            db.execute(
                "INSERT INTO benchmark_results("
                "experiment_id,config_id,executed_sql,index_config,avg_ms,min_ms,max_ms,"
                "row_count,improvement_pct,access_type,est_rows,plan_json,status"
                ") VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    exp,
                    cid,
                    full_sql,
                    ", ".join(idx) if idx else "none",
                    t_metrics["avg"],
                    t_metrics["min"],
                    t_metrics["max"],
                    t_metrics["rows"],
                    imp,
                    access_type,
                    step.get("rows") if isinstance(step.get("rows"), int) else None,
                    json.dumps(p_plan, default=str),
                    status_row
                )
            )

            results.append({
                "config": cfg,
                **t_metrics,
                "improvement": imp,
                "index": idx or [],
                "plan": p_plan,
                "status": status_row,
                "access_type": access_type
            })

        except Exception as e:
            overall_status = "partial"
            results.append({
                "config": cfg,
                "error": str(e),
                "status": "error"
            })
        finally:
            if idx_name:
                try:
                    optimizer.drop_index(table, idx_name)
                except Exception:
                    pass

    db.execute("UPDATE benchmark_experiments SET status=%s WHERE id=%s", (overall_status, exp))
    return exp, results
