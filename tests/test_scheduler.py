from unittest import TestCase
from unittest.mock import MagicMock, patch


class SchedulerTests(TestCase):
    def setUp(self):
        modules = {
            'PyQt5': MagicMock(),
            'PyQt5.QtCore': MagicMock(),
            'PyQt5.QtWidgets': MagicMock(),
            'anki': MagicMock(),
            'anki.hooks': MagicMock(),
            'anki.notes': MagicMock(),
            'anki.utils': MagicMock(),
            'aqt': MagicMock(),
            'aqt.addcards': MagicMock(),
            'aqt.browser': MagicMock(),
            'aqt.editcurrent': MagicMock(),
            'aqt.reviewer': MagicMock(),
            'aqt.tagedit': MagicMock(),
            'aqt.utils': MagicMock(),
            'ir.main': MagicMock(),
        }
        self.patcher = patch.dict('sys.modules', modules)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_scheduler(self):
        from ir.schedule import Scheduler
        Scheduler()
