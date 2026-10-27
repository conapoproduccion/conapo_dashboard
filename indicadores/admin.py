from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import IndicadoresMunicipio, PoblacionQuinquenal, PoblacionEdad
from .resources import (
    IndicadoresMunicipioResource,
    PoblacionQuinquenalResource,
    PoblacionEdadResource,
)


@admin.register(IndicadoresMunicipio)
class IndicadoresMunicipioAdmin(ImportExportModelAdmin):
    resource_class = IndicadoresMunicipioResource

    list_display = ('clave', 'nom_ent', 'nom_mun', 'anio', 'pob_mit_mun', 'fuente')
    list_filter = ('fuente', 'nom_ent', 'nom_mun', 'anio')
    search_fields = ('clave', 'nom_mun', 'nom_ent')
    ordering = ('clave', 'anio', 'fuente')


@admin.register(PoblacionQuinquenal)
class PoblacionQuinquenalAdmin(ImportExportModelAdmin):
    resource_class = PoblacionQuinquenalResource

    list_display = ('clave', 'nom_mun', 'sexo', 'anio', 'pob_total', 'fuente')
    list_filter = ('fuente', 'nom_ent', 'nom_mun', 'sexo', 'anio')
    search_fields = ('clave', 'nom_mun')
    ordering = ('clave', 'anio', 'sexo', 'fuente')


@admin.register(PoblacionEdad)
class PoblacionEdadAdmin(ImportExportModelAdmin):
    resource_class = PoblacionEdadResource

    # Agregamos 'li', 'ls' y 'cv' después de 'pob'
    list_display = (
        'clave', 'nom_ent', 'nom_mun', 'gedad', 'sexo',
        'anio', 'pob', 'li', 'ls', 'cv', 'rhm', 'fuente',
    )
    list_filter = ('fuente', 'nom_ent', 'nom_mun', 'sexo', 'gedad', 'anio')
    search_fields = ('clave', 'nom_mun', 'nom_ent')
    ordering = ('clave', 'anio', 'gedad', 'sexo', 'fuente')