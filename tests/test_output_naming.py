"""
Testes para o módulo de resolução segura de nomes de arquivos de saída (`output_naming.py`).
Verifica que o arquivo original nunca é sobrescrito e que o usuário pode manter
o nome original ou escolher um nome personalizado.
"""

from pathlib import Path
from cortex_pdf.core.output_naming import resolve_multi_output_paths, resolve_output_path


def test_keep_original_name_in_same_directory_creates_safe_new_file(sample_pdf: Path):
    out = resolve_output_path(
        input_path=sample_pdf,
        output_dir=sample_pdf.parent,
        keep_original_name=True,
        default_suffix="_novo",
    )
    assert out != sample_pdf.resolve()
    assert not out.exists()
    assert out.name == "documento_original_novo.pdf"


def test_keep_original_name_in_different_directory_preserves_exact_filename(
    sample_pdf: Path, tmp_path: Path
):
    dest_dir = tmp_path / "saida_exportada"
    out = resolve_output_path(
        input_path=sample_pdf,
        output_dir=dest_dir,
        keep_original_name=True,
    )
    assert out != sample_pdf.resolve()
    assert out.parent == dest_dir.resolve()
    assert out.name == sample_pdf.name


def test_custom_name_modifies_generated_filename(sample_pdf: Path, tmp_path: Path):
    out = resolve_output_path(
        input_path=sample_pdf,
        output_dir=tmp_path,
        keep_original_name=False,
        custom_name="meu_relatorio_final",
        target_extension=".pdf",
    )
    assert out != sample_pdf.resolve()
    assert out.name == "meu_relatorio_final.pdf"


def test_custom_name_collision_with_original_never_overwrites(sample_pdf: Path):
    out = resolve_output_path(
        input_path=sample_pdf,
        output_dir=sample_pdf.parent,
        keep_original_name=False,
        custom_name=sample_pdf.name,
        default_suffix="_copia",
    )
    assert out != sample_pdf.resolve()
    assert out.name == "documento_original_copia.pdf"


def test_resolve_multi_output_paths_creates_distinct_files(sample_pdf: Path, tmp_path: Path):
    paths_keep = resolve_multi_output_paths(
        input_path=sample_pdf,
        part_count=3,
        output_dir=tmp_path,
        keep_original_name=True,
    )
    assert len(paths_keep) == 3
    assert paths_keep[0].name == "documento_original_parte_01.pdf"
    assert paths_keep[1].name == "documento_original_parte_02.pdf"
    assert paths_keep[2].name == "documento_original_parte_03.pdf"

    paths_custom = resolve_multi_output_paths(
        input_path=sample_pdf,
        part_count=2,
        output_dir=tmp_path,
        keep_original_name=False,
        custom_base_name="capitulo",
    )
    assert len(paths_custom) == 2
    assert paths_custom[0].name == "capitulo_parte_01.pdf"
    assert paths_custom[1].name == "capitulo_parte_02.pdf"
