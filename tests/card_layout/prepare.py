"""Copy the production manager and its tests from the validated Chromium tree."""
from pathlib import Path
import sys

source = Path(sys.argv[1]).resolve()
if sys.platform == "win32":
    source = Path("\\\\?\\" + str(source))
project = Path(__file__).resolve().parent
main = project / "src/main/java"
test = project / "src/test/java"
main.mkdir(parents=True, exist_ok=True)
test.mkdir(parents=True, exist_ok=True)
component = source / "chrome/android/features/tab_ui"
manager = (component / "java/src/org/chromium/chrome/browser/tasks/tab_management/TabCardLayoutManager.java").read_text()
# Standalone tests omit Chromium's nullness marker; layout code is copied unchanged.
manager = manager.replace("import org.chromium.build.annotations.NullMarked;\n", "").replace("@NullMarked\n", "")
(main / "TabCardLayoutManager.java").write_text(manager)
tests = (component / "junit/src/org/chromium/chrome/browser/tasks/tab_management/TabCardLayoutManagerUnitTest.java").read_text()
# Chromium registers the same tests with its own runner in chrome/android/junit/BUILD.gn.
tests = tests.replace("org.chromium.base.test.BaseRobolectricTestRunner", "org.robolectric.RobolectricTestRunner").replace("BaseRobolectricTestRunner.class", "RobolectricTestRunner.class")
(test / "TabCardLayoutManagerUnitTest.java").write_text(tests)
(project / "src/main/AndroidManifest.xml").write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android"/>')

# Exercise the production OLED overlay with Material's real attribute resolution.
styles = source / "components/browser_ui/styles/android"
helper = (styles / "java/src/org/chromium/components/browser_ui/styles/OledBlackTheme.java").read_text(encoding="utf-8")
helper = helper.replace("import org.chromium.build.annotations.NullMarked;\n", "").replace("@NullMarked\n", "")
(main / "OledBlackTheme.java").write_text(helper, encoding="utf-8")
tests = (styles / "junit/src/org/chromium/components/browser_ui/styles/OledBlackThemeUnitTest.java").read_text(encoding="utf-8")
tests = tests.replace("org.chromium.base.test.BaseRobolectricTestRunner", "org.robolectric.RobolectricTestRunner").replace("BaseRobolectricTestRunner.class", "RobolectricTestRunner.class")
(test / "OledBlackThemeUnitTest.java").write_text(tests, encoding="utf-8")
resources = project / "src/main/res/values"
resources.mkdir(parents=True, exist_ok=True)
for name in ("oled_black.xml", "attrs.xml"):
    (resources / name).write_bytes((styles / "java/res/values" / name).read_bytes())
