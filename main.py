import sys
import asyncio
import json
import secrets
import threading
import webbrowser
import html
import hashlib
import os
import time

from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode

import aiohttp
import websockets

from dotenv import load_dotenv

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import pyqtgraph as pg


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")

REDIRECT_URI = "http://localhost:3000"

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_URL = "https://api.twitch.tv/helix"
TWITCH_EVENTSUB_URL = "wss://eventsub.wss.twitch.tv/ws"

TWITCH_SCOPES = [
    "user:read:chat",
]

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly"
]

YOUTUBE_CREDENTIALS_FILE = "credentials.json"
YOUTUBE_TOKEN_FILE = "youtube_token.json"


# ============================================================
# ROSÉ PINE MOON
# ============================================================

BASE = "#232136"
SURFACE = "#2a273f"
OVERLAY = "#393552"

BORDER = "#44415a"
BORDER_SOFT = "#36334d"

TEXT = "#e0def4"
MUTED = "#908caa"

LOVE = "#eb6f92"
GOLD = "#f6c177"
ROSE = "#ea9a97"
PINE = "#3e8fb0"
FOAM = "#9ccfd8"
IRIS = "#c4a7e7"

TWITCH_COLOR = IRIS
YOUTUBE_COLOR = LOVE

MODERATOR_COLOR = "#4DA6FF"


# ============================================================
# SIGNALS
# ============================================================

class Signals(QObject):

    twitch_message = Signal(
        str, str, str, bool, str
    )

    twitch_viewers = Signal(int)
    twitch_status = Signal(str)

    youtube_message = Signal(
        str, str, str, bool, str
    )

    youtube_viewers = Signal(int)
    youtube_status = Signal(str)


signals = Signals()


# ============================================================
# TWITCH OAUTH
# ============================================================

oauth_code = None
oauth_error = None
oauth_state = None


class OAuthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        global oauth_code
        global oauth_error

        parsed = urlparse(self.path)

        if parsed.path != "/":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)

        received_state = params.get(
            "state",
            [None]
        )[0]

        code = params.get(
            "code",
            [None]
        )[0]

        error = params.get(
            "error",
            [None]
        )[0]

        if error:

            oauth_error = error

        elif received_state != oauth_state:

            oauth_error = "Invalid OAuth state"

        elif not code:

            oauth_error = "No authorization code received"

        else:

            oauth_code = code

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/html"
        )

        self.end_headers()

        message = f"""
        <html>
        <body style="
            background:{BASE};
            color:{TEXT};
            font-family:sans-serif;
            text-align:center;
            padding:50px;
        ">
            <h1>Authentication complete</h1>
            <p>You can close this window.</p>
        </body>
        </html>
        """

        self.wfile.write(
            message.encode()
        )

    def log_message(
        self,
        format,
        *args
    ):
        pass


def start_oauth_server():

    server = HTTPServer(
        ("localhost", 3000),
        OAuthHandler
    )

    server.handle_request()


async def twitch_login():

    global oauth_code
    global oauth_error
    global oauth_state

    oauth_code = None
    oauth_error = None

    oauth_state = secrets.token_urlsafe(32)

    params = {
        "client_id": TWITCH_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(TWITCH_SCOPES),
        "state": oauth_state,
    }

    auth_url = (
        f"{TWITCH_AUTH_URL}?"
        f"{urlencode(params)}"
    )

    threading.Thread(
        target=start_oauth_server,
        daemon=True,
    ).start()

    signals.twitch_status.emit(
        "Opening Twitch authentication..."
    )

    webbrowser.open(auth_url)

    while (
        oauth_code is None
        and oauth_error is None
    ):
        await asyncio.sleep(0.1)

    if oauth_error:
        raise RuntimeError(oauth_error)

    async with aiohttp.ClientSession() as session:

        data = {
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "code": oauth_code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        }

        async with session.post(
            TWITCH_TOKEN_URL,
            params=data,
        ) as response:

            result = await response.json()

            if response.status != 200:

                raise RuntimeError(
                    f"Twitch token request failed: {result}"
                )

            return result["access_token"]


# ============================================================
# TWITCH API
# ============================================================

