import os
import re
import sqlite3
import mysql.connector
import config

SIZES = [1000, 10000, 50000, 100000]
SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "visualsql.db"))
BACKEND = "mysql"

DEFAULT_CONFIGS = [
    ("baseline", "none", "Original query, unindexed full table scan"),
    ("rewrite", "query rewrite", "Projection optimization: SELECT * replaced by explicit columns"),
    ("indexed", "indexing", "Single-column index on primary filter predicate"),
    ("indexed+rewrite", "indexing+rewrite", "Index seek combined with explicit column projection"),
    ("composite_index", "composite index", "Composite multi-column index for multiple predicates or ORDER BY"),
    ("covering_index", "covering index", "Covering index containing both filter and projected columns"),
]


def _mysql_connection(admin=False):
    creds = config.ADMIN if admin else config.BENCH
    if not creds.get("user") or not creds.get("password"):
        raise RuntimeError("Database credentials are missing.")
    c = mysql.connector.connect(**config.DB, **creds, connection_timeout=5)
    if not admin:
        cur = c.cursor()
        cur.execute(f"SET SESSION MAX_EXECUTION_TIME={config.TIMEOUT_MS}")
        cur.close()
    return c


def _sqlite_connection():
    c = sqlite3.connect(SQLITE_PATH, timeout=30, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    c.execute("PRAGMA synchronous = NORMAL")
    return c


def _init_sqlite():
    c = _sqlite_connection()
    try:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS datasets(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL UNIQUE,
            row_count INTEGER NOT NULL,
            source TEXT NOT NULL DEFAULT 'generated',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS employees(
            employee_id INTEGER PRIMARY KEY,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL,
            city TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS optimization_configurations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            technique TEXT NOT NULL,
            description TEXT
        );
        CREATE TABLE IF NOT EXISTS benchmark_experiments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_name TEXT NOT NULL,
            sql_text TEXT NOT NULL,
            dataset_id INTEGER,
            dataset_size INTEGER NOT NULL,
            repetitions INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS benchmark_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            config_id INTEGER NOT NULL,
            executed_sql TEXT NOT NULL,
            index_config TEXT NOT NULL,
            avg_ms REAL,
            min_ms REAL,
            max_ms REAL,
            row_count INTEGER,
            improvement_pct REAL,
            access_type TEXT,
            est_rows INTEGER,
            plan_json TEXT,
            status TEXT NOT NULL,
            FOREIGN KEY(experiment_id) REFERENCES benchmark_experiments(id) ON DELETE CASCADE,
            FOREIGN KEY(config_id) REFERENCES optimization_configurations(id)
        );
        """)
        c.executemany(
            "INSERT OR IGNORE INTO optimization_configurations(name,technique,description) VALUES(?,?,?)",
            DEFAULT_CONFIGS,
        )
        c.commit()
    finally:
        c.close()


try:
    _mysql_connection(False).close()
except Exception:
    BACKEND = "sqlite"
    _init_sqlite()


def conn(admin=False):
    if BACKEND == "sqlite":
        return _sqlite_connection()
    return _mysql_connection(admin)


def _sqlite_sql(sql):
    sql = sql.replace("%s", "?")
    sql = sql.replace("INSERT IGNORE INTO", "INSERT OR IGNORE INTO")
    sql = sql.replace("REPLACE INTO", "INSERT OR REPLACE INTO")
    sql = re.sub(r"DROP\s+INDEX\s+[`\"]?([^`\"\s]+)[`\"]?\s+ON\s+[`\"]?[^`\"\s]+[`\"]?", r'DROP INDEX IF EXISTS "\1"', sql, flags=re.I)
    sql = re.sub(r"CREATE\s+INDEX\s+[`\"]?([^`\"\s]+)[`\"]?\s+ON\s+[`\"]?([^`\"\s\(]+)[`\"]?", r'CREATE INDEX IF NOT EXISTS "\1" ON "\2"', sql, flags=re.I)
    return sql


def fetch(sql, params=None, admin=False, with_columns=False):
    c = conn(admin)
    try:
        cur = c.cursor()
        cols = []
        if BACKEND == "sqlite":
            cur.execute(_sqlite_sql(sql), params or ())
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            else:
                rows = []
        else:
            cur = c.cursor(dictionary=True)
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            if cur.description:
                cols = [d[0] for d in cur.description]
        if with_columns:
            return rows, cols
        return rows
    finally:
        c.close()


def execute(sql, params=None):
    c = conn(True)
    try:
        cur = c.cursor()
        cur.execute(_sqlite_sql(sql) if BACKEND == "sqlite" else sql, params or ())
        c.commit()
        return cur.lastrowid
    finally:
        c.close()


def create_index(table, index_name, columns):
    cols_str = ", ".join(f"`{c}`" if BACKEND == "mysql" else f'"{c}"' for c in columns)
    if BACKEND == "sqlite":
        execute(f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table}" ({cols_str})')
    else:
        execute(f"CREATE INDEX `{index_name}` ON `{table}` ({cols_str})")


def drop_index(table, index_name):
    if BACKEND == "sqlite":
        execute(f'DROP INDEX IF EXISTS "{index_name}"')
    else:
        execute(f"DROP INDEX `{index_name}` ON `{table}`")


def get_schema_info():
    """Returns rich schema metadata for all tables in the database."""
    tables_meta = []
    if BACKEND == "sqlite":
        c = conn()
        try:
            cur = c.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
            tables = [r[0] for r in cur.fetchall()]
            for tbl in tables:
                cur.execute(f'PRAGMA table_info("{tbl}")')
                cols = [{"name": r["name"], "type": r["type"], "pk": bool(r["pk"])} for r in cur.fetchall()]
                cur.execute(f'PRAGMA index_list("{tbl}")')
                indexes = [{"name": r["name"], "unique": bool(r["unique"])} for r in cur.fetchall()]
                cur.execute(f'SELECT COUNT(*) as cnt FROM "{tbl}"')
                cnt_row = cur.fetchone()
                row_cnt = cnt_row[0] if cnt_row else 0
                tables_meta.append({
                    "name": tbl,
                    "columns": cols,
                    "indexes": indexes,
                    "row_count": row_cnt,
                    "is_benchmark_target": tbl.startswith("employees")
                })
        finally:
            c.close()
    else:
        db_name = config.DB["database"]
        raw_tables = fetch("SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema=%s ORDER BY table_name", (db_name,))
        for t in raw_tables:
            tbl = t["table_name"]
            raw_cols = fetch("SELECT column_name, data_type, column_key FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position", (db_name, tbl))
            cols = [{"name": c["column_name"], "type": c["data_type"], "pk": c["column_key"] == "PRI"} for c in raw_cols]
            raw_idx = fetch("SELECT DISTINCT index_name, non_unique FROM information_schema.statistics WHERE table_schema=%s AND table_name=%s", (db_name, tbl))
            indexes = [{"name": i["index_name"], "unique": i["non_unique"] == 0} for i in raw_idx]
            tables_meta.append({
                "name": tbl,
                "columns": cols,
                "indexes": indexes,
                "row_count": t.get("table_rows", 0) or 0,
                "is_benchmark_target": tbl.startswith("employees")
            })
    return tables_meta
