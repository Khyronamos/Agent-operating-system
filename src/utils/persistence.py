import sqlite3
import json
import asyncio
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

class SQLitePersistenceManager:
    """
    Manages persistence for the APIA Knowledge Base using SQLite.
    """
    def __init__(self, db_path: str = "apia_knowledge_base.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        logger.info(f"SQLitePersistenceManager initialized with DB: {self.db_path}")

    async def _connect(self):
        """Establishes a database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row # Access columns by name
            await self._execute_query("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            logger.info("SQLite database connected and schema ensured.")

    async def _execute_query(self, query: str, params: tuple = ()) -> Any:
        """Executes a database query asynchronously."""
        async with self._lock:
            if self._conn is None:
                await self._connect()
            
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, # Use default thread pool
                lambda: self._execute_sync(query, params)
            )

    def _execute_sync(self, query: str, params: tuple = ()) -> Any:
        """Synchronous execution of a database query."""
        cursor = self._conn.cursor()
        try:
            cursor.execute(query, params)
            self._conn.commit()
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"SQLite query failed: {query} with params {params}. Error: {e}")
            self._conn.rollback()
            raise

    async def set_knowledge_base_value(self, key: str, value: Any):
        """Stores a key-value pair in the knowledge base."""
        value_json = json.dumps(value)
        await self._execute_query(
            "INSERT OR REPLACE INTO knowledge_base (key, value) VALUES (?, ?)",
            (key, value_json)
        )
        logger.debug(f"Persisted KB value for key: {key}")

    async def get_knowledge_base_value(self, key: str) -> Optional[Any]:
        """Retrieves a value from the knowledge base by key."""
        rows = await self._execute_query(
            "SELECT value FROM knowledge_base WHERE key = ?",
            (key,)
        )
        if rows:
            value_json = rows[0]["value"]
            return json.loads(value_json)
        return None

    async def delete_knowledge_base_value(self, key: str):
        """Deletes a key-value pair from the knowledge base."""
        await self._execute_query(
            "DELETE FROM knowledge_base WHERE key = ?",
            (key,)
        )
        logger.debug(f"Deleted KB value for key: {key}")

    async def list_knowledge_base_keys(self, prefix: Optional[str] = None) -> List[str]:
        """Lists keys in the knowledge base, optionally filtered by prefix."""
        if prefix:
            rows = await self._execute_query(
                "SELECT key FROM knowledge_base WHERE key LIKE ?",
                (f"{prefix}%",)
            )
        else:
            rows = await self._execute_query("SELECT key FROM knowledge_base")
        return [row["key"] for row in rows]

    async def close(self):
        """Closes the database connection."""
        async with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
                logger.info("SQLite database connection closed.")