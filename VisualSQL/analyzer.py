import re
import json
import database as db

EXPLAIN_TEXT = {
    "ALL": "Full table scan: every row is read sequentially. High disk/memory I/O on large tables. Consider adding an index.",
    "index": "Full index scan: entire index tree is traversed. Better than ALL if index is small, but still O(N).",
    "range": "Index range scan: reads only index rows within a given key range (e.g. BETWEEN, >, <, IN). Highly efficient.",
    "ref": "Index lookup on non-unique key: reads matching rows using index key. Standard fast O(log N) lookup.",
    "eq_ref": "Unique key lookup: exactly one row is read per key from unique index or primary key. Optimal.",
    "const": "Single-row lookup: table has at most one matching row, treated as constant by optimizer.",
    "system": "System table: table has zero or one row. Instant access.",
}

SEVERITY_MAP = {
    "ALL": "danger",
    "index": "warning",
    "range": "success",
    "ref": "success",
    "eq_ref": "optimal",
    "const": "optimal",
    "system": "optimal",
}


def explain_sqlite(sql):
    """Executes EXPLAIN QUERY PLAN in SQLite and translates details into rich structured plan steps."""
    try:
        raw_rows = db.fetch("EXPLAIN QUERY PLAN " + sql)
    except Exception as e:
        return {
            "steps": [],
            "graph_nodes": [],
            "analyze": None,
            "cost": None,
            "health_score": 50,
            "verdict": f"Explain failed: {e}",
            "raw_plan": str(e)
        }

    steps = []
    graph_nodes = []
    has_full_scan = False
    has_index = False
    has_covering = False

    for idx, r in enumerate(raw_rows):
        detail = r.get("detail", "")
        # Parse table name
        tbl_match = re.search(r"(?:SCAN|SEARCH)\s+([A-Za-z0-9_]+)", detail, re.IGNORECASE)
        tbl_name = tbl_match.group(1) if tbl_match else "employees"

        # Determine access pattern
        if "COVERING INDEX" in detail.upper():
            idx_match = re.search(r"USING\s+COVERING\s+INDEX\s+([A-Za-z0-9_]+)", detail, re.IGNORECASE)
            key_name = idx_match.group(1) if idx_match else "covering_index"
            access_type = "COVERING INDEX"
            severity = "optimal"
            has_covering = True
            meaning = f"Covering index lookup ({key_name}): all required columns are served directly from the index tree without fetching main table pages."
            suggestion = "Optimal query configuration: zero secondary table page I/O."
            full_scan = False
        elif "USING INDEX" in detail.upper():
            idx_match = re.search(r"USING\s+INDEX\s+([A-Za-z0-9_]+)", detail, re.IGNORECASE)
            key_name = idx_match.group(1) if idx_match else "index"
            access_type = "INDEX SEEK (ref)"
            severity = "success"
            has_index = True
            meaning = f"B-Tree index seek ({key_name}): SQLite navigates directly to matching keys in O(log N) time, then fetches matching row pages."
            suggestion = "Good performance. For ultra-high volume, consider a covering index to avoid main table lookups."
            full_scan = False
        elif "USING INTEGER PRIMARY KEY" in detail.upper():
            key_name = "PRIMARY (ROWID)"
            access_type = "PRIMARY KEY"
            severity = "optimal"
            has_index = True
            meaning = "Primary key direct lookup: SQLite navigates the primary B-Tree root directly."
            suggestion = "Peak efficiency: constant or O(log N) primary key access."
            full_scan = False
        elif "SCAN" in detail.upper():
            key_name = None
            access_type = "SCAN (Full Table Scan)"
            severity = "danger"
            has_full_scan = True
            meaning = f"Full table scan on '{tbl_name}': Every single row is evaluated sequentially from storage. Execution time scales linearly O(N)."
            suggestion = f"Create an index on the filtered columns of '{tbl_name}' to convert this to an O(log N) B-Tree seek."
            full_scan = True
        elif "USE TEMP B-TREE" in detail.upper():
            key_name = None
            access_type = "TEMP B-TREE (Sort Buffer)"
            severity = "warning"
            meaning = "Temporary in-memory/disk B-Tree allocated for ORDER BY or GROUP BY clause."
            suggestion = "Adding an index that matches the ORDER BY columns can eliminate the temporary sorting pass."
            full_scan = False
        else:
            key_name = None
            access_type = "FILTER / COMPUTE"
            severity = "info"
            meaning = detail
            suggestion = "Internal engine processing step."
            full_scan = False

        steps.append({
            "step_id": r.get("id", idx + 1),
            "parent_id": r.get("parent", 0),
            "table": tbl_name,
            "access_type": access_type,
            "key": key_name,
            "possible_keys": [key_name] if key_name else [],
            "rows": "~",
            "filtered": "100%",
            "extra": detail,
            "full_scan": full_scan,
            "severity": severity,
            "meaning": meaning,
            "suggestion": suggestion
        })

        graph_nodes.append({
            "id": f"node_{idx+1}",
            "label": f"{tbl_name}: {access_type}",
            "detail": detail,
            "severity": severity,
            "type": "scan" if full_scan else "seek"
        })

    # Health score calculation
    if has_covering:
        health_score = 98
        verdict = "Optimal: Query uses a covering index for zero-table-read execution."
    elif has_index and not has_full_scan:
        health_score = 88
        verdict = "Efficient: Query utilizes B-Tree indexes for fast filtered lookups."
    elif has_full_scan:
        health_score = 35
        verdict = "Warning: Full table scan detected. Every record is inspected sequentially."
    else:
        health_score = 70
        verdict = "Acceptable: Query plan executed with standard evaluation."

    return {
        "steps": steps,
        "graph_nodes": graph_nodes,
        "analyze": None,
        "cost": 1.0 if not has_full_scan else 100.0,
        "health_score": health_score,
        "verdict": verdict,
        "raw_plan": raw_rows
    }


