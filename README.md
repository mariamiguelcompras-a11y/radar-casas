# Radar de casas

Página: https://mariamiguelcompras-a11y.github.io/radar-casas/

- `scraper/scrape.py` pesquisa o Imovirtual (T2 ou maior, até 360 000 €, Oeiras, Algés, Carcavelos, Cascais, Alcabideche, Alfragide e Sintra perto de Oeiras) e grava `data/imoveis.json`.
- `.github/workflows/radar.yml` corre a pesquisa de 2 em 2 dias (e à mão em Actions → "Pesquisa de casas" → Run workflow).
- `data/avaliacoes.json` guarda as avaliações, o contacto e as visitas feitas na página.
- Em cada pesquisa, todos os anúncios guardados são reabertos; os que já não existem passam a "Removido".
