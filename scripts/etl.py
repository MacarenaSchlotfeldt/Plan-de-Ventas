"""ETL Plan de Ventas 2026: replica las consultas Power Query del PBIX a partir de los Excel.
Uso: python etl.py <carpeta_base_pbi> <carpeta_maestros_json>  -> devuelve dict de DataFrames
"""
import sys, os, json
import pandas as pd

def _xl(path, sheet, header=0):
    return pd.read_excel(path, sheet_name=sheet, header=header, dtype=object)

def _txt(s):
    return s.map(lambda v: None if pd.isna(v) else (str(int(v)) if isinstance(v, float) and v.is_integer() else str(v)))

def load(base, maestros):
    f = lambda n: os.path.join(base, n)
    out = {}
    # --- Maestros (embebidos en el PBIX / Maestro_Etapas.xlsx externo)
    for t in ("M_Etapas", "M_Regiones", "M_Etapa_Venta"):
        out[t] = pd.read_json(os.path.join(maestros, f"{t}.json"), dtype=False)

    # --- Seg Regional / Seg Regional PA: hoja Consolidado, doble encabezado
    def seg(fn):
        df = _xl(f(fn), "Consolidado", header=1)
        df = df[df["CARTERA CE"] == "Si"].copy()
        df["Etapa"] = df["Etapa"].astype(str).str.replace("0. No iniciado", "1.1 Verificar carácter del inmueble", regex=False)
        df["IDUC"] = pd.to_numeric(df["IDUC"], errors="coerce")
        df["ID DBN"] = pd.to_numeric(df["ID DBN"], errors="coerce")
        return df
    out["Seg Regional"] = seg("Seguimiento Regional - Lista Licitaciones - Consolidado.xlsx")
    out["Seg Regional PA"] = seg("Seguimiento Regional - Lista Licitaciones - Consolidado PA.xlsx")

    # --- Web: Licitacion WEB.xlsx, ETAPA = "WEB"
    w = _xl(f("Licitacion WEB.xlsx"), "Hoja1")
    w = w[w["ETAPA"] == "WEB"].copy()
    w["Valor comercial mínimo UF "] = pd.to_numeric(w["Valor comercial mínimo UF "], errors="coerce")
    out["Web"] = w

    # --- Sistred (CASOS_EN_PROCESO_DBN) y Sistred PA
    cols = ["NRO_EXPEDIENTE", "SERVICIO_TRAMITE", "FECHA_INGRESO_SISTEMA", "ACTIVIDAD", "ETAPA1_FECHA_INICIO", "ASIGNADO", "ESTADO_SISTEMA", "FECHA_TERMINO_SISTEMA"]
    s = pd.read_excel(f("CASOS_EN_PROCESO_DBN.xlsx"), sheet_name="DetalleCP", usecols=cols, dtype=object)
    s["NRO_EXPEDIENTE"] = _txt(s["NRO_EXPEDIENTE"])
    s = s[s["SERVICIO_TRAMITE"] == "Venta"]
    spa = pd.read_excel(f("CASOS_EN_PROCESO_DBN PA.xlsx"), sheet_name="DetalleCP", usecols=["NRO_EXPEDIENTE", "SERVICIO_TRAMITE", "ACTIVIDAD"], dtype=object)
    spa["NRO_EXPEDIENTE"] = _txt(spa["NRO_EXPEDIENTE"])  # OJO: Sistred PA no filtra SERVICIO_TRAMITE = "Venta"

    # --- Ventas Directas (+ merge Sistred) y Ventas Directas PA (+ merge Sistred PA)
    vd_src = "20260721 Ventas directas avanzadas y PP pasadas por escriturar adjudicatario.xlsx"
    vd = _xl(f(vd_src), "Ventas directas avanzadas")
    vd = vd.drop(columns=[c for c in ["SISTEMA", "SERVICIO_POSTULACION", "ACTIVIDAD", "ETAPA1_FECHA_INICIO", "ASIGNADO", "ESTADO_SISTEMA"] if c in vd.columns])
    vd["NRO_EXPEDIENTE"] = _txt(vd["NRO_EXPEDIENTE"])
    vd["Precio UF"] = pd.to_numeric(vd["Precio UF"], errors="coerce")
    sx = s.rename(columns={c: "Sistred." + c for c in s.columns if c != "NRO_EXPEDIENTE"})
    vd = vd.merge(sx, on="NRO_EXPEDIENTE", how="left")
    out["Ventas Directas"] = vd
    vdpa = _xl(f(vd_src), "Ventas directas avanzadas")[["NRO_EXPEDIENTE"]].copy()
    vdpa["NRO_EXPEDIENTE"] = _txt(vdpa["NRO_EXPEDIENTE"])
    vdpa = vdpa.merge(spa[["NRO_EXPEDIENTE", "ACTIVIDAD"]].rename(columns={"ACTIVIDAD": "Sistred PA.ACTIVIDAD"}), on="NRO_EXPEDIENTE", how="left")
    out["Ventas Directas PA"] = vdpa

    # --- Ofertas WEB.xlsx (fuente nueva, no está en el PBIX). Excluye la fila de totales (sin N° Expediente PP).
    of = _xl(f("Ofertas WEB.xlsx"), "Hoja1")
    of.columns = [str(c).strip() for c in of.columns]
    of = of[of["N° Expediente PP"].notna()].copy()
    of["con_oferta"] = of["N° Ofertas Recibidas"].map(lambda v: not (pd.isna(v) or str(v).strip() in ("0", "0.0", "")))
    of["Monto UF mayor oferta"] = pd.to_numeric(of["Monto UF mayor oferta"], errors="coerce").fillna(0)
    out["Ofertas"] = of

    # --- VPP: Seguimiento PP.xlsx Hoja1
    out["VPP"] = _xl(f("Seguimiento PP.xlsx"), "Hoja1")
    return out

if __name__ == "__main__":
    d = load(sys.argv[1], sys.argv[2])
    for k, v in d.items():
        print(k, v.shape)
