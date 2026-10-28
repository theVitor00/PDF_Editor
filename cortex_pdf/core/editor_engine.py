"""
Motor de Edição de Texto em PDF com Alta Fidelidade de Formatação.
Permite inspecionar se o PDF possui camada de texto editável, detectar sombreamento/cor de fundo,
preservar estilo de fonte (negrito, itálico, serifa, monoespaçada), tamanho, cor original do texto
(incluindo textos claros/brancos sobre fundos escuros ou sombreados) e camadas de sombra (drop-shadow),
gerando sempre um novo arquivo PDF sem modificar o original.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import pymupdf

from cortex_pdf.core.output_naming import resolve_output_path


@dataclass
class EditableSpan:
    """Representa um trecho de texto editável em uma página de PDF com metadados completos de estilo."""
    page_index: int
    block_index: int
    line_index: int
    span_index: int
    text: str
    bbox: tuple[float, float, float, float]
    origin: tuple[float, float]
    font_name: str
    font_size: float
    flags: int
    is_bold: bool
    is_italic: bool
    color_rgb: tuple[float, float, float]
    background_rgb: Optional[tuple[float, float, float]] = None
    has_shading: bool = False


@dataclass
class EditResult:
    """Resultado de uma operação de edição de PDF."""
    input_path: Path
    output_path: Path
    replacements_count: int
    has_editable_text: bool
    message: str


def _int_color_to_rgb(color_int: int) -> tuple[float, float, float]:
    """Converte inteiro sRGB do PyMuPDF (0xRRGGBB) para tupla (r, g, b) entre 0.0 e 1.0."""
    if not isinstance(color_int, int):
        return (0.0, 0.0, 0.0)
    r = ((color_int >> 16) & 255) / 255.0
    g = ((color_int >> 8) & 255) / 255.0
    b = (color_int & 255) / 255.0
    return (round(r, 4), round(g, 4), round(b, 4))


def _detect_font_traits(font_name: str, flags: int) -> tuple[bool, bool, bool, bool]:
    """
    Retorna (is_bold, is_italic, is_serif, is_mono) combinando as flags do PDF
    e o nome da fonte original.
    """
    fn = (font_name or "").lower()
    is_bold = bool(flags & 16) or any(
        k in fn for k in ("bold", "black", "heavy", "demi", "semibold", "extrabold", "-bd", ",bold")
    )
    is_italic = bool(flags & 2) or any(
        k in fn for k in ("italic", "oblique", "slanted", "-it", "inclined", ",italic")
    )
    is_mono = bool(flags & 8) or any(
        k in fn for k in ("courier", "consolas", "mono", "menlo", "fira", "lucida console")
    )
    is_serif = (bool(flags & 4) and not is_mono) or any(
        k in fn for k in ("times", "georgia", "garamond", "cambria", "serif", "roman", "palatino")
    )
    return is_bold, is_italic, is_serif, is_mono


def _select_base14_font(font_name: str, flags: int) -> str:
    """
    Seleciona a variante Base-14 do PDF que preserva fielmente família (sans, serif, mono),
    peso (regular/negrito) e inclinação (itálico/oblíquo) do trecho original.
    """
    is_bold, is_italic, is_serif, is_mono = _detect_font_traits(font_name, flags)

    if is_mono:
        if is_bold and is_italic:
            return "cobi"
        if is_bold:
            return "cobo"
        if is_italic:
            return "coit"
        return "cour"

    if is_serif:
        if is_bold and is_italic:
            return "tibi"
        if is_bold:
            return "tibo"
        if is_italic:
            return "tiit"
        return "tiro"

    # Sans-serif (Helvetica)
    if is_bold and is_italic:
        return "hebi"
    if is_bold:
        return "hebo"
    if is_italic:
        return "heit"
    return "helv"


def _sample_background_rgb(page: pymupdf.Page, rect: pymupdf.Rect) -> tuple[tuple[float, float, float], bool]:
    """
    Amostra a cor de fundo/sombreamento real na borda interna do retângulo do texto.
    Retorna ((r, g, b), has_shading) onde `has_shading` indica se há sombreamento/fundo não-branco.
    """
    try:
        clip = pymupdf.Rect(rect.x0 - 2, rect.y0 - 2, rect.x1 + 2, rect.y1 + 2) & page.rect
        if clip.is_empty or clip.width < 1 or clip.height < 1:
            return (1.0, 1.0, 1.0), False
        pix = page.get_pixmap(clip=clip, alpha=False)
        if pix.width < 1 or pix.height < 1:
            return (1.0, 1.0, 1.0), False

        # Amostra pontos da margem do bbox onde normalmente fica apenas o fundo/sombreamento
        sample_coords = [
            (0, 0),
            (pix.width - 1, 0),
            (0, pix.height - 1),
            (pix.width - 1, pix.height - 1),
            (pix.width // 2, 0),
            (pix.width // 2, pix.height - 1),
        ]
        samples = [pix.pixel(x, y) for x, y in sample_coords]
        avg_r = sum(c[0] for c in samples) / (len(samples) * 255.0)
        avg_g = sum(c[1] for c in samples) / (len(samples) * 255.0)
        avg_b = sum(c[2] for c in samples) / (len(samples) * 255.0)
        bg_rgb = (round(avg_r, 4), round(avg_g, 4), round(avg_b, 4))
        has_shading = (avg_r < 0.96) or (avg_g < 0.96) or (avg_b < 0.96)
        return bg_rgb, has_shading
    except Exception:
        return (1.0, 1.0, 1.0), False


def _find_best_matching_span(
    rect: pymupdf.Rect,
    spans_list: list[dict],
    used_span_ids: set[int],
) -> Optional[dict]:
    """
    Localiza o span que melhor corresponde ao retângulo `rect`.
    Se houver múltiplos spans sobrepostos (como texto com sombra / drop-shadow),
    prioriza spans ainda não consumidos com maior sobreposição e menor distância de origem.
    """
    best_span = None
    best_score = -1.0

    for idx, sp in enumerate(spans_list):
        s_rect = pymupdf.Rect(sp["bbox"])
        if not s_rect.intersects(rect):
            continue

        inter = s_rect & rect
        if inter.is_empty:
            continue

        inter_area = inter.width * inter.height
        rect_area = max(0.001, rect.width * rect.height)
        coverage = inter_area / rect_area

        # Penaliza levemente se já foi usado (para suportar camadas de sombra + frente na ordem certa)
        unused_bonus = 10.0 if idx not in used_span_ids else 0.0
        dist_penalty = abs(s_rect.x0 - rect.x0) * 0.1 + abs(s_rect.y0 - rect.y0) * 0.1
        score = unused_bonus + coverage - dist_penalty

        if score > best_score:
            best_score = score
            best_span = (idx, sp)

    if best_span is not None:
        used_span_ids.add(best_span[0])
        return best_span[1]
    return None


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
    Extrai todos os spans de texto editáveis de uma página (ou de todo o PDF),
    incluindo informações de fonte, negrito/itálico, cor do texto e detecção de sombreamento de fundo.
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
                        font_name = str(span.get("font", "helv"))
                        flags = int(span.get("flags", 0))
                        size = float(span.get("size", 11.0))
                        color = _int_color_to_rgb(span.get("color", 0))
                        is_bold, is_italic, _, _ = _detect_font_traits(font_name, flags)
                        bg_rgb, has_shading = _sample_background_rgb(page, pymupdf.Rect(bbox))
                        spans.append(
                            EditableSpan(
                                page_index=p_idx,
                                block_index=b_idx,
                                line_index=l_idx,
                                span_index=s_idx,
                                text=txt,
                                bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
                                origin=(float(origin[0]), float(origin[1])),
                                font_name=font_name,
                                font_size=size,
                                flags=flags,
                                is_bold=is_bold,
                                is_italic=is_italic,
                                color_rgb=color,
                                background_rgb=bg_rgb,
                                has_shading=has_shading,
                            )
                        )
    return spans


def _collect_page_spans_flat(page: pymupdf.Page) -> list[dict]:
    """Retorna lista plana de todos os spans da página na ordem exata de renderização."""
    text_dict = page.get_text("dict")
    flat: list[dict] = []
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if span.get("text", "").strip():
                    flat.append(span)
    return flat


def _redact_and_replace_on_page(
    page: pymupdf.Page,
    search_text: str,
    new_text: str,
    override_fontsize: Optional[float] = None,
) -> int:
    """
    Executa a substituição de `search_text` por `new_text` em `page` preservando:
    - O fundo/sombreamento original (usando `fill=False` e `graphics=PDF_REDACT_LINE_ART_NONE`
      para nunca pintar retângulos brancos sobre áreas sombreadas nem apagar desenhos vetoriais)
    - A cor exata do texto de cada camada (incluindo texto branco `(1, 1, 1)` e sombras)
    - O estilo da fonte (família sans/serif/mono, negrito e itálico) e tamanho original.
    """
    hit_rects = page.search_for(search_text)
    if not hit_rects:
        return 0

    flat_spans = _collect_page_spans_flat(page)
    used_span_ids: set[int] = set()
    insertions: list[tuple[float, float, float, tuple[float, float, float], str]] = []

    # Verifica também se existem spans idênticos sobrepostos (efeito drop-shadow / texto sombreado)
    # que o `search_for` possa ter agrupado ou retornado em sequência
    for rect in hit_rects:
        matched_span = _find_best_matching_span(rect, flat_spans, used_span_ids)

        if matched_span is not None:
            fsize = float(override_fontsize or matched_span.get("size", 11.0))
            color = _int_color_to_rgb(matched_span.get("color", 0))
            font_name = str(matched_span.get("font", "helv"))
            flags = int(matched_span.get("flags", 0))
            base14_font = _select_base14_font(font_name, flags)
            origin = matched_span.get("origin")
            if origin and len(origin) == 2:
                baseline_y = float(origin[1])
                # Se a busca corresponde ao início do span, usa o x exato da origem
                span_bbox = matched_span.get("bbox", (rect.x0, rect.y0, rect.x1, rect.y1))
                if abs(rect.x0 - float(span_bbox[0])) < 2.5:
                    x0 = float(origin[0])
                else:
                    x0 = float(rect.x0)
            else:
                x0 = float(rect.x0)
                baseline_y = float(rect.y1 - (rect.height * 0.18))
        else:
            fsize = float(override_fontsize or 11.0)
            color = (0.0, 0.0, 0.0)
            base14_font = "helv"
            x0 = float(rect.x0)
            baseline_y = float(rect.y1 - (rect.height * 0.18))

        # fill=False garante que NENHUM retângulo branco seja desenhado sobre o fundo sombreado!
        page.add_redact_annot(rect, fill=False)
        insertions.append((x0, baseline_y, fsize, color, base14_font))

    # Remove APENAS os glifos de texto, mantendo 100% das imagens e artes vetoriais/sombreamentos de fundo
    page.apply_redactions(
        images=pymupdf.PDF_REDACT_IMAGE_NONE,
        graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
    )

    for x0, base_y, fsize, color, base14_font in insertions:
        if new_text:
            page.insert_text(
                pymupdf.Point(x0, base_y),
                new_text,
                fontsize=max(4.0, fsize),
                fontname=base14_font,
                color=color,
            )

    return len(insertions)


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
    preservando sombreamento/fundo original, posição, estilo da fonte (negrito/itálico/família),
    tamanho e cor (incluindo textos brancos sobre fundos coloridos/sombreados).
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
            replacements += _redact_and_replace_on_page(page, search_text, new_text)

        doc.save(str(out_path), garbage=2, deflate=True)

    return EditResult(
        input_path=src,
        output_path=out_path,
        replacements_count=replacements,
        has_editable_text=True,
        message=(
            f"{replacements} substituição(ões) realizada(s) preservando a formatação e o sombreamento original."
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
    de novos textos em páginas específicas) preservando sombreamento e formatação,
    e salva em um novo arquivo.
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

        for item in replacements or []:
            old_t = item.get("old_text", "")
            new_t = item.get("new_text", "")
            target_page = item.get("page_index")
            override_fs = float(item["fontsize"]) if item.get("fontsize") else None
            if not old_t:
                continue

            pages = [target_page] if target_page is not None else range(len(doc))
            for p_idx in pages:
                if p_idx < 0 or p_idx >= len(doc):
                    continue
                total_changes += _redact_and_replace_on_page(
                    doc[p_idx],
                    old_t,
                    new_t,
                    override_fontsize=override_fs,
                )

        for add in additions or []:
            p_idx = int(add.get("page_index", 0))
            if 0 <= p_idx < len(doc):
                txt = str(add.get("text", ""))
                if txt:
                    x = float(add.get("x", 50.0))
                    y = float(add.get("y", 50.0))
                    fs = float(add.get("fontsize", 12.0))
                    color = tuple(add.get("color_rgb", (0.0, 0.0, 0.0)))
                    doc[p_idx].insert_text(
                        pymupdf.Point(x, y),
                        txt,
                        fontsize=max(4.0, fs),
                        fontname="helv",
                        color=color,
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
