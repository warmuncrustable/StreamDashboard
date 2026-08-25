# Setup

This guide covers the complete configuration required to get Stream Dashboard working.

There are two separate integrations:

1. Twitch
2. YouTube

If you only want to use one platform, you can configure that platform and ignore the other.

## Table of Contents

- [Before You Start](#before-you-start)
- [Project Files](#project-files)
- [Twitch Setup](#twitch-setup)
  - [Create a Twitch Application](#create-a-twitch-application)
  - [Configure the Redirect URI](#configure-the-redirect-uri)
  - [Get Your Twitch Credentials](#get-your-twitch-credentials)
  - [Configure the Environment Variables](#configure-the-environment-variables)
  - [Choose Your Twitch Channel](#choose-your-twitch-channel)
  - [Twitch OAuth](#twitch-oauth)
  - [Twitch Troubleshooting](#twitch-troubleshooting)
- [YouTube Setup](#youtube-setup)
  - [Create a Google Cloud Project](#create-a-google-cloud-project)
  - [Enable YouTube Data API v3](#enable-youtube-data-api-v3)
  - [Configure OAuth](#configure-oauth)
  - [Add a Test User](#add-a-test-user)
  - [Create OAuth Credentials](#create-oauth-credentials)
  - [Install credentials.json](#install-credentialsjson)
  - [First YouTube Login](#first-youtube-login)
  - [YouTube Token](#youtube-token)
  - [YouTube Troubleshooting](#youtube-troubleshooting)
- [Running the Application](#running-the-application)
- [Common Problems](#common-problems)
- [Final Checklist](#final-checklist)

## Before You Start

Make sure you have completed the installation instructions in [INSTALLATION.md](INSTALLATION.md).

You should be able to run:

```bash
python stream_dashboard.py
```

The application may display errors at this point.

That's expected if you haven't configured the APIs yet.

## Project Files

The important configuration files are:

```text
stream_dashboard.py
.env
credentials.json
youtube_token.json
```

You create `.env` and `credentials.json` yourself.

`youtube_token.json` is created automatically after successful YouTube authentication.

---

# Twitch Setup

## Create a Twitch Application

Open the Twitch Developer Console and sign in with the Twitch account you intend to use.

Create a new application.

The exact wording of Twitch's developer interface may change over time, but you need a normal Twitch application that can use OAuth.

## Configure the Redirect URI

The application currently uses:

```text
http://localhost:3000
```

This is extremely important.

Your Twitch application must use exactly:

```text
http://localhost:3000
```

as its OAuth redirect URI.

The Python application contains:

```python
REDIRECT_URI = "http://localhost:3000"
```

These two values must match.

### Common Redirect URI Mistakes

These are **not** equivalent:

```text
http://localhost:3000
http://localhost:3000/
https://localhost:3000
http://127.0.0.1:3000
```

Use:

```text
http://localhost:3000
```

unless you intentionally change the application code.

## Get Your Twitch Credentials

After creating the Twitch application, obtain:

- Client ID
- Client Secret

The Client Secret is private.

Do not put it directly into your Python source code.

## Configure the Environment Variables

Create or edit:

```text
.env
```

Add:

```env
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret
TWITCH_CHANNEL=your_channel_name
```

For example:

```env
TWITCH_CLIENT_ID=123456789
TWITCH_CLIENT_SECRET=abc123yoursecret
TWITCH_CHANNEL=mychannel
```

Do not commit `.env` to GitHub.

## Choose Your Twitch Channel

`TWITCH_CHANNEL` is the channel login name.

For:

```text
https://www.twitch.tv/examplechannel
```

use:

```env
TWITCH_CHANNEL=examplechannel
```

Do not include:

```text
https://
```

Do not include:

```text
www.twitch.tv/
```

Do not include:

```text
#
```

Just use the login name.

## Twitch OAuth

When the application needs Twitch authentication, it creates a local HTTP server.

The server listens on:

```text
localhost:3000
```

The application then opens your browser.

The authentication flow looks like:

```text
Stream Dashboard
       |
       v
Twitch OAuth
       |
       v
Authorize Application
       |
       v
localhost:3000
       |
       v
Stream Dashboard
```

After successful authentication, the application receives the authorization code and exchanges it for an access token.

## Twitch Troubleshooting

### Browser doesn't open

If your browser doesn't automatically open, check the terminal output.

You can manually open the authentication URL if necessary.

The application uses Python's `webbrowser` module to open the URL.

### `Invalid OAuth state`

Restart the application and try authentication again.

The application generates a random state value for each login attempt.

If the callback doesn't contain the expected state, authentication is rejected.

### Port 3000 is already in use

The Twitch callback server requires port `3000`.

On Linux/macOS, you can check what's using it with:

```bash
lsof -i :3000
```

On Windows:

```powershell
netstat -ano | findstr :3000
```

If another application is using the port, close it and restart Stream Dashboard.

### Twitch says the redirect URI is invalid

Check the Twitch Developer Console.

Make sure it says:

```text
http://localhost:3000
```

Then check the Python source:

```python
REDIRECT_URI = "http://localhost:3000"
```

They must match exactly.

### Twitch channel cannot be found

Check:

```env
TWITCH_CHANNEL=examplechannel
```

Make sure you are using the Twitch login name.

---

# YouTube Setup

The YouTube integration uses Google's OAuth system and the **YouTube Data API v3**.

## Create a Google Cloud Project

Open Google Cloud Console.

Create a new project.

A separate project for Stream Dashboard is recommended.

Give it a recognizable name such as:

```text
Stream Dashboard
```

## Enable YouTube Data API v3

Open the API Library for your project.

Search for:

```text
YouTube Data API v3
```

Enable it.

Without this API enabled, the application cannot retrieve YouTube livestream information or chat.

## Configure OAuth

Open the Google Cloud OAuth configuration for your project.

Configure the OAuth consent screen.

The application requests this scope:

```text
https://www.googleapis.com/auth/youtube.readonly
```

This is a read-only YouTube scope.

The application uses it to read:

- Your live broadcasts
- Live chat
- Viewer statistics
- Basic information needed to identify the active broadcast

It does not need permission to modify your channel.

## Add a Test User

If Google has your OAuth application in testing mode, add the Google account that owns your YouTube channel as a test user.

This is one of the most common causes of confusing Google OAuth errors.

The account you authenticate with should be the account that has access to the YouTube channel you want to monitor.

If you have multiple Google accounts signed into your browser, pay close attention to which account you authorize.

## Create OAuth Credentials

Create a new OAuth client ID.

Choose:

```text
Desktop app
```

Do not create a web application for this project.

The Python code uses:

```python
InstalledAppFlow
```

which is designed for installed/desktop applications.

Download the resulting JSON file.

## Install `credentials.json`

Rename the downloaded OAuth file to:

```text
credentials.json
```

Place it in the same directory as:

```text
stream_dashboard.py
```

Your directory should look like:

```text
stream-dashboard/
├── stream_dashboard.py
├── credentials.json
├── .env
└── ...
```

The application specifically searches for:

```python
YOUTUBE_CREDENTIALS_FILE = "credentials.json"
```

If the file is somewhere else, the application won't find it.

## First YouTube Login

Start the application:

```bash
python stream_dashboard.py
```

When YouTube authentication is required, a browser window will open.

Sign into the Google account associated with your YouTube channel.

Grant the requested permissions.

After authentication, Google redirects the authorization back to the local application.

The application then saves the resulting credentials.

## YouTube Token

After successful authentication, you should see:

```text
youtube_token.json
```

This file is created automatically.

You don't need to create it yourself.

On future launches, the application attempts to reuse the token.

If the token has expired and contains a refresh token, the application attempts to refresh it automatically.

## Delete the Token to Force Login Again

If something has changed with your Google authentication, delete:

```text
youtube_token.json
```

Then start the application again.

This forces a fresh authentication process.

This is particularly useful after:

- Changing Google accounts
- Changing Google Cloud projects
- Creating new OAuth credentials
- Changing OAuth settings
- Revoking application access
- Getting stuck in an authentication loop

# YouTube Troubleshooting

## `credentials.json` not found

Make sure the file is directly beside the Python program:

```text
stream_dashboard.py
credentials.json
```

Not:

```text
credentials/credentials.json
```

unless you modify the Python code.

## Google says the app is unverified

For a personal development project, this can be expected.

Check that your Google account has been added as a test user if the OAuth application is in testing mode.

Do not publish an OAuth application to other users without checking Google's verification requirements.

## Wrong Google account opens

If your browser automatically chooses the wrong account, sign out of the unnecessary Google accounts or use a browser/profile where the correct account is logged in.

The important thing is that the account you authorize has access to the YouTube channel you want to monitor.

## YouTube says there is no active stream

The application searches for a broadcast whose lifecycle status is:

```text
live
```

If your channel is not currently streaming, the application will show:

```text
No active YouTube stream
```

This is normal.

Start your YouTube livestream and wait for the application to detect it.

## YouTube chat is unavailable

There are several possible causes.

Check that:

- The broadcast is actually live.
- Live chat is enabled.
- You authenticated with the correct Google account.
- The authenticated account has access to the channel.
- The YouTube Data API is enabled.

## YouTube viewer count isn't appearing

Viewer statistics are retrieved from the active broadcast.

If the broadcast isn't currently live, there may not be a concurrent viewer count available.

# Running the Application

Once both services are configured:

### Linux / macOS

```bash
source .venv/bin/activate
python stream_dashboard.py
```

### Windows

```powershell
.venv\Scripts\Activate.ps1
python stream_dashboard.py
```

The application will start both network managers in the background.

# Common Problems

## The application opens but Twitch doesn't connect

Check:

```text
.env
```

and verify:

```env
TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
TWITCH_CHANNEL=...
```

Then verify the Twitch redirect URI.

## The application opens but YouTube doesn't connect

Check:

```text
credentials.json
```

and make sure YouTube Data API v3 is enabled.

If you've previously authenticated, try deleting:

```text
youtube_token.json
```

and authenticate again.

## Everything worked previously but stopped working

First try restarting the application.

For YouTube, try removing:

```text
youtube_token.json
```

and authenticating again.

For Twitch, try restarting the Twitch OAuth flow.

If the problem persists, check whether the relevant API credentials or developer application configuration has changed.

# Final Checklist

Before considering the setup complete:

- [ ] Twitch Developer application created
- [ ] Twitch redirect URI set to `http://localhost:3000`
- [ ] Twitch Client ID added to `.env`
- [ ] Twitch Client Secret added to `.env`
- [ ] Twitch channel name added to `.env`
- [ ] Google Cloud project created
- [ ] YouTube Data API v3 enabled
- [ ] Google OAuth consent screen configured
- [ ] Google account added as a test user if required
- [ ] Desktop OAuth credentials created
- [ ] `credentials.json` downloaded
- [ ] `credentials.json` placed beside the Python file
- [ ] Twitch authentication completed
- [ ] YouTube authentication completed
- [ ] `youtube_token.json` created
- [ ] Twitch livestream running
- [ ] YouTube livestream running
- [ ] Twitch chat appears
- [ ] YouTube chat appears
- [ ] Viewer counts update

If all of these work, you're ready to stream.
