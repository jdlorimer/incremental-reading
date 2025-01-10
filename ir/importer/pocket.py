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

from json.decoder import JSONDecodeError
from typing import List
from urllib.parse import urlencode

from anki.utils import is_mac, is_win
from aqt.utils import askUser, openLink, showCritical, showInfo
from requests import post

from ir.util import Article


class Pocket:
    _accessToken = None
    _redirectURI = "https://github.com/luoliyan/incremental-reading"
    _headers = {"X-Accept": "application/json"}

    if is_win:
        consumerKey = "71462-da4f02100e7e381cbc4a86df"
    elif is_mac:
        consumerKey = "71462-ed224e5a561a545814023bf9"
    else:
        consumerKey = "71462-05fb63bf0314903c7e73c52f"

    def getArticles(self) -> List[Article]:
        if not self._accessToken:
            self._accessToken = self._authenticate()

        if not self._accessToken:
            showCritical("Authentication failed.")
            return []

        response = post(
            "https://getpocket.com/v3/get",
            json={
                "consumer_key": self.consumerKey,
                "access_token": self._accessToken,
                "contentType": "article",
                "count": 30,
                "detailType": "complete",
                "sort": "newest",
            },
            headers=self._headers,
        )

        if response.json()["list"]:
            return [
                Article(title=a["resolved_title"], data=a)
                for a in response.json()["list"].values()
            ]

        showInfo("You have no unread articles remaining.")
        return []

    def _authenticate(self):
        response = post(
            "https://getpocket.com/v3/oauth/request",
            json={
                "consumer_key": self.consumerKey,
                "redirect_uri": self._redirectURI,
            },
            headers=self._headers,
        )

        requestToken = response.json()["code"]

        authUrl = "https://getpocket.com/auth/authorize?"
        authParams = {
            "request_token": requestToken,
            "redirect_uri": self._redirectURI,
        }

        openLink(authUrl + urlencode(authParams))
        if not askUser("I have authenticated with Pocket."):
            return None

        response = post(
            "https://getpocket.com/v3/oauth/authorize",
            json={"consumer_key": self.consumerKey, "code": requestToken},
            headers=self._headers,
        )

        try:
            return response.json()["access_token"]
        except JSONDecodeError:
            return None

    def archive(self, article: Article) -> None:
        post(
            "https://getpocket.com/v3/send",
            json={
                "consumer_key": self.consumerKey,
                "access_token": self._accessToken,
                "actions": [{"action": "archive", "item_id": article.data["item_id"]}],
            },
        )
