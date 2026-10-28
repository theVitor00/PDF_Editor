"""
Aba de Visualização de Documentos PDF.
Suporta:
- Abrir PDF
- Zoom-In, Zoom-Out, Reset (100%)
- Rotação de página
- Navegação entre páginas
- Seleção de texto arrastando o mouse sobre a página (RubberBand) ou no painel lateral
- Cópia de texto para a área de transferência (Clipboard)
- Busca de texto na página
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QImage, QPainter, QColor, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRubberBand,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from cortex_pdf.core.viewer_engine import PDFViewerEngine


class InteractivePageLabel(QLabel):
    """
    Canvas interativo que exibe a página PDF renderizada e permite selecionar
    uma região retangular com o mouse para extrair/copiar o texto contido nela.
    """

    rect_selected = pyqtSignal(float, float, float, float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self._origin = QPoint()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._rubber_band.setGeometry(QRect(self._origin, QSize()))
            self._rubber_band.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if not self._origin.isNull():
            self._rubber_band.setGeometry(QRect(self._origin, event.pos()).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._origin.isNull():
            rect = QRect(self._origin, event.pos()).normalized()
            self._rubber_band.hide()
            if rect.width() > 4 and rect.height() > 4:
                self.rect_selected.emit(
                    float(rect.left()),
                    float(rect.top()),
                    float(rect.right()),
                    float(rect.bottom()),
                )
        super().mouseReleaseEvent(event)


class ViewerTab(QWidget):
    """Aba completa de visualização de PDF com zoom, seleção e cópia de texto."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.engine = PDFViewerEngine()
        self.current_page_index: int = 0
        self._highlight_rects: list[tuple[float, float, float, float]] = []

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Cabeçalho
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("Visualizador de Documentos PDF")
        lbl_title.setProperty("class", "PageHeaderTitle")
        lbl_desc = QLabel(
            "Visualize páginas com zoom, pesquise termos, selecione texto na imagem ou no painel lateral e copie rapidamente."
        )
        lbl_desc.setProperty("class", "PageHeaderDesc")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)

        self.open_btn = QPushButton("📂 Abrir PDF...")
        self.open_btn.setProperty("class", "PrimaryButton")
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.clicked.connect(self._on_open_dialog)

        header_row.addLayout(title_box, stretch=1)
        header_row.addWidget(self.open_btn)
        main_layout.addLayout(header_row)

        # Barra de Ferramentas de Visualização
        toolbar_frame = QFrame()
        toolbar_frame.setProperty("class", "StepCard")
        tb_layout = QHBoxLayout(toolbar_frame)
        tb_layout.setContentsMargins(12, 8, 12, 8)
        tb_layout.setSpacing(8)

        self.prev_page_btn = QPushButton("◀ Anterior")
        self.prev_page_btn.setProperty("class", "SecondaryButton")
        self.prev_page_btn.clicked.connect(self.prev_page)

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.valueChanged.connect(self._on_spin_page_changed)

        self.total_pages_lbl = QLabel("de 0")

        self.next_page_btn = QPushButton("Próxima ▶")
        self.next_page_btn.setProperty("class", "SecondaryButton")
        self.next_page_btn.clicked.connect(self.next_page)

        self.zoom_out_btn = QPushButton("🔍 - Zoom Out")
        self.zoom_out_btn.setProperty("class", "SecondaryButton")
        self.zoom_out_btn.clicked.connect(self.zoom_out)

        self.zoom_lbl = QLabel("100%")
        self.zoom_lbl.setMinimumWidth(52)
        self.zoom_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_lbl.setStyleSheet("font-weight: 700; color: #38bdf8;")

        self.zoom_in_btn = QPushButton("🔍 + Zoom In")
        self.zoom_in_btn.setProperty("class", "SecondaryButton")
        self.zoom_in_btn.clicked.connect(self.zoom_in)

        self.zoom_reset_btn = QPushButton("100%")
        self.zoom_reset_btn.setProperty("class", "SecondaryButton")
        self.zoom_reset_btn.clicked.connect(self.reset_zoom)

        self.rotate_btn = QPushButton("↻ Girar 90°")
        self.rotate_btn.setProperty("class", "SecondaryButton")
        self.rotate_btn.clicked.connect(self.rotate_page)

        # Busca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar texto na página...")
        self.search_input.returnPressed.connect(self.search_in_page)
        self.search_btn = QPushButton("Buscar")
        self.search_btn.setProperty("class", "SecondaryButton")
        self.search_btn.clicked.connect(self.search_in_page)

        tb_layout.addWidget(self.prev_page_btn)
        tb_layout.addWidget(QLabel("Pág:"))
        tb_layout.addWidget(self.page_spin)
        tb_layout.addWidget(self.total_pages_lbl)
        tb_layout.addWidget(self.next_page_btn)
        tb_layout.addSpacing(12)
        tb_layout.addWidget(self.zoom_out_btn)
        tb_layout.addWidget(self.zoom_lbl)
        tb_layout.addWidget(self.zoom_in_btn)
        tb_layout.addWidget(self.zoom_reset_btn)
        tb_layout.addWidget(self.rotate_btn)
        tb_layout.addStretch()
        tb_layout.addWidget(self.search_input)
        tb_layout.addWidget(self.search_btn)

        main_layout.addWidget(toolbar_frame)

        # Área central dividida: Canvas da Página (Esquerda) + Painel de Seleção e Cópia de Texto (Direita)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Esquerda: ScrollArea com a página renderizada
        canvas_frame = QFrame()
        canvas_frame.setProperty("class", "StepCard")
        canvas_layout = QVBoxLayout(canvas_frame)
        canvas_layout.setContentsMargins(8, 8, 8, 8)

        hint_lbl = QLabel(
            "💡 Dica: Arraste o mouse sobre qualquer área da página abaixo para selecionar e extrair o texto daquela região."
        )
        hint_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        canvas_layout.addWidget(hint_lbl)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.page_canvas = InteractivePageLabel()
        self.page_canvas.setText("Nenhum documento PDF aberto.\nClique em 'Abrir PDF...' para começar.")
        self.page_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_canvas.setStyleSheet("color: #64748b; font-size: 14px; padding: 40px;")
        self.page_canvas.rect_selected.connect(self._on_canvas_rect_selected)

        self.scroll_area.setWidget(self.page_canvas)
        canvas_layout.addWidget(self.scroll_area, stretch=1)

        # Direita: Painel de Seleção e Cópia de Texto
        text_panel = QFrame()
        text_panel.setProperty("class", "StepCard")
        tp_layout = QVBoxLayout(text_panel)
        tp_layout.setContentsMargins(12, 12, 12, 12)
        tp_layout.setSpacing(8)

        tp_title = QLabel("Texto Extraído / Selecionado")
        tp_title.setProperty("class", "StepTitle")
        tp_sub = QLabel(
            "Selecione qualquer trecho abaixo ou arraste na página ao lado e clique em Copiar."
        )
        tp_sub.setProperty("class", "StepSubtitle")
        tp_sub.setWordWrap(True)

        self.text_view = QPlainTextEdit()
        self.text_view.setPlaceholderText("O texto da página ou da seleção aparecerá aqui...")

        copy_btns_row = QHBoxLayout()
        self.copy_selected_btn = QPushButton("📋 Copiar Seleção")
        self.copy_selected_btn.setProperty("class", "PrimaryButton")
        self.copy_selected_btn.clicked.connect(self.copy_selected_text)

        self.copy_all_btn = QPushButton("📄 Copiar Página Inteira")
        self.copy_all_btn.setProperty("class", "SecondaryButton")
        self.copy_all_btn.clicked.connect(self.copy_all_page_text)

        copy_btns_row.addWidget(self.copy_selected_btn)
        copy_btns_row.addWidget(self.copy_all_btn)

        self.copy_status_lbl = QLabel("")
        self.copy_status_lbl.setStyleSheet("color: #34d399; font-size: 12px; font-weight: 600;")

        tp_layout.addWidget(tp_title)
        tp_layout.addWidget(tp_sub)
        tp_layout.addWidget(self.text_view, stretch=1)
        tp_layout.addLayout(copy_btns_row)
        tp_layout.addWidget(self.copy_status_lbl)

        splitter.addWidget(canvas_frame)
        splitter.addWidget(text_panel)
        splitter.setSizes([720, 360])

        main_layout.addWidget(splitter, stretch=1)
        self._update_controls_state()

    def _on_open_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Documento PDF",
            "",
            "Arquivos PDF (*.pdf)",
        )
        if file_path:
            self.load_pdf(file_path)

    def load_pdf(self, pdf_path: str | Path) -> None:
        """Carrega um arquivo PDF no visualizador."""
        try:
            self.engine.open_document(pdf_path)
            self.current_page_index = 0
            self._highlight_rects = []
            self.page_spin.blockSignals(True)
            self.page_spin.setMaximum(max(1, self.engine.page_count))
            self.page_spin.setValue(1)
            self.page_spin.blockSignals(False)
            self.total_pages_lbl.setText(f"de {self.engine.page_count}")
            self._render_current_page()
            self._update_controls_state()
            self.copy_status_lbl.setText(f"Arquivo aberto: {Path(pdf_path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao abrir PDF", str(exc))

    def _render_current_page(self) -> None:
        if not self.engine.is_open:
            return
        rendered = self.engine.render_page(self.current_page_index)
        qimg = QImage.fromData(rendered.png_bytes, "PNG")
        pixmap = QPixmap.fromImage(qimg)

        # Desenha destaques de busca, se houver
        if self._highlight_rects:
            painter = QPainter(pixmap)
            pen = QPen(QColor(245, 158, 11, 220), 2)
            painter.setPen(pen)
            painter.setBrush(QColor(253, 224, 71, 85))
            z = rendered.zoom
            for x0, y0, x1, y1 in self._highlight_rects:
                painter.drawRect(int(x0 * z), int(y0 * z), int((x1 - x0) * z), int((y1 - y0) * z))
            painter.end()

        self.page_canvas.setStyleSheet("padding: 0px;")
        self.page_canvas.setPixmap(pixmap)
        self.page_canvas.setFixedSize(pixmap.size())
        self.zoom_lbl.setText(f"{int(round(self.engine.zoom * 100))}%")

        page_text = self.engine.get_page_text(self.current_page_index)
        self.text_view.setPlainText(page_text)

    def _on_canvas_rect_selected(self, x0: float, y0: float, x1: float, y1: float) -> None:
        if not self.engine.is_open:
            return
        extracted = self.engine.get_text_in_rect(
            self.current_page_index,
            (x0, y0, x1, y1),
            from_zoomed_coords=True,
        )
        if extracted:
            self.text_view.setPlainText(extracted)
            self.text_view.selectAll()
            self.copy_status_lbl.setText("Trecho selecionado da página! Clique em 'Copiar Seleção'.")
        else:
            self.copy_status_lbl.setText("Nenhum texto encontrado na área selecionada.")

    def zoom_in(self) -> None:
        if self.engine.is_open:
            self.engine.zoom_in()
            self._render_current_page()

    def zoom_out(self) -> None:
        if self.engine.is_open:
            self.engine.zoom_out()
            self._render_current_page()

    def reset_zoom(self) -> None:
        if self.engine.is_open:
            self.engine.reset_zoom()
            self._render_current_page()

    def rotate_page(self) -> None:
        if self.engine.is_open:
            self.engine.rotation = (self.engine.rotation + 90) % 360
            self._render_current_page()

    def prev_page(self) -> None:
        if self.engine.is_open and self.current_page_index > 0:
            self.current_page_index -= 1
            self._highlight_rects = []
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(self.current_page_index + 1)
            self.page_spin.blockSignals(False)
            self._render_current_page()
            self._update_controls_state()

    def next_page(self) -> None:
        if self.engine.is_open and self.current_page_index < self.engine.page_count - 1:
            self.current_page_index += 1
            self._highlight_rects = []
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(self.current_page_index + 1)
            self.page_spin.blockSignals(False)
            self._render_current_page()
            self._update_controls_state()

    def _on_spin_page_changed(self, value: int) -> None:
        if self.engine.is_open:
            idx = value - 1
            if 0 <= idx < self.engine.page_count:
                self.current_page_index = idx
                self._highlight_rects = []
                self._render_current_page()
                self._update_controls_state()

    def search_in_page(self) -> None:
        if not self.engine.is_open:
            return
        query = self.search_input.text().strip()
        if not query:
            self._highlight_rects = []
            self._render_current_page()
            return
        rects = self.engine.search_text(self.current_page_index, query)
        self._highlight_rects = rects
        self._render_current_page()
        self.copy_status_lbl.setText(f"{len(rects)} ocorrência(s) encontrada(s) na página.")

    def copy_selected_text(self) -> None:
        cursor = self.text_view.textCursor()
        selected = cursor.selectedText().replace("\u2029", "\n").strip()
        if not selected:
            selected = self.text_view.toPlainText().strip()
        if selected:
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(selected)
            self.copy_status_lbl.setText("✅ Texto copiado para a área de transferência!")
        else:
            self.copy_status_lbl.setText("Nenhum texto para copiar.")

    def copy_all_page_text(self) -> None:
        if not self.engine.is_open:
            return
        full_text = self.engine.get_page_text(self.current_page_index).strip()
        if full_text:
            clipboard = QGuiApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(full_text)
            self.text_view.setPlainText(full_text)
            self.copy_status_lbl.setText("✅ Todo o texto da página foi copiado!")
        else:
            self.copy_status_lbl.setText("Esta página não possui texto selecionável.")

    def _update_controls_state(self) -> None:
        has_doc = self.engine.is_open
        self.prev_page_btn.setEnabled(has_doc and self.current_page_index > 0)
        self.next_page_btn.setEnabled(has_doc and self.current_page_index < self.engine.page_count - 1)
        self.page_spin.setEnabled(has_doc)
        self.zoom_in_btn.setEnabled(has_doc)
        self.zoom_out_btn.setEnabled(has_doc)
        self.zoom_reset_btn.setEnabled(has_doc)
        self.rotate_btn.setEnabled(has_doc)
        self.search_btn.setEnabled(has_doc)
        self.copy_selected_btn.setEnabled(has_doc)
        self.copy_all_btn.setEnabled(has_doc)
