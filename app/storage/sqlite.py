import sqlite3
from pathlib import Path

from app.personalization.baseline import BaselineState


class SQLiteBaselineRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS baselines (
                    subject_id TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    mean REAL NOT NULL,
                    variance REAL NOT NULL,
                    count INTEGER NOT NULL,
                    alpha REAL NOT NULL,
                    warmup_minimum INTEGER NOT NULL,
                    PRIMARY KEY (subject_id, metric)
                )
                """
            )

    def save(self, state: BaselineState) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO baselines (
                    subject_id,
                    metric,
                    mean,
                    variance,
                    count,
                    alpha,
                    warmup_minimum
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(subject_id, metric)
                DO UPDATE SET
                    mean = excluded.mean,
                    variance = excluded.variance,
                    count = excluded.count,
                    alpha = excluded.alpha,
                    warmup_minimum = excluded.warmup_minimum
                """,
                (
                    state.subject_id,
                    state.metric,
                    state.mean,
                    state.variance,
                    state.count,
                    state.alpha,
                    state.warmup_minimum,
                ),
            )

    def load(
        self,
        subject_id: str,
        metric: str,
    ) -> BaselineState | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    subject_id,
                    metric,
                    mean,
                    variance,
                    count,
                    alpha,
                    warmup_minimum
                FROM baselines
                WHERE subject_id = ?
                  AND metric = ?
                """,
                (subject_id, metric),
            ).fetchone()

        if row is None:
            return None

        return BaselineState(
            subject_id=row[0],
            metric=row[1],
            mean=row[2],
            variance=row[3],
            count=row[4],
            alpha=row[5],
            warmup_minimum=row[6],
        )
