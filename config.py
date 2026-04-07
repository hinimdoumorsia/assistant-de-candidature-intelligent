"""
config.py - Configuration centrale du SCA Desktop
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Chemins ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = BASE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"
ENV_PATH = BASE_DIR / ".env"

for d in (DATA_DIR, EXPORTS_DIR, LOGS_DIR):
    d.mkdir(exist_ok=True)

if ENV_PATH.exists():
    try:
        os.chmod(ENV_PATH, 0o600)
    except Exception:
        # On Windows, chmod can be partially unsupported depending on filesystem.
        pass

# ── Base de données ────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/sca_data.db")

# ── API Keys ───────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", os.getenv("ANTHROPIC_KEY", ""))
CLAUDE_MODEL   = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY", "")

# ── Sources de scraping ────────────────────────────────────────────────────────
SOURCES = {
    "indeed_rss": {
        "enabled": True,
        "method": "rss",
        "url": "https://fr.indeed.com/rss?q=stage&l=Maroc",
        "label": "Indeed",
    },
    "rekrute": {
        "enabled": True,
        "method": "playwright",
        "url": "https://www.rekrute.com/offres.html",
        "label": "Rekrute",
        "selectors": {
            "listing": ".post-id",
            "title": "h2.title a",
            "company": ".company",
            "location": ".location",
            "link": "h2.title a",
        },
    },
    "emploi_ma": {
        "enabled": True,
        "method": "playwright",
        "url": "https://www.emploi.ma/recherche-jobs-maroc",
        "label": "Emploi.ma",
        "selectors": {
            "listing": ".job-list-item",
            "title": ".job-title",
            "company": ".company-name",
            "location": ".job-location",
            "link": "a.job-title",
        },
    },
    "bayt": {
        "enabled": True,
        "method": "rss+playwright",
        "url": "https://www.bayt.com/fr/maroc/jobs/",
        "rss_url": "https://www.bayt.com/rss/maroc/stage-jobs/",
        "label": "Bayt",
    },
    "adzuna": {
        "enabled": True,
        "method": "api",
        "base_url": "https://api.adzuna.com/v1/api/jobs/ma/search",
        "label": "Adzuna",
    },
    "remotive": {
        "enabled": False,
        "method": "rss",
        "url": "https://remotive.com/feed",
        "label": "Remotive",
    },
}

# ── Scraping & Matching ────────────────────────────────────────────────────────
SCRAPE_INTERVAL_MINUTES = 30
TFIDF_THRESHOLD         = 0.40
CLAUDE_THRESHOLD        = 60
DEDUP_COSINE_THRESHOLD  = 0.85
MAX_OFFERS_PER_RUN      = 50

# ── Playwright ─────────────────────────────────────────────────────────────────
PLAYWRIGHT_HEADLESS    = True
PLAYWRIGHT_TIMEOUT_MS  = 15_000
PLAYWRIGHT_BROWSER     = "chromium"

# ── Sécurité ───────────────────────────────────────────────────────────────────
BCRYPT_ROUNDS         = 12
SESSION_TIMEOUT_HOURS = 8

# ── UI / Thème SOMBRE ──────────────────────────────────────────────────────────
APP_NAME    = "SCA Desktop"
APP_VERSION = "1.1"

COLORS = {
    "bg":            "#0f1117",
    "bg_dark":       "#12151e",
    "bg_card":       "#1a1f2e",
    "bg_input":      "#161b27",
    "border":        "#1e2535",
    "card_border":   "#1e2535",
    "primary":       "#5b6af0",
    "primary_dark":  "#4a59d0",
    "primary_light": "#5b6af033",
    "accent":        "#5b6af0",
    "accent_light":  "#5b6af033",
    "purple":        "#a855f7",
    "green":         "#22c55e",
    "orange":        "#f97316",
    "red":           "#ef4444",
    "yellow":        "#eab308",
    "text":          "#e2e8f0",
    "text_light":    "#6b7280",
    "sidebar_text":  "#e2e8f0",
    "sidebar":       "#12151e",
    "danger":        "#ef4444",
    "warning":       "#f97316",
    "success":       "#22c55e",
    "white":         "#1a1f2e",
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLORS['bg']};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: {COLORS['text']};
}}

/* IMPORTANT : pas de background transparent sur QWidget
   sinon tout devient invisible sur fond noir */
QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: {COLORS['text']};
    background-color: {COLORS['bg']};
}}

QLabel {{
    color: {COLORS['text']};
    background-color: transparent;
}}

QFrame {{
    background-color: {COLORS['bg']};
    border: none;
}}

QScrollArea {{
    border: none;
    background-color: {COLORS['bg']};
}}

QScrollArea > QWidget > QWidget {{
    background-color: {COLORS['bg']};
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_card']};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['primary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background-color: {COLORS['bg_card']};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background-color: {COLORS['border']};
    border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
    min-height: 36px;
}}
QPushButton:hover {{ background-color: {COLORS['primary_dark']}; }}
QPushButton:pressed {{ background-color: #3a48b0; }}
QPushButton:disabled {{
    background-color: #2a2f3e;
    color: {COLORS['text_light']};
}}

QPushButton[class="accent"] {{ background-color: {COLORS['orange']}; }}
QPushButton[class="accent"]:hover {{ background-color: #e06010; }}

QPushButton[class="secondary"] {{
    background-color: transparent;
    color: {COLORS['primary']};
    border: 1px solid {COLORS['border']};
}}
QPushButton[class="secondary"]:hover {{
    background-color: {COLORS['bg_card']};
    border-color: {COLORS['primary']};
}}

QPushButton[class="danger"] {{
    background-color: transparent;
    color: {COLORS['red']};
    border: 1px solid {COLORS['red']}55;
}}
QPushButton[class="danger"]:hover {{
    background-color: {COLORS['red']}15;
    border-color: {COLORS['red']};
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: {COLORS['text']};
    min-height: 36px;
    selection-background-color: {COLORS['primary']}44;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['primary']};
}}
QLineEdit[readOnly="true"] {{ color: {COLORS['text_light']}; }}

QComboBox {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 36px;
    font-size: 13px;
    color: {COLORS['text']};
}}
QComboBox:focus {{ border-color: {COLORS['primary']}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS['text_light']};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text']};
    selection-background-color: {COLORS['primary']}33;
    outline: none;
}}

QTableWidget {{
    background-color: transparent;
    border: none;
    outline: none;
    gridline-color: {COLORS['border']};
    font-size: 13px;
    color: {COLORS['text']};
}}
QTableWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid {COLORS['border']};
    color: {COLORS['text']};
    background-color: transparent;
}}
QTableWidget::item:selected {{
    background-color: {COLORS['primary']}22;
    color: {COLORS['text']};
}}
QHeaderView::section {{
    background-color: {COLORS['bg']};
    color: {COLORS['text_light']};
    font-weight: 600;
    padding: 8px 6px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    font-size: 12px;
}}
QTableCornerButton::section {{
    background-color: {COLORS['bg']};
    border: none;
}}

QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_card']};
}}
QTabBar::tab {{
    background-color: {COLORS['bg']};
    color: {COLORS['text_light']};
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-size: 13px;
    border: 1px solid {COLORS['border']};
}}
QTabBar::tab:selected {{
    background-color: {COLORS['primary']};
    color: white;
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text']};
}}

QProgressBar {{
    border: none;
    border-radius: 4px;
    background-color: {COLORS['border']};
    height: 8px;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['purple']});
    border-radius: 4px;
}}

QListWidget[class="sidebar"] {{
    background-color: {COLORS['sidebar']};
    border: none;
    color: {COLORS['text']};
    font-size: 14px;
    padding: 8px 0;
}}
QListWidget[class="sidebar"]::item {{
    padding: 14px 20px;
    color: {COLORS['text_light']};
}}
QListWidget[class="sidebar"]::item:selected,
QListWidget[class="sidebar"]::item:hover {{
    background-color: {COLORS['primary']}22;
    color: {COLORS['text']};
}}

QMessageBox {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text']};
}}
QMessageBox QLabel {{
    color: {COLORS['text']};
    background-color: transparent;
}}

QToolTip {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

QGroupBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 16px;
    background-color: {COLORS['bg_card']};
    color: {COLORS['text']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    top: -2px;
    background-color: {COLORS['bg_card']};
    padding: 0 6px;
    color: {COLORS['text']};
    font-weight: 600;
    font-size: 13px;
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 36px;
    color: {COLORS['text']};
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['primary']};
}}

QInputDialog {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text']};
}}

QMenu {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    color: {COLORS['text']};
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: 6px;
    background-color: transparent;
}}
QMenu::item:selected {{
    background-color: {COLORS['primary']}33;
    color: {COLORS['text']};
}}
"""