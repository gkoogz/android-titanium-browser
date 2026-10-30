# OLED black browser backgrounds

**Settings → Appearance → OLED black backgrounds** is an opt-in browser UI mode.
It uses opaque `#000000` surfaces and dark controls. The prior Light/Dark/System
choice is retained and restored when OLED black is disabled. The theme-choice row
shows the active OLED mode while that override is enabled.

Android's dynamic palette is applied first, and a surface-only overlay follows it.
The overlay leaves primary, secondary, tertiary and on-accent color roles intact.
It disables elevation tinting so elevated surfaces cannot become tinted gray or
brown. OLED mode uses the OS palette when dynamic colors are available, rather
than an NTP custom color palette. There is no hard-coded accent hue.

The overlay covers browser surfaces and the window background. Separate background
providers also honor it for the Hub/tab switcher, search, incognito, top/bottom
toolbar, tab cards, tab groups and selection controls. Selected tab cards retain a
thin outline and readable title/close colors from the active accent palette.
Webpage pixels and tab preview images remain webpage content; this is not a website
dark-mode filter.

The night-mode controller watches the OLED preference and recreates the UI even if
the browser was already dark, so enabling/disabling the palette takes effect without
restarting the browser process. The setting is off by default.

## Implementation and checks

`patches/0002-oled-black-browser-surfaces.patch` applies after the bottom-UI patch.
The source validation tool checks both patches in order against the pinned Chromium
and Vanadium sources, and verifies their reverse application in a temporary index.

The standalone Android test harness compiles the actual OLED resource overlay with
Material's theme resources and checks:

* The OLED theme marker is opt-in.
* All overridden surface roles resolve to opaque black.
* Accent and on-accent roles are unchanged by the overlay.
* Elevation cannot retint black surfaces.
* Body text retains at least 4.5:1 contrast against black.

The ten tab-layout regression tests also run. The Chromium patch includes additional
night-mode regression cases for restoring the saved Light choice and notifying
observers when changing the palette while already dark. Those full Chromium tests
have not been run locally.

## Pending Android acceptance

A full Titanium APK build and live device testing remain required. Before release,
enable and disable OLED black starting from Light, Dark and System default. Check
settings, regular/incognito tabs, Grid/Cards, tab groups, inactive-tab messages,
URL editing, browser menus, dialogs, keyboard and system navigation transitions.
Change Android's wallpaper/accent palette and verify that accents follow it while
browser surfaces stay black. Check selected-tab visibility, large text and TalkBack.

Automated palette/layout checks do not establish observed browser behavior on a phone.
