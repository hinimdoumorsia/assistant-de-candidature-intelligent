"""
main.py - Point d'entrée SCA Desktop
Lance la fenêtre de login, puis le dashboard après authentification.
"""
import sys
import logging
from pathlib import Path

# ── Logging ────────────────────────────────────────────────────────────────────
from config import LOGS_DIR
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "sca.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("sca.main")


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    from config import STYLESHEET, APP_NAME

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(STYLESHEET)

    # Police par défaut
    font = QFont("Segoe UI", 11)
    app.setFont(font)

    # Init DB
    from database.db_manager import init_db
    init_db()

    # Références globales (pour éviter GC)
    _windows = {}

    def show_dashboard():
        from ui.dashboard import DashboardWindow
        dashboard = DashboardWindow()
        _windows["dashboard"] = dashboard
        dashboard.show()
        if "login" in _windows:
            _windows["login"].close()

    from ui.login_window import LoginWindow
    login = LoginWindow(on_login_success=show_dashboard)
    _windows["login"] = login
    login.show()

    logger.info("SCA Desktop démarré.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
