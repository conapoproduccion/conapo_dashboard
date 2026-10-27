import json
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum
from .models import IndicadoresMunicipio, PoblacionQuinquenal, PoblacionEdad


FUENTE_DEFAULT = 'CONAPO'
FUENTE_DEFAULT_EDAD = 'CONAPO_CRUDA'

RANGOS_EDAD = ['00-04', '05-09', '10-14', '15-19', '20-24', '25-29', '30-34',
               '35-39', '40-44', '45-49', '50-54', '55-59', '60-64', '65-69',
               '70-74', '75-79', '80-84', '85+']

def _mapa_grupo_quinquenal(grupo):
    if grupo == 'total':
        return None
    return grupo.replace('_', '-').replace('mm', '+')

def _safe_float(val):
    if val in (None, '', 'NA', 'N/A'):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ============================================================
# LÓGICA COMPARTIDA
# ============================================================
def _calcular_indicadores(qs, grupo_quinquenal, años_piramide, es_municipio=False):
    
    # 1. POBLACIÓN TOTAL (Sumar SOLO Hombres + Mujeres, EXCLUIR 'TOTAL')
    sexo_anual = {}
    qs_pob = qs.filter(sexo__in=['Hombres', 'Mujeres']).exclude(gedad__iexact='TOTAL')
    
    for q in qs_pob.values('anio', 'sexo').annotate(pob=Sum('pob')):
        sexo_anual.setdefault(q['anio'], {'Hombres': 0, 'Mujeres': 0})
        sexo_anual[q['anio']][q['sexo']] = q['pob'] or 0

    # 2. LI / LS / CV (Extraer del grupo 'TOTAL')
    gedad_sel_tmp = _mapa_grupo_quinquenal(grupo_quinquenal)
    
    if gedad_sel_tmp:
        qs_meta = qs.filter(sexo='Total', gedad=gedad_sel_tmp)
    else:
        qs_meta = qs.filter(sexo='Total', gedad__iexact='TOTAL')
        if not qs_meta.exists():
            qs_meta = qs.filter(sexo='Total').exclude(gedad__iexact='TOTAL')
    
    meta_anual = {}
    for r in qs_meta.values('anio', 'li', 'ls', 'cv'):
        anio = r['anio']
        if anio not in meta_anual:
            meta_anual[anio] = {'li': 0.0, 'ls': 0.0, 'cv': None, 'cv_count': 0}
            
        li_val = _safe_float(r.get('li'))
        ls_val = _safe_float(r.get('ls'))
        cv_val = _safe_float(r.get('cv'))
        
        if li_val is not None: meta_anual[anio]['li'] += li_val
        if ls_val is not None: meta_anual[anio]['ls'] += ls_val
            
        if cv_val is not None:
            meta_anual[anio]['cv'] = (meta_anual[anio]['cv'] or 0) + cv_val
            meta_anual[anio]['cv_count'] += 1

    for anio in meta_anual:
        if meta_anual[anio]['cv_count'] > 0:
            meta_anual[anio]['cv'] = round(meta_anual[anio]['cv'] / meta_anual[anio]['cv_count'], 2)
        if meta_anual[anio]['li'] == 0.0: meta_anual[anio]['li'] = None
        if meta_anual[anio]['ls'] == 0.0: meta_anual[anio]['ls'] = None

    # 3. Población del Grupo de Edad específico (Hombres y Mujeres)
    gedad_sel = gedad_sel_tmp
    edad_anual = {}
    if gedad_sel:
        qs_edad = qs.filter(gedad=gedad_sel, sexo__in=['Hombres', 'Mujeres'])
        for q in qs_edad.values('anio', 'sexo').annotate(pob=Sum('pob')):
            edad_anual.setdefault(q['anio'], {'Hombres': 0, 'Mujeres': 0})
            edad_anual[q['anio']][q['sexo']] = q['pob'] or 0

    # 4. RHM ya calculada (Leer SOLO de las filas 'Total')
    rhm_por_anio_gedad = {}
    qs_rhm_rows = qs.filter(sexo='Total').exclude(rhm__isnull=True).values('anio', 'gedad', 'rhm')
    for r in qs_rhm_rows:
        rhm_por_anio_gedad[(r['anio'], r['gedad'].upper())] = float(r['rhm'])

    # 5. Armar series
    anios = sorted(sexo_anual.keys())
    hom_total, muj_total, pob_total, razon = [], [], [], []

    for anio in anios:
        h = sexo_anual.get(anio, {}).get('Hombres', 0)
        m = sexo_anual.get(anio, {}).get('Mujeres', 0)

        hom_total.append(h)
        muj_total.append(m)
        pob_total.append(h + m)

        # --- LÓGICA DE LA RAZÓN DE MASCULINIDAD ---
        if es_municipio:
            # MUNICIPIO: Confiamos en el RHM de la base de datos
            if gedad_sel:
                rhm_val = rhm_por_anio_gedad.get((anio, gedad_sel.upper()))
            else:
                rhm_val = rhm_por_anio_gedad.get((anio, 'TOTAL'))

            if rhm_val is not None and rhm_val > 0:
                razon.append(round(rhm_val, 2))
            else:
                # Fallback si el municipio no tiene RHM en la DB
                if gedad_sel:
                    h_e = edad_anual.get(anio, {}).get('Hombres', 0)
                    m_e = edad_anual.get(anio, {}).get('Mujeres', 0)
                else:
                    h_e, m_e = h, m
                razon.append(round(h_e / m_e * 100, 2) if m_e else 0)
        else:
            # ENTIDAD O VALLE DE MÉXICO: Calculamos siempre para evitar promedios falsos
            if gedad_sel:
                h_e = edad_anual.get(anio, {}).get('Hombres', 0)
                m_e = edad_anual.get(anio, {}).get('Mujeres', 0)
            else:
                h_e, m_e = h, m
            razon.append(round(h_e / m_e * 100, 2) if m_e else 0)

    # 6. Series LI / LS / CV alineadas
    li_serie, ls_serie, cv_serie = [], [], []
    for anio in anios:
        m = meta_anual.get(anio, {})
        li_serie.append(m.get('li'))
        ls_serie.append(m.get('ls'))
        cv_serie.append(m.get('cv'))

    # 7. Pirámides (Filtramos H y M y EXCLUIMOS 'TOTAL')
    piramides = {}
    for anio in años_piramide:
        base = qs.filter(anio=anio, sexo__in=['Hombres', 'Mujeres']).exclude(gedad__iexact='TOTAL')
        by = {}
        for q in base.values('gedad', 'sexo').annotate(pob=Sum('pob')):
            by.setdefault(q['sexo'], {})[q['gedad']] = q['pob'] or 0
        piramides[str(anio)] = {
            'hombres': [by.get('Hombres', {}).get(g, 0) for g in RANGOS_EDAD],
            'mujeres': [by.get('Mujeres', {}).get(g, 0) for g in RANGOS_EDAD],
        }

    return {
        'anios': anios,
        'hom_total': hom_total,
        'muj_total': muj_total,
        'pob_total': pob_total,
        'razon_hombres': razon,
        'rangos_edad': RANGOS_EDAD,
        'piramides': piramides,
        'li_serie': li_serie,
        'ls_serie': ls_serie,
        'cv_serie': cv_serie,
    }


