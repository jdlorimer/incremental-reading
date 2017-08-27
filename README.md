**Note: The version of the add-on in this branch has been modified to work with Anki 2.1. It is not backwards-compatible with previous versions of Anki. If you are using an older version of Anki 2, please download the legacy branch [here](https://github.com/luoliyan/incremental-reading-for-anki/archive/legacy.zip).**

**Note: Currently, scroll position is not being restored when a card is loaded. This is a known issue, and is due to a change in the more recent Anki 2.1 betas. This will be addressed in the future.**

## Introduction

This is an updated version of the [Incremental Reading add-on](https://github.com/aleksejrs/anki-2.0-vsa-and-ire), which aims to provide features that support incremental reading in Anki. The idea of working with long-form content within a spaced-repetition program appears to have originated with SuperMemo, which offers an elaborate implementation of the technique (see their [help article](https://www.supermemo.com/help/read.htm) for more information). This add-on for Anki is comparatively bare-bones, providing a minimal set of tools for iterating over long texts and creating new flashcards from existing ones. For an overview of these features, see below.

## Features

The main things this add-on allows you to do:

* Import content from web feeds (RSS, atom, etc.) or webpages
* Extract selected text into a new card by pressing <kbd>x</kbd>
* Highlight selected text by pressing <kbd>h</kbd>
* Remove selected text by pressing <kbd>r</kbd>
* Create custom shortcuts to quickly add cards
* Maintain scroll position and zoom on a per-card basis
* Rearrange cards in the built-in organiser
* Control the scheduling of incremental reading cards

### New to Version 4

#### Features

* Compatible with Anki 2.1
* Automatically import a single webpage into a new Anki card (<kbd>Alt</kbd>+<kbd>3</kbd>)
* Automatically import a web feed into multiple new Anki cards (<kbd>Alt</kbd>+<kbd>4</kbd>)

### New to Version 3

#### Features

* Remove unwanted text from note with a single key-press
* New options to control how text is extracted:
    * Open the full note editor for each extraction (slow), or simply a title entry box (fast)
    * Extract selected text as HTML (retain color and formatting) or plain text (remove all formatting)
    * Choose a destination deck for extracts
* New options for several aspects of zoom and scroll functionality:
    * _Zoom Step_ (the amount that magnification changes when zooming in or out)
    * _General Zoom_ (the zoom level for the deck browser and overview screens)
    * _Line Step_ (the amount the page moves up or down when the Up or Down direction keys are used)
    * _Page Step_ (same as above, but with the <kbd>Page Up</kbd> and <kbd>Page Down</kbd> keys)
* Highlighting:
    * Both the background color and text color used for highlighting can be customized
    * A drop-down list of available colors is provided
    * A preview is now displayed when selecting highlight colors
    * The colors applied to text extracted with <kbd>x</kbd> can now be set independently
* Quick Keys
    * A list of all existing Quick Keys is now shown, to allow easy modification
    * Unwanted Quick Keys can be easily deleted
    * A plain text extraction option has also been added
* All existing options have been consolidated into a single tabbed dialog, and several new ones added

#### Bugfixes

* Highlighting now causes fewer issues; saves only relevant part of page to note
* Zoom factor and scroll position are now saved, and restored, more reliably
* Fixed serious issue where, under certain conditions, the add-on would alter the scheduling of regular Anki cards
* Fixed a bug where switching between profiles resulted in duplicate menu items
* Fixed a bug that prevented editing of the source note unless also editing the extracted note

## Installation

You will first need to have Anki installed. Download the relevant installer [here](http://ankisrs.net).

At present, v4 cannot be installed via AnkiWeb, since a separate section for Anki 2.1 add-ons has yet to be created. To install manually, download the GitHub repository ([here](https://github.com/luoliyan/incremental-reading-for-anki/archive/master.zip)) and extract the following files into your add-ons folder:

* `ir`
* `ir_addons.py`

If you are unsure where the add-ons folder is located, go to Tools → Add-ons → Open Add-ons Folder.

## Compatibility

In general, the settings stored in `_ir.json` will be preserved when upgrading to newer versions of the add-on. The main exception to this rule is that v3 and v4 of the add-on are not backwards-compatible with v2. The newer versions store settings in a very different manner; as such, any v2 settings will be ignored.

Additionally, changes were made to the v2 card template, so if you have incremental reading notes from v2, you will need to select them in the card browser and choose Edit → Change Note Type, to convert them to IR3 notes.

## Support

If any issues are encountered, please post details to the [Anki add-ons forum](https://anki.tenderapp.com/discussions/add-ons). It is best if you post in the existing thread ([here](https://anki.tenderapp.com/discussions/add-ons/9054-incremental-reading-add-on-discussion-support)), since I will recieve a notification of that by e-mail. Alternatively, feel free to [note an issue](https://github.com/luoliyan/incremental-reading-for-anki/issues) on GitHub (where you can also make a pull request if you are so inclined).

Please include the following information in your post:
* The version of Anki you are using (e.g., v2.1.0-beta5)
* The version of IR you are using (this can be found in `ir/__init__.py`)
* The operating system you are using
* Details of the problem

I would also appreciate if you could try to replicate the problem with all other add-ons disabled.

## License

Multiple people have contributed to this add-on, and it's somewhat unclear who to credit for which changes, and which licenses to apply.

Tiago Barroso appears to be the person who began the project, and he has [stated](https://groups.google.com/d/msg/anki-addons/xibqDVFqQwQ/-qpxKvxurPMJ) that he releases all of his add-ons under the ISC license. Frank Kmiec was responsible for vastly expanding the add-on, but it's unclear which license his changes were released under. Presuming he didn't specify one, the [terms and conditions of AnkiWeb](https://ankiweb.net/account/terms) suggest they were automatically released under the AGPL v3. Aleksej's changes to Frank's version are ["multi-licensed under the same ISC license, GNU LGPL v3+, GNU GPL v3+ and GNU AGPL v3+"](https://github.com/aleksejrs/anki-2.0-vsa-and-ire).

For the sake of simplicity, I am also releasing my changes under the ISC license. For each author, I have placed a copyright line in the license with what I believe are correct dates. If I have made a mistake in this respect, please let me know. I have also removed the manual that is still available in Aleksej's fork, mainly because it is becoming less relevant, but also because it is a Google Groups conversation, which makes the licensing slightly murky.

Frank Raiser released an Anki 1 add-on under a similar name, but it doesn't appear to share any code with the current project and the functionality is quite different. For more information, see [Anki Incremental Reading](http://frankraiser.de/drupal/AnkiIR).
