"""Private, operator-only Gmail SMTP setup. Never imported by the website."""
import argparse
import json
import os
from pathlib import Path
import re
import smtplib
import ssl
import sys
from email.message import EmailMessage
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT = "lefnzbymcrbpwzynmptg"
PRIVATE_FILE = Path.home() / ".config" / "workspace-apps" / "gmail-smtp.env"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_KEYS = {"smtp_host", "smtp_port", "smtp_user", "smtp_pass", "smtp_admin_email", "smtp_sender_name"}


def load_private(path):
    """Parse data, never shell code. Existing server environment takes priority."""
    values = dict(os.environ)
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            if not separator or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
                raise ValueError("Invalid private environment file format.")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values.setdefault(key, value)
    return values


def settings(values):
    user = values.get("GMAIL_SMTP_USER", "").strip()
    password = values.get("GMAIL_SMTP_APP_PASSWORD", "").replace(" ", "")
    if not re.fullmatch(r"[A-Za-z0-9._%+-]+@gmail\.com", user, re.I):
        raise ValueError("Set GMAIL_SMTP_USER to the personal Gmail sending address privately.")
    if not re.fullmatch(r"[A-Za-z]{16}", password):
        raise ValueError("Set GMAIL_SMTP_APP_PASSWORD to a 16-letter Google app password privately.")
    return {"smtp_host": SMTP_HOST, "smtp_port": str(SMTP_PORT), "smtp_user": user,
            "smtp_pass": password, "smtp_admin_email": user, "smtp_sender_name": "Workspace Apps"}


def connect_smtp(config):
    client = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    try:
        client.ehlo()
        # Fail closed: no login or mail before verified STARTTLS succeeds.
        client.starttls(context=ssl.create_default_context())
        client.ehlo()
        client.login(config["smtp_user"], config["smtp_pass"])
        return client
    except Exception:
        client.close()
        raise


def management(token, patch=None):
    request = Request(f"https://api.supabase.com/v1/projects/{PROJECT}/config/auth",
                      data=None if patch is None else json.dumps(patch).encode(),
                      headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
                      method="GET" if patch is None else "PATCH")
    # Never print response bodies: auth config can contain credentials and templates.
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def preserved(config):
    return {key: value for key, value in config.items()
            if key in {"site_url", "uri_allow_list", "disable_signup", "mailer_autoconfirm",
                       "mailer_allow_unverified_email_sign_ins", "external_email_enabled", "rate_limit_email_sent"}
            or key.startswith(("mailer_templates_", "mailer_subjects_", "hook_"))}


def apply_settings(values, config):
    token = values.get("SUPABASE_ACCESS_TOKEN", "").strip()
    if not token:
        raise ValueError("Set SUPABASE_ACCESS_TOKEN privately for the one-time Supabase settings update.")
    before = management(token)
    if before.get("hook_send_email_enabled"):
        raise ValueError("An email hook is enabled. Review it before switching SMTP; no settings changed.")
    if set(config) != SMTP_KEYS:
        raise ValueError("Refusing changes outside the SMTP settings.")
    management(token, config)
    after = management(token)
    if preserved(before) != preserved(after):
        raise ValueError("SMTP updated, but auth flow settings differ on readback. Review the Supabase dashboard.")
    if any(str(after.get(key)) != value for key, value in config.items() if key != "smtp_pass"):
        raise ValueError("SMTP settings could not be verified on readback. Review the dashboard.")
    print("Supabase Gmail SMTP settings verified. Invitation/recovery templates, redirects, confirmations and limits preserved.")


def send_test(values, config):
    recipient = values.get("SMTP_TEST_RECIPIENT", "").strip()
    if not re.fullmatch(r"[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+", recipient):
        raise ValueError("Set SMTP_TEST_RECIPIENT privately to a mailbox you control.")
    message = EmailMessage()
    message["From"] = "Workspace Apps <" + config["smtp_user"] + ">"
    message["To"] = recipient
    message["Subject"] = "Workspace Apps Gmail SMTP delivery check"
    message.set_content("This is the requested SMTP delivery test. No sign-in links or private app data are included. Please confirm receipt and check Spam. Invitation and password-reset flows require separate end-to-end checks through Supabase.")
    with connect_smtp(config) as client:
        refused = client.send_message(message)
    if refused:
        raise ValueError("The SMTP server rejected the test recipient.")
    print("Gmail accepted the test message. Inbox delivery is NOT verified; check the destination mailbox and Spam.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=PRIVATE_FILE)
    parser.add_argument("--apply", action="store_true", help="Update only this project's SMTP settings after TLS/auth preflight")
    parser.add_argument("--send-test", action="store_true", help="Send one plain delivery test to SMTP_TEST_RECIPIENT")
    args = parser.parse_args()
    try:
        values = load_private(args.env_file)
        config = settings(values)
        with connect_smtp(config):
            pass
        print("Gmail authentication and certificate-verified STARTTLS on port 587 passed.")
        if args.apply:
            apply_settings(values, config)
        if args.send_test:
            send_test(values, config)
        if not args.apply:
            print("Supabase settings were not changed. Use --apply when ready.")
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    except HTTPError as error:
        print(f"Supabase management request failed (HTTP {error.code}); response details suppressed.", file=sys.stderr)
        return 1
    except (OSError, URLError, smtplib.SMTPException):
        print("SMTP/network check failed. Verify credentials, app-password availability, quotas and connectivity privately; no credentials were logged.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
