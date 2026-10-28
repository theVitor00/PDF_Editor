"""
Testes para o motor de edição de texto em PDF (`editor_engine.py`).
Verifica inspeção de editabilidade, extração de spans, substituição de texto,
manutenção do arquivo original intacto e opções de nomeação.
"""

from pathlib import Path
import pymupdf
import pytest

from cortex_pdf.core.editor_engine import (
    edit_pdf_by_operations,
    extract_editable_spans,
    inspect_pdf_editability,
    replace_text_in_pdf,
)
from tests.conftest import file_sha256


def test_inspect_and_extract_editable_spans(sample_pdf: Path):
    info = inspect_pdf_editability(sample_pdf)
    assert info["editable"] is True
    assert info["page_count"] == 3
    assert info["total_text_spans"] >= 5

    spans_p0 = extract_editable_spans(sample_pdf, page_index=0)
    assert any("Valor Antigo: 1000" in s.text for s in spans_p0)


def test_replace_text_in_pdf_creates_new_file_and_preserves_original(
    sample_pdf: Path, tmp_path: Path
):
    original_hash = file_sha256(sample_pdf)

    # 1. Mantendo o nome original (em pasta de saída separada)
    out_dir = tmp_path / "editados"
    res = replace_text_in_pdf(
        input_path=sample_pdf,
        search_text="Valor Antigo: 1000",
        new_text="Valor Novo: 2500",
        output_dir=out_dir,
        keep_original_name=True,
    )

    assert res.output_path.exists()
    assert res.output_path.name == sample_pdf.name
    assert res.output_path != sample_pdf
    assert res.replacements_count == 1
    assert file_sha256(sample_pdf) == original_hash

    with pymupdf.open(str(res.output_path)) as edited_doc:
        p1_txt = edited_doc[0].get_text("text")
        assert "Valor Novo: 2500" in p1_txt
        assert "Valor Antigo: 1000" not in p1_txt

    # 2. Modificando o nome do arquivo gerado
    res_custom = replace_text_in_pdf(
        input_path=sample_pdf,
        search_text="Segunda Pagina do Relatorio",
        new_text="Segunda Pagina Revisada",
        output_dir=tmp_path,
        keep_original_name=False,
        custom_name="relatorio_revisado.pdf",
    )
    assert res_custom.output_path.exists()
    assert res_custom.output_path.name == "relatorio_revisado.pdf"
    assert file_sha256(sample_pdf) == original_hash

    with pymupdf.open(str(res_custom.output_path)) as doc2:
        assert "Segunda Pagina Revisada" in doc2[1].get_text("text")


def test_edit_pdf_by_batch_operations(sample_pdf: Path, tmp_path: Path):
    original_hash = file_sha256(sample_pdf)

    res = edit_pdf_by_operations(
        input_path=sample_pdf,
        replacements=[
            {"page_index": 0, "old_text": "Titulo Principal Cortex PDF", "new_text": "Novo Titulo Editado"}
        ],
        additions=[
            {"page_index": 2, "x": 72, "y": 300, "text": "Assinado Digitalmente", "fontsize": 14}
        ],
        output_dir=tmp_path,
        keep_original_name=False,
        custom_name="documento_lote",
    )
    assert res.output_path.exists()
    assert res.replacements_count == 2
    assert file_sha256(sample_pdf) == original_hash

    with pymupdf.open(str(res.output_path)) as doc:
        assert "Novo Titulo Editado" in doc[0].get_text("text")
        assert "Assinado Digitalmente" in doc[2].get_text("text")


def test_non_editable_image_only_pdf_raises_clear_error(sample_image: Path, tmp_path: Path):
    # Cria um PDF contendo apenas uma imagem (sem camada de texto)
    img_only_pdf = tmp_path / "digitalizado_sem_texto.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page(width=400, height=300)
        page.insert_image(pymupdf.Rect(0, 0, 400, 300), filename=str(sample_image))
        doc.save(str(img_only_pdf))

    info = inspect_pdf_editability(img_only_pdf)
    assert info["editable"] is False

    with pytest.raises(ValueError, match="camada de texto"):
        replace_text_in_pdf(
            input_path=img_only_pdf,
            search_text="Qualquer",
            new_text="Novo",
            output_dir=tmp_path,
        )
