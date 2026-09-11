import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_DB_PATH = "data/loglens.db"


class Database:
    """
    SQLite persistence layer for the LogLens platform.
    Stores logs, mined templates, alerts, agent investigations, responses,
    and blockchain blocks.
    """
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Logs table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_id INTEGER NOT NULL,
                raw_log TEXT NOT NULL,
                source TEXT NOT NULL,
                timestamp TEXT,
                cluster_id TEXT
            )
            """)

            # Templates table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                cluster_id TEXT PRIMARY KEY,
                template TEXT NOT NULL,
                count INTEGER NOT NULL,
                frequency REAL NOT NULL,
                source TEXT,
                signature TEXT
            )
            """)

            # Alerts table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                cluster_id TEXT NOT NULL,
                source TEXT NOT NULL,
                risk TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                confidence REAL NOT NULL,
                template TEXT,
                reason TEXT,
                breakdown_json TEXT,
                evidence_json TEXT,
                created_at REAL
            )
            """)

            # Investigations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                agent_id TEXT NOT NULL,
                alert_id TEXT PRIMARY KEY,
                cluster_id TEXT NOT NULL,
                risk TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                confidence REAL NOT NULL,
                status TEXT NOT NULL,
                reason TEXT,
                recommended_action TEXT,
                investigated_at REAL
            )
            """)

            # Responses table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                response_id TEXT PRIMARY KEY,
                alert_id TEXT NOT NULL,
                cluster_id TEXT NOT NULL,
                action TEXT NOT NULL,
                priority TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                reason TEXT,
                risk_score INTEGER NOT NULL,
                decided_at REAL
            )
            """)

            # Blockchain blocks table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS blockchain_blocks (
                block_index INTEGER PRIMARY KEY,
                timestamp REAL NOT NULL,
                event_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                block_hash TEXT NOT NULL
            )
            """)

            conn.commit()

    def clear_analysis(self):
        """Clears logs, templates, alerts, investigations, and responses for fresh analysis."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM logs")
            cursor.execute("DELETE FROM templates")
            cursor.execute("DELETE FROM alerts")
            cursor.execute("DELETE FROM investigations")
            cursor.execute("DELETE FROM responses")
            conn.commit()

    def save_analysis_run(
        self,
        logs: List[Dict[str, Any]],
        templates: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
        investigations: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        source: str = "Generic",
        clear_previous: bool = True
    ):
        """Persists complete analysis pipeline outputs."""
        if clear_previous:
            self.clear_analysis()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert logs (batch)
            log_tuples = []
            for log in logs:
                log_tuples.append((
                    log.get("line_id"),
                    log.get("raw_log", ""),
                    log.get("source", source),
                    log.get("timestamp", ""),
                    log.get("cluster_id", "")
                ))
            cursor.executemany(
                "INSERT INTO logs (line_id, raw_log, source, timestamp, cluster_id) VALUES (?, ?, ?, ?, ?)",
                log_tuples
            )

            # Insert templates
            for tmpl in templates:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO templates
                    (cluster_id, template, count, frequency, source, signature)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tmpl.get("cluster_id"),
                        tmpl.get("template"),
                        tmpl.get("count", tmpl.get("size", 0)),
                        tmpl.get("frequency", 0.0),
                        source,
                        tmpl.get("signature", "")
                    )
                )

            # Insert alerts
            for alert in alerts:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO alerts
                    (alert_id, cluster_id, source, risk, risk_score, confidence, template, reason, breakdown_json, evidence_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert.get("alert_id"),
                        alert.get("cluster_id"),
                        alert.get("source", source),
                        alert.get("risk"),
                        alert.get("risk_score"),
                        alert.get("confidence", 0.9),
                        alert.get("template"),
                        alert.get("reason"),
                        json.dumps(alert.get("breakdown", {})),
                        json.dumps(alert.get("evidence", [])),
                        alert.get("created_at", 0.0)
                    )
                )

            # Insert investigations
            for inv in investigations:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO investigations
                    (agent_id, alert_id, cluster_id, risk, risk_score, confidence, status, reason, recommended_action, investigated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        inv.get("agent_id"),
                        inv.get("alert_id"),
                        inv.get("cluster_id"),
                        inv.get("risk"),
                        inv.get("risk_score"),
                        inv.get("confidence", 0.9),
                        inv.get("status"),
                        inv.get("reason"),
                        inv.get("recommended_action"),
                        inv.get("investigated_at", 0.0)
                    )
                )

            # Insert responses
            for resp in responses:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO responses
                    (response_id, alert_id, cluster_id, action, priority, agent_id, reason, risk_score, decided_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        resp.get("response_id"),
                        resp.get("alert_id"),
                        resp.get("cluster_id"),
                        resp.get("action"),
                        resp.get("priority"),
                        resp.get("agent_id"),
                        resp.get("reason"),
                        resp.get("risk_score", 0),
                        resp.get("decided_at", 0.0)
                    )
                )

            conn.commit()

    def sync_blockchain_blocks(self, blocks: List[Dict[str, Any]]):
        """Synchronizes blockchain block records with SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for b in blocks:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO blockchain_blocks
                    (block_index, timestamp, event_json, previous_hash, block_hash)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        b["index"],
                        b["timestamp"],
                        json.dumps(b["event"], ensure_ascii=False),
                        b["previous_hash"],
                        b["hash"]
                    )
                )
            conn.commit()

    def get_logs(
        self,
        source: Optional[str] = None,
        cluster_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Queries logs with optional filters and pagination."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT line_id, raw_log, source, timestamp, cluster_id FROM logs WHERE 1=1"
            params: List[Any] = []

            if source and source != "ALL":
                query += " AND source = ?"
                params.append(source)
            if cluster_id:
                query += " AND cluster_id = ?"
                params.append(cluster_id)
            if search:
                query += " AND raw_log LIKE ?"
                params.append(f"%{search}%")

            # Count total
            count_query = f"SELECT COUNT(*) FROM ({query})"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            query += " ORDER BY line_id ASC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cursor.execute(query, params)
            rows = [dict(row) for row in cursor.fetchall()]

            return rows, total

    def get_templates(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM templates ORDER BY count DESC")
            return [dict(r) for r in cursor.fetchall()]

    def get_alerts(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts ORDER BY risk_score DESC")
            rows = []
            for r in cursor.fetchall():
                d = dict(r)
                d["breakdown"] = json.loads(d.get("breakdown_json") or "{}")
                d["evidence"] = json.loads(d.get("evidence_json") or "[]")
                rows.append(d)
            return rows

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["breakdown"] = json.loads(d.get("breakdown_json") or "{}")
            d["evidence"] = json.loads(d.get("evidence_json") or "[]")
            return d

    def get_investigations(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM investigations ORDER BY risk_score DESC")
            return [dict(r) for r in cursor.fetchall()]

    def get_responses(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM responses ORDER BY risk_score DESC")
            return [dict(r) for r in cursor.fetchall()]

    def get_blockchain_blocks(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blockchain_blocks ORDER BY block_index ASC")
            blocks = []
            for r in cursor.fetchall():
                blocks.append({
                    "index": r["block_index"],
                    "timestamp": r["timestamp"],
                    "event": json.loads(r["event_json"]),
                    "previous_hash": r["previous_hash"],
                    "hash": r["block_hash"]
                })
            return blocks


_global_db = None

def get_db() -> Database:
    global _global_db
    if _global_db is None:
        _global_db = Database()
    return _global_db