def explain_mysql(sql):
    """Executes EXPLAIN in MySQL and parses standard relational planner attributes."""
    rows = db.fetch("EXPLAIN " + sql)
    steps = []
    graph_nodes = []
    has_full_scan = False
    has_index = False

    for idx, r in enumerate(rows):
        r = {k.lower(): v for k, v in r.items()}
        atype = r.get("type", "ALL")
        full_scan = (atype == "ALL")
        if full_scan:
            has_full_scan = True
        else:
            has_index = True

        severity = SEVERITY_MAP.get(atype, "info")
        meaning = EXPLAIN_TEXT.get(atype, f"Access type '{atype}'")
        tbl = r.get("table", "employees")

        steps.append({
            "step_id": idx + 1,
            "table": tbl,
            "access_type": atype,
            "possible_keys": (r.get("possible_keys") or "").split(",") if r.get("possible_keys") else [],
            "key": r.get("key"),
            "rows": r.get("rows"),
            "filtered": f"{r.get('filtered', 100)}%",
            "extra": r.get("extra", ""),
            "full_scan": full_scan,
            "severity": severity,
            "meaning": meaning,
            "suggestion": (
                f"Add an index to '{tbl}' on predicate columns to eliminate table scan."
                if full_scan else "Index in use. Monitor cardinality and execution times."
            )
        })

        graph_nodes.append({
            "id": f"node_{idx+1}",
            "label": f"{tbl}: {atype}",
            "detail": f"Key: {r.get('key') or 'None'} | Rows: {r.get('rows')}",
            "severity": severity,
            "type": "scan" if full_scan else "seek"
        })

    res = {
        "steps": steps,
        "graph_nodes": graph_nodes,
        "analyze": None,
        "cost": None,
        "health_score": 35 if has_full_scan else (92 if has_index else 70),
        "verdict": "Full table scan detected." if has_full_scan else "Indexes used effectively.",
        "raw_plan": rows
    }

    try:
        j = db.fetch("EXPLAIN FORMAT=JSON " + sql)[0]
        parsed = json.loads(list(j.values())[0])
        res["cost"] = parsed.get("query_block", {}).get("cost_info", {}).get("query_cost")
    except Exception:
        pass

    try:
        res["analyze"] = list(db.fetch("EXPLAIN ANALYZE " + sql)[0].values())[0]
    except Exception:
        pass

    return res


def explain(sql):
    if db.BACKEND == "sqlite":
        return explain_sqlite(sql)
    return explain_mysql(sql)