async def twitch_api_get(
    endpoint,
    token,
    params=None,
):

    headers = {
        "Authorization": f"Bearer {token}",
        "Client-Id": TWITCH_CLIENT_ID,
    }

    async with aiohttp.ClientSession() as session:

        async with session.get(
            f"{TWITCH_API_URL}{endpoint}",
            headers=headers,
            params=params,
        ) as response:

            result = await response.json()

            if response.status >= 400:

                raise RuntimeError(
                    f"Twitch API error: {result}"
                )

            return result


async def get_twitch_user(token):

    result = await twitch_api_get(
        "/users",
        token,
        {
            "login": TWITCH_CHANNEL
        }
    )

    if not result.get("data"):

        raise RuntimeError(
            f"Twitch channel "
            f"'{TWITCH_CHANNEL}' "
            f"was not found."
        )

    return result["data"][0]


async def get_twitch_viewers(
    token,
    user_id,
):

    result = await twitch_api_get(
        "/streams",
        token,
        {
            "user_id": user_id
        }
    )

    if result.get("data"):

        return result["data"][0]["viewer_count"]

    return 0


# ============================================================
# TWITCH CHAT
# ============================================================

async def twitch_chat(
    token,
    user,
):

    user_id = user["id"]
    channel_name = user["login"]

    signals.twitch_status.emit(
        f"Connecting to #{channel_name}..."
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Client-Id": TWITCH_CLIENT_ID,
        "Content-Type": "application/json",
    }

    async with websockets.connect(
        TWITCH_EVENTSUB_URL
    ) as websocket:

        raw = await websocket.recv()

        welcome = json.loads(raw)

        if (
            welcome["metadata"]["message_type"]
            != "session_welcome"
        ):

            raise RuntimeError(
                "Invalid Twitch EventSub welcome"
            )

        session_id = (
            welcome["payload"]["session"]["id"]
        )

        subscription = {
            "type": "channel.chat.message",
            "version": "1",
            "condition": {
                "broadcaster_user_id": user_id,
                "user_id": user_id,
            },
            "transport": {
                "method": "websocket",
                "session_id": session_id,
            },
        }

        async with aiohttp.ClientSession() as session:

            async with session.post(
                "https://api.twitch.tv/helix/eventsub/subscriptions",
                headers=headers,
                json=subscription,
            ) as response:

                result = await response.json()

                if response.status not in (200, 202):

                    raise RuntimeError(
                        "Could not subscribe to "
                        f"Twitch chat: {result}"
                    )

        signals.twitch_status.emit(
            f"Listening to #{channel_name}"
        )

        async for raw in websocket:

            message = json.loads(raw)

            if (
                message
                .get("metadata", {})
                .get("message_type")
                != "notification"
            ):
                continue

            event = (
                message
                .get("payload", {})
                .get("event", {})
            )

            username = event.get(
                "chatter_user_name",
                "Unknown"
            )

            message_text = (
                event
                .get("message", {})
                .get("text", "")
            )

            username_color = (
                event.get("color")
                or generate_username_color(username)
            )

            badges = event.get(
                "badges",
                []
            )

            is_moderator = any(
                badge.get("set_id") == "moderator"
                for badge in badges
            )

            if is_moderator:
                username_color = MODERATOR_COLOR

            signals.twitch_message.emit(
                username,
                message_text,
                username_color,
                is_moderator,
                "twitch",
            )


async def twitch_manager():

    try:

        if not TWITCH_CLIENT_ID:
            raise RuntimeError(
                "TWITCH_CLIENT_ID missing"
            )

        if not TWITCH_CLIENT_SECRET:
            raise RuntimeError(
                "TWITCH_CLIENT_SECRET missing"
            )

        if not TWITCH_CHANNEL:
            raise RuntimeError(
                "TWITCH_CHANNEL missing"
            )

        token = await twitch_login()

        user = await get_twitch_user(token)

        async def viewer_loop():

            while True:

                try:

                    viewers = (
                        await get_twitch_viewers(
                            token,
                            user["id"]
                        )
                    )

                    signals.twitch_viewers.emit(
                        viewers
                    )

                except Exception as error:

                    print(
                        "Twitch viewer error:",
                        error
                    )

                await asyncio.sleep(10)

        await asyncio.gather(
            twitch_chat(
                token,
                user
            ),
            viewer_loop()
        )

    except Exception as error:

        print(
            "Twitch error:",
            error
        )

        signals.twitch_status.emit(
            f"ERROR: {error}"
        )


