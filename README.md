##  [View Size Adjust and Incremental Reading Extension](https://github.com/aleksejrs/anki-2.0-vsa-and-ire)

These are Aleksej's changes for Anki 2 add-ons by Frank.
The source code was taken from AnkiWeb (links not working now): [Incremental Reading Extension](https://ankiweb.net/shared/info/2880922486) and [View Size Adjust](https://ankiweb.net/shared/info/3136737107).

## What are these for

View Size Adjust lets you change the font size easily using Ctrl++ and
Ctrl+-.  It also provides some of the features necessary for the other addon.

Incremental Reading Extension is for
[incremental reading](http://www.supermemo.com/help/read.htm).  See
"Usage" below for details.

## License

“Incremental Reading Extension” is based on “Incremental Reading”
by Tiago Barroso (tmbb). There is no license specified for any of
the add-ons; Tiago agreed to add a license, saying also “You can
consider all my addons released with this license
https://en.wikipedia.org/wiki/ISC_license, copyright to Tiago
Barroso.” in [this message](https://groups.google.com/d/msg/anki-
addons/xibqDVFqQwQ/-qpxKvxurPMJ).

Consider my changes to these 2 add-ons multi-licensed under the
same ISC license, GNU LGPL v3+, GNU GPL v3+ and GNU AGPL v3+.

The licensing does not apply to the Google Groups page just because
I copied it here.

## Installation

The .py files are to be put into the addons/ folder in the Anki
folder.  See <http://ankisrs.net/docs/manual.html#file-locations>
for details on where the Anki folder is.

### Important

If you are switching to these versions from Frank's versions
(mentioned above, they are probably the only other versions with
these names), rename the .dat files in the collection.media/
directory in your Anki profile by prepending “_” as follows:

* _IncrementalReadingExtension.dat

* _ViewSizeAdjustAddon.dat

## Usage

Please see the html file saved from Google Groups for the original
manual (find a link to the source code near the top of here if you
are not reading this file as a part of the source code).


Suggestions on use of IRE that I haven't found in the
manual:

1. Do not press "Show answer" on IRead2 cards.  Instead, just
press 1 or 2.  This way you can change the queue position of
the card without affecting statistics, and if you don't like the
randomly chosen position, you can try again by pressing 1 or 2
again.

2. If you follow the above suggestion, you can put the IR deck
in one subtree with your normal spaced repetition decks.  For
example, I have a root deck which contains a SR subtree and
after it, the IR deck:

    * root deck

        * spaced repetition decks
        * incremental reading deck

    The incremental reading cards appear between reviews, after
    I view all the new cards, and with a frequency depending on
    the daily new card limits.


## Changelog

* 2014-04-21:

     Commented "import pyqtconfig" out, as it is unused. That's needed for compatibility with Qt5.

* 2013-04:

    Hide .dat files from unused media check by adding "_".

    Fix Organizer not opening if titles have non-ASCII.
