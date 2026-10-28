"""
Aba de Junção (Merge) de Arquivos PDF.
Permite selecionar dois ou mais arquivos PDF, ordenar a sequência desejada
e gerar um único novo arquivo PDF sem modificar os originais.
Utiliza ícones Font Awesome e tema claro/clean.
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cortex_pdf.core.merger import merge_pdfs
from cortex_pdf.ui.components import (
    OutputNamingCard,
    PipelineBanner,
    ResultStatusCard,
)
from cortex_pdf.ui.icons import fa_icon


class MergeTab(QWidget):
    """Aba para juntar dois ou mais arquivos PDF em um único documento."""

    open_in_viewer = pyqtSignal(str)

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

        lbl_title = QLabel("Juntar Arquivos PDF")
        lbl_title.setProperty("class", "PageHeaderTitle")
        lbl_desc = QLabel(
            "Combine dois ou mais documentos PDF em um único novo arquivo PDF mantendo os originais intactos."
        )
        lbl_desc.setProperty("class", "PageHeaderDesc")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addWidget(PipelineBanner())

        # Etapa 1 & 2: Entrada e Ordem de Junção
        input_card = QFrame()
        input_card.setProperty("class", "StepCard")
        in_layout = QVBoxLayout(input_card)
        in_layout.setContentsMargins(16, 14, 16, 14)
        in_layout.setSpacing(10)

        lbl_in = QLabel("1 & 2. Entrada e Ordem de Processamento — Arquivos a Juntar")
        lbl_in.setProperty("class", "StepTitle")
        lbl_sub = QLabel(
            "Adicione pelo menos 2 arquivos PDF. Você pode alterar a ordem usando os botões Subir/Descer."
        )
        lbl_sub.setProperty("class", "StepSubtitle")

        self.files_list = QListWidget()
        self.files_list.setMinimumHeight(140)

        btns_row = QHBoxLayout()
        self.add_btn = QPushButton("Adicionar PDF(s)...")
        self.add_btn.setIcon(fa_icon("plus", color="#334155"))
        self.add_btn.setProperty("class", "SecondaryButton")
        self.add_btn.clicked.connect(self._on_add_files)

        self.up_btn = QPushButton("Subir")
        self.up_btn.setIcon(fa_icon("arrow-up", color="#334155"))
        self.up_btn.setProperty("class", "SecondaryButton")
        self.up_btn.clicked.connect(self.move_up)

        self.down_btn = QPushButton("Descer")
        self.down_btn.setIcon(fa_icon("arrow-down", color="#334155"))
        self.down_btn.setProperty("class", "SecondaryButton")
        self.down_btn.clicked.connect(self.move_down)

        self.remove_btn = QPushButton("Remover Selecionado")
        self.remove_btn.setIcon(fa_icon("trash-alt", color="#334155"))
        self.remove_btn.setProperty("class", "SecondaryButton")
        self.remove_btn.clicked.connect(self.remove_selected)

        self.clear_btn = QPushButton("Limpar Lista")
        self.clear_btn.setIcon(fa_icon("eraser", color="#334155"))
        self.clear_btn.setProperty("class", "SecondaryButton")
        self.clear_btn.clicked.connect(self.files_list.clear)

        btns_row.addWidget(self.add_btn)
        btns_row.addWidget(self.up_btn)
        btns_row.addWidget(self.down_btn)
        btns_row.addWidget(self.remove_btn)
        btns_row.addWidget(self.clear_btn)
        btns_row.addStretch()

        in_layout.addWidget(lbl_in)
        in_layout.addWidget(lbl_sub)
        in_layout.addWidget(self.files_list)
        in_layout.addLayout(btns_row)
        layout.addWidget(input_card)

        # Etapa 3: Saída
        self.output_card = OutputNamingCard()
        layout.addWidget(self.output_card)

        # Botão de Ação
        self.merge_btn = QPushButton("Juntar PDFs em um Único Arquivo")
        self.merge_btn.setIcon(fa_icon("object-group", color="#ffffff"))
        self.merge_btn.setProperty("class", "PrimaryButton")
        self.merge_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.merge_btn.clicked.connect(self.run_merge)
        layout.addWidget(self.merge_btn)

        self.result_card = ResultStatusCard()
        self.result_card.open_in_viewer_requested.connect(self.open_in_viewer.emit)
        layout.addWidget(self.result_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def add_file_path(self, path_str: str) -> None:
        cleaned = str(path_str).strip()
        if cleaned:
            self.files_list.addItem(cleaned)
            if self.files_list.count() == 1:
                self.output_card.suggest_from_input(cleaned)

    def _on_add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Arquivos PDF para Juntar",
            "",
            "Arquivos PDF (*.pdf)",
        )
        for f in files:
            self.add_file_path(f)

    def move_up(self) -> None:
        row = self.files_list.currentRow()
        if row > 0:
            item = self.files_list.takeItem(row)
            self.files_list.insertItem(row - 1, item)
            self.files_list.setCurrentRow(row - 1)

    def move_down(self) -> None:
        row = self.files_list.currentRow()
        if 0 <= row < self.files_list.count() - 1:
            item = self.files_list.takeItem(row)
            self.files_list.insertItem(row + 1, item)
            self.files_list.setCurrentRow(row + 1)

    def remove_selected(self) -> None:
        row = self.files_list.currentRow()
        if row >= 0:
            self.files_list.takeItem(row)

    def get_file_paths(self) -> list[str]:
        return [self.files_list.item(i).text() for i in range(self.files_list.count())]

    def run_merge(self) -> None:
        paths = self.get_file_paths()
        if len(paths) < 2:
            self.result_card.set_error("Adicione pelo menos 2 arquivos PDF para juntar.")
            return

        try:
            res = merge_pdfs(
                input_paths=paths,
                output_dir=self.output_card.output_dir,
                keep_original_name=self.output_card.keep_original_name,
                custom_name=self.output_card.custom_name,
            )
            self.result_card.set_success(res.message, res.output_path)
        except Exception as exc:
            self.result_card.set_error(str(exc))
