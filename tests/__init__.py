import os

# Keep the test run isolated: separate QSettings store, no session restore, no modal prompts.
os.environ.setdefault("ANOTERRA_TESTING", "1")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
