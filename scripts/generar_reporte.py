"""Genera el reporte HTML "Plan de Ventas 2026" a partir de los Excel de la carpeta Base PBI.

Uso simple (desde la raíz del repositorio):
    python scripts/generar_reporte.py "<carpeta con los Excel>" [--corte dd-mm-aaaa]
      -> escribe index.html en la raíz del repositorio (corte por defecto: fecha de hoy)

Uso completo (compatibilidad):
    python scripts/generar_reporte.py <carpeta_excel> <carpeta_maestros> <plantilla.html> <salida.html> [dd-mm-aaaa]

Replica la lógica del PBIX "Seguimiento - Plan de Ventas 2026-2027.pbix".
"""
import sys, os, json, warnings, datetime as dt
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import etl

def s(v):
    if v is None or (isinstance(v, float) and pd.isna(v)) or (not isinstance(v, str) and pd.isna(v)):
        return None
    return str(v).strip()

def n(v):
    try:
        f = float(v)
        return None if pd.isna(f) else f
    except Exception:
        return None

def fecha(v):
    """Sistred trae fechas como texto dd/mm/aa (o datetime). Devuelve dd-mm-aa como el PBI."""
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    if isinstance(v, (dt.date, dt.datetime, pd.Timestamp)):
        return pd.Timestamp(v).strftime("%d-%m-%y")
    try:
        return pd.to_datetime(str(v), dayfirst=True).strftime("%d-%m-%y")
    except Exception:
        return str(v)

def build(base, maestros, corte):
    d = etl.load(base, maestros)
    me, mr, mev = d["M_Etapas"], d["M_Regiones"], d["M_Etapa_Venta"]
    data = {
        "meta": {"corte": corte, "generado": dt.date.today().strftime("%d-%m-%Y")},
        "etapas": [{"e": r["Etapa"], "abrv": r["Etapa Abrv"], "macro": r["Etapa Macro"], "prog": r["Progreso Etapa"]} for _, r in me.iterrows()],
        "regiones": [{"cod": int(r["CodigoReg"]), "region": r["Region"], "key": r["Key"]} for _, r in mr.iterrows()],
        "etapaVenta": [{"act": r["Actividad_BD_SISTRED"], "etapa": r["Etapa"], "actividad": r["Actividad"], "cumpl": str(r["Cumplimiento"]),
                         "orden": int(r["Orden"]), "ordenEtapa": int(r["OrdenEtapas"])} for _, r in mev.iterrows()],
        "seg": [{"id": n(r["ID DBN"]), "inm": s(r["INMUEBLE (UC)"]), "reg": s(r["REGION"]), "exp": s(r["Expediente"]), "etapa": s(r["Etapa"])}
                for _, r in d["Seg Regional"].iterrows()],
        "segPA": [{"etapa": s(r["Etapa"]), "reg": s(r["REGION"])} for _, r in d["Seg Regional PA"].iterrows()],
        "web": [{"reg": s(r["Región"]), "valor": n(r["Valor comercial mínimo UF "])} for _, r in d["Web"].iterrows()],
        "vd": [{"exp": s(r["NRO_EXPEDIENTE"]), "reg": s(r["INMUEBLE1_REGION"]), "comuna": s(r["INMUEBLE1_COMUNA"]), "ubic": s(r["UBICACION"]),
                "estado": s(r["Sistred.ESTADO_SISTEMA"]), "act": s(r["Sistred.ACTIVIDAD"]), "fecha": fecha(r["Sistred.ETAPA1_FECHA_INICIO"]),
                "asig": s(r["Sistred.ASIGNADO"]), "precio": n(r["Precio UF"])} for _, r in d["Ventas Directas"].iterrows()],
        "vdpa": [{"exp": s(r["NRO_EXPEDIENTE"]), "act": s(r["Sistred PA.ACTIVIDAD"])} for _, r in d["Ventas Directas PA"].iterrows()],
        # Solo región, si tuvo oferta y monto: NO se embeben los nombres de oferentes
        "ofertas": [{"exp": s(r["N° Expediente PP"]), "reg": s(r["Región"]), "ofe": bool(r["con_oferta"]), "monto": n(r["Monto UF mayor oferta"])}
                    for _, r in d["Ofertas"].iterrows()],
        "vpp": [{"exp": s(r["N° Expte VPP"]), "etapa": s(r["Etapa"]), "region": s(r["Región"]), "prov": s(r["Provincia"]),
                 "ubic": s(r["Ubicación Inmueble"]), "estado": s(r["Estado"])} for _, r in d["VPP"].iterrows()],
    }
    return data

HERE = os.path.dirname(os.path.abspath(__file__))

def _args(argv):
    """Admite el uso simple (carpeta + --corte opcional) y el uso completo de 5 argumentos."""
    corte = dt.date.today().strftime("%d-%m-%Y")
    if "--corte" in argv:
        i = argv.index("--corte"); corte = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if len(argv) == 1:
        return argv[0], os.path.join(HERE, "maestros"), os.path.join(HERE, "plantilla.html"), os.path.join(HERE, "..", "index.html"), corte
    if len(argv) in (4, 5):
        return (*argv[:4], argv[4] if len(argv) == 5 else corte)
    sys.exit(__doc__)

if __name__ == "__main__":
    base, maestros, plantilla, salida, corte = _args(sys.argv[1:])
    if not os.path.isdir(base):
        sys.exit(f"No encuentro la carpeta de Excel: {base}")
    print(f"Leyendo Excel de {base} (puede tardar 1-2 minutos)...")
    data = build(base, maestros, corte)
    html = open(plantilla, encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/null", payload)
    open(salida, "w", encoding="utf-8").write(html)
    print("OK ->", os.path.normpath(salida), "| corte", corte, "|", {k: len(v) for k, v in data.items() if isinstance(v, list)})
