## Introduction

This is an updated version of the [Incremental Reading add-on](https://github.com/aleksejrs/anki-2.0-vsa-and-ire), which aims to provide features that support incremental reading in Anki. The <a href="https://www.supermemo.com/help/read.htm" rel="nofollow">SuperMemo help article on the subject</a> is interesting, but the implementation here is quite different. Read it to get a general overview of the concept.

I am not the original author of this add-on, but I've used the previous version long enough, and seriously enough, to have made substantial changes. Some of those changes might be of general interest, so I am gradually releasing them as version 3. All credit for the basic idea belongs to others.

## Features

The main things this add-on allows you to do:

* Maintain scroll position and zoom on a per-card basis
* Extract selected text into a new card by pressing 'x'
* Highlight selected text by pressing 'h'
* Remove selected text by pressing 'r'
* Create custom shortcuts to quickly add cards
* Control the scheduling of incremental reading cards
* Rearrange cards in the built-in organiser

### New to Version 3

#### Features

* All existing options have been consolidated into a single tabbed dialog, and several new ones added
* Remove uninteresting/junk text from note with a single key-press
* New options to control how text is extracted:
    * Open the full note editor for each extraction (slow), or simply a title entry box (fast)
    * Extract selected text as HTML (retain color and formatting) or plain text (remove all formatting)
    * Choose a destination deck for extracts
* New options for several aspects of zoom and scroll functionality:
    * _Zoom Step_ (the amount that magnification changes when zooming in or out)
    * _General Zoom_ (the zoom level for the deck browser and overview screens)
    * _Line Step_ (the amount the page moves up or down when the Up or Down direction keys are used)
    * _Page Step_ (same as above, but with the Page Up and Page Down keys)
* Highlighting:
    * Both the background color and text color used for highlighting can be customized
    * A drop-down list of available colors is provided
    * A preview is now displayed when selecting highlight colors
    * The colors applied to text extracted with 'x' can now be set independently
* Quick Keys
    * A list of all existing Quick Keys is now shown, to allow easy modification
    * Unwanted Quick Keys can be easily deleted
    * A plain text extraction option has also been added

#### Bugfixes

* Highlighting now causes fewer issues; saves only relevant part of page to note
* Zoom factor and scroll position are now saved, and restored, more reliably
* Fixed serious issue where, under certain conditions, the add-on would alter the scheduling of regular Anki cards
* Fixed a bug where switching between profiles resulted in duplicate menu items
* Fixed a bug that prevented editing of the source note unless also editing the extracted note

## Installation

You will first need to have Anki installed. Download the relevant installer [here](http://ankisrs.net).

Once Anki is installed, go to Tools -> Add-ons -> Browse & Install, then enter the code 1081195335

To install manually, copy the following files into your add-ons folder:

* ir
* ir_addons.py

If you are unsure where the add-ons folder is located, go to Tools -> Add-ons -> Open Add-ons Folder.

## Compatibility

This fork of the Incremental Reading add-on is incompatible with previous versions in two respects.

First, settings were previously stored in two separate files, one for View Size Adjust and one for Incremental Reading Extension. All settings are now stored together in one file, and the format has changed. This means that any previous settings will be lost.

Second, to accommodate changes to how highlighting works, a slight change to the card template was needed. Given that this fork already breaks backwards compatibility, the template was modified and the model renamed. If you already have incremental reading notes from a previous version, you will need to select them in the card browser and choose Edit -> Change Note Type, and convert them to IR3 notes. They will now be recognised by the add-on.

If you have the following files in your media directory, you can safely delete them:

* \_IncrementalReadingExtension.dat
* \_ViewSizeAdjustAddon.dat

## Support

If any issues are encountered, please post details to the [Anki add-ons forum](https://anki.tenderapp.com/discussions/add-ons). If you create a new topic, be sure to mention Incremental Reading in the title.

Alternatively, feel free to [note an issue](https://github.com/luoliyan/incremental-reading-for-anki/issues) on GitHub. Pull requests are also welcome.

## License

Multiple people have contributed to this add-on, and it's slightly unclear who to credit for which changes, and what licenses to apply.

Tiago Barroso appears to be the one who started the project, and he has [stated](https://groups.google.com/d/msg/anki-addons/xibqDVFqQwQ/-qpxKvxurPMJ) that he releases all of his add-ons under the ISC license.

Frank Kmiec was responsible for vastly expanding the add-on, but it's not clear what license his changes were released under. Presuming he didn't specify one, the [terms and conditions of AnkiWeb](https://ankiweb.net/account/terms) would mean they were automatically released under the AGPL v3.

Aleksej's changes to Frank's version are ["multi-licensed under the same ISC license, GNU LGPL v3+, GNU GPL v3+ and GNU AGPL v3+"](https://github.com/aleksejrs/anki-2.0-vsa-and-ire).

For the sake of simplicity, I am also releasing my changes under the ISC license (a copy of which can be found in this repository). For each author, I have placed a copyright line in the license with what I believe are correct dates. If I have made a mistake in this regard, please let me know.

I have also removed the manual that is still available in Aleksej's fork, mainly because it is becoming less relevant, but also because it is a Google Groups conversation, which makes the licensing slightly murky.

Frank Raiser released an Anki 1 add-on under a similar name, but it doesn't appear to share any code with the current project and the functionality is quite different. For more information, see [Anki Incremental Reading](http://frankraiser.de/drupal/AnkiIR).
