# Bottom address bar and optional tab cards

This fork extends two existing settings on phones:

* **Address bar → Bottom:** editing stays above the keyboard; the highest-ranked
  suggestion is nearest the address field and other suggestions extend upward.
  The tab switcher puts its search field at the bottom, with new-tab, pane and
  menu controls above it. Short tab lists align with the bottom controls.
* **Tabs and tab groups → Tab switcher layout:** **Grid** (default) or **Cards**.
  Cards use one wide column of overlapping previews. Tab identity, thumbnails,
  close actions, groups and transition animations use the existing tab model and
  views. The preference is independent of address-bar placement and changes the
  phone switcher without restarting the browser.

The group dialog, selection editor, tablets, automotive and XR keep their existing
layouts. The unfocused NTP fakebox retains Chromium's placement; focusing it moves
editing to the configured bottom address bar. Find in page and picture-in-picture
retain Chromium's existing toolbar rules.

## Source integration

`patch.sh` applies `patches/0001-complete-bottom-address-bar-and-tab-cards.patch`
after Titanium's existing overrides, and stops the build if the patch cannot apply.
The implementation was developed against Chromium **156.0.8078.73**, from the
pinned Vanadium submodule **8ae4b1b8b014862146ff9a09dc8c6fc6e9a0a978**.

The focused address bar uses the existing toolbar controller's IME handling, with
resize mode avoiding a second keyboard subtraction. Suggestions use the toolbar's
actual position in its window rather than estimating available space from display
height. Hub search supplies its bottom placement through the location-bar embedder.
The Hub toolbar observes the existing placement preference and reserves its measured
height, including navigation insets, in the pane host.

Cards retain GridLayoutManager's tab integration and use one span with negative top
decoration insets between adjacent tab cards. Message cards retain their full height.
The last preview retains its full bottom edge after closing a tab. Predictive layout
is disabled in Cards mode; the existing tab item and switcher animations remain.

## Automated validation

Run the source integration check (requires Python 3, Git, internet and the submodule):

```sh
python3 tools/check_bottom_ui_patch.py --output-dir /tmp/titanium-ui-source
```

The output directory must be new or empty. The check downloads only the affected
files at the pinned Chromium tag, verifies their Git blob hashes, applies relevant
Vanadium patches with Titanium branding, applies this patch, parses its XML and
checks that the patch can be reversed. A Chromium upgrade deliberately fails the
hash check until the patch is ported.

The `Check bottom UI` workflow also runs isolated Android RecyclerView tests using
the production card layout manager and the same test cases registered in Chromium:

```sh
python3 tests/card_layout/prepare.py /tmp/titanium-ui-source
gradle --no-daemon -p tests/card_layout testDebugUnitTest
```

This requires Gradle 8.10.2, Java 17 and Android SDK 35 (build tools 35.0.1). Set
`ANDROID_HOME` or an untracked `tests/card_layout/local.properties` with `sdk.dir`.
The standalone harness omits Chromium's nullness annotation and substitutes the
standard Robolectric runner; the production layout and scrolling code are unchanged.
It covers overlap, empty/single/long lists, scroll gestures, switching back to Grid,
message cards, bottom padding, smaller viewports, and closing first/middle/last tabs.

Toolbar and suggestion-positioning regression tests are updated in the Chromium
patch, but the full Chromium test suite has not been run locally. The standalone
tests do not verify native browser startup, URL editing, thumbnails or transitions.

## Android acceptance before release

A full Titanium APK build and live Android checks remain required. Use the existing
Build workflow or the documented Linux build with your own signing configuration.

1. With Address bar set to Bottom, focus a page URL, type, choose a suggestion and
   dismiss the keyboard. Repeat in incognito and from the NTP fakebox.
2. Check floating keyboards, keyboard height changes, gesture and three-button
   navigation, portrait/landscape and split-screen. Confirm the field stays reachable
   and suggestions do not cover it or double-subtract the keyboard height.
3. Open the tab switcher with 0, 1, 3 and many tabs. Check search, new tab, menu and
   regular/incognito/group pane switching, including typed searches.
4. Change Grid/Cards while the switcher is warm. Check opening, selecting, swiping
   closed and undoing tabs, especially the first and last cards. Check thumbnails,
   tab groups, drag-to-group, archive/message cards and transition animations.
5. Restore Address bar → Top and Grid. Check TalkBack, keyboard navigation and large
   text. Compare tablet, automotive and XR behavior with the upstream build.

These are pending acceptance checks, not claims of observed device behavior.
