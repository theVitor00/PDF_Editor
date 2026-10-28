"""
Aba de Conversão de PDF para diversos formatos (DOCX, HTML, Markdown, TXT, PNG, JPG).
Segue o fluxo: Entrada -> Processamento -> Saída.
"""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cortex_pdf.core.converter_from_pdf import convert_pdf_to_format
from cortex_pdf.ui.components import (
    FileInputCard,
    OutputNamingCard,
    PipelineBanner,
    ResultStatusCard,
)


class ConvertFromPDFTab(QWidget):
    """Aba para converter documentos PDF para outros formatos mantendo a formatação."""

    FORMAT_ITEMS = [
        ("Word Document (.docx) — Alta Fidelidade de Layout", "docx"),
        ("Página Web (.html) — Fidelidade Visual e Posicionamento", "html"),
        ("Markdown (.md) — Texto Estruturado com Títulos", "md"),
        ("Texto Puro (.txt) — Blocos Ordenados", "txt"),
        ("Imagem PNG (.png) — Alta Resolução por Página", "png"),
        ("Imagem JPEG (.jpg) — Compacta por Página", "jpg"),
    ]

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

        lbl_title = QLabel("Converter PDF para Outros Formatos")
        lbl_title.setProperty("class", "PageHeaderTitle")
        lbl_desc = QLabel(
            "Exporte arquivos PDF para Word (.docx), HTML, Markdown, Texto ou Imagens preservando a formatação."
        )
        lbl_desc.setProperty("class", "PageHeaderDesc")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addWidget(PipelineBanner())

        # Etapa 1: Entrada
        self.input_card = FileInputCard(
            title="1. Entrada — Selecionar Arquivo PDF",
            subtitle="Escolha o documento PDF que deseja converter.",
            file_filter="Arquivos PDF (*.pdf)",
        )
        self.input_card.file_selected.connect(self._on_file_selected)
        layout.addWidget(self.input_card)

        # Etapa 2: Processamento
        proc_card = QFrame()
        proc_card.setProperty("class", "StepCard")
        proc_layout = QVBoxLayout(proc_card)
        proc_layout.setContentsMargins(16, 14, 16, 14)
        proc_layout.setSpacing(10)

        lbl_proc = QLabel("2. Processamento — Formato de Destino")
        lbl_proc.setProperty("class", "StepTitle")

        row = QHBoxLayout()
        row.addWidget(QLabel("Formato de saída desejado:"))
        self.format_combo = QComboBox()
        for label, code in self.FORMAT_ITEMS:
            self.format_combo.addItem(label, userData=code)

        row.addWidget(self.format_combo, stretch=1)
        row.addSpacing(12)
        row.addWidget(QLabel("Resolução (DPI p/ imagens):"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(200)
        row.addWidget(self.dpi_spin)

        proc_layout.addWidget(lbl_proc)
        proc_layout.addLayout(row)
        layout.addWidget(proc_card)

        # Etapa 3: Saída
        self.output_card = OutputNamingCard()
        layout.addWidget(self.output_card)

        # Ação
        self.convert_btn = QPushButton("🔄 Converter PDF Agora")
        self.convert_btn.setProperty("class", "PrimaryButton")
        self.convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convert_btn.clicked.connect(self.run_conversion)
        layout.addWidget(self.convert_btn)

        self.result_card = ResultStatusCard()
        layout.addWidget(self.result_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _on_file_selected(self, path_str: str) -> None:
        self.output_card.suggest_from_input(path_str)

    @property
    def selected_format(self) -> str:
        return str(self.format_combo.currentData())

    def run_conversion(self) -> None:
        src = self.input_card.selected_path
        if not src:
            self.result_card.set_error("Selecione um arquivo PDF de entrada primeiro.")
            return

        try:
            res = convert_pdf_to_format(
                input_path=src,
                target_format=self.selected_format,
                output_dir=self.output_card.output_dir,
                keep_original_name=self.output_card.keep_original_name,
                custom_name=self.output_card.custom_name,
                dpi=self.dpi_spin.value(),
            )
            first_out = res.output_paths[0] if res.output_paths else None
            self.result_card.set_success(res.message, first_out)
        except Exception as exc:
            self.result_card.set_error(str(exc))
