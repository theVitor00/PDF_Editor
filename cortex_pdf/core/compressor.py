"""
Motor de Compressão de PDF.
Reduz o tamanho total do arquivo PDF através de:
- Desduplicação de objetos e remoção de objetos órfãos (garbage=4)
- Compressão de fluxos de dados, imagens e fontes (deflate)
- Recompressão e subamostragem inteligente de imagens embutidas (níveis Médio e Alto)
- Limpeza de metadados redundantes

O arquivo original nunca é modificado; um novo arquivo comprimido é gerado.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import pymupdf

from cortex_pdf.core.output_naming import resolve_output_path


COMPRESSION_LEVELS = ("low", "medium", "high")


@dataclass
class CompressionResult:
    """Resultado da operação de compressão de PDF."""
    input_path: Path
    output_path: Path
    original_size_bytes: int
    compressed_size_bytes: int
    reduction_percent: float
    level: str
    message: str


def compress_pdf(
    input_path: Union[str, Path],
    level: str = "medium",
    output_dir: Optional[Union[str, Path]] = None,
    keep_original_name: bool = True,
    custom_name: Optional[str] = None,
) -> CompressionResult:
    """
    Comprime um documento PDF gerando um novo arquivo otimizado.

    Níveis disponíveis:
        - 'low': Compressão sem perdas (limpeza de fluxos, deflate e garbage collection).
        - 'medium': Compressão balanceada (inclui otimização de imagens para 150 DPI, qualidade 75).
        - 'high': Compressão máxima (otimização de imagens para 96 DPI, qualidade 50).
    """
    src = Path(input_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {src}")

    norm_level = level.lower().strip()
    if norm_level not in COMPRESSION_LEVELS:
        raise ValueError(
            f"Nível de compressão inválido: '{level}'. Use um de: {', '.join(COMPRESSION_LEVELS)}"
        )

    out_path = resolve_output_path(
        input_path=src,
        output_dir=output_dir,
        keep_original_name=keep_original_name,
        custom_name=custom_name,
        target_extension=".pdf",
        default_suffix="_comprimido",
    )

    original_size = src.stat().st_size

    with pymupdf.open(str(src)) as doc:
        if norm_level in ("medium", "high"):
            dpi_threshold = 180 if norm_level == "medium" else 110
            dpi_target = 140 if norm_level == "medium" else 90
            quality = 75 if norm_level == "medium" else 50
            if hasattr(doc, "rewrite_images"):
                try:
                    doc.rewrite_images(
                        dpi_threshold=dpi_threshold,
                        dpi_target=dpi_target,
                        quality=quality,
                    )
                except Exception:
                    pass

        if hasattr(doc, "scrub"):
            try:
                doc.scrub(
                    attached_files=False,
                    clean_pages=True,
                    embedded_files=False,
                    hidden_text=False,
                    javascript=False,
                    metadata=False,
                    redactions=False,
                    redact_images=0,
                    remove_links=False,
                    reset_fields=False,
                    reset_responses=False,
                    thumbnails=True,
                    xml_metadata=True,
                )
            except Exception:
                pass

        doc.save(
            str(out_path),
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            clean=True,
        )

    compressed_size = out_path.stat().st_size
    if original_size > 0:
        reduction = max(0.0, ((original_size - compressed_size) / original_size) * 100.0)
    else:
        reduction = 0.0

    return CompressionResult(
        input_path=src,
        output_path=out_path,
        original_size_bytes=original_size,
        compressed_size_bytes=compressed_size,
        reduction_percent=round(reduction, 2),
        level=norm_level,
        message=(
            f"PDF comprimido com sucesso! Tamanho original: {_format_bytes(original_size)} -> "
            f"Novo tamanho: {_format_bytes(compressed_size)} ({reduction:.1f}% de redução)."
        ),
    )


def _format_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"
