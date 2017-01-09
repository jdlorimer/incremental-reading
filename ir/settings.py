import codecs
import json
import os

import aqt

import ir.util


class SettingsManager():
    def getSettings(self):
        self.mediaDir = os.path.join(aqt.mw.pm.profileFolder(),
                                     'collection.media')
        self.jsonPath = os.path.join(self.mediaDir, '_ir.json')

        if os.path.isfile(self.jsonPath):
            with codecs.open(self.jsonPath, encoding='utf-8') as jsonFile:
                return json.load(jsonFile)
        else:
            return {'doHighlightFont': 'false',
                    'highlightColor': 'yellow',
                    'schedLaterInt': 50,
                    'schedLaterRandom': True,
                    'schedLaterType': 'pct',
                    'schedSoonInt': 10,
                    'schedSoonRandom': True,
                    'schedSoonType': 'pct',
                    'zoomAndScroll': {}}

    def saveSettings(self, settings):
        with codecs.open(self.jsonPath, 'w', encoding='utf-8') as jsonFile:
            json.dump(settings, jsonFile)

        # Touch the media folder to force sync
        ir.util.updateModificationTime(self.mediaDir)
