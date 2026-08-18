from socialModules.moduleContent import display_posts


class TestDisplayPosts:
    def test_displays_titles_by_default(self, capsys):
        class Api:
            def getPosts(self):
                return ["first", "second"]

            def getPostTitle(self, post):
                return post.title()

        displayed = display_posts(Api())

        assert displayed == ["first", "second"]
        assert capsys.readouterr().out == "0) First\n1) Second\n"

    def test_uses_the_requested_limit_formatter_and_separator(self, capsys):
        class Api:
            def getPosts(self):
                return []

        displayed = display_posts(
            Api(),
            ["first", "second", "third"],
            format_post=lambda post: f"Post: {post}",
            limit=2,
            separator=": ",
            title="Recent posts:",
        )

        assert displayed == ["second", "third"]
        assert capsys.readouterr().out == "Recent posts:\n0: Post: second\n1: Post: third\n"
