import os
from dotenv import load_dotenv
load_dotenv()
DB = dict(host=os.getenv("DB_HOST", "localhost"), database=os.getenv("DB_NAME", "visualsql"))
ADMIN = dict(user=os.getenv("ADMIN_USER"), password=os.getenv("ADMIN_PASSWORD"))
BENCH = dict(user=os.getenv("BENCH_USER"), password=os.getenv("BENCH_PASSWORD"))
TIMEOUT_MS = int(os.getenv("QUERY_TIMEOUT_MS", "15000"))
SIZES = [1000, 10000, 50000, 100000]