# ============================================================
# VISTAS
# ============================================================
def dashboard_view(request):
    todas_fuentes = sorted(set(PoblacionEdad.objects.values_list('fuente', flat=True).distinct())) or [FUENTE_DEFAULT_EDAD]
    entidades_qs = PoblacionEdad.objects.values_list('clave_ent', 'nom_ent').distinct()
    entidades_dict = {c: f"{str(c).zfill(2)} {n.strip().title()}" for c, n in entidades_qs if n}
    municipios_qs = PoblacionEdad.objects.values_list('clave_ent', 'clave', 'nom_mun').distinct()
    municipios_por_entidad = {}
    for clave_ent, clave_mun, nom_mun in municipios_qs:
        if nom_mun:
            c_str = str(clave_ent)
            municipios_por_entidad.setdefault(c_str, set())
            nombre_ent = entidades_dict.get(clave_ent, "")
            municipios_por_entidad[c_str].add(f"{nombre_ent} - {nom_mun.strip().title()} ({str(clave_mun).zfill(3)})")
    for clave in municipios_por_entidad:
        municipios_por_entidad[clave] = sorted(list(municipios_por_entidad[clave]))
    entidades_list = [{'clave_ent': k, 'nom_ent': v} for k, v in sorted(entidades_dict.items(), key=lambda item: item[1])]
    return render(request, 'indicadores/dashboard.html', {'entidades': entidades_list, 'municipios_json': json.dumps(municipios_por_entidad), 'todas_fuentes': todas_fuentes, 'fuente_default': todas_fuentes[0]})

