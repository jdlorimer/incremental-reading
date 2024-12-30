# Copyright 2013 Tiago Barroso
# Copyright 2013 Frank Kmiec
# Copyright 2013-2016 Aleksej
# Copyright 2018 Timothée Chauvin
# Copyright 2017-2019 Joseph Lorimer <joseph@lorimer.me>
#
# Permission to use, copy, modify, and distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright
# notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

from typing import Any, Sequence

from anki.cards import Card
from anki.hooks import addHook, wrap
from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.qt import sip
from aqt.reviewer import Reviewer

from .about import showAbout
from .gui import SettingsDialog
from .importer import Importer
from .schedule import Scheduler
from .settings import SettingsManager
from .text import TextManager
from .util import addMenuItem, isIrCard, loadFile
from .view import ViewManager


class ReadingManager:
    shortcuts = []

    def __init__(self):
        self.importer = Importer()
        self.scheduler = Scheduler()
        self.textManager = TextManager()
        self.viewManager = ViewManager()
        gui_hooks.profile_did_open.append(self.onProfileLoaded)
        gui_hooks.card_will_show.append(self.onPrepareQA)

        addHook("overviewStateShortcuts", self.setShortcuts)
        addHook("reviewStateShortcuts", self.setReviewShortcuts)

    def onProfileLoaded(self) -> None:
        self.settings = SettingsManager()
        mw.addonManager.setConfigAction(__name__, lambda: SettingsDialog(self.settings))
        self.importer.changeProfile(self.settings)
        self.scheduler.changeProfile(self.settings)
        self.textManager.changeProfile(self.settings)
        self.viewManager.changeProfile(self.settings)
        self.viewManager.resetZoom("deckBrowser")
        self.addModel()
        self.loadMenuItems()
        self.shortcuts = [
            (self.settings["extractKey"], self.textManager.extract),
            (self.settings["highlightKey"], self.textManager.highlight),
            (self.settings["removeKey"], self.textManager.remove),
            (self.settings["undoKey"], self.textManager.undo),
            (self.settings["overlaySeq"], self.textManager.toggleOverlay),
            (
                self.settings["boldSeq"],
                lambda: self.textManager.format("bold"),
            ),
            (
                self.settings["italicSeq"],
                lambda: self.textManager.format("italic"),
            ),
            (
                self.settings["strikeSeq"],
                lambda: self.textManager.format("strike"),
            ),
            (
                self.settings["underlineSeq"],
                lambda: self.textManager.format("underline"),
            ),
        ]

    def loadMenuItems(self):
        if hasattr(mw, "customMenus") and "Read" in mw.customMenus:
            mw.customMenus["Read"].clear()

        addMenuItem(
            "Read",
            "Options...",
            lambda: SettingsDialog(self.settings),
            "Alt+1",
        )
        addMenuItem("Read", "Organizer...", self.scheduler.showDialog, "Alt+2")
        addMenuItem("Read", "Import Webpage", self.importer.importWebpage, "Alt+3")
        addMenuItem("Read", "Import Feed", self.importer.importFeed, "Alt+4")
        addMenuItem("Read", "Import Pocket", self.importer.importPocket, "Alt+5")
        addMenuItem("Read", "Import Epub", self.importer.importEpub, "Alt+6")
        addMenuItem("Read", "Zoom In", self.viewManager.zoomIn, "Ctrl++")
        addMenuItem("Read", "Zoom Out", self.viewManager.zoomOut, "Ctrl+-")
        addMenuItem("Read", "About...", showAbout)

        self.settings.loadMenuItems()

    def onPrepareQA(self, text: str, card: Card, kind: str) -> str:
        if self.settings["prioEnabled"]:
            answerShortcuts = ["1", "2", "3", "4"]
        else:
            answerShortcuts = ["4"]

        activeAnswerShortcuts = [
            next((s for s in mw.stateShortcuts if s.key().toString() == i), None)
            for i in answerShortcuts
        ]

        if isIrCard(card):
            for shortcut in activeAnswerShortcuts:
                if shortcut:
                    mw.stateShortcuts.remove(shortcut)
                    sip.delete(shortcut)
        else:
            for shortcut in answerShortcuts:
                if not activeAnswerShortcuts[answerShortcuts.index(shortcut)]:
                    mw.stateShortcuts += mw.applyShortcuts(
                        [
                            (
                                shortcut,
                                lambda: mw.reviewer._answerCard(int(shortcut)),
                            )
                        ]
                    )

        return text

    def setShortcuts(self, shortcuts) -> None:
        shortcuts.append(("Ctrl+=", self.viewManager.zoomIn))

    def setReviewShortcuts(self, shortcuts) -> None:
        self.setShortcuts(shortcuts)
        shortcuts.extend(self.shortcuts)

    def addModel(self) -> None:
        if mw.col.models.by_name(self.settings["modelName"]):
            return

        model = mw.col.models.new(self.settings["modelName"])
        model["css"] = loadFile("web", "model.css")

        titleField = mw.col.models.new_field(self.settings["titleField"])
        textField = mw.col.models.new_field(self.settings["textField"])
        sourceField = mw.col.models.new_field(self.settings["sourceField"])
        sourceField["sticky"] = True

        mw.col.models.add_field(model, titleField)
        if self.settings["prioEnabled"]:
            prioField = mw.col.models.new_field(self.settings["prioField"])
            mw.col.models.add_field(model, prioField)

        mw.col.models.add_field(model, textField)
        mw.col.models.add_field(model, sourceField)

        template = mw.col.models.new_template("IR Card")
        template["qfmt"] = "\n".join(
            [
                '<div class="ir-title">{{%s}}</div>' % self.settings["titleField"],
                '<div class="ir-text">{{%s}}</div>' % self.settings["textField"],
                '<div class="ir-src">{{%s}}</div>' % self.settings["sourceField"],
                '<div class="ir-tags">{{Tags}}</div>',
            ]
        )

        if self.settings["prioEnabled"]:
            template["afmt"] = "Hit space to move to the next article"
        else:
            template["afmt"] = "When do you want to see this card again?"

        mw.col.models.add_template(model, template)
        mw.col.models.add(model)


def answerButtonList(self, _old: Any) -> tuple[tuple[int, str], ...]:
    if isIrCard(self.card):
        if mw.readingManager.settings["prioEnabled"]:
            return ((1, "Next"),)
        return ((1, "Soon"), (2, "Later"), (3, "Custom"))

    return _old(self)


def answerCard(self, ease: int, _old: Any):
    card = self.card
    _old(self, ease)
    if isIrCard(card):
        mw.readingManager.scheduler.answer(card, ease)


def buttonTime(self, i: int, v3_labels: Sequence[str], _old: Any) -> str:
    if isIrCard(mw.reviewer.card):
        return "<div class=spacer></div>"
    return _old(self, i, v3_labels)


def onBrowserClosed(self) -> None:
    try:
        mw.readingManager.scheduler._updateListItems()
    except:
        return


Reviewer._answerButtonList = wrap(
    Reviewer._answerButtonList, answerButtonList, "around"
)
Reviewer._answerCard = wrap(Reviewer._answerCard, answerCard, "around")
Reviewer._buttonTime = wrap(Reviewer._buttonTime, buttonTime, "around")
Browser._closeWindow = wrap(Browser._closeWindow, onBrowserClosed)
