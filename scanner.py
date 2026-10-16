"""Scanner de imagens de medições de engenharia.

Lê as imagens de uma pasta, usa OCR (Tesseract) para ler o texto impresso na
foto (coordenadas, data, horário e nome de quem fotografou) e grava tudo em
uma planilha do Excel com pandas.

Uso:
    python scanner.py                      # lê ./imagens e gera medicoes.xlsx
    python scanner.py minha_pasta saida.xlsx
"""
import re
import sys
from pathlib import Path

import pandas as pd
import pytesseract
from PIL import Image, ImageOps

EXTENSOES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
def _escolher_idioma():
    """Usa português + inglês se o Tesseract tiver o pacote 'por'; senão, só inglês."""
    try:
        instalados = pytesseract.get_languages(config="")
    except Exception:
        return "eng"
    return "por+eng" if "por" in instalados else "eng"


IDIOMA_OCR = _escolher_idioma()

# ---------- Padrões de extração (ajuste ao formato das suas fotos) ----------
NUMERO = r"-?\d{1,3}[.,]\d{3,8}"
RE_LAT_LON_ROTULO = re.compile(
    rf"lat(?:itude)?\.?\s*[:=]?\s*(?P<lat>{NUMERO}).{{0,20}}?"
    rf"lon(?:g|gitude)?\.?\s*[:=]?\s*(?P<lon>{NUMERO})",
    re.IGNORECASE | re.DOTALL,
)
RE_LAT_LON_PAR = re.compile(rf"(?P<lat>{NUMERO})\s*[,;/ ]\s*(?P<lon>{NUMERO})")
RE_DATA = re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})\b")
RE_HORA = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?\b")
RE_NOME = re.compile(
    r"(?:nome|autor|fot.?grafo|respons.?vel|operador|por)\s*[:\-]\s*"
    r"(?P<nome>[A-Za-zÀ-ÿ'. ]{3,60})",
    re.IGNORECASE,
)
COLUNAS = ["arquivo", "latitude", "longitude", "data", "horario", "nome", "revisar"]


def _para_float(texto):
    return float(texto.replace(",", "."))


def extrair_campos(texto):
    """Recebe o texto lido pelo OCR e devolve um dicionário com os campos."""
    campos = {"latitude": None, "longitude": None, "data": None, "horario": None, "nome": None}

    achado = RE_LAT_LON_ROTULO.search(texto) or RE_LAT_LON_PAR.search(texto)
    if achado:
        lat, lon = _para_float(achado["lat"]), _para_float(achado["lon"])
        if -90 <= lat <= 90 and -180 <= lon <= 180:  # descarta leituras absurdas
            campos["latitude"], campos["longitude"] = lat, lon

    if (m := RE_DATA.search(texto)):
        campos["data"] = m.group(1).replace("-", "/")  # padroniza 15-10-2026 -> 15/10/2026

    if (m := RE_HORA.search(texto)):
        h, mi, s = m.group(1), m.group(2), m.group(3) or "00"
        campos["horario"] = f"{int(h):02d}:{mi}:{s}"

    if (m := RE_NOME.search(texto)):
        # Fica só com a primeira linha, pois o OCR pode juntar linhas seguintes.
        campos["nome"] = " ".join(m["nome"].splitlines()[0].split()).title()

    return campos


def preparar_imagem(caminho):
    """Pré-processamento que costuma melhorar muito a leitura do Tesseract."""
    img = Image.open(caminho)
    img = ImageOps.exif_transpose(img).convert("L")  # corrige rotação e vai p/ cinza
    img = ImageOps.autocontrast(img)
    if img.width < 1500:  # amplia fotos pequenas
        fator = 1500 / img.width
        img = img.resize((int(img.width * fator), int(img.height * fator)), Image.LANCZOS)
    return img


def ler_texto(caminho):
    return pytesseract.image_to_string(
        preparar_imagem(caminho), lang=IDIOMA_OCR, config="--psm 6"
    )


def processar_pasta(pasta):
    """Percorre as imagens da pasta e devolve um DataFrame com uma linha por foto."""
    linhas = []
    for caminho in sorted(Path(pasta).iterdir()):
        if caminho.suffix.lower() not in EXTENSOES:
            continue
        try:
            campos = extrair_campos(ler_texto(caminho))
        except Exception as erro:  # uma foto ruim não pode parar o lote
            print(f"[erro] {caminho.name}: {erro}")
            campos = {}
        linha = {"arquivo": caminho.name, **campos}
        # Marca para conferência humana quando algum campo não foi encontrado.
        linha["revisar"] = "SIM" if any(linha.get(c) is None for c in COLUNAS[1:6]) else "NÃO"
        linhas.append(linha)
    return pd.DataFrame(linhas, columns=COLUNAS)


def salvar_excel(df, destino):
    with pd.ExcelWriter(destino, engine="openpyxl") as escritor:
        df.to_excel(escritor, index=False, sheet_name="Medições")
        aba = escritor.sheets["Medições"]
        for coluna in aba.columns:  # largura automática das colunas
            tamanho = max(len(str(c.value or "")) for c in coluna)
            aba.column_dimensions[coluna[0].column_letter].width = tamanho + 3


def main():
    pasta = sys.argv[1] if len(sys.argv) > 1 else "imagens"
    destino = sys.argv[2] if len(sys.argv) > 2 else "medicoes.xlsx"
    df = processar_pasta(pasta)
    if df.empty:
        print(f"Nenhuma imagem encontrada em '{pasta}'.")
        return
    salvar_excel(df, destino)
    pendentes = (df["revisar"] == "SIM").sum()
    print(f"{len(df)} imagem(ns) processada(s) -> {destino} ({pendentes} para revisar)")


if __name__ == "__main__":
    main()
