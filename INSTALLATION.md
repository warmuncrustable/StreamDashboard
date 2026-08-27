# Installation

This guide covers the basic installation of Stream Dashboard.

For Twitch and YouTube configuration, OAuth setup, API configuration, and troubleshooting, see **[SETUP.md](SETUP.md)**.

## Table of Contents

- [Requirements](#requirements)
- [Releases]_(#releases)
- [Linux](#linux)
  - [Clone the Repository](#clone-the-repository)
  - [Create a Virtual Environment](#create-a-virtual-environment)
  - [Install Dependencies](#install-dependencies)
  - [Run the Application](#run-the-application)
- [macOS](#macos)
  - [Clone the Repository](#clone-the-repository-1)
  - [Check Python](#check-python)
  - [Create a Virtual Environment](#create-a-virtual-environment-1)
  - [Install Dependencies](#install-dependencies-1)
  - [Run the Application](#run-the-application-1)
- [Windows](#windows)
  - [Clone the Repository](#clone-the-repository-2)
  - [Check Python](#check-python-1)
  - [Create a Virtual Environment](#create-a-virtual-environment-2)
  - [Install Dependencies](#install-dependencies-2)
  - [Run the Application](#run-the-application-2)
- [Quick Installation](#quick-installation)
- [curl](#curl)
- [After Installation](#after-installation)

## Requirements

You need:

- Python 3.10 or newer
- Git
- An internet connection

The application runs locally on your computer.

# Releases

If you don't need the latest development changes, the easiest way to install Stream Dashboard is to download a precompiled release.

Precompiled binaries are available from the project's GitHub Releases page.

Download the appropriate package for your operating system and architecture, extract it if necessary, and run the application.

> Release builds do not require Python or the project's Python dependencies to be installed separately.

For the latest features and fixes that have not yet been released, manually install the application for your system via the instructions below 

**These binaries are only compiled for Windows and Linux, do not complain about the binaries not working on your system if you are not using windows or linux, i gave manual install instructions for a reason**

# Linux

## Clone the Repository

Open a terminal and clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace the URL with the actual repository URL.

## Create a Virtual Environment

Create the virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

You should now see something similar to:

```text
(.venv) user@computer:~/stream-dashboard$
```

## Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

The requirements file contains the application's dependencies, including:

- PySide6
- PyQtGraph
- aiohttp
- websockets
- python-dotenv
- Google API libraries

## Run the Application

```bash
python stream_dashboard.py
```

If the installation was successful, the application window should open.

# macOS

## Clone the Repository

Open Terminal:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

## Check Python

Make sure Python 3.10 or newer is installed:

```bash
python3 --version
```

## Create a Virtual Environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
python stream_dashboard.py
```

If macOS asks for permission related to Python or the application opening a local window, allow it.

# Windows

## Clone the Repository

Open PowerShell:

```powershell
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

## Check Python

Run:

```powershell
python --version
```

You should have Python 3.10 or newer.

## Create a Virtual Environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

## Install Dependencies

```powershell
pip install -r requirements.txt
```

## Run the Application

```powershell
python stream_dashboard.py
```

If PowerShell prevents the activation script from running, you can use the virtual environment directly:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then:

```powershell
.venv\Scripts\python.exe stream_dashboard.py
```

# Quick Installation

If you already have Python and Git installed, use the following.

## Linux / macOS

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python stream_dashboard.py
```

## Windows

```powershell
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python stream_dashboard.py
```

# curl

If you specifically want to download the repository using `curl`, you can download the repository archive:

```bash
curl -L https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/archive/refs/heads/main.zip -o stream-dashboard.zip
```

Extract the downloaded archive and enter the project directory.

Then follow the dependency installation instructions for your operating system above.

> `curl` only downloads the project. It does not install Python or the project's dependencies.

# After Installation

At this point, the application itself is installed.

It will **not** be fully functional until Twitch and YouTube have been configured.

Continue to:

**[SETUP.md](SETUP.md)**
