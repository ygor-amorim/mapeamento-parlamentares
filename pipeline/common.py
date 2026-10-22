"""Utilitários compartilhados: download com retry, leitura de CSV do TSE e normalização de nomes e links."""
import csv
import io
import json
import re
import time
import urllib.request
import zipfile
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / ".cache"
USER_AGENT = "mapeamento-parlamentares/1.0 (+https://github.com)"


def http_get(url, accept=None, tries=4, timeout=120):
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
                return r.read()
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def get_json(url):
    return json.loads(http_get(url, accept="application/json"))


def download(url, name):
    """Baixa um arquivo para .cache/ (reaproveita se já existir)."""
    RAW_DIR.mkdir(exist_ok=True)
    path = RAW_DIR / name
    if not path.exists():
        path.write_bytes(http_get(url))
    return path


def read_tse_zip(path, suffix="_BRASIL.csv"):
    """Lê o CSV nacional de um zip do TSE (latin-1, separador ;)."""
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith(suffix))
        text = z.read(name).decode("latin-1")
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


TITLES = {"dr": "Dr", "dra": "Dra", "pr": "Pr", "pra": "Pra", "sgt": "Sgt", "sd": "Sd", "cb": "Cb", "ten": "Ten",
          "cel": "Cel", "cap": "Cap", "prof": "Prof", "profa": "Profa", "jr": "Jr", "sr": "Sr", "sra": "Sra",
          "pe": "Pe", "dj": "DJ", "mc": "MC", "st": "St", "dep": "Dep", "ver": "Ver"}
PARTICLES = {"da", "de", "do", "das", "dos", "e", "di", "du", "del", "della", "van", "von", "la", "le"}
ROMAN = {"ii", "iii", "iv", "vi", "vii", "viii", "ix", "xi", "xii"}


def smart_title(s):
    """'DR. JOÃO DA SILVA II' -> 'Dr. João da Silva II'."""
    out = []
    for i, w in enumerate((s or "").lower().split()):
        core = w.strip(".,")
        if i > 0 and w in PARTICLES:
            out.append(w)
        elif core in TITLES:
            out.append(w.replace(core, TITLES[core], 1))
        elif core in ROMAN:
            out.append(w.upper())
        elif core.isalpha() and len(core) <= 4 and not re.search(r"[aeiouyáéíóúâêôãõà]", core):
            out.append(w.upper())  # siglas sem vogal
        else:
            parts = re.split(r"([-'’])", w)
            out.append("".join(p[:1].upper() + p[1:] if p not in "-'’" else p for p in parts))
    return " ".join(out)


PLATFORMS = [
    ("instagram", ["instagram.com", "instagr.am"]),
    ("x", ["twitter.com", "://x.com", "www.x.com"]),
    ("facebook", ["facebook.com", "fb.com", "fb.me", "fb.watch"]),
    ("tiktok", ["tiktok.com"]),
    ("youtube", ["youtube.com", "youtu.be"]),
    # links que expõem telefone ou convite de grupo privado: descartados de propósito
    ("privado", ["wa.me/", "chat.whatsapp.com", "api.whatsapp.com/send", "whatsapp.com/send"]),
]


def platform(url):
    low = url.lower()
    for key, patterns in PLATFORMS:
        if any(p in low for p in patterns):
            return key
    return "outros"


def normalize_url(url, plat):
    u = url.strip().strip('"').replace(" ", "")
    if not u:
        return ""
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u.lstrip("/")
    m = re.match(r"^(https?://)([^/?#]+)(.*)$", u, re.I)
    if not m:
        return u
    scheme, host, rest = m.group(1).lower(), m.group(2).lower(), m.group(3)
    # o TSE grava muitos links em maiúsculas; IDs de canal do YouTube são sensíveis a caixa
    if u == u.upper() and not (plat == "youtube" and "/CHANNEL/" in rest.upper()):
        rest = rest.lower()
    if plat in ("instagram", "tiktok", "x") or (plat == "facebook" and "profile.php" not in rest.lower()):
        rest = re.split(r"[?#]", rest)[0]  # remove rastreadores (?igsh=, ?hl=...)
    return scheme + host + rest
