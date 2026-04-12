"""
Database Module
──────────────
SQLite-backed data store with rich sample data.
Provides natural language → SQL query interface via LangChain.
"""

import sqlite3
import os
from pathlib import Path
from typing import Any
from datetime import datetime, timedelta
import random


DB_PATH = os.getenv("DB_PATH", "./docubot.db")


class Database:
    """
    SQLite wrapper with:
    - Employees, Products, Projects, Contracts tables
    - Seeded sample data for demo
    - LangChain SQLDatabaseChain integration
    - Direct query capability
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    # ──────────────────────────────────────────────────────────────────────────
    # Schema
    # ──────────────────────────────────────────────────────────────────────────

    def _create_tables(self):
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS employees (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT NOT NULL,
                    email       TEXT UNIQUE,
                    department  TEXT,
                    role        TEXT,
                    salary      REAL,
                    hire_date   TEXT,
                    status      TEXT DEFAULT 'active'
                );

                CREATE TABLE IF NOT EXISTS products (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT NOT NULL,
                    category    TEXT,
                    price       REAL,
                    stock       INTEGER,
                    description TEXT,
                    sku         TEXT UNIQUE,
                    active      INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    title       TEXT NOT NULL,
                    status      TEXT,
                    start_date  TEXT,
                    end_date    TEXT,
                    budget      REAL,
                    lead_id     INTEGER,
                    FOREIGN KEY (lead_id) REFERENCES employees(id)
                );

                CREATE TABLE IF NOT EXISTS contracts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT NOT NULL,
                    value       REAL,
                    start_date  TEXT,
                    end_date    TEXT,
                    status      TEXT,
                    project_id  INTEGER,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
            """)

    # ──────────────────────────────────────────────────────────────────────────
    # Seed Data
    # ──────────────────────────────────────────────────────────────────────────

    def seed_sample_data(self):
        """Populate tables with realistic demo data if empty."""
        if self._table_has_data("employees"):
            return

        employees = [
            ("Alice Johnson", "alice@company.com", "Engineering", "Senior Engineer", 115000, "2021-03-15"),
            ("Bob Martinez", "bob@company.com", "Engineering", "Junior Developer", 72000, "2023-01-10"),
            ("Carol White", "carol@company.com", "Product", "Product Manager", 105000, "2020-07-22"),
            ("David Kim", "david@company.com", "Sales", "Account Executive", 85000, "2022-06-01"),
            ("Eva Chen", "eva@company.com", "HR", "HR Manager", 90000, "2019-11-05"),
            ("Frank Brown", "frank@company.com", "Engineering", "DevOps Engineer", 108000, "2021-09-18"),
            ("Grace Lee", "grace@company.com", "Design", "UX Designer", 95000, "2022-02-14"),
            ("Henry Davis", "henry@company.com", "Engineering", "Tech Lead", 130000, "2018-04-30"),
            ("Iris Patel", "iris@company.com", "Marketing", "Marketing Manager", 88000, "2023-03-07"),
            ("James Wilson", "james@company.com", "Sales", "Sales Director", 145000, "2017-08-12"),
        ]

        products = [
            ("CloudSync Pro", "Software", 299.99, 999, "Enterprise cloud synchronization", "CSP-001"),
            ("DataVault", "Software", 199.99, 500, "Secure data storage solution", "DV-002"),
            ("API Gateway", "Infrastructure", 499.99, 200, "Scalable API management", "APG-003"),
            ("AI Analyzer", "AI/ML", 899.99, 150, "Document AI analysis tool", "AIA-004"),
            ("StreamBot", "Software", 149.99, 750, "Real-time data streaming", "SB-005"),
            ("SecureVPN", "Security", 59.99, 2000, "Enterprise VPN solution", "SVN-006"),
            ("MonitorDash", "DevOps", 249.99, 400, "System monitoring dashboard", "MD-007"),
            ("BackupCloud", "Infrastructure", 79.99, 1500, "Automated cloud backups", "BC-008"),
        ]

        projects = [
            ("DocuBot Integration", "in_progress", "2024-01-01", "2024-06-30", 250000, 8),
            ("Customer Portal v2", "completed", "2023-06-01", "2023-12-31", 180000, 1),
            ("AI Migration", "planning", "2024-03-01", "2024-09-30", 400000, 8),
            ("Mobile App Launch", "in_progress", "2024-02-01", "2024-08-31", 320000, 3),
            ("Security Audit", "completed", "2023-09-01", "2023-11-30", 95000, 6),
        ]

        contracts = [
            ("Acme Corp", 450000, "2024-01-15", "2024-12-31", "active", 1),
            ("TechStart Inc", 125000, "2023-06-01", "2023-12-31", "completed", 2),
            ("Global Enterprises", 780000, "2024-03-01", "2025-02-28", "active", 3),
            ("Startup Hub", 67000, "2024-02-15", "2024-08-15", "active", 4),
            ("SecureBank Ltd", 210000, "2023-09-01", "2023-11-30", "completed", 5),
        ]

        with self.conn:
            self.conn.executemany(
                "INSERT OR IGNORE INTO employees (name, email, department, role, salary, hire_date) VALUES (?,?,?,?,?,?)",
                employees,
            )
            self.conn.executemany(
                "INSERT OR IGNORE INTO products (name, category, price, stock, description, sku) VALUES (?,?,?,?,?,?)",
                products,
            )
            self.conn.executemany(
                "INSERT OR IGNORE INTO projects (title, status, start_date, end_date, budget, lead_id) VALUES (?,?,?,?,?,?)",
                projects,
            )
            self.conn.executemany(
                "INSERT OR IGNORE INTO contracts (client_name, value, start_date, end_date, status, project_id) VALUES (?,?,?,?,?,?)",
                contracts,
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Query Methods
    # ──────────────────────────────────────────────────────────────────────────

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        """Execute a raw SQL query and return list of row dicts."""
        try:
            cursor = self.conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            return [{"error": str(e)}]

    def get_schema(self) -> str:
        """Return schema description for LLM context."""
        tables = self.query("SELECT name FROM sqlite_master WHERE type='table'")
        schema_parts = []
        for t in tables:
            tname = t["name"]
            cols = self.query(f"PRAGMA table_info({tname})")
            col_desc = ", ".join(f"{c['name']} ({c['type']})" for c in cols)
            schema_parts.append(f"Table '{tname}': {col_desc}")
        return "\n".join(schema_parts)

    def get_record_count(self) -> int:
        tables = ["employees", "products", "projects", "contracts"]
        total = 0
        for t in tables:
            try:
                result = self.query(f"SELECT COUNT(*) as n FROM {t}")
                total += result[0]["n"]
            except:
                pass
        return total

    def get_context_summary(self) -> str:
        """Compact text summary of DB contents for LLM prompts."""
        emp_count = self.query("SELECT COUNT(*) as n FROM employees")[0]["n"]
        prod_count = self.query("SELECT COUNT(*) as n FROM products")[0]["n"]
        proj_count = self.query("SELECT COUNT(*) as n FROM projects")[0]["n"]
        dept_rows = self.query("SELECT DISTINCT department FROM employees")
        depts = ", ".join(r["department"] for r in dept_rows)

        return (
            f"Database contains {emp_count} employees across departments: {depts}. "
            f"{prod_count} products in catalog. "
            f"{proj_count} projects tracked. "
            "Tables: employees, products, projects, contracts."
        )

    def _table_has_data(self, table: str) -> bool:
        result = self.query(f"SELECT COUNT(*) as n FROM {table}")
        return result[0]["n"] > 0
