class NoteManager:
    def __init__(self, storage_dir=None):
        self.storage_dir = storage_dir

    def list_notes(self):
        # Return a list of note identifiers/titles for compatibility with moduleNotes
        return ["example_note"]

    def create_note(self, title=None, content=None):
        # Return a lightweight dict as a creation result
        return {"id": "example_id", "title": title, "content": content}

    def delete_note(self, note_id):
        return True


class StorageManager:
    def __init__(self, storage_dir=None):
        self.storage_dir = storage_dir

    def load_note(self, title_or_id):
        # Return a note-like dict compatible with moduleNotes expectations
        return {"id": title_or_id, "title": title_or_id, "content": "stub content", "created_at": None}
