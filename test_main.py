"""Tests for the global Budget setting and its email template substitution.

Run with:  python3 -m unittest -v
"""
import json
import os
import tempfile
import unittest
from unittest import mock

import main


class FakeSMTP:
    """Captures the message that would be sent instead of hitting the network."""

    sent = []

    def __init__(self, *args, **kwargs):
        pass

    def ehlo(self):
        pass

    def login(self, user, password):
        pass

    def send_message(self, msg):
        FakeSMTP.sent.append(msg)

    def close(self):
        pass


class BudgetSettingTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self._orig_data_file = main.DATA_FILE
        main.DATA_FILE = os.path.join(self.tmpdir.name, "secret_santa_data.json")
        FakeSMTP.sent = []

    def tearDown(self):
        main.DATA_FILE = self._orig_data_file
        self.tmpdir.cleanup()

    # ---- persistence -------------------------------------------------
    def test_default_budget_used_when_no_data_file_exists(self):
        self.assertEqual(main.get_budget(), main.DEFAULT_SETTINGS["budget"])

    def test_save_budget_persists_to_the_same_json_file(self):
        main.save_budget("$40")

        with open(main.DATA_FILE) as f:
            raw = json.load(f)
        self.assertEqual(raw["settings"]["budget"], "$40")
        self.assertEqual(main.get_budget(), "$40")
        self.assertEqual(main.get_settings()["budget"], "$40")

    def test_save_budget_strips_whitespace(self):
        self.assertEqual(main.save_budget("  $15  "), "$15")
        self.assertEqual(main.get_budget(), "$15")

    def test_save_budget_rejects_empty_value(self):
        with self.assertRaises(ValueError):
            main.save_budget("   ")
        self.assertEqual(main.get_budget(), main.DEFAULT_SETTINGS["budget"])

    def test_settings_survive_other_saves(self):
        main.save_budget("$60")
        adults = [("Alice", "alice@example.com")]
        children = [("Bob", "")]

        # Simulates the app saving participants after a budget was set.
        main.save_data(adults, children)

        data = main.load_data()
        self.assertEqual(data["settings"]["budget"], "$60")
        self.assertEqual(data["adults"], [["Alice", "alice@example.com"]])
        self.assertEqual(data["children"], [["Bob", ""]])

    def test_unknown_new_settings_fall_back_to_defaults(self):
        # A file written before the budget setting existed must still load.
        with open(main.DATA_FILE, "w") as f:
            json.dump({"adults": [], "children": []}, f)
        self.assertEqual(main.get_budget(), main.DEFAULT_SETTINGS["budget"])

    # ---- template substitution --------------------------------------
    def test_build_email_body_substitutes_the_global_budget(self):
        main.save_budget("$50")
        body = main.build_email_body(
            adult_name="Alice Smith",
            adult_assignment="Bob Jones",
        )
        self.assertIn("$50", body)
        self.assertNotIn("$25", body)
        self.assertIn("spending limit of $50", body)

    def test_every_participant_is_told_the_same_global_amount(self):
        main.save_budget("$75")
        first = main.build_email_body("Alice Smith", "Bob Jones")
        second = main.build_email_body("Carol White", "Dave Black", child_assignment="Eve")
        self.assertIn("$75", first)
        self.assertIn("$75", second)
        self.assertNotIn("$25", first + second)

    def test_changing_the_setting_changes_the_template(self):
        main.save_budget("$10")
        self.assertIn("$10", main.build_email_body("Alice", "Bob"))
        main.save_budget("$99")
        self.assertIn("$99", main.build_email_body("Alice", "Bob"))
        self.assertNotIn("$10", main.build_email_body("Alice", "Bob"))

    def test_sent_email_uses_the_global_budget_for_all_recipients(self):
        main.save_budget("$42")

        with mock.patch.object(main.smtplib, "SMTP_SSL", FakeSMTP):
            main.send_email_direct("Alice Smith", "alice@example.com", "Bob Jones")
            main.send_email_direct(
                "Carol White", "carol@example.com", "Dave Black",
                child_assignment="Eve",
            )

        self.assertEqual(len(FakeSMTP.sent), 2)
        bodies = [part.get_payload(decode=True).decode() for msg in FakeSMTP.sent
                  for part in msg.walk() if part.get_content_type() == "text/plain"]
        for body in bodies:
            self.assertIn("$42", body)
            self.assertNotIn("$25", body)

    def test_explicit_budget_argument_overrides_for_that_email_only(self):
        main.save_budget("$42")
        body = main.build_email_body("Alice", "Bob", budget="$5")
        self.assertIn("$5", body)
        # The stored global setting is unchanged.
        self.assertEqual(main.get_budget(), "$42")


if __name__ == "__main__":
    unittest.main()
