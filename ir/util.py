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

import os
import re
import stat
import time
from dataclasses import dataclass
from typing import Any, List
from urllib.parse import unquote

from anki.cards import Card

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QKeySequence
except ModuleNotFoundError:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QKeySequence

from aqt import dialogs, mw
from aqt.qt import (
    QAbstractItemView,
    QAction,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QSpinBox,
    QVBoxLayout,
)
from bs4 import BeautifulSoup


@dataclass
class Article:
    title: str
    data: Any


def isIrCard(card: Card) -> bool:
    return card and (
        card.note_type()["name"] == mw.readingManager.settings["modelName"]
    )


def viewingIrText():
    return (
        isIrCard(mw.reviewer.card)
        and (mw.reviewer.state == "question")
        and (mw.state == "review")
    )


def addMenu(fullPath: str):
    # FIXME: Subpath doesn't work as quick keys don't show up
    if not hasattr(mw, "customMenus"):
        mw.customMenus = {}

    if len(fullPath.split("::")) == 2:
        menuPath, submenuPath = fullPath.split("::")
        hasSubmenu = True
    else:
        menuPath = fullPath
        hasSubmenu = False

    if menuPath not in mw.customMenus:
        menu = QMenu("&" + menuPath, mw)
        mw.customMenus[menuPath] = menu
        mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(), menu)

    if hasSubmenu and (fullPath not in mw.customMenus):
        submenu = QMenu("&" + submenuPath, mw)
        mw.customMenus[fullPath] = submenu
        mw.customMenus[menuPath].addMenu(submenu)


def setMenuVisibility(path):
    if path not in mw.customMenus:
        return

    if mw.customMenus[path].isEmpty():
        mw.customMenus[path].menuAction().setVisible(False)
    else:
        mw.customMenus[path].menuAction().setVisible(True)


def addMenuItem(path: str, text: str, function, keys=None):
    action = QAction(text, mw)

    if keys:
        action.setShortcut(QKeySequence(keys))

    # Override surprising behavior in OSX
    # https://doc.qt.io/qt-6/qmenubar.html#qmenubar-as-a-global-menu-bar
    if _hasSpecialOsxMenuKeywords(text):
        action.setMenuRole(QAction.MenuRole.NoRole)

    action.triggered.connect(function)

    menu = None
    if path == "File":
        menu = mw.form.menuCol
    elif path == "Edit":
        menu = mw.form.menuEdit
    elif path == "Tools":
        menu = mw.form.menuTools
    elif path == "Help":
        menu = mw.form.menuHelp
    else:
        addMenu(path)
        menu = mw.customMenus[path]

    menu.addAction(action)


def _hasSpecialOsxMenuKeywords(text: str):
    """Checks if a string contains any of the specified keywords.
    Args:
        text: The string to check.

    Returns:
        True if any keyword is found, False otherwise.
    """
    keywords = r"about|config|options|setup|settings|preferences|quit|exit"
    return bool(re.search(keywords, text, re.IGNORECASE))


def getField(note, fieldName):
    model = note.note_type()
    index, _ = mw.col.models.field_map(model)[fieldName]
    return note.fields[index]


def setField(note, field, value):
    """Set the value of a note field. Overwrite any existing value."""
    model = note.note_type()
    index, _ = mw.col.models.field_map(model)[field]
    note.fields[index] = value


def getFieldNames(modelName):
    """Return list of field names for given model name."""
    if not modelName:
        return []
    return mw.col.models.field_names(mw.col.models.by_name(modelName))


def createSpinBox(value, minimum, maximum, step):
    spinBox = QSpinBox()
    spinBox.setRange(minimum, maximum)
    spinBox.setSingleStep(step)
    spinBox.setValue(value)
    return spinBox


def setComboBoxItem(comboBox, text):
    index = comboBox.findText(text, Qt.MatchFlag.MatchFixedString)
    comboBox.setCurrentIndex(index)


def removeComboBoxItem(comboBox, text):
    index = comboBox.findText(text, Qt.MatchFlag.MatchFixedString)
    comboBox.removeItem(index)


def updateModificationTime(path):
    accessTime = os.stat(path)[stat.ST_ATIME]
    modificationTime = time.time()
    os.utime(path, (accessTime, modificationTime))


def fixImages(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        img["src"] = os.path.basename(unquote(img["src"]))
    return str(soup)


def loadFile(fileDir, filename):
    moduleDir, _ = os.path.split(__file__)
    path = os.path.join(moduleDir, fileDir, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


def getColorList():
    moduleDir, _ = os.path.split(__file__)
    colorsFilePath = os.path.join(moduleDir, "data", "colors.u8")
    with open(colorsFilePath, encoding="utf-8") as colorsFile:
        return [line.strip() for line in colorsFile]


def showBrowser(nid):
    browser = dialogs.open("Browser", mw)
    browser.form.searchEdit.lineEdit().setText("nid:" + str(nid))
    browser.onSearchActivated()


def selectArticles(articles: List[Article]) -> List[Article]:
    """Select which articles to import using a dialog.

    Args:
        choices: List of Article objects to select from

    Returns:
        List of selected articles
    """
    if not articles:
        return []

    dialog = QDialog(mw)
    layout = QVBoxLayout()

    textWidget = QLabel()
    textWidget.setText("Select articles to import: ")

    listWidget = QListWidget()
    listWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    for article in articles:
        item = QListWidgetItem(article.title)
        item.setData(Qt.ItemDataRole.UserRole, article)
        listWidget.addItem(item)

    buttonBox = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Close | QDialogButtonBox.StandardButton.SaveAll
    )
    buttonBox.accepted.connect(dialog.accept)
    buttonBox.rejected.connect(dialog.reject)
    buttonBox.setOrientation(Qt.Orientation.Horizontal)

    layout.addWidget(textWidget)
    layout.addWidget(listWidget)
    layout.addWidget(buttonBox)

    dialog.setLayout(layout)
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.resize(500, 500)
    choice = dialog.exec()

    if choice == 1:
        res = [
            item.data(Qt.ItemDataRole.UserRole) for item in listWidget.selectedItems()
        ]
        return res
    return []
