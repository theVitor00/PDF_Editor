# Histórico Detalhado de Desenvolvimento — Cortex PDF Editor

Este documento funciona como um diário técnico detalhado de todas as solicitações, decisões arquiteturais, implementações e verificações realizadas no projeto **Cortex PDF Editor**.

---

## Resumo da Solicitação Original

- **Data de Solicitação:** 28/10/2026
- **Descrição do que foi pedido pelo usuário:**
  1. Criar uma aplicação em Python com interface gráfica moderna contendo as seguintes funcionalidades:
     - **Visualizar documentos PDF:** com ações básicas como zoom-in, zoom-out, seleção de texto, cópia, busca e navegação entre páginas.
     - **Editar o texto dos documentos PDF:** nos casos onde isso seja possível (documentos com camada de texto editável).
     - **Converter PDF para diversos formatos:** mantendo a fidelidade da formatação nos casos onde isso seja possível (`.docx`, `.html`, `.md`, `.txt`, `.png`, `.jpg`).
     - **Converter outros formatos para PDF:** suportando múltiplos formatos de entrada (`.docx`, `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.tiff`, `.html`, `.txt`, `.md`, `.csv`, `.xlsx`).
     - **Comprimir PDF:** reduzindo o seu tamanho total.
     - **Juntar dois (ou mais) arquivos em um único PDF.**
     - **Dividir um único arquivo em dois ou mais PDFs.**
  2. **Regra de Imutabilidade do Original:** Em todos os casos, o arquivo original não deve ser modificado. Um novo arquivo deve ser gerado, e o usuário deve poder escolher entre modificar o nome do arquivo gerado ou manter o mesmo nome.
  3. **Privacidade e Simplicidade:** Nenhuma informação precisa ser coletada e o processo deve seguir estritamente o fluxo simples: `Entrada → Processamento → Saída`.
  4. **Qualidade e Testes:** Garantir a existência de testes automatizados cobrindo todas as funcionalidades.
  5. **Controle de Versão:** Criar um repositório Git e realizar commit de todo o trabalho desenvolvido.
  6. **Documentação de Histórico:** Escrever este arquivo `historico.md` detalhando tudo o que foi realizado com data, hora, descrição do pedido e descrição técnica do que foi feito.

---

## Diário Cronológico de Alterações e Implementações

### Registro 01 — Diagnóstico do Ambiente e Instalação de Dependências
- **Data:** 28/10/2026
- **Hora:** 08:34 - 08:36 (BRT / UTC-03:00)
- **O que foi pedido:** Preparação da base tecnológica para suportar interface gráfica moderna, manipulação avançada de PDF e conversões de alta fidelidade.
- **O que foi feito:**
  - Verificação da versão do Python (`Python 3.13.5`) e pacotes instalados (`PyQt6`, `QtAwesome`, `python-docx`, `Pillow`, `reportlab`, `openpyxl`, `pytest`).
  - Instalação dos pacotes `pymupdf` (motor de renderização, edição, compressão e layout de PDFs) e `pdf2docx` (conversão estruturada de PDF para Word `.docx`).
  - Criação dos arquivos `.gitignore` e `requirements.txt`.

---

### Registro 02 — Implementação do Gerenciador de Saída Não-Destrutiva (`output_naming.py`)
- **Data:** 28/10/2026
- **Hora:** 08:37 (BRT / UTC-03:00)
- **O que foi pedido:** Garantir que em todos os casos o arquivo original jamais seja modificado, gerando sempre um novo arquivo e permitindo ao usuário escolher entre manter o nome original ou definir um nome personalizado.
- **O que foi feito:**
  - Implementação do módulo `cortex_pdf/core/output_naming.py` contendo as funções `resolve_output_path` e `resolve_multi_output_paths`.
  - Quando o usuário escolhe **manter o nome original** (`keep_original_name=True`):
    - Se a pasta de destino for diferente da pasta de origem, o novo arquivo mantém exatamente o mesmo nome do arquivo de entrada.
    - Se a pasta de destino for a mesma pasta do arquivo original (ou se já existir arquivo homônimo), o sistema adiciona automaticamente um sufixo seguro (`_novo`, `_editado`, `_comprimido`, `_unificado`, `_parte_01`, etc.) ou contador incremental para jamais sobrescrever o arquivo original.
  - Quando o usuário escolhe **modificar o nome** (`keep_original_name=False`), o sistema utiliza o `custom_name` informado pelo usuário, garantindo a extensão correta e protegendo contra colisões com o arquivo de entrada.

---

