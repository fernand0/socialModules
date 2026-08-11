"""Minimal test stub for note_app package used by moduleNotes during local testing."""

from .manager import NoteManager, StorageManager


def create_client(storage_dir=None):
    return {"manager": NoteManager(storage_dir), "storage": StorageManager(storage_dir)}


__all__ = ["NoteManager", "StorageManager", "create_client"]
