# Plan de Ventas 2026

Reporte HTML de seguimiento del Plan de Ventas 2026 de la División de Bienes Nacionales (MBN). Replica la lógica del informe Power BI *Seguimiento - Plan de Ventas 2026-2027* en una sola página web, sin dependencias externas.

**Ver el reporte:** abre `index.html` en cualquier navegador. Si el repositorio tiene GitHub Pages activo, queda disponible en `https://<usuario>.github.io/<repositorio>/`.

## Contenido del reporte

| Hoja | Qué muestra |
|---|---|
| **Licitaciones – Seguimiento Regional** | Ofertas recibidas, inmuebles publicados, avance para publicar, inmuebles por macroetapa, estado de trámite por etapa, avance por región y comparación con el período anterior (PA) |
| **Venta Directa** | Expedientes totales, con decreto aprobatorio y su valor; expedientes por hito (actual vs PA); detalle descargable en Excel |
| **PP por escriturar** | Expedientes de propuestas públicas pasadas pendientes de escritura; detalle descargable en Excel |

Al hacer clic en una región, etapa o hito se filtra el resto de la hoja, igual que en Power BI.

## Estructura del repositorio

```
index.html                      Reporte publicado (datos embebidos a la fecha de corte)
scripts/
  generar_reporte.py            Genera index.html desde los Excel
  etl.py                        Lee y transforma los Excel (replica Power Query)
  plantilla.html                Diseño y lógica del reporte (sin datos)
  maestros/
    M_Etapas.json               Etapas de licitación y % de progreso
    M_Regiones.json             Regiones (nombre y clave)
    M_Etapa_Venta.json          Hitos de venta directa (desde Maestro_Etapas.xlsx)
requirements.txt
```

## Cómo actualizar el reporte

Los Excel de origen **no están en el repositorio** (contienen datos personales). Se leen desde la carpeta local "Base PBI".

1. Instalar Python 3.10 o superior y las dependencias (una sola vez):
   ```
   pip install -r requirements.txt
   ```
2. Copiar los Excel nuevos en la carpeta Base PBI. Si cambia el período, los archivos actuales pasan a llamarse "PA" (ver tabla de fuentes).
3. Desde la raíz del repositorio, ejecutar:
   ```
   python scripts/generar_reporte.py "C:\ruta\a\Base PBI" --corte 22-10-2026
   ```
   Si se omite `--corte`, se usa la fecha de hoy. Tarda 1 a 2 minutos (los Excel de Sistred son grandes) y sobrescribe `index.html`.
4. Abrir `index.html`, revisar y subir el cambio a GitHub.

## Fuentes de datos (carpeta Base PBI)

| Archivo | Hoja | Uso |
|---|---|---|
| `Seguimiento Regional - Lista Licitaciones - Consolidado.xlsx` | Consolidado | Inmuebles a licitar (solo `CARTERA CE = "Si"`) |
| `Seguimiento Regional - Lista Licitaciones - Consolidado PA.xlsx` | Consolidado | Foto del período anterior |
| `Licitacion WEB.xlsx` | Hoja1 | Inmuebles publicados (`ETAPA = "WEB"`) y valor comercial mínimo |
| `Ofertas WEB.xlsx` | Hoja1 | Ofertas recibidas y monto de la mayor oferta (se excluye la fila de totales) |
| `20260721 Ventas directas avanzadas y PP pasadas por escriturar adjudicatario.xlsx` | Ventas directas avanzadas | Cartera de venta directa y precio UF |
| `CASOS_EN_PROCESO_DBN.xlsx` | DetalleCP | Sistred: actividad, estado y asignado de cada expediente (trámites de Venta) |
| `CASOS_EN_PROCESO_DBN PA.xlsx` | DetalleCP | Sistred del período anterior |
| `Seguimiento PP.xlsx` | Hoja1 | Ventas de propuestas públicas pasadas por escriturar |

## Reglas de cálculo principales

- **Avance para publicar**: promedio del % asignado a la etapa de cada inmueble (1.1 = 10 % … 4.3 = 95 %; desde 5. Publicación = 100 %).
- **Inmuebles publicados vs meta**: inmuebles en `Licitacion WEB` frente al total de la cartera.
- **Ofertas recibidas**: expedientes con "N° Ofertas Recibidas" distinto de 0; **valor UF mayor oferta**: suma de "Monto UF mayor oferta".
- **VD con decreto aprobatorio**: expedientes en hitos con Cumplimiento = 1 (desde "Recibir Antecedentes Aprob") o finalizados en Sistred.
- Publicados y ofertas se filtran por región, pero no por etapa (sus Excel no traen la etapa del inmueble).

## Privacidad

- **No subir** archivos `.xlsx` ni `.pbix`: el `.gitignore` los excluye.
- `index.html` contiene datos institucionales (expedientes, ubicaciones y nombre del funcionario asignado en Venta Directa). Antes de hacer público el repositorio o activar GitHub Pages, confirmar que su publicación está autorizada.
