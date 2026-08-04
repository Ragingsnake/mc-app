import random
from flask import Flask, jsonify

app = Flask(__name__)

characters = ["A brave knight", "A wise wizard", "A cunning rogue", "A friendly dragon"]

@app.route('/character')
def get_character():
    return jsonify({"character": random.choice(characters)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
