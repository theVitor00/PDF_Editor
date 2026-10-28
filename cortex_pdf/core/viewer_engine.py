"""
Motor de Visualização de PDF.
Suporta renderização com zoom-in / zoom-out, rotação, extração de texto,
seleção de texto por área retangular (rubber-band), busca de termos e cópia.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import pymupdf


@dataclass
class TextBlockInfo:
    """Representa um bloco de texto extraído de uma página do PDF."""
    block_no: int
    bbox: tuple[float, float, float, float]
    text: str


@dataclass
class RenderedPage:
    """Resultado da renderização de uma página em imagem."""
    page_index: int
    width: int
    height: int
    zoom: float
    png_bytes: bytes


class PDFViewerEngine:
    """
    Gerencia a abertura e leitura de documentos PDF para visualização interativa.
    Garante leitura não-destrutiva do arquivo original.
    """

    MIN_ZOOM = 0.25
    MAX_ZOOM = 4.0
    ZOOM_STEP = 0.25

    def __init__(self, pdf_path: Optional[Union[str, Path]] = None):
        self._doc: Optional[pymupdf.Document] = None
        self._path: Optional[Path] = None
        self._zoom: float = 1.0
        self._rotation: int = 0
        if pdf_path is not None:
            self.open_document(pdf_path)

    @property
    def is_open(self) -> bool:
        return self._doc is not None and not self._doc.is_closed

    @property
    def file_path(self) -> Optional[Path]:
        return self._path

    @property
    def page_count(self) -> int:
        if not self.is_open:
            return 0
        return len(self._doc)

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, round(float(value), 2)))

    @property
    def rotation(self) -> int:
        return self._rotation

    @rotation.setter
    def rotation(self, degrees: int) -> None:
        self._rotation = degrees % 360

    def open_document(self, pdf_path: Union[str, Path]) -> None:
        """Abre um documento PDF para leitura."""
        path = Path(pdf_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {path}")
        self.close()
        self._doc = pymupdf.open(str(path))
        self._path = path
        self._zoom = 1.0
        self._rotation = 0

    def close(self) -> None:
        """Fecha o documento atual."""
        if self._doc is not None and not self._doc.is_closed:
            self._doc.close()
        self._doc = None
        self._path = None

    def zoom_in(self, step: Optional[float] = None) -> float:
        """Aumenta o nível de zoom e retorna o novo valor."""
        inc = step if step is not None else self.ZOOM_STEP
        self.zoom = self._zoom + inc
        return self._zoom

    def zoom_out(self, step: Optional[float] = None) -> float:
        """Diminui o nível de zoom e retorna o novo valor."""
        dec = step if step is not None else self.ZOOM_STEP
        self.zoom = self._zoom - dec
        return self._zoom

    def reset_zoom(self) -> float:
        """Restaura o zoom para 100% (1.0)."""
        self.zoom = 1.0
        return self._zoom

    def render_page(
        self,
        page_index: int,
        zoom: Optional[float] = None,
        rotation: Optional[int] = None,
    ) -> RenderedPage:
        """Renderiza uma página do PDF em bytes PNG na escala solicitada."""
        self._ensure_valid_page(page_index)
        effective_zoom = zoom if zoom is not None else self._zoom
        effective_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, float(effective_zoom)))
        effective_rot = rotation if rotation is not None else self._rotation

        page = self._doc[page_index]
        matrix = pymupdf.Matrix(effective_zoom, effective_zoom).prerotate(effective_rot)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        return RenderedPage(
            page_index=page_index,
            width=pix.width,
            height=pix.height,
            zoom=effective_zoom,
            png_bytes=pix.tobytes("png"),
        )

    def get_page_text(self, page_index: int) -> str:
        """Extrai todo o texto de uma página específica."""
        self._ensure_valid_page(page_index)
        page = self._doc[page_index]
        return page.get_text("text")

    def get_all_text(self) -> str:
        """Extrai o texto de todas as páginas do documento."""
        if not self.is_open:
            raise RuntimeError("Nenhum documento PDF aberto.")
        parts = []
        for idx in range(len(self._doc)):
            parts.append(self.get_page_text(idx))
        return "\n".join(parts)

    def get_text_in_rect(
        self,
        page_index: int,
        rect_coords: tuple[float, float, float, float],
        from_zoomed_coords: bool = False,
    ) -> str:
        """
        Extrai o texto contido dentro de um retângulo de seleção (x0, y0, x1, y1).
        Se `from_zoomed_coords=True`, converte as coordenadas da tela (com zoom)
        para coordenadas reais da página do PDF.
        """
        self._ensure_valid_page(page_index)
        x0, y0, x1, y1 = rect_coords
        if from_zoomed_coords and self._zoom > 0:
            x0 /= self._zoom
            y0 /= self._zoom
            x1 /= self._zoom
            y1 /= self._zoom

        clip_rect = pymupdf.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        page = self._doc[page_index]
        return page.get_text("text", clip=clip_rect).strip()

    def get_text_blocks(self, page_index: int) -> list[TextBlockInfo]:
        """Retorna os blocos de texto da página com suas respectivas coordenadas."""
        self._ensure_valid_page(page_index)
        page = self._doc[page_index]
        raw_blocks = page.get_text("blocks")
        blocks: list[TextBlockInfo] = []
        for b in raw_blocks:
            # b = (x0, y0, x1, y1, "text", block_no, block_type)
            if len(b) >= 7 and b[6] == 0:  # block_type == 0 indica texto
                text_clean = b[4].strip()
                if text_clean:
                    blocks.append(
                        TextBlockInfo(
                            block_no=int(b[5]),
                            bbox=(float(b[0]), float(b[1]), float(b[2]), float(b[3])),
                            text=text_clean,
                        )
                    )
        return blocks

    def search_text(self, page_index: int, query: str) -> list[tuple[float, float, float, float]]:
        """
        Busca um termo na página e retorna lista de retângulos (x0, y0, x1, y1)
        nas coordenadas reais da página.
        """
        self._ensure_valid_page(page_index)
        if not query or not query.strip():
            return []
        page = self._doc[page_index]
        rects = page.search_for(query.strip())
        return [(r.x0, r.y0, r.x1, r.y1) for r in rects]

    def _ensure_valid_page(self, page_index: int) -> None:
        if not self.is_open:
            raise RuntimeError("Nenhum documento PDF está aberto.")
        if page_index < 0 or page_index >= len(self._doc):
            raise IndexError(
                f"Índice de página inválido: {page_index}. Total de páginas: {len(self._doc)}"
            )

