"""Permission-rule persistence and resolution on a Store-owned connection."""

from __future__ import annotations

import fnmatch
import sqlite3
import uuid
from typing import Any, Callable


def perm_match(text: str, pattern: str) -> bool:
    """Match a permission target while preserving exact metacharacter text."""
    text = text or ""
    pattern = pattern or "*"
    if pattern in ("*", ""):
        return True
    if text == pattern:
        return True
    try:
        return fnmatch.fnmatchcase(text, pattern)
    except Exception:  # noqa: BLE001
        return False


# Gentle defaults for the local research daemon.  The kernel can already run
# arbitrary Python, so routine confined work stays frictionless while genuinely
# external or irreversible host operations ask an actively watching human.
DEFAULT_PERMISSION_RULES = (
    ("read_file", "*.env", "deny"),
    ("read_file", "*", "allow"),
    ("write_file", "*", "allow"),
    ("edit_file", "*", "allow"),
    ("glob", "*", "allow"),
    ("grep", "*", "allow"),
    ("list_dir", "*", "allow"),
    ("save_artifact", "*", "allow"),
    ("delegate", "*", "allow"),
    ("env_setup", "*", "allow"),
    ("web_fetch", "*", "allow"),
    ("web_search", "*", "allow"),
    ("skills_edit", "*", "allow"),
    ("mcp_call", "*", "ask"),
    ("exec_background", "*", "ask"),
    ("credentials_set", "*", "ask"),
    ("skills_delete", "*", "ask"),
    ("skills_publish", "*", "ask"),
)


class PermissionRuleRepository:
    """Own persisted permission rules and their precedence semantics.

    ``Store`` supplies its SQLite connection and re-entrant lock.  Settings
    callbacks preserve the existing two-step seed behavior: commit default
    rules first, then write the ``perm_seeded`` marker through Store.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        lock: Any,
        *,
        clock_ms: Callable[[], int],
        get_setting: Callable[[str, str | None], str | None],
        set_setting: Callable[[str, str], None],
    ) -> None:
        self._connection = connection
        self._lock = lock
        self._clock_ms = clock_ms
        self._get_setting = get_setting
        self._set_setting = set_setting

    def set_rule(
        self,
        *,
        scope: str,
        scope_id: str = "",
        tool: str,
        pattern: str = "*",
        decision: str,
    ) -> str:
        """Upsert a rule while retaining its identity for the same key."""
        scope_id = scope_id or ""
        pattern = pattern or "*"
        now = self._clock_ms()
        with self._lock:
            row = self._connection.execute(
                "SELECT rule_id FROM permission_rules WHERE scope=? AND "
                "scope_id=? AND tool=? AND pattern=?",
                (scope, scope_id, tool, pattern),
            ).fetchone()
            if row:
                rule_id = row["rule_id"]
                self._connection.execute(
                    "UPDATE permission_rules SET decision=?, updated_at=? "
                    "WHERE rule_id=?",
                    (decision, now, rule_id),
                )
            else:
                rule_id = f"perm_{uuid.uuid4().hex[:12]}"
                self._connection.execute(
                    "INSERT INTO permission_rules(rule_id,scope,scope_id,tool,"
                    "pattern,decision,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                    (
                        rule_id,
                        scope,
                        scope_id,
                        tool,
                        pattern,
                        decision,
                        now,
                        now,
                    ),
                )
            self._connection.commit()
        return rule_id

    def delete_rule(self, rule_id: str) -> None:
        with self._lock:
            self._connection.execute(
                "DELETE FROM permission_rules WHERE rule_id=?",
                (rule_id,),
            )
            self._connection.commit()

    def get_rules(self, *, scope: str, scope_id: str = "") -> list[dict]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM permission_rules WHERE scope=? AND scope_id=? "
                "ORDER BY updated_at",
                (scope, scope_id or ""),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_for_frame(
        self,
        *,
        root_frame_id: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        """Return every rule relevant to a conversation, grouped by scope."""
        return {
            "global": self.get_rules(scope="global", scope_id=""),
            "project": (
                self.get_rules(scope="project", scope_id=project_id)
                if project_id
                else []
            ),
            "conversation": (
                self.get_rules(scope="conversation", scope_id=root_frame_id)
                if root_frame_id
                else []
            ),
        }

    def resolve(
        self,
        *,
        root_frame_id: str | None = None,
        project_id: str | None = None,
        tool: str,
        pattern_input: str = "",
    ) -> str:
        """Resolve a call to ``allow``, ``ask``, or ``deny``.

        Any matching deny is an absolute veto.  Otherwise the most specific
        tool and target pattern wins, followed by narrower scope and recency.
        """
        candidates = list(self.get_rules(scope="global", scope_id=""))
        if project_id:
            candidates += self.get_rules(scope="project", scope_id=project_id)
        if root_frame_id:
            candidates += self.get_rules(
                scope="conversation",
                scope_id=root_frame_id,
            )

        scope_rank = {"global": 0, "project": 1, "conversation": 2}
        best = None
        best_key = None
        for rule in candidates:
            rule_tool = rule["tool"] or "*"
            rule_pattern = rule["pattern"] or "*"
            if not perm_match(tool, rule_tool):
                continue
            if not perm_match(pattern_input or "", rule_pattern):
                continue
            if rule["decision"] == "deny":
                return "deny"
            key = (
                0 if rule_tool in ("*", "") else 1,
                0 if rule_pattern in ("*", "") else 1,
                len(rule_pattern),
                scope_rank.get(rule["scope"], 0),
                rule.get("updated_at") or 0,
            )
            if best_key is None or key > best_key:
                best_key = key
                best = rule
        return best["decision"] if best else "ask"

    def seed_defaults(self, *, force: bool = False) -> None:
        """Idempotently insert defaults or restore them during a reset."""
        if not force and self._get_setting("perm_seeded", None):
            return
        now = self._clock_ms()
        with self._lock:
            for tool, pattern, decision in DEFAULT_PERMISSION_RULES:
                row = self._connection.execute(
                    "SELECT rule_id, decision FROM permission_rules "
                    "WHERE scope='global' AND scope_id='' AND tool=? AND pattern=?",
                    (tool, pattern),
                ).fetchone()
                if row is not None:
                    if force and row["decision"] != decision:
                        self._connection.execute(
                            "UPDATE permission_rules SET decision=?, updated_at=? "
                            "WHERE rule_id=?",
                            (decision, now, row["rule_id"]),
                        )
                    continue
                self._connection.execute(
                    "INSERT INTO permission_rules(rule_id,scope,scope_id,tool,"
                    "pattern,decision,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                    (
                        f"perm_{uuid.uuid4().hex[:12]}",
                        "global",
                        "",
                        tool,
                        pattern,
                        decision,
                        now,
                        now,
                    ),
                )
            self._connection.commit()
        self._set_setting("perm_seeded", "1")


__all__ = [
    "DEFAULT_PERMISSION_RULES",
    "PermissionRuleRepository",
    "perm_match",
]
