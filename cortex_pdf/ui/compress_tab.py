"""
Aba de Compressão de PDF.
Segue o fluxo: Entrada -> Processamento -> Saída.
Reduz o tamanho total do PDF sem modificar o arquivo original.
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cortex_pdf.core.compressor import compress_pdf
from cortex_pdf.ui.components import (
    FileInputCard,
    OutputNamingCard,
    PipelineBanner,
    ResultStatusCard,
)


class CompressTab(QWidget):
    """Aba para comprimir documentos PDF reduzindo seu tamanho em disco."""

    open_in_viewer = pyqtSignal(str)

    LEVEL_OPTIONS = [
        ("Média (Recomendada — Equilíbrio entre tamanho e nitidez)", "medium"),
        ("Alta (Máxima Redução — Ideal para envio por e-mail/web)", "high"),
        ("Baixa (Sem perda visual — Limpeza estrutural e fluxos Deflate)", "low"),
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

        lbl_title = QLabel("Comprimir Documento PDF")
        lbl_title.setProperty("class", "PageHeaderTitle")
        lbl_desc = QLabel(
            "Reduza o tamanho total do seu PDF otimizando fluxos internos, fontes e imagens embutidas."
        )
        lbl_desc.setProperty("class", "PageHeaderDesc")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addWidget(PipelineBanner())

        # Etapa 1: Entrada
        self.input_card = FileInputCard(
            title="1. Entrada — Selecionar PDF para Comprimir",
            subtitle="O arquivo original não será alterado.",
            file_filter="Arquivos PDF (*.pdf)",
        )
        self.input_card.file_selected.connect(self.output_card_suggest)
        layout.addWidget(self.input_card)

        # Etapa 2: Processamento
        proc_card = QFrame()
        proc_card.setProperty("class", "StepCard")
        proc_layout = QVBoxLayout(proc_card)
        proc_layout.setContentsMargins(16, 14, 16, 14)
        proc_layout.setSpacing(8)

        lbl_proc = QLabel("2. Processamento — Nível de Compressão")
        lbl_proc.setProperty("class", "StepTitle")

        row = QHBoxLayout()
        row.addWidget(QLabel("Intensidade da compressão:"))
        self.level_combo = QComboBox()
        for label, code in self.LEVEL_OPTIONS:
            self.level_combo.addItem(label, userData=code)
        row.addWidget(self.level_combo, stretch=1)

        proc_layout.addWidget(lbl_proc)
        proc_layout.addLayout(row)
        layout.addWidget(proc_card)

        # Etapa 3: Saída
        self.output_card = OutputNamingCard()
        layout.addWidget(self.output_card)

        # Ação
        self.compress_btn = QPushButton("🗜️ Comprimir PDF e Gerar Novo Arquivo")
        self.compress_btn.setProperty("class", "PrimaryButton")
        self.compress_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.compress_btn.clicked.connect(self.run_compression)
        layout.addWidget(self.compress_btn)

        self.result_card = ResultStatusCard()
        self.result_card.open_in_viewer_requested.connect(self.open_in_viewer.emit)
        layout.addWidget(self.result_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def output_card_suggest(self, path_str: str) -> None:
        self.output_card.suggest_from_input(path_str)

    @property
    def selected_level(self) -> str:
        return str(self.level_combo.currentData())

    def run_compression(self) -> None:
        src = self.input_card.selected_path
        if not src:
            self.result_card.set_error("Selecione um arquivo PDF para comprimir.")
            return

        try:
            res = compress_pdf(
                input_path=src,
                level=self.selected_level,
                output_dir=self.output_card.output_dir,
                keep_original_name=self.output_card.keep_original_name,
                custom_name=self.output_card.custom_name,
            )
            self.result_card.set_success(res.message, res.output_path)
        except Exception as exc:
            self.result_card.set_error(str(exc))
