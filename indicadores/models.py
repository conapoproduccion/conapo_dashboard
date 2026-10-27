from django.db import models


class IndicadoresMunicipio(models.Model):
    clave = models.CharField(max_length=10, db_index=True)
    clave_ent = models.IntegerField()
    nom_ent = models.CharField("Entidad", max_length=100)
    nom_mun = models.CharField("Municipio", max_length=150, db_index=True)
    anio = models.IntegerField("Año", db_index=True)

    hom_mit_anio = models.IntegerField()
    muj_mit_anio = models.IntegerField()
    pob_mit_mun = models.IntegerField()

    muj_00_14 = models.IntegerField()
    hom_00_14 = models.IntegerField()
    pob_00_14 = models.IntegerField()
    muj_15_64 = models.IntegerField()
    hom_15_64 = models.IntegerField()
    pob_15_64 = models.IntegerField()
    muj_60_mas = models.IntegerField()
    hom_60_mas = models.IntegerField()
    pob_60_mas = models.IntegerField()
    muj_65_mas = models.IntegerField()
    hom_65_mas = models.IntegerField()
    pob_65_mas = models.IntegerField()

    pob_mit_ent = models.IntegerField()
    edad_med = models.IntegerField()
    por_mun = models.DecimalField(max_digits=6, decimal_places=2)
    ind_env_60 = models.DecimalField(max_digits=6, decimal_places=2)
    ind_env_65 = models.DecimalField(max_digits=6, decimal_places=2)
    rhm = models.DecimalField(max_digits=6, decimal_places=2)
    raz_dep_adu = models.DecimalField(max_digits=6, decimal_places=2)
    raz_dep_inf = models.DecimalField(max_digits=6, decimal_places=2)
    raz_dep = models.DecimalField(max_digits=6, decimal_places=2)

    fuente = models.CharField("Fuente", max_length=100, default='CONAPO', db_index=True)

    class Meta:
        db_table = 'indicadores_municipio'
        unique_together = ('clave', 'anio', 'fuente')
        ordering = ['clave', 'anio', 'fuente']

    def __str__(self):
        return f"{self.nom_mun} ({self.anio}) - {self.fuente}"


class PoblacionQuinquenal(models.Model):
    SEXO_CHOICES = [('HOMBRES', 'Hombres'), ('MUJERES', 'Mujeres')]

    clave = models.CharField(max_length=10, db_index=True)
    clave_ent = models.IntegerField()
    nom_ent = models.CharField("Entidad", max_length=100)
    nom_mun = models.CharField("Municipio", max_length=150, db_index=True)
    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES, db_index=True)
    anio = models.IntegerField("Año", db_index=True)

    pob_00_04 = models.IntegerField()
    pob_05_09 = models.IntegerField()
    pob_10_14 = models.IntegerField()
    pob_15_19 = models.IntegerField()
    pob_20_24 = models.IntegerField()
    pob_25_29 = models.IntegerField()
    pob_30_34 = models.IntegerField()
    pob_35_39 = models.IntegerField()
    pob_40_44 = models.IntegerField()
    pob_45_49 = models.IntegerField()
    pob_50_54 = models.IntegerField()
    pob_55_59 = models.IntegerField()
    pob_60_64 = models.IntegerField()
    pob_65_69 = models.IntegerField()
    pob_70_74 = models.IntegerField()
    pob_75_79 = models.IntegerField()
    pob_80_84 = models.IntegerField()
    pob_85_mm = models.IntegerField()
    pob_total = models.IntegerField()

    fuente = models.CharField("Fuente", max_length=100, default='CONAPO', db_index=True)

    class Meta:
        db_table = 'poblacion_quinquenal'
        unique_together = ('clave', 'anio', 'sexo', 'fuente')
        ordering = ['clave', 'anio', 'sexo', 'fuente']

    def __str__(self):
        return f"{self.nom_mun} - {self.sexo} ({self.anio}) - {self.fuente}"


# ============================================================
# Formato largo (una fila por edad/sexo/año)
# Compatible con db_nueva_27102026.csv
# ============================================================

class PoblacionEdad(models.Model):
    """
    Formato largo. Cada fila = (municipio, año, grupo de edad, sexo, fuente).
    Incluye RHM (razón de masculinidad) ya calculada por la fuente.
    """
    SEXO_CHOICES = [
        ('Hombres', 'Hombres'),
        ('Mujeres', 'Mujeres'),
        ('Total',   'Total'),
    ]

    clave     = models.CharField(max_length=10, db_index=True)
    clave_ent = models.IntegerField(db_index=True)
    nom_ent   = models.CharField("Entidad", max_length=100)
    nom_mun   = models.CharField("Municipio", max_length=150, db_index=True)

    gedad = models.CharField("Grupo de edad", max_length=10, db_index=True)  # '00-04', '85+'
    sexo  = models.CharField(max_length=10, choices=SEXO_CHOICES, db_index=True)
    anio  = models.IntegerField("Año", db_index=True)
    pob   = models.IntegerField("Población")

    # NUEVO: razón de masculinidad (viene ya calculada en la DB nueva)
    rhm = models.DecimalField(
        "Razón de masculinidad", max_digits=10, decimal_places=4,
        null=True, blank=True, db_index=True,
    )

    # Metadatos opcionales del CSV
    censados = models.CharField(max_length=20, blank=True, null=True)
    ee       = models.CharField(max_length=20, blank=True, null=True)
    li       = models.CharField(max_length=20, blank=True, null=True)
    ls       = models.CharField(max_length=20, blank=True, null=True)
    cv       = models.CharField(max_length=20, blank=True, null=True)
    munmod   = models.IntegerField(default=0)

    fuente = models.CharField("Fuente", max_length=100, db_index=True, default='CONAPO_CRUDA')

    class Meta:
        db_table = 'poblacion_edad'
        unique_together = ('clave', 'nom_mun', 'anio', 'sexo', 'gedad', 'fuente')
        ordering = ['clave', 'anio', 'gedad', 'sexo', 'fuente']
        indexes = [
            models.Index(fields=['fuente', 'anio']),
            models.Index(fields=['clave_ent', 'nom_mun', 'anio']),
        ]

    def __str__(self):
        return f"{self.nom_mun} | {self.gedad} | {self.sexo} | {self.anio} | {self.fuente}"