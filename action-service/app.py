import random
from flask import Flask, jsonify

app = Flask(__name__)

actions = ["found a hidden treasure", "saved the village", "cast a powerful spell", "went to sleep"]

@app.route('/action')
def get_action():
    return jsonify({"action": random.choice(actions)})

def sad():
    return 5

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)