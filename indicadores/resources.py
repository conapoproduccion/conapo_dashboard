from import_export import resources, fields
from .models import IndicadoresMunicipio, PoblacionQuinquenal, PoblacionEdad


FUENTE_DEFAULT = 'CONAPO'
FUENTE_ALIASES = ('FUENTE', 'ORIGEN', 'FUENTE_DATOS', 'FUENTE_DATO')

# Normalización de la fuente (incluye los alias nuevos de db_nueva_27102026.csv)
FUENTE_MAP_EDAD = {
    'CONAPO_CRUDA':        'CONAPO_CRUDA',
    'CONAPO':              'CONAPO',
    'CONAPO_PROY':         'CONAPO_PROY',
    'CONAPO_PROYECCION':   'CONAPO_PROY',
    'CONAPO_PROYECCIONES': 'CONAPO_PROY',
    'INEGI_CRUDA':         'INEGI_CRUDA',
    'INEGI':               'INEGI',
    'CENSO':               'CENSO',
    'ENADID':              'ENADID',
}

# Normalización de grupos de edad: unifica '75mm'/'85mm'/'85_mm' a un catálogo único.
# La pirámide del frontend espera: 00-04 ... 70-74, 75-79, 80-84, 85+
GEDAD_NORMALIZE = {
    '00-04': '00-04', '00_04': '00-04', '00mm': '00-04',
    '05-09': '05-09', '05_09': '05-09',
    '10-14': '10-14', '10_14': '10-14',
    '15-19': '15-19', '15_19': '15-19',
    '20-24': '20-24', '20_24': '20-24',
    '25-29': '25-29', '25_29': '25-29',
    '30-34': '30-34', '30_34': '30-34',
    '35-39': '35-39', '35_39': '35-39',
    '40-44': '40-44', '40_44': '40-44',
    '45-49': '45-49', '45_49': '45-49',
    '50-54': '50-54', '50_54': '50-54',
    '55-59': '55-59', '55_59': '55-59',
    '60-64': '60-64', '60_64': '60-64',
    '65-69': '65-69', '65_69': '65-69',
    '70-74': '70-74', '70_74': '70-74',
    # '75+' abierto (INEGI_CRUDA a veces lo manda así): se pliega a 75-79
    '75+': '75-79', '75mm': '75-79', '75_mm': '75-79', '75-79': '75-79', '75_79': '75-79',
    '80+': '80-84', '80mm': '80-84', '80_mm': '80-84', '80-84': '80-84', '80_84': '80-84',
    '85+': '85+',   '85mm': '85+',   '85_mm': '85+',   '85-89': '85+', '85_89': '85+',
    '90+': '85+',   '90mm': '85+',   '90_mm': '85+',
}


def _resolver_fuente(row):
    """Busca la fuente en cualquiera de los alias y normaliza; si no hay, CONAPO."""
    valor = None
    for alias in FUENTE_ALIASES:
        if alias in row and row.get(alias) not in (None, ''):
            valor = row.get(alias)
            break
    if not valor or str(valor).strip() == '':
        return FUENTE_DEFAULT
    return str(valor).strip().upper()


def _normalizar_gedad(valor):
    """Devuelve el grupo de edad normalizado al catálogo de 18 grupos."""
    if valor in (None, ''):
        return ''
    raw = str(valor).strip().lower().replace(' ', '')
    # Intento directo por el mapa (con el valor original y con guion bajo)
    if raw in GEDAD_NORMALIZE:
        return GEDAD_NORMALIZE[raw]
    raw_us = raw.replace('-', '_')
    if raw_us in GEDAD_NORMALIZE:
        return GEDAD_NORMALIZE[raw_us]
    # Fallback: devolver tal cual (sin espacios)
    return str(valor).strip()


