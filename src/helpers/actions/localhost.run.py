import re, time, os, json, requests, socketio
sio = socketio.Client()

log_path = "tmp/localhost.run.log"
aws_urlPath = "awsfun.url"
token = os.environ['AWS_TOKEN']
# Regular expression pattern to search for
pattern = r'(https?:\/\/.*?\.life)'
used = []

@sio.event
def connect():
    print('Localhost.run.py connected locally') 

sio.connect('http://127.0.0.1:8000')

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

def push_to_connected_clients(url):
    sio.emit('urlChanged', {'url': url, 'token': token})

def push_to_aws(url):
    with open(aws_urlPath, "r") as file:
        content = file.read()
    body_data = {'url': url}
    headers = {
        'authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    r = requests.post(content + '/urlPush', headers=headers, data=json.dumps(body_data))
    if r.ok: print(f"Successfully pushed {url} to AWS", flush=True)
    else: print(f"Failed to push {url} to AWS", flush=True)

if __name__ == "__main__":
    while True:
        result = fetch_until_pattern_found()
        if result:
            push_to_connected_clients(result)
            push_to_aws(result)
