"""
Aba de Edição de Texto em Documentos PDF.
Segue o fluxo: Entrada -> Processamento -> Saída.
Inspeciona os blocos/spans editáveis do PDF e permite substituir textos ou inserir
novos textos gerando um novo arquivo PDF sem modificar o original.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cortex_pdf.core.editor_engine import (
    extract_editable_spans,
    inspect_pdf_editability,
    replace_text_in_pdf,
)
from cortex_pdf.ui.components import (
    FileInputCard,
    OutputNamingCard,
    PipelineBanner,
    ResultStatusCard,
)


class EditorTab(QWidget):
    """Aba para editar textos contidos em documentos PDF."""

    open_in_viewer = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Cabeçalho
        lbl_title = QLabel("Editar Texto do PDF")
        lbl_title.setProperty("class", "PageHeaderTitle")
        lbl_desc = QLabel(
            "Localize e edite trechos de texto em documentos PDF que possuem camada de texto editável."
        )
        lbl_desc.setProperty("class", "PageHeaderDesc")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addWidget(PipelineBanner())

        # Etapa 1: Entrada
        self.input_card = FileInputCard(
            title="1. Entrada — Selecionar PDF para Edição",
            subtitle="Selecione o arquivo PDF cujo texto deseja editar. O original não será alterado.",
            file_filter="Arquivos PDF (*.pdf)",
        )
        self.input_card.file_selected.connect(self._on_file_selected)
        layout.addWidget(self.input_card)

        # Etapa 2: Processamento (Inspeção e Substituição de Texto)
        proc_card = QFrame()
        proc_card.setProperty("class", "StepCard")
        proc_layout = QVBoxLayout(proc_card)
        proc_layout.setContentsMargins(16, 14, 16, 14)
        proc_layout.setSpacing(10)

        lbl_proc = QLabel("2. Processamento — Selecionar e Substituir Texto")
        lbl_proc.setProperty("class", "StepTitle")
        self.editability_lbl = QLabel("Selecione um arquivo PDF acima para inspecionar os textos editáveis.")
        self.editability_lbl.setProperty("class", "StepSubtitle")

        # Lista de trechos detectados para clique rápido
        spans_lbl = QLabel("Trechos de texto detectados no documento (clique em um item para preencher):")
        self.spans_list = QListWidget()
        self.spans_list.setMaximumHeight(130)
        self.spans_list.itemClicked.connect(self._on_span_item_clicked)

        # Campos de busca e substituição
        fields_row = QHBoxLayout()
        col_old = QVBoxLayout()
        col_old.addWidget(QLabel("Texto atual a ser substituído:"))
        self.search_text_edit = QLineEdit()
        self.search_text_edit.setPlaceholderText("Ex: Texto antigo...")
        col_old.addWidget(self.search_text_edit)

        col_new = QVBoxLayout()
        col_new.addWidget(QLabel("Novo texto substituto:"))
        self.replace_text_edit = QLineEdit()
        self.replace_text_edit.setPlaceholderText("Ex: Novo texto atualizado...")
        col_new.addWidget(self.replace_text_edit)

        fields_row.addLayout(col_old, stretch=1)
        fields_row.addLayout(col_new, stretch=1)

        # Filtro opcional por página
        scope_row = QHBoxLayout()
        self.all_pages_chk = QCheckBox("Aplicar em todas as páginas do documento")
        self.all_pages_chk.setChecked(True)
        self.all_pages_chk.toggled.connect(self._on_scope_toggled)

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.setEnabled(False)

        scope_row.addWidget(self.all_pages_chk)
        scope_row.addSpacing(16)
        scope_row.addWidget(QLabel("Ou apenas na página:"))
        scope_row.addWidget(self.page_spin)
        scope_row.addStretch()

        proc_layout.addWidget(lbl_proc)
        proc_layout.addWidget(self.editability_lbl)
        proc_layout.addWidget(spans_lbl)
        proc_layout.addWidget(self.spans_list)
        proc_layout.addLayout(fields_row)
        proc_layout.addLayout(scope_row)
        layout.addWidget(proc_card)

        # Etapa 3: Saída
        self.output_card = OutputNamingCard()
        layout.addWidget(self.output_card)

        # Botão de Ação e Status
        self.run_btn = QPushButton("✏️ Aplicar Edição e Gerar Novo PDF")
        self.run_btn.setProperty("class", "PrimaryButton")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self.run_edit)
        layout.addWidget(self.run_btn)

        self.result_card = ResultStatusCard()
        self.result_card.open_in_viewer_requested.connect(self.open_in_viewer.emit)
        layout.addWidget(self.result_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def _on_scope_toggled(self, all_pages: bool) -> None:
        self.page_spin.setEnabled(not all_pages)

    def _on_file_selected(self, path_str: str) -> None:
        self.output_card.suggest_from_input(path_str)
        self.spans_list.clear()
        try:
            info = inspect_pdf_editability(path_str)
            if not info["editable"]:
                self.editability_lbl.setText(f"⚠️ {info['reason']}")
                self.editability_lbl.setStyleSheet("color: #fbbf24; font-weight: 600;")
                self.run_btn.setEnabled(False)
                return

            self.run_btn.setEnabled(True)
            self.page_spin.setMaximum(max(1, info["page_count"]))
            self.editability_lbl.setText(
                f"✅ {info['reason']} ({info['total_text_spans']} trechos encontrados em {info['page_count']} página(s))."
            )
            self.editability_lbl.setStyleSheet("color: #34d399; font-weight: 600;")

            spans = extract_editable_spans(path_str)
            for sp in spans[:150]:
                item = QListWidgetItem(f"[Pág. {sp.page_index + 1}] {sp.text}")
                item.setData(Qt.ItemDataRole.UserRole, sp.text)
                self.spans_list.addItem(item)
        except Exception as exc:
            self.result_card.set_error(str(exc))

    def _on_span_item_clicked(self, item: QListWidgetItem) -> None:
        raw_text = item.data(Qt.ItemDataRole.UserRole)
        if raw_text:
            self.search_text_edit.setText(raw_text)
            self.replace_text_edit.setText(raw_text)
            self.replace_text_edit.setFocus()

    def run_edit(self) -> None:
        input_path = self.input_card.selected_path
        if not input_path:
            self.result_card.set_error("Selecione um arquivo PDF de entrada primeiro.")
            return

        old_txt = self.search_text_edit.text()
        new_txt = self.replace_text_edit.text()
        if not old_txt:
            self.result_card.set_error("Informe o texto atual que deseja substituir.")
            return

        target_page = None if self.all_pages_chk.isChecked() else (self.page_spin.value() - 1)

        try:
            res = replace_text_in_pdf(
                input_path=input_path,
                search_text=old_txt,
                new_text=new_txt,
                output_dir=self.output_card.output_dir,
                keep_original_name=self.output_card.keep_original_name,
                custom_name=self.output_card.custom_name,
                page_index=target_page,
            )
            self.result_card.set_success(res.message, res.output_path)
        except Exception as exc:
            self.result_card.set_error(str(exc))