def _to_int(value, default=0):
    """Convierte '185.0' / 'NA' / '' a int de forma segura."""
    if value in (None, '', 'NA', 'N/A'):
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def _to_float_or_none(value):
    """Convierte a float; 'NA' / '' / None → None."""
    if value in (None, '', 'NA', 'N/A'):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class IndicadoresMunicipioResource(resources.ModelResource):
    clave     = fields.Field(column_name='CLAVE',     attribute='clave')
    clave_ent = fields.Field(column_name='CLAVE_ENT', attribute='clave_ent')
    nom_ent   = fields.Field(column_name='NOM_ENT',   attribute='nom_ent')
    nom_mun   = fields.Field(column_name='NOM_MUN',   attribute='nom_mun')
    anio      = fields.Field(column_name='AÑO',       attribute='anio')

    hom_mit_anio = fields.Field(column_name='HOM_MIT_AÑO', attribute='hom_mit_anio')
    muj_mit_anio = fields.Field(column_name='MUJ_MIT_AÑO', attribute='muj_mit_anio')
    pob_mit_mun  = fields.Field(column_name='POB_MIT_MUN',  attribute='pob_mit_mun')

    muj_00_14 = fields.Field(column_name='MUJ_00_14', attribute='muj_00_14')
    hom_00_14 = fields.Field(column_name='HOM_00_14', attribute='hom_00_14')
    pob_00_14 = fields.Field(column_name='POB_00_14', attribute='pob_00_14')
    muj_15_64 = fields.Field(column_name='MUJ_15_64', attribute='muj_15_64')
    hom_15_64 = fields.Field(column_name='HOM_15_64', attribute='hom_15_64')
    pob_15_64 = fields.Field(column_name='POB_15_64', attribute='pob_15_64')
    muj_60_mas = fields.Field(column_name='MUJ_60_MAS', attribute='muj_60_mas')
    hom_60_mas = fields.Field(column_name='HOM_60_MAS', attribute='hom_60_mas')
    pob_60_mas = fields.Field(column_name='POB_60_MAS', attribute='pob_60_mas')
    muj_65_mas = fields.Field(column_name='MUJ_65_MAS', attribute='muj_65_mas')
    hom_65_mas = fields.Field(column_name='HOM_65_MAS', attribute='hom_65_mas')
    pob_65_mas = fields.Field(column_name='POB_65_MAS', attribute='pob_65_mas')

    pob_mit_ent = fields.Field(column_name='POB_MIT_ENT', attribute='pob_mit_ent')
    edad_med    = fields.Field(column_name='EDAD_MED',    attribute='edad_med')
    por_mun     = fields.Field(column_name='POR_MUN',     attribute='por_mun')
    ind_env_60  = fields.Field(column_name='IND_ENV_60',  attribute='ind_env_60')
    ind_env_65  = fields.Field(column_name='IND_ENV_65',  attribute='ind_env_65')
    rhm         = fields.Field(column_name='RHM',         attribute='rhm')
    raz_dep_adu = fields.Field(column_name='RAZ_DEP_ADU', attribute='raz_dep_adu')
    raz_dep_inf = fields.Field(column_name='RAZ_DEP_INF', attribute='raz_dep_inf')
    raz_dep     = fields.Field(column_name='RAZ_DEP',     attribute='raz_dep')

    fuente = fields.Field(column_name='FUENTE', attribute='fuente')

    class Meta:
        model = IndicadoresMunicipio
        import_id_fields = ('clave', 'anio', 'fuente')
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        row['FUENTE'] = _resolver_fuente(row)


class PoblacionQuinquenalResource(resources.ModelResource):
    clave     = fields.Field(column_name='CLAVE',     attribute='clave')
    clave_ent = fields.Field(column_name='CLAVE_ENT', attribute='clave_ent')
    nom_ent   = fields.Field(column_name='NOM_ENT',   attribute='nom_ent')
    nom_mun   = fields.Field(column_name='NOM_MUN',   attribute='nom_mun')
    sexo      = fields.Field(column_name='SEXO',      attribute='sexo')
    anio      = fields.Field(column_name='AÑO',       attribute='anio')

    pob_00_04 = fields.Field(column_name='POB_00_04', attribute='pob_00_04')
    pob_05_09 = fields.Field(column_name='POB_05_09', attribute='pob_05_09')
    pob_10_14 = fields.Field(column_name='POB_10_14', attribute='pob_10_14')
    pob_15_19 = fields.Field(column_name='POB_15_19', attribute='pob_15_19')
    pob_20_24 = fields.Field(column_name='POB_20_24', attribute='pob_20_24')
    pob_25_29 = fields.Field(column_name='POB_25_29', attribute='pob_25_29')
    pob_30_34 = fields.Field(column_name='POB_30_34', attribute='pob_30_34')
    pob_35_39 = fields.Field(column_name='POB_35_39', attribute='pob_35_39')
    pob_40_44 = fields.Field(column_name='POB_40_44', attribute='pob_40_44')
    pob_45_49 = fields.Field(column_name='POB_45_49', attribute='pob_45_49')
    pob_50_54 = fields.Field(column_name='POB_50_54', attribute='pob_50_54')
    pob_55_59 = fields.Field(column_name='POB_55_59', attribute='pob_55_59')
    pob_60_64 = fields.Field(column_name='POB_60_64', attribute='pob_60_64')
    pob_65_69 = fields.Field(column_name='POB_65_69', attribute='pob_65_69')
    pob_70_74 = fields.Field(column_name='POB_70_74', attribute='pob_70_74')
    pob_75_79 = fields.Field(column_name='POB_75_79', attribute='pob_75_79')
    pob_80_84 = fields.Field(column_name='POB_80_84', attribute='pob_80_84')
    pob_85_mm = fields.Field(column_name='POB_85_mm', attribute='pob_85_mm')
    pob_total = fields.Field(column_name='POB_TOTAL', attribute='pob_total')

    fuente = fields.Field(column_name='FUENTE', attribute='fuente')

    class Meta:
        model = PoblacionQuinquenal
        import_id_fields = ('clave', 'anio', 'sexo', 'fuente')
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        row['FUENTE'] = _resolver_fuente(row)


