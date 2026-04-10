import threading
import urllib.request
import socket
import time

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import (Color, RoundedRectangle, Rectangle,
                            Ellipse, Line)
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp
import math

# Android imports
try:
    from android.permissions import request_permissions, Permission
    from jnius import autoclass

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    NotificationManager = autoclass('android.app.NotificationManager')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
    NotificationCompatBuilder = autoclass(
        'androidx.core.app.NotificationCompat$Builder')
    PendingIntent = autoclass('android.app.PendingIntent')
    Intent = autoclass('android.content.Intent')
    Build = autoclass('android.os.Build')
    ANDROID = True
except Exception:
    ANDROID = False

Window.clearcolor = get_color_from_hex('#070B18')

CHANNEL_ID = 'vpn_shield_channel'
NOTIF_ID_PERSISTENT = 1
NOTIF_ID_ALERT = 2

C_BG = '#070B18'
C_CARD = '#0D1425'
C_CYAN = '#00D4FF'
C_GREEN = '#00FF88'
C_RED = '#FF2D55'
C_YELLOW = '#FFD60A'
C_GRAY = '#1C2744'
C_TEXT_DIM = '#3A4F6A'
C_TEXT_MID = '#5A7A9A'


# ─────────────────────────────────────────────
#  ANDROID NOTIFICATION HELPER
# ─────────────────────────────────────────────
class Notifier:
    _manager = None
    _ctx = None
    _ready = False

    @classmethod
    def init(cls):
        if not ANDROID:
            cls._ready = False
            return
        try:
            cls._ctx = PythonActivity.mActivity
            cls._manager = cls._ctx.getSystemService(
                Context.NOTIFICATION_SERVICE)
            if Build.VERSION.SDK_INT >= 26:
                ch = NotificationChannel(
                    CHANNEL_ID,
                    'VPN Shield',
                    NotificationManager.IMPORTANCE_HIGH
                )
                ch.setDescription('VPN IP monitoring')
                cls._manager.createNotificationChannel(ch)
            cls._ready = True
        except Exception as e:
            print(f'Notifier.init error: {e}')
            cls._ready = False

    @classmethod
    def _build(cls, title, body, priority, ongoing=False, icon=None):
        if not cls._ready:
            return None
        try:
            builder = NotificationCompatBuilder(cls._ctx, CHANNEL_ID)
            builder.setContentTitle(title)
            builder.setContentText(body)
            builder.setSmallIcon(
                cls._ctx.getApplicationInfo().icon
            )
            builder.setPriority(priority)
            builder.setOngoing(ongoing)
            builder.setAutoCancel(not ongoing)
            builder.setStyle(
                autoclass(
                    'androidx.core.app.NotificationCompat$BigTextStyle'
                )().bigText(body)
            )
            return builder.build()
        except Exception as e:
            print(f'Notifier._build error: {e}')
            return None

    @classmethod
    def persistent(cls, title, body):
        """Always-visible notification in status bar."""
        if not cls._ready:
            print(f'[NOTIF persistent] {title}: {body}')
            return
        try:
            n = cls._build(
                title, body,
                NotificationCompat.PRIORITY_LOW,
                ongoing=True
            )
            if n:
                cls._manager.notify(NOTIF_ID_PERSISTENT, n)
        except Exception as e:
            print(f'Notifier.persistent error: {e}')

    @classmethod
    def alert(cls, title, body):
        """Pop-up alert notification."""
        if not cls._ready:
            print(f'[NOTIF alert] {title}: {body}')
            return
        try:
            n = cls._build(
                title, body,
                NotificationCompat.PRIORITY_HIGH,
                ongoing=False
            )
            if n:
                cls._manager.notify(NOTIF_ID_ALERT, n)
        except Exception as e:
            print(f'Notifier.alert error: {e}')

    @classmethod
    def cancel(cls, notif_id):
        if cls._ready:
            try:
                cls._manager.cancel(notif_id)
            except:
                pass


