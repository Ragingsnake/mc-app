import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Using SQLite for local dev, can easily swap to Postgres for Helm
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///stories.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    ratings_sum = db.Column(db.Integer, default=0)
    ratings_count = db.Column(db.Integer, default=0)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    user = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer, nullable=True)

with app.app_context():
    db.create_all()

import threading, time, redis, json

broker = redis.Redis(host=os.environ.get('REDIS_BROKER_HOST', 'redis-broker'), port=6379, db=0)
cache = redis.Redis(host=os.environ.get('REDIS_HOST', 'redis'), port=6379, db=0)

def consumer_loop():
    
    
    with app.app_context():
        while True:
            try:
                broker.xgroup_create("stream:db:request", "db_group", id="0", mkstream=True)
            except Exception as e:
                pass

            try:
                messages = broker.xreadgroup("db_group", "db_consumer", {"stream:db:request": ">"}, count=1, block=1000)
                if messages:
                    for stream, msg_list in messages:
                        for msg_id, msg_data in msg_list:
                            payload = json.loads(msg_data[b'payload'].decode('utf-8'))
                            
                            try:
                                # Cache final output for orchestrator
                                corr_id = payload.get('correlation_id')
                                if corr_id:
                                    cache.set(f"story:{corr_id}", json.dumps(payload), ex=3600)
                                corr_id = payload.get('correlation_id')
                                if corr_id:
                                    cache.set(f"story:{corr_id}", json.dumps(payload), ex=3600)
                            except Exception as e:
                                print(f"Error saving to DB/Cache: {e}")
                                
                            broker.xack("stream:db:request", "db_group", msg_id)
            except Exception as e:
                print("Error reading from stream:", e)
                time.sleep(1)

threading.Thread(target=consumer_loop, daemon=True).start()

@app.route('/api/db/stories', methods=['GET', 'POST'])
def manage_stories():
    if request.method == 'POST':
        data = request.json
        new_story = Story(author=data.get('author', 'Anonymous'), content=data.get('content', ''))
        db.session.add(new_story)
        db.session.commit()
        return jsonify({"success": True, "id": new_story.id})

    stories = Story.query.all()
    result = []
    for s in stories:
        avg = s.ratings_sum / s.ratings_count if s.ratings_count > 0 else 0
        comments = Comment.query.filter_by(story_id=s.id).all()
        result.append({
            "id": s.id,
            "author": s.author,
            "content": s.content,
            "avg_rating": round(avg, 2),
            "comments": [{"user": c.user, "text": c.text, "rating": c.rating} for c in comments]
        })
    return jsonify(result)

@app.route('/api/db/stories/<int:story_id>/rate', methods=['POST'])
def rate_story(story_id):
    data = request.json
    story = Story.query.get_or_404(story_id)
    story.ratings_sum += int(data['rating'])
    story.ratings_count += 1
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/db/stories/<int:story_id>/comment', methods=['POST'])
def add_comment(story_id):
    data = request.json
    new_comment = Comment(story_id=story_id, user=data.get('user', 'Anon'), text=data.get('text'), rating=data.get('rating'))
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/health/live', methods=['GET'])
def health_live():
    return jsonify({"status": "alive"}), 200

@app.route('/health/ready', methods=['GET'])
def health_ready():
    try:
        broker.ping()
        cache.ping()
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        return jsonify({"status": "unready", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
