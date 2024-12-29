# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Don't switch to deck browser after import (#38)
- Properly handle importing a page when title is missing (#34)

### Changed
- Use `poetry` to manage the project (#43)
- Add GitHub workflow to run tests automatically

### Removed
- `maxWidth` configuration


## [4.11.9] - 2023-03-05

### Added
- Add ability to import Epub files (lujun9972@).

### Fixed
- Fix compatibility with 23.10 (lujun9972@, khonkhortisan@, tvhong@).

## [4.11.8]

### Fixed
- Use resolved title from Pocket when import from Pocket (contribution by lujun9972@).

## [4.11.7]

### Fixed
Fix bug for first time user creating IR cards.

## [4.11.6]

### Fixed
- Fix bug in enabling priority queue.

## [4.11.5]

### Fixed
- Fix images and named anchors importing.

## [4.11.4]

### Fixed
- Fix HTTPS imports in MacOS.

## [4.11.3]

### Removed
- Remove deprecated imports from Anki 2.1.54.