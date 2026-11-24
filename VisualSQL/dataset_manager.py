import random
from pathlib import Path
import pandas as pd
import database as db
from query_validator import valid_identifier, InvalidQuery

DEPTS = ["Engineering", "Finance", "HR", "Sales", "Support", "Marketing", "Operations", "Product", "Legal"]
CITIES = ["Chennai", "Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Pune", "Kolkata", "Noida", "Ahmedabad"]
FIRST_NAMES = ["Aarav", "Aditi", "Bhuvan", "Deepa", "Karthik", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Rohan", "Meera", "Suresh", "Pooja", "Arjun", "Divya"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Rao", "Kumar", "Singh", "Gupta", "Deshmukh", "Joshi", "Bose", "Mehta"]
COLS = ["employee_id", "employee_name", "department", "salary", "city"]


def generate_csv(n, path=None, seed=42):
    r = random.Random(seed)
    names = [f"{r.choice(FIRST_NAMES)} {r.choice(LAST_NAMES)}" for _ in range(n)]
    df = pd.DataFrame({
        "employee_id": range(1, n + 1),
        "employee_name": names,
        "department": [r.choice(DEPTS) for _ in range(n)],
        "salary": [round(r.uniform(28000, 185000), 2) for _ in range(n)],
        "city": [r.choice(CITIES) for _ in range(n)]
    })
    if path:
        df.to_csv(path, index=False)
    return df


def load_dataframe(df, table, source="generated"):
    table = valid_identifier(table)
    if not isinstance(df, pd.DataFrame):
        raise InvalidQuery("Invalid dataset structure.")
    df = df.copy()
    if list(df.columns) != COLS:
        raise InvalidQuery(f"CSV columns must be exactly: {', '.join(COLS)}")
    if df.isnull().any().any():
        raise InvalidQuery("CSV contains missing/null values.")
    try:
        df = df.astype({"employee_id": int, "salary": float})
        if (df["employee_id"] <= 0).any():
            raise InvalidQuery("employee_id values must be positive integers.")
        if df["employee_id"].duplicated().any():
            raise InvalidQuery("employee_id values must be unique.")
    except (TypeError, ValueError, OverflowError) as e:
        raise InvalidQuery("employee_id and salary must contain valid numeric values.") from e

    db.execute(f"DROP TABLE IF EXISTS `{table}`" if db.BACKEND == "mysql" else f'DROP TABLE IF EXISTS "{table}"')

    create_sql = (
        f"CREATE TABLE `{table}` (employee_id INT PRIMARY KEY, employee_name VARCHAR(80), department VARCHAR(40), salary DECIMAL(10,2), city VARCHAR(40))"
        if db.BACKEND == "mysql"
        else f'CREATE TABLE "{table}" (employee_id INTEGER PRIMARY KEY, employee_name TEXT NOT NULL, department TEXT NOT NULL, salary REAL NOT NULL, city TEXT NOT NULL)'
    )
    db.execute(create_sql)

    c = db.conn(True)
    cur = c.cursor()
    try:
        placeholders = "?,?,?,?,?" if db.BACKEND == "sqlite" else "%s,%s,%s,%s,%s"
        insert_sql = (
            f'INSERT INTO "{table}" VALUES ({placeholders})'
            if db.BACKEND == "sqlite"
            else f"INSERT INTO `{table}` VALUES ({placeholders})"
        )
        cur.executemany(insert_sql, df[COLS].itertuples(index=False, name=None))
        c.commit()
    finally:
        c.close()

    db.execute(
        "REPLACE INTO datasets(table_name,row_count,source) VALUES(%s,%s,%s)",
        (table, len(df), source)
    )


def delete_dataset(table):
    table = valid_identifier(table)
    db.execute(f"DROP TABLE IF EXISTS `{table}`" if db.BACKEND == "mysql" else f'DROP TABLE IF EXISTS "{table}"')
    db.execute("DELETE FROM datasets WHERE table_name=%s", (table,))


def import_upload(file_storage, name):
    if not file_storage or not getattr(file_storage, "filename", ""):
        raise InvalidQuery("A CSV file is required.")
    if not name or not name.strip():
        raise InvalidQuery("A dataset name is required.")
    clean_name = valid_identifier(name.strip().lower().replace(" ", "_"))
    df = pd.read_csv(file_storage)
    if len(df) > 500000:
        raise InvalidQuery("CSV exceeds maximum allowed size (500,000 rows).")
    load_dataframe(df, f"user_{clean_name}", "upload")


def preview(file_storage, rows=10):
    return pd.read_csv(file_storage, nrows=rows).to_dict("records")


def setup_samples(sizes=(1000, 10000, 50000, 100000)):
    Path("datasets").mkdir(parents=True, exist_ok=True)
    for n in sizes:
        load_dataframe(generate_csv(n), f"employees_{n}", "generated")
    generate_csv(1000, "datasets/sample_data.csv")


def ensure_initial_sample():
    """Ensures at least employees_1000 exists so initial queries run without setup."""
    existing = db.fetch("SELECT id FROM datasets WHERE table_name='employees_1000'")
    if not existing:
        load_dataframe(generate_csv(1000), "employees_1000", "generated")


if __name__ == "__main__":
    setup_samples()
    print("Sample datasets created.")
