# Bottom address bar and optional tab cards

This fork extends two existing settings on phones:

* **Address bar → Bottom:** editing stays above the keyboard; the highest-ranked
  suggestion is nearest the address field and other suggestions extend upward.
  The tab switcher puts its search field at the bottom, with new-tab, pane and
  menu controls above it. Short tab lists align with the bottom controls.
  On the home page, the utility toolbar sits at the bottom, the search field
  directly above it, and the remaining short page contents above the search field.
* **Tabs and tab groups → Tab switcher layout:** **Grid** (default) or **Cards**.
  Cards use one wide column of overlapping previews. Tab identity, thumbnails,
  close actions, groups and transition animations use the existing tab model and
  views. The preference is independent of address-bar placement and changes the
  phone switcher without restarting the browser.

The group dialog, selection editor, tablets, automotive and XR keep their existing
layouts. The home page follows the address-bar preference, including while editing.
Long home-page contents remain scrollable, and Top mode restores the original
ordering. Find in page and picture-in-picture retain Chromium's existing toolbar rules.

## Source integration

`patch.sh` applies the ordered patches in `patches/` after Titanium's existing
overrides, and stops the build if a patch cannot apply. The first patch implements
the bottom controls/cards; the second adds [OLED black backgrounds](oled-black.md).
Later patches repair integration and lifecycle issues, align close animations,
and apply Bottom mode to the home page.
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
is disabled in Cards mode and bottom-aligned grids. This prevents the predictive
pass from moving a disappearing card back to the top before its shrink animation;
the existing shrink, move and switcher animations remain.

The home page puts its fake search field after the other page elements and fills
short pages to the scroll viewport, using bottom gravity. It retains status-bar
insets, tracks viewport resizing, and restores the original order, padding and
minimum height when Top mode is selected. Preference and viewport observers are
removed when the view detaches. The bottom toolbar stays at its own origin during
home search focus and scrolling, keeping the editing field above the keyboard.

## Automated validation

Run the source integration check (requires Python 3, Git, internet and the submodule):

```sh
python3 tools/check_bottom_ui_patch.py --output-dir /tmp/titanium-ui-source
```

The output directory must be new or empty. The check downloads only the affected
files at the pinned Chromium tag, verifies their Git blob hashes, applies relevant
Vanadium patches with Titanium branding, applies this patch, parses its XML and
checks that the ordered patches can be reversed. A Chromium upgrade deliberately fails the
hash check until the patch is ported.

The `Check bottom UI` workflow also runs isolated Android RecyclerView and OLED
palette tests using production code/resources and the same test cases registered
in Chromium:

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

Chromium's test suite also registers real-animator coordinate checks and home-page
ordering, inset, scrolling, keyboard-viewport and preference regression cases.
The focused animation, home-page, binder and toolbar suites passed 204 cases on
Android API 29 and 36. This is a subset of Chromium's tests. The standalone Gradle
harness does not verify native startup, URL editing, thumbnails or transitions.

## Android acceptance before release

After changes, build the complete APK and repeat the live Android checks. Use the
documented Linux test build or the existing release workflow with your own signing
configuration.

1. With Address bar set to Bottom, focus a page URL, type, choose a suggestion and
   dismiss the keyboard. Repeat in incognito and from the NTP fakebox.
   On the home page, verify bottom utility controls, search above them and page
   content above search; repeat after resizing and after switching back to Top.
2. Check floating keyboards, keyboard height changes, gesture and three-button
   navigation, portrait/landscape and split-screen. Confirm the field stays reachable
   and suggestions do not cover it or double-subtract the keyboard height.
3. Open the tab switcher with 0, 1, 3 and many tabs. Check search, new tab, menu and
   regular/incognito/group pane switching, including typed searches.
4. Change Grid/Cards while the switcher is warm. Check opening, selecting, swiping
   closed and undoing tabs, especially the first and last cards. Check thumbnails,
   tab groups, drag-to-group, archive/message cards and transition animations.
   The disappearing preview must shrink at the position of the actual closed tab,
   including the second grid column and when a removal changes the number of rows.
5. Restore Address bar → Top and Grid. Check TalkBack, keyboard navigation and large
   text. Compare tablet, automotive and XR behavior with the upstream build.

These are pending acceptance checks, not claims of observed device behavior.
