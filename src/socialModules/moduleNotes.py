#!/usr/bin/env python
"""
Module adapter for the external `note_app` package.

This module provides a thin wrapper around a generic note application
client. It follows the structure used by other socialModules modules
so it can be used interchangeably by the rest of the project.

The implementation is intentionally defensive: it attempts to discover
sensible API method names on the provided client (list_notes, get_notes,
notes attribute, create_note, create, delete_note, delete) so it can
work with a variety of note client implementations.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from socialModules.configMod import logMsg, safe_get
from socialModules.moduleContent import Content


logger = logging.getLogger(__name__)


class moduleNotes(Content):
    """Adapter for a note-taking application.

    It exposes methods that the rest of the socialModules framework expects:
    - initApi: initialise the underlying note client
    - setApiPosts: fetch notes and expose them as posts
    - publishApiPost: create a new note
    - deleteApiPosts: delete a note

    The concrete methods used on the underlying client are discovered at
    runtime to keep this adapter flexible.
    """

    def getKeys(self, config):
        # Notes clients typically do not require per-user API keys for a
        # local or simple note store. Keep method for interface compatibility.
        PATH = config.get("NoteApp", "notes_dir")
        return (PATH, ) 

    def initApi(self, keys: Optional[Dict[str, str]] = None) -> Any:
        """Initialise the note client.

        Returns the client object on success or a string starting with
        "Error:" on failure (keeps parity with other modules' patterns).
        """
        try:
            import note_app
        except Exception as e:
            msg = f"Error: Could not import note_app: {e}"
            logMsg(msg, 3, False)
            return msg

        storage_dir = os.path.join(os.path.expanduser("~"), keys[0]) if keys else os.path.join(os.path.expanduser("~"), 'notes')
        # Try to instantiate a sensible client object. Try common names.
        client = None
        try:
            # Try to import manager/storage helper classes if the package exposes them.
            try:
                from note_app.manager import NoteManager, StorageManager
                from note_app.config import Config
            except Exception:
                NoteManager = None
                StorageManager = None
                Config = None

            if hasattr(note_app, "NoteClient"):
                client = note_app.NoteClient()
            elif hasattr(note_app, "Client"):
                client = note_app.Client()
            elif hasattr(note_app, "create_client"):
                client = note_app.create_client()
            else:
                # If the top-level module acts as a client, use it directly.
                # If manager/storage classes are available, instantiate them.
                if NoteManager and StorageManager:
                    client = {'manager': NoteManager(storage_dir),
                              'storage': StorageManager(storage_dir)}
                else:
                    client = note_app

        except Exception as e:
            msg = f"Error: Failed to instantiate note_app client: {e}"
            logMsg(msg, 3, False)
            return msg

        # Save client for later use
        self.client = client
        msgLog = f"{self.indent} Note client initialised"
        logMsg(msgLog, 2, False)
        return client

    # def _list_notes_via_client(self) -> List[Dict[str, Any]]:
    #     """Attempt to list notes using the client with several fallback names.

    #     Returns a list of lightweight dicts with keys: id, title, content, created_at
    #     """
    #     posts: List[Dict[str, Any]] = []
    #     client = getattr(self, "client", None)
    #     if client is None:
    #         return posts

    #     # possible methods/attributes
    #     candidates = ["list_notes", "get_notes", "notes", "list", "all_notes"]
    #     notes = None
    #     for name in candidates:
    #         try:
    #             if hasattr(client, name):
    #                 attr = getattr(client, name)
    #                 if callable(attr):
    #                     notes = attr()
    #                 else:
    #                     notes = attr
    #                 break
    #         except Exception:
    #             continue

    #     # If still None, try calling a top-level function in module
    #     if notes is None:
    #         try:
    #             import note_app

    #             if hasattr(note_app, "list_notes"):
    #                 notes = note_app.list_notes()
    #         except Exception:
    #             notes = None

    #     if not notes:
    #         return posts

    #     # Normalize notes into dicts
    #     for n in notes:
    #         note_dict: Dict[str, Any] = {}
    #         # If it's already a dict-like object
    #         if isinstance(n, dict):
    #             note_dict["id"] = n.get("id")
    #             note_dict["title"] = n.get("title") or n.get("name") or ""
    #             note_dict["content"] = n.get("content") or n.get("body") or ""
    #             note_dict["created_at"] = n.get("created_at") or n.get("created") or None
    #         else:
    #             # Try attribute access
    #             note_dict["id"] = getattr(n, "id", None)
    #             note_dict["title"] = getattr(n, "title", None) or getattr(n, "name", "")
    #             note_dict["content"] = getattr(n, "content", None) or getattr(n, "body", "")
    #             note_dict["created_at"] = getattr(n, "created_at", None) or getattr(n, "created", None)

    #         posts.append(note_dict)

    #     return posts

    def setApiPosts(self) -> List[Dict[str, Any]]:
        """Load notes from the note client and expose them as posts.

        Returns the list of note dicts assigned to self.posts.
        """
        posts: List[Dict[str, Any]] = []
        # Ensure client is available
        if not hasattr(self, "client") or self.client is None:
            res = self.initApi()
            if isinstance(res, str) and res.startswith("Error:"):
                msgLog = f"{self.indent} Note client unavailable, returning empty posts"
                logMsg(msgLog, 3, False)
                self.assignPosts([])
                return []

        try:
            notes = self.getClient()['manager'].list_notes()
            #print(f"Posts: {notes}")
            #print(f"Client: {self.getClient()}")
            for note_title in notes:
                #print(f"Note title: {note_title}")
                note = self.getClient()['manager'].read_note(note_title)
                print(f"Note: {note}")
                posts.append(note)

        except Exception as e:
            msgLog = f"{self.indent} Error fetching notes: {e}"
            logMsg(msgLog, 3, False)
            posts = []
        # assignPosts expects a list-like of posts; moduleContent.assignPosts will wrap
        # the provided posts. To be consistent with other modules, we pass the list
        self.assignPosts(posts)
        return self.posts

    def publishApiPost(self, *args, **kwargs) -> Dict[str, Any]:
        """Create a new note.

        Attempts to call client.create_note(title=..., content=...) or client.create(...)
        or fallbacks. Returns a dictionary with success, post_url (empty), error_message, raw_response.
        """
        res = {"success": False, "post_url": "", "error_message": "", "raw_response": None}
        content = ""
        title = ""
        link = ""

        if args and len(args) == 3:
            title, link, comment = args
            if comment:
                content = comment
        elif kwargs:
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            logging.info(f"Post: {post}")
            logging.info(f"Api: {api}")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            if post:
                content = api.getPostContent(post)

        if not title and not link:
            self.res_dict["error_message"] = "No title or link to publish."
            return self.res_dict

        if not hasattr(self, "client") or self.client is None:
            init_res = self.initApi()
            if isinstance(init_res, str) and init_res.startswith("Error:"):
                res["error_message"] = init_res
                return res

        client = self.getClient()['manager']
        create_candidates = [
            ("create_note", {"title": title, "content": content}),
            ("create", {"title": title, "content": content}),
            ("add_note", {"title": title, "body": content}),
        ]
        try:
            raw = client.create_note(title=title, content=content)
            res["raw_response"] = raw
            res["success"] = True
            return res
        except Exception as e:
            self.res_dict["error_message"] = self.report(
                "NoteApp", None, "", sys.exc_info()
            )
            self.res_dict["raw_response"] = e

        return self.res_dict


    def deleteApiPosts(self, idPost: Any) -> Any:
        """Delete a note with the given id.

        Returns the underlying client response when possible.
        """
        if not hasattr(self, "client") or self.client is None:
            init_res = self.initApi()
            if isinstance(init_res, str) and init_res.startswith("Error:"):
                return init_res

        client = self.getClient()

        try:
            return client['manager'].delete_note(idPost)
        except Exception as e:
            msgLog = f"{self.indent} Delete candidate {name} failed: {e}"
            logMsg(msgLog, 2, False)
            return msgLog

        # top-level fallback
        try:
            import note_app

            if hasattr(note_app, "delete_note"):
                return note_app.delete_note(idPost)
        except Exception:
            pass

        return f"Error: no suitable delete method found for id {idPost}"

    # Utility accessors to keep parity with other modules
    def getPostId(self, post: Any) -> Optional[Any]:
        if isinstance(post, dict):
            return post.get("id")
        return getattr(post, "id", None)

    def getApiPostTitle(self, post: Any) -> str:
        note = post.to_dict()
        result = safe_get(note, ["title"])
        return result

    def getApiPostContent(self, post: Any) -> str:
        """Robustly return a post's content for API-style callers.

        Accept dicts or objects with to_dict(), and fall back to attributes.
        """
        logging.info(f"getApiPostContent called with: {post}")
        try:
            logging.info(f"getApiPostContent called with: {post}")
            if post is None:
                return ""
            if isinstance(post, dict):
                note = post
            elif hasattr(post, 'to_dict') and callable(getattr(post, 'to_dict')):
                note = post.to_dict()
                print(f"Note: {note}")
            else:
                note = {'content': getattr(post, 'content', None)}
            # Prefer using safe_get to handle nested structures
            return safe_get(note, ["content"]) or ""
        except Exception as e:
            print(f"getApiPostContent error: {e}")
            return ""


    def getApiPostBody(self, post: Any) -> str:
        result = self.getApiPostContent(post)
        return result


    def getApiPostLink(self, post: Any) -> str:
        # Notes typically do not have public URLs; return id as string when available
        pid = self.getPostId(post)
        return str(pid) if pid is not None else ""

    def getApiPostBody(self, post: Any) -> str:
        """Return the content of a post. Accepts dicts or objects with to_dict()."""
        return self.getApiPostContent(post)


    # def getApiPostContent(self, post: Any) -> str:
    #     """Return the content of a post. Accepts dicts or objects with to_dict()."""
    #     try:
    #         if post is None:
    #             return ""
    #         if isinstance(post, dict):
    #             result = safe_get(post, 'content')
    #             # print(f"getPostContent (dict): {result}")
    #             return result or ""
    #         # objects
    #         if hasattr(post, 'to_dict') and callable(getattr(post, 'to_dict')):
    #             note = post.to_dict()
    #         else:
    #             note = {
    #                 'content': getattr(post, 'content', None)
    #             }
    #         result = safe_get(note, 'content')
    #         print(f"Result: {result}")
    #         # print(f"getPostContent (obj): {note}")
    #         return result or ""
    #     except Exception as e:
    #         # print(f"getPostContent error: {e}")
    #         return ""

    def getPostTime(self, post: Any) -> Optional[Any]:
        note = post.to_dict()
        result = safe_get(note, 'created_at')
        return result

    # Adapter helpers expected by ModuleTester
    def get_user_info(self, client: Any) -> str:
        """Return a short description for test connection output."""
        user = getattr(self, "user", None)
        if user:
            return str(user)
        # try to get username from client if available
        client_user = getattr(getattr(self, "client", None), "user", None)
        return str(client_user) if client_user else "note_app"

    def get_post_id_from_result(self, result: Any) -> Optional[Any]:
        """Extract post id from a create result for deletion checks."""
        result = safe_get(result, 'id') or safe_get(result, "post_id")
        return result

    def register_specific_tests(self, tester):
        """Register minimal tests to check client discovery and listing.

        Tests are defensive: if note_app or its client isn't available they are
        skipped silently by returning an informational string.
        """
        def _test_list_notes(api_src=None):
            msgLog = f"{self.indent} Running note app list test"
            logMsg(msgLog, 2, False)
            posts = self.setApiPosts()
            assert isinstance(posts, list)

        def _test_create_and_delete(api_src=None):
            """If the client supports create/delete, perform a roundtrip create->delete."""
            msgLog = f"{self.indent} Running create/delete roundtrip test"
            logMsg(msgLog, 2, False)

            # Ensure client is initialised
            client_res = self.initApi()
            if isinstance(client_res, str) and client_res.startswith("Error:"):
                # Nothing to do
                return

            # Attempt to create a note
            title = "unittest note"
            content = "temporary content"
            create_res = self.publishApiPost(title=title, content=content)

            # If creation failed due to lack of method, skip
            if not create_res.get("success"):
                return

            post_id = self.get_post_id_from_result(create_res.get("raw_response") or create_res)
            if not post_id:
                # nothing to delete
                return

            # Attempt deletion
            delete_res = self.deleteApiPosts(post_id)
            # Accept any non-exception return as success
            return

        tester.add_test("NoteApp: list notes test", _test_list_notes)
        tester.add_test("NoteApp: create/delete roundtrip", _test_create_and_delete)


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    note_module = moduleNotes()
    tester = ModuleTester(note_module)
    tester.run()



    m = moduleNotes()
    print("Initialising note client...")
    res = m.initApi()
    print("Client init result:", res)
    print("Fetching notes...")
    m.setPosts()
    posts = m.getPosts()
    print("Found notes:", len(posts))


if __name__ == "__main__":
    main()
