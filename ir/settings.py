import codecs
import json
import os

import aqt

import ir.util


class SettingsManager():
    def __init__(self):
        self.loadSettings()

    def loadSettings(self):
        self.mediaDir = os.path.join(aqt.mw.pm.profileFolder(),
                                     'collection.media')
        self.jsonPath = os.path.join(self.mediaDir, '_ir.json')

        if os.path.isfile(self.jsonPath):
            with codecs.open(self.jsonPath, encoding='utf-8') as jsonFile:
                self.settings = json.load(jsonFile)
        else:
            self.settings = {'doHighlightFont': 'false',
                             'highlightColor': 'yellow',
                             'lastDialogQuickKey': {},
                             'quickKeys': {},
                             'schedLaterInt': 50,
                             'schedLaterRandom': True,
                             'schedLaterType': 'pct',
                             'schedSoonInt': 10,
                             'schedSoonRandom': True,
                             'schedSoonType': 'pct',
                             'scroll': {},
                             'textSizeMultiplier': 1,
                             'zoom': {},
                             'zoomStep': 0.1}

    def saveSettings(self):
        with codecs.open(self.jsonPath, 'w', encoding='utf-8') as jsonFile:
            json.dump(self.settings, jsonFile)

        # Touch the media folder to force sync
        ir.util.updateModificationTime(self.mediaDir)
