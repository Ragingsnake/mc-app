import os
import json
import time
import threading
import redis
import google.generativeai as genai
from flask import Flask, jsonify

app = Flask(__name__)

# Configure Redis
REDIS_BROKER_HOST = os.environ.get("REDIS_BROKER_HOST", "redis-broker")
REDIS_PORT = 6379
ALL_MODEL_OUT = False
broker = redis.Redis(host=REDIS_BROKER_HOST, port=REDIS_PORT, db=0)

# Configure Gemini
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip().strip('"').strip("'")
if API_KEY:
    genai.configure(api_key=API_KEY)

# Use flash for speed
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    model = None
    print(f"Failed to initialize model: {e}")

import requests

import json

def enhance_story(payload):
    if not API_KEY:
        return payload
        
    try:
        events = payload.get("story_events", [])
        if not events:
            return payload

        simplified_events = []
        for ev in events:
            simplified_events.append({
                "time": ev.get("time", ""),
                "text": ev.get("text", ""),
                "chat_lines": ev.get("chat_lines", []),
                "protagonists": ev.get("protagonists", [])
            })

        prompt = (
            "You are an expert Minecraft storyteller. I am giving you a JSON array "
            "of events from a procedural Minecraft survival game. "
            "Your job is to rewrite the 'text' (narrative) and 'chat_lines' (dialogue) "
            "to make the story more cohesive, dramatic, and entertaining. "
            "Improve the flow between paragraphs.\n\n"
            "CRITICAL CHARACTER RULES:\n"
            "Each event has a 'protagonists' list defining the characters present and their 'personality' traits. "
            "You MUST keep these exact characters and NEVER hallucinate new party members. "
            "When rewriting dialogue, you MUST perfectly match the character's 'personality' trait (e.g., toxic_sweat, loot_goblin, sleepy, confused_noob) and preserve the original dialogue as much as possible.\n\n"
            "OUTPUT RULES:\n"
            "1. Output ONLY a valid JSON array.\n"
            "2. The output array MUST have the exact same number of items as the input.\n"
            "3. Keep the 'time' field exactly the same for each event.\n"
            "4. For 'chat_lines', each item is an object with 'speaker' and 'message'. You can modify the messages or add new lines to make the characters sound more alive.\n\n"
            f"INPUT JSON:\n{json.dumps(simplified_events)}"
        )

        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": 32768
            }
        }
        
        proxies = {
            "http": "http://host.docker.internal:3128",
            "https": "http://host.docker.internal:3128",
        }

        models_to_try = [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash",
            "gemini-3.6-flash",
            "gemini-3.7-flash"
        ]
        
        full_text = ""
        success = False
        
        for model_name in models_to_try:
            print(f"Attempting AI enhancement with model: {model_name}...", flush=True)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?alt=sse&key={API_KEY}"
            
            try:
                resp = requests.post(url, headers=headers, json=data, proxies=proxies, timeout=120, stream=True)
                resp.raise_for_status()
                
                full_text = ""
                for line in resp.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            try:
                                chunk = json.loads(decoded_line[6:])
                                text_part = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                full_text += text_part
                            except Exception:
                                pass
                
                if full_text:
                    success = True
                    print(f"Successfully generated with {model_name}", flush=True)
                    break
                    
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code in (429, 503):
                    print(f"Model {model_name} hit {e.response.status_code} (Quota Exceeded/Overloaded). Falling back to next model...", flush=True)
                    continue
                else:
                    print(f"Model {model_name} failed with HTTPError: {e}. Falling back to next model...", flush=True)
                    continue
            except Exception as e:
                print(f"Model {model_name} failed with error: {e}. Falling back to next model...", flush=True)
                continue
                
        if not success:
            raise Exception("All fallback models in the chain failed or exceeded quota.")
            
        ai_text = full_text
        
        if ai_text:
            try:
                ai_events = json.loads(ai_text)
                if isinstance(ai_events, list) and len(ai_events) == len(events):
                    for i in range(len(events)):
                        events[i]["text"] = ai_events[i].get("text", events[i]["text"])
                        events[i]["chat_lines"] = ai_events[i].get("chat_lines", events[i]["chat_lines"])
                    print("Successfully enhanced story with AI.", flush=True)
                else:
                    print("AI JSON length mismatch.", flush=True)
            except Exception as e:
                print(f"Failed to parse AI JSON: {e}", flush=True)
            
    except Exception as e:
        print(f"AI enhancement failed (falling back to raw): {e}", flush=True)
        
    return payload

def consumer_loop():
    while True:
        try:
            broker.xgroup_create('stream:ai:request', 'ai-group', id='0', mkstream=True)
        except:
            pass
            
        try:
            messages = broker.xreadgroup('ai-group', 'ai-consumer', {'stream:ai:request': '>'}, count=1, block=2000)
            if messages:
                for stream, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        payload = json.loads(msg_data[b'payload'].decode('utf-8'))
                        
                        # Enhance the payload
                        enhanced_payload = enhance_story(payload)
                        broker.xadd('stream:db:request', {'payload': json.dumps(enhanced_payload)})
                        broker.xack('stream:ai:request', 'ai-group', msg_id)

        except Exception as e:
            print(f"Error in ai-enhancer loop: {e}", flush=True)
            time.sleep(2)

threading.Thread(target=consumer_loop, daemon=True).start()

@app.route('/health/live', methods=['GET'])
def live(): return jsonify({"status": "alive"}), 200

@app.route('/health/ready', methods=['GET'])
def ready(): return jsonify({"status": "ready"}), 200

if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=5016)
