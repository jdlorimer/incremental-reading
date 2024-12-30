from unittest.mock import MagicMock, mock_open, patch

from . import SettingsTests


class SaveTests(SettingsTests):
    def test_save(self):
        open_mock = mock_open()
        dump_mock = MagicMock()
        open_patcher = patch("ir.settings.open", open_mock)
        dump_patcher = patch("ir.settings.json.dump", dump_mock)
        open_patcher.start()
        dump_patcher.start()
        self.sm.getSettingsPath = MagicMock(return_value="foo.json")
        self.sm.settings = {"foo": "bar"}
        self.sm.save()
        open_mock.assert_called_once_with("foo.json", "w", encoding="utf-8")
        dump_mock.assert_called_once_with({"foo": "bar"}, open_mock())
        dump_patcher.stop()


class PathTests(SettingsTests):
    def test_getMediaDir(self):
        with patch("ir.settings.mw.pm.profileFolder", MagicMock(return_value="foo")):
            self.assertEqual(self.sm.getMediaDir(), "foo/collection.media")

    def test_getSettingsPath(self):
        self.sm.getMediaDir = MagicMock(return_value="foo")
        self.assertEqual(self.sm.getSettingsPath(), "foo/_ir.json")


class ValidateFormatStringsTests(SettingsTests):
    def test_valid(self):
        self.sm.defaults = {"fooFormat": "{foo} {bar}", "barFormat": "{baz} {qux}"}
        self.sm.settings = self.sm.defaults.copy()
        self.sm.requiredFormatKeys = {
            "fooFormat": ["foo", "bar"],
            "barFormat": ["baz", "qux"],
        }
        self.sm._validateFormatStrings()
        self.assertEqual(self.sm.settings, self.sm.defaults)

    def test_invalid(self):
        self.sm.defaults = {"fooFormat": "{foo} {bar}", "barFormat": "{baz} {qux}"}
        invalidSettings = {"fooFormat": "{baz} {qux}", "barFormat": "{foo} {bar}"}
        self.sm.settings = invalidSettings
        self.sm.requiredFormatKeys = {
            "fooFormat": ["foo", "bar"],
            "barFormat": ["baz", "qux"],
        }
        self.sm._validateFormatStrings()
        self.assertEqual(self.sm.settings, self.sm.defaults)


class ValidFormatTests(SettingsTests):
    def test_valid(self):
        self.sm.requiredFormatKeys = {"test": ["foo", "bar", "baz"]}
        self.assertTrue(self.sm.validFormat("test", "{foo} {bar} {baz}"))

    def test_invalid(self):
        self.sm.requiredFormatKeys = {"test": ["foo", "bar", "baz"]}
        self.assertFalse(self.sm.validFormat("test", "{foo} {baz}"))