# ============================================================
# YOUTUBE AUTH
# ============================================================

def youtube_login():

    credentials = None

    if os.path.exists(
        YOUTUBE_TOKEN_FILE
    ):

        credentials = (
            Credentials
            .from_authorized_user_file(
                YOUTUBE_TOKEN_FILE,
                YOUTUBE_SCOPES,
            )
        )

    if (
        credentials
        and credentials.expired
    ):

        if credentials.refresh_token:

            credentials.refresh(
                Request()
            )

        else:

            credentials = None

    if not credentials:

        flow = (
            InstalledAppFlow
            .from_client_secrets_file(
                YOUTUBE_CREDENTIALS_FILE,
                YOUTUBE_SCOPES,
            )
        )

        credentials = (
            flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent",
            )
        )

        with open(
            YOUTUBE_TOKEN_FILE,
            "w"
        ) as token:

            token.write(
                credentials.to_json()
            )

        os.chmod(
            YOUTUBE_TOKEN_FILE,
            0o600
        )

    return credentials


# ============================================================
# YOUTUBE API
# ============================================================

def get_youtube_broadcast(youtube):

    response = (
        youtube
        .liveBroadcasts()
        .list(
            part=(
                "id,"
                "snippet,"
                "status,"
                "statistics"
            ),
            mine=True,
            maxResults=10,
        )
        .execute()
    )

    broadcasts = response.get(
        "items",
        []
    )

    for broadcast in broadcasts:

        lifecycle = (
            broadcast
            .get("status", {})
            .get("lifeCycleStatus")
        )

        if lifecycle == "live":
            return broadcast

    return None


def youtube_chat_loop():

    signals.youtube_status.emit(
        "Authenticating with YouTube..."
    )

    credentials = youtube_login()

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    signals.youtube_status.emit(
        "Connected to YouTube"
    )

    while True:

        try:

            broadcast = get_youtube_broadcast(
                youtube
            )

            if not broadcast:

                signals.youtube_status.emit(
                    "No active YouTube stream"
                )

                signals.youtube_viewers.emit(0)

                time.sleep(15)

                continue

            live_chat_id = (
                broadcast
                .get("snippet", {})
                .get("liveChatId")
            )

            if not live_chat_id:

                signals.youtube_status.emit(
                    "YouTube chat unavailable"
                )

                time.sleep(10)

                continue

            statistics = broadcast.get(
                "statistics",
                {}
            )

            viewers = statistics.get(
                "concurrentViewers"
            )

            if viewers is not None:

                signals.youtube_viewers.emit(
                    int(viewers)
                )

            signals.youtube_status.emit(
                "Listening to YouTube chat"
            )

            page_token = None

            while True:

                request = (
                    youtube
                    .liveChatMessages()
                    .list(
                        liveChatId=live_chat_id,
                        part=(
                            "snippet,"
                            "authorDetails"
                        ),
                        maxResults=200,
                        pageToken=page_token,
                    )
                )

                response = request.execute()

                for item in response.get(
                    "items",
                    []
                ):

                    snippet = item.get(
                        "snippet",
                        {}
                    )

                    author = item.get(
                        "authorDetails",
                        {}
                    )

                    username = author.get(
                        "displayName",
                        "Unknown"
                    )

                    message_text = snippet.get(
                        "displayMessage",
                        ""
                    )

                    is_moderator = (
                        author.get(
                            "isChatModerator",
                            False
                        )
                    )

                    if is_moderator:

                        username_color = (
                            MODERATOR_COLOR
                        )

                    else:

                        username_color = (
                            generate_username_color(
                                username
                            )
                        )

                    signals.youtube_message.emit(
                        username,
                        message_text,
                        username_color,
                        is_moderator,
                        "youtube",
                    )

                page_token = response.get(
                    "nextPageToken"
                )

                polling_interval = response.get(
                    "pollingIntervalMillis",
                    5000
                )

                if not page_token:
                    break

                time.sleep(
                    polling_interval / 1000
                )

        except Exception as error:

            print(
                "YouTube error:",
                error
            )

            signals.youtube_status.emit(
                f"ERROR: {error}"
            )

            time.sleep(10)