### Registro 03 — Implementação dos Motores Core de PDF (`cortex_pdf/core/`)
- **Data:** 28/10/2026
- **Hora:** 08:38 - 08:41 (BRT / UTC-03:00)
- **O que foi pedido:** Implementar os motores de processamento para todas as 7 funcionalidades exigidas seguindo o fluxo `Entrada → Processamento → Saída`.
- **O que foi feito:**
  1. **Visualização (`cortex_pdf/core/viewer_engine.py`):**
     - Criação da classe `PDFViewerEngine` com controle de zoom (`zoom_in`, `zoom_out`, `reset_zoom` entre `25%` e `400%`), rotação (`0°`, `90°`, `180°`, `270°`), renderização de página em PNG (`render_page`), extração de texto da página (`get_page_text`), extração de texto por área retangular selecionada com o mouse (`get_text_in_rect`) e busca de termos com coordenadas de destaque (`search_text`).
  2. **Edição de Texto (`cortex_pdf/core/editor_engine.py`):**
     - Criação das funções `inspect_pdf_editability`, `extract_editable_spans`, `replace_text_in_pdf` e `edit_pdf_by_operations`.
     - Verifica se o PDF possui camada de texto editável (identificando PDFs criptografados ou puramente digitalizados sem OCR).
     - Substitui textos localizados preservando posição da linha de base (*baseline*), tamanho aproximado da fonte e cor RGB através de anotação de redação limpa (preservando imagens) seguida da inserção do novo texto em um novo arquivo PDF.
  3. **Conversão de PDF para Outros Formatos (`cortex_pdf/core/converter_from_pdf.py`):**
     - Implementação de `convert_pdf_to_format` suportando:
       - `.docx` (via `pdf2docx` com fallback estruturado `python-docx`)
       - `.html` (via PyMuPDF HTML preservando posicionamento visual e fontes)
       - `.md` (Markdown estruturado com detecção de títulos por tamanho de fonte)
       - `.txt` (Texto puro ordenado por blocos de leitura)
       - `.png` e `.jpg` (Renderização das páginas em alta resolução com DPI configurável).
  4. **Conversão de Outros Formatos para PDF (`cortex_pdf/core/converter_to_pdf.py`):**
     - Implementação de `convert_to_pdf` suportando `.docx` (preservando títulos, negrito, itálico, sublinhado e tabelas), imagens (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.tiff`), páginas `.html`/`.htm`, arquivos `.txt`/`.md`, além de planilhas `.csv` e `.xlsx` renderizadas em tabelas PDF vetoriais via `pymupdf.Story` e `DocumentWriter`.
  5. **Compressão de PDF (`cortex_pdf/core/compressor.py`):**
     - Implementação de `compress_pdf` com três níveis (`low`, `medium`, `high`), realizando limpeza de objetos órfãos (`garbage=4`), compressão Deflate de streams/fontes/imagens, remoção de metadados redundantes (`scrub`) e recompressão/subamostragem de imagens embutidas (`rewrite_images`).
  6. **Junção de PDFs (`cortex_pdf/core/merger.py`):**
     - Implementação de `merge_pdfs` que combina 2 ou mais arquivos PDF na ordem escolhida em um único novo documento PDF.
  7. **Divisão de PDF (`cortex_pdf/core/splitter.py`):**
     - Implementação de `split_pdf_at_page` (divide 1 PDF em 2 arquivos após uma página escolhida), `split_pdf_by_ranges` (divide por intervalos como `1-2, 3-5`) e `split_pdf_every_n_pages` (divide a cada N páginas).

---

### Registro 04 — Construção da Interface Gráfica Moderna (`cortex_pdf/ui/` e `main.py`)
- **Data:** 28/10/2026
- **Hora:** 08:41 - 08:46 (BRT / UTC-03:00)
- **O que foi pedido:** Interface gráfica moderna em Python, sem coleta de informações, com fluxo simples `Entrada → Processamento → Saída` e escolha entre manter ou alterar o nome do arquivo de saída.
- **O que foi feito:**
  - Criação do tema visual moderno Dark Slate & Indigo em `cortex_pdf/ui/styles.py`.
  - Criação dos componentes padronizados em `cortex_pdf/ui/components.py`:
    - `PipelineBanner`: exibe claramente o fluxo `1. Entrada ➔ 2. Processamento ➔ 3. Saída` e o selo de zero coleta de dados.
    - `FileInputCard`: seletor de arquivo com suporte a *Drag and Drop* (arrastar e soltar).
    - `OutputNamingCard`: permite alternar entre *"Manter o nome original"* e *"Modificar o nome do novo arquivo gerado"*, além de escolher a pasta de destino.
    - `ResultStatusCard`: exibe o resultado detalhado e botão rápido para abrir o novo PDF gerado diretamente na aba do Visualizador.
  - Criação das 7 abas especializadas (`viewer_tab.py`, `editor_tab.py`, `convert_from_pdf_tab.py`, `convert_to_pdf_tab.py`, `compress_tab.py`, `merge_tab.py`, `split_tab.py`) e da janela principal `CortexMainWindow` (`main_window.py`) + ponto de entrada `main.py`.

---

### Registro 05 — Implementação e Execução de Testes Automatizados e Repositório Git
- **Data:** 28/10/2026
- **Hora:** 08:46 - 08:50 (BRT / UTC-03:00)
- **O que foi pedido:** Garantir testes para todas as funcionalidades e criar repositório Git com commit do trabalho realizado.
- **O que foi feito:**
  - Criação da suíte de testes em `tests/`:
    - `test_output_naming.py`: testa manutenção do nome original, nome customizado e proteção contra sobrescrita.
    - `test_viewer.py`: testa abertura, zoom-in, zoom-out, rotação, busca, seleção de texto por retângulo e extração.
    - `test_editor.py`: testa detecção de editabilidade, substituição de texto preservando o original intacto (verificado via hash SHA-256) e rejeição amigável de PDFs sem camada de texto.
    - `test_converter_from_pdf.py`: testa conversão de PDF para DOCX, HTML, Markdown, TXT, PNG e JPG.
    - `test_converter_to_pdf.py`: testa conversão de DOCX, PNG, TXT, MD, HTML, CSV e XLSX para PDF.
    - `test_compressor.py`: testa redução real de tamanho de arquivo PDF e preservação do arquivo original.
    - `test_merger.py`: testa junção de múltiplos PDFs e validação de número mínimo de arquivos.
    - `test_splitter.py`: testa divisão em dois arquivos por página de corte, divisão por intervalos e divisão por página.
    - `test_ui.py`: testa a interface gráfica `CortexMainWindow` e o fluxo completo `Entrada → Processamento → Saída` em todas as 7 abas.
  - Inicialização do repositório Git (`git init`) e realização do commit com todos os arquivos do projeto.
