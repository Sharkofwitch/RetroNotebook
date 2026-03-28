"""Snapshot-based version history for RetroNotebook.

Snapshots are stored as JSON files in:
  ~/retro-notebook-notebooks/.history/<notebook_name>/
Each file is named YYYYMMDD_HHMMSS.json and contains the full cell list
plus metadata (timestamp, reason).
"""

import json
import os
import datetime

from app.storage import cells_to_data

KEEP_SNAPSHOTS = 20


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def get_history_dir(notebook_name):
    """Return (and create) the history directory for *notebook_name*."""
    home = os.path.expanduser("~")
    history_dir = os.path.join(
        home, "retro-notebook-notebooks", ".history", notebook_name
    )
    os.makedirs(history_dir, exist_ok=True)
    return history_dir


# ---------------------------------------------------------------------------
# Snapshot I/O
# ---------------------------------------------------------------------------

def save_snapshot(cells, notebook_name, reason="manual"):
    """Save a snapshot of the current notebook.

    Parameters
    ----------
    cells:
        List of NotebookCell widget instances (the live notebook).
    notebook_name:
        Short identifier used to group snapshots (e.g. "auto_save").
    reason:
        Human-readable tag such as "manual", "pre-restore", etc.

    Returns
    -------
    str
        Full path to the newly created snapshot file.
    """
    history_dir = get_history_dir(notebook_name)
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(history_dir, f"{timestamp}.json")

    snapshot = {
        "timestamp": now.isoformat(),
        "reason": reason,
        "cells": cells_to_data(cells),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    cleanup_old_snapshots(notebook_name)
    return path


def list_snapshots(notebook_name):
    """Return all snapshots for *notebook_name*, newest first.

    Each entry is a dict with keys:
      path, timestamp, reason, cells
    """
    history_dir = get_history_dir(notebook_name)
    snapshots = []
    for fname in sorted(os.listdir(history_dir), reverse=True):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(history_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                snap = json.load(f)
            snapshots.append({
                "path": path,
                "timestamp": snap.get("timestamp", ""),
                "reason": snap.get("reason", ""),
                "cells": snap.get("cells", []),
            })
        except Exception:
            continue
    return snapshots


def load_snapshot(path):
    """Return the cell data list stored in *path*."""
    with open(path, "r", encoding="utf-8") as f:
        snap = json.load(f)
    return snap.get("cells", [])


# ---------------------------------------------------------------------------
# Diff helper
# ---------------------------------------------------------------------------

def get_diff_summary(snap_cells, current_cells):
    """Return a short human-readable diff between two cell-data lists.

    Parameters
    ----------
    snap_cells:
        Cell data from a snapshot (list of dicts).
    current_cells:
        Current cell data (list of dicts).
    """
    old_count = len(snap_cells)
    new_count = len(current_cells)

    added = max(0, new_count - old_count)
    removed = max(0, old_count - new_count)

    edited = 0
    for i in range(min(old_count, new_count)):
        if snap_cells[i].get("input", "") != current_cells[i].get("input", ""):
            edited += 1

    parts = []
    if added:
        parts.append(f"+{added} cell{'s' if added != 1 else ''}")
    if removed:
        parts.append(f"-{removed} cell{'s' if removed != 1 else ''}")
    if edited:
        parts.append(f"~{edited} edited")

    return ", ".join(parts) if parts else "no changes"


# ---------------------------------------------------------------------------
# Retention policy
# ---------------------------------------------------------------------------

def cleanup_old_snapshots(notebook_name, keep=KEEP_SNAPSHOTS):
    """Delete snapshots beyond the *keep* limit (oldest first)."""
    history_dir = get_history_dir(notebook_name)
    files = sorted(
        [f for f in os.listdir(history_dir) if f.endswith(".json")],
        reverse=True,
    )
    for old_file in files[keep:]:
        try:
            os.remove(os.path.join(history_dir, old_file))
        except Exception:
            pass
