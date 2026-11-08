# -*- coding: utf-8 -*-
"""Task Manager (PySide6)"""

import json
import os
import shutil
import sys
import uuid
from datetime import datetime, date, timedelta
from functools import reduce

from PySide6.QtCore import Qt, QRectF, QPointF, QPoint, QTimer, QEvent, Signal
from PySide6.QtGui import (QPainter, QColor, QPainterPath, QPen, QFont, QPixmap,
                           QShortcut, QKeySequence, QPalette)
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QScrollArea, QFrame, QSlider,
                               QMenu, QDialog, QFileDialog, QMessageBox, QButtonGroup,
                               QGraphicsDropShadowEffect)

APP_NAME = "TaskManager"
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
DATA_FILE = os.path.join(DATA_DIR, "data.json")
os.makedirs(DATA_DIR, exist_ok=True)

DT_FMT = "%Y-%m-%d %H:%M"
NO_PROJECT = "No Project"
ALL_TASKS = "All Tasks"
VIEW_ALL = "__all__"
VIEW_NONE = "__none__"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
MONTHS_S = [m[:3] for m in MONTHS]
DOW = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

THEMES = {
    "dark": dict(bg="#000000", panel="#0d0d0f", text="#f2f2f4", sub="#8a8a93",
                 accent="#7c9cff", accentHover="#97b0ff", late="#ff5c5c",
                 hover=(255, 255, 255, 14), field=(255, 255, 255, 17),
                 line=(255, 255, 255, 28), overlay=(0, 0, 0)),
    "light": dict(bg="#f6f6f8", panel="#ffffff", text="#17181c", sub="#6c6c76",
                  accent="#4f6ef7", accentHover="#6783fa", late="#e5393a",
                  hover=(0, 0, 0, 12), field=(0, 0, 0, 11),
                  line=(0, 0, 0, 28), overlay=(255, 255, 255)),
}
STATE = {"t": THEMES["dark"]}

DEFAULT_SETTINGS = dict(theme="dark", bg_path=None, dim=40, transp_on=False,
                        transp=25, win=None, sidebar_hidden=False)


def T():
    return STATE["t"]


def qc(v, a=None):
    c = QColor(*v) if isinstance(v, tuple) else QColor(v)
    if a is not None:
        c.setAlpha(a)
    return c


def css(v, a=None):
    c = qc(v, a)
    return f"rgba({c.red()},{c.green()},{c.blue()},{c.alpha()})"


QSS = """
QWidget { font-family: "Segoe UI", "Arial"; font-size: 10.5pt; color: %(text)s; }
QLabel { background: transparent; }
QLabel#h1 { font-size: 23pt; font-weight: 700; }
QLabel#h2 { font-size: 12.5pt; font-weight: 600; }
QLabel#appName { color: %(sub)s; font-size: 9.5pt; font-weight: 600; }
QLabel#sub { color: %(sub)s; font-size: 9.5pt; }
QLabel#secHead { color: %(sub)s; font-size: 9.5pt; font-weight: 600; }
QLabel#task { font-size: 11.5pt; }
QLabel#taskDone { font-size: 11.5pt; color: %(sub)s; }
QLabel#taskLate { font-size: 11.5pt; color: %(late)s; }
QLabel#chip { color: %(accent)s; background: %(accentSoft)s; border-radius: 8px; padding: 2px 9px; font-size: 9pt; }
QLabel#due { color: %(sub)s; font-size: 9.5pt; }
QLabel#dueLate { color: %(late)s; font-size: 9.5pt; font-weight: 600; }
QLabel#empty { color: %(sub)s; font-size: 11pt; }
QLabel#colon { font-size: 18pt; font-weight: 600; }
#addbar { background: %(field)s; border-radius: 14px; }
#timeBox { background: %(field)s; border-radius: 14px; }
QPushButton#ampm { background: transparent; color: %(sub)s; border: none; border-radius: 8px; padding: 7px 10px; font-weight: 600; }
QPushButton#ampm:hover { background: %(hover)s; }
QPushButton#ampm:checked { background: %(accent)s; color: white; }
QLineEdit#newTask { background: transparent; border: none; padding: 10px 8px; font-size: 11.5pt; selection-background-color: %(accent)s; selection-color: white; }
QLineEdit#newProj { background: %(field)s; border: 1px solid %(accent)s; border-radius: 9px; padding: 7px 10px; selection-background-color: %(accent)s; }
QPushButton#chipbtn { background: transparent; color: %(sub)s; border: none; border-radius: 9px; padding: 7px 12px; font-size: 9.5pt; }
QPushButton#chipbtn:hover { background: %(hover)s; color: %(text)s; }
QPushButton#chipbtnOn { background: %(accentSoft)s; color: %(accent)s; border: none; border-radius: 9px; padding: 7px 12px; font-size: 9.5pt; }
QPushButton#addBtn { background: %(accent)s; color: white; border: none; border-radius: 10px; padding: 8px 18px; font-weight: 600; }
QPushButton#addBtn:hover { background: %(accentHover)s; }
QPushButton#linkbtn { background: transparent; color: %(sub)s; border: none; text-align: left; padding: 9px 12px; border-radius: 9px; }
QPushButton#linkbtn:hover { background: %(hover)s; color: %(text)s; }
QPushButton#pill { background: %(field)s; color: %(text)s; border: none; border-radius: 9px; padding: 8px 14px; }
QPushButton#pill:hover { background: %(line)s; }
QPushButton#seg { background: %(field)s; color: %(sub)s; border: none; border-radius: 9px; padding: 8px 0; }
QPushButton#seg:checked { background: %(accent)s; color: white; font-weight: 600; }
#vline { background: %(line)s; }
#Settings { background: %(panelA)s; border: 1px solid %(line)s; border-radius: 14px; }
#dlg { background: transparent; }
#dlgFrame { background: %(panel)s; border: 1px solid %(line)s; border-radius: 16px; }
QSlider::groove:horizontal { height: 4px; background: %(line)s; border-radius: 2px; }
QSlider::sub-page:horizontal { background: %(accent)s; border-radius: 2px; }
QSlider::handle:horizontal { background: white; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
QAbstractScrollArea, QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: %(line2)s; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QMenu { background: %(panel)s; border: 1px solid %(line)s; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 8px 22px; border-radius: 7px; }
QMenu::item:selected { background: %(field)s; }
QToolTip { background: %(panel)s; color: %(text)s; border: 1px solid %(line)s; padding: 4px 8px; }
QMessageBox { background: %(panel)s; }
QMessageBox QPushButton { background: %(field)s; border: none; border-radius: 8px; padding: 7px 18px; min-width: 70px; }
QMessageBox QPushButton:hover { background: %(line)s; }
"""


