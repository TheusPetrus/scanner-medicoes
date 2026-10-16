# Scanner de imagens de medições de engenharia

Protótipo em Python que lê fotos de medições, extrai com OCR o texto impresso nelas
(coordenadas, data, horário e nome de quem fotografou) e preenche uma planilha do Excel.

## Como funciona

1. **Pré-processamento (Pillow):** corrige a rotação, converte para tons de cinza, aumenta o contraste e amplia fotos pequenas.
2. **OCR (Tesseract):** transforma a imagem em texto.
3. **Extração (expressões regulares):** encontra latitude/longitude, data, horário e nome. Coordenadas fora do intervalo válido são descartadas.
4. **Planilha (pandas + openpyxl):** gera `medicoes.xlsx` com uma linha por foto. Linhas com algum campo não encontrado recebem `revisar = SIM`, para conferência humana.

## Instalação

1. Instale o [Tesseract](https://github.com/tesseract-ocr/tesseract) (no Windows, use o instalador da UB Mannheim e marque o idioma Português; no Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-por`).
2. No Windows, se o comando `tesseract` não for encontrado, adicione no topo do `scanner.py`:
   `pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"`
3. `pip install -r requirements.txt`

## Uso

```
python scanner.py                       # lê a pasta imagens/ e gera medicoes.xlsx
python scanner.py outra_pasta saida.xlsx
```

## Testes

```
python -m unittest -v
```

## Ajustando ao seu formato de foto

Os padrões de extração estão no começo do `scanner.py` (`RE_LAT_LON_ROTULO`, `RE_DATA`, `RE_HORA`, `RE_NOME`).
Se os rótulos das suas fotos forem diferentes (por exemplo "Autor:" ou "Resp."), basta incluí-los nesses padrões.

## Próximos passos

- Recortar só a região da foto onde fica o texto, para ler com mais precisão.
- Aceitar coordenadas em graus, minutos e segundos.
- Interface simples para conferir as linhas marcadas como `revisar`.
