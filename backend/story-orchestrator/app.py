import os, requests, uuid, json, redis
from flask import Flask, jsonify, request
import threading

app = Flask(__name__)
is_healthy = True

broker = redis.Redis(host=os.environ.get('REDIS_BROKER_HOST', 'redis-broker'), port=6379, db=0)
cache = redis.Redis(host=os.environ.get('REDIS_HOST', 'redis'), port=6379, db=0)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json or {}
        corr_id = str(uuid.uuid4())
        data['correlation_id'] = corr_id
        data['story_parts'] = []
        data['stages_count'] = 0
        
        # Publish to the first stream in the pipeline
        broker.xadd('stream:character:request', {'payload': json.dumps(data)})
        
        return jsonify({"status": "processing", "correlation_id": corr_id})
    except Exception as e:
        return jsonify({"story": "Error starting generation", "error": str(e)}), 500

@app.route('/status/<corr_id>', methods=['GET'])
def status(corr_id):
    try:
        result = cache.get(f"story:{corr_id}")
        if result:
            return jsonify({"status": "done", "story": json.loads(result.decode('utf-8'))})
        else:
            return jsonify({"status": "processing"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    if is_healthy:
        try:
            broker.ping()
            cache.ping()
            return jsonify({"status": "healthy"}), 200
        except:
            return jsonify({"status": "unhealthy", "reason": "redis down"}), 500
    else:
        return jsonify({"status": "unhealthy"}), 500

@app.route('/health/live', methods=['GET'])
def liveness():
    if is_healthy:
        return jsonify({"status": "alive"}), 200
    else:
        return jsonify({"status": "dead"}), 500

@app.route('/health/ready', methods=['GET'])
def readiness():
    if is_healthy:
        try:
            broker.ping()
            cache.ping()
            return jsonify({"status": "ready"}), 200
        except:
            return jsonify({"status": "unready"}), 500
    else:
        return jsonify({"status": "unready"}), 500

@app.route('/break', methods=['POST'])
def break_app():
    global is_healthy
    is_healthy = False
    return jsonify({"message": "App broken."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5015)
