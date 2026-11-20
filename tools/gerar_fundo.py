"""Gera assets/fundo.pdf e assets/fundo.png a partir da arte original.
Remove apenas os textos editaveis e os marcadores (o titulo 'cardapio' e o logo ficam).
Uso: python tools/gerar_fundo.py tools/original.pdf"""
import re, sys, pymupdf

src = sys.argv[1] if len(sys.argv) > 1 else "tools/original.pdf"
doc = pymupdf.open(src)
page = doc[0]
page.clean_contents()  # junta streams em um so
xref = page.get_contents()[0]
c = doc.xref_stream(xref).decode("latin1")

# 1) textos: remove operadores Tj/TJ, exceto o titulo "card\341pio"
def drop(m):
    return m.group(0) if "card" in m.group(0) else ""
c, n_txt = re.subn(r"\((?:\.|[^\)])*\)\s*Tj|\[(?:\((?:\.|[^\)])*\)|[^\]])*\]\s*TJ", drop, c)

# 2) marcadores: blocos q..Q com o caminho da estrelinha
bullet = r"q 1 0 0 1 [\d.]+ [\d.]+ cm (?:[\d.]+ [\d.]+ [\d.]+ [\d.]+ k )?0 0 m \.437 -1\.579 1\.321 -3\.698.*? f Q"
m = re.search(bullet, c, re.S)
path = m.group(0) if m else None
c, n_bul = re.subn(bullet, "", c, flags=re.S)

doc.update_stream(xref, c.encode("latin1"))
print("textos removidos:", n_txt, "| marcadores removidos:", n_bul)
assert n_bul == 18, n_bul
left = [s["text"] for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"] if s["text"].strip()]
print("texto restante:", left)

doc.save("public/assets/fundo.pdf", garbage=3, deflate=True)
pymupdf.open("public/assets/fundo.pdf")[0].get_pixmap(dpi=216).save("public/assets/fundo.png")
if path:
    print("CAMINHO_MARCADOR:\n" + path)
