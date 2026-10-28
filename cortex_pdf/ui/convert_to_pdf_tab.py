"""
Aba de Conversão de Outros Formatos para PDF.
Suporta DOCX, Imagens (PNG, JPG, BMP, WEBP, TIFF), HTML, Markdown, TXT, CSV e XLSX.
Segue o fluxo: Entrada -> Processamento -> Saída.
Utiliza ícones Font Awesome e tema claro/clean.
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cortex_pdf.core.converter_to_pdf import convert_to_pdf
from cortex_pdf.ui.components import (
    FileInputCard,
    OutputNamingCard,
    PipelineBanner,
    ResultStatusCard,
)
from cortex_pdf.ui.icons import fa_icon


class ConvertToPDFTab(QWidget):
    """Aba para converter documentos e imagens em arquivos PDF."""

    open_in_viewer = pyqtSignal(str)

    FILE_FILTER = (
        "Todos os Formatos Suportados (*.docx *.png *.jpg *.jpeg *.bmp *.webp *.tiff *.html *.htm *.txt *.md *.csv *.xlsx);;"
        "Documentos Word (*.docx);;"
        "Imagens (*.png *.jpg *.jpeg *.bmp *.webp *.tiff);;"
        "Web e Texto (*.html *.htm *.txt *.md);;"
        "Planilhas (*.xlsx *.csv)"
    )

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        lbl_title = QLabel("Converter Outros Formatos para PDF")
        lbl_title.setProperty("class", "PageHeaderTitle")
        lbl_desc = QLabel(
            "Transforme arquivos Word (.docx), Imagens (.png, .jpg, .webp), HTML, Markdown, TXT, Excel (.xlsx) e CSV em PDF."
        )
        lbl_desc.setProperty("class", "PageHeaderDesc")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addWidget(PipelineBanner())

        # Etapa 1: Entrada
        self.input_card = FileInputCard(
            title="1. Entrada — Selecionar Arquivo de Origem",
            subtitle="Formatos suportados: DOCX, PNG, JPG, BMP, WEBP, TIFF, HTML, TXT, MD, CSV, XLSX.",
            file_filter=self.FILE_FILTER,
        )
        self.input_card.file_selected.connect(self._on_file_selected)
        layout.addWidget(self.input_card)

        # Etapa 2: Processamento
        proc_card = QFrame()
        proc_card.setProperty("class", "StepCard")
        proc_layout = QVBoxLayout(proc_card)
        proc_layout.setContentsMargins(16, 14, 16, 14)
        proc_layout.setSpacing(6)

        lbl_proc = QLabel("2. Processamento — Detecção Automática de Formato")
        lbl_proc.setProperty("class", "StepTitle")
        self.format_detected_lbl = QLabel(
            "Selecione um arquivo na etapa 1. O motor de renderização preservará estrutura, tabelas e imagens."
        )
        self.format_detected_lbl.setProperty("class", "StepSubtitle")

        proc_layout.addWidget(lbl_proc)
        proc_layout.addWidget(self.format_detected_lbl)
        layout.addWidget(proc_card)

        # Etapa 3: Saída
        self.output_card = OutputNamingCard()
        layout.addWidget(self.output_card)

        # Botão
        self.convert_btn = QPushButton("Gerar Arquivo PDF")
        self.convert_btn.setIcon(fa_icon("file-pdf", color="#ffffff"))
        self.convert_btn.setProperty("class", "PrimaryButton")
        self.convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convert_btn.clicked.connect(self.run_conversion)
        layout.addWidget(self.convert_btn)

        self.result_card = ResultStatusCard()
        self.result_card.open_in_viewer_requested.connect(self.open_in_viewer.emit)
        layout.addWidget(self.result_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _on_file_selected(self, path_str: str) -> None:
        self.output_card.suggest_from_input(path_str)
        self.format_detected_lbl.setText(f"Arquivo pronto para conversão em PDF: {path_str}")
        self.format_detected_lbl.setStyleSheet("color: #2563eb; font-weight: 600;")

    def run_conversion(self) -> None:
        src = self.input_card.selected_path
        if not src:
            self.result_card.set_error("Selecione um arquivo de entrada para converter.")
            return

        try:
            res = convert_to_pdf(
                input_path=src,
                output_dir=self.output_card.output_dir,
                keep_original_name=self.output_card.keep_original_name,
                custom_name=self.output_card.custom_name,
            )
            self.result_card.set_success(res.message, res.output_path)
        except Exception as exc:
            self.result_card.set_error(str(exc))
