from unittest import TestCase
from unittest.mock import MagicMock, patch


class SchedulerTests(TestCase):
    def setUp(self):
        modules = {
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
        }
        self.patcher = patch.dict('sys.modules', modules)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_scheduler(self):
        from ir.schedule import Scheduler
        Scheduler()