def api_dashboard_data(request):
    entidad = request.GET.get('entidad', '')
    municipio = request.GET.get('municipio', '')
    año_inicio = int(request.GET.get('año_inicio', 1990))
    año_fin = int(request.GET.get('año_fin', 2040))
    años_piramide_str = request.GET.get('años_piramide', '2025')
    grupo_quinquenal = request.GET.get('grupo_quinquenal', 'total')
    fuente = request.GET.get('fuente', FUENTE_DEFAULT_EDAD) or FUENTE_DEFAULT_EDAD
    años_piramide = [int(y.strip()) for y in años_piramide_str.split(',') if y.strip().isdigit()]

    qs = PoblacionEdad.objects.filter(fuente=fuente, anio__gte=año_inicio, anio__lte=año_fin)
    if entidad: qs = qs.filter(clave_ent=entidad)
    
    es_municipio = False
    if municipio:
        nombre_limpio = municipio.split(' - ')[-1].rsplit(' (', 1)[0].strip()
        qs = qs.filter(nom_mun__iexact=nombre_limpio)
        es_municipio = True

    data = _calcular_indicadores(qs, grupo_quinquenal, años_piramide, es_municipio=es_municipio)
    return JsonResponse(data)


def dashboard_comparativo_view(request):
    todas_fuentes = sorted(set(PoblacionEdad.objects.values_list('fuente', flat=True).distinct())) or [FUENTE_DEFAULT_EDAD]
    entidades_qs = PoblacionEdad.objects.values_list('clave_ent', 'nom_ent').distinct()
    entidades_dict = {c: f"{str(c).zfill(2)} {n.strip().title()}" for c, n in entidades_qs if n}
    municipios_qs = PoblacionEdad.objects.values_list('clave_ent', 'clave', 'nom_mun').distinct()
    municipios_por_entidad = {}
    for clave_ent, clave_mun, nom_mun in municipios_qs:
        if nom_mun:
            c_str = str(clave_ent)
            municipios_por_entidad.setdefault(c_str, set())
            nombre_ent = entidades_dict.get(clave_ent, "")
            municipios_por_entidad[c_str].add(f"{nombre_ent} - {nom_mun.strip().title()} ({str(clave_mun).zfill(3)})")
    for clave in municipios_por_entidad:
        municipios_por_entidad[clave] = sorted(list(municipios_por_entidad[clave]))
    entidades_list = [{'clave_ent': k, 'nom_ent': v} for k, v in sorted(entidades_dict.items(), key=lambda item: item[1])]
    return render(request, 'indicadores/dashboard_comparativo.html', {'entidades': entidades_list, 'municipios_json': json.dumps(municipios_por_entidad), 'todas_fuentes': todas_fuentes, 'fuente_default': todas_fuentes[0]})

def api_dashboard_comparativo(request):
    entidad = request.GET.get('entidad', '')
    municipio = request.GET.get('municipio', '')
    año_inicio = int(request.GET.get('año_inicio', 1990))
    año_fin = int(request.GET.get('año_fin', 2040))
    años_piramide_str = request.GET.get('años_piramide', '2025')
    grupo_quinquenal = request.GET.get('grupo_quinquenal', 'total')

    fuente_a = request.GET.get('fuente_a', FUENTE_DEFAULT_EDAD) or FUENTE_DEFAULT_EDAD
    fuente_b = request.GET.get('fuente_b', '') or ''

    años_piramide = [int(y.strip()) for y in años_piramide_str.split(',') if y.strip().isdigit()]

    def _filtrar(fuente):
        qs = PoblacionEdad.objects.filter(fuente=fuente, anio__gte=año_inicio, anio__lte=año_fin)
        if entidad: qs = qs.filter(clave_ent=entidad)
        if municipio:
            nombre_limpio = municipio.split(' - ')[-1].rsplit(' (', 1)[0].strip()
            qs = qs.filter(nom_mun__iexact=nombre_limpio)
        return qs

    es_municipio = bool(municipio)

    data_a = _calcular_indicadores(_filtrar(fuente_a), grupo_quinquenal, años_piramide, es_municipio=es_municipio)
    data_b = None
    if fuente_b:
        data_b = _calcular_indicadores(_filtrar(fuente_b), grupo_quinquenal, años_piramide, es_municipio=es_municipio)

    li_ls_ultimo_anio = None
    if data_b:
        for i in range(len(data_b['anios']) - 1, -1, -1):
            if data_b['li_serie'][i] is not None and data_b['ls_serie'][i] is not None:
                li_ls_ultimo_anio = {
                    'anio': data_b['anios'][i],
                    'li': data_b['li_serie'][i],
                    'ls': data_b['ls_serie'][i]
                }
                break

    return JsonResponse({
        'fuente_a': fuente_a,
        'fuente_b': fuente_b,
        'a': data_a,
        'b': data_b,
        'li_ls_ultimo_anio': li_ls_ultimo_anio,
    })