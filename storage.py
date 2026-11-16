"""
Storage layer. Two interchangeable backends behind one Store:

  SupabaseBackend  free hosted Postgres (permanent, use this for real data)
  SQLiteBackend    a local file (zero setup, but Streamlit Cloud wipes it on restart)

Plus a Dropbox backup/restore of the whole database as one JSON file.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone

import requests

COLUMNS = {
    "students": ["id", "name", "roll", "class_name", "section", "language", "level",
                 "photo", "consent", "teacher", "created_at"],
    "attempts": ["id", "student_id", "ts", "language", "level", "wcpm", "accuracy",
                 "coverage", "correct", "misread", "skipped", "extra", "duration",
                 "comprehension", "met", "bad_words", "skip_words"],
    "badges": ["id", "student_id", "badge_key", "earned_at"],
}
_INT = {"level", "consent", "correct", "misread", "skipped", "extra", "comprehension", "met"}
_REAL = {"wcpm", "accuracy", "coverage", "duration"}


def _sqlite_type(col):
    return "INTEGER" if col in _INT else "REAL" if col in _REAL else "TEXT"


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id():
    return uuid.uuid4().hex[:10]


def _check(table, cols):
    bad = [c for c in cols if c not in COLUMNS[table]]
    if bad:
        raise ValueError(f"unknown column(s) {bad} for {table}")


# --------------------------------------------------------------------------- SQLite
class SQLiteBackend:
    kind = "sqlite"
    label = "Local SQLite file"
    permanent = False

    def __init__(self, path="padho_local.db"):
        self.path = path
        with self._conn() as c:
            for t, cols in COLUMNS.items():
                defs = ", ".join(f"{col} {_sqlite_type(col)}" + (" PRIMARY KEY" if col == "id" else "")
                                 for col in cols)
                c.execute(f"CREATE TABLE IF NOT EXISTS {t} ({defs})")
            c.execute("CREATE INDEX IF NOT EXISTS ix_att ON attempts(student_id)")

    def _conn(self):
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def select(self, table, where=None, columns=None, order=None, limit=None):
        cols = columns or COLUMNS[table]
        _check(table, cols)
        sql, args = f"SELECT {','.join(cols)} FROM {table}", []
        if where:
            _check(table, where)
            sql += " WHERE " + " AND ".join(f"{k}=?" for k in where)
            args = list(where.values())
        if order:
            col, _, d = order.partition(".")
            _check(table, [col])
            sql += f" ORDER BY {col} {'DESC' if d == 'desc' else 'ASC'}"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._conn() as c:
            return [dict(r) for r in c.execute(sql, args).fetchall()]

    def insert(self, table, rows, ignore_dupes=False):
        rows = rows if isinstance(rows, list) else [rows]
        if not rows:
            return
        cols = COLUMNS[table]
        verb = "INSERT OR IGNORE" if ignore_dupes else "INSERT"
        sql = f"{verb} INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})"
        with self._conn() as c:
            c.executemany(sql, [[r.get(col) for col in cols] for r in rows])

    def update(self, table, id_, patch):
        _check(table, patch)
        sql = f"UPDATE {table} SET {', '.join(f'{k}=?' for k in patch)} WHERE id=?"
        with self._conn() as c:
            c.execute(sql, list(patch.values()) + [id_])

    def delete(self, table, where):
        _check(table, where)
        sql = f"DELETE FROM {table} WHERE " + " AND ".join(f"{k}=?" for k in where)
        with self._conn() as c:
            c.execute(sql, list(where.values()))


# ------------------------------------------------------------------------- Supabase
class SupabaseBackend:
    kind = "supabase"
    label = "Supabase (Postgres)"
    permanent = True

    def __init__(self, url, key):
        self.base = url.rstrip("/") + "/rest/v1"
        self.h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _req(self, method, table, params=None, json_body=None, headers=None):
        r = requests.request(method, f"{self.base}/{table}", params=params, json=json_body,
                             headers={**self.h, **(headers or {})}, timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase HTTP {r.status_code}: {r.text[:300]}")
        return r

    def select(self, table, where=None, columns=None, order=None, limit=None):
        cols = columns or COLUMNS[table]
        _check(table, cols)
        params = {"select": ",".join(cols)}
        if where:
            _check(table, where)
            params.update({k: f"eq.{v}" for k, v in where.items()})
        if order:
            _check(table, [order.partition(".")[0]])
            params["order"] = order
        out, start, page = [], 0, 1000
        while True:
            hdr = {"Range-Unit": "items", "Range": f"{start}-{start + page - 1}"}
            rows = self._req("GET", table, params, headers=hdr).json()
            out += rows
            if limit and len(out) >= limit:
                return out[:limit]
            if len(rows) < page:
                return out
            start += page

    def insert(self, table, rows, ignore_dupes=False):
        rows = rows if isinstance(rows, list) else [rows]
        cols = COLUMNS[table]
        prefer = ("resolution=ignore-duplicates," if ignore_dupes else "") + "return=minimal"
        params = {"on_conflict": "id"} if ignore_dupes else None
        for i in range(0, len(rows), 200):
            chunk = [{c: r.get(c) for c in cols} for r in rows[i:i + 200]]
            self._req("POST", table, params, chunk, {"Prefer": prefer})

    def update(self, table, id_, patch):
        _check(table, patch)
        self._req("PATCH", table, {"id": f"eq.{id_}"}, patch, {"Prefer": "return=minimal"})

    def delete(self, table, where):
        _check(table, where)
        self._req("DELETE", table, {k: f"eq.{v}" for k, v in where.items()})


# ---------------------------------------------------------------------------- Store
class Store:
    def __init__(self, backend):
        self.b = backend

    # students
    def students(self):
        cols = [c for c in COLUMNS["students"] if c != "photo"]  # photos are fetched one at a time
        return sorted(self.b.select("students", columns=cols), key=lambda s: (s["class_name"] or "", s["name"].lower()))

    def student(self, sid):
        rows = self.b.select("students", where={"id": sid})
        return rows[0] if rows else None

    def photo(self, sid):
        rows = self.b.select("students", where={"id": sid}, columns=["photo"])
        return (rows[0]["photo"] if rows else None) or None

    def add_student(self, **f):
        row = {"id": new_id(), "level": 1, "consent": 0, "created_at": now_iso(), **f}
        self.b.insert("students", row)
        return row["id"]

    def update_student(self, sid, **patch):
        self.b.update("students", sid, patch)

    def delete_student(self, sid):
        self.b.delete("attempts", {"student_id": sid})
        self.b.delete("badges", {"student_id": sid})
        self.b.delete("students", {"id": sid})

    # attempts
    def attempts(self, student_id=None):
        where = {"student_id": student_id} if student_id else None
        return self.b.select("attempts", where=where, order="ts.asc")

    def add_attempt(self, **f):
        row = {"id": new_id(), "ts": now_iso(), **f}
        self.b.insert("attempts", row)
        return row

    # badges
    def badges(self, student_id=None):
        where = {"student_id": student_id} if student_id else None
        return self.b.select("badges", where=where)

    def award(self, student_id, key):
        self.b.insert("badges", {"id": f"{student_id}:{key}", "student_id": student_id,
                                 "badge_key": key, "earned_at": now_iso()}, ignore_dupes=True)

    # backup / restore
    def dump(self):
        return {"app": "padho", "version": 1, "exported_at": now_iso(),
                "students": self.b.select("students"),
                "attempts": self.b.select("attempts"),
                "badges": self.b.select("badges")}

    def restore(self, data):
        counts = {}
        for t in ("students", "attempts", "badges"):
            rows = data.get(t, [])
            self.b.insert(t, rows, ignore_dupes=True)
            counts[t] = len(rows)
        return counts


# ------------------------------------------------------------------------- Dropbox
def _dropbox_token(get):
    """Short-lived token from a refresh token (preferred), else a plain access token."""
    rt, app_key, app_secret = get("DROPBOX_REFRESH_TOKEN"), get("DROPBOX_APP_KEY"), get("DROPBOX_APP_SECRET")
    if rt and app_key and app_secret:
        r = requests.post("https://api.dropbox.com/oauth2/token",
                          data={"grant_type": "refresh_token", "refresh_token": rt},
                          auth=(app_key, app_secret), timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"Dropbox token refresh failed: {r.text[:200]}")
        return r.json()["access_token"]
    tok = get("DROPBOX_ACCESS_TOKEN")
    if not tok:
        raise RuntimeError("No Dropbox credentials in Secrets")
    return tok


def dropbox_configured(get):
    return bool(get("DROPBOX_ACCESS_TOKEN") or (get("DROPBOX_REFRESH_TOKEN") and get("DROPBOX_APP_KEY")
                                                and get("DROPBOX_APP_SECRET")))


def dropbox_upload(get, data: bytes, path: str):
    token = _dropbox_token(get)
    arg = json.dumps({"path": path, "mode": "overwrite", "mute": True})
    r = requests.post("https://content.dropboxapi.com/2/files/upload",
                      headers={"Authorization": f"Bearer {token}", "Dropbox-API-Arg": arg,
                               "Content-Type": "application/octet-stream"},
                      data=data, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Dropbox HTTP {r.status_code}: {r.text[:300]}")
    return r.json().get("path_display", path)


def dropbox_latest(get, folder="/Padho"):
    """Return (path, bytes) of the newest backup file in the folder."""
    token = _dropbox_token(get)
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post("https://api.dropboxapi.com/2/files/list_folder", headers=h,
                      json={"path": folder}, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"Dropbox HTTP {r.status_code}: {r.text[:300]}")
    files = [e for e in r.json().get("entries", []) if e.get(".tag") == "file" and e["name"].endswith(".json")]
    if not files:
        raise RuntimeError(f"No backup files found in {folder}")
    newest = max(files, key=lambda e: e["server_modified"])
    d = requests.post("https://content.dropboxapi.com/2/files/download",
                      headers={**h, "Dropbox-API-Arg": json.dumps({"path": newest["path_lower"]})}, timeout=60)
    if d.status_code >= 400:
        raise RuntimeError(f"Dropbox HTTP {d.status_code}: {d.text[:300]}")
    return newest["path_display"], d.content
