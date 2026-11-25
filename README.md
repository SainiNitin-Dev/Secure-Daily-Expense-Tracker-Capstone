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

The default settings are for a local HTTP demo and generate a fresh signing key when the server restarts. Setting `DJANGO_DEBUG=0` requires `DJANGO_SECRET_KEY`. For an HTTPS deployment, also set `DJANGO_ALLOWED_HOSTS` to the deployment hostname. That mode enables HTTPS redirects and secure session and CSRF cookies.
