"""
Utilitário centralizado de ícones Font Awesome (via QtAwesome) para a interface clean do Cortex PDF Editor.
Substitui todos os emojis por ícones vetoriais nítidos (`fa5s.*`).
"""

from typing import Optional
import qtawesome as qta
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QLabel, QWidget


def fa_icon(name: str, color: str = "#334155") -> QIcon:
    """Retorna um QIcon do Font Awesome 5 Solid (`fa5s.<name>`)."""
    full_name = name if "." in name else f"fa5s.{name}"
    try:
        return qta.icon(full_name, color=color)
    except Exception:
        return QIcon()


def fa_pixmap_label(
    name: str,
    color: str = "#2563eb",
    size: int = 16,
    parent: Optional[QWidget] = None,
) -> QLabel:
    """Cria um QLabel exibindo um ícone Font Awesome renderizado na dimensão informada."""
    lbl = QLabel(parent)
    icon = fa_icon(name, color=color)
    pix = icon.pixmap(QSize(size, size))
    lbl.setPixmap(pix)
    lbl.setFixedSize(size + 4, size + 4)
    return lbl
