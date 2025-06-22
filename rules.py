# rules.py

# Geometrische Analyse → Augenform
def determine_eye_shape(open_ratio, tilt_angle):
    if open_ratio < 0.25 and tilt_angle < -0.1:
        return "monolid"
    elif open_ratio > 0.4 and tilt_angle > 0.1:
        return "round"
    elif tilt_angle < -0.1:
        return "downturned"
    elif tilt_angle > 0.1:
        return "upturned"
    else:
        return "almond"

# Erweiterte Schulungsbasierte Regeln
lash_mapping_rules = {
    "monolid": {
        "style": "Dolly",
        "mapping": "Längste Länge in der Mitte",
        "curl": "L",
        "length": "7–12 mm",
        "notes": "Empfohlen bei sehr schmalem Augenlid ohne Falte"
    },
    "round": {
        "style": "Cat / Squirrel",
        "mapping": "Außen betont",
        "curl": "C / D",
        "length": "außen oder mittig",
        "notes": "Mitte nicht zu lang – sonst wirkt es noch runder"
    },
    "almond": {
        "style": "Beliebig",
        "mapping": "Individuell",
        "curl": "C / CC",
        "length": "Individuell",
        "notes": "Kundenwunsch abfragen – jede Form möglich"
    },
    "downturned": {
        "style": "Cat / Squirrel",
        "mapping": "Außen verlängert",
        "curl": "C / D",
        "length": "7–13 mm",
        "notes": "Auge optisch anheben"
    },
    "upturned": {
        "style": "Natural",
        "mapping": "Mitte betont",
        "curl": "C",
        "length": "8–11 mm",
        "notes": "Letztes Drittel nicht zu lang – außen evtl. braun"
    }
}

def get_mapping_recommendation(eye_shape):
    return lash_mapping_rules.get(eye_shape, {
        "style": "Natural",
        "mapping": "Klassisch",
        "curl": "C",
        "length": "8–11 mm",
        "notes": "Keine spezifische Empfehlung gefunden"
    })

