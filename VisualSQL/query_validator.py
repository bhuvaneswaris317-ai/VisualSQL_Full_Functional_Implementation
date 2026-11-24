import re
import sqlparse
from sqlparse.tokens import Keyword, DML, DDL

FORBIDDEN = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
    "GRANT", "REPLACE", "INTO", "OUTFILE", "SLEEP", "BENCHMARK", "LOAD_FILE",
    "DUMPFILE", "INFORMATION_SCHEMA", "SHUTDOWN"
}
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
KNOWN_COLS = ["employee_id", "employee_name", "department", "salary", "city"]


class InvalidQuery(ValueError):
    pass


def valid_identifier(name):
    if not isinstance(name, str) or not IDENT.match(name):
        raise InvalidQuery(f"Invalid identifier: {name!r}")
    return name


def format_sql(sql):
    """Pretty prints and beautifies SQL with keyword uppercase and clean indentation."""
    if not sql or not sql.strip():
        return ""
    return sqlparse.format(
        sql.strip(),
        reindent=True,
        keyword_case="upper",
        identifier_case="lower",
        strip_comments=False
    )


def extract_candidate_columns(sql, valid_cols=None):
    """
    Parses SQL and detects columns used in filtering (WHERE),
    sorting (ORDER BY), and grouping (GROUP BY) to suggest high-impact indexes.
    """
    if valid_cols is None:
        valid_cols = KNOWN_COLS
    valid_set = set(valid_cols)
    sql_lower = sql.lower()

    # Simple robust regex extraction of known columns in WHERE / ORDER BY clauses
    where_match = re.search(r"\bwhere\b(.*?)(?:\border\s+by\b|\bgroup\s+by\b|\blimit\b|$)", sql_lower, re.DOTALL)
    order_match = re.search(r"\border\s+by\b(.*?)(?:\blimit\b|$)", sql_lower, re.DOTALL)

    where_cols = []
    order_cols = []

    if where_match:
        where_text = where_match.group(1)
        for col in valid_cols:
            if re.search(rf"\b{col}\b", where_text) and col not in where_cols:
                where_cols.append(col)

    if order_match:
        order_text = order_match.group(1)
        for col in valid_cols:
            if re.search(rf"\b{col}\b", order_text) and col not in order_cols:
                order_cols.append(col)

    candidates = []
    # Primary single column index
    if where_cols:
        candidates.append([where_cols[0]])
    # Multi-column composite index
    if len(where_cols) > 1:
        candidates.append(where_cols[:2])
    # Filter + Sort index
    if where_cols and order_cols and order_cols[0] not in where_cols:
        candidates.append([where_cols[0], order_cols[0]])

    # Deduplicate while preserving order
    unique_candidates = []
    seen = set()
    for c in candidates:
        key = tuple(c)
        if key not in seen:
            seen.add(key)
            unique_candidates.append(c)

    return {
        "where_columns": where_cols,
        "order_columns": order_cols,
        "suggested_indexes": unique_candidates
    }


def validate(sql):
    if not sql or not sql.strip():
        raise InvalidQuery("Query is empty.")

    stmts = [s for s in sqlparse.parse(sql) if str(s).strip().strip(";")]
    if len(stmts) != 1:
        raise InvalidQuery("Exactly one statement is allowed.")

    st = stmts[0]
    st_type = st.get_type()
    
    # Allow SELECT and WITH (CTE) queries
    first_non_ws = next((t for t in st.tokens if not t.is_whitespace), None)
    first_word = first_non_ws.value.upper() if first_non_ws else ""
    if st_type not in ("SELECT", "UNKNOWN") and first_word not in ("SELECT", "WITH"):
        raise InvalidQuery("Only read-only SELECT or WITH (CTE) queries are allowed.")

    # Flatten tokens to inspect for disallowed DDL/DML keywords
    for t in st.flatten():
        val = t.value.upper()
        norm = getattr(t, "normalized", "").upper()
        if t.ttype in (Keyword, DML, DDL) and (norm in FORBIDDEN or val in FORBIDDEN):
            raise InvalidQuery(f"Keyword not allowed: {norm or val}")
        if (val in FORBIDDEN or norm in FORBIDDEN) and t.ttype is not None and "Name" in str(t.ttype):
            raise InvalidQuery(f"Keyword not allowed: {val}")

    return str(st).strip().rstrip(";")
