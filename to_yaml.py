import yaml
import json

data = None
with open("Testdata.json", "r") as f1:
    data = json.load(f1)

print(type(data))
with open("Testdata.yml", "w") as f2:
    yaml.dump(data, f2)
