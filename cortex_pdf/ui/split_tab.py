"""
Aba de Divisão (Split) de Arquivo PDF.
Permite dividir um único arquivo PDF em dois ou mais arquivos PDF:
- Dividir em 2 arquivos após uma página específica
- Dividir por intervalos personalizados (ex: '1-2, 3-5')
- Dividir a cada N páginas (ex: 1 página por arquivo)
"""

from typing import Optional
import pymupdf
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cortex_pdf.core.splitter import (
    split_pdf_at_page,
    split_pdf_by_ranges,
    split_pdf_every_n_pages,
)
from cortex_pdf.ui.components import (
    FileInputCard,
    OutputNamingCard,
    PipelineBanner,
    ResultStatusCard,
)


class SplitTab(QWidget):
    """Aba para dividir um único PDF em dois ou mais documentos PDF."""

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

        lbl_title = QLabel("Dividir Arquivo PDF")
        lbl_title.setProperty("class", "PageHeaderTitle")
        lbl_desc = QLabel(
            "Divida um documento PDF em dois ou mais arquivos independentes sem modificar o original."
        )
        lbl_desc.setProperty("class", "PageHeaderDesc")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addWidget(PipelineBanner())

        # Etapa 1: Entrada
        self.input_card = FileInputCard(
            title="1. Entrada — Selecionar PDF para Dividir",
            subtitle="O documento deve possuir pelo menos 2 páginas.",
            file_filter="Arquivos PDF (*.pdf)",
        )
        self.input_card.file_selected.connect(self._on_file_selected)
        layout.addWidget(self.input_card)

        # Etapa 2: Processamento (Modo de Divisão)
        proc_card = QFrame()
        proc_card.setProperty("class", "StepCard")
        proc_layout = QVBoxLayout(proc_card)
        proc_layout.setContentsMargins(16, 14, 16, 14)
        proc_layout.setSpacing(10)

        lbl_proc = QLabel("2. Processamento — Modo de Divisão")
        lbl_proc.setProperty("class", "StepTitle")
        self.page_info_lbl = QLabel("Selecione um arquivo PDF para visualizar o total de páginas.")
        self.page_info_lbl.setProperty("class", "StepSubtitle")

        self.mode_group = QButtonGroup(self)

        # Modo 1: Dividir em 2 na página X
        row_m1 = QHBoxLayout()
        self.radio_at_page = QRadioButton("Dividir em 2 PDFs após a página:")
        self.radio_at_page.setChecked(True)
        self.split_page_spin = QSpinBox()
        self.split_page_spin.setMinimum(1)
        self.split_page_spin.setMaximum(9999)
        self.split_page_spin.setValue(1)
        row_m1.addWidget(self.radio_at_page)
        row_m1.addWidget(self.split_page_spin)
        row_m1.addStretch()

        # Modo 2: Intervalos personalizados
        row_m2 = QHBoxLayout()
        self.radio_ranges = QRadioButton("Dividir por intervalos de páginas (ex: 1-2, 3-4):")
        self.ranges_edit = QLineEdit()
        self.ranges_edit.setPlaceholderText("Ex: 1-2, 3-5")
        self.ranges_edit.setEnabled(False)
        row_m2.addWidget(self.radio_ranges)
        row_m2.addWidget(self.ranges_edit, stretch=1)

        # Modo 3: A cada N páginas
        row_m3 = QHBoxLayout()
        self.radio_every_n = QRadioButton("Dividir a cada N páginas por arquivo:")
        self.every_n_spin = QSpinBox()
        self.every_n_spin.setMinimum(1)
        self.every_n_spin.setMaximum(9999)
        self.every_n_spin.setValue(1)
        self.every_n_spin.setEnabled(False)
        row_m3.addWidget(self.radio_every_n)
        row_m3.addWidget(self.every_n_spin)
        row_m3.addStretch()

        self.mode_group.addButton(self.radio_at_page)
        self.mode_group.addButton(self.radio_ranges)
        self.mode_group.addButton(self.radio_every_n)

        self.radio_at_page.toggled.connect(self._update_mode_inputs)
        self.radio_ranges.toggled.connect(self._update_mode_inputs)
        self.radio_every_n.toggled.connect(self._update_mode_inputs)

        proc_layout.addWidget(lbl_proc)
        proc_layout.addWidget(self.page_info_lbl)
        proc_layout.addLayout(row_m1)
        proc_layout.addLayout(row_m2)
        proc_layout.addLayout(row_m3)
        layout.addWidget(proc_card)

        # Etapa 3: Saída
        self.output_card = OutputNamingCard(
            title="3. Saída — Nome Base dos Novos Arquivos Gerados"
        )
        layout.addWidget(self.output_card)

        # Ação
        self.split_btn = QPushButton("✂️ Dividir PDF Agora")
        self.split_btn.setProperty("class", "PrimaryButton")
        self.split_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.split_btn.clicked.connect(self.run_split)
        layout.addWidget(self.split_btn)

        self.result_card = ResultStatusCard()
        self.result_card.open_in_viewer_requested.connect(self.open_in_viewer.emit)
        layout.addWidget(self.result_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _update_mode_inputs(self) -> None:
        self.split_page_spin.setEnabled(self.radio_at_page.isChecked())
        self.ranges_edit.setEnabled(self.radio_ranges.isChecked())
        self.every_n_spin.setEnabled(self.radio_every_n.isChecked())

    def _on_file_selected(self, path_str: str) -> None:
        self.output_card.suggest_from_input(path_str)
        try:
            with pymupdf.open(path_str) as doc:
                total = len(doc)
            self.page_info_lbl.setText(f"Documento carregado com {total} página(s).")
            self.page_info_lbl.setStyleSheet("color: #34d399; font-weight: 600;")
            if total >= 2:
                self.split_page_spin.setMaximum(total - 1)
                self.split_page_spin.setValue(max(1, total // 2))
                self.ranges_edit.setText(f"1-{max(1, total // 2)}, {max(1, total // 2) + 1}-{total}")
        except Exception as exc:
            self.result_card.set_error(str(exc))

    def run_split(self) -> None:
        src = self.input_card.selected_path
        if not src:
            self.result_card.set_error("Selecione um arquivo PDF de entrada para dividir.")
            return

        try:
            if self.radio_at_page.isChecked():
                res = split_pdf_at_page(
                    input_path=src,
                    split_after_page=self.split_page_spin.value(),
                    output_dir=self.output_card.output_dir,
                    keep_original_name=self.output_card.keep_original_name,
                    custom_base_name=self.output_card.custom_name,
                )
            elif self.radio_ranges.isChecked():
                res = split_pdf_by_ranges(
                    input_path=src,
                    page_ranges=self.ranges_edit.text(),
                    output_dir=self.output_card.output_dir,
                    keep_original_name=self.output_card.keep_original_name,
                    custom_base_name=self.output_card.custom_name,
                )
            else:
                res = split_pdf_every_n_pages(
                    input_path=src,
                    pages_per_part=self.every_n_spin.value(),
                    output_dir=self.output_card.output_dir,
                    keep_original_name=self.output_card.keep_original_name,
                    custom_base_name=self.output_card.custom_name,
                )

            first_out = res.output_paths[0] if res.output_paths else None
            names = ", ".join(p.name for p in res.output_paths[:5])
            if len(res.output_paths) > 5:
                names += f" (+{len(res.output_paths) - 5} arquivos)"
            self.result_card.set_success(f"{res.message} Arquivos: {names}", first_out)
        except Exception as exc:
            self.result_card.set_error(str(exc))
