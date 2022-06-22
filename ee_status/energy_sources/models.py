from django.db import models


class SolarExtended(models.Model):
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
    gemeinsamerwechselrichtermitspeicher = models.TextField(
        max_length=256, blank=True, null=True
    )
    lage = models.TextField(max_length=256, blank=True, null=True)
    leistungsbegrenzung = models.TextField(max_length=256, blank=True, null=True)
    hauptausrichtung = models.TextField(max_length=256, blank=True, null=True)
    hauptausrichtungneigungswinkel = models.TextField(
        max_length=256, blank=True, null=True
    )
    inanspruchgenommeneflaeche = models.FloatField(blank=True, null=True)
    artderflaeche = models.TextField(max_length=256, blank=True, null=True)
    inanspruchgenommeneackerflaeche = models.FloatField(blank=True, null=True)
    nutzungsbereich = models.TextField(max_length=256, blank=True, null=True)
    artderflaecheids = models.TextField(max_length=256, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "solar_extended"
