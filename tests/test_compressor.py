"""
Testes para o motor de compressão de PDF (`compressor.py`).
Verifica redução do tamanho total do arquivo, níveis de compressão e preservação do original.
"""

from pathlib import Path
import pymupdf
from cortex_pdf.core.compressor import compress_pdf
from tests.conftest import file_sha256


def test_compress_pdf_reduces_size_and_preserves_original(bloated_pdf: Path, tmp_path: Path):
    orig_hash = file_sha256(bloated_pdf)
    orig_size = bloated_pdf.stat().st_size

    res_high = compress_pdf(
        input_path=bloated_pdf,
        level="high",
        output_dir=tmp_path,
        keep_original_name=False,
        custom_name="pdf_otimizado",
    )

    assert res_high.output_path.exists()
    assert res_high.output_path.name == "pdf_otimizado.pdf"
    assert res_high.original_size_bytes == orig_size
    assert res_high.compressed_size_bytes < orig_size
    assert res_high.reduction_percent > 0
    assert file_sha256(bloated_pdf) == orig_hash

    with pymupdf.open(str(res_high.output_path)) as doc:
        assert len(doc) == 1
        assert "PDF com imagem pesada" in doc[0].get_text("text")


def test_compress_pdf_keep_original_name(sample_pdf: Path):
    orig_hash = file_sha256(sample_pdf)

    res = compress_pdf(
        input_path=sample_pdf,
        level="low",
        output_dir=sample_pdf.parent,
        keep_original_name=True,
    )
    assert res.output_path.exists()
    assert res.output_path != sample_pdf
    assert res.output_path.name == "documento_original_comprimido.pdf"
    assert file_sha256(sample_pdf) == orig_hash
