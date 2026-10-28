"""
Motor de Divisão (Split) de Arquivos PDF.
Permite dividir um único arquivo PDF em dois ou mais arquivos PDF:
1. Dividir em dois arquivos a partir de uma página de corte (ex: Parte 1 = 1..k, Parte 2 = k+1..N)
2. Dividir por intervalos personalizados de páginas (ex: '1-2, 3-5, 6')
3. Dividir cada página em um arquivo PDF individual (ou blocos de N páginas)

O arquivo original nunca é modificado.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union
import pymupdf

from cortex_pdf.core.output_naming import resolve_multi_output_paths


@dataclass
class SplitResult:
    """Resultado da operação de divisão de PDF."""
    input_path: Path
    output_paths: list[Path]
    parts_page_counts: list[int]
    message: str


def split_pdf_at_page(
    input_path: Union[str, Path],
    split_after_page: int,
    output_dir: Optional[Union[str, Path]] = None,
    keep_original_name: bool = True,
    custom_base_name: Optional[str] = None,
) -> SplitResult:
    """
    Divide um PDF de N páginas em exatamente 2 arquivos PDF:
    - Parte 1: páginas de 1 até `split_after_page` (1-based, inclusivo)
    - Parte 2: páginas de `split_after_page + 1` até N
    """
    src = Path(input_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {src}")

    with pymupdf.open(str(src)) as doc:
        total = len(doc)
        if total < 2:
            raise ValueError("O PDF precisa ter pelo menos 2 páginas para ser dividido em dois arquivos.")
        if split_after_page < 1 or split_after_page >= total:
            raise ValueError(
                f"A página de corte deve estar entre 1 e {total - 1} (informado: {split_after_page})."
            )

    ranges = [(1, split_after_page), (split_after_page + 1, total)]
    return split_pdf_by_ranges(
        input_path=src,
        page_ranges=ranges,
        output_dir=output_dir,
        keep_original_name=keep_original_name,
        custom_base_name=custom_base_name,
    )


def split_pdf_every_n_pages(
    input_path: Union[str, Path],
    pages_per_part: int = 1,
    output_dir: Optional[Union[str, Path]] = None,
    keep_original_name: bool = True,
    custom_base_name: Optional[str] = None,
) -> SplitResult:
    """
    Divide um PDF em múltiplos arquivos com até `pages_per_part` páginas cada.
    Se `pages_per_part=1`, cada página vira um arquivo PDF independente.
    """
    src = Path(input_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {src}")
    if pages_per_part < 1:
        raise ValueError("O número de páginas por parte deve ser pelo menos 1.")

    with pymupdf.open(str(src)) as doc:
        total = len(doc)
        if total < 2:
            raise ValueError("O PDF precisa ter pelo menos 2 páginas para ser dividido.")

    ranges: list[tuple[int, int]] = []
    start = 1
    while start <= total:
        end = min(total, start + pages_per_part - 1)
        ranges.append((start, end))
        start = end + 1

    if len(ranges) < 2:
        raise ValueError(
            "A configuração escolhida resultaria em apenas 1 arquivo. "
            "Reduza o número de páginas por arquivo para dividir em 2 ou mais partes."
        )

    return split_pdf_by_ranges(
        input_path=src,
        page_ranges=ranges,
        output_dir=output_dir,
        keep_original_name=keep_original_name,
        custom_base_name=custom_base_name,
    )


def parse_page_ranges_string(ranges_str: str, total_pages: int) -> list[tuple[int, int]]:
    """
    Converte uma string como '1-2, 3, 4-5' em uma lista de tuplas (inicio_1based, fim_1based).
    """
    if not ranges_str or not ranges_str.strip():
        raise ValueError("Informe ao menos dois intervalos de páginas (ex: '1-2, 3-4').")

    parts = [p.strip() for p in ranges_str.split(",") if p.strip()]
    if len(parts) < 2:
        raise ValueError("Informe pelo menos 2 intervalos separados por vírgula para dividir o PDF.")

    parsed: list[tuple[int, int]] = []
    for part in parts:
        if "-" in part:
            sub = part.split("-", 1)
            try:
                start = int(sub[0].strip())
                end = int(sub[1].strip())
            except ValueError as exc:
                raise ValueError(f"Intervalo inválido: '{part}'.") from exc
        else:
            try:
                start = int(part)
                end = start
            except ValueError as exc:
                raise ValueError(f"Número de página inválido: '{part}'.") from exc

        if start < 1 or end < start or end > total_pages:
            raise ValueError(
                f"Intervalo '{part}' fora dos limites do documento (1 a {total_pages})."
            )
        parsed.append((start, end))

    return parsed


def split_pdf_by_ranges(
    input_path: Union[str, Path],
    page_ranges: Union[str, Sequence[tuple[int, int]]],
    output_dir: Optional[Union[str, Path]] = None,
    keep_original_name: bool = True,
    custom_base_name: Optional[str] = None,
) -> SplitResult:
    """
    Divide o PDF de acordo com uma lista de intervalos (1-based inclusivos) ou string de intervalos.
    """
    src = Path(input_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {src}")

    with pymupdf.open(str(src)) as src_doc:
        total_pages = len(src_doc)
        if total_pages < 2:
            raise ValueError("O PDF precisa ter pelo menos 2 páginas para ser dividido.")

        if isinstance(page_ranges, str):
            ranges_list = parse_page_ranges_string(page_ranges, total_pages)
        else:
            ranges_list = list(page_ranges)

        if len(ranges_list) < 2:
            raise ValueError("A divisão requer a geração de pelo menos 2 arquivos PDF.")

        for start, end in ranges_list:
            if start < 1 or end < start or end > total_pages:
                raise ValueError(
                    f"Intervalo ({start}, {end}) inválido para documento com {total_pages} páginas."
                )

        out_paths = resolve_multi_output_paths(
            input_path=src,
            part_count=len(ranges_list),
            output_dir=output_dir,
            keep_original_name=keep_original_name,
            custom_base_name=custom_base_name,
            target_extension=".pdf",
        )

        counts: list[int] = []
        for idx, (start_1b, end_1b) in enumerate(ranges_list):
            with pymupdf.open() as part_doc:
                part_doc.insert_pdf(
                    src_doc,
                    from_page=start_1b - 1,
                    to_page=end_1b - 1,
                )
                part_doc.save(str(out_paths[idx]), garbage=2, deflate=True)
                counts.append(len(part_doc))

    return SplitResult(
        input_path=src,
        output_paths=out_paths,
        parts_page_counts=counts,
        message=f"PDF dividido com sucesso em {len(out_paths)} novos arquivos.",
    )
