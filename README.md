# Stream Dashboard

A desktop dashboard for monitoring **Twitch and YouTube livestreams simultaneously**.

Built with Python, PySide6, PyQtGraph, Twitch EventSub, and the YouTube Data API.

## Table of Contents

## Table of Contents

- [Why I Made This](#why-i-made-this)
- [Features](#features)
- [Screenshots](#screenshots)
- [Technology](#technology)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Setup](#setup)
- [Security](#security)
- [License](#license)
- [Disclaimer](#disclaimer)


## Why I Made This

I wanted to start streaming on both **Twitch and YouTube**, but I couldn't find a dashboard that did what I wanted.

I wanted something simple where I could have both platforms open at the same time and immediately see:

- Both chats
- Viewer counts
- Stream status
- Basic stream analytics

The existing tools I found either focused on one platform, had features I didn't need, or didn't provide the kind of simple desktop dashboard I was looking for.

So I decided to make my own.

The goal was straightforward:

> **One window where I can see both Twitch and YouTube while I'm streaming.**

This project started as a personal tool for my own streams. I decided to put it on GitHub so other people who stream on both platforms can use it, modify it, or build on top of it.

## Features

### Twitch

- Live Twitch chat
- Twitch viewer count
- Twitch EventSub integration
- Twitch OAuth authentication
- Moderator detection
- Automatic username colors
- Stream status

### YouTube

- Live YouTube chat
- YouTube concurrent viewer count
- YouTube Data API integration
- Google OAuth authentication
- Moderator detection
- Automatic username colors
- Stream status

### Analytics

Each platform has its own analytics panel containing:

- Current viewers
- Peak viewers
- Total messages
- Chat messages per minute
- Stream duration
- Viewer history graph
- Chat-rate graph
- Live/offline status

## Screenshots

Screenshots will be added here.

<!--
Add screenshots here later.

Example:

![Stream Dashboard](images/dashboard.png)
-->

## Technology

The application is written in Python and uses:

- **Python** — application logic
- **PySide6** — desktop GUI
- **PyQtGraph** — analytics graphs
- **aiohttp** — asynchronous HTTP requests
- **websockets** — Twitch EventSub connection
- **python-dotenv** — environment configuration
- **Google API Client** — YouTube API access
- **Google OAuth** — YouTube authentication
- **Twitch OAuth** — Twitch authentication
- **Twitch EventSub** — Twitch chat events

## How It Works

The application runs a desktop GUI while network operations run in the background.

### Twitch

Twitch authentication is performed through Twitch OAuth.

After authentication, the application connects to Twitch EventSub and listens for chat events.

The Twitch API is also used to retrieve the current stream and viewer count.

### YouTube

YouTube authentication is handled through Google's OAuth system.

After authentication, the application uses the YouTube Data API to find an active livestream and retrieve its live chat and viewer information.

### Application Architecture

The GUI is built with PySide6.

Network operations run separately from the GUI so that API requests and chat connections don't block the desktop interface.

Qt signals are used to send information from the network components to the appropriate UI panels.

## Installation

See:

**[INSTALLATION.md](INSTALLATION.md)**

The installation guide covers:

- Windows
- macOS
- Linux
- Python setup
- Virtual environments
- Dependency installation
- Running the application

## Setup

After installing the application, Twitch and YouTube need to be configured.

See:

**[SETUP.md](SETUP.md)**

The setup guide covers:

- Twitch Developer application
- Twitch OAuth
- Twitch redirect URI
- Twitch environment variables
- Google Cloud project
- YouTube Data API
- Google OAuth credentials
- `credentials.json`
- `youtube_token.json`
- Authentication troubleshooting
- Common API problems

## Security

This application uses OAuth credentials and authentication tokens.

The following files contain sensitive information and should never be uploaded to GitHub:

```text
.env
credentials.json
youtube_token.json
```
## License

This project is licensed under the **GNU General Public License v3.0**.

See the LICENSE file for the full license text.

GPLv3 allows you to use, modify, and redistribute this software while requiring distributed derivative versions to remain under compatible copyleft terms.

## Disclamer!!

This project is not affiliated with or endorsed by Twitch, YouTube, Google, or any other platform or service mentioned in this repository.

You are responsible for complying with the respective platform's API terms and developer policies when using this software.
