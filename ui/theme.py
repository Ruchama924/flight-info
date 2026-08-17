"""Centralized design tokens and global QSS for FlightAdvisor."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication


class Colors:
    PRIMARY = "#0B57D0"
    PRIMARY_HOVER = "#0842A0"
    PRIMARY_LIGHT = "#E8F0FE"

    BG = "#F4F6F8"
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#F8FAFC"

    BORDER = "#DDE3EA"
    BORDER_FOCUS = "#0B57D0"

    TEXT = "#1A1D21"
    TEXT_SECONDARY = "#5C6570"
    TEXT_MUTED = "#8A939E"
    TEXT_INVERSE = "#FFFFFF"

    SUCCESS = "#0F7B4A"
    SUCCESS_BG = "#E6F4EA"
    WARNING = "#B06000"
    WARNING_BG = "#FEF7E0"
    ERROR = "#C5221F"
    ERROR_BG = "#FCE8E6"

    SIDEBAR = "#0F1724"
    SIDEBAR_HOVER = "#1A2433"
    SIDEBAR_ACTIVE = "#243044"
    SIDEBAR_TEXT = "#C8D0DA"
    SIDEBAR_TEXT_ACTIVE = "#FFFFFF"

    CHART_BAR = "#0B57D0"
    CHART_GRID = "#E8ECF0"


class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


class Fonts:
    FAMILY = "Segoe UI"
    SIZE_SM = 11
    SIZE_BASE = 13
    SIZE_LG = 15
    SIZE_XL = 20
    SIZE_XXL = 26


def build_stylesheet() -> str:
  c = Colors
  return f"""
/* ---- Global ---- */
QWidget {{
    background-color: {c.BG};
    color: {c.TEXT};
    font-family: "{Fonts.FAMILY}", "SF Pro Text", "Helvetica Neue", sans-serif;
    font-size: {Fonts.SIZE_BASE}px;
}}

QMainWindow, QDialog {{
    background-color: {c.BG};
}}

/* ---- Labels ---- */
QLabel[class="page-title"] {{
    font-size: {Fonts.SIZE_XXL}px;
    font-weight: 600;
    color: {c.TEXT};
    background: transparent;
}}

QLabel[class="page-subtitle"] {{
    font-size: {Fonts.SIZE_BASE}px;
    color: {c.TEXT_SECONDARY};
    background: transparent;
}}

QLabel[class="section-title"] {{
    font-size: {Fonts.SIZE_LG}px;
    font-weight: 600;
    color: {c.TEXT};
    background: transparent;
}}

QLabel[class="muted"] {{
    color: {c.TEXT_MUTED};
    background: transparent;
}}

QLabel[class="price"] {{
    font-size: 22px;
    font-weight: 700;
    color: {c.PRIMARY};
    background: transparent;
}}

/* ---- Inputs ---- */
QLineEdit, QTextEdit, QDateEdit, QComboBox {{
    background-color: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: 8px;
    padding: 10px 12px;
    color: {c.TEXT};
    selection-background-color: {c.PRIMARY_LIGHT};
}}

QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QComboBox:focus {{
    border: 1px solid {c.BORDER_FOCUS};
}}

QLineEdit:disabled, QTextEdit:disabled, QDateEdit:disabled {{
    background-color: {c.SURFACE_ALT};
    color: {c.TEXT_MUTED};
}}

QTextEdit[class="chat-input"] {{
    min-height: 44px;
    max-height: 120px;
}}

QTextEdit[class="chat-history"] {{
    background-color: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: 12px;
    padding: 16px;
}}

/* ---- Buttons ---- */
QPushButton {{
    background-color: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: 8px;
    padding: 10px 18px;
    color: {c.TEXT};
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {c.SURFACE_ALT};
    border-color: #C5CDD6;
}}

QPushButton:pressed {{
    background-color: #EEF1F5;
}}

QPushButton:disabled {{
    background-color: {c.SURFACE_ALT};
    color: {c.TEXT_MUTED};
    border-color: {c.BORDER};
}}

QPushButton[class="primary"] {{
    background-color: {c.PRIMARY};
    border: 1px solid {c.PRIMARY};
    color: {c.TEXT_INVERSE};
    font-weight: 600;
}}

