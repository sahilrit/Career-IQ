# Google setup (Gmail + Calendar)

CareerOS can send outreach from your Gmail and manage interview events on
your Calendar. Each user connects **their own** Google account; you (the
operator) only need to register the app once so the "Connect Google" button
works. Until the two keys below are set, the button is hidden and everything
else works normally.

## 1. Create the Google Cloud project

1. Go to <https://console.cloud.google.com> → create a project (e.g. "CareerOS").
2. **APIs & Services → Library** → enable **Gmail API** and **Google Calendar API**.

## 2. OAuth consent screen

1. **APIs & Services → OAuth consent screen** → User type **External** → Create.
2. Fill app name, support email, developer email. Save.
3. **Scopes** → add: `.../auth/gmail.send`, `.../auth/calendar.events`,
   `.../auth/userinfo.email`.
4. **Test users** → add your own Google address (while the app is in "Testing",
   only listed test users can connect — that's fine for you). Publish later to
   open it up.

## 3. OAuth client credentials

1. **APIs & Services → Credentials → Create credentials → OAuth client ID**.
2. Application type **Web application**.
3. **Authorized redirect URIs** → add exactly:
   `https://<your-web-app-url>/settings/google/callback`
   (e.g. `https://careeros-web-1tor.onrender.com/settings/google/callback`).
   Add a `http://localhost:3000/settings/google/callback` entry too for local dev.
4. Create → copy the **Client ID** and **Client secret**.

## 4. Set the env on `careeros-api` (Render)

- `CAREEROS_GOOGLE_CLIENT_ID` = the client ID
- `CAREEROS_GOOGLE_CLIENT_SECRET` = the client secret
- `CAREEROS_APP_BASE_URL` = your web app URL (used to build the redirect;
  must match the redirect URI's origin above)

Save → the API redeploys. Now open the app → **Settings → Google → Connect
Google**, approve the consent screen, and you're connected: send email and
see your calendar from Settings.

## Notes

- We store only the long-lived **refresh token**, encrypted in the vault; a
  fresh access token is fetched per request.
- If a connect ever fails with "no refresh token", revoke the app at
  <https://myaccount.google.com/permissions> and connect again (Google only
  returns a refresh token on first consent).
- Scopes are minimal: send-only Gmail (can't read your inbox) and calendar
  events. Disconnect any time from Settings.
