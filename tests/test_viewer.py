"""
Testes para o motor de visualização de PDF (`viewer_engine.py`).
Cobre: abertura, contagem de páginas, zoom-in, zoom-out, reset de zoom,
rotação, extração de texto, seleção de texto por retângulo e busca.
"""

from pathlib import Path
from cortex_pdf.core.viewer_engine import PDFViewerEngine
from tests.conftest import file_sha256


def test_viewer_open_zoom_and_render(sample_pdf: Path):
    before_hash = file_sha256(sample_pdf)

    viewer = PDFViewerEngine(sample_pdf)
    assert viewer.is_open
    assert viewer.page_count == 3
    assert viewer.zoom == 1.0

    # Renderização em 100%
    r1 = viewer.render_page(0)
    assert r1.width > 0 and r1.height > 0
    assert r1.png_bytes.startswith(b"\x89PNG")

    # Zoom-in
    new_z = viewer.zoom_in(0.5)
    assert new_z == 1.5
    r_zoom_in = viewer.render_page(0)
    assert r_zoom_in.width > r1.width
    assert r_zoom_in.height > r1.height

    # Zoom-out
    z_out = viewer.zoom_out(0.75)
    assert z_out == 0.75
    r_zoom_out = viewer.render_page(0)
    assert r_zoom_out.width < r1.width

    # Reset zoom
    assert viewer.reset_zoom() == 1.0

    # Rotação
    viewer.rotation = 90
    r_rot = viewer.render_page(0)
    assert r_rot.width == r1.height
    assert r_rot.height == r1.width

    viewer.close()
    assert not viewer.is_open
    assert file_sha256(sample_pdf) == before_hash


def test_viewer_text_extraction_selection_and_search(sample_pdf: Path):
    viewer = PDFViewerEngine(sample_pdf)

    # Texto da página 1
    p1_text = viewer.get_page_text(0)
    assert "Titulo Principal Cortex PDF" in p1_text
    assert "Valor Antigo: 1000" in p1_text

    # Texto completo
    all_text = viewer.get_all_text()
    assert "Segunda Pagina do Relatorio" in all_text
    assert "Terceira Pagina Final" in all_text

    # Blocos de texto
    blocks = viewer.get_text_blocks(0)
    assert len(blocks) >= 2
    assert any("Titulo Principal" in b.text for b in blocks)

    # Busca de texto e seleção por retângulo (simulando seleção de mouse)
    found_rects = viewer.search_text(0, "Titulo Principal")
    assert len(found_rects) == 1
    rect = found_rects[0]

    selected_text = viewer.get_text_in_rect(
        0,
        (rect[0] - 2, rect[1] - 2, rect[2] + 2, rect[3] + 2),
        from_zoomed_coords=False,
    )
    assert "Titulo Principal" in selected_text

    viewer.close()