def build_qss():
    t = T()
    d = dict(text=t["text"], sub=t["sub"], accent=t["accent"], accentHover=t["accentHover"],
             late=t["late"], panel=t["panel"], accentSoft=css(t["accent"], 38),
             field=css(t["field"]), hover=css(t["hover"]), line=css(t["line"]),
             line2=css(t["line"][:3] + (80,)), panelA=css(t["panel"], 246))
    return QSS % d


# ---------- data ----------
def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, DT_FMT)
    except ValueError:
        return None


def fmt_time12(d):
    return f"{d.hour % 12 or 12}:{d.minute:02d} {'AM' if d.hour < 12 else 'PM'}"


def fmt_deadline(s):
    d = parse_dt(s)
    if not d:
        return ""
    today = date.today()
    if d.date() == today:
        day = "Today"
    elif d.date() == today + timedelta(days=1):
        day = "Tomorrow"
    elif d.date() == today - timedelta(days=1):
        day = "Yesterday"
    elif d.year == today.year:
        day = f"{MONTHS_S[d.month - 1]} {d.day}"
    else:
        day = f"{MONTHS_S[d.month - 1]} {d.day}, {d.year}"
    return f"{day}  {fmt_time12(d)}"


def load_data():
    data = {"projects": [], "tasks": [], "settings": dict(DEFAULT_SETTINGS)}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        data["projects"] = list(raw.get("projects", []))
        data["tasks"] = list(raw.get("tasks", []))
        data["settings"].update(raw.get("settings", {}))
    except Exception:
        pass
    return data


def clear_layout(layout):
    while layout.count():
        it = layout.takeAt(0)
        w = it.widget()
        if w is not None:
            w.setParent(None)
            w.deleteLater()


def repolish(w):
    w.style().unpolish(w)
    w.style().polish(w)
    w.update()


def L(p, x1, y1, x2, y2):
    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def make_transparent(sa):
    """QScrollArea.setWidget() turns autoFillBackground back on, which paints a
    solid panel behind the lists. Turn it off for the area, viewport and content."""
    for w in (sa, sa.viewport(), sa.widget()):
        if w is None:
            continue
        w.setAutoFillBackground(False)
        pal = w.palette()
        for role in (QPalette.ColorRole.Window, QPalette.ColorRole.Base):
            pal.setColor(role, Qt.GlobalColor.transparent)
        w.setPalette(pal)


def inside(w, e):
    return e.button() == Qt.MouseButton.LeftButton and w.rect().contains(e.position().toPoint())


# ---------- custom painted widgets ----------
# NOTE: every clickable widget accepts the mouse press. Without that, the press
# travels up to the parent (e.g. the title bar) and the click never arrives.
class ClickLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, e):
        e.accept()

    def mouseReleaseEvent(self, e):
        if inside(self, e):
            self.clicked.emit()


