# Bottom address bar and optional tab cards

This fork extends two existing settings on phones:

* **Address bar → Bottom:** editing stays above the keyboard; the highest-ranked
  suggestion is nearest the address field and other suggestions extend upward.
  The tab switcher puts its search field at the bottom, with new-tab, pane and
  menu controls above it. Short tab lists align with the bottom controls.
  In Grid, tabs fill from the bottom-right toward the left, then continue in
  the row above. An incomplete row stays against the right edge. Long grids
  scroll upward to reach later tabs. Text keeps the system's language direction.
  On the home page, the utility toolbar sits at the bottom, the search field
  directly above it, and the remaining short page contents above the search field.
* **Tabs and tab groups → Tab switcher layout:** **Grid** (default),
  **Vertical cards**, or **Horizontal cards**. Vertical cards use a column of
  overlapping previews with 10% margins on either side. Cards fade smoothly
  through the bottom edge instead of disappearing while their titles are visible.
  Horizontal cards form a fanned deck, with the primary preview about 75% of the
  screen width and 70% of its height. The primary card sits above the bottom
  action controls, or vertically centered when Top controls are selected.
  Swiping browses the deck; the departing card keeps its size and fades near
  the edge, while the next card slides in and grows slightly in height.
  Use the close button to close a tab in Horizontal cards.
  Tab identity, thumbnails,
  close actions, groups and transition animations use the existing tab model and
  views. The preference is independent of address-bar placement and changes the
  phone switcher without restarting the browser.
* **Tab switcher handedness:** Right handed (default) or Left handed mirrors
  Grid columns and the Horizontal cards deck, including its swipe direction.
  The preference is disabled in Vertical cards, which is symmetric.
  Existing Cards users retain Vertical cards without resetting the preference.

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

All modes retain GridLayoutManager's tab integration. Vertical cards use one span
with negative top decoration insets between adjacent previews and 10% side insets.
Message cards retain their full height.
The last preview retains its full bottom edge after closing a tab. Predictive layout
is disabled in Cards mode and bottom-aligned grids. This prevents the predictive
pass from moving a disappearing card back to the top before its shrink animation;
the existing shrink, move and switcher animations remain.
Bottom-mode Grid uses reverse vertical layout and right-to-left span placement,
without changing the RecyclerView or tab contents' language direction. Top mode
and the overlapping Vertical cards layout retain their existing vertical ordering.
Horizontal cards use one horizontal span, edge snapping and transformed previews
with a small height reduction behind the primary card. Extra layout space keeps
overlapping previews attached until they finish fading. Switching modes clears
the preview transforms. Horizontal deck gestures bypass swipe-to-close so browsing
cannot accidentally dismiss a tab; close buttons retain the existing close action.

The home page puts its fake search field after the other page elements and fills
short pages to the scroll viewport, using bottom gravity. It retains status-bar
insets, tracks viewport resizing, and restores the original order, padding and
minimum height when Top mode is selected. Preference and viewport observers are
removed when the view detaches. The bottom toolbar stays at its own origin during
home search focus and scrolling, keeping the editing field above the keyboard.

Page-to-switcher transitions obtain their thumbnail target at a stable pre-draw,
after ancestor layouts and pending card moves have settled. Target bounds include
ancestor transforms and the complete thumbnail rather than a viewport-clipped
rectangle. The animated bitmap interpolates to the same top-center fill crop used
by the thumbnail, retaining its final transform until removal. A short blend at
the end avoids a hard change between the page capture and cached preview.
Thumbnail and container origins use the same screen coordinate system, including
the window's status-bar offset. Fan transforms are reapplied after binding settles.

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

The bottom-right Grid change passed 58 production-manager and real close-animation
cases on API 29 and 36. These cover odd/even tab counts, two/three columns, full-width
message rows, padding, scrolling in both directions, Top/Cards restoration and
language direction. Fourteen new-order checks failed before the change.

The Vertical/Horizontal cards and handedness update passed 88 production layout,
real close-animation and gesture-routing checks on API 29/36. These include side
margins, retained fading cards, horizontal size/depth/alpha, outgoing size stability,
both hands, selected-tab positioning, window centering, resizing, empty/single/long
decks and mode restoration. Horizontal swipes are checked to bypass tab dismissal.

The page/thumbnail transition repair passed 138 geometry, bitmap-crop, provider,
card-layout and real close-animation checks on API 29/36. It covers the reproduced
240-pixel parent relayout, clipping, transformed ancestors, cancellation, matched
tall-card crops, continuous bitmap scaling and final-frame transform retention.
The additional checks cover window-origin normalization and restoring the fan
after binding/item-animation callbacks alter presentation properties.

## Preview resolution

Phone previews capture at physical screen resolution in all three modes. The JPEG
cache preserves the captured dimensions at the existing quality setting instead
of halving each axis again. JPEG reads still sample down to the requested card
size, and the existing two-entry native cache and bounded compression/write queues
remain unchanged. Native-page animation callbacks reuse the captured bitmap rather
than allocating another half-size image. Tablet capture density retains upstream
behavior.

On the Moto's 1220-pixel-wide display, the previous capture and JPEG reductions
produced 353-pixel-wide previews, which the wide cards magnified. Previously saved
previews retain their old detail until the corresponding page is visited and
captured again; missing detail cannot be recovered by enlarging those files.

Sixteen TabContentManager cases passed on API 29/36, including high-density phone
capture and consistent native readback bounds. The native JPEG tests also check
encoded dimensions and retention of alternating two-pixel lines.

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
   In Bottom/Grid, verify the first tab is at bottom-right, the second to its
   left, and the third in the row above on the right. Scroll long lists in both
   directions and repeat after changing orientation and Top/Bottom placement.
4. Change Grid/Vertical cards/Horizontal cards while the switcher is warm.
   Check opening, selecting, swiping
   closed and undoing tabs, especially the first and last cards. Check thumbnails,
   tab groups, drag-to-group, archive/message cards and transition animations.
   The disappearing preview must shrink at the position of the actual closed tab,
   including the second grid column and when a removal changes the number of rows.
   For Horizontal cards, check the active preview, fan depth, height growth,
   outgoing fade, edge snap, both swipe directions and the close button. Change
   handedness and confirm the deck and Grid mirror without mirroring tab text.
5. Restore Address bar → Top and Grid. Check TalkBack, keyboard navigation and large
   text. Compare tablet, automotive and XR behavior with the upstream build.

These are pending acceptance checks, not claims of observed device behavior.
