import json

with open('ytlist.json', 'r') as file:
    ytlist = json.load(file)

formatted_data = [[item[1].split('=')[-1].split('/')[-1], item[2]["multiplier"]] for item in ytlist]
stringData = json.dumps(formatted_data)
out = stringData.replace(" ", "")

with open('ytlist.min.json', 'w') as outfile:
    outfile.write(out)