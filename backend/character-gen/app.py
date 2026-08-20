import random, json, os, threading, time, redis, copy
from flask import Flask, jsonify

app = Flask(__name__)
is_healthy = True
broker = redis.Redis(host=os.environ.get('REDIS_BROKER_HOST', 'redis-broker'), port=6379, db=0)

def consumer_loop():
    while True:
        try: broker.xgroup_create('stream:character:request', 'character-group', id='0', mkstream=True)
        except: pass
        try:
            messages = broker.xreadgroup('character-group', 'character-consumer', {'stream:character:request': '>'}, count=1, block=2000)
            if messages:
                for stream, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        payload = json.loads(msg_data[b'payload'].decode('utf-8'))
                        num_prots = random.randint(1, 5)
                        
                        names_pool = [
                            {"name": "CharlieKirk", "personality": "normal"},
                            {"name": "xX_NoobSlayer_Xx", "personality": "toxic_sweat"},
                            {"name": "SpeedRunner_Dream", "personality": "speedrunner"},
                            {"name": "GamerNoob", "personality": "confused_noob"},
                            {"name": "SaltGamer", "personality": "salty"},
                            {"name": "xX_LootGoblin_Xx", "personality": "loot_goblin"},
                            {"name": "MineCraftGamer69", "personality": "meme_gamer"},
                            {"name": "GeorgeFloyd", "personality": "hood_angry"},
                            {"name": "Chauvin", "personality": "salty_cop"},
                            {"name": "DreamyBull", "personality": "dreamy_bull"},
                            {"name": "ExposeMe", "personality": "expose_me"},
                            {"name": "TomPearl", "personality": "tom_pearl"},
                            {"name": "RedstoneGod", "personality": "debater"},
                            {"name": "DiamondMiner", "personality": "loot_goblin"},
                            {"name": "TechnoFan", "personality": "toxic_sweat"}
                        ]
                        random.shuffle(names_pool)
                        
                        prots = []
                        chat_lines = []
                        for i in range(num_prots):
                            p_info = names_pool[i]
                            
                            goals_pool = [
                                "Find 10 Diamonds", "Build a dirt hut", "Troll other players",
                                "Defeat the Ender Dragon", "Steal from chests", "Become the richest player",
                                "Speedrun to the Nether"
                            ]
                            
                            starter_tools = ["wooden_sword", "wooden_pickaxe", "stone_axe"]
                            starter_food = ["bread", "apple", "cooked_beef"]
                            
                            prots.append({
                                "name": p_info["name"],
                                "health": 20,
                                "inventory": [random.choice(starter_tools), random.choice(starter_food)],
                                "location": "Overworld Spawn",
                                "creative_mode": False,
                                "status": "alive",
                                "personality": p_info["personality"],
                                "goal": random.choice(goals_pool),
                                "relationships": {}
                            })
                            chat_lines.append({"speaker": "System", "message": f"{p_info['name']} joined the game"})
                        
                        # Populate default relationships (friction starts immediately!)
                        for p in prots:
                            for other in prots:
                                if p["name"] != other["name"]:
                                    p["relationships"][other["name"]] = random.randint(-35, 10)
                                    
                        # Set pre-established relationships
                        extra_texts = []
                        
                        # GeorgeFloyd vs Chauvin
                        if any(p["name"] == "GeorgeFloyd" for p in prots) and any(p["name"] == "Chauvin" for p in prots):
                            for p in prots:
                                if p["name"] == "GeorgeFloyd": p["relationships"]["Chauvin"] = -60
                                if p["name"] == "Chauvin": p["relationships"]["GeorgeFloyd"] = -60
                            extra_texts.append("Chauvin and GeorgeFloyd spawned with an established rivalry over server claim block rules.")
                            
                        # CharlieKirk vs xX_NoobSlayer_Xx
                        if any(p["name"] == "CharlieKirk" for p in prots) and any(p["name"] == "xX_NoobSlayer_Xx" for p in prots):
                            for p in prots:
                                if p["name"] == "CharlieKirk": p["relationships"]["xX_NoobSlayer_Xx"] = -40
                                if p["name"] == "xX_NoobSlayer_Xx": p["relationships"]["CharlieKirk"] = -40
                            extra_texts.append("CharlieKirk and xX_NoobSlayer_Xx were already arguing in spawn over PvP settings.")
                            
                        # DreamyBull vs ExposeMe
                        if any(p["name"] == "DreamyBull" for p in prots) and any(p["name"] == "ExposeMe" for p in prots):
                            for p in prots:
                                if p["name"] == "DreamyBull": p["relationships"]["ExposeMe"] = -45
                                if p["name"] == "ExposeMe": p["relationships"]["DreamyBull"] = -45
                            extra_texts.append("DreamyBull and ExposeMe eyed each other suspiciously from the start.")
                            
                        # GamerNoob vs SaltGamer
                        if any(p["name"] == "GamerNoob" for p in prots) and any(p["name"] == "SaltGamer" for p in prots):
                            for p in prots:
                                if p["name"] == "GamerNoob": p["relationships"]["SaltGamer"] = -35
                                if p["name"] == "SaltGamer": p["relationships"]["GamerNoob"] = -35
                            extra_texts.append("SaltGamer was already annoyed by GamerNoob's constant basic questions.")
                            
                        # RedstoneGod and TechnoFan
                        if any(p["name"] == "RedstoneGod" for p in prots) and any(p["name"] == "TechnoFan" for p in prots):
                            for p in prots:
                                if p["name"] == "RedstoneGod": p["relationships"]["TechnoFan"] = 35
                                if p["name"] == "TechnoFan": p["relationships"]["RedstoneGod"] = 35
                            extra_texts.append("RedstoneGod and TechnoFan immediately agreed to share base design plans.")

                        s_names = ", ".join([p["name"] for p in prots])
                        extra_text = " " + " ".join(extra_texts) if extra_texts else ""
                        text = f"The adventure begins! {s_names} spawned into a brand new survival world, punching trees and crafting basic tools.{extra_text}"
                        
                        payload["protagonists"] = prots
                        payload["intruders"] = []
                        payload["day"] = 1
                        payload["time_of_day"] = "Morning"
                        payload["memory_log"] = [text]
                        payload["goal_status"] = "in_progress"
                        
                        payload["story_events"] = [{
                            "text": text,
                            "chat_lines": chat_lines,
                            "time": "Day 1 (Morning)",
                            "protagonists": copy.deepcopy(prots)
                        }]
                        payload["next_stage"] = "scenario"
                        
                        broker.xadd('stream:scenario:request', {'payload': json.dumps(payload)})
                        broker.xack('stream:character:request', 'character-group', msg_id)
        except Exception as e:
            print(f"Error in character-gen: {e}")
            time.sleep(2)

threading.Thread(target=consumer_loop, daemon=True).start()
@app.route('/health/live', methods=['GET'])
def live(): return jsonify({"status": "alive"}), 200
@app.route('/health/ready', methods=['GET'])
def ready(): return jsonify({"status": "ready"}), 200
if __name__ == '__main__': app.run(host='0.0.0.0', port=5011)
