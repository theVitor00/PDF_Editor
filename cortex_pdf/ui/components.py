"""
Componentes reutilizáveis de interface gráfica para manter o fluxo padronizado:
Entrada -> Processamento -> Saída (sempre gerando um novo arquivo sem tocar no original).
Utiliza ícones Font Awesome via QtAwesome e tema claro/clean.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from cortex_pdf.ui.icons import fa_icon, fa_pixmap_label


class PipelineBanner(QFrame):
    """Banner compacto exibindo o fluxo Entrada -> Processamento -> Saída com ícones Font Awesome."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("PipelineBanner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)

        icon_bolt = fa_pixmap_label("bolt", color="#2563eb", size=14)
        lbl_flow = QLabel(
            "Fluxo Direto:   1. Entrada (Original Intacto)   →   "
            "2. Processamento Local   →   3. Saída (Novo Arquivo Gerado)"
        )
        lbl_flow.setStyleSheet("color: #1e40af; font-weight: 600; font-size: 12px;")

        icon_lock = fa_pixmap_label("shield-alt", color="#475569", size=14)
        lbl_privacy = QLabel("Zero coleta de dados")
        lbl_privacy.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600;")

        layout.addWidget(icon_bolt)
        layout.addWidget(lbl_flow)
        layout.addStretch()
        layout.addWidget(icon_lock)
        layout.addWidget(lbl_privacy)


class FileInputCard(QFrame):
    """
    Card de Entrada (Etapa 1): Permite selecionar o arquivo de origem.
    """

    file_selected = pyqtSignal(str)

    def __init__(
        self,
        title: str = "1. Entrada — Selecionar Arquivo",
        subtitle: str = "O arquivo selecionado será apenas lido e nunca será modificado.",
        file_filter: str = "Arquivos PDF (*.pdf)",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setProperty("class", "StepCard")
        self._file_filter = file_filter
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "StepTitle")
        lbl_sub = QLabel(subtitle)
        lbl_sub.setProperty("class", "StepSubtitle")

        row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Selecione um arquivo ou arraste e solte aqui...")
        self.path_edit.setReadOnly(True)

        self.browse_btn = QPushButton("Procurar Arquivo...")
        self.browse_btn.setIcon(fa_icon("folder-open", color="#334155"))
        self.browse_btn.setProperty("class", "SecondaryButton")
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.clicked.connect(self._on_browse)

        row.addWidget(self.path_edit, stretch=1)
        row.addWidget(self.browse_btn)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)
        layout.addLayout(row)

    @property
    def selected_path(self) -> str:
        return self.path_edit.text().strip()

    def set_file_path(self, path_str: str) -> None:
        cleaned = str(path_str).strip()
        self.path_edit.setText(cleaned)
        if cleaned:
            self.file_selected.emit(cleaned)

    def _on_browse(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Entrada",
            "",
            self._file_filter,
        )
        if file_path:
            self.set_file_path(file_path)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            local_path = urls[0].toLocalFile()
            if local_path:
                self.set_file_path(local_path)