QPushButton[class="primary"]:hover {{
    background-color: {c.PRIMARY_HOVER};
    border-color: {c.PRIMARY_HOVER};
}}

QPushButton[class="primary"]:pressed {{
    background-color: #063678;
}}

QPushButton[class="secondary"] {{
    background-color: {c.SURFACE};
    border: 1px solid {c.BORDER};
}}

QPushButton[class="ghost"] {{
    background-color: transparent;
    border: 1px solid transparent;
    color: {c.PRIMARY};
}}

QPushButton[class="ghost"]:hover {{
    background-color: {c.PRIMARY_LIGHT};
}}

QPushButton[class="danger"] {{
    background-color: {c.SURFACE};
    border: 1px solid #F5C6C4;
    color: {c.ERROR};
}}

QPushButton[class="danger"]:hover {{
    background-color: {c.ERROR_BG};
}}

QPushButton[class="nav"] {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    color: {c.SIDEBAR_TEXT};
    text-align: left;
    font-weight: 500;
}}

QPushButton[class="nav"]:hover {{
    background-color: {c.SIDEBAR_HOVER};
    color: {c.SIDEBAR_TEXT_ACTIVE};
}}

QPushButton[class="nav-active"] {{
    background-color: {c.SIDEBAR_ACTIVE};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    color: {c.SIDEBAR_TEXT_ACTIVE};
    text-align: left;
    font-weight: 600;
}}

/* ---- Cards ---- */
QFrame[class="card"] {{
    background-color: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: 12px;
}}

QFrame[class="card-hover"]:hover {{
    border-color: #B8C4D0;
}}

QFrame[class="search-panel"] {{
    background-color: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: 16px;
}}

QFrame[class="auth-card"] {{
    background-color: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: 16px;
}}

QFrame[class="timeline-card"] {{
    background-color: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: 12px;
}}

/* ---- Scroll areas ---- */
QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px;
}}

QScrollBar::handle:vertical {{
    background: #C5CDD6;
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: #A8B2BD;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 4px;
}}

QScrollBar::handle:horizontal {{
    background: #C5CDD6;
    border-radius: 5px;
    min-width: 30px;
}}

/* ---- Tables (fallback) ---- */
QTableWidget {{
    background-color: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: 12px;
    gridline-color: {c.BORDER};
    selection-background-color: {c.PRIMARY_LIGHT};
    selection-color: {c.TEXT};
}}

QHeaderView::section {{
    background-color: {c.SURFACE_ALT};
    color: {c.TEXT_SECONDARY};
    padding: 10px;
    border: none;
    border-bottom: 1px solid {c.BORDER};
    font-weight: 600;
}}

/* ---- Sidebar shell ---- */
QFrame[class="sidebar"] {{
    background-color: {c.SIDEBAR};
    border: none;
    border-right: 1px solid #1A2433;
}}

QFrame[class="content-area"] {{
    background-color: {c.BG};
    border: none;
}}

QFrame[class="top-bar"] {{
    background-color: {c.SURFACE};
    border: none;
    border-bottom: 1px solid {c.BORDER};
}}

/* ---- Status badges ---- */
QLabel[class="badge-active"] {{
    background-color: {c.SUCCESS_BG};
    color: {c.SUCCESS};
    border-radius: 10px;
    padding: 4px 10px;
    font-size: {Fonts.SIZE_SM}px;
    font-weight: 600;
}}

QLabel[class="badge-cancelled"] {{
    background-color: {c.SURFACE_ALT};
    color: {c.TEXT_SECONDARY};
    border-radius: 10px;
    padding: 4px 10px;
    font-size: {Fonts.SIZE_SM}px;
    font-weight: 600;
}}

QLabel[class="badge-warning"] {{
    background-color: {c.WARNING_BG};
    color: {c.WARNING};
    border-radius: 10px;
    padding: 4px 10px;
    font-size: {Fonts.SIZE_SM}px;
    font-weight: 600;
}}

/* ---- Message boxes ---- */
QMessageBox {{
    background-color: {c.SURFACE};
}}

/* ---- Date edit dropdown ---- */
QDateEdit::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet())

    font = QFont(Fonts.FAMILY, Fonts.SIZE_BASE)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.SURFACE_ALT))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.TEXT_INVERSE))
    app.setPalette(palette)
