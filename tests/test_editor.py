"""
Testes para o motor de edição de texto em PDF (`editor_engine.py`).
Verifica inspeção de editabilidade, extração de spans, substituição de texto,
preservação de sombreamento de fundo (evitando quadrados brancos sobre textos brancos),
preservação de negrito/itálico/fonte, manutenção do arquivo original intacto e opções de nomeação.
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


def test_white_text_on_shaded_background_does_not_become_white_square(tmp_path: Path):
    """
    Garante que ao editar um texto com fonte branca sobre um fundo colorido/sombreado,
    o fundo sombreado NÃO é apagado nem coberto por um retângulo branco, e o novo texto
    continua branco e visível sobre o sombreamento original.
    """
    shaded_pdf = tmp_path / "cabecalho_sombreado.pdf"
    bg_color = (0.1, 0.2, 0.5)  # Azul escuro sombreado (~ RGB 25, 51, 127)

    with pymupdf.open() as doc:
        page = doc.new_page(width=595, height=842)
        # Desenha retângulo sombreado escuro
        banner_rect = pymupdf.Rect(50, 50, 450, 110)
        page.draw_rect(banner_rect, color=bg_color, fill=bg_color)
        # Insere texto com fonte branca em negrito sobre o sombreamento
        page.insert_text(
            pymupdf.Point(70, 88),
            "TITULO BRANCO SOMBREADO",
            fontsize=16,
            fontname="hebo",
            color=(1.0, 1.0, 1.0),
        )
        doc.save(str(shaded_pdf))

    # Verifica que extract_editable_spans detecta o sombreamento e a fonte branca em negrito
    spans = extract_editable_spans(shaded_pdf, page_index=0)
    assert len(spans) == 1
    assert spans[0].has_shading is True
    assert spans[0].color_rgb == (1.0, 1.0, 1.0)
    assert spans[0].is_bold is True

    # Substitui o texto branco
    res = replace_text_in_pdf(
        input_path=shaded_pdf,
        search_text="TITULO BRANCO SOMBREADO",
        new_text="NOVO TITULO BRANCO",
        output_dir=tmp_path,
        keep_original_name=False,
        custom_name="cabecalho_editado",
    )

    assert res.output_path.exists()
    with pymupdf.open(str(res.output_path)) as out_doc:
        out_page = out_doc[0]
        assert "NOVO TITULO BRANCO" in out_page.get_text("text")

        # Verifica os spans do novo PDF: deve continuar branco (1.0, 1.0, 1.0) e negrito
        new_spans = extract_editable_spans(res.output_path, page_index=0)
        assert len(new_spans) == 1
        assert new_spans[0].color_rgb == (1.0, 1.0, 1.0)
        assert new_spans[0].is_bold is True
        assert new_spans[0].has_shading is True

        # Verifica no pixmap renderizado que o interior do banner sombreado NÃO virou um quadrado branco
        pix = out_page.get_pixmap(alpha=False)
        # Amostra pixel dentro da região onde ficava o texto antigo (mas fora de traço de letra)
        sample_px = pix.pixel(68, 65)
        assert sample_px != (255, 255, 255), "O fundo sombreado não pode virar um quadrado branco!"
        assert sample_px[0] < 60 and sample_px[2] > 100


def test_drop_shadow_layered_text_preserves_both_layers(tmp_path: Path):
    """
    Verifica que textos com sombreamento em camada dupla (uma camada escura de sombra
    deslocada + uma camada frontal clara/branca) preservam ambas as cores e posições.
    """
    shadow_pdf = tmp_path / "texto_com_sombra.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page(width=595, height=842)
        page.draw_rect(pymupdf.Rect(40, 40, 400, 120), color=(0.3, 0.3, 0.35), fill=(0.3, 0.3, 0.35))
        # Camada 1: Sombra preta deslocada em (+1.5, +1.5)
        page.insert_text(
            pymupdf.Point(61.5, 81.5),
            "Texto Sombreado",
            fontsize=18,
            fontname="hebo",
            color=(0.1, 0.1, 0.1),
        )
        # Camada 2: Frente branca em (60, 80)
        page.insert_text(
            pymupdf.Point(60.0, 80.0),
            "Texto Sombreado",
            fontsize=18,
            fontname="hebo",
            color=(1.0, 1.0, 1.0),
        )
        doc.save(str(shadow_pdf))

    res = replace_text_in_pdf(
        input_path=shadow_pdf,
        search_text="Texto Sombreado",
        new_text="Texto Atualizado",
        output_dir=tmp_path,
        keep_original_name=False,
        custom_name="sombra_editada",
    )

    assert res.replacements_count == 2
    edited_spans = extract_editable_spans(res.output_path, page_index=0)
    colors = [s.color_rgb for s in edited_spans]
    assert (1.0, 1.0, 1.0) in colors
    assert any(c[0] < 0.2 and c[1] < 0.2 and c[2] < 0.2 for c in colors)


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
