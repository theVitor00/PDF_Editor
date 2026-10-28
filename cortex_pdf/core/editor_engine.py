"""
Motor de Edição de Texto em PDF.
Permite inspecionar se o PDF possui camada de texto editável, listar trechos/blocos,
substituir textos mantendo posição e tamanho aproximado da fonte, editar blocos específicos
ou adicionar novos textos, gerando sempre um novo arquivo PDF sem modificar o original.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import pymupdf

from cortex_pdf.core.output_naming import resolve_output_path


@dataclass
class EditableSpan:
    """Representa um trecho de texto editável em uma página de PDF."""
    page_index: int
    block_index: int
    line_index: int
    span_index: int
    text: str
    bbox: tuple[float, float, float, float]
    origin: tuple[float, float]
    font_size: float
    color_rgb: tuple[float, float, float]


@dataclass
class EditResult:
    """Resultado de uma operação de edição de PDF."""
    input_path: Path
    output_path: Path
    replacements_count: int
    has_editable_text: bool
    message: str


def _int_color_to_rgb(color_int: int) -> tuple[float, float, float]:
    """Converte inteiro RGB do PyMuPDF (0xRRGGBB) para tupla (r, g, b) entre 0.0 e 1.0."""
    if not isinstance(color_int, int):
        return (0.0, 0.0, 0.0)
    r = ((color_int >> 16) & 255) / 255.0
    g = ((color_int >> 8) & 255) / 255.0
    b = (color_int & 255) / 255.0
    return (r, g, b)


def inspect_pdf_editability(pdf_path: Union[str, Path]) -> dict:
    """
    Verifica se o PDF permite edição de texto (não é criptografado sem senha e possui
    camada de texto real em vez de apenas imagens digitalizadas).
    """
    path = Path(pdf_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {path}")

    with pymupdf.open(str(path)) as doc:
        if doc.is_encrypted:
            return {
                "editable": False,
                "page_count": 0,
                "total_text_spans": 0,
                "reason": "O documento PDF é protegido por senha/criptografado.",
            }

        total_spans = 0
        for page in doc:
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if span.get("text", "").strip():
                                total_spans += 1

        if total_spans == 0:
            return {
                "editable": False,
                "page_count": len(doc),
                "total_text_spans": 0,
                "reason": "O PDF não contém camada de texto editável (documento digitalizado/apenas imagem).",
            }

        return {
            "editable": True,
            "page_count": len(doc),
            "total_text_spans": total_spans,
            "reason": "PDF possui camada de texto editável.",
        }


def extract_editable_spans(
    pdf_path: Union[str, Path],
    page_index: Optional[int] = None,
) -> list[EditableSpan]:
    """
    Extrai todos os spans de texto editáveis de uma página (ou de todo o PDF).
    """
    path = Path(pdf_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {path}")

    spans: list[EditableSpan] = []
    with pymupdf.open(str(path)) as doc:
        pages_to_scan = [page_index] if page_index is not None else range(len(doc))
        for p_idx in pages_to_scan:
            if p_idx < 0 or p_idx >= len(doc):
                raise IndexError(f"Página inválida: {p_idx}")
            page = doc[p_idx]
            text_dict = page.get_text("dict")
            for b_idx, block in enumerate(text_dict.get("blocks", [])):
                if block.get("type") != 0:
                    continue
                for l_idx, line in enumerate(block.get("lines", [])):
                    for s_idx, span in enumerate(line.get("spans", [])):
                        txt = span.get("text", "")
                        if not txt.strip():
                            continue
                        bbox = span.get("bbox", (0.0, 0.0, 0.0, 0.0))
                        origin = span.get("origin", (bbox[0], bbox[3]))
                        size = float(span.get("size", 11.0))
                        color = _int_color_to_rgb(span.get("color", 0))
                        spans.append(
                            EditableSpan(
                                page_index=p_idx,
                                block_index=b_idx,
                                line_index=l_idx,
                                span_index=s_idx,
                                text=txt,
                                bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
                                origin=(float(origin[0]), float(origin[1])),
                                font_size=size,
                                color_rgb=color,
                            )
                        )
    return spans


def replace_text_in_pdf(
    input_path: Union[str, Path],
    search_text: str,
    new_text: str,
    output_dir: Optional[Union[str, Path]] = None,
    keep_original_name: bool = True,
    custom_name: Optional[str] = None,
    page_index: Optional[int] = None,
) -> EditResult:
    """
    Localiza ocorrências de `search_text` no PDF e substitui por `new_text`,
    preservando posição, tamanho aproximado da fonte e cor quando possível.
    Gera um novo arquivo PDF sem modificar o original.
    """
    src = Path(input_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {src}")
    if not search_text:
        raise ValueError("O texto de busca não pode ser vazio.")

    info = inspect_pdf_editability(src)
    if not info["editable"]:
        raise ValueError(info["reason"])

    out_path = resolve_output_path(
        input_path=src,
        output_dir=output_dir,
        keep_original_name=keep_original_name,
        custom_name=custom_name,
        target_extension=".pdf",
        default_suffix="_editado",
    )

    replacements = 0
    with pymupdf.open(str(src)) as doc:
        pages_to_edit = [page_index] if page_index is not None else range(len(doc))
        for p_idx in pages_to_edit:
            if p_idx < 0 or p_idx >= len(doc):
                raise IndexError(f"Página fora do intervalo: {p_idx}")
            page = doc[p_idx]
            hit_rects = page.search_for(search_text)
            if not hit_rects:
                continue

            # Coleta metadados de fonte/cor dos spans que cruzam cada hit_rect
            text_dict = page.get_text("dict")
            insertions = []

            for rect in hit_rects:
                matched_size = 11.0
                matched_color = (0.0, 0.0, 0.0)
                baseline_y = rect.y1 - (rect.height * 0.18)

                for block in text_dict.get("blocks", []):
                    if block.get("type") != 0:
                        continue
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            span_rect = pymupdf.Rect(span.get("bbox", (0, 0, 0, 0)))
                            if span_rect.intersects(rect):
                                matched_size = float(span.get("size", 11.0))
                                matched_color = _int_color_to_rgb(span.get("color", 0))
                                origin = span.get("origin")
                                if origin and len(origin) == 2:
                                    baseline_y = float(origin[1])
                                break

                page.add_redact_annot(rect, fill=(1, 1, 1))
                insertions.append((rect.x0, baseline_y, matched_size, matched_color))
                replacements += 1

            # Aplica a remoção do texto antigo preservando imagens da página
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

            # Insere o novo texto nas coordenadas originais
            for x0, base_y, fsize, color in insertions:
                if new_text:
                    page.insert_text(
                        pymupdf.Point(x0, base_y),
                        new_text,
                        fontsize=max(4.0, fsize),
                        fontname="helv",
                        color=color,
                    )

        doc.save(str(out_path), garbage=2, deflate=True)

    return EditResult(
        input_path=src,
        output_path=out_path,
        replacements_count=replacements,
        has_editable_text=True,
        message=(
            f"{replacements} substituição(ões) realizada(s) com sucesso."
            if replacements > 0
            else "Nenhuma ocorrência do texto pesquisado foi encontrada; novo arquivo salvo."
        ),
    )


def edit_pdf_by_operations(
    input_path: Union[str, Path],
    replacements: list[dict],
    additions: Optional[list[dict]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    keep_original_name: bool = True,
    custom_name: Optional[str] = None,
) -> EditResult:
    """
    Realiza múltiplas edições em lote em um PDF (substituições de texto e/ou inserções
    de novos textos em páginas específicas) e salva em um novo arquivo.

    Formato de `replacements`:
        [{"page_index": 0 (ou None para todas), "old_text": "Antigo", "new_text": "Novo"}, ...]
    Formato de `additions`:
        [{"page_index": 0, "x": 72.0, "y": 100.0, "text": "Novo Texto", "fontsize": 12.0}, ...]
    """
    src = Path(input_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {src}")

    out_path = resolve_output_path(
        input_path=src,
        output_dir=output_dir,
        keep_original_name=keep_original_name,
        custom_name=custom_name,
        target_extension=".pdf",
        default_suffix="_editado",
    )

    total_changes = 0
    with pymupdf.open(str(src)) as doc:
        if doc.is_encrypted:
            raise ValueError("Não é possível editar um PDF criptografado.")

        # Processa substituições
        for item in replacements or []:
            old_t = item.get("old_text", "")
            new_t = item.get("new_text", "")
            target_page = item.get("page_index")
            if not old_t:
                continue

            pages = [target_page] if target_page is not None else range(len(doc))
            for p_idx in pages:
                if p_idx < 0 or p_idx >= len(doc):
                    continue
                page = doc[p_idx]
                hit_rects = page.search_for(old_t)
                if not hit_rects:
                    continue

                text_dict = page.get_text("dict")
                pending_inserts = []
                for rect in hit_rects:
                    fsize = float(item.get("fontsize") or 11.0)
                    color = (0.0, 0.0, 0.0)
                    base_y = rect.y1 - (rect.height * 0.18)

                    for block in text_dict.get("blocks", []):
                        if block.get("type") != 0:
                            continue
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                if pymupdf.Rect(span.get("bbox", (0, 0, 0, 0))).intersects(rect):
                                    if not item.get("fontsize"):
                                        fsize = float(span.get("size", 11.0))
                                    color = _int_color_to_rgb(span.get("color", 0))
                                    origin = span.get("origin")
                                    if origin and len(origin) == 2:
                                        base_y = float(origin[1])
                                    break

                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    pending_inserts.append((rect.x0, base_y, fsize, color))
                    total_changes += 1

                page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
                for x0, by, fs, col in pending_inserts:
                    if new_t:
                        page.insert_text(
                            pymupdf.Point(x0, by),
                            new_t,
                            fontsize=max(4.0, fs),
                            fontname="helv",
                            color=col,
                        )

        # Processa adições de novos textos
        for add in additions or []:
            p_idx = int(add.get("page_index", 0))
            if 0 <= p_idx < len(doc):
                txt = str(add.get("text", ""))
                if txt:
                    x = float(add.get("x", 50.0))
                    y = float(add.get("y", 50.0))
                    fs = float(add.get("fontsize", 12.0))
                    doc[p_idx].insert_text(
                        pymupdf.Point(x, y),
                        txt,
                        fontsize=max(4.0, fs),
                        fontname="helv",
                        color=(0.0, 0.0, 0.0),
                    )
                    total_changes += 1

        doc.save(str(out_path), garbage=2, deflate=True)

    return EditResult(
        input_path=src,
        output_path=out_path,
        replacements_count=total_changes,
        has_editable_text=True,
        message=f"Edição concluída ({total_changes} alteração(ões) aplicada(s)).",
    )
