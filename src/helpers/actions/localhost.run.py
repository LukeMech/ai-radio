import re, time, os
from subprocess import run

log_path = "tmp/localhost.run.log"
# Regular expression pattern to search for
pattern = r'(https?:\/\/.*?\.life)'
used = []

num = 0
files = os.listdir('.')
weburlpattern = r'website\.(\d+)\.url'
for filename in files:
    # Match the filename pattern
    match = re.match(weburlpattern, filename)
    if match:
        # Extract the number from the filename
        number = match.group(1)
        print("Previous file number: ", number)
        num = int(number) + 1
        if(num > 9): num = 0
        
# Function to fetch the file and search for the pattern
def search_local_file():
    try:
        with open(log_path, "r") as file:
            content = file.read()
        # Do not use same url again
        for inUse in used:
            content = content.replace(inUse, "")
        matches = re.findall(pattern, content)
        if matches:
            used.append(matches[0])
            return matches[0]
    except:
        return None

# Function to periodically fetch the file until the pattern is found
def fetch_until_pattern_found():
    while True:
        result = search_local_file()
        if result:
            return result
        time.sleep(2)

def save_url_to_file(url):
    global num
    with open(f"website.{num}.url", "w") as file:
        file.write(url)
    if num>9: num = 0;
    if num==0: delnum = 9
    else: delnum = num-1
    if(os.path.exists(f"website.{delnum}.url")): os.remove(f"website.{delnum}.url")
    num+=1
    print(f"{url} saved to 'website.url' file.", flush=True)

def git_add_commit_push():
    run("cd .. && git pull", shell=True)
    run("cd .. && git add .", shell=True)
    run("cd .. && git commit -m 'Update website URL'", shell=True)
    run("cd .. && git push", shell=True)
    print("URL updated successfully.", flush=True)

if __name__ == "__main__":
    while True:
        result = fetch_until_pattern_found()
        if result:
            save_url_to_file(result)
            git_add_commit_push()
