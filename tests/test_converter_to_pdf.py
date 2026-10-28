"""
Testes para conversão de outros formatos para PDF (`converter_to_pdf.py`).
Cobre: DOCX, PNG, HTML, TXT, Markdown, CSV e XLSX.
Garante que os arquivos originais permanecem intactos.
"""

from pathlib import Path
import pymupdf
from cortex_pdf.core.converter_to_pdf import convert_to_pdf
from tests.conftest import file_sha256


def test_convert_docx_to_pdf(sample_docx: Path, tmp_path: Path):
    orig_hash = file_sha256(sample_docx)

    res = convert_to_pdf(
        input_path=sample_docx,
        output_dir=tmp_path,
        keep_original_name=True,
    )
    assert res.output_path.exists()
    assert res.output_path.name == "contrato_exemplo.pdf"
    assert file_sha256(sample_docx) == orig_hash

    with pymupdf.open(str(res.output_path)) as doc:
        assert len(doc) >= 1
        text = doc[0].get_text("text")
        assert "Contrato de Prestacao de Servicos" in text
        assert "Consultoria Tecnica" in text


def test_convert_image_to_pdf(sample_image: Path, tmp_path: Path):
    orig_hash = file_sha256(sample_image)

    res = convert_to_pdf(
        input_path=sample_image,
        output_dir=tmp_path,
        keep_original_name=False,
        custom_name="grafico_convertido",
    )
    assert res.output_path.exists()
    assert res.output_path.name == "grafico_convertido.pdf"
    assert file_sha256(sample_image) == orig_hash

    with pymupdf.open(str(res.output_path)) as doc:
        assert len(doc) == 1
        assert doc[0].rect.width == 400
        assert doc[0].rect.height == 300


def test_convert_txt_md_html_csv_xlsx_to_pdf(
    sample_txt: Path,
    sample_md: Path,
    sample_html: Path,
    sample_csv: Path,
    sample_xlsx: Path,
    tmp_path: Path,
):
    cases = [
        (sample_txt, "Ata de Reuniao"),
        (sample_md, "Guia Rapido"),
        (sample_html, "Relatorio HTML"),
        (sample_csv, "Janeiro"),
        (sample_xlsx, "Licenca Cortex"),
    ]

    for src_file, expected_text in cases:
        before_hash = file_sha256(src_file)
        res = convert_to_pdf(
            input_path=src_file,
            output_dir=tmp_path,
            keep_original_name=True,
        )
        assert res.output_path.exists()
        assert res.output_path.suffix == ".pdf"
        assert file_sha256(src_file) == before_hash

        with pymupdf.open(str(res.output_path)) as pdf_doc:
            extracted = pdf_doc[0].get_text("text")
            assert expected_text in extracted
