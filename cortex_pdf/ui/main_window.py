"""
Janela Principal do Cortex PDF Editor.
Integra todas as 7 funcionalidades com barra lateral moderna e fluxo simples:
Entrada -> Processamento -> Saída.
"""

from typing import Optional
from PyQt6.QtCore import Qt
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
from cortex_pdf.ui.merge_tab import MergeTab
from cortex_pdf.ui.split_tab import SplitTab
from cortex_pdf.ui.styles import MODERN_STYLESHEET
from cortex_pdf.ui.viewer_tab import ViewerTab


class CortexMainWindow(QMainWindow):
    """Janela principal com navegação lateral para todas as ferramentas de PDF."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.resize(1180, 780)
        self.setStyleSheet(MODERN_STYLESHEET)

        self._nav_buttons: list[QPushButton] = []
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
        sidebar.setFixedWidth(250)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 20, 16, 20)
        sb_layout.setSpacing(6)

        brand_title = QLabel("⚡ Cortex PDF")
        brand_title.setObjectName("BrandTitle")
        brand_sub = QLabel("Entrada → Processamento → Saída\n100% Local • Originais Intactos")
        brand_sub.setObjectName("BrandSubtitle")

        sb_layout.addWidget(brand_title)
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

        # Conecta sinal "Abrir no Visualizador" das abas geradoras de PDF
        for tab in (
            self.editor_tab,
            self.convert_to_pdf_tab,
            self.compress_tab,
            self.merge_tab,
            self.split_tab,
        ):
            tab.open_in_viewer.connect(self.open_pdf_in_viewer)

        pages = [
            ("📖  Visualizar PDF", self.viewer_tab),
            ("✏️  Editar Texto do PDF", self.editor_tab),
            ("🔄  Converter PDF p/ Outros", self.convert_from_pdf_tab),
            ("📄  Converter p/ PDF", self.convert_to_pdf_tab),
            ("🗜️  Comprimir PDF", self.compress_tab),
            ("🔗  Juntar PDFs", self.merge_tab),
            ("✂️  Dividir PDF", self.split_tab),
        ]

        for idx, (label, widget) in enumerate(pages):
            self.stack.addWidget(widget)
            btn = QPushButton(label)
            btn.setProperty("class", "NavButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=idx: self.switch_tab(i))
            sb_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sb_layout.addStretch()

        footer_lbl = QLabel("🔒 Privacidade Total:\nNenhum dado é coletado.\nArquivos originais preservados.")
        footer_lbl.setStyleSheet("color: #64748b; font-size: 11px; padding-top: 12px;")
        sb_layout.addWidget(footer_lbl)

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
            for i, btn in enumerate(self._nav_buttons):
                btn.setProperty("active", "true" if i == index else "false")
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def open_pdf_in_viewer(self, pdf_path: str) -> None:
        self.switch_tab(0)
        self.viewer_tab.load_pdf(pdf_path)
