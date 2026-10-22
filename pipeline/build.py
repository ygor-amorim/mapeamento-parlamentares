"""Gera data/parlamentares.csv e data/frentes_camara.csv.

Uso: python -m pipeline.build
"""
import csv
import datetime
import json
import re
from pathlib import Path

from . import camara, tse

DATA = Path(__file__).resolve().parent.parent / "data"
ORDEM_CASA = {"Senado Federal": 0, "Câmara dos Deputados": 1, "Assembleia Legislativa": 2, "Câmara Legislativa do DF": 2}
CASA_CURTA = {"Câmara dos Deputados": "Câmara", "Senado Federal": "Senado",
              "Assembleia Legislativa": "ALE", "Câmara Legislativa do DF": "CLDF"}

# Rótulos temáticos a partir dos títulos das frentes. Sinal fraco: cada deputado assina ~200 frentes.
SINAIS = [
    ("Saúde mental", r"sa[úu]de mental"), ("SUS", r"\bSUS\b|Sistema [ÚU]nico de Sa[úu]de"),
    ("Educação pública", r"Escola P[úu]blica|Plano Nacional de Educa|Institutos Federais|Mista da Educa[çc][ãa]o$|Investimentos Federais na Educa"),
    ("Conselhos tutelares", r"Conselhos Tutelares"), ("Direitos humanos", r"Direitos Humanos"), ("LGBTI+", r"LGBT"),
    ("Trabalho", r"Trabalhadores por Aplicativo|Trabalho, Emprego e Renda|Economia Informal"), ("Tarifa zero", r"Tarifa Zero"),
    ("Cidadania digital", r"Economia e Cidadania Digitais"), ("Ciência e tecnologia", r"Ci[êe]ncia, Tecnologia|FINEP"),
    ("Meio ambiente", r"Ambientalista|Transi[çc][ãa]o Clim[áa]tica"), ("Moradia", r"Habita[çc][ãa]o"),
    ("Evangélica", r"Evang[ée]lica"), ("Católica", r"Cat[óo]lica"),
    ("Segurança pública", r"^Frente Parlamentar da Seguran[çc]a P[úu]blica$"), ("Agropecuária (FPA)", r"Agropecu[áa]ria - FPA"),
    ("Livre mercado", r"Livre Mercado"), ("Educação sem doutrinação", r"Sem Doutrina[çc][ãa]o"),
]

COLUNAS = ["chave", "casa", "uf", "nome_urna", "nome_civil", "nome_social", "partido", "federacao", "numero",
           "situacao_tse", "eleito_2022_mesmo_cargo", "eleito_2022_outro_cargo", "em_exercicio_camara_hoje",
           "ocupacao_declarada", "email_gabinete", "telefone_gabinete", "pagina_camara",
           "instagram", "x_twitter", "facebook", "tiktok", "youtube", "outros_links",
           "sinais_frentes", "n_frentes", "camara_id", "sq_candidato_tse"]


def main():
    DATA.mkdir(exist_ok=True)
    rows = tse.eleitos()
    deputados = camara.em_exercicio()
    frentes_long = []
    for r in rows:
        info = deputados.get(r.pop("_cpf")) if r["casa"] == "Câmara dos Deputados" else None
        r["em_exercicio_camara_hoje"] = ("Sim" if info else "Não") if r["casa"] == "Câmara dos Deputados" else ""
        info = info or {}
        for k in ("camara_id", "email_gabinete", "telefone_gabinete", "pagina_camara"):
            r[k] = info.get(k, "")
        frentes = info.get("frentes", [])
        r["sinais_frentes"] = "; ".join(lab for lab, rx in SINAIS if any(re.search(rx, f, re.I) for f in frentes))
        r["n_frentes"] = str(len(frentes)) if info else ""
        r["chave"] = f"{r['uf']} · {CASA_CURTA[r['casa']]} · {r['nome_urna']} ({r['partido']})"
        r["_frentes"] = frentes

    # chave única e legível (usada como identificador na planilha)
    vistos = {}
    for r in rows:
        vistos[r["chave"]] = vistos.get(r["chave"], 0) + 1
    dup = {k for k, n in vistos.items() if n > 1}
    cont = {}
    for r in rows:
        if r["chave"] in dup:
            cont[r["chave"]] = cont.get(r["chave"], 0) + 1
            r["chave"] += f" #{cont[r['chave']]}"

    rows.sort(key=lambda r: (r["uf"], ORDEM_CASA[r["casa"]], r["nome_urna"]))
    with open(DATA / "parlamentares.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(DATA / "frentes_camara.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["chave", "camara_id", "nome_urna", "partido", "uf", "frente"])
        for r in rows:
            for fr in r["_frentes"]:
                w.writerow([r["chave"], r["camara_id"], r["nome_urna"], r["partido"], r["uf"], fr])

    resumo = {
        "gerado_em": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "total": len(rows),
        "por_casa": {c: sum(1 for r in rows if r["casa"] == c) for c in ORDEM_CASA},
        "federais_em_exercicio": sum(1 for r in rows if r["em_exercicio_camara_hoje"] == "Sim"),
    }
    (DATA / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