# ─────────────────────────────────────────────
#  CUSTOM WIDGETS
# ─────────────────────────────────────────────
class RoundCard(BoxLayout):
    def __init__(self, radius=24, border_color=None,
                 bg_color=None, **kwargs):
        super().__init__(**kwargs)
        self._radius = radius
        self._border = border_color or get_color_from_hex(C_CYAN)
        self._bg = bg_color or get_color_from_hex(C_CARD)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            # Shadow
            Color(0, 0, 0, 0.4)
            RoundedRectangle(
                pos=(self.x + 3, self.y - 3),
                size=self.size,
                radius=[self._radius]
            )
            # BG
            Color(*self._bg)
            RoundedRectangle(
                pos=self.pos, size=self.size,
                radius=[self._radius]
            )
            # Border glow outer
            r, g, b, _ = self._border
            Color(r, g, b, 0.08)
            RoundedRectangle(
                pos=(self.x - 2, self.y - 2),
                size=(self.width + 4, self.height + 4),
                radius=[self._radius + 2]
            )
            # Border
            Color(r, g, b, 0.5)
            Line(
                rounded_rectangle=(
                    self.x + 1, self.y + 1,
                    self.width - 2, self.height - 2,
                    self._radius
                ),
                width=1.4
            )

    def set_border(self, color_hex):
        self._border = get_color_from_hex(color_hex)
        self._draw()


class NeonButton(Button):
    def __init__(self, neon=C_CYAN, **kwargs):
        super().__init__(**kwargs)
        self._neon = get_color_from_hex(neon)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''
        self.color = (1, 1, 1, 1)
        self.font_size = sp(16)
        self.bold = True
        self._pressed = False
        self.bind(pos=self._draw, size=self._draw)
        self.bind(on_press=self._press, on_release=self._release)

    def _press(self, *a):
        self._pressed = True
        self._draw()

    def _release(self, *a):
        self._pressed = False
        self._draw()

    def _draw(self, *a):
        self.canvas.before.clear()
        r, g, b, _ = self._neon
        alpha = 0.95 if self._pressed else 0.7
        fill_a = 0.25 if self._pressed else 0.12
        with self.canvas.before:
            # Outer glow
            Color(r, g, b, 0.1)
            RoundedRectangle(
                pos=(self.x - 5, self.y - 5),
                size=(self.width + 10, self.height + 10),
                radius=[22]
            )
            # Fill
            Color(r, g, b, fill_a)
            RoundedRectangle(
                pos=self.pos, size=self.size, radius=[18]
            )
            # Border
            Color(r, g, b, alpha)
            Line(
                rounded_rectangle=(
                    self.x + 1, self.y + 1,
                    self.width - 2, self.height - 2, 18
                ),
                width=1.8
            )

    def set_neon(self, color_hex):
        self._neon = get_color_from_hex(color_hex)
        self._draw()


