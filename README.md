# ⚡ Cortex PDF Editor

Aplicação desktop moderna em Python (PyQt6 + PyMuPDF) para visualização, edição, conversão, compressão, junção e divisão de arquivos PDF.

## Princípios Fundamentais
- **Fluxo Direto:** `Entrada → Processamento → Saída`
- **Preservação Absoluta do Original:** O arquivo de entrada nunca é modificado ou sobrescrito. Um novo arquivo é sempre gerado.
- **Flexibilidade de Nomeação:** Em todas as operações geradoras de arquivos, o usuário pode optar por **manter o nome original** ou **definir um novo nome personalizado**.
- **Privacidade Total:** Nenhuma informação pessoal ou telemetria é coletada; todo o processamento ocorre 100% localmente.

---

## Funcionalidades Implementadas

1. **Visualizar Documentos PDF (`viewer_engine.py` / `viewer_tab.py`)**
   - Abertura rápida de documentos PDF.
   - Zoom-In (`+`), Zoom-Out (`-`), Reset (`100%`) e rotação de páginas (`90°`).
   - Navegação entre páginas.
   - Seleção de texto interativa arrastando o mouse sobre a área desejada da página (RubberBand) ou diretamente no painel lateral de texto extraído.
   - Cópia de trechos selecionados ou da página inteira para a área de transferência (*Clipboard*) e busca de termos com destaque visual na página.

2. **Editar Texto do PDF (`editor_engine.py` / `editor_tab.py`)**
   - Inspeção automática de editabilidade (detecta se o PDF possui camada de texto editável ou se é apenas imagem digitalizada/criptografado).
   - Listagem dos trechos de texto detectados por página para preenchimento rápido.
   - Substituição de textos preservando posição, tamanho aproximado da fonte e cor original, gerando um novo PDF.

3. **Converter PDF para Diversos Formatos (`converter_from_pdf.py` / `convert_from_pdf_tab.py`)**
   - Exportação mantendo fidelidade de formatação e estrutura para:
     - **Word (`.docx`)** via `pdf2docx` / `python-docx`
     - **HTML (`.html`)** preservando layout visual e posicionamento
     - **Markdown (`.md`)** estruturado com cabeçalhos e parágrafos
     - **Texto (`.txt`)** com ordenação de blocos de leitura
     - **Imagens (`.png`, `.jpg`)** com resolução (DPI) configurável

4. **Converter Outros Formatos para PDF (`converter_to_pdf.py` / `convert_to_pdf_tab.py`)**
   - Conversão direta para PDF a partir de:
     - Documentos Word (`.docx`) preservando títulos, estilos e tabelas
     - Imagens (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.tiff`)
     - Páginas Web (`.html`, `.htm`)
     - Texto e Markdown (`.txt`, `.md`)
     - Planilhas e Tabelas (`.xlsx`, `.csv`)

5. **Comprimir PDF (`compressor.py` / `compress_tab.py`)**
   - Três níveis de compressão (`Baixa`, `Média`, `Alta`) com limpeza estrutural (`garbage=4`), compressão Deflate de fluxos/fontes e reamostragem inteligente de imagens embutidas.

6. **Juntar Arquivos em um Único PDF (`merger.py` / `merge_tab.py`)**
   - Combinação de dois ou mais arquivos PDF na ordem definida pelo usuário em um novo PDF unificado.

7. **Dividir um Único PDF em Dois ou Mais PDFs (`splitter.py` / `split_tab.py`)**
   - Divisão em 2 arquivos após uma página específica, divisão por intervalos personalizados (ex: `1-2, 3-5`) ou divisão a cada `N` páginas.

---

## Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar a aplicação gráfica
```bash
python main.py
```

### 3. Executar a suíte de testes automatizados
```bash
pytest -v
```

