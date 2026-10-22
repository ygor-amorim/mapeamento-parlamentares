# Mapeamento de parlamentares · legislatura 2027–2031

Base aberta com os parlamentares eleitos em 4 de outubro de 2026, construída a partir de dados públicos do TSE e da Câmara dos Deputados, para apoiar o mapeamento de gabinetes abertos ao diálogo por tema.

| Casa | Eleitos |
|---|---|
| Câmara dos Deputados | 513 |
| Assembleias Legislativas | 1.035 |
| Câmara Legislativa do DF | 24 |
| Senado Federal | 52 |

## Arquivos

- `data/parlamentares.csv` — um parlamentar por linha (UTF-8, separador vírgula).
- `data/frentes_camara.csv` — formato longo: uma linha por deputado federal em exercício × frente parlamentar assinada (legislatura 2023–2026).
- `data/resumo.json` — contagens e data da última geração.

### Colunas de `parlamentares.csv`

| Coluna | O que é |
|---|---|
| `chave` | Identificador legível e único: `UF · Casa · Nome de urna (PARTIDO)`. É a chave usada na planilha de trabalho. |
| `casa`, `uf`, `partido`, `federacao`, `numero` | Como registrados no TSE. |
| `nome_urna`, `nome_civil`, `nome_social` | Normalizados de maiúsculas para caixa de título. |
| `situacao_tse` | `Eleito (QP)`, `Eleito (média)` ou `Eleito` (Senado). |
| `eleito_2022_mesmo_cargo` | Se a mesma pessoa foi eleita para o mesmo cargo e UF em 2022. Aproximação de "reeleito". |
| `eleito_2022_outro_cargo` | Outro cargo para o qual foi eleita em 2022, se houver. |
| `em_exercicio_camara_hoje` | Só federais: se está em exercício na Câmara na data da geração. |
| `email_gabinete`, `telefone_gabinete`, `pagina_camara`, `camara_id` | Só federais em exercício. |
| `instagram` … `outros_links` | Redes declaradas ao TSE; múltiplos links separados por ` \| `. |
| `sinais_frentes`, `n_frentes` | Rótulos temáticos derivados das frentes assinadas. **Sinal fraco**: cada deputado assina em média ~210 frentes. |
| `sq_candidato_tse` | Identificador do candidato no TSE, para rastrear a origem. |

## Como rodar

Só biblioteca padrão do Python (3.10+), sem dependências:

```bash
python -m pipeline.build
```

Os arquivos brutos ficam em `.cache/` (ignorado pelo git). Uma GitHub Action (`.github/workflows/atualizar.yml`) roda o pipeline todo dia 1º e commita se os dados mudarem; também dá para disparar manualmente na aba Actions.

### Usar na planilha (Google Sheets)

Na aba de parlamentares da planilha de trabalho:

```
=IMPORTDATA("https://raw.githubusercontent.com/ygor-amorim/mapeamento-parlamentares/main/data/parlamentares.csv")
```

As avaliações, interações e contatos ficam **só na planilha**, nunca neste repositório.

## O que fica de fora, de propósito

- CPF, título de eleitor e data de nascimento. O CPF é usado apenas em memória para cruzar 2026 com 2022 e com a Câmara.
- E-mail e telefone de campanha, links `wa.me` e convites de grupos de WhatsApp, que o TSE também publica.
- Qualquer avaliação sobre parlamentares. Este repositório é só a camada de dados públicos.

## Limitações conhecidas

- `eleito_2022_mesmo_cargo` não identifica suplentes que assumiram mandato; o campo de reeleição do TSE veio vazio em 2026.
- Contato oficial de gabinete só existe para federais em exercício. Os gabinetes novos abrem com a posse, em fevereiro de 2027.
- Senado: só os eleitos em 2026. O arquivo do TSE está sem totalização para o Senado na Paraíba; os eleitos em 2022 (mandato até 2031) não estão na base.
- Vereadores (eleitos em 2024) não estão na base.
- Links de redes estão como declarados pelos candidatos; o TSE grava muitos em maiúsculas e a normalização pode deixar alguns quebrados.

## Fontes

- TSE, Portal de Dados Abertos: `consulta_cand_2026`, `rede_social_candidato_2026`, `consulta_cand_2022` (cdn.tse.jus.br/estatistica/sead/odsele).
- Câmara dos Deputados, API de Dados Abertos: dadosabertos.camara.leg.br/api/v2.

## Contribuindo

Ideias de próximas fontes: votações nominais selecionadas, vereadores eleitos em 2024, senadores eleitos em 2022, Assembleias Legislativas com API própria. Abra uma issue antes de mandar o PR.
