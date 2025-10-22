import unittest
from socialModules.moduleHtml import moduleHtml

class TestModuleHtml(unittest.TestCase):

    def setUp(self):
        self.module_html = moduleHtml()

    def test_getApiPostTitle_with_title(self):
        html_content = "<html><head><title>Test Title</title></head><body><h1>Hello</h1></body></html>"
        title = self.module_html.getApiPostTitle(html_content)
        self.assertEqual(title, "Test Title")

    def test_getApiPostTitle_without_title(self):
        html_content = "<html><head></head><body><h1>Hello</h1></body></html>"
        title = self.module_html.getApiPostTitle(html_content)
        self.assertEqual(title, "")

    def test_getApiPostTitle_empty_html(self):
        html_content = ""
        title = self.module_html.getApiPostTitle(html_content)
        self.assertEqual(title, "")

    def test_getApiPostTitle_no_head(self):
        html_content = "<html><body><h1>Hello</h1><title>Wrong Title</title></body></html>"
        title = self.module_html.getApiPostTitle(html_content)
        self.assertEqual(title, "Wrong Title")

if __name__ == '__main__':
    unittest.main()