async def youtube_manager():

    loop = asyncio.get_running_loop()

    await loop.run_in_executor(
        None,
        youtube_chat_loop,
    )


# ============================================================
# USERNAME COLORS
# ============================================================

def generate_username_color(username):

    colors = [
        LOVE,
        GOLD,
        ROSE,
        PINE,
        FOAM,
        IRIS,
    ]

    digest = hashlib.md5(
        username.lower().encode()
    ).hexdigest()

    index = (
        int(digest[:8], 16)
        % len(colors)
    )

    return colors[index]


# ============================================================
# ANALYTICS PANEL
# ============================================================

class AnalyticsPanel(QWidget):

    def __init__(
        self,
        platform_color,
    ):

        super().__init__()

        self.platform_color = platform_color

        self.current_viewers = 0
        self.peak_viewers = 0

        self.messages = 0

        self.message_times = deque(
            maxlen=300
        )

        self.stream_start = None
        self.stream_id = None
        self.stream_live = False

        self.viewer_history = deque(
            maxlen=360
        )

        self.viewer_times = deque(
            maxlen=360
        )

        self.chat_rate_history = deque(
            maxlen=360
        )

        self.chat_rate_times = deque(
            maxlen=360
        )

        self.current_value = self.make_value()
        self.peak_value = self.make_value()
        self.messages_value = self.make_value()
        self.rate_value = self.make_value()
        self.duration_value = self.make_value()
        self.status_value = self.make_value()

        self.viewer_plot = self.create_plot(
            "Concurrent viewers"
        )

        self.chat_plot = self.create_plot(
            "Chat rate"
        )

        self.viewer_curve = (
            self.viewer_plot.plot(
                [],
                [],
                pen=pg.mkPen(
                    color=platform_color,
                    width=2,
                ),
            )
        )

        self.chat_curve = (
            self.chat_plot.plot(
                [],
                [],
                pen=pg.mkPen(
                    color=IRIS,
                    width=2,
                ),
            )
        )

        layout = QVBoxLayout()

        layout.setContentsMargins(
            14,
            14,
            14,
            14
        )

        layout.setSpacing(8)

        layout.addWidget(
            self.section_title("STREAM")
        )

        layout.addWidget(
            self.metric_row(
                "Status",
                self.status_value
            )
        )

        layout.addWidget(
            self.metric_row(
                "Duration",
                self.duration_value
            )
        )

        layout.addSpacing(10)

        layout.addWidget(
            self.section_title("VIEWERS")
        )

        layout.addWidget(
            self.metric_row(
                "Current",
                self.current_value
            )
        )

        layout.addWidget(
            self.metric_row(
                "Peak",
                self.peak_value
            )
        )

        layout.addWidget(
            self.viewer_plot
        )

        layout.addSpacing(10)

        layout.addWidget(
            self.section_title("CHAT")
        )

        layout.addWidget(
            self.metric_row(
                "Messages",
                self.messages_value
            )
        )

        layout.addWidget(
            self.metric_row(
                "Rate",
                self.rate_value
            )
        )

        layout.addWidget(
            self.chat_plot
        )

        layout.addStretch()

        self.setLayout(layout)

        self.setStyleSheet(
            f"""
            QWidget {{
                background: {SURFACE};
            }}
            """
        )

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.update_stats
        )

        self.timer.start(1000)

    # --------------------------------------------------------
    # UI helpers
    # --------------------------------------------------------

    def section_title(self, text):

        label = QLabel(text)

        label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.platform_color};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                padding-bottom: 3px;
            }}
            """
        )

        return label

    def make_value(self):

        label = QLabel("—")

        label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 18px;
                font-weight: bold;
            }}
            """
        )

        return label

    def metric_row(
        self,
        name,
        value,
    ):

        row = QWidget()

        layout = QHBoxLayout()

        layout.setContentsMargins(
            4,
            3,
            4,
            3
        )

        label = QLabel(name)

        label.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 12px;
            }}
            """
        )

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(value)

        row.setLayout(layout)

        return row

    # --------------------------------------------------------
    # Graphs
    # --------------------------------------------------------

    def create_plot(self, title):

        plot = pg.PlotWidget(
            background=BASE
        )

        plot.setMinimumHeight(150)

        plot.setStyleSheet(
            f"""
            QWidget {{
                border: 1px solid {BORDER_SOFT};
                border-radius: 5px;
            }}
            """
        )

        plot.showGrid(
            x=True,
            y=True,
            alpha=0.12
        )

        plot.setMouseEnabled(
            x=False,
            y=False
        )

        plot.setMenuEnabled(False)
        plot.hideButtons()

        plot.setLabel(
            "left",
            title,
            color=MUTED
        )

        plot.getAxis(
            "left"
        ).setTextPen(
            pg.mkPen(MUTED)
        )

        plot.getAxis(
            "bottom"
        ).setTextPen(
            pg.mkPen(MUTED)
        )

        plot.getAxis(
            "left"
        ).setPen(
            pg.mkPen(BORDER)
        )

        plot.getAxis(
            "bottom"
        ).setPen(
            pg.mkPen(BORDER)
        )

        return plot

    # --------------------------------------------------------
    # Stream lifecycle
    # --------------------------------------------------------

    def start_stream(
        self,
        stream_id,
        start_time,
    ):

        if (
            self.stream_id == stream_id
            and self.stream_live
        ):
            return

        self.stream_id = stream_id
        self.stream_start = start_time
        self.stream_live = True

        self.current_viewers = 0
        self.peak_viewers = 0

        self.messages = 0
        self.message_times.clear()

        self.viewer_history.clear()
        self.viewer_times.clear()

        self.chat_rate_history.clear()
        self.chat_rate_times.clear()

        self.current_value.setText("0")
        self.peak_value.setText("0")
        self.messages_value.setText("0")
        self.rate_value.setText("0/min")
        self.duration_value.setText("00:00:00")
        self.status_value.setText("LIVE")

        self.viewer_curve.setData([], [])
        self.chat_curve.setData([], [])

    def stop_stream(self):

        if not self.stream_live:
            return

        self.stream_live = False

        self.status_value.setText(
            "OFFLINE"
        )

    # --------------------------------------------------------
    # Data
    # --------------------------------------------------------

    def set_viewers(self, count):

        self.current_viewers = count

        if count > self.peak_viewers:
            self.peak_viewers = count

        self.current_value.setText(
            f"{count:,}"
        )

        self.peak_value.setText(
            f"{self.peak_viewers:,}"
        )

        if self.stream_live:

            elapsed = self.elapsed_seconds()

            self.viewer_times.append(
                elapsed
            )

            self.viewer_history.append(
                count
            )

    def add_message(self):

        self.messages += 1

        self.message_times.append(
            time.time()
        )

        self.messages_value.setText(
            f"{self.messages:,}"
        )

    def set_status(self, status):

        self.status_value.setText(
            status
        )

    # --------------------------------------------------------
    # Timing
    # --------------------------------------------------------

    def elapsed_seconds(self):

        if self.stream_start is None:
            return 0

        return max(
            0,
            time.time() - self.stream_start
        )

    # --------------------------------------------------------
    # Statistics update
    # --------------------------------------------------------

    def update_stats(self):

        now = time.time()

        while (
            self.message_times
            and self.message_times[0] < now - 60
        ):

            self.message_times.popleft()

        rate = len(
            self.message_times
        )

        self.rate_value.setText(
            f"{rate}/min"
        )

        if self.stream_live:

            elapsed = self.elapsed_seconds()

            self.chat_rate_times.append(
                elapsed
            )

            self.chat_rate_history.append(
                rate
            )

            elapsed_int = int(elapsed)

            hours, remainder = divmod(
                elapsed_int,
                3600
            )

            minutes, seconds = divmod(
                remainder,
                60
            )

            self.duration_value.setText(
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        if self.viewer_history:

            self.viewer_curve.setData(
                list(self.viewer_times),
                list(self.viewer_history)
            )

            latest = self.viewer_times[-1]

            self.viewer_plot.setXRange(
                max(0, latest - 1800),
                max(1800, latest),
                padding=0
            )

        if self.chat_rate_history:

            self.chat_curve.setData(
                list(self.chat_rate_times),
                list(self.chat_rate_history)
            )

            latest = self.chat_rate_times[-1]

            self.chat_plot.setXRange(
                max(0, latest - 1800),
                max(1800, latest),
                padding=0
            )


# ============================================================
# CHAT PANEL
# ============================================================

class ChatPanel(QWidget):

    def __init__(
        self,
        platform,
        color,
    ):

        super().__init__()

        self.platform = platform
        self.platform_color = color

        self.analytics = AnalyticsPanel(
            color
        )

        # ----------------------------------------------------
        # Viewer count
        # ----------------------------------------------------

        self.viewer_label = QLabel(
            "— viewers"
        )

        self.viewer_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 13px;
                font-weight: bold;
            }}
            """
        )

        # ----------------------------------------------------
        # Chat
        
