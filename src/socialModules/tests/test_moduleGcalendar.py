from unittest.mock import ANY, MagicMock

from socialModules.moduleGcalendar import moduleGcalendar


class TestModuleGcalendar:
    def test_set_posts_accepts_optional_query_parameters(self, capsys):
        calendar = moduleGcalendar()
        calendar.active = "calendar-id"
        client = MagicMock()
        events_api = client.events.return_value
        events_api.list.return_value.execute.return_value = {"items": []}
        calendar.client = client

        calendar.setPosts(max_results=None, event_types="default", show_active=False)

        events_api.list.assert_called_once_with(
            calendarId="calendar-id",
            timeMin=ANY,
            singleEvents=True,
            orderBy="startTime",
            eventTypes="default",
        )
        assert capsys.readouterr().out == ""
