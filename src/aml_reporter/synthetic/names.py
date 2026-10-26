"""Curated reference lists for synthetic customers and counterparties.

Only very common Italian first names and surnames are used, so no generated person points to a
recognisable individual. Street names are deliberately fictitious.
"""

CITIES = (  # (city, postal code, municipality code used in tax codes)
    ("Milano", "20121", "F205"),
    ("Roma", "00184", "H501"),
    ("Torino", "10121", "L219"),
    ("Napoli", "80133", "F839"),
    ("Bologna", "40121", "A944"),
    ("Firenze", "50123", "D612"),
)
OCCUPATIONS = (  # Declared occupations of individual customers
    "Logistics clerk",
    "Nurse",
    "Teacher",
    "Software developer",
    "Accountant",
)
SOLE_TRADES = (  # (trade name, sector) pairs for sole traders
    ("IMPIANTI ELETTRICI", "Electrical installation"),
    ("RISTRUTTURAZIONI", "Home renovation"),
    ("CONSULENZA INFORMATICA", "IT consulting"),
)

MALE_NAMES = (  # Common Italian male first names
    "MARCO",
    "LUCA",
    "ANDREA",
    "MATTEO",
    "ALESSANDRO",
    "DAVIDE",
    "SIMONE",
    "FEDERICO",
    "PAOLO",
    "STEFANO",
    "GIUSEPPE",
    "FRANCESCO",
    "ANTONIO",
    "GIOVANNI",
    "ROBERTO",
    "LORENZO",
)
FEMALE_NAMES = (  # Common Italian female first names
    "GIULIA",
    "FRANCESCA",
    "CHIARA",
    "SARA",
    "ELENA",
    "LAURA",
    "VALENTINA",
    "MARTINA",
    "SILVIA",
    "ANNA",
    "FEDERICA",
    "ALESSIA",
    "PAOLA",
    "ELISA",
    "GIORGIA",
    "ILARIA",
)
LAST_NAMES = (  # Among the most common Italian surnames
    "ROSSI",
    "FERRARI",
    "ESPOSITO",
    "BIANCHI",
    "ROMANO",
    "COLOMBO",
    "RICCI",
    "MARINO",
    "GRECO",
    "BRUNO",
    "GALLO",
    "CONTI",
    "DE LUCA",
    "MANCINI",
    "COSTA",
    "GIORDANO",
    "RIZZO",
    "LOMBARDI",
    "MORETTI",
    "BARBIERI",
    "FONTANA",
    "SANTORO",
    "MARIANI",
    "RINALDI",
)
STREETS = (  # Fictitious street names, so no address can match a real home
    "VIA ESEMPIO",
    "VIA IMMAGINARIA",
    "VIALE FITTIZIO",
    "PIAZZA CAMPIONE",
    "CORSO PROTOTIPO",
    "VIA SINTETICA",
)
