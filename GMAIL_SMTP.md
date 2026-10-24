# Gmail SMTP for Workspace Apps

Status: prepared, not configured or delivery-verified. Private credentials are required before any live change.

All Apps use one Supabase Auth project. Supabase, rather than the Vercel frontend, sends confirmation, invitation and password-recovery emails. Updating its custom SMTP changes transport without replacing those flows or templates.

## Private variables

Enter these only in `C:\Users\ajmer\.config\workspace-apps\gmail-smtp.env`, or inject them into the operator script's server-side environment. This file is outside Git and OneDrive. Do not paste credentials into chat, add a `NEXT_PUBLIC_` prefix, or put them in Vercel's client bundle.

```dotenv
GMAIL_SMTP_USER=
GMAIL_SMTP_APP_PASSWORD=
SUPABASE_ACCESS_TOKEN=
SMTP_TEST_RECIPIENT=
```

Use the complete personal Gmail address and a dedicated 16-letter Google app password. Enable 2-Step Verification and create it privately at https://myaccount.google.com/apppasswords. Never use the regular Gmail password. The recipient must be a mailbox you control.

The Supabase personal access token is needed only for the one-time Management API update. Create it privately at https://supabase.com/dashboard/account/tokens with access to the Workspace Apps project and auth-configuration read/write permissions where available. It is not the project's publishable or service-role key. Revoke the temporary token and remove it from the file after setup; the Gmail app password must remain active while Supabase sends mail.

## Configure and test

From this repository, with Python 3 installed:

```sh
python scripts/configure_supabase_smtp.py
python scripts/configure_supabase_smtp.py --apply --send-test
```

The script verifies certificate-checked STARTTLS at `smtp.gmail.com:587` before authentication. It sends credentials only to Google SMTP and Supabase's HTTPS Management API. It reads the current auth configuration, patches only six SMTP fields, and checks that invitation/recovery templates, redirects, confirmations and email rate limits stayed unchanged. It stops if a Send Email hook overrides SMTP. No credentials, auth config response bodies or email links are logged.

Hosted Supabase stores the submitted SMTP credentials in its server-side Auth configuration. Merely adding environment variables to Vercel will not configure Supabase Auth. The private environment file is an operator input, not a frontend runtime dependency.

Gmail accepting a test message proves SMTP submission, not inbox delivery. Confirm arrival and check Spam. Then use designated test accounts to verify Supabase signup confirmation, a dashboard invitation and password reset, including link return and completion. Do not claim production delivery works until these checks pass. The current app does not contain a custom invitation or password-reset screen; retain Supabase's existing native flows and document that UI limitation separately.

## Limits

- Personal Gmail may suspend sending after more than 500 messages per day; other abuse/recipient restrictions can apply sooner. Supabase's existing email rate limits still apply.
- Recipients see the Gmail sender address. Gmail is intended here for low volume, without a transactional-email delivery SLA or a custom sending domain.
- App passwords require 2-Step Verification and may be unavailable under some Google account policies. Changing the Google password revokes app passwords.
- An SMTP success response does not prove delivery, and SMTP checks alone do not verify invitation or recovery links.

References: [Google app passwords](https://support.google.com/accounts/answer/185833), [Gmail limits](https://support.google.com/mail/answer/22839?hl=en), [Supabase SMTP](https://supabase.com/docs/guides/auth/auth-smtp), [Management API](https://supabase.com/docs/reference/api/v1-update-auth-service-config).
