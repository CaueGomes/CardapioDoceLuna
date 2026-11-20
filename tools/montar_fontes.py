"""Prepara as fontes do editor a partir das fontes DEMO + PDF original + Nunito.

As fontes Fontspring DEMO trazem um selo "DEMO" no lugar de quase toda a pontuacao
(e do digito 4) e nao tem acentos. Este script gera, em public/assets/:
  arg-<peso>.otf        DEMO sem os glifos-selo (kerning original preservado)
  arg-<peso>-extra.otf  glifos extras: $ - Ç reais (tirados do PDF original, so no Bold)
                        e letras acentuadas = letra AllRound + acento da Nunito.
Com as fontes licenciadas completas nada disso e necessario (ver README).
Uso: python tools/montar_fontes.py
"""
import io
import unicodedata
import pymupdf
from fontTools.ttLib import TTFont
from fontTools.cffLib import CFFFontSet
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

A = "public/assets/"
ACENTOS = "ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÑáàâãäéèêëíìîïóòôõöúùûüñ"


def contours(rec):
    """Divide uma gravacao de caminho em contornos."""
    out, cur = [], []
    for op, args in rec.value:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            out.append(cur); cur = []
    return out


def bounds(cs_list, gs=None):
    bp = BoundsPen(gs)
    for c in cs_list:
        for op, args in c: getattr(bp, op)(*args)
    return bp.bounds


def replay(cs_list, pen, dx=0, dy=0):
    tp = TransformPen(pen, (1, 0, 0, 1, dx, dy))
    for c in cs_list:
        for op, args in c: getattr(tp, op)(*args)


def rec_of(glyphset, name):
    r = DecomposingRecordingPen(glyphset); glyphset[name].draw(r); return contours(r)


def build(peso, nunito, pdf_xref):
    demo = TTFont(f"tools/fontes-demo/allround-{peso}.otf")
    gs = demo.getGlyphSet(); cmap = demo.getBestCmap(); hmtx = demo["hmtx"].metrics
    selo = demo["CFF "].cff[0].CharStrings[cmap[ord("!")]].bytecode

    # 1) remove do cmap todo glifo que e o selo "DEMO"
    ruins = {cp for cp, g in cmap.items() if demo["CFF "].cff[0].CharStrings[g].bytecode == selo}
    for t in demo["cmap"].tables:
        for cp in ruins: t.cmap.pop(cp, None)
    demo.save(f"{A}arg-{peso}.otf")
    print(peso, "glifos-selo removidos:", "".join(sorted(chr(c) for c in ruins)))

    # 2) fonte extra
    nf = TTFont(nunito); ngs = nf.getGlyphSet(); ncm = nf.getBestCmap(); glyf = nf["glyf"]
    xh, cap = demo["OS/2"].sxHeight, demo["OS/2"].sCapHeight
    nxh, ncap = nf["OS/2"].sxHeight, nf["OS/2"].sCapHeight
    glyphs, widths, cmap_out = {}, {}, {}

    def add(ch, width, draw):
        name = f"u{ord(ch):04X}"
        pen = T2CharStringPen(width, None); draw(pen)
        glyphs[name] = pen.getCharString(); widths[name] = width; cmap_out[ord(ch)] = name

    real = {}
    if pdf_xref:  # glifos verdadeiros da AllRound embutidos no PDF original
        _, _, _, data = pymupdf.open("tools/original.pdf").extract_font(pdf_xref)
        cff = CFFFontSet(); cff.decompile(io.BytesIO(data), None)
        pcs = cff[0].CharStrings
        for ch, g in (("$", "dollar"), ("-", "hyphen"), ("Ç", "Ccedilla")):
            r = RecordingPen(); pcs[g].draw(r); real[ch] = (contours(r), pcs[g].width)
            add(ch, pcs[g].width, lambda p, c=real[ch][0]: replay(c, p))

    # cedilha da Nunito (o Ç real da AllRound tem a cedilha fundida no C, nao da para separar)
    ced = rec_of(ngs, "cedilla")[0]

    def com_cedilha(ch, base):
        b = rec_of(gs, cmap[ord(base)]); bb = bounds(b); cb = bounds([ced])
        dx = (bb[0] + bb[2]) / 2 - (cb[0] + cb[2]) / 2
        add(ch, hmtx[cmap[ord(base)]][0], lambda p: (replay(b, p), replay([ced], p, dx, 0)))

    if "Ç" not in real: com_cedilha("Ç", "C")
    com_cedilha("ç", "c")

    for ch in ACENTOS:
        comp = glyf[ncm[ord(ch)]].components
        base = unicodedata.normalize("NFD", ch)[0]
        mark_name, mx, my = comp[1].glyphName, comp[1].x, comp[1].y
        nbase = comp[0].glyphName
        mark = rec_of(ngs, mark_name)
        # posicao do acento relativa ao centro da letra base na Nunito
        nb = bounds(rec_of(ngs, nbase)); mb = bounds(mark)
        rel = (mb[0] + mb[2]) / 2 + mx - (nb[0] + nb[2]) / 2
        b = rec_of(gs, cmap[ord(base)])
        if base == "i":  # i sem pingo: fica so o contorno mais baixo
            b = [min(b, key=lambda c: bounds([c])[1])]
        bb = bounds(b)
        dx = (bb[0] + bb[2]) / 2 + rel - (mb[0] + mb[2]) / 2
        dy = my + ((cap - ncap) if base.isupper() else (xh - nxh))
        add(ch, hmtx[cmap[ord(base)]][0], lambda p, b=b, m=mark, dx=dx, dy=dy: (replay(b, p), replay(m, p, dx, dy)))

    fb = FontBuilder(1000, isTTF=False)
    order = [".notdef"] + list(glyphs)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap_out)
    p = T2CharStringPen(500, None); glyphs[".notdef"] = p.getCharString(); widths[".notdef"] = 500
    fam = f"ARG {peso} extra"
    fb.setupCFF(fam.replace(" ", ""), {"FullName": fam}, glyphs, {})
    fb.setupHorizontalMetrics({g: (widths[g], bounds_lsb(glyphs[g])) for g in order})
    h = demo["hhea"]; o = demo["OS/2"]
    fb.setupHorizontalHeader(ascent=h.ascent, descent=h.descent)
    fb.setupNameTable({"familyName": fam, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=o.sTypoAscender, sTypoDescender=o.sTypoDescender, sTypoLineGap=o.sTypoLineGap,
                usWinAscent=o.usWinAscent, usWinDescent=o.usWinDescent, sxHeight=xh, sCapHeight=cap)
    fb.setupPost()
    fb.save(f"{A}arg-{peso}-extra.otf")
    print(peso, "extras:", "".join(chr(c) for c in cmap_out))


def bounds_lsb(cs):
    bp = BoundsPen(None); cs.draw(bp); return bp.bounds[0] if bp.bounds else 0


build("bold", f"tools/fontes-demo/nunito-900.woff", 10)
build("book", f"tools/fontes-demo/nunito-500.woff", None)
