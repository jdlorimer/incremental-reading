## Introduction

This is my fork of the [Incremental Reading Extension and View Size Adjust Add-on](https://github.com/aleksejrs/anki-2.0-vsa-and-ire). The originals have long been removed from AnkiWeb, so their descriptions are no longer available there. I have begun the process of merging these two add-ons, and will refer to them simply as the Incremental Reading add-on.

The purpose of this add-on is to provide features that support [incremental reading](http://www.supermemo.com/help/read.htm) in Anki. The SuperMemo article is only slightly relevant, but will give an idea what the overall aim is.

## Features

The main things this add-on allows you to do:

* Maintain scroll position and zoom on a per-card basis
* Extract selected text into a new card by pressing 'x'
* Highlight selected text by pressing 'h'
* Create custom shortcuts to quickly add cards
* Control the scheduling of incremental reading cards
* Rearrange cards in the built-in organiser

## Installation

You will first need to have Anki installed. Download the relevant installer [here](http://ankisrs.net).

Once Anki is installed, copy the following files into your add-ons folder:

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

## Version History

### v3.2.8

#### Features

- The following options have been added to give more control over how text is extracted:
  - Open the full note editor for each extraction (slow), or simply a title entry box (fast)
  - Extract selected text as HTML (retain color and formatting) or plain text (remove all formatting)
  - Open the source note for editing on each extraction

- It is also now possible to control several aspects of how zooming operates:
  - **Zoom Step** (the amount that magnification changes when zooming in or out)
  - **General Zoom** (the zoom level for the deck browser and overview screens)

- All settings have been merged into a single JSON file for easier editing and debugging

#### Bugfixes

- Highlighting now causes fewer issues; saves only relevant part of page to note
- Zoom factor and scroll position are now saved, and restored, more reliably
- Fixed bug where switching between profiles resulted in duplicate menu items
- Fixed formatting of IR menu items, so they now blend better with standard Anki items
- IR menu items are now located under the "Read" menu, rather than spread throughout other menus
