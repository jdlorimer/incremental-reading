# Copyright 2017 Christian Weiß
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

from functools import partial
import json
import os

from anki.hooks import addHook
from aqt import mw
from aqt.utils import showInfo

from ._version import __version__
from .about import IR_GITHUB_URL
from .util import addMenuItem, setMenuVisibility, updateModificationTime


class SettingsManager:
    updated = False
    requiredFormatKeys = {
        'organizerFormat': ['info', 'title'],
        'sourceFormat': ['url', 'date'],
    }
    doNotUpdate = ['feedLog', 'modified', 'quickKeys', 'scroll', 'zoom']
    defaults = {
        'badTags': ['iframe', 'script'],
        'boldSeq': 'Ctrl+B',
        'copyTitle': False,
        'editExtract': False,
        'editSource': False,
        'extractBgColor': 'Green',
        'extractDeck': None,
        'extractKey': 'x',
        'extractMethod': 'percent',
        'extractRandom': True,
        'extractTextColor': 'White',
        'extractValue': 30,
        'feedLog': {},
        'generalZoom': 1,
        'highlightBgColor': 'Yellow',
        'highlightKey': 'h',
        'highlightTextColor': 'Black',
        'importDeck': None,
        'isQuickKey': False,
        'italicSeq': 'Ctrl+I',
        'laterMethod': 'percent',
        'laterRandom': True,
        'laterValue': 50,
        'limitWidth': True,
        'limitWidthAll': False,
        'lineScrollFactor': 0.05,
        'maxWidth': 600,
        'modelName': 'IR3',
        'modified': [],
        'organizerFormat': '❰ {info} ❱\t{title}',
        'overlaySeq': 'Ctrl+Shift+O',
        'pageScrollFactor': 0.5,
        'plainText': False,
        'pocketArchive': True,
        'prioDefault': '5',
        'prioEnabled': False,
        'prioField': 'Priority',
        'priorities': ['', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
        'quickKeys': {},
        'removeKey': 'z',
        'scheduleExtract': True,
        'scroll': {},
        'soonMethod': 'percent',
        'soonRandom': True,
        'soonValue': 10,
        'sourceField': 'Source',
        'sourceFormat': '{url} ({date})',
        'strikeSeq': 'Ctrl+S',
        'textField': 'Text',
        'titleField': 'Title',
        'underlineSeq': 'Ctrl+U',
        'undoKey': 'u',
        'userAgent': 'IR/{} (+{})'.format(__version__, IR_GITHUB_URL),
        'version': __version__,
        'zoom': {},
        'zoomStep': 0.1,
    }

    def __init__(self):
        addHook('unloadProfile', self._unload)
        self.load()

    def __setitem__(self, key, value):
        if (
            self.settings[key] != value
            and key not in self.settings['modified']
        ):
            self.settings['modified'].append(key)

        self.settings[key] = value

    def __getitem__(self, key):
        return self.settings[key]

    def load(self):
        if os.path.isfile(self.getSettingsPath()):
            self._loadExisting()
        else:
            self.settings = self.defaults

        if self.updated:
            showInfo('Your Incremental Reading settings have been updated.')

    def _loadExisting(self):
        with open(self.getSettingsPath(), encoding='utf-8') as jsonFile:
            self.settings = json.load(jsonFile)
        self._update()

    def getSettingsPath(self):
        return os.path.join(self.getMediaDir(), '_ir.json')

    def getMediaDir(self):
        return os.path.join(mw.pm.profileFolder(), 'collection.media')

    def _update(self):
        self.settings['version'] = self.defaults['version']
        self._addMissing()
        self._removeOutdated()
        self._updateUnmodified()
        self._validateFormatStrings()

    def _addMissing(self):
        for k, v in self.defaults.items():
            if k not in self.settings:
                self.settings[k] = v
                self.updated = True

    def _removeOutdated(self):
        required = [
            'alt',
            'ctrl',
            'editExtract',
            'editSource',
            'extractBgColor',
            'extractDeck',
            'extractTextColor',
            'isQuickKey',
            'modelName',
            'regularKey',
            'shift',
            'sourceField',
            'tags',
            'textField',
        ]

        for keyCombo, settings in self.settings['quickKeys'].copy().items():
            for k in required:
                if k not in settings:
                    self.settings['quickKeys'].pop(keyCombo)
                    self.updated = True
                    break

        outdated = [k for k in self.settings if k not in self.defaults]
        for k in outdated:
            self.settings.pop(k)
            self.updated = True

    def _updateUnmodified(self):
        for k in self.settings:
            if k in self.doNotUpdate:
                continue

            if k in self.settings['modified']:
                continue

            if self.settings[k] == self.defaults[k]:
                continue

            self.settings[k] = self.defaults[k]
            self.updated = True

    def _validateFormatStrings(self):
        for name in self.requiredFormatKeys:
            if not self.validFormat(name, self.settings[name]):
                self.settings[name] = self.defaults[name]

    def validFormat(self, name, fmt):
        for k in self.requiredFormatKeys[name]:
            if fmt.find('{%s}' % k) == -1:
                return False
        return True

    def _unload(self):
        for menu in mw.customMenus.values():
            mw.form.menubar.removeAction(menu.menuAction())

        mw.customMenus.clear()
        self.save()

    def save(self):
        with open(self.getSettingsPath(), 'w', encoding='utf-8') as jsonFile:
            json.dump(self.settings, jsonFile)

        updateModificationTime(self.getMediaDir())

    def loadMenuItems(self):
        path = 'Read::Quick Keys'

        if path in mw.customMenus:
            mw.customMenus[path].clear()

        for keyCombo, settings in self.settings['quickKeys'].items():
            text = 'Add Card [%s -> %s]' % (
                settings['modelName'],
                settings['extractDeck'],
            )
            func = partial(mw.readingManager.textManager.extract, settings)
            addMenuItem(path, text, func, keyCombo)

        setMenuVisibility(path)
