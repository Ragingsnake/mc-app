import random, json, os, threading, time, redis, copy
from flask import Flask, jsonify

app = Flask(__name__)
is_healthy = True
broker = redis.Redis(host=os.environ.get('REDIS_BROKER_HOST', 'redis-broker'), port=6379, db=0)

def process_payload(data):
    prots = data.get("protagonists", [])
    story_events = data.get("story_events", [])
    story = ""
    chat_lines = []
    
    alive_prots = [p for p in prots if p["status"] == "alive"]
    current_time_str = advance_time(data)
    
    if not alive_prots:
        story += "With the final player's death, the server fell silent. The blocky world remained, completely empty and devoid of life."
        chat_lines.append({"speaker": "System", "message": "GAME OVER. Everyone died or left."})
    else:
        survivors = ", ".join([p["name"] for p in alive_prots])
        ending = random.choice([
            "They finally found the End Portal, diving in and slaying the Ender Dragon after an epic final showdown in the void.",
            "They managed to construct the Wither, barely defeating it and claiming the Nether Star for a beacon.",
            "They found an Ancient City and snuck past the Warden, looting chests of enchanted apples and escaping into the sunrise.",
            "Tired of fighting, they returned to spawn and built a massive, peaceful castle to live out their days."
        ])
        story += f"Against all odds, the surviving players achieved their ultimate goal. {ending}"
        chat_lines.append({"speaker": "System", "message": f"VICTORY! {survivors} conquered the server."})
        
    story_events.append({
        "text": story,
        "chat_lines": chat_lines,
        "time": current_time_str,
        "protagonists": copy.deepcopy(prots)
    })
    data["story_events"] = story_events
    
    # Compile full story for database compatibility
    full_story = ""
    for ev in story_events:
        if ev.get("text"):
            full_story += ev["text"] + "\n\n"
        for line in ev.get("chat_lines", []):
            if line["speaker"] == "System":
                full_story += f"[System] {line['message']}\n\n"
            else:
                full_story += f"<{line['speaker']}> {line['message']}\n\n"
                
    data["story"] = full_story
    data["next_stage"] = "db"
    return data

def advance_time(data):
    day = data.get("day", 1)
    tod = data.get("time_of_day", "Morning")
    if tod == "Morning":
        tod = "Afternoon"
    elif tod == "Afternoon":
        tod = "Night"
    elif tod == "Night":
        tod = "Morning"
        day += 1
    data["day"] = day
    data["time_of_day"] = tod
    return f"Day {day} ({tod})"

def consumer_loop():
    while True:
        try: broker.xgroup_create("stream:ending:request", "ending_group", id="0", mkstream=True)
        except: pass
        try:
            messages = broker.xreadgroup("ending_group", "ending_consumer", {"stream:ending:request": ">"}, count=1, block=1000)
            if messages:
                for stream, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        payload = json.loads(msg_data[b'payload'].decode('utf-8'))
                        result = process_payload(payload)
                        broker.xadd("stream:db:request", {"payload": json.dumps(result)})
                        broker.xack("stream:ending:request", "ending_group", msg_id)
        except Exception as e:
            print(f"Error in endings-gen: {e}")
            time.sleep(1)

threading.Thread(target=consumer_loop, daemon=True).start()
@app.route('/health/live', methods=['GET'])
def live(): return jsonify({"status": "alive"}), 200
@app.route('/health/ready', methods=['GET'])
def ready(): return jsonify({"status": "ready"}), 200
if __name__ == '__main__': app.run(host='0.0.0.0', port=5014)
