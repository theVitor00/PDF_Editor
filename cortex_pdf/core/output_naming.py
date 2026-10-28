"""
Gerenciamento seguro de caminhos de saída.
Garante que o arquivo original NUNCA seja modificado ou sobrescrito,
permitindo ao usuário escolher entre manter o nome original ou definir um novo nome.
"""

from pathlib import Path
from typing import Optional, Union


def resolve_output_path(
    input_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    keep_original_name: bool = True,
    custom_name: Optional[str] = None,
    target_extension: Optional[str] = None,
    default_suffix: str = "_novo",
) -> Path:
    """
    Resolve o caminho do novo arquivo a ser gerado garantindo que o arquivo de entrada
    original jamais seja modificado ou sobrescrito.

    Parâmetros:
        input_path: Caminho do arquivo de entrada original.
        output_dir: Diretório onde o novo arquivo será salvo (padrão: mesmo diretório da entrada).
        keep_original_name: Se True, mantém o nome base do arquivo original.
                            Se False, utiliza `custom_name`.
        custom_name: Nome personalizado escolhido pelo usuário (com ou sem extensão).
        target_extension: Extensão final desejada (ex: '.pdf', '.docx', '.html').
                          Se omitida, usa a extensão do arquivo original.
        default_suffix: Sufixo utilizado caso o arquivo de saída colida com o arquivo
                        de entrada no mesmo diretório.

    Retorna:
        Path absoluto do novo arquivo seguro para escrita.
    """
    src = Path(input_path).resolve()
    dest_dir = Path(output_dir).resolve() if output_dir else src.parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = target_extension if target_extension else src.suffix
    if ext and not ext.startswith("."):
        ext = f".{ext}"

    if keep_original_name or not custom_name or not custom_name.strip():
        base_stem = src.stem
    else:
        cleaned = custom_name.strip()
        custom_path = Path(cleaned)
        if custom_path.suffix.lower() == ext.lower() and custom_path.stem:
            base_stem = custom_path.stem
        else:
            base_stem = cleaned

    candidate = dest_dir / f"{base_stem}{ext}"

    # Proteção estrita: nunca sobrescrever o arquivo original nem arquivos já existentes
    if candidate.resolve() == src or candidate.exists():
        # Se o usuário optou por manter o nome no mesmo diretório onde o arquivo já existe,
        # adicionamos o sufixo ou contador incremental para gerar um novo arquivo sem tocar no original.
        candidate_with_suffix = dest_dir / f"{base_stem}{default_suffix}{ext}"
        if candidate_with_suffix.resolve() != src and not candidate_with_suffix.exists():
            return candidate_with_suffix

        counter = 1
        while True:
            numbered = dest_dir / f"{base_stem}{default_suffix}_{counter}{ext}"
            if numbered.resolve() != src and not numbered.exists():
                return numbered
            counter += 1

    return candidate


def resolve_multi_output_paths(
    input_path: Union[str, Path],
    part_count: int,
    output_dir: Optional[Union[str, Path]] = None,
    keep_original_name: bool = True,
    custom_base_name: Optional[str] = None,
    target_extension: str = ".pdf",
) -> list[Path]:
    """
    Gera múltiplos caminhos seguros de saída (ex: para divisão de PDF ou exportação de páginas).
    Nunca modifica o arquivo original.
    """
    src = Path(input_path).resolve()
    dest_dir = Path(output_dir).resolve() if output_dir else src.parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = target_extension if target_extension.startswith(".") else f".{target_extension}"

    if keep_original_name or not custom_base_name or not custom_base_name.strip():
        base_stem = src.stem
    else:
        cleaned = custom_base_name.strip()
        cpath = Path(cleaned)
        base_stem = cpath.stem if cpath.suffix.lower() == ext.lower() and cpath.stem else cleaned

    paths: list[Path] = []
    for idx in range(1, part_count + 1):
        candidate = dest_dir / f"{base_stem}_parte_{idx:02d}{ext}"
        counter = 1
        while candidate.resolve() == src or candidate.exists() or candidate in paths:
            candidate = dest_dir / f"{base_stem}_parte_{idx:02d}_{counter}{ext}"
            counter += 1
        paths.append(candidate)

    return paths