class IconButton(QWidget):
    clicked = Signal()

    def __init__(self, kind, size=32, danger=False, tip=None, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.danger = danger
        self._hover = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tip:
            self.setToolTip(tip)

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def mousePressEvent(self, e):
        e.accept()

    def mouseReleaseEvent(self, e):
        if inside(self, e):
            self.clicked.emit()

    def paintEvent(self, e):
        t = T()
        k = self.kind
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        if self._hover:
            if k == "close":
                bg = QColor("#e5484d")
            elif self.danger:
                bg = qc(t["late"], 45)
            else:
                bg = qc(t["hover"])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 8, 8)
        if k == "close" and self._hover:
            col = QColor("white")
        elif self.danger and self._hover:
            col = qc(t["late"])
        elif self._hover:
            col = qc(t["text"])
        else:
            col = qc(t["sub"])
        pen = QPen(col, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        c = r.center()
        cx, cy = c.x(), c.y()
        if k == "min":
            L(p, cx - 5, cy + 3, cx + 5, cy + 3)
        elif k == "max":
            if self.window().isMaximized():
                p.drawRoundedRect(QRectF(cx - 5, cy - 2, 7, 7), 1.5, 1.5)
                L(p, cx - 2, cy - 5, cx + 5, cy - 5)
                L(p, cx + 5, cy - 5, cx + 5, cy + 2)
            else:
                p.drawRoundedRect(QRectF(cx - 5, cy - 5, 10, 10), 2, 2)
        elif k in ("close", "x"):
            s = 4.5 if k == "close" else 3.8
            L(p, cx - s, cy - s, cx + s, cy + s)
            L(p, cx - s, cy + s, cx + s, cy - s)
        elif k == "up":
            L(p, cx - 5, cy + 2.5, cx, cy - 2.5)
            L(p, cx, cy - 2.5, cx + 5, cy + 2.5)
        elif k == "down":
            L(p, cx - 5, cy - 2.5, cx, cy + 2.5)
            L(p, cx, cy + 2.5, cx + 5, cy - 2.5)
        elif k == "sidebar":
            p.drawRoundedRect(QRectF(cx - 7, cy - 6, 14, 12), 2.5, 2.5)
            L(p, cx - 2.5, cy - 6, cx - 2.5, cy + 6)
        elif k == "trash":
            L(p, cx - 6, cy - 4, cx + 6, cy - 4)
            L(p, cx - 2, cy - 4, cx - 2, cy - 6)
            L(p, cx - 2, cy - 6, cx + 2, cy - 6)
            L(p, cx + 2, cy - 6, cx + 2, cy - 4)
            path = QPainterPath()
            path.moveTo(cx - 4.5, cy - 2)
            path.lineTo(cx - 3.8, cy + 6)
            path.lineTo(cx + 3.8, cy + 6)
            path.lineTo(cx + 4.5, cy - 2)
            p.drawPath(path)
        elif k == "gear":
            p.translate(c)
            p.drawEllipse(QPointF(0, 0), 4.6, 4.6)
            for i in range(8):
                p.save()
                p.rotate(i * 45)
                L(p, 0, -6.2, 0, -8.2)
                p.restore()


class CheckCircle(QWidget):
    clicked = Signal()

    def __init__(self, checked=False, late=False, parent=None):
        super().__init__(parent)
        self.checked = checked
        self.late = late
        self._hover = False
        self.setFixedSize(24, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def mousePressEvent(self, e):
        e.accept()

    def mouseReleaseEvent(self, e):
        if inside(self, e):
            self.clicked.emit()

    def paintEvent(self, e):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QPointF(self.width() / 2, self.height() / 2)
        rad = 9.0
        if self.checked:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(qc(t["accent"]))
            p.drawEllipse(c, rad, rad)
            pen = QPen(QColor("white"), 2.0)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            path = QPainterPath()
            path.moveTo(c.x() - 4, c.y() + 0.5)
            path.lineTo(c.x() - 1, c.y() + 3.5)
            path.lineTo(c.x() + 4.2, c.y() - 3)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
        else:
            col = qc(t["late"]) if self.late else (qc(t["accent"]) if self._hover else qc(t["sub"]))
            if self._hover:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(qc(t["late"] if self.late else t["accent"], 40))
                p.drawEllipse(c, rad, rad)
            p.setPen(QPen(col, 1.8))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(c, rad, rad)


class Switch(QWidget):
    toggled = Signal(bool)

    def __init__(self, on=False, parent=None):
        super().__init__(parent)
        self.on = on
        self.setFixedSize(44, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_on(self, v):
        self.on = v
        self.update()

    def mousePressEvent(self, e):
        e.accept()

    def mouseReleaseEvent(self, e):
        if inside(self, e):
            self.on = not self.on
            self.update()
            self.toggled.emit(self.on)

    def paintEvent(self, e):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(qc(t["accent"]) if self.on else qc(t["text"], 55))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        x = r.right() - 12 if self.on else r.left() + 12
        p.setBrush(QColor("white"))
        p.drawEllipse(QPointF(x, r.center().y()), 9, 9)


class InlineEdit(QLineEdit):
    cancelled = Signal()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            return
        super().keyPressEvent(e)

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self.cancelled.emit()


# ---------- date + time pickers ----------
class CalendarPicker(QWidget):
    CW, CH, HEAD, WK = 44, 38, 42, 26

    def __init__(self, d):
        super().__init__()
        self.sel = d
        self.vy, self.vm = d.year, d.month
        self.hover = None
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(7 * self.CW, self.HEAD + self.WK + 6 * self.CH)

    def _first(self):
        first = date(self.vy, self.vm, 1)
        return first - timedelta(days=(first.weekday() + 1) % 7)

    def _cell_rect(self, i):
        return QRectF((i % 7) * self.CW, self.HEAD + self.WK + (i // 7) * self.CH,
                      self.CW, self.CH)

    def _index_at(self, pos):
        x, y = pos.x(), pos.y() - self.HEAD - self.WK
        if y < 0 or x < 0 or x >= 7 * self.CW or y >= 6 * self.CH:
            return None
        return int(y // self.CH) * 7 + int(x // self.CW)

    def shift(self, n):
        m = self.vm - 1 + n
        self.vy += m // 12
        self.vm = m % 12 + 1
        self.update()

    def leaveEvent(self, e):
        self.hover = None
        self.update()

    def mouseMoveEvent(self, e):
        h = self._index_at(e.position().toPoint())
        if h != self.hover:
            self.hover = h
            self.update()

    def mousePressEvent(self, e):
        e.accept()

    def mouseReleaseEvent(self, e):
        if not inside(self, e):
            return
        pos = e.position().toPoint()
        if pos.y() < self.HEAD:
            if pos.x() < 44:
                self.shift(-1)
            elif pos.x() > self.width() - 44:
                self.shift(1)
            return
        i = self._index_at(pos)
        if i is not None:
            self.sel = self._first() + timedelta(days=i)
            if (self.sel.year, self.sel.month) != (self.vy, self.vm):
                self.vy, self.vm = self.sel.year, self.sel.month
            self.update()

    def paintEvent(self, e):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        # header
        f = QFont(self.font())
        f.setPointSizeF(11.5)
        f.setBold(True)
        p.setFont(f)
        p.setPen(qc(t["text"]))
        p.drawText(QRectF(44, 0, w - 88, self.HEAD), Qt.AlignmentFlag.AlignCenter,
                   f"{MONTHS[self.vm - 1]} {self.vy}")
        pen = QPen(qc(t["sub"]), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        cy = self.HEAD / 2
        p.drawLine(QPointF(25, cy - 6), QPointF(19, cy))
        p.drawLine(QPointF(19, cy), QPointF(25, cy + 6))
        p.drawLine(QPointF(w - 25, cy - 6), QPointF(w - 19, cy))
        p.drawLine(QPointF(w - 19, cy), QPointF(w - 25, cy + 6))
        # weekday names
        f2 = QFont(self.font())
        f2.setPointSizeF(9)
        f2.setBold(True)
        p.setFont(f2)
        p.setPen(qc(t["sub"]))
        for i, name in enumerate(DOW):
            p.drawText(QRectF(i * self.CW, self.HEAD, self.CW, self.WK),
                       Qt.AlignmentFlag.AlignCenter, name)
        # days
        f3 = QFont(self.font())
        f3.setPointSizeF(10.5)
        first = self._first()
        today = date.today()
        for i in range(42):
            d = first + timedelta(days=i)
            r = self._cell_rect(i)
            c = r.center()
            in_month = (d.month == self.vm)
            if d == self.sel:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(qc(t["accent"]))
                p.drawEllipse(c, 16, 16)
                f3.setBold(True)
                p.setFont(f3)
                p.setPen(QColor("white"))
            else:
                if i == self.hover:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(qc(t["hover"]))
                    p.drawEllipse(c, 16, 16)
                if d == today:
                    p.setPen(QPen(qc(t["accent"]), 1.6))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawEllipse(c, 16, 16)
                f3.setBold(False)
                p.setFont(f3)
                p.setPen(qc(t["text"]) if in_month else qc(t["sub"], 110))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, str(d.day))


class NumberField(QWidget):
    """Custom number box (wheel, arrow keys, typing) - always draws its digits."""

    def __init__(self, lo, hi, value):
        super().__init__()
        self.lo, self.hi, self.v = lo, hi, value
        self.buf = ""
        self._hover = False
        self.setFixedSize(66, 46)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def value(self):
        return self.v

    def step(self, d):
        self.v += d
        if self.v > self.hi:
            self.v = self.lo
        elif self.v < self.lo:
            self.v = self.hi
        self.buf = ""
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self.update()

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self.buf = ""
        self.update()

    def mousePressEvent(self, e):
        self.setFocus()
        e.accept()

    def wheelEvent(self, e):
        self.step(1 if e.angleDelta().y() > 0 else -1)
        e.accept()

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key.Key_Up:
            self.step(1)
        elif k == Qt.Key.Key_Down:
            self.step(-1)
        elif len(e.text()) == 1 and e.text().isdigit():
            nb = self.buf + e.text()
            if len(nb) > 2 or int(nb) > self.hi:
                nb = e.text()
            self.buf = nb
            n = int(nb)
            if self.lo <= n <= self.hi:
                self.v = n
            self.update()
        else:
            super().keyPressEvent(e)

    def paintEvent(self, e):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        if self.hasFocus():
            p.setPen(QPen(qc(t["accent"]), 1.6))
            p.setBrush(qc(t["accent"], 28))
            p.drawRoundedRect(r, 11, 11)
        elif self._hover:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(qc(t["hover"]))
            p.drawRoundedRect(r, 11, 11)
        f = QFont(self.font())
        f.setPointSizeF(19)
        f.setBold(True)
        p.setFont(f)
        p.setPen(qc(t["text"]))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.v:02d}")


class TimePicker(QFrame):
    """12-hour time box: hours | minutes | AM/PM"""

    def __init__(self, hour24, minute):
        super().__init__()
        self.setObjectName("timeBox")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 12, 8)
        lay.setSpacing(4)

        self.h = NumberField(1, 12, hour24 % 12 or 12)
        self.m = NumberField(0, 59, minute)

        def column(field):
            v = QVBoxLayout()
            v.setSpacing(0)
            up = IconButton("up", 30)
            dn = IconButton("down", 30)
            up.clicked.connect(lambda: field.step(1))
            dn.clicked.connect(lambda: field.step(-1))
            v.addWidget(up, 0, Qt.AlignmentFlag.AlignHCenter)
            v.addWidget(field, 0, Qt.AlignmentFlag.AlignHCenter)
            v.addWidget(dn, 0, Qt.AlignmentFlag.AlignHCenter)
            return v

        lay.addLayout(column(self.h))
        colon = QLabel(":")
        colon.setObjectName("colon")
        lay.addWidget(colon)
        lay.addLayout(column(self.m))
        lay.addSpacing(8)

        ap = QVBoxLayout()
        ap.setSpacing(4)
        self.am = QPushButton("AM")
        self.pm = QPushButton("PM")
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        for b in (self.am, self.pm):
            b.setObjectName("ampm")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            grp.addButton(b)
            ap.addWidget(b)
        (self.pm if hour24 >= 12 else self.am).setChecked(True)
        lay.addLayout(ap)

    def hour24(self):
        return self.h.value() % 12 + (12 if self.pm.isChecked() else 0)

    def minute(self):
        return self.m.value()


class DeadlineDialog(QDialog):
    def __init__(self, parent, current):
        super().__init__(parent)
        self.setObjectName("dlg")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.outcome = "cancel"
        self.value = None
        cur = parse_dt(current)
        if not cur:
            cur = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        frame = QFrame()
        frame.setObjectName("dlgFrame")
        sh = QGraphicsDropShadowEffect(frame)
        sh.setBlurRadius(28)
        sh.setOffset(0, 6)
        sh.setColor(QColor(0, 0, 0, 130))
        frame.setGraphicsEffect(sh)
        outer.addWidget(frame)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.setSpacing(12)
        title = QLabel("Deadline")
        title.setObjectName("h2")
        lay.addWidget(title)

        self.cal = CalendarPicker(cur.date())
        lay.addWidget(self.cal, 0, Qt.AlignmentFlag.AlignHCenter)

        trow = QHBoxLayout()
        tl = QLabel("Time")
        tl.setObjectName("secHead")
        trow.addWidget(tl)
        trow.addStretch(1)
        self.time = TimePicker(cur.hour, cur.minute)
        trow.addWidget(self.time)
        lay.addLayout(trow)

        brow = QHBoxLayout()
        brow.setSpacing(8)
        ok = QPushButton("Save")
        ok.setObjectName("addBtn")
        clr = QPushButton("No deadline")
        clr.setObjectName("pill")
        cn = QPushButton("Cancel")
        cn.setObjectName("pill")
        for b in (ok, clr, cn):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(self._save)
        clr.clicked.connect(self._clear)
        cn.clicked.connect(self.reject)
        brow.addWidget(ok)
        brow.addWidget(clr)
        brow.addWidget(cn)
        lay.addLayout(brow)

    def _save(self):
        d = self.cal.sel
        self.value = datetime(d.year, d.month, d.day, self.time.hour24(),
                              self.time.minute()).strftime(DT_FMT)
        self.outcome = "save"
        self.accept()

    def _clear(self):
        self.value = None
        self.outcome = "clear"
        self.accept()

    def run(self):
        self.adjustSize()
        pg = self.parent().frameGeometry()
        self.move(pg.center() - self.rect().center())
        self.exec()


# ---------- list items ----------
class ProjItem(QWidget):
    clicked = Signal()
    removed = Signal()

    def __init__(self, text, count, selected, removable):
        super().__init__()
        self.selected = selected
        self._hover = False
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 6, 0)
        lay.setSpacing(6)
        name = QLabel(text)
        f = name.font()
        f.setBold(selected)
        name.setFont(f)
        lay.addWidget(name, 1)
        cnt = QLabel(str(count))
        cnt.setObjectName("sub")
        lay.addWidget(cnt)
        if removable:
            x = IconButton("x", 26, danger=True)
            sp = x.sizePolicy()
            sp.setRetainSizeWhenHidden(True)
            x.setSizePolicy(sp)
            x.setVisible(selected)
            x.clicked.connect(self.removed.emit)
            lay.addWidget(x)

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def mousePressEvent(self, e):
        e.accept()

    def mouseReleaseEvent(self, e):
        if inside(self, e):
            self.clicked.emit()

    def paintEvent(self, e):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = None
        if self.selected:
            col = qc(t["accent"], 40)
        elif self._hover:
            col = qc(t["hover"])
        if col:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(col)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(0, 1, 0, -1), 10, 10)


class TaskRow(QWidget):
    def __init__(self, app, task, done, show_project):
        super().__init__()
        self.late = app.is_late(task)
        self._hover = False
        self.setMinimumHeight(48)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 8, 8)
        lay.setSpacing(12)

        chk = CheckCircle(done, self.late)
        chk.clicked.connect(lambda i=task["id"]: app.toggle(i))
        lay.addWidget(chk)

        title = QLabel(task["title"])
        title.setWordWrap(True)
        title.setObjectName("taskDone" if done else ("taskLate" if self.late else "task"))
        if done:
            f = title.font()
            f.setStrikeOut(True)
            title.setFont(f)
        lay.addWidget(title, 1)

        if show_project and task.get("project"):
            chip = QLabel(task["project"])
            chip.setObjectName("chip")
            lay.addWidget(chip)

        if task.get("deadline"):
            due = ClickLabel(("Overdue · " if self.late else "") + fmt_deadline(task["deadline"]))
            due.setObjectName("dueLate" if self.late else "due")
            if not done:
                due.setCursor(Qt.CursorShape.PointingHandCursor)
                due.clicked.connect(lambda t_=task: app.edit_deadline(t_))
            lay.addWidget(due)
        elif not done:
            due = ClickLabel("+ Deadline")
            due.setObjectName("due")
            due.setCursor(Qt.CursorShape.PointingHandCursor)
            due.clicked.connect(lambda t_=task: app.edit_deadline(t_))
            lay.addWidget(due)

        self.del_btn = IconButton("trash", 30, danger=True)
        sp = self.del_btn.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.del_btn.setSizePolicy(sp)
        self.del_btn.setVisible(False)
        self.del_btn.clicked.connect(lambda i=task["id"]: app.delete_task(i))
        lay.addWidget(self.del_btn)

    def enterEvent(self, e):
        self._hover = True
        self.del_btn.setVisible(True)
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.del_btn.setVisible(False)
        self.update()

    def paintEvent(self, e):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = None
        if self.late:
            col = qc(t["late"], 46 if self._hover else 26)
        elif self._hover:
            col = qc(t["hover"])
        if col:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(col)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(0, 1, 0, -1), 11, 11)