class PulseRing(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._t = 0
        self._active = False
        self._color = get_color_from_hex(C_GREEN)
        Clock.schedule_interval(self._tick, 1 / 30)
        self.bind(pos=self._draw, size=self._draw)

    def set_state(self, active, color_hex):
        self._active = active
        self._color = get_color_from_hex(color_hex)

    def _tick(self, dt):
        self._t += dt
        self._draw()

    def _draw(self, *a):
        self.canvas.clear()
        cx = self.center_x
        cy = self.center_y
        base_r = min(self.width, self.height) * 0.28
        r, g, b, _ = self._color
        t = self._t

        with self.canvas:
            # Animated outer rings
            for i in range(3):
                phase = t * 1.2 - i * 0.5
                ring_a = max(0, 0.18 - i * 0.05) * (
                    0.5 + 0.5 * math.sin(phase)
                )
                ring_r = base_r + 14 + i * 14 + 6 * math.sin(
                    phase + i
                )
                Color(r, g, b, ring_a)
                Ellipse(
                    pos=(cx - ring_r, cy - ring_r),
                    size=(ring_r * 2, ring_r * 2)
                )

            # Mid glow
            Color(r, g, b, 0.15)
            Ellipse(
                pos=(cx - base_r - 8, cy - base_r - 8),
                size=((base_r + 8) * 2, (base_r + 8) * 2)
            )

            # Core circle
            Color(r, g, b, 0.9)
            Ellipse(
                pos=(cx - base_r, cy - base_r),
                size=(base_r * 2, base_r * 2)
            )

            # Inner shine
            Color(1, 1, 1, 0.2)
            sr = base_r * 0.38
            Ellipse(
                pos=(cx - sr * 0.6, cy + base_r * 0.2),
                size=(sr, sr * 0.55)
            )

            # Center icon text drawn via canvas trick
            # (status icon is handled by Label overlay)


class StarField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stars = []
        self._t = 0
        Clock.schedule_interval(self._tick, 1 / 15)
        self.bind(size=self._init_stars)

    def _init_stars(self, *a):
        import random
        random.seed(42)
        self._stars = [
            {
                'x': random.random(),
                'y': random.random(),
                'r': random.uniform(0.6, 2.2),
                'speed': random.uniform(0.3, 1.2),
                'phase': random.uniform(0, math.pi * 2),
                'cyan': random.random() > 0.6,
            }
            for _ in range(55)
        ]

    def _tick(self, dt):
        self._t += dt
        self._draw()

    def _draw(self, *a):
        self.canvas.clear()
        with self.canvas:
            for s in self._stars:
                a = 0.08 + 0.2 * math.sin(
                    self._t * s['speed'] + s['phase']
                )
                if s['cyan']:
                    Color(0, 0.83, 1, a)
                else:
                    Color(0.6, 0.8, 1, a * 0.6)
                sx = self.x + s['x'] * self.width
                sy = self.y + s['y'] * self.height
                r = s['r']
                Ellipse(
                    pos=(sx - r, sy - r),
                    size=(r * 2, r * 2)
                )


# ─────────────────────────────────────────────
#  MAIN UI
# ─────────────────────────────────────────────
class MainScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._original_ip = None
        self._current_ip = None
        self._protected = False
        self._monitoring = False
        self._monitor_event = None
        self._check_lock = threading.Lock()
        self._build()
        Notifier.init()
        Clock.schedule_once(self._first_check, 0.8)

    # ── BUILD ──────────────────────────────────
    def _build(self):
        # Stars bg
        self.stars = StarField(
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(self.stars)

        # Subtle grid overlay
        self._grid = Widget(
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}
        )
        self._grid.bind(size=self._draw_grid, pos=self._draw_grid)
        self.add_widget(self._grid)

        root = BoxLayout(
            orientation='vertical',
            padding=[dp(18), dp(44), dp(18), dp(24)],
            spacing=dp(14),
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )

        # ── HEADER
        hdr = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(62),
            spacing=dp(2)
        )
        lbl_title = Label(
            text='VPN SHIELD',
            font_size=sp(30),
            bold=True,
            color=get_color_from_hex(C_CYAN),
            halign='center'
        )
        lbl_sub = Label(
            text='IP PROTECTION MONITOR',
            font_size=sp(11),
            color=get_color_from_hex(C_TEXT_DIM),
            halign='center',
            letter_spacing=dp(3)
        )
        hdr.add_widget(lbl_title)
        hdr.add_widget(lbl_sub)
        root.add_widget(hdr)

        # ── PULSE CARD (big)
        pulse_card = RoundCard(
            orientation='overlay',
            size_hint_y=None,
            height=dp(210),
            padding=dp(10)
        )
        self.pulse_ring = PulseRing(size_hint=(1, 1))
        pulse_card.add_widget(self.pulse_ring)

        self.lbl_shield = Label(
            text='◉',
            font_size=sp(36),
            bold=True,
            color=get_color_from_hex(C_TEXT_DIM),
            halign='center',
            valign='center',
            size_hint=(1, 1)
        )
        self.lbl_shield.bind(
            size=self.lbl_shield.setter('text_size')
        )
        pulse_card.add_widget(self.lbl_shield)
        root.add_widget(pulse_card)

        # ── STATUS TEXT (big)
        self.lbl_status = Label(
            text='INITIALIZING',
            font_size=sp(22),
            bold=True,
            color=get_color_from_hex(C_TEXT_MID),
            halign='center',
            size_hint_y=None,
            height=dp(36)
        )
        root.add_widget(self.lbl_status)

        # ── IP CARDS ROW
        ip_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(100),
            spacing=dp(12)
        )

        # Original IP card
        orig_card = RoundCard(
            orientation='vertical',
            padding=[dp(14), dp(10)],
            spacing=dp(4),
            border_color=get_color_from_hex(C_TEXT_DIM)
        )
        Label(
            text='ORIGINAL IP',
            font_size=sp(9),
            color=get_color_from_hex(C_TEXT_DIM),
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(18)
        ).let(lambda l: orig_card.add_widget(l)) if False else None
        lbl_orig_top = Label(
            text='ORIGINAL IP',
            font_size=sp(9),
            color=get_color_from_hex(C_TEXT_DIM),
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(18)
        )
        self.lbl_orig_ip = Label(
            text='Not saved',
            font_size=sp(13),
            bold=True,
            color=get_color_from_hex(C_TEXT_MID),
            halign='center',
            size_hint_y=1
        )
        orig_card.add_widget(lbl_orig_top)
        orig_card.add_widget(self.lbl_orig_ip)

        # Current IP card
        curr_card = RoundCard(
            orientation='vertical',
            padding=[dp(14), dp(10)],
            spacing=dp(4)
        )
        self.curr_card_ref = curr_card
        lbl_curr_top = Label(
            text='CURRENT IP',
            font_size=sp(9),
            color=get_color_from_hex(C_TEXT_DIM),
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(18)
        )
        self.lbl_curr_ip = Label(
            text='Checking...',
            font_size=sp(13),
            bold=True,
            color=get_color_from_hex(C_CYAN),
            halign='center',
            size_hint_y=1
        )
        curr_card.add_widget(lbl_curr_top)
        curr_card.add_widget(self.lbl_curr_ip)

        ip_row.add_widget(orig_card)
        ip_row.add_widget(curr_card)
        root.add_widget(ip_row)

        # ── BOTTOM STATUS BAR
        status_bar = RoundCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
            padding=[dp(18), dp(8)],
            border_color=get_color_from_hex(C_GRAY),
            bg_color=(
                *get_color_from_hex(C_CARD)[:3], 0.6
            )
        )
        self.lbl_bar = Label(
            text='⏳  Starting up...',
            font_size=sp(12),
            color=get_color_from_hex(C_TEXT_MID),
            halign='left',
            valign='middle'
        )
        self.lbl_bar.bind(size=self.lbl_bar.setter('text_size'))
        status_bar.add_widget(self.lbl_bar)
        root.add_widget(status_bar)

        # ── BUTTONS
        btn_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(160),
            spacing=dp(12)
        )

        self.btn_save = NeonButton(
            text='💾   SAVE MY IP AS ORIGINAL',
            neon=C_CYAN,
            size_hint_y=None,
            height=dp(62)
        )
        self.btn_save.bind(on_press=self._save_ip)

        self.btn_monitor = NeonButton(
            text='▶   START MONITORING',
            neon=C_GREEN,
            size_hint_y=None,
            height=dp(62)
        )
        self.btn_monitor.bind(on_press=self._toggle_monitor)

        btn_box.add_widget(self.btn_save)
        btn_box.add_widget(self.btn_monitor)
        root.add_widget(btn_box)

        self.add_widget(root)

    def _draw_grid(self, *a):
        w = self._grid
        w.canvas.clear()
        with w.canvas:
            Color(0.0, 0.5, 1.0, 0.03)
            step = dp(40)
            x = w.x
            while x < w.right:
                Line(points=[x, w.y, x, w.top], width=0.8)
                x += step
            y = w.y
            while y < w.top:
                Line(points=[w.x, y, w.right, y], width=0.8)
                y += step

    # ── NETWORK ────────────────────────────────
    def _get_ip(self):
        urls = [
            'https://api.ipify.org',
            'https://ifconfig.me/ip',
            'https://icanhazip.com',
            'https://api4.my-ip.io/ip',
        ]
        for url in urls:
            try:
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'VPNShield/1.0'}
                )
                with urllib.request.urlopen(req, timeout=5) as r:
                    ip = r.read().decode().strip()
                    if ip and '.' in ip:
                        return ip
            except:
                continue
        return None

    # ── FIRST CHECK ────────────────────────────
    def _first_check(self, *a):
        def run():
            ip = self._get_ip()
            Clock.schedule_once(lambda dt: self._on_first_ip(ip))

        threading.Thread(target=run, daemon=True).start()

    def _on_first_ip(self, ip):
        if ip:
            self._current_ip = ip
            self.lbl_curr_ip.text = ip
            self.lbl_curr_ip.color = get_color_from_hex(C_CYAN)
            self._set_bar(f'✔  Got current IP: {ip}', C_CYAN)
            self.lbl_status.text = 'READY'
            self.lbl_status.color = get_color_from_hex(C_CYAN)
            self.pulse_ring.set_state(False, C_TEXT_DIM)
            self.lbl_shield.text = '◎'
        else:
            self._set_bar('✖  No internet connection', C_RED)
            self.lbl_status.text = 'NO CONNECTION'
            self.lbl_status.color = get_color_from_hex(C_RED)

    # ── SAVE IP ────────────────────────────────
    def _save_ip(self, *a):
        if not self._current_ip:
            self._set_bar('⚠  No IP fetched yet!', C_YELLOW)
            return

        self._original_ip = self._current_ip
        self.lbl_orig_ip.text = self._original_ip
        self.lbl_orig_ip.color = get_color_from_hex(C_YELLOW)

        anim = Animation(
            color=get_color_from_hex(C_TEXT_MID), duration=2
        )
        anim.start(self.lbl_orig_ip)

        self._set_bar(
            f'✔  Original IP saved: {self._original_ip}', C_GREEN
        )

        # Flash button
        self.btn_save.text = '✔   IP SAVED!'
        Clock.schedule_once(
            lambda dt: setattr(
                self.btn_save, 'text',
                '💾   SAVE MY IP AS ORIGINAL'
            ), 2
        )

    # ── MONITOR TOGGLE ─────────────────────────
    def _toggle_monitor(self, *a):
        if not self._original_ip:
            self._set_bar(
                '⚠  Save your original IP first!', C_YELLOW
            )
            # Shake animation hint
            anim = (
                Animation(x=self.btn_save.x + dp(6), duration=0.05)
                + Animation(x=self.btn_save.x - dp(6), duration=0.05)
                + Animation(x=self.btn_save.x, duration=0.05)
            )
            anim.start(self.btn_save)
            return

        if not self._monitoring:
            self._start_monitoring()
        else:
            self._stop_monitoring()

    def _start_monitoring(self):
        self._monitoring = True
        self.btn_monitor.text = '■   STOP MONITORING'
        self.btn_monitor.set_neon(C_RED)
        self._set_bar('👁  Monitoring active...', C_GREEN)
        self._monitor_event = Clock.schedule_interval(
            lambda dt: self._do_check(), 8
        )
        # Immediate first check
        self._do_check()

    def _stop_monitoring(self):
        self._monitoring = False
        if self._monitor_event:
            self._monitor_event.cancel()
            self._monitor_event = None
        self.btn_monitor.text = '▶   START MONITORING'
        self.btn_monitor.set_neon(C_GREEN)
        self._set_bar('⏹  Monitoring stopped', C_TEXT_MID)

        # Update UI to neutral
        self._set_protected(None)
        Notifier.cancel(NOTIF_ID_PERSISTENT)

    # ── PERIODIC CHECK ─────────────────────────
    def _do_check(self):
        if not self._check_lock.acquire(blocking=False):
            return

        def run():
            try:
                ip = self._get_ip()
                Clock.schedule_once(
                    lambda dt: self._on_check_result(ip)
                )
            finally:
                self._check_lock.release()

        threading.Thread(target=run, daemon=True).start()

    def _on_check_result(self, ip):
        if not self._monitoring:
            return

        if not ip:
            self._set_bar('⚠  Connection lost!', C_YELLOW)
            Notifier.alert(
                '⚠️ VPN Shield Warning',
                'Cannot reach internet. Your protection status is unknown!'
            )
            return

        self._current_ip = ip
        self.lbl_curr_ip.text = ip

        was_protected = self._protected
        is_protected = (ip != self._original_ip)
        self._set_protected(is_protected)

        # Notifications
        if is_protected:
            self.lbl_curr_ip.color = get_color_from_hex(C_GREEN)
            Notifier.persistent(
                '🛡️ Your IP is HIDDEN',
                f'Protected IP: {ip}  |  Original: {self._original_ip}'
            )
            if not was_protected:
                Notifier.alert(
                    '✅ IP is now HIDDEN',
                    f'VPN active. Current IP: {ip}'
                )
        else:
            self.lbl_curr_ip.color = get_color_from_hex(C_RED)
            Notifier.persistent(
                '🚨 Your IP is EXPOSED!',
                f'Real IP visible: {ip} — Turn on your VPN!'
            )
            if was_protected is True:
                # Was protected, now exposed → ALERT
                Notifier.alert(
                    '🚨 IP EXPOSED! VPN Disconnected!',
                    f'Your real IP {ip} is now visible! '
                    f'Turn on VPN immediately!'
                )

    # ── UI STATE ───────────────────────────────
    def _set_protected(self, state):
        """state: True=protected, False=exposed, None=neutral"""
        self._protected = state
        if state is True:
            self.lbl_status.text = '🛡  YOUR IP IS HIDDEN'
            self.lbl_status.color = get_color_from_hex(C_GREEN)
            self.pulse_ring.set_state(True, C_GREEN)
            self.lbl_shield.text = '🛡'
            self._set_bar(
                f'✔  IP masked  |  Real: {self._original_ip}',
                C_GREEN
            )
        elif state is False:
            self.lbl_status.text = '🚨  IP IS EXPOSED!'
            self.lbl_status.color = get_color_from_hex(C_RED)
            self.pulse_ring.set_state(True, C_RED)
            self.lbl_shield.text = '⚠'
            self._set_bar(
                '⚠  VPN off! Real IP visible!', C_RED
            )
        else:
            self.lbl_status.text = 'MONITORING OFF'
            self.lbl_status.color = get_color_from_hex(C_TEXT_MID)
            self.pulse_ring.set_state(False, C_TEXT_DIM)
            self.lbl_shield.text = '◎'

    def _set_bar(self, text, color_hex):
        self.lbl_bar.text = text
        self.lbl_bar.color = get_color_from_hex(color_hex)


# ─────────────────────────────────────────────
#  APP
# ─────────────────────────────────────────────
class VPNShieldApp(App):
    def build(self):
        self.title = 'VPN Shield'
        if ANDROID:
            try:
                request_permissions([
                    Permission.INTERNET,
                    Permission.FOREGROUND_SERVICE,
                    Permission.RECEIVE_BOOT_COMPLETED,
                ])
            except:
                pass
        return MainScreen()

    def on_pause(self):
        return True  # Keep running in background

    def on_resume(self):
        pass


if __name__ == '__main__':
    VPNShieldApp().run()
