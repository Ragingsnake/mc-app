import os
import requests
from flask import Flask

app = Flask(__name__)

STORY_URL = os.environ.get('STORY_SERVICE_URL', 'http://story-service:5003')

@app.route('/')
def index():
    try:
        res = requests.get(f"{STORY_URL}/story").json()
        story = res.get('story', 'Once upon a time...')
    except:
        story = "Error fetching story"
        
    return f"<h1>Random Story</h1><p>{story}</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
