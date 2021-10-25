detailFields = ["Site", "Name", "Vrf"]

detailChecks = ["Ent.Summ", "Site Summ"]

metadata = {
    "site": {"controlType": "lineEdit", "colorMap": {}},
    "Name": {"controlType": "lineEdit", "colorMap": {}},
    "Vrf": {
        "controlType": "lineEdit",
        "colorMap": {"GLOBAL": "green", "DATA": "orange", "VOIP": "purple"},
    },
    "Ent.Summ": {"controlType": "checkbox", "colorMap": {}},
    "Site.Summ": {"controlType": "checkbox", "colorMap": {}},
}
