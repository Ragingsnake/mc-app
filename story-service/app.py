import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

CHARACTER_URL = os.environ.get('CHARACTER_SERVICE_URL', 'http://character-service:5001')
ACTION_URL = os.environ.get('ACTION_SERVICE_URL', 'http://action-service:5002')

@app.route('/story')
def get_story():
    try:
        char_res = requests.get(f"{CHARACTER_URL}/character").json()
        character = char_res.get('character', 'Someone')
    except:
        character = "Someone"
        
    try:
        act_res = requests.get(f"{ACTION_URL}/action").json()
        action = act_res.get('action', 'did something')
    except:
        action = "did something"
        
    story = f"One day, {character.lower()} decided it was time for an adventure. Without hesitation, they {action}. It was truly a memorable moment!"
    
    return jsonify({"story": story})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
