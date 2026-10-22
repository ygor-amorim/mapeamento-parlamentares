"""Deputados federais em exercício (API de Dados Abertos da Câmara): gabinete e frentes parlamentares."""
import concurrent.futures

from .common import get_json

API = "https://dadosabertos.camara.leg.br/api/v2"


def _paginado(url):
    while url:
        d = get_json(url)
        yield from d["dados"]
        url = next((l["href"] for l in d["links"] if l["rel"] == "next"), None)


def em_exercicio(workers=8):
    """Retorna {cpf: {id, email, telefone, pagina, frentes}} dos deputados em exercício hoje."""
    lista = list(_paginado(f"{API}/deputados?itens=100&ordem=ASC&ordenarPor=nome"))

    def detalhe(dep):
        d = get_json(f"{API}/deputados/{dep['id']}")["dados"]
        frentes = sorted({f["titulo"] for f in _paginado(f"{API}/deputados/{dep['id']}/frentes")})
        gab = d["ultimoStatus"].get("gabinete") or {}
        tel = gab.get("telefone") or ""
        return d.get("cpf"), {
            "camara_id": str(d["id"]),
            "email_gabinete": gab.get("email") or d["ultimoStatus"].get("email") or "",
            "telefone_gabinete": f"(61) {tel}" if tel and not tel.startswith("(") else tel,
            "pagina_camara": f"https://www.camara.leg.br/deputados/{d['id']}",
            "frentes": frentes,
        }

    with concurrent.futures.ThreadPoolExecutor(workers) as ex:
        return {cpf: info for cpf, info in ex.map(detalhe, lista) if cpf}