# ---------- settings card ----------
class SettingsCard(QFrame):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setObjectName("Settings")
        self.setFixedWidth(310)
        v = QVBoxLayout(self)
        v.setContentsMargins(18, 14, 18, 18)
        v.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel("Appearance")
        title.setObjectName("h2")
        head.addWidget(title)
        head.addStretch(1)
        x = IconButton("x", 28)
        x.clicked.connect(self.hide)
        head.addWidget(x)
        v.addLayout(head)

        v.addWidget(self._cap("Theme"))
        seg = QHBoxLayout()
        seg.setSpacing(8)
        self.b_dark = QPushButton("Dark")
        self.b_light = QPushButton("Light")
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        for b in (self.b_dark, self.b_light):
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            grp.addButton(b)
            seg.addWidget(b)
        self.b_dark.clicked.connect(lambda: win.set_theme("dark"))
        self.b_light.clicked.connect(lambda: win.set_theme("light"))
        v.addLayout(seg)

        v.addWidget(self._cap("Background"))
        brow = QHBoxLayout()
        brow.setSpacing(8)
        pick = QPushButton("Choose image")
        rem = QPushButton("Remove")
        for b in (pick, rem):
            b.setObjectName("pill")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            brow.addWidget(b)
        pick.clicked.connect(win.choose_bg)
        rem.clicked.connect(win.remove_bg)
        v.addLayout(brow)

        row, self.dim_val = self._row("Background dim")
        v.addLayout(row)
        self.dim_sl = self._slider(0, 90)
        self.dim_sl.valueChanged.connect(win.set_dim)
        v.addWidget(self.dim_sl)

        srow = QHBoxLayout()
        sl = QLabel("Transparent window")
        srow.addWidget(sl)
        srow.addStretch(1)
        self.sw = Switch()
        self.sw.toggled.connect(win.set_transp_on)
        srow.addWidget(self.sw)
        v.addLayout(srow)

        row, self.tr_val = self._row("Transparency")
        v.addLayout(row)
        self.tr_sl = self._slider(0, 90)
        self.tr_sl.valueChanged.connect(win.set_transp)
        v.addWidget(self.tr_sl)

        self.sync()

    def _cap(self, text):
        l = QLabel(text)
        l.setObjectName("secHead")
        return l

    def _row(self, text):
        r = QHBoxLayout()
        l = QLabel(text)
        l.setObjectName("sub")
        r.addWidget(l)
        r.addStretch(1)
        val = QLabel("0%")
        val.setObjectName("sub")
        r.addWidget(val)
        return r, val

    def _slider(self, a, b):
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(a, b)
        s.setCursor(Qt.CursorShape.PointingHandCursor)
        return s

    def sync(self):
        s = self.win.s
        (self.b_dark if s["theme"] == "dark" else self.b_light).setChecked(True)
        for sl, key in ((self.dim_sl, "dim"), (self.tr_sl, "transp")):
            sl.blockSignals(True)
            sl.setValue(int(s[key]))
            sl.blockSignals(False)
        self.dim_val.setText(f"{int(s['dim'])}%")
        self.tr_val.setText(f"{int(s['transp'])}%")
        self.sw.set_on(bool(s["transp_on"]))


