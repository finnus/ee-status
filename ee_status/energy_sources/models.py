from django.db import models


class EnergySources(models.Model):
    einheitmastrnummer = models.TextField(
        max_length=256, unique=True, blank=True, null=True
    )
    land = models.TextField(max_length=256, blank=True, null=True)
    bundesland = models.TextField(max_length=256, blank=True, null=True)
    landkreis = models.TextField(max_length=256, blank=True, null=True)
    gemeinde = models.TextField(max_length=256, blank=True, null=True)
    gemeindeschluessel = models.TextField(max_length=256, blank=True, null=True)
    postleitzahl = models.TextField(max_length=256, blank=True, null=True)
    ort = models.TextField(max_length=256, blank=True, null=True)
    breitengrad = models.FloatField(blank=True, null=True)
    geplantesinbetriebnahmedatum = models.DateField(blank=True, null=True)
    inbetriebnahmedatum = models.DateField(blank=True, null=True)
    datumendgueltigestilllegung = models.DateField(blank=True, null=True)
    datumbeginnvoruebergehendestilllegung = models.DateField(blank=True, null=True)
    datumbeendigungvorlaeufigenstilllegung = models.DateField(blank=True, null=True)
    datumwiederaufnahmebetrieb = models.DateField(blank=True, null=True)
    einheitbetriebsstatus = models.TextField(max_length=256, blank=True, null=True)
    energietraeger = models.TextField(max_length=256, blank=True, null=True)
    bruttoleistung = models.FloatField(blank=True, null=True)
    nettonennleistung = models.FloatField(blank=True, null=True)
    anschlussanhoechstoderhochspannung = models.BooleanField(blank=True, null=True)
    schwarzstartfaehigkeit = models.BooleanField(blank=True, null=True)
    inselbetriebsfaehigkeit = models.BooleanField(blank=True, null=True)
    fernsteuerbarkeitnb = models.BooleanField(blank=True, null=True)
    fernsteuerbarkeitdv = models.BooleanField(blank=True, null=True)
    fernsteuerbarkeitdr = models.BooleanField(blank=True, null=True)
    einspeisungsart = models.TextField(max_length=256, blank=True, null=True)
    praequalifiziertfuerregelenergie = models.BooleanField(blank=True, null=True)
    solar_lage = models.TextField(max_length=256, blank=True, null=True)
    solar_leistungsbegrenzung = models.TextField(max_length=256, blank=True, null=True)
    solar_hauptausrichtung = models.TextField(max_length=256, blank=True, null=True)
    solar_hauptausrichtungneigungswinkel = models.TextField(
        max_length=256, blank=True, null=True
    )
    solar_inanspruchgenommeneflaeche = models.FloatField(blank=True, null=True)
    solar_artderflaeche = models.TextField(max_length=256, blank=True, null=True)
    solar_inanspruchgenommeneackerflaeche = models.FloatField(blank=True, null=True)
    solar_nutzungsbereich = models.TextField(max_length=256, blank=True, null=True)
    solar_artderflaecheids = models.TextField(max_length=256, blank=True, null=True)
    biomass_hauptbrennstoff = models.TextField(max_length=256, blank=True, null=True)
    biomass_biomasseart = models.TextField(max_length=256, blank=True, null=True)
    biomass_technologie = models.TextField(max_length=256, blank=True, null=True)
    hydro_artderwasserkraftanlage = models.TextField(
        max_length=256, blank=True, null=True
    )
    hydro_minderungstromerzeugung = models.BooleanField(blank=True, null=True)
    hydro_nettonennleistungdeutschland = models.FloatField(blank=True, null=True)
    hydro_artdeszuflusses = models.TextField(max_length=256, blank=True, null=True)
    wind_lage = models.TextField(max_length=256, blank=True, null=True)
    wind_seelage = models.TextField(max_length=256, blank=True, null=True)
    wind_clusterostsee = models.TextField(max_length=256, blank=True, null=True)
    wind_clusternordsee = models.TextField(max_length=256, blank=True, null=True)
    wind_technologie = models.TextField(max_length=256, blank=True, null=True)
    wind_nabenhoehe = models.FloatField(blank=True, null=True)
    wind_rotordurchmesser = models.FloatField(blank=True, null=True)
    wind_wassertiefe = models.FloatField(blank=True, null=True)
    wind_kuestenentfernung = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "energy_sources"
