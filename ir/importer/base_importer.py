from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from anki.notes import Note
from aqt import mw
from aqt.utils import chooseList, showCritical, showWarning, tooltip

from ir.settings import SettingsManager
from ir.util import Article, setField

from .exceptions import ErrorLevel, ImporterError
from .models import NoteModel


class BaseImporter(ABC):
    def __init__(self, settings: SettingsManager):
        self.settings = settings

    def importContent(self) -> None:
        """Template method that defines the import algorithm"""
        try:
            articles = self._getArticles()
            selected = self._selectArticles(articles)
            if not selected:
                return

            priority = self._getPriority() if self.settings["prioEnabled"] else None
            mw.progress.start(
                label=self._getProgressLabel(), max=len(selected), immediate=True
            )

            deckName = None
            for i, article in enumerate(selected, start=1):
                noteModel = self._processArticle(article, priority)
                deckName = self._createNote(noteModel)
                self._postProcessArticle(article)
                mw.progress.update(value=i)

            mw.progress.finish()

            tooltip(f"Added {len(selected)} item(s) to deck: {deckName}")

            return

        except ImporterError as e:
            self._handleError(e)
            return

    @abstractmethod
    def _getArticles(self) -> List[Article]:
        """Get the articles to be imported"""
        pass

    @abstractmethod
    def _selectArticles(self, articles: List[Article]) -> List[Article]:
        """Select which articles to import. Can be overridden by subclasses."""
        pass

    @abstractmethod
    def _processArticle(self, article: Article, priority: Optional[str]) -> NoteModel:
        """Process a single article"""
        pass

    def _postProcessArticle(self, article: Article) -> None:
        """Post-process a single article"""
        pass

    @abstractmethod
    def _getProgressLabel(self) -> str:
        """Get the progress label for the import operation"""
        pass

    def _getPriority(self) -> str:
        prompt = "Select priority for import"
        return self.settings["priorities"][
            chooseList(prompt, self.settings["priorities"])
        ]

    def _createNote(self, noteModel: NoteModel) -> str:
        """Create a note from a NoteModel"""
        if self.settings["importDeck"]:
            deck = mw.col.decks.by_name(self.settings["importDeck"])
            if not deck:
                showWarning(
                    f'Destination deck "{deck}" no longer exists. Please update your settings.'
                )
                return ""
            deckId = deck["id"]
        else:
            deckId = mw.col.conf["curDeck"]

        model = mw.col.models.by_name(self.settings["modelName"])
        note = Note(mw.col, model)
        setField(note, self.settings["titleField"], noteModel.title)
        setField(note, self.settings["textField"], noteModel.content)

        source = self.settings["sourceFormat"].format(
            date=date.today(), url=f'<a href="{noteModel.url}">{noteModel.url}</a>'
        )
        setField(note, self.settings["sourceField"], source)
        if noteModel.priority:
            setField(note, self.settings["prioField"], noteModel.priority)

        note.note_type()["did"] = deckId
        mw.col.addNote(note)

        return mw.col.decks.get(deckId)["name"]

    def _handleError(self, error: ImporterError) -> None:
        """Handle import errors"""
        if error.errorLevel == ErrorLevel.CRITICAL:
            showCritical(error.message)
        elif error.errorLevel == ErrorLevel.WARNING:
            showWarning(error.message)
