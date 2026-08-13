import os
import json
import requests
import redis
from flask import Flask, request, jsonify

app = Flask(__name__)

GENERATOR_URL = os.environ.get('STORY_ORCHESTRATOR_URL', 'http://story-orchestrator:5015')
DB_URL = os.environ.get('STORY_DB_SERVICE_URL', 'http://story-db-service:5002')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')

cache = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

@app.route('/api/generate', methods=['GET', 'POST'])
def generate_story():
    res = requests.post(f"{GENERATOR_URL}/generate", json=request.json if request.is_json else {})
    return jsonify(res.json()), res.status_code

@app.route('/api/status/<corr_id>', methods=['GET'])
def check_status(corr_id):
    res = requests.get(f"{GENERATOR_URL}/status/{corr_id}")
    return jsonify(res.json()), res.status_code

@app.route('/api/stories', methods=['POST'])
def publish_story():
    data = request.json
    res = requests.post(f"{DB_URL}/api/db/stories", json=data)

    try:
        cache.delete('all_stories')
    except:
        pass
    return jsonify(res.json()), res.status_code

@app.route('/api/stories', methods=['GET'])
def get_all_stories():
    try:
        cached = cache.get('all_stories')
        if cached:
            return jsonify(json.loads(cached))
    except:
        pass

    res = requests.get(f"{DB_URL}/api/db/stories")
    
    try:
        cache.setex('all_stories', 60, json.dumps(res.json()))
    except:
        pass
        
    return jsonify(res.json()), res.status_code

@app.route('/api/stories/<int:story_id>/rate', methods=['POST'])
def rate(story_id):
    res = requests.post(f"{DB_URL}/api/db/stories/{story_id}/rate", json=request.json)
    try:
        cache.delete('all_stories') # Invalidate cache
    except:
        pass
    return jsonify(res.json()), res.status_code

@app.route('/api/stories/<int:story_id>/comment', methods=['POST'])
def comment(story_id):
    res = requests.post(f"{DB_URL}/api/db/stories/{story_id}/comment", json=request.json)
    try:
        cache.delete('all_stories') # Invalidate cache
    except:
        pass
    return jsonify(res.json()), res.status_code

@app.route('/health/live', methods=['GET'])
def health_live():
    return jsonify({"status": "alive"}), 200

@app.route('/health/ready', methods=['GET'])
def health_ready():
    try:
        cache.ping()
        return jsonify({"status": "ready"}), 200
    except:
        return jsonify({"status": "unready"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
