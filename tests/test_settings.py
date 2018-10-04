from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch


class SettingsTests(TestCase):
    def setUp(self):
        modules = {
            'anki.hooks': MagicMock(),
            'aqt': MagicMock(),
            'aqt.utils': MagicMock(),
            'ir.about': MagicMock(),
            'ir.main': MagicMock(),
            'ir.util': MagicMock(),
        }
        self.patcher = patch.dict('sys.modules', modules)
        self.patcher.start()
        from ir.settings import SettingsManager
        self.sm = SettingsManager

    def tearDown(self):
        self.patcher.stop()

    def test_settings(self):
        pf_mock = MagicMock(return_value=str())
        if_mock = MagicMock(return_value=True)
        patch('aqt.mw.pm.profileFolder', pf_mock).start()
        patch('os.path.isfile', if_mock).start()
        patch('ir.settings.open', mock_open()).start()
        patch('json.load', MagicMock()).start()
        self.sm()
        patch.stopall()
