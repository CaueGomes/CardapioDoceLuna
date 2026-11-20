# Editor de Cardápio — Doce Luna

Site estático: abre o cardápio, clica no texto, edita, clica em **Exportar PDF**.

- `public/` — o site (é só isso que vai para o Render)
  - `index.html` — editor + exportação (pdf-lib, no próprio navegador)
  - `assets/fundo.pdf` — arte original vetorial, sem os textos editáveis e sem as estrelinhas
  - `assets/fundo.png` — a mesma arte em imagem, usada só na tela
  - `assets/arg-*.otf`, `assets/nunito-*.ttf` — fontes
- `tools/` — scripts para regerar os arquivos acima (não vão para o site)

## Publicar no Render

1. Suba esta pasta para um repositório no GitHub.
2. No Render: **New → Blueprint**, escolha o repositório (ele lê o `render.yaml`).
   Ou **New → Static Site**, Publish directory = `public`, Build command vazio.

## O PDF exportado

- Mesmo tamanho do original (A4, 595,276 × 841,89 pt), arte original vetorial em CMYK.
- Textos em vetor (fontes embutidas), nas cores CMYK originais.
- Sem nenhum elemento da interface.

## Fontes (importante)

As fontes enviadas são **Fontspring DEMO**: não têm acentos e trocam quase toda a pontuação
e o dígito **4** por um selo "DEMO". Para contornar, `tools/montar_fontes.py`:

- remove os glifos-selo;
- usa `$`, `-` e `Ç` reais da AllRound tirados do PDF original;
- monta as letras acentuadas com a letra da AllRound + o acento da Nunito;
- o que ainda faltar (`4`, `%`, `&`, `/`, `(` …) aparece em Nunito.

Com as fontes **licenciadas** (AllRoundGothic-Book, -BookOblique e -Bold completas), basta
substituir `public/assets/arg-book.otf` e `arg-bold.otf` pelas completas e apagar os
`arg-*-extra.otf` (e tirá-los de `FONTES` e do CSS em `index.html`). A licença precisa permitir uso na web.

## Se a arte mudar no Illustrator

```bash
pip install pymupdf fonttools
python tools/gerar_fundo.py tools/original.pdf
python tools/montar_fontes.py
```

Se textos mudarem de lugar, ajuste as coordenadas em `LAYOUT` no `index.html`
(o script `gerar_fundo.py` remove todo texto exceto o título "cardápio").
