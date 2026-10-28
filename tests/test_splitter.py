"""
Testes para o motor de divisão de PDF (`splitter.py`).
Cobre:
- Dividir um PDF em 2 arquivos após uma página específica
- Dividir por intervalos personalizados
- Dividir a cada N páginas (ex: 1 página por PDF)
Garante que o arquivo original nunca é modificado.
"""

from pathlib import Path
import pymupdf
from cortex_pdf.core.splitter import (
    split_pdf_at_page,
    split_pdf_by_ranges,
    split_pdf_every_n_pages,
)
from tests.conftest import file_sha256


def test_split_pdf_at_page_into_two_files(sample_pdf: Path, tmp_path: Path):
    orig_hash = file_sha256(sample_pdf)

    res = split_pdf_at_page(
        input_path=sample_pdf,
        split_after_page=1,
        output_dir=tmp_path,
        keep_original_name=True,
    )

    assert len(res.output_paths) == 2
    assert res.parts_page_counts == [1, 2]
    assert res.output_paths[0].exists()
    assert res.output_paths[1].exists()
    assert file_sha256(sample_pdf) == orig_hash

    with pymupdf.open(str(res.output_paths[0])) as p1_doc:
        assert len(p1_doc) == 1
        assert "Titulo Principal Cortex PDF" in p1_doc[0].get_text("text")

    with pymupdf.open(str(res.output_paths[1])) as p2_doc:
        assert len(p2_doc) == 2
        assert "Segunda Pagina do Relatorio" in p2_doc[0].get_text("text")
        assert "Terceira Pagina Final" in p2_doc[1].get_text("text")


def test_split_pdf_every_page_with_custom_name(sample_pdf: Path, tmp_path: Path):
    orig_hash = file_sha256(sample_pdf)

    res = split_pdf_every_n_pages(
        input_path=sample_pdf,
        pages_per_part=1,
        output_dir=tmp_path,
        keep_original_name=False,
        custom_base_name="folha",
    )

    assert len(res.output_paths) == 3
    assert res.parts_page_counts == [1, 1, 1]
    assert res.output_paths[0].name == "folha_parte_01.pdf"
    assert res.output_paths[1].name == "folha_parte_02.pdf"
    assert res.output_paths[2].name == "folha_parte_03.pdf"
    assert file_sha256(sample_pdf) == orig_hash


def test_split_pdf_by_ranges_string(sample_pdf: Path, tmp_path: Path):
    orig_hash = file_sha256(sample_pdf)

    res = split_pdf_by_ranges(
        input_path=sample_pdf,
        page_ranges="1-2, 3",
        output_dir=tmp_path,
        keep_original_name=False,
        custom_base_name="secao",
    )

    assert len(res.output_paths) == 2
    assert res.parts_page_counts == [2, 1]
    assert file_sha256(sample_pdf) == orig_hash