# ----------------------------------------------------

        self.chat = QTextEdit()

        self.chat.setReadOnly(True)

        self.chat.setStyleSheet(
            f"""
            QTextEdit {{
                background: {BASE};
                color: {TEXT};
                border: none;
                padding: 10px;
                font-size: 14px;
            }}
            """
        )

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = QHBoxLayout()

        header.setContentsMargins(
            12,
            9,
            12,
            9
        )

        title = QLabel(
            platform.upper()
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            """
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.viewer_label)

        header_widget = QWidget()

        header_widget.setLayout(header)

        header_widget.setStyleSheet(
            f"""
            QWidget {{
                background: {SURFACE};
                border-bottom: 1px solid {BORDER};
            }}
            """
        )

        # ----------------------------------------------------
        # Tabs
        # ----------------------------------------------------

        self.chat_button = QPushButton(
            "Chat"
        )

        self.analytics_button = QPushButton(
            "Analytics"
        )

        for button in (
            self.chat_button,
            self.analytics_button,
        ):

            button.setCheckable(True)

        self.chat_button.setChecked(True)

        self.chat_button.clicked.connect(
            lambda: self.show_tab(0)
        )

        self.analytics_button.clicked.connect(
            lambda: self.show_tab(1)
        )

        tabs = QHBoxLayout()

        tabs.setContentsMargins(
            10,
            7,
            10,
            7
        )

        tabs.setSpacing(4)

        tabs.addWidget(
            self.chat_button
        )

        tabs.addWidget(
            self.analytics_button
        )

        tabs.addStretch()

        tabs_widget = QWidget()

        tabs_widget.setLayout(tabs)

        tabs_widget.setStyleSheet(
            f"""
            QWidget {{
                background: {SURFACE};
                border-bottom: 1px solid {BORDER};
            }}
            """
        )

        # ----------------------------------------------------
        # Stack
        # ----------------------------------------------------

        self.stack = QStackedWidget()

        self.stack.addWidget(
            self.chat
        )

        self.stack.addWidget(
            self.analytics
        )

        self.stack.setStyleSheet(
            f"""
            QStackedWidget {{
                background: {BASE};
            }}
            """
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.status = QLabel(
            "Starting..."
        )

        self.status.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                background: {SURFACE};
                border-top: 1px solid {BORDER};
                padding: 7px 10px;
                font-size: 11px;
            }}
            """
        )

        # ----------------------------------------------------
        # Main layout
        # ----------------------------------------------------

        layout = QVBoxLayout()

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(0)

        layout.addWidget(
            header_widget
        )

        layout.addWidget(
            tabs_widget
        )

        layout.addWidget(
            self.stack
        )

        layout.addWidget(
            self.status
        )

        self.setLayout(layout)

        # ----------------------------------------------------
        # Panel stylesheet
        # ----------------------------------------------------

        self.setStyleSheet(
            f"""
            QWidget {{
                background: {BASE};
            }}

            QPushButton {{
                background: {SURFACE};
                color: {MUTED};
                border: 1px solid {BORDER_SOFT};
                padding: 7px 18px;
                border-radius: 5px;
                font-size: 13px;
            }}

            QPushButton:hover {{
                background: {OVERLAY};
                color: {TEXT};
                border-color: {BORDER};
            }}

            QPushButton:checked {{
                background: {OVERLAY};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-bottom: 2px solid {color};
            }}
            """
        )

    # --------------------------------------------------------
    # Tabs
    # --------------------------------------------------------

    def show_tab(self, index):

        self.stack.setCurrentIndex(
            index
        )

        self.chat_button.setChecked(
            index == 0
        )

        self.analytics_button.setChecked(
            index == 1
        )

    # --------------------------------------------------------
    # Chat messages
    # --------------------------------------------------------

    def add_message(
        self,
        username,
        message,
        username_color,
        is_moderator,
        platform,
    ):

        self.analytics.add_message()

        timestamp = datetime.now().strftime(
            "%H:%M"
        )

        safe_username = html.escape(
            username
        )

        safe_message = html.escape(
            message
        )

        safe_color = html.escape(
            username_color
        )

        moderator_badge = ""

        if is_moderator:

            moderator_badge = (
                '<span style="'
                f'color:{MODERATOR_COLOR};'
                'font-weight:bold;'
                '">MOD</span> '
            )

        formatted = (
            f'<span style="'
            f'color:{MUTED};'
            f'">[{timestamp}]</span> '

            f'{moderator_badge}'

            f'<span style="'
            f'color:{safe_color};'
            f'font-weight:bold;'
            f'">'
            f'{safe_username}'
            f'</span>'

            f'<span style="'
            f'color:{MUTED};'
            f'">:</span> '

            f'<span style="'
            f'color:{TEXT};'
            f'">'
            f'{safe_message}'
            f'</span>'
        )

        self.chat.append(
            formatted
        )

        cursor = self.chat.textCursor()

        cursor.movePosition(
            QTextCursor.MoveOperation.End
        )

        self.chat.setTextCursor(
            cursor
        )

    # --------------------------------------------------------
    # Viewers
    # --------------------------------------------------------

    def set_viewers(self, count):

        self.viewer_label.setText(
            f"{count:,} viewers"
        )

        self.analytics.set_viewers(
            count
        )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    def set_status(self, text):

        self.status.setText(text)

        self.analytics.set_status(
            text
        )


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Stream Dashboard"
        )

        self.resize(
            1200,
            800
        )

        # ----------------------------------------------------
        # Panels
        # ----------------------------------------------------

        self.twitch = ChatPanel(
            "Twitch",
            TWITCH_COLOR
        )

        self.youtube = ChatPanel(
            "YouTube",
            YOUTUBE_COLOR
        )

        # ----------------------------------------------------
        # Vertical divider
        # ----------------------------------------------------

        divider = QFrame()

        divider.setFrameShape(
            QFrame.Shape.VLine
        )

        divider.setFrameShadow(
            QFrame.Shadow.Plain
        )

        divider.setFixedWidth(1)

        divider.setStyleSheet(
            f"""
            QFrame {{
                background: {BORDER};
                border: none;
            }}
            """
        )

        # ----------------------------------------------------
        # Main layout
        # ----------------------------------------------------

        layout = QHBoxLayout()

        layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        layout.setSpacing(8)

        layout.addWidget(
            self.twitch
        )

        layout.addWidget(
            divider
        )

        layout.addWidget(
            self.youtube
        )

        layout.setStretch(
            0,
            1
        )

        layout.setStretch(
            2,
            1
        )

        central = QWidget()

        central.setLayout(layout)

        self.setCentralWidget(
            central
        )

        # ----------------------------------------------------
        # Main stylesheet
        # ----------------------------------------------------

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {BASE};
            }}

            QWidget {{
                background: {BASE};
            }}

            QToolTip {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                padding: 5px;
            }}
            """
        )

        # ----------------------------------------------------
        # Signals
        # ----------------------------------------------------

        signals.twitch_message.connect(
            self.twitch.add_message
        )

        signals.twitch_viewers.connect(
            self.twitch.set_viewers
        )

        signals.twitch_status.connect(
            self.twitch.set_status
        )

        signals.youtube_message.connect(
            self.youtube.add_message
        )

        signals.youtube_viewers.connect(
            self.youtube.set_viewers
        )

        signals.youtube_status.connect(
            self.youtube.set_status
        )


# ============================================================
# NETWORK
# ============================================================

async def network_manager():

    await asyncio.gather(
        twitch_manager(),
        youtube_manager(),
    )


def run_network():

    asyncio.run(
        network_manager()
    )


# ============================================================
# START
# ============================================================

def main():

    app = QApplication(sys.argv)

    app.setApplicationName(
        "Stream Dashboard"
    )

    window = MainWindow()

    window.show()

    network_thread = threading.Thread(
        target=run_network,
        daemon=True,
    )

    network_thread.start()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
