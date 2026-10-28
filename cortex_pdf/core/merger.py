"""
Motor de Junção (Merge) de Arquivos PDF.
Permite juntar dois ou mais arquivos PDF em um único novo documento PDF,
sem modificar nenhum dos arquivos originais.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union
import pymupdf

from cortex_pdf.core.output_naming import resolve_output_path


@dataclass
class MergeResult:
    """Resultado da operação de junção de PDFs."""
    input_paths: list[Path]
    output_path: Path
    total_pages: int
    message: str


def merge_pdfs(
    input_paths: Sequence[Union[str, Path]],
    output_dir: Optional[Union[str, Path]] = None,
    keep_original_name: bool = True,
    custom_name: Optional[str] = None,
) -> MergeResult:
    """
    Junta dois ou mais arquivos PDF em um único novo arquivo PDF na ordem informada.
    """
    if len(input_paths) < 2:
        raise ValueError("São necessários pelo menos dois arquivos PDF para realizar a junção.")

    resolved_inputs: list[Path] = []
    for p in input_paths:
        rp = Path(p).resolve()
        if not rp.exists():
            raise FileNotFoundError(f"Arquivo PDF de entrada não encontrado: {rp}")
        resolved_inputs.append(rp)

    out_path = resolve_output_path(
        input_path=resolved_inputs[0],
        output_dir=output_dir,
        keep_original_name=keep_original_name,
        custom_name=custom_name,
        target_extension=".pdf",
        default_suffix="_unificado",
    )

    # Garante que out_path também não colida com nenhum dos demais inputs
    while out_path.resolve() in resolved_inputs:
        out_path = resolve_output_path(
            input_path=out_path,
            output_dir=out_path.parent,
            keep_original_name=False,
            custom_name=f"{out_path.stem}_unificado",
            target_extension=".pdf",
        )

    total_pages = 0
    with pymupdf.open() as merged_doc:
        for src in resolved_inputs:
            with pymupdf.open(str(src)) as src_doc:
                merged_doc.insert_pdf(src_doc)
                total_pages += len(src_doc)

        merged_doc.save(str(out_path), garbage=3, deflate=True)

    return MergeResult(
        input_paths=resolved_inputs,
        output_path=out_path,
        total_pages=total_pages,
        message=(
            f"{len(resolved_inputs)} arquivos PDF foram unidos em '{out_path.name}' "
            f"({total_pages} página(s) no total)."
        ),
    )
