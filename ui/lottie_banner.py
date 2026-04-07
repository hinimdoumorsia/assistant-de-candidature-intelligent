"""
ui/lottie_banner.py - Illustration animee avec support Lottie optionnel.
Fallback local si l'asset n'existe pas ou si le moteur n'est pas disponible.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QSize, QRectF
from PyQt6.QtGui import QColor, QPainter, QPixmap, QMovie, QLinearGradient, QBrush
from PyQt6.QtWidgets import QFrame, QLabel, QStackedWidget, QVBoxLayout, QWidget
from config import COLORS

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore
    WEB_ENGINE_AVAILABLE = True
except Exception:
    QWebEngineView = None
    WEB_ENGINE_AVAILABLE = False


ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "animations"


def build_targeted_html(asset_name: str, title: str, subtitle: str) -> str | None:
        primary = COLORS["primary"]
        primary_dark = COLORS["primary_dark"]
        muted = COLORS["text_light"]

        if asset_name == "welcome":
                return f"""
                <!doctype html>
                <html>
                <head>
                    <meta charset='utf-8' />
                    <meta name='viewport' content='width=device-width, initial-scale=1' />
                    <style>
                        html, body {{ margin:0; width:100%; height:100%; overflow:hidden; background:transparent; }}
                        body {{ display:flex; align-items:center; justify-content:center; font-family:Segoe UI, Arial, sans-serif; }}
                        .wrap {{ width:100%; height:100%; max-width:460px; max-height:280px; position:relative; display:flex; align-items:center; justify-content:center; }}
                        .ring {{ position:absolute; width:220px; height:220px; border:2px solid rgba(91,106,240,.22); border-radius:50%; animation:spin 14s linear infinite; }}
                        .ring::after {{ content:''; position:absolute; inset:18px; border:2px dashed rgba(139,92,246,.22); border-radius:50%; animation:spin 20s linear infinite reverse; }}
                        .card {{ width:250px; padding:22px; border-radius:24px; background:linear-gradient(145deg, {primary_dark}, {primary}); box-shadow:0 20px 50px rgba(15,23,42,.28); transform:translateY(0); animation:float 4.5s ease-in-out infinite; color:white; position:relative; }}
                        .title {{ font-size:26px; font-weight:700; }}
                        .subtitle {{ margin-top:6px; font-size:13px; line-height:1.45; color:rgba(255,255,255,.82); }}
                        .plane {{ position:absolute; right:22px; top:20px; width:34px; height:34px; border-radius:10px; background:rgba(255,255,255,.16); }}
                        .plane::before {{ content:''; position:absolute; left:8px; top:8px; width:14px; height:14px; border-top:3px solid white; border-right:3px solid white; transform:rotate(45deg); }}
                        .trail {{ position:absolute; right:54px; top:34px; width:74px; height:2px; background:linear-gradient(90deg, rgba(255,255,255,.0), rgba(255,255,255,.9)); transform-origin:right center; animation:trail 3s ease-in-out infinite; }}
                        .dot {{ position:absolute; width:10px; height:10px; border-radius:50%; background:white; box-shadow:0 0 0 6px rgba(255,255,255,.12); animation:pulse 2.6s ease-in-out infinite; }}
                        .d1 {{ left:22px; bottom:22px; }}
                        .d2 {{ left:54px; top:26px; animation-delay:.5s; }}
                        .d3 {{ right:28px; bottom:28px; animation-delay:1s; }}
                        .caption {{ position:absolute; bottom:10px; width:100%; text-align:center; color:{muted}; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }}
                        @keyframes spin {{ from {{ transform:rotate(0deg); }} to {{ transform:rotate(360deg); }} }}
                        @keyframes float {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-8px); }} }}
                        @keyframes pulse {{ 0%,100% {{ transform:scale(1); opacity:.8; }} 50% {{ transform:scale(1.45); opacity:1; }} }}
                        @keyframes trail {{ 0%,100% {{ transform:scaleX(.65); opacity:.35; }} 50% {{ transform:scaleX(1.1); opacity:1; }} }}
                    </style>
                </head>
                <body>
                    <div class='wrap'>
                        <div class='ring'></div>
                        <div class='card'>
                            <div class='plane'></div>
                            <div class='trail'></div>
                            <div class='title'>{title}</div>
                            <div class='subtitle'>{subtitle}</div>
                        </div>
                        <div class='dot d1'></div>
                        <div class='dot d2'></div>
                        <div class='dot d3'></div>
                        <div class='caption'>Welcome flow</div>
                    </div>
                </body>
                </html>
                """

        if asset_name == "register":
                return f"""
                <!doctype html>
                <html>
                <head>
                    <meta charset='utf-8' />
                    <meta name='viewport' content='width=device-width, initial-scale=1' />
                    <style>
                        html, body {{ margin:0; width:100%; height:100%; overflow:hidden; background:transparent; }}
                        body {{ display:flex; align-items:center; justify-content:center; font-family:Segoe UI, Arial, sans-serif; }}
                        .wrap {{ width:100%; height:100%; max-width:460px; max-height:280px; position:relative; display:flex; align-items:center; justify-content:center; }}
                        .panel {{ width:280px; height:170px; border-radius:24px; background:linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.03)); border:1px solid rgba(255,255,255,.14); box-shadow:0 18px 45px rgba(15,23,42,.22); padding:18px 20px; animation:lift 4s ease-in-out infinite; color:white; }}
                        .header {{ display:flex; align-items:center; gap:10px; margin-bottom:16px; }}
                        .badge {{ width:28px; height:28px; border-radius:50%; background:linear-gradient(145deg, {primary_dark}, {primary}); display:flex; align-items:center; justify-content:center; color:white; font-size:18px; font-weight:700; }}
                        .line {{ height:10px; border-radius:999px; background:rgba(255,255,255,.16); margin-bottom:10px; overflow:hidden; position:relative; }}
                        .line::after {{ content:''; position:absolute; inset:0; width:45%; background:linear-gradient(90deg, rgba(255,255,255,.0), rgba(255,255,255,.9), rgba(255,255,255,.0)); animation:scan 2.8s ease-in-out infinite; }}
                        .check {{ position:absolute; right:76px; top:72px; width:82px; height:82px; border-radius:50%; background:rgba(91,106,240,.18); border:1px solid rgba(91,106,240,.28); display:flex; align-items:center; justify-content:center; animation:pop 2.8s ease-in-out infinite; }}
                        .check::before {{ content:''; width:28px; height:14px; border-left:5px solid white; border-bottom:5px solid white; transform:rotate(-45deg) translateY(-2px); }}
                        .title {{ font-size:24px; font-weight:700; margin-top:6px; color:white; }}
                        .subtitle {{ margin-top:4px; font-size:13px; line-height:1.45; color:rgba(255,255,255,.82); }}
                        .caption {{ position:absolute; bottom:10px; width:100%; text-align:center; color:{muted}; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }}
                        @keyframes scan {{ 0%,100% {{ transform:translateX(-60%); }} 50% {{ transform:translateX(220%); }} }}
                        @keyframes lift {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-7px); }} }}
                        @keyframes pop {{ 0%,100% {{ transform:scale(1); }} 50% {{ transform:scale(1.12); }} }}
                    </style>
                </head>
                <body>
                    <div class='wrap'>
                        <div class='panel'>
                            <div class='header'>
                                <div class='badge'>+</div>
                                <div>
                                    <div class='title'>{title}</div>
                                    <div class='subtitle'>{subtitle}</div>
                                </div>
                            </div>
                            <div class='line'></div>
                            <div class='line' style='width:82%;'></div>
                            <div class='line' style='width:64%;'></div>
                        </div>
                        <div class='check'></div>
                        <div class='caption'>Registration flow</div>
                    </div>
                </body>
                </html>
                """

        if asset_name == "settings":
                return f"""
                <!doctype html>
                <html>
                <head>
                    <meta charset='utf-8' />
                    <meta name='viewport' content='width=device-width, initial-scale=1' />
                    <style>
                        html, body {{ margin:0; width:100%; height:100%; overflow:hidden; background:transparent; }}
                        body {{ display:flex; align-items:center; justify-content:center; font-family:Segoe UI, Arial, sans-serif; }}
                        .wrap {{ width:100%; height:100%; max-width:460px; max-height:280px; position:relative; display:flex; align-items:center; justify-content:center; }}
                        .gear {{ position:relative; width:170px; height:170px; border-radius:50%; border:16px solid rgba(91,106,240,.30); animation:spin 10s linear infinite; }}
                        .gear::before {{ content:''; position:absolute; inset:32px; border-radius:50%; border:8px solid rgba(139,92,246,.34); }}
                        .hub {{ position:absolute; width:58px; height:58px; border-radius:50%; background:linear-gradient(145deg, {primary_dark}, {primary}); box-shadow:0 0 0 12px rgba(255,255,255,.08); }}
                        .spoke {{ position:absolute; width:16px; height:44px; border-radius:999px; background:rgba(255,255,255,.28); top:50%; left:50%; transform-origin:center -68px; }}
                        .s1 {{ transform:translate(-50%, -50%) rotate(0deg); }}
                        .s2 {{ transform:translate(-50%, -50%) rotate(60deg); }}
                        .s3 {{ transform:translate(-50%, -50%) rotate(120deg); }}
                        .s4 {{ transform:translate(-50%, -50%) rotate(180deg); }}
                        .s5 {{ transform:translate(-50%, -50%) rotate(240deg); }}
                        .s6 {{ transform:translate(-50%, -50%) rotate(300deg); }}
                        .panel {{ position:absolute; right:26px; bottom:30px; width:156px; height:92px; border-radius:18px; background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.12); padding:14px; color:white; animation:float 4s ease-in-out infinite; }}
                        .panel .row {{ height:10px; border-radius:999px; background:rgba(255,255,255,.18); margin-bottom:10px; }}
                        .panel .row:nth-child(2) {{ width:84%; }}
                        .panel .row:nth-child(3) {{ width:66%; }}
                        .panel .row:nth-child(4) {{ width:54%; }}
                        .caption {{ position:absolute; bottom:10px; width:100%; text-align:center; color:{muted}; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }}
                        @keyframes spin {{ from {{ transform:rotate(0deg); }} to {{ transform:rotate(360deg); }} }}
                        @keyframes float {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-8px); }} }}
                    </style>
                </head>
                <body>
                    <div class='wrap'>
                        <div class='gear'>
                            <div class='spoke s1'></div>
                            <div class='spoke s2'></div>
                            <div class='spoke s3'></div>
                            <div class='spoke s4'></div>
                            <div class='spoke s5'></div>
                            <div class='spoke s6'></div>
                        </div>
                        <div class='hub'></div>
                        <div class='panel'>
                            <div class='row'></div>
                            <div class='row'></div>
                            <div class='row'></div>
                        </div>
                        <div class='caption'>Settings flow</div>
                    </div>
                </body>
                </html>
                """

        return None


class PulsingFallbackWidget(QFrame):
    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.phase = 0
        self.setMinimumSize(320, 260)
        self.setMaximumHeight(320)
        self.setObjectName("pulsingFallback")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(90)

        self.text_title = QLabel(title, self)
        self.text_sub = QLabel(subtitle, self)
        self.text_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_title.setStyleSheet("color: white; font-size: 26px; font-weight: 700; background: transparent;")
        self.text_sub.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px; background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addStretch()
        layout.addWidget(self.text_title)
        layout.addWidget(self.text_sub)
        layout.addStretch()

    def _tick(self):
        self.phase = (self.phase + 1) % 24
        self.update()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        gradient.setColorAt(0.0, QColor(COLORS["primary_dark"]))
        gradient.setColorAt(0.6, QColor(COLORS["primary"]))
        gradient.setColorAt(1.0, QColor(COLORS["purple"]))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 26, 26)

        # decorative orbs
        orb_colors = [QColor(255, 255, 255, 40), QColor(255, 255, 255, 28), QColor(255, 255, 255, 20)]
        for index, color in enumerate(orb_colors):
            radius = 36 + index * 16 + (self.phase % 6)
            x = rect.width() - 88 - index * 42
            y = 52 + index * 34
            painter.setBrush(color)
            painter.drawEllipse(x - radius // 2, y - radius // 2, radius, radius)

        # animated dots
        base_x = 44
        base_y = rect.height() - 52
        dot_r = 8
        for index in range(4):
            alpha = 60 + ((self.phase + index * 4) % 24) * 8
            painter.setBrush(QColor(255, 255, 255, min(alpha, 180)))
            x = base_x + index * 22
            painter.drawEllipse(x, base_y, dot_r, dot_r)


class LottieBannerWidget(QWidget):
    def __init__(self, asset_name: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.asset_name = asset_name
        self.setMinimumHeight(270)

        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        self._build_views(title, subtitle)

        def _targeted_html(self, title: str, subtitle: str) -> str | None:
                primary = COLORS["primary"]
                primary_dark = COLORS["primary_dark"]
                muted = COLORS["text_light"]

                if self.asset_name == "welcome":
                        return f"""
                        <!doctype html>
                        <html>
                        <head>
                            <meta charset='utf-8' />
                            <meta name='viewport' content='width=device-width, initial-scale=1' />
                            <style>
                                html, body {{ margin:0; width:100%; height:100%; overflow:hidden; background:transparent; }}
                                body {{ display:flex; align-items:center; justify-content:center; font-family:Segoe UI, Arial, sans-serif; }}
                                .wrap {{ width:100%; height:100%; max-width:460px; max-height:280px; position:relative; display:flex; align-items:center; justify-content:center; }}
                                .ring {{ position:absolute; width:220px; height:220px; border:2px solid rgba(91,106,240,.22); border-radius:50%; animation:spin 14s linear infinite; }}
                                .ring::after {{ content:''; position:absolute; inset:18px; border:2px dashed rgba(139,92,246,.22); border-radius:50%; animation:spin 20s linear infinite reverse; }}
                                .card {{ width:250px; padding:22px; border-radius:24px; background:linear-gradient(145deg, {primary_dark}, {primary}); box-shadow:0 20px 50px rgba(15,23,42,.28); transform:translateY(0); animation:float 4.5s ease-in-out infinite; color:white; position:relative; }}
                                .title {{ font-size:26px; font-weight:700; }}
                                .subtitle {{ margin-top:6px; font-size:13px; line-height:1.45; color:rgba(255,255,255,.82); }}
                                .plane {{ position:absolute; right:22px; top:20px; width:34px; height:34px; border-radius:10px; background:rgba(255,255,255,.16); }}
                                .plane::before {{ content:''; position:absolute; left:8px; top:8px; width:14px; height:14px; border-top:3px solid white; border-right:3px solid white; transform:rotate(45deg); }}
                                .trail {{ position:absolute; right:54px; top:34px; width:74px; height:2px; background:linear-gradient(90deg, rgba(255,255,255,.0), rgba(255,255,255,.9)); transform-origin:right center; animation:trail 3s ease-in-out infinite; }}
                                .dot {{ position:absolute; width:10px; height:10px; border-radius:50%; background:white; box-shadow:0 0 0 6px rgba(255,255,255,.12); animation:pulse 2.6s ease-in-out infinite; }}
                                .d1 {{ left:22px; bottom:22px; }}
                                .d2 {{ left:54px; top:26px; animation-delay:.5s; }}
                                .d3 {{ right:28px; bottom:28px; animation-delay:1s; }}
                                .caption {{ position:absolute; bottom:10px; width:100%; text-align:center; color:{muted}; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }}
                                @keyframes spin {{ from {{ transform:rotate(0deg); }} to {{ transform:rotate(360deg); }} }}
                                @keyframes float {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-8px); }} }}
                                @keyframes pulse {{ 0%,100% {{ transform:scale(1); opacity:.8; }} 50% {{ transform:scale(1.45); opacity:1; }} }}
                                @keyframes trail {{ 0%,100% {{ transform:scaleX(.65); opacity:.35; }} 50% {{ transform:scaleX(1.1); opacity:1; }} }}
                            </style>
                        </head>
                        <body>
                            <div class='wrap'>
                                <div class='ring'></div>
                                <div class='card'>
                                    <div class='plane'></div>
                                    <div class='trail'></div>
                                    <div class='title'>{title}</div>
                                    <div class='subtitle'>{subtitle}</div>
                                </div>
                                <div class='dot d1'></div>
                                <div class='dot d2'></div>
                                <div class='dot d3'></div>
                                <div class='caption'>Welcome flow</div>
                            </div>
                        </body>
                        </html>
                        """

                if self.asset_name == "register":
                        return f"""
                        <!doctype html>
                        <html>
                        <head>
                            <meta charset='utf-8' />
                            <meta name='viewport' content='width=device-width, initial-scale=1' />
                            <style>
                                html, body {{ margin:0; width:100%; height:100%; overflow:hidden; background:transparent; }}
                                body {{ display:flex; align-items:center; justify-content:center; font-family:Segoe UI, Arial, sans-serif; }}
                                .wrap {{ width:100%; height:100%; max-width:460px; max-height:280px; position:relative; display:flex; align-items:center; justify-content:center; }}
                                .panel {{ width:280px; height:170px; border-radius:24px; background:linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.03)); border:1px solid rgba(255,255,255,.14); box-shadow:0 18px 45px rgba(15,23,42,.22); padding:18px 20px; animation:lift 4s ease-in-out infinite; color:white; }}
                                .header {{ display:flex; align-items:center; gap:10px; margin-bottom:16px; }}
                                .badge {{ width:28px; height:28px; border-radius:50%; background:linear-gradient(145deg, {primary_dark}, {primary}); display:flex; align-items:center; justify-content:center; color:white; font-size:18px; font-weight:700; }}
                                .line {{ height:10px; border-radius:999px; background:rgba(255,255,255,.16); margin-bottom:10px; overflow:hidden; position:relative; }}
                                .line::after {{ content:''; position:absolute; inset:0; width:45%; background:linear-gradient(90deg, rgba(255,255,255,.0), rgba(255,255,255,.9), rgba(255,255,255,.0)); animation:scan 2.8s ease-in-out infinite; }}
                                .check {{ position:absolute; right:76px; top:72px; width:82px; height:82px; border-radius:50%; background:rgba(91,106,240,.18); border:1px solid rgba(91,106,240,.28); display:flex; align-items:center; justify-content:center; animation:pop 2.8s ease-in-out infinite; }}
                                .check::before {{ content:''; width:28px; height:14px; border-left:5px solid white; border-bottom:5px solid white; transform:rotate(-45deg) translateY(-2px); }}
                                .title {{ font-size:24px; font-weight:700; margin-top:6px; color:white; }}
                                .subtitle {{ margin-top:4px; font-size:13px; line-height:1.45; color:rgba(255,255,255,.82); }}
                                .caption {{ position:absolute; bottom:10px; width:100%; text-align:center; color:{muted}; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }}
                                @keyframes scan {{ 0%,100% {{ transform:translateX(-60%); }} 50% {{ transform:translateX(220%); }} }}
                                @keyframes lift {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-7px); }} }}
                                @keyframes pop {{ 0%,100% {{ transform:scale(1); }} 50% {{ transform:scale(1.12); }} }}
                            </style>
                        </head>
                        <body>
                            <div class='wrap'>
                                <div class='panel'>
                                    <div class='header'>
                                        <div class='badge'>+</div>
                                        <div>
                                            <div class='title'>{title}</div>
                                            <div class='subtitle'>{subtitle}</div>
                                        </div>
                                    </div>
                                    <div class='line'></div>
                                    <div class='line' style='width:82%;'></div>
                                    <div class='line' style='width:64%;'></div>
                                </div>
                                <div class='check'></div>
                                <div class='caption'>Registration flow</div>
                            </div>
                        </body>
                        </html>
                        """

                if self.asset_name == "settings":
                        return f"""
                        <!doctype html>
                        <html>
                        <head>
                            <meta charset='utf-8' />
                            <meta name='viewport' content='width=device-width, initial-scale=1' />
                            <style>
                                html, body {{ margin:0; width:100%; height:100%; overflow:hidden; background:transparent; }}
                                body {{ display:flex; align-items:center; justify-content:center; font-family:Segoe UI, Arial, sans-serif; }}
                                .wrap {{ width:100%; height:100%; max-width:460px; max-height:280px; position:relative; display:flex; align-items:center; justify-content:center; }}
                                .gear {{ position:relative; width:170px; height:170px; border-radius:50%; border:16px solid rgba(91,106,240,.30); animation:spin 10s linear infinite; }}
                                .gear::before {{ content:''; position:absolute; inset:32px; border-radius:50%; border:8px solid rgba(139,92,246,.34); }}
                                .hub {{ position:absolute; width:58px; height:58px; border-radius:50%; background:linear-gradient(145deg, {primary_dark}, {primary}); box-shadow:0 0 0 12px rgba(255,255,255,.08); }}
                                .spoke {{ position:absolute; width:16px; height:44px; border-radius:999px; background:rgba(255,255,255,.28); top:50%; left:50%; transform-origin:center -68px; }}
                                .s1 {{ transform:translate(-50%, -50%) rotate(0deg); }}
                                .s2 {{ transform:translate(-50%, -50%) rotate(60deg); }}
                                .s3 {{ transform:translate(-50%, -50%) rotate(120deg); }}
                                .s4 {{ transform:translate(-50%, -50%) rotate(180deg); }}
                                .s5 {{ transform:translate(-50%, -50%) rotate(240deg); }}
                                .s6 {{ transform:translate(-50%, -50%) rotate(300deg); }}
                                .panel {{ position:absolute; right:26px; bottom:30px; width:156px; height:92px; border-radius:18px; background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.12); padding:14px; color:white; animation:float 4s ease-in-out infinite; }}
                                .panel .row {{ height:10px; border-radius:999px; background:rgba(255,255,255,.18); margin-bottom:10px; }}
                                .panel .row:nth-child(2) {{ width:84%; }}
                                .panel .row:nth-child(3) {{ width:66%; }}
                                .panel .row:nth-child(4) {{ width:54%; }}
                                .caption {{ position:absolute; bottom:10px; width:100%; text-align:center; color:{muted}; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }}
                                @keyframes spin {{ from {{ transform:rotate(0deg); }} to {{ transform:rotate(360deg); }} }}
                                @keyframes float {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-8px); }} }}
                            </style>
                        </head>
                        <body>
                            <div class='wrap'>
                                <div class='gear'>
                                    <div class='spoke s1'></div>
                                    <div class='spoke s2'></div>
                                    <div class='spoke s3'></div>
                                    <div class='spoke s4'></div>
                                    <div class='spoke s5'></div>
                                    <div class='spoke s6'></div>
                                </div>
                                <div class='hub'></div>
                                <div class='panel'>
                                    <div class='row'></div>
                                    <div class='row'></div>
                                    <div class='row'></div>
                                </div>
                                <div class='caption'>Settings flow</div>
                            </div>
                        </body>
                        </html>
                        """

                return None

    def _build_views(self, title: str, subtitle: str):
        json_path = ASSET_DIR / f"{self.asset_name}.json"
        gif_path = ASSET_DIR / f"{self.asset_name}.gif"

        targeted_html = build_targeted_html(self.asset_name, title, subtitle)
        if targeted_html:
            view = QWebEngineView() if WEB_ENGINE_AVAILABLE and QWebEngineView is not None else None
            if view is not None:
                view.setHtml(targeted_html)
                self.stack.addWidget(view)
                self.stack.setCurrentWidget(view)
                return

        if json_path.exists() and WEB_ENGINE_AVAILABLE and QWebEngineView is not None:
            view = QWebEngineView()
            html = f"""
            <!doctype html>
            <html>
            <head>
              <meta charset='utf-8' />
              <meta name='viewport' content='width=device-width, initial-scale=1' />
              <style>
                html, body {{ margin:0; width:100%; height:100%; overflow:hidden; background:transparent; }}
                #wrap {{ width:100%; height:100%; display:flex; align-items:center; justify-content:center; }}
                #anim {{ width:100%; height:100%; max-width: 440px; max-height: 280px; }}
              </style>
              <script src='https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js'></script>
            </head>
            <body>
              <div id='wrap'><div id='anim'></div></div>
              <script>
                fetch('file:///{json_path.as_posix()}')
                  .then(r => r.json())
                  .then(data => lottie.loadAnimation({{
                    container: document.getElementById('anim'),
                    renderer: 'svg',
                    loop: true,
                    autoplay: true,
                    animationData: data
                  }}));
              </script>
            </body>
            </html>
            """
            view.setHtml(html)
            self.stack.addWidget(view)
            self.stack.setCurrentWidget(view)
            return

        if gif_path.exists():
            label = QLabel()
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            movie = QMovie(str(gif_path))
            movie.setScaledSize(QSize(420, 240))
            label.setMovie(movie)
            movie.start()
            self.stack.addWidget(label)
            self.stack.setCurrentWidget(label)
            return

        fallback = PulsingFallbackWidget(title, subtitle)
        self.stack.addWidget(fallback)
        self.stack.setCurrentWidget(fallback)
