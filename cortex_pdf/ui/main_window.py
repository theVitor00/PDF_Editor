"""
Janela Principal do Cortex PDF Editor.
Integra todas as 7 funcionalidades com barra lateral moderna e fluxo simples:
Entrada -> Processamento -> Saída.
Utiliza ícones Font Awesome (via QtAwesome) e tema clean e claro.
"""

from typing import Optional
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from cortex_pdf import __app_name__, __version__
from cortex_pdf.ui.compress_tab import CompressTab
from cortex_pdf.ui.convert_from_pdf_tab import ConvertFromPDFTab
from cortex_pdf.ui.convert_to_pdf_tab import ConvertToPDFTab
from cortex_pdf.ui.editor_tab import EditorTab
from cortex_pdf.ui.icons import fa_icon, fa_pixmap_label
from cortex_pdf.ui.merge_tab import MergeTab
from cortex_pdf.ui.split_tab import SplitTab
from cortex_pdf.ui.styles import MODERN_STYLESHEET
from cortex_pdf.ui.viewer_tab import ViewerTab


class CortexMainWindow(QMainWindow):
    """Janela principal com navegação lateral clean e ícones Font Awesome."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.setWindowIcon(fa_icon("file-pdf", color="#2563eb"))
        self.resize(1180, 780)
        self.setStyleSheet(MODERN_STYLESHEET)

        self._nav_buttons: list[tuple[QPushButton, str]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("MainCentralWidget")
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Barra Lateral
        sidebar = QFrame()
        sidebar.setObjectName("SidebarFrame")
        sidebar.setFixedWidth(256)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 20, 16, 20)
        sb_layout.setSpacing(6)

        brand_row = QHBoxLayout()
        brand_icon = fa_pixmap_label("file-pdf", color="#2563eb", size=22)
        brand_title = QLabel("Cortex PDF")
        brand_title.setObjectName("BrandTitle")
        brand_row.addWidget(brand_icon)
        brand_row.addWidget(brand_title, stretch=1)

        brand_sub = QLabel("Entrada → Processamento → Saída\n100% Local • Originais Intactos")
        brand_sub.setObjectName("BrandSubtitle")

        sb_layout.addLayout(brand_row)
        sb_layout.addWidget(brand_sub)

        # Abas / Telas
        self.stack = QStackedWidget()

        self.viewer_tab = ViewerTab()
        self.editor_tab = EditorTab()
        self.convert_from_pdf_tab = ConvertFromPDFTab()
        self.convert_to_pdf_tab = ConvertToPDFTab()
        self.compress_tab = CompressTab()
        self.merge_tab = MergeTab()
        self.split_tab = SplitTab()

        for tab in (
            self.editor_tab,
            self.convert_to_pdf_tab,
            self.compress_tab,
            self.merge_tab,
            self.split_tab,
        ):
            tab.open_in_viewer.connect(self.open_pdf_in_viewer)

        pages = [
            ("book-open", "Visualizar PDF", self.viewer_tab),
            ("edit", "Editar Texto do PDF", self.editor_tab),
            ("exchange-alt", "Converter PDF p/ Outros", self.convert_from_pdf_tab),
            ("file-export", "Converter p/ PDF", self.convert_to_pdf_tab),
            ("compress-arrows-alt", "Comprimir PDF", self.compress_tab),
            ("object-group", "Juntar PDFs", self.merge_tab),
            ("cut", "Dividir PDF", self.split_tab),
        ]

        for idx, (icon_name, label, widget) in enumerate(pages):
            self.stack.addWidget(widget)
            btn = QPushButton(f"  {label}")
            btn.setIcon(fa_icon(icon_name, color="#475569"))
            btn.setIconSize(QSize(16, 16))
            btn.setProperty("class", "NavButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=idx: self.switch_tab(i))
            sb_layout.addWidget(btn)
            self._nav_buttons.append((btn, icon_name))

        sb_layout.addStretch()

        footer_row = QHBoxLayout()
        footer_icon = fa_pixmap_label("shield-alt", color="#64748b", size=14)
        footer_lbl = QLabel("Privacidade Total:\nNenhum dado é coletado.\nArquivos originais preservados.")
        footer_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        footer_row.addWidget(footer_icon)
        footer_row.addWidget(footer_lbl, stretch=1)
        sb_layout.addLayout(footer_row)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack, stretch=1)

        status_bar = QStatusBar()
        status_bar.showMessage(
            "Pronto — Selecione uma ferramenta no menu lateral. O arquivo original nunca é modificado."
        )
        self.setStatusBar(status_bar)

        self.switch_tab(0)

    def switch_tab(self, index: int) -> None:
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            for i, (btn, icon_name) in enumerate(self._nav_buttons):
                is_active = i == index
                btn.setProperty("active", "true" if is_active else "false")
                btn.setIcon(fa_icon(icon_name, color="#1d4ed8" if is_active else "#475569"))
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def open_pdf_in_viewer(self, pdf_path: str) -> None:
        self.switch_tab(0)
        self.viewer_tab.load_pdf(pdf_path)
