"""
Testes automatizados da Interface Gráfica (PyQt6) em modo offscreen.
Verifica que a janela principal e todas as 7 abas executam o fluxo:
Entrada -> Processamento -> Saída corretamente.
"""

from pathlib import Path
import pytest
from PyQt6.QtWidgets import QApplication

from cortex_pdf.ui.main_window import CortexMainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_and_all_tabs_workflow(
    qapp,
    sample_pdf: Path,
    second_pdf: Path,
    sample_txt: Path,
    tmp_path: Path,
):
    window = CortexMainWindow()
    assert window.stack.count() == 7

    # 1. Aba Visualizar PDF
    window.switch_tab(0)
    viewer = window.viewer_tab
    viewer.load_pdf(sample_pdf)
    assert viewer.engine.is_open
    assert viewer.engine.page_count == 3
    viewer.zoom_in()
    assert viewer.engine.zoom > 1.0
    viewer.zoom_out()
    viewer.next_page()
    assert viewer.current_page_index == 1
    viewer.prev_page()
    assert viewer.current_page_index == 0
    viewer.copy_all_page_text()
    assert "copiado" in viewer.copy_status_lbl.text().lower()

    # 2. Aba Editar Texto do PDF
    window.switch_tab(1)
    editor = window.editor_tab
    editor.input_card.set_file_path(str(sample_pdf))
    editor.search_text_edit.setText("Valor Antigo: 1000")
    editor.replace_text_edit.setText("Valor Novo: 9999")
    editor.output_card.output_dir_edit.setText(str(tmp_path / "ui_edit"))
    editor.output_card.radio_custom.setChecked(True)
    editor.output_card.custom_name_edit.setText("editado_via_ui")
    editor.run_edit()
    assert (tmp_path / "ui_edit" / "editado_via_ui.pdf").exists()

    # 3. Aba Converter PDF para Outros Formatos
    window.switch_tab(2)
    conv_from = window.convert_from_pdf_tab
    conv_from.input_card.set_file_path(str(sample_pdf))
    # Seleciona TXT (índice 3)
    conv_from.format_combo.setCurrentIndex(3)
    conv_from.output_card.output_dir_edit.setText(str(tmp_path / "ui_from_pdf"))
    conv_from.run_conversion()
    assert (tmp_path / "ui_from_pdf" / "documento_original.txt").exists()

    # 4. Aba Converter Outros Formatos para PDF
    window.switch_tab(3)
    conv_to = window.convert_to_pdf_tab
    conv_to.input_card.set_file_path(str(sample_txt))
    conv_to.output_card.output_dir_edit.setText(str(tmp_path / "ui_to_pdf"))
    conv_to.run_conversion()
    assert (tmp_path / "ui_to_pdf" / "notas_reuniao.pdf").exists()

    # 5. Aba Comprimir PDF
    window.switch_tab(4)
    comp = window.compress_tab
    comp.input_card.set_file_path(str(sample_pdf))
    comp.output_card.output_dir_edit.setText(str(tmp_path / "ui_compress"))
    comp.run_compression()
    assert (tmp_path / "ui_compress" / "documento_original.pdf").exists()

    # 6. Aba Juntar PDFs
    window.switch_tab(5)
    merge = window.merge_tab
    merge.add_file_path(str(sample_pdf))
    merge.add_file_path(str(second_pdf))
    merge.output_card.output_dir_edit.setText(str(tmp_path / "ui_merge"))
    merge.output_card.radio_custom.setChecked(True)
    merge.output_card.custom_name_edit.setText("unificado_ui")
    merge.run_merge()
    assert (tmp_path / "ui_merge" / "unificado_ui.pdf").exists()

    # 7. Aba Dividir PDF
    window.switch_tab(6)
    split = window.split_tab
    split.input_card.set_file_path(str(sample_pdf))
    split.output_card.output_dir_edit.setText(str(tmp_path / "ui_split"))
    split.run_split()
    assert (tmp_path / "ui_split" / "documento_original_parte_01.pdf").exists()
    assert (tmp_path / "ui_split" / "documento_original_parte_02.pdf").exists()

    viewer.engine.close()
    window.close()
