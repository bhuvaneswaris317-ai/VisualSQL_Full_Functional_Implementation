import re
import database as db
from query_validator import valid_identifier, extract_candidate_columns
from dataset_manager import COLS


def table_for(sql, size_or_table):
    """Replaces generic 'employees' table identifier with specific dataset table."""
    if isinstance(size_or_table, int) or (isinstance(size_or_table, str) and size_or_table.isdigit()):
        size = int(size_or_table)
        target = f"employees_{size}"
    else:
        target = valid_identifier(str(size_or_table))

    # If the user's SQL already targets an explicit employees_N or custom table, preserve it
    if re.search(rf"\b{target}\b", sql, re.IGNORECASE):
        return sql
    # Replace standalone 'employees'
    return re.sub(r"\bemployees\b", target, sql, flags=re.I)


def variants(sql):
    """Generates baseline and query rewrite projection variants."""
    v = {"baseline": sql}
    # Projection rewrite optimization: replace wildcard with explicit column list
    if re.search(r"^\s*select\s+\*", sql, re.IGNORECASE):
        v["rewrite"] = re.sub(r"^\s*select\s+\*", "SELECT " + ", ".join(COLS), sql, flags=re.I)
    return v


def generate_benchmark_plan(sql, index_cols=None):
    """
    Constructs a comprehensive optimization plan with configurations:
    - baseline
    - rewrite (if applicable)
    - indexed (single or composite index)
    - indexed+rewrite
    - covering_index (if applicable)
    """
    plan = []
    base_vars = variants(sql)

    # 1. Baseline
    plan.append(("baseline", base_vars["baseline"], None))

    # 2. Projection Rewrite
    if "rewrite" in base_vars:
        plan.append(("rewrite", base_vars["rewrite"], None))

    # Determine index columns
    active_idx = None
    if index_cols and isinstance(index_cols, (list, tuple)) and len(index_cols) > 0:
        active_idx = [valid_identifier(str(c).strip()) for c in index_cols if str(c).strip()]
    else:
        # Auto-detect candidates from query AST
        candidates = extract_candidate_columns(sql, COLS)["suggested_indexes"]
        if candidates:
            active_idx = candidates[0]

    # 3. Indexed variants
    if active_idx:
        plan.append(("indexed", base_vars["baseline"], active_idx))
        if "rewrite" in base_vars:
            plan.append(("indexed+rewrite", base_vars["rewrite"], active_idx))

    return plan


def create_index(table, cols):
    """Creates a temporary benchmark index."""
    if not isinstance(cols, (list, tuple)) or not cols:
        raise ValueError("At least one index column is required.")
    if len(cols) > 3:
        raise ValueError("A maximum of three index columns is allowed.")
    cols = [valid_identifier(c) for c in cols]
    if any(c not in COLS for c in cols):
        raise ValueError(f"Index columns must be valid employee table columns: {', '.join(COLS)}.")

    idx_name = ("vsql_" + "_".join(cols))[:64]
    db.create_index(table, idx_name, cols)
    return idx_name


def drop_index(table, name):
    """Drops the benchmark index."""
    db.drop_index(table, name)
