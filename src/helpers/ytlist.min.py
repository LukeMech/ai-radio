import json

with open('ytlist.json', 'r') as file:
    ytlist = json.load(file)

formatted_data = []
for item in ytlist:
    video_id = item[1].split('=')[-1].split('/')[-1]
    multiplier = 1
    new_flag = 0
    eurovision_country = 0
    if len(item) >= 3:  # Checking if item has index 2
        multiplier = item[2].get("multiplier", 1)
        if(item[2].get("new", 0)):
            new_flag = 1
        else: new_flag = 0
        eurovision_country = item[2].get("eurovision", 0)

    formatted_item = [video_id, {"m": multiplier, "n": new_flag, "ev": eurovision_country}]
    formatted_data.append(formatted_item)

stringData = json.dumps(formatted_data)
out = stringData.replace(" ", "")

with open('ytlist.min.json', 'w') as outfile:
    outfile.write(out)