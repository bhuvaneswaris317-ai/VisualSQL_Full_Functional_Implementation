CREATE DATABASE IF NOT EXISTS visualsql;
USE visualsql;
CREATE TABLE IF NOT EXISTS datasets(id INT AUTO_INCREMENT PRIMARY KEY, table_name VARCHAR(64) NOT NULL UNIQUE, row_count INT NOT NULL, source VARCHAR(20) NOT NULL DEFAULT 'generated', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS employees(employee_id INT PRIMARY KEY, employee_name VARCHAR(80) NOT NULL, department VARCHAR(40) NOT NULL, salary DECIMAL(10,2) NOT NULL, city VARCHAR(40) NOT NULL);
CREATE TABLE IF NOT EXISTS optimization_configurations(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(60) NOT NULL UNIQUE, technique VARCHAR(40) NOT NULL, description VARCHAR(255));
CREATE TABLE IF NOT EXISTS benchmark_experiments(id INT AUTO_INCREMENT PRIMARY KEY, query_name VARCHAR(80) NOT NULL, sql_text TEXT NOT NULL, dataset_id INT, dataset_size INT NOT NULL, repetitions INT NOT NULL, status VARCHAR(20) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE SET NULL, INDEX(created_at));
CREATE TABLE IF NOT EXISTS benchmark_results(id INT AUTO_INCREMENT PRIMARY KEY, experiment_id INT NOT NULL, config_id INT NOT NULL, executed_sql TEXT NOT NULL, index_config VARCHAR(120) NOT NULL, avg_ms DOUBLE, min_ms DOUBLE, max_ms DOUBLE, row_count INT, improvement_pct DOUBLE, access_type VARCHAR(30), est_rows BIGINT, plan_json JSON, status VARCHAR(30) NOT NULL, FOREIGN KEY(experiment_id) REFERENCES benchmark_experiments(id) ON DELETE CASCADE, FOREIGN KEY(config_id) REFERENCES optimization_configurations(id), INDEX(experiment_id));
INSERT IGNORE INTO optimization_configurations(name,technique,description) VALUES('baseline','none','Original query, no extra index'),('rewrite','query rewrite','SELECT * replaced by explicit columns'),('indexed','indexing','Original query with temporary index'),('indexed+rewrite','indexing+rewrite','Index plus explicit columns');
-- As admin, create the read-only benchmark account (matches BENCH_USER in .env):
-- CREATE USER 'visualsql_ro'@'localhost' IDENTIFIED BY 'change_me';
-- GRANT SELECT ON visualsql.* TO 'visualsql_ro'@'localhost';
