# Incremental Reading for Anki

[![Build Status](https://travis-ci.org/luoliyan/incremental-reading.svg?branch=master)](https://travis-ci.org/luoliyan/incremental-reading)

**Note:** Version 4 of the add-on is only available for Anki 2.1+. Some features will be missing from the earlier versions.

## Introduction

This is a rewrite of the [Incremental Reading add-on](https://github.com/aleksejrs/anki-2.0-vsa-and-ire), which aims to provide features that support incremental reading in Anki. The idea of working with long-form content within a spaced-repetition program appears to have originated with SuperMemo, which offers an elaborate implementation of the technique (see their [help article](https://www.supermemo.com/help/read.htm) for more information). This add-on for Anki is comparatively bare-bones, providing a minimal set of tools for iterating over long texts and creating new flashcards from existing ones. For an overview of these features, see below.

- Version 4: [GitHub](https://github.com/luoliyan/incremental-reading), [issue tracker](https://github.com/luoliyan/incremental-reading/issues), [discussion board](https://anki.tenderapp.com/discussions/add-ons/9054-incremental-reading-add-on-discussion-support)
- Version 3: [GitHub](https://github.com/luoliyan/incremental-reading/tree/legacy), [discussion board](https://anki.tenderapp.com/discussions/add-ons/9054-incremental-reading-add-on-discussion-support)
- Version 2: [AnkiWeb](https://ankiweb.net/shared/info/355348508), [GitHub](https://github.com/aleksejrs/anki-2.0-vsa-and-ire), [manual](https://luoliyan.github.io/incremental-reading)

## Main Features

- Import content from web feeds (RSS/Atom), webpages, or Pocket (**v4 only**)
- Extract selected text into a new card by pressing <kbd>x</kbd>
- Highlight selected text by pressing <kbd>h</kbd>
- Remove selected text by pressing <kbd>z</kbd>
- Undo changes to the text by pressing <kbd>u</kbd>
- Apply rich text formatting while reading
- Create custom shortcuts to quickly add cards
- Maintain scroll position and zoom on a per-card basis
- Rearrange cards in the built-in organiser
- Control the scheduling of incremental reading cards
- Limit the width of cards (useful on large screens) (**v4 only**)

### New to Version 4

- Compatible with Anki 2.1
- Import single webpages (<kbd>Alt</kbd>+<kbd>3</kbd>)
- Import web feeds (<kbd>Alt</kbd>+<kbd>4</kbd>)
- Import Pocket articles (<kbd>Alt</kbd>+<kbd>5</kbd>)
- Apply bold, italics, underline or strikethrough (<kbd>Ctrl</kbd>+<kbd>B</kbd>, <kbd>I</kbd>, <kbd>U</kbd>, or <kbd>S</kbd>)
- Toggle formatting on and off (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>O</kbd>)
- Choose maximum width of cards (see options: <kbd>Alt</kbd>+<kbd>1</kbd>)
- Control initial scheduling of extracts (see options: <kbd>Alt</kbd>+<kbd>1</kbd>)

### New to Version 3

- Remove unwanted text with a single key-press (<kbd>z</kbd>)
- Multi-level undo, for reverting text changes (<kbd>u</kbd>)
- New options to control how text is extracted:
  - Open the full note editor for each extraction (slow), or simply a title entry box (fast)
  - Extract selected text as HTML (retain color and formatting) or plain text (remove all formatting)
  - Choose a destination deck for extracts
- New options for several aspects of zoom and scroll functionality:
  - _Zoom Step_ (the amount that magnification changes when zooming in or out)
  - _General Zoom_ (the zoom level for the deck browser and overview screens)
  - _Line Step_ (the amount the page moves up or down when the Up or Down direction keys are used)
  - _Page Step_ (same as above, but with the <kbd>Page Up</kbd> and <kbd>Page Down</kbd> keys)
- Highlighting:
  - Both the background color and text color used for highlighting can be customized
  - A drop-down list of available colors is provided
  - A preview is now displayed when selecting highlight colors
  - The colors applied to text extracted with <kbd>x</kbd> can now be set independently
- Quick Keys
  - A list of all existing Quick Keys is now shown, to allow easy modification
  - Unwanted Quick Keys can be easily deleted
  - A plain text extraction option has also been added
- All options have been consolidated into a single tabbed dialog

## Screenshots

**Note:** These are fairly outdated.

![Screenshot #1](https://raw.githubusercontent.com/luoliyan/incremental-reading/master/screenshots/extraction-and-highlighting.png)
![Screenshot #2](https://raw.githubusercontent.com/luoliyan/incremental-reading/master/screenshots/highlighting-tab.png)
![Screenshot #3](https://raw.githubusercontent.com/luoliyan/incremental-reading/master/screenshots/quick-keys-tab.png)

## Installation

You will first need to have Anki installed. Download the relevant installer [here](http://ankisrs.net).

To install through Anki, navigate to Tools → Add-ons → Get Add-ons..., and enter the code `935264945`. To install manually, download the GitHub repository ([here](https://github.com/luoliyan/incremental-reading-for-anki/archive/master.zip)) and place the `ir` folder into your add-ons folder.

## Usage

Experimentation should lead to a pretty quick understanding of how the add-on works. If in doubt, start with the following:

1. Create a new IR note with an article you want to study (the easiest way to do this is to import a webpage, by pressing <kbd>Alt</kbd>+<kbd>3</kbd> while on the deck overview screen)
2. Set up a shortcut for creating regular Anki cards from IR cards (press <kbd>Alt</kbd>+<kbd>1</kbd>, or go to the menu, then go to the Quick Keys tab)
3. Review the IR card that was created, and extract any text you find interesting (by selecting the text and pressing <kbd>x</kbd>)
4. Choose _Soon_ or _Later_ when you want to move to the next card (which will be a portion of text you extracted)
5. Whenever you want to create a regular Anki note, simply select the desired text and use the shortcut you created earlier

Outdated instructions can be found [here](https://luoliyan.github.io/incremental-reading). They were written for v2, but the basic behaviour of the add-on is still similar.

## Support

If any issues are encountered, please post details to the [Anki add-ons forum](https://anki.tenderapp.com/discussions/add-ons). It’s best if you post in the existing thread ([here](https://anki.tenderapp.com/discussions/add-ons/9054-incremental-reading-add-on-discussion-support)) so I receive an email notification. Otherwise, [note an issue](https://github.com/luoliyan/incremental-reading-for-anki/issues) or make a pull request on GitHub.

Please include the following information in your post:

- The version of Anki you are using (e.g., v2.1.0-beta5; can be found in Help → About...)
- The version of IR you are using (this can be found in Read → About...)
- The operating system you are using
- Details of the problem
- Steps needed to reproduce the problem

## License

Multiple people have contributed to this add-on, and it’s somewhat unclear who to credit for which changes and which licenses to apply.

Tiago Barroso appears to have initiated the project, and he has [stated](https://groups.google.com/d/msg/anki-addons/xibqDVFqQwQ/-qpxKvxurPMJ) that he releases all of his add-ons under the ISC license. Frank Kmiec later vastly expanded the add-on, but it’s unclear which license his changes were released under. Presuming he didn’t specify one, the [AnkiWeb terms and conditions](https://ankiweb.net/account/terms) suggest they were automatically released under the AGPL v3. Aleksej’s changes to Frank’s version are [multi-licensed under the GPL and ISC licenses](https://github.com/aleksejrs/anki-2.0-vsa-and-ire).

For the sake of simplicity, my changes are also released under the ISC license. For each author, I have placed a copyright lines where appropriate, with what I believe are correct dates. If I have made a mistake in this respect, please let me know.

Frank Raiser released an Anki 1 add-on under a similar name, but it doesn’t appear to share any code with the current project and functions quite differently. For more information, see [Anki Incremental Reading](http://frankraiser.de/drupal/AnkiIR).
