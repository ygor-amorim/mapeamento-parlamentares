"""Eleitos em 2026 a partir dos dados abertos do TSE, com cruzamento contra os eleitos de 2022."""
import collections

from .common import download, normalize_url, platform, read_tse_zip, smart_title

BASE = "https://cdn.tse.jus.br/estatistica/sead/odsele"
CASAS = {
    "DEPUTADO FEDERAL": "Câmara dos Deputados",
    "DEPUTADO ESTADUAL": "Assembleia Legislativa",
    "DEPUTADO DISTRITAL": "Câmara Legislativa do DF",
    "SENADOR": "Senado Federal",
}
ELEITO = {"ELEITO POR QP": "Eleito (QP)", "ELEITO POR MÉDIA": "Eleito (média)", "ELEITO": "Eleito"}
NULOS = {"#NULO", "#NE", ""}


def eleitos(ano=2026, ano_anterior=2022):
    cand = read_tse_zip(download(f"{BASE}/consulta_cand/consulta_cand_{ano}.zip", f"consulta_cand_{ano}.zip"))
    redes_rows = read_tse_zip(download(f"{BASE}/consulta_cand/rede_social_candidato_{ano}.zip",
                                       f"rede_social_candidato_{ano}.zip"))
    anterior = read_tse_zip(download(f"{BASE}/consulta_cand/consulta_cand_{ano_anterior}.zip",
                                     f"consulta_cand_{ano_anterior}.zip"))

    redes = collections.defaultdict(list)
    for r in redes_rows:
        redes[r["SQ_CANDIDATO"]].append((int(r["NR_ORDEM_REDE_SOCIAL"] or 0), r["DS_URL"]))

    # quem foi eleito na eleição anterior, por CPF (o CPF nunca sai deste módulo)
    eleitos_antes = collections.defaultdict(list)
    for r in anterior:
        if r["DS_SIT_TOT_TURNO"] in ELEITO and r["NR_CPF_CANDIDATO"].isdigit():
            eleitos_antes[r["NR_CPF_CANDIDATO"]].append((r["DS_CARGO"], r["SG_UF"]))

    out = []
    for r in cand:
        cargo, sit = r["DS_CARGO"], r["DS_SIT_TOT_TURNO"]
        if cargo not in CASAS or sit not in ELEITO:
            continue
        if cargo == "SENADOR" and sit != "ELEITO":
            continue
        if cargo != "SENADOR" and sit == "ELEITO":
            continue
        links = collections.defaultdict(list)
        for _, url in sorted(redes.get(r["SQ_CANDIDATO"], [])):
            plat = platform(url)
            if plat == "privado":
                continue
            nu = normalize_url(url, plat)
            if nu and nu not in links[plat]:
                links[plat].append(nu)
        cpf = r["NR_CPF_CANDIDATO"]
        antes = eleitos_antes.get(cpf, [])
        mesmo = any(c == cargo and uf == r["SG_UF"] for c, uf in antes)
        outro = [f"{smart_title(c)} ({uf})" for c, uf in antes if not (c == cargo and uf == r["SG_UF"])]
        out.append({
            "casa": CASAS[cargo],
            "uf": r["SG_UF"],
            "nome_urna": smart_title(r["NM_URNA_CANDIDATO"]),
            "nome_civil": smart_title(r["NM_CANDIDATO"]),
            "nome_social": "" if r["NM_SOCIAL_CANDIDATO"] in NULOS else smart_title(r["NM_SOCIAL_CANDIDATO"]),
            "partido": r["SG_PARTIDO"],
            "federacao": "" if r["SG_FEDERACAO"] in NULOS else r["SG_FEDERACAO"],
            "numero": r["NR_CANDIDATO"],
            "situacao_tse": ELEITO[sit],
            f"eleito_{ano_anterior}_mesmo_cargo": "Sim" if mesmo else "Não",
            f"eleito_{ano_anterior}_outro_cargo": "; ".join(outro),
            "ocupacao_declarada": r["DS_OCUPACAO"].strip().capitalize(),
            "instagram": " | ".join(links["instagram"]),
            "x_twitter": " | ".join(links["x"]),
            "facebook": " | ".join(links["facebook"]),
            "tiktok": " | ".join(links["tiktok"]),
            "youtube": " | ".join(links["youtube"]),
            "outros_links": " | ".join(links["outros"]),
            "sq_candidato_tse": r["SQ_CANDIDATO"],
            "_cpf": cpf,  # só para cruzamento em memória; removido antes de gravar
        })
    return out
