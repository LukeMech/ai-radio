import re, time
from subprocess import run

log_path = "tmp/localhost.run.log"
# Regular expression pattern to search for
pattern = r'(https?:\/\/.*?\.life)'
used = []

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
    with open("website.url", "w") as file:
        file.write(url)
    print(f"{url} saved to 'website.url' file.", flush=True)

def git_add_commit_push():
    run("cd .. && git add src/website.url", shell=True)
    run("cd .. && git commit -m 'Update website URL'", shell=True)
    run("cd .. && git push", shell=True)
    print("URL updated successfully.", flush=True)

if __name__ == "__main__":
    while True:
        result = fetch_until_pattern_found()
        if result:
            save_url_to_file(result)
            git_add_commit_push()