# ============================================================
# RESOURCE: Importa db_nueva_27102026.csv (o los divididos por año)
# ============================================================

class PoblacionEdadResource(resources.ModelResource):
    clave     = fields.Field(column_name='CLAVE',     attribute='clave')
    clave_ent = fields.Field(column_name='CLAVE_ENT', attribute='clave_ent')
    nom_ent   = fields.Field(column_name='NOM_ENT',   attribute='nom_ent')
    nom_mun   = fields.Field(column_name='NOM_MUN',   attribute='nom_mun')
    gedad     = fields.Field(column_name='GEDAD',     attribute='gedad')
    sexo      = fields.Field(column_name='SEXO',      attribute='sexo')
    anio      = fields.Field(column_name='ANIO',      attribute='anio')
    pob       = fields.Field(column_name='POB',       attribute='pob')
    rhm       = fields.Field(column_name='RHM',       attribute='rhm')   # NUEVO
    censados  = fields.Field(column_name='CENSADOS',  attribute='censados')
    ee        = fields.Field(column_name='EE',        attribute='ee')
    li        = fields.Field(column_name='LI',        attribute='li')
    ls        = fields.Field(column_name='LS',        attribute='ls')
    cv        = fields.Field(column_name='CV',        attribute='cv')
    munmod    = fields.Field(column_name='MUNMOD',    attribute='munmod')
    fuente    = fields.Field(column_name='FUENTE',    attribute='fuente')

    class Meta:
        model = PoblacionEdad
        import_id_fields = ('clave', 'nom_mun', 'anio', 'sexo', 'gedad', 'fuente')
        skip_unchanged = True
        report_skipped = True
        exclude = ('id',)

    def before_import_row(self, row, **kwargs):
        # --- 1. POBLACIÓN (int, evita el problema de "185.0") ---
        row['POB'] = _to_int(row.get('POB'), default=0)

        # --- 2. RHM (viene ya calculado; puede venir 'NA' cuando no aplica) ---
        row['RHM'] = _to_float_or_none(row.get('RHM'))

        # --- 3. FUENTE ---
        raw = (row.get('FUENTE') or '').strip().upper()
        row['FUENTE'] = FUENTE_MAP_EDAD.get(raw, raw or 'CONAPO_CRUDA')

        # --- 4. SEXO ---
        sexo = (row.get('SEXO') or '').strip()
        row['SEXO'] = sexo.capitalize() if sexo else 'Total'

        # --- 5. Nombres y grupo de edad normalizado ---
        row['NOM_ENT'] = (row.get('NOM_ENT') or '').strip().title()
        row['NOM_MUN'] = (row.get('NOM_MUN') or '').strip().title()
        row['GEDAD']   = _normalizar_gedad(row.get('GEDAD'))

        # --- 6. Metadatos con 'NA' → None ---
        for campo in ('CENSADOS', 'EE', 'LI', 'LS', 'CV'):
            if row.get(campo) in ('NA', 'N/A', '', None):
                row[campo] = None

        # --- 7. MUNMOD ---
        row['MUNMOD'] = _to_int(row.get('MUNMOD'), default=0)