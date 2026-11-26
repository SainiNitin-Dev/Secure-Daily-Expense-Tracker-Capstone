# Secure Daily Expense Tracker

A small Django app for recording, finding, and deleting your own expenses. It uses SQLite and server-rendered HTML/CSS.

## Run locally in PowerShell

From the project folder, run these commands:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver --no-color
```

Open [the tracker](http://127.0.0.1:8000/) in your browser. Select **Create an account**, then log in. Django creates the SQLite file during migration.

## Run the checks

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

The tests use a temporary database. They cover account creation, password hashing, login/logout, failed-login recording, filters, ownership, input validation, CSRF protection, and the SQL-looking input from the brief.

To see failed login attempts during a demo, enter a wrong password, then run:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from expenses.models import FailedLoginAttempt; print(list(FailedLoginAttempt.objects.values('username', 'attempted_at').order_by('-attempted_at')[:5]))"
```

Each record contains the submitted username and a timestamp.

## Explain the app in a project review

| Question | Short answer |
| --- | --- |
| What happens when I add an expense? | The view receives the form. Django validates it, the view attaches the signed-in user, and the model saves it to SQLite. |
| How do you protect another user's records? | Every expense query starts with the signed-in user. To delete an expense, both its ID and its owner must match. |
| How do you handle the security example in the brief? | The category allowlist rejects it. A description accepts it as text. Django passes values as query parameters and escapes descriptions in HTML. |
| Why use POST and a CSRF token to delete? | POST represents a change. Django uses the CSRF token to check that the request came from a form served by this app. |
| How does logging out work? | Django invalidates the database-backed session. The browser must log in again to access expenses. |

The routes are in `tracker/urls.py`, the form checks are in `expenses/forms.py`, and the save, list, and delete logic is in `expenses/views.py`.

## Deploy to Vercel

Vercel runs Django online and Neon stores the deployed app's users, sessions, and expenses. SQLite is available for running the app on your computer.

1. Open the Vercel project's **Storage** tab and connect a **Neon Postgres** database to the **Production** environment. Verify that the integration added `DATABASE_URL` in **Settings → Environment Variables**.
2. Add a production variable named `DJANGO_SECRET_KEY`. Generate its value locally with `.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`.
3. Enable **System Environment Variables** so Django can read the deployment hostname and use HTTPS settings. If you use an additional custom domain, add its hostname to `DJANGO_ALLOWED_HOSTS`.
4. Deploy this revision to production with the project's Build Command override disabled. The repository's build command applies the Django migrations to Neon, using the direct connection when `DATABASE_URL_UNPOOLED` is available.
5. Open the deployed URL and register an account. Add an expense, log out, then log back in to verify that the expense was saved.

Production migrations run during the Vercel build. Preview deployments need their own connection and a migrated database if you want to use them. The local SQLite file is excluded from Git. Accounts and expenses created locally can be transferred separately if needed.
