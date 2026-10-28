"""
Testes para o motor de junção de PDFs (`merger.py`).
Verifica que dois ou mais arquivos PDF são unidos na ordem correta sem modificar os originais.
"""

from pathlib import Path
import pymupdf
import pytest
from cortex_pdf.core.merger import merge_pdfs
from tests.conftest import file_sha256


def test_merge_two_pdfs_creates_combined_file_and_keeps_originals(
    sample_pdf: Path, second_pdf: Path, tmp_path: Path
):
    hash1 = file_sha256(sample_pdf)
    hash2 = file_sha256(second_pdf)

    res = merge_pdfs(
        input_paths=[sample_pdf, second_pdf],
        output_dir=tmp_path,
        keep_original_name=False,
        custom_name="documentos_unidos",
    )

    assert res.output_path.exists()
    assert res.output_path.name == "documentos_unidos.pdf"
    assert res.total_pages == 5  # 3 páginas do sample_pdf + 2 páginas do second_pdf
    assert file_sha256(sample_pdf) == hash1
    assert file_sha256(second_pdf) == hash2

    with pymupdf.open(str(res.output_path)) as merged:
        assert len(merged) == 5
        assert "Titulo Principal Cortex PDF" in merged[0].get_text("text")
        assert "Anexo Parte A" in merged[3].get_text("text")
        assert "Anexo Parte B" in merged[4].get_text("text")


def test_merge_requires_at_least_two_files(sample_pdf: Path):
    with pytest.raises(ValueError, match="pelo menos dois"):
        merge_pdfs([sample_pdf])