# ---------- title bar ----------
class TitleBar(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 8, 0)
        lay.setSpacing(2)
        self.side_btn = IconButton("sidebar", 34, tip="Show / hide projects  (Ctrl+B)")
        self.side_btn.clicked.connect(win.toggle_sidebar)
        lay.addWidget(self.side_btn)
        lay.addSpacing(4)
        name = QLabel("Task Manager")
        name.setObjectName("appName")
        lay.addWidget(name)
        lay.addStretch(1)
        self.gear = IconButton("gear", 34, tip="Appearance")
        self.gear.clicked.connect(win.toggle_settings)
        lay.addWidget(self.gear)
        lay.addSpacing(6)
        mn = IconButton("min", 34, tip="Minimize")
        mn.clicked.connect(win.showMinimized)
        self.mx = IconButton("max", 34, tip="Maximize / restore")
        self.mx.clicked.connect(win.toggle_max)
        cl = IconButton("close", 34, tip="Close")
        cl.clicked.connect(win.close)
        for b in (mn, self.mx, cl):
            lay.addWidget(b)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            h = self.win.windowHandle()
            if h is not None:
                h.startSystemMove()
        e.accept()

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.win.toggle_max()


# ---------- main window ----------
class MainWindow(QWidget):
    M = 8

    def __init__(self):
        super().__init__()
        self.data = load_data()
        self.s = self.data["settings"]
        STATE["t"] = THEMES.get(self.s["theme"], THEMES["dark"])
        QApplication.instance().setStyleSheet(build_qss())

        self.view = VIEW_ALL
        self.new_deadline = None
        self.new_proj = None
        self.done_collapsed = False
        self._pix = None
        self._cpix = None
        self._ckey = None
        self._late_sig = None

        self.setWindowTitle("Task Manager")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(860, 560)

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self.save)

        self.build_ui()
        self.load_bg()
        self.settings.sync()
        self.apply_sidebar()
        QShortcut(QKeySequence("Ctrl+B"), self, activated=self.toggle_sidebar)

        w = self.s.get("win")
        if isinstance(w, list) and len(w) == 4 and w[2] >= 860 and w[3] >= 560:
            self.setGeometry(*w)
        else:
            self.resize(1100, 720)

        self.refresh_all()
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self.tick)
        self.tick_timer.start(20000)

    # ----- saving -----
    def save(self):
        try:
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, DATA_FILE)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save data:\n{e}")

    def schedule_save(self):
        self._save_timer.start()

    def closeEvent(self, e):
        if not self.isMaximized():
            g = self.geometry()
            self.s["win"] = [g.x(), g.y(), g.width(), g.height()]
        self.save()
        super().closeEvent(e)

    # ----- UI -----
    def build_ui(self):
        M = self.M
        root = QVBoxLayout(self)
        root.setContentsMargins(M, M, M, M)
        root.setSpacing(0)
        self.root_layout = root

        self.titlebar = TitleBar(self)
        root.addWidget(self.titlebar)

        body = QWidget()
        body.setCursor(Qt.CursorShape.ArrowCursor)
        bl = QHBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)
        root.addWidget(body, 1)

        # sidebar
        self.side = QWidget()
        self.side.setFixedWidth(250)
        sv = QVBoxLayout(self.side)
        sv.setContentsMargins(10, 6, 14, 14)
        sv.setSpacing(6)
        cap = QLabel("PROJECTS")
        cap.setObjectName("secHead")
        cap.setContentsMargins(14, 0, 0, 0)
        sv.addWidget(cap)

        self.proj_scroll = QScrollArea()
        self.proj_scroll.setWidgetResizable(True)
        self.proj_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.proj_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.proj_scroll.viewport().setAutoFillBackground(False)
        pc = QWidget()
        pc.setAutoFillBackground(False)
        self.pl = QVBoxLayout(pc)
        self.pl.setContentsMargins(0, 0, 0, 0)
        self.pl.setSpacing(2)
        self.proj_scroll.setWidget(pc)
        make_transparent(self.proj_scroll)
        sv.addWidget(self.proj_scroll, 1)

        self.newproj_btn = QPushButton("+  New project")
        self.newproj_btn.setObjectName("linkbtn")
        self.newproj_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.newproj_btn.clicked.connect(self.start_new_project)
        sv.addWidget(self.newproj_btn)
        self.newproj_edit = InlineEdit()
        self.newproj_edit.setObjectName("newProj")
        self.newproj_edit.setPlaceholderText("Project name, then Enter")
        self.newproj_edit.returnPressed.connect(self.submit_project)
        self.newproj_edit.cancelled.connect(self.cancel_new_project)
        self.newproj_edit.hide()
        sv.addWidget(self.newproj_edit)
        bl.addWidget(self.side)

        self.vline = QFrame()
        self.vline.setObjectName("vline")
        self.vline.setFixedWidth(1)
        bl.addWidget(self.vline)

        # main area
        main = QWidget()
        mv = QVBoxLayout(main)
        mv.setContentsMargins(30, 10, 30, 20)
        mv.setSpacing(14)

        hv = QVBoxLayout()
        hv.setSpacing(0)
        self.title_lbl = QLabel("")
        self.title_lbl.setObjectName("h1")
        self.sub_lbl = QLabel("")
        self.sub_lbl.setObjectName("sub")
        hv.addWidget(self.title_lbl)
        hv.addWidget(self.sub_lbl)
        mv.addLayout(hv)

        bar = QFrame()
        bar.setObjectName("addbar")
        ab = QHBoxLayout(bar)
        ab.setContentsMargins(10, 5, 6, 5)
        ab.setSpacing(4)
        self.edit = QLineEdit()
        self.edit.setObjectName("newTask")
        self.edit.setPlaceholderText("Add a new task...")
        self.edit.returnPressed.connect(self.add_task)
        ab.addWidget(self.edit, 1)
        self.proj_btn = QPushButton("")
        self.proj_btn.setObjectName("chipbtn")
        self.proj_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.proj_btn.clicked.connect(self.pick_project)
        ab.addWidget(self.proj_btn)
        self.due_btn = QPushButton("")
        self.due_btn.setObjectName("chipbtn")
        self.due_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.due_btn.clicked.connect(self.pick_new_deadline)
        ab.addWidget(self.due_btn)
        add = QPushButton("Add")
        add.setObjectName("addBtn")
        add.setCursor(Qt.CursorShape.PointingHandCursor)
        add.clicked.connect(self.add_task)
        ab.addWidget(add)
        mv.addWidget(bar)

        self.task_scroll = QScrollArea()
        self.task_scroll.setWidgetResizable(True)
        self.task_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.task_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.task_scroll.viewport().setAutoFillBackground(False)
        tc = QWidget()
        tc.setAutoFillBackground(False)
        self.tl = QVBoxLayout(tc)
        self.tl.setContentsMargins(0, 0, 6, 0)
        self.tl.setSpacing(2)
        self.task_scroll.setWidget(tc)
        make_transparent(self.task_scroll)
        mv.addWidget(self.task_scroll, 1)
        bl.addWidget(main, 1)

        self.settings = SettingsCard(self)
        self.settings.hide()
        self.update_chips()

    # ----- sidebar / settings / window -----
    def apply_sidebar(self):
        hidden = bool(self.s.get("sidebar_hidden"))
        self.side.setVisible(not hidden)
        self.vline.setVisible(not hidden)

    def toggle_sidebar(self):
        self.s["sidebar_hidden"] = not self.s.get("sidebar_hidden")
        self.apply_sidebar()
        self.schedule_save()

    def toggle_settings(self):
        if self.settings.isVisible():
            self.settings.hide()
        else:
            self.settings.sync()
            self.settings.adjustSize()
            self.place_settings()
            self.settings.show()
            self.settings.raise_()

    def place_settings(self):
        self.settings.move(self.width() - self.margin() - self.settings.width() - 14,
                           self.margin() + 48)

    def margin(self):
        return 0 if self.isMaximized() else self.M

    def toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def changeEvent(self, e):
        if e.type() == QEvent.Type.WindowStateChange:
            m = self.margin()
            self.root_layout.setContentsMargins(m, m, m, m)
            self.titlebar.mx.update()
            self.update()
            if self.settings.isVisible():
                self.place_settings()
        super().changeEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "settings") and self.settings.isVisible():
            self.place_settings()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape and self.settings.isVisible():
            self.settings.hide()
            return
        super().keyPressEvent(e)

    # ----- edge resizing -----
    def _edges(self, pos):
        if self.isMaximized():
            return None
        m, w, h = self.M, self.width(), self.height()
        es = []
        if pos.x() < m:
            es.append(Qt.Edge.LeftEdge)
        if pos.x() > w - m:
            es.append(Qt.Edge.RightEdge)
        if pos.y() < m:
            es.append(Qt.Edge.TopEdge)
        if pos.y() > h - m:
            es.append(Qt.Edge.BottomEdge)
        return reduce(lambda a, b: a | b, es) if es else None

    def mouseMoveEvent(self, e):
        ed = self._edges(e.position().toPoint())
        cur = Qt.CursorShape.ArrowCursor
        if ed is not None:
            hor = bool(ed & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge))
            ver = bool(ed & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge))
            if hor and ver:
                diag_main = (bool(ed & Qt.Edge.LeftEdge) == bool(ed & Qt.Edge.TopEdge))
                cur = Qt.CursorShape.SizeFDiagCursor if diag_main else Qt.CursorShape.SizeBDiagCursor
            elif hor:
                cur = Qt.CursorShape.SizeHorCursor
            else:
                cur = Qt.CursorShape.SizeVerCursor
        self.setCursor(cur)
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            ed = self._edges(e.position().toPoint())
            if ed is not None and self.windowHandle() is not None:
                self.windowHandle().startSystemResize(ed)
                return
        super().mousePressEvent(e)

    # ----- painting -----
    def opacity(self):
        return 1.0 - self.s["transp"] / 100.0 if self.s["transp_on"] else 1.0

    def load_bg(self):
        self._pix = None
        self._ckey = None
        path = self.s.get("bg_path")
        if path and os.path.exists(path):
            pm = QPixmap(path)
            if not pm.isNull():
                if pm.width() > 2400:
                    pm = pm.scaledToWidth(2400, Qt.TransformationMode.SmoothTransformation)
                self._pix = pm

    def _compose(self, w, h):
        dpr = self.devicePixelRatioF()
        pw, ph = max(int(w * dpr), 1), max(int(h * dpr), 1)
        key = (pw, ph, self.s.get("bg_path"), self.s["dim"], self.s["theme"])
        if key == self._ckey and self._cpix is not None:
            return self._cpix
        t = T()
        pm = QPixmap(pw, ph)
        pm.fill(qc(t["bg"]))
        src = self._pix.scaled(pw, ph, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
        pp = QPainter(pm)
        pp.drawPixmap(0, 0, src, (src.width() - pw) // 2, (src.height() - ph) // 2, pw, ph)
        ov = t["overlay"]
        pp.fillRect(0, 0, pw, ph, QColor(ov[0], ov[1], ov[2], int(255 * self.s["dim"] / 100.0)))
        pp.end()
        self._cpix, self._ckey = pm, key
        return pm

    def paintEvent(self, e):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # near-invisible fill so the border area still receives the mouse (for resizing)
        p.fillRect(self.rect(), QColor(0, 0, 0, 1))
        m = self.margin()
        r = QRectF(self.rect()).adjusted(m, m, -m, -m)
        path = QPainterPath()
        radius = 0 if self.isMaximized() else 16
        path.addRoundedRect(r, radius, radius)
        op = self.opacity()
        p.setClipPath(path)
        if self._pix is not None:
            pm = self._compose(int(r.width()), int(r.height()))
            p.setOpacity(op)
            p.drawPixmap(r, pm, QRectF(pm.rect()))
            p.setOpacity(1.0)
        else:
            p.fillRect(r, qc(t["bg"], int(255 * op)))
        p.setClipping(False)
        p.setPen(QPen(qc(t["line"]), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

    # ----- appearance -----
    def set_theme(self, name):
        if self.s["theme"] == name:
            return
        self.s["theme"] = name
        STATE["t"] = THEMES[name]
        QApplication.instance().setStyleSheet(build_qss())
        self._ckey = None
        for w in self.findChildren(QWidget):
            w.update()
        self.update()
        self.refresh_all()
        self.settings.sync()
        self.schedule_save()

    def set_dim(self, v):
        self.s["dim"] = int(v)
        self.settings.dim_val.setText(f"{int(v)}%")
        self.update()
        self.schedule_save()

    def set_transp_on(self, on):
        self.s["transp_on"] = bool(on)
        self.update()
        self.schedule_save()

    def set_transp(self, v):
        self.s["transp"] = int(v)
        self.settings.tr_val.setText(f"{int(v)}%")
        self.update()
        self.schedule_save()

    def choose_bg(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose a background image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All files (*.*)")
        if not path:
            return
        if QPixmap(path).isNull():
            QMessageBox.warning(self, "Error", "Could not open this image.")
            return
        ext = os.path.splitext(path)[1].lower() or ".png"
        dest = os.path.join(DATA_DIR, f"bg_{uuid.uuid4().hex[:8]}{ext}")
        try:
            shutil.copyfile(path, dest)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not copy the image:\n{e}")
            return
        self._drop_old_bg()
        self.s["bg_path"] = dest
        self.load_bg()
        self.update()
        self.save()

    def _drop_old_bg(self):
        old = self.s.get("bg_path")
        if old and os.path.exists(old) and os.path.dirname(old) == DATA_DIR:
            try:
                os.remove(old)
            except OSError:
                pass

    def remove_bg(self):
        self._drop_old_bg()
        self.s["bg_path"] = None
        self.load_bg()
        self.update()
        self.save()

    # ----- tasks -----
    def is_late(self, task):
        if task.get("done"):
            return False
        d = parse_dt(task.get("deadline"))
        return bool(d and d < datetime.now())

    def late_signature(self):
        return tuple(sorted(x["id"] for x in self.data["tasks"] if self.is_late(x)))

    def tick(self):
        if self.late_signature() != self._late_sig:
            self.refresh_tasks()

    def find(self, tid):
        for x in self.data["tasks"]:
            if x["id"] == tid:
                return x
        return None

    def add_task(self):
        title = self.edit.text().strip()
        if not title:
            return
        self.data["tasks"].append({
            "id": uuid.uuid4().hex, "title": title, "project": self.new_proj,
            "deadline": self.new_deadline, "done": False,
            "created": datetime.now().isoformat(),
        })
        self.save()
        self.edit.clear()
        self.new_deadline = None
        self.update_chips()
        self.refresh_all()
        self.edit.setFocus()

    def toggle(self, tid):
        x = self.find(tid)
        if x:
            x["done"] = not x["done"]
            x["done_at"] = datetime.now().isoformat() if x["done"] else ""
            self.save()
            self.refresh_all()

    def delete_task(self, tid):
        self.data["tasks"] = [x for x in self.data["tasks"] if x["id"] != tid]
        self.save()
        self.refresh_all()

    # ----- deadlines -----
    def update_chips(self):
        self.proj_btn.setText((self.new_proj or NO_PROJECT) + "  ▾")
        self.due_btn.setText(fmt_deadline(self.new_deadline) if self.new_deadline else "Deadline")
        self.due_btn.setObjectName("chipbtnOn" if self.new_deadline else "chipbtn")
        repolish(self.due_btn)

    def pick_project(self):
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        acts = {menu.addAction(NO_PROJECT): None}
        for p in self.data["projects"]:
            acts[menu.addAction(p)] = p
        chosen = menu.exec(self.proj_btn.mapToGlobal(QPoint(0, self.proj_btn.height() + 4)))
        if chosen is not None:
            self.new_proj = acts[chosen]
            self.update_chips()

    def pick_new_deadline(self):
        dlg = DeadlineDialog(self, self.new_deadline)
        dlg.run()
        if dlg.outcome == "save":
            self.new_deadline = dlg.value
        elif dlg.outcome == "clear":
            self.new_deadline = None
        self.update_chips()

    def edit_deadline(self, task):
        dlg = DeadlineDialog(self, task.get("deadline"))
        dlg.run()
        if dlg.outcome == "save":
            task["deadline"] = dlg.value
        elif dlg.outcome == "clear":
            task["deadline"] = None
        else:
            return
        self.save()
        self.refresh_all()

    # ----- projects -----
    def start_new_project(self):
        self.newproj_btn.hide()
        self.newproj_edit.show()
        self.newproj_edit.setFocus()

    def cancel_new_project(self):
        self.newproj_edit.clear()
        self.newproj_edit.hide()
        self.newproj_btn.show()

    def submit_project(self):
        name = self.newproj_edit.text().strip()
        self.cancel_new_project()
        if not name or name in (NO_PROJECT, ALL_TASKS):
            return
        if name in self.data["projects"]:
            QMessageBox.information(self, "Notice", "This project already exists.")
            return
        self.data["projects"].append(name)
        self.save()
        self.set_view(name)

    def delete_project(self, name):
        box = QMessageBox(self)
        box.setWindowTitle("Delete project")
        box.setText(f"Delete project “{name}”?\nIts tasks will move to “{NO_PROJECT}”.")
        yes = box.addButton("Delete", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is not yes:
            return
        self.data["projects"].remove(name)
        for x in self.data["tasks"]:
            if x.get("project") == name:
                x["project"] = None
        if self.new_proj == name:
            self.new_proj = None
        self.save()
        self.set_view(VIEW_ALL)

    def set_view(self, view):
        self.view = view
        self.new_proj = view if view in self.data["projects"] else None
        self.update_chips()
        self.refresh_all()

    # ----- lists -----
    def refresh_all(self):
        self.refresh_projects()
        self.refresh_tasks()

    def count_active(self, pred):
        return sum(1 for x in self.data["tasks"] if not x["done"] and pred(x))

    def refresh_projects(self):
        clear_layout(self.pl)

        def item(label, view, n, removable=False):
            it = ProjItem(label, n, self.view == view, removable)
            it.clicked.connect(lambda v=view: self.set_view(v))
            if removable:
                it.removed.connect(lambda nm=view: self.delete_project(nm))
            self.pl.addWidget(it)

        item(ALL_TASKS, VIEW_ALL, self.count_active(lambda x: True))
        item(NO_PROJECT, VIEW_NONE, self.count_active(lambda x: not x.get("project")))
        for p in self.data["projects"]:
            item(p, p, self.count_active(lambda x, p=p: x.get("project") == p), True)
        self.pl.addStretch(1)

    def filtered(self):
        tasks = self.data["tasks"]
        if self.view == VIEW_ALL:
            return tasks
        if self.view == VIEW_NONE:
            return [x for x in tasks if not x.get("project")]
        return [x for x in tasks if x.get("project") == self.view]

    def refresh_tasks(self):
        clear_layout(self.tl)
        if self.view == VIEW_ALL:
            self.title_lbl.setText(ALL_TASKS)
        elif self.view == VIEW_NONE:
            self.title_lbl.setText(NO_PROJECT)
        else:
            self.title_lbl.setText(self.view)

        tasks = self.filtered()
        active = [x for x in tasks if not x["done"]]
        done = [x for x in tasks if x["done"]]
        active.sort(key=lambda x: (x.get("deadline") is None, x.get("deadline") or "",
                                   x.get("created", "")))
        done.sort(key=lambda x: x.get("done_at", ""), reverse=True)
        n = len(active)
        self.sub_lbl.setText(f"{n} task{'s' if n != 1 else ''} left" if n else "All done")

        show_proj = (self.view == VIEW_ALL)
        if not active and not done:
            lab = QLabel("No tasks here yet.\nType a task above and press Enter.")
            lab.setObjectName("empty")
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lab.setMinimumHeight(160)
            self.tl.addWidget(lab)
        for x in active:
            self.tl.addWidget(TaskRow(self, x, False, show_proj))

        if done:
            arrow = "▸" if self.done_collapsed else "▾"
            head = ClickLabel(f"{arrow}  Done ({len(done)})")
            head.setObjectName("secHead")
            head.setCursor(Qt.CursorShape.PointingHandCursor)
            head.setContentsMargins(12, 16, 0, 6)
            head.clicked.connect(self.toggle_done_section)
            self.tl.addWidget(head)
            if not self.done_collapsed:
                for x in done:
                    self.tl.addWidget(TaskRow(self, x, True, show_proj))
        self.tl.addStretch(1)
        self._late_sig = self.late_signature()

    def toggle_done_section(self):
        self.done_collapsed = not self.done_collapsed
        self.refresh_tasks()


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    app.setFont(QFont("Segoe UI", 10))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
