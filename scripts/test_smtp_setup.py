import unittest
from unittest.mock import MagicMock, patch
import configure_supabase_smtp as setup


class SMTPSetupTests(unittest.TestCase):
    def config(self):
        return setup.settings({"GMAIL_SMTP_USER": "test@gmail.com", "GMAIL_SMTP_APP_PASSWORD": "abcd efgh ijkl mnop"})

    @patch.object(setup.smtplib, "SMTP")
    def test_starttls_precedes_authentication(self, smtp):
        client = smtp.return_value
        setup.connect_smtp(self.config())
        self.assertEqual([call[0] for call in client.method_calls], ["ehlo", "starttls", "ehlo", "login"])
        self.assertTrue(client.starttls.call_args.kwargs["context"].check_hostname)

    @patch.object(setup.smtplib, "SMTP")
    def test_tls_failure_never_sends_credentials(self, smtp):
        client = smtp.return_value
        client.starttls.side_effect = setup.smtplib.SMTPNotSupportedError("No TLS")
        with self.assertRaises(setup.smtplib.SMTPException):
            setup.connect_smtp(self.config())
        client.login.assert_not_called()
        client.close.assert_called_once()

    @patch.object(setup, "management")
    def test_patch_preserves_invites_recovery_and_confirmation(self, api):
        config = self.config()
        before = {"mailer_templates_invite_content": "invite", "mailer_templates_recovery_content": "recovery", "site_url": "https://workspaceapps.vercel.app", "mailer_autoconfirm": False}
        api.side_effect = [before, {}, {**before, **config}]
        setup.apply_settings({"SUPABASE_ACCESS_TOKEN": "fixture"}, config)
        self.assertEqual(api.call_args_list[1].args[1], config)
        self.assertEqual(set(config), setup.SMTP_KEYS)

    @patch.object(setup, "management")
    def test_existing_email_hook_blocks_switch(self, api):
        api.return_value = {"hook_send_email_enabled": True}
        with self.assertRaises(ValueError):
            setup.apply_settings({"SUPABASE_ACCESS_TOKEN": "fixture"}, self.config())
        self.assertEqual(api.call_count, 1)


if __name__ == "__main__":
    unittest.main()
