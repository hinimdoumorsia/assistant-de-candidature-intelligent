"""Minimal Lottie wrapper for PyQt6 using QWebEngineView."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QVBoxLayout, QWidget

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except Exception:  # pragma: no cover - optional runtime dependency
    QWebEngineView = None


class LottieWidget(QWidget):
    """Display a local Lottie JSON animation with transparent background."""

    def __init__(self, json_path: str, loop: bool = True, parent=None):
        super().__init__(parent)
        self._view = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        path = Path(json_path).resolve()
        if QWebEngineView is None or not path.exists():
            return

        self._view = QWebEngineView(self)
        html = f"""
<!doctype html>
<html>
<head>
  <meta charset='utf-8'/>
  <style>
    html, body {{ margin:0; width:100%; height:100%; background: transparent; overflow: hidden; }}
    #anim {{ width:100%; height:100%; }}
  </style>
  <script src='https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js'></script>
</head>
<body>
  <div id='anim'></div>
  <script>
    fetch('file:///{path.as_posix()}')
      .then(r => r.json())
      .then(data => lottie.loadAnimation({{
        container: document.getElementById('anim'),
        renderer: 'svg',
        loop: {str(loop).lower()},
        autoplay: true,
        animationData: data
      }}));
  </script>
</body>
</html>
"""
        self._view.setHtml(html)
        layout.addWidget(self._view)