class OutputNamingCard(QFrame):
    """
    Card de Saída (Etapa 3): Permite ao usuário escolher entre manter o nome original
    ou modificar o nome do novo arquivo gerado, além de escolher a pasta de destino.
    """

    def __init__(
        self,
        title: str = "3. Saída — Configuração do Novo Arquivo",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setProperty("class", "StepCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "StepTitle")
        lbl_sub = QLabel(
            "Um novo arquivo será gerado. O arquivo original permanece 100% intacto."
        )
        lbl_sub.setProperty("class", "StepSubtitle")

        self.radio_keep = QRadioButton(
            "Manter o nome original (adiciona sufixo automático se salvo na mesma pasta)"
        )
        self.radio_custom = QRadioButton("Modificar o nome do novo arquivo gerado:")
        self.radio_keep.setChecked(True)

        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.radio_keep)
        self.btn_group.addButton(self.radio_custom)

        self.custom_name_edit = QLineEdit()
        self.custom_name_edit.setPlaceholderText("Digite o novo nome para o arquivo de saída...")
        self.custom_name_edit.setEnabled(False)

        self.radio_keep.toggled.connect(self._on_mode_changed)

        dir_row = QHBoxLayout()
        lbl_dir = QLabel("Pasta de saída:")
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText(
            "Mesma pasta do arquivo de entrada (padrão)"
        )
        self.browse_dir_btn = QPushButton("Escolher Pasta...")
        self.browse_dir_btn.setIcon(fa_icon("folder", color="#334155"))
        self.browse_dir_btn.setProperty("class", "SecondaryButton")
        self.browse_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_dir_btn.clicked.connect(self._on_browse_dir)

        dir_row.addWidget(lbl_dir)
        dir_row.addWidget(self.output_dir_edit, stretch=1)
        dir_row.addWidget(self.browse_dir_btn)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)
        layout.addWidget(self.radio_keep)
        layout.addWidget(self.radio_custom)
        layout.addWidget(self.custom_name_edit)
        layout.addLayout(dir_row)

    def _on_mode_changed(self, keep_checked: bool) -> None:
        self.custom_name_edit.setEnabled(not keep_checked)

    def _on_browse_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Saída")
        if folder:
            self.output_dir_edit.setText(folder)

    @property
    def keep_original_name(self) -> bool:
        return self.radio_keep.isChecked()

    @property
    def custom_name(self) -> Optional[str]:
        if self.keep_original_name:
            return None
        val = self.custom_name_edit.text().strip()
        return val if val else None

    @property
    def output_dir(self) -> Optional[Path]:
        txt = self.output_dir_edit.text().strip()
        return Path(txt) if txt else None

    def suggest_from_input(self, input_path_str: str) -> None:
        """Preenche sugestão de nome e pasta baseados no arquivo de entrada."""
        if not input_path_str:
            return
        p = Path(input_path_str)
        if not self.custom_name_edit.text().strip():
            self.custom_name_edit.setText(f"{p.stem}_novo")


class ResultStatusCard(QFrame):
    """Exibe o resultado claro da operação com ícone Font Awesome e botão rápido para visualizar."""

    open_in_viewer_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("class", "StepCard")
        self._last_pdf_path: Optional[str] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.status_icon = QLabel()
        self.status_icon.setPixmap(fa_icon("info-circle", color="#64748b").pixmap(QSize(18, 18)))

        self.status_label = QLabel("Aguardando processamento...")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #64748b; font-size: 13px;")

        self.open_viewer_btn = QPushButton("Abrir no Visualizador")
        self.open_viewer_btn.setIcon(fa_icon("eye", color="#334155"))
        self.open_viewer_btn.setProperty("class", "SecondaryButton")
        self.open_viewer_btn.setVisible(False)
        self.open_viewer_btn.clicked.connect(self._emit_open_viewer)

        layout.addWidget(self.status_icon)
        layout.addWidget(self.status_label, stretch=1)
        layout.addWidget(self.open_viewer_btn)

    def set_success(self, message: str, output_path: Optional[Path] = None) -> None:
        out_info = f"\nArquivo salvo em: {output_path}" if output_path else ""
        self.status_icon.setPixmap(fa_icon("check-circle", color="#15803d").pixmap(QSize(18, 18)))
        self.status_label.setText(f"{message}{out_info}")
        self.status_label.setStyleSheet("color: #15803d; font-weight: 600; font-size: 13px;")
        if output_path and output_path.suffix.lower() == ".pdf" and output_path.exists():
            self._last_pdf_path = str(output_path)
            self.open_viewer_btn.setVisible(True)
        else:
            self._last_pdf_path = None
            self.open_viewer_btn.setVisible(False)

    def set_error(self, error_msg: str) -> None:
        self.status_icon.setPixmap(fa_icon("exclamation-circle", color="#dc2626").pixmap(QSize(18, 18)))
        self.status_label.setText(f"Erro: {error_msg}")
        self.status_label.setStyleSheet("color: #dc2626; font-weight: 600; font-size: 13px;")
        self.open_viewer_btn.setVisible(False)

    def _emit_open_viewer(self) -> None:
        if self._last_pdf_path:
            self.open_in_viewer_requested.emit(self._last_pdf_path)
