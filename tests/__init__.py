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
        patch.dict('sys.modules', modules).start()
        pf_mock = MagicMock(return_value=str())
        if_mock = MagicMock(return_value=True)
        patch('ir.settings.json.load', MagicMock()).start()
        patch('ir.settings.mw.pm.profileFolder', pf_mock).start()
        patch('ir.settings.open', mock_open()).start()
        patch('ir.settings.os.path.isfile', if_mock).start()
        from ir.settings import SettingsManager
        self.sm = SettingsManager()

    def tearDown(self):
        patch.stopall()
