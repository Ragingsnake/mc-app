import random, json, os, threading, time, redis, copy
from flask import Flask, jsonify

app = Flask(__name__)
is_healthy = True
broker = redis.Redis(host=os.environ.get('REDIS_BROKER_HOST', 'redis-broker'), port=6379, db=0)

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

def get_dialogue(personality, action, context=None):
    context = (context or "").lower()
    
    options = {
        "normal": {
            "discover": [
                f"I found a {context}.",
                f"Look at this {context} we found.",
                f"There's a {context} over here."
            ],
            "spotted_intruder": [
                f"Watch out, there's a {context}.",
                f"I see a {context} nearby.",
                f"Be careful of that {context}."
            ],
            "combat_damage": [
                f"I'm taking damage from this {context}!",
                f"Ouch, that hurt.",
                f"Need some help here!"
            ],
            "combat_win": [
                "Got 'em.",
                "That's taken care of.",
                "Let's move on."
            ],
            "accident": [
                "I fell down.",
                "Took some fall damage.",
                "Whoops, fell off."
            ]
        },
        "hood_angry": {
            "discover": [
                f"yo cuh check out this {context}, deadass looks weird af.",
                f"man what the fuck is this {context} doing on my block?",
                f"i ain't never seen no {context} round my ends."
            ],
            "spotted_intruder": [
                f"who this {context} think they is stepping on my turf??",
                f"yo this {context} boutta get popped fr.",
                f"square up {context}, ain't nobody disrespect me."
            ],
            "combat_damage": [
                f"WTF! this {context} actually hitting me bro!",
                f"man this {context} got hands, chill out!",
                f"nah they wildin! get this {context} off me!"
            ],
            "combat_win": [
                "smoked that fool.",
                "don't ever step to me again.",
                "easy clap, left 'em in the dirt."
            ],
            "accident": [
                "man who put this cliff here bruh wtf.",
                "tripped on god, my legs broken.",
                "this gravity ain't right cuh."
            ]
        },
        "toxic_sweat": {
            "discover": [
                f"found a {context} you trash noobs. get over here.",
                f"speedrunning this {context}. try to keep up you slow shits.",
                f"easy {context} loot. don't touch anything."
            ],
            "spotted_intruder": [
                f"wtf is that {context} doing. i'm gonna ez drop him.",
                f"free kill spotted. {context} is absolute trash.",
                f"look at this garbage {context} standing there. ez."
            ],
            "combat_damage": [
                f"shit! hacker! this {context} has reach wtf!",
                f"unbelievable reach hacks on this {context}. check my logs.",
                f"dude i'm lagging wtf he's hitting me through blocks!"
            ],
            "combat_win": [
                "trash mob. ez drop. get good kid.",
                "lmao you bots actually struggled with that? ez.",
                "sit down kid. uninstall."
            ],
            "accident": [
                "fucking lag pushed me off. server is trash.",
                "admin fix your server wtf i fell.",
                "input lag ate my jump wtf."
            ]
        },
        "speedrunner": {
            "discover": [
                f"speedrunning this {context}. no time to waste.",
                f"this {context} coordinates are perfect. god seed.",
                f"routing through the {context} to save 3 seconds."
            ],
            "spotted_intruder": [
                f"ignore that {context}. speedrun routing doesn't need this.",
                f"skip the {context}. it's a time loss.",
                f"wasting ticks looking at that {context}."
            ],
            "combat_damage": [
                "shit i need to clutch with water bucket now!",
                "taking damage, resetting run if i drop below 3 hearts.",
                f"this {context} is ruining my splits!"
            ],
            "combat_win": [
                "dream luck activated. let's go.",
                "perfect drop. split is green.",
                "sub-10 minute run is still alive."
            ],
            "accident": [
                "reset the run. i missed the block clutch.",
                "failed the block jump. starting a new seed.",
                "time loss from fall damage. terrible splits."
            ]
        },
        "confused_noob": {
            "discover": [
                f"wait wtf is this {context} thing? is it safe?",
                f"guys i found a weird {context}. is this a house?",
                f"ooh glowing blocks in this {context}! can i eat them?"
            ],
            "spotted_intruder": [
                f"guys there is a weird {context} looking at me... how do i hit it?",
                f"is that {context} friendly? it's moving towards me help",
                f"what does a {context} do? is it a boss?"
            ],
            "combat_damage": [
                "help help help how do i block with shield shit!",
                "my screen is red! why is my screen red help!",
                "it's biting me wtf wtf wtf help!"
            ],
            "combat_win": [
                "yay i survived somehow lol.",
                "we won! did i do good guys?",
                "i got a block of dirt from it! cool!"
            ],
            "accident": [
                "how do i turn off fall damage guys? i fell.",
                "i fell in lava! water water water! where is water!",
                "which key makes me crouch? i walked off a cliff."
            ]
        },
        "salty": {
            "discover": [
                f"great. another useless {context}. garbage seed.",
                f"this {context} looks completely empty. waste of time.",
                f"spawned in a trash {context}. thanks notch."
            ],
            "spotted_intruder": [
                f"why does the game spawn this {context} trash now. fucking stupid.",
                f"intruder {context} spawned. typical admin abuse.",
                f"great, a {context}. as if this server wasn't bad enough."
            ],
            "combat_damage": [
                "this game mechanics are absolute shit. i'm taking damage through walls.",
                f"broken hitboxes wtf. i clearly blocked that {context}.",
                "fucking stupid game. shield doesn't even work."
            ],
            "combat_win": [
                "whatever. drop was garbage anyway.",
                "i got a piece of rotten flesh. exciting.",
                "loot is absolute trash. wasted durability."
            ],
            "accident": [
                "fucking broken game. i'm logging off soon.",
                "fell through the block. client is buggy as hell.",
                "uninstalled. gravity is bugged."
            ]
        },
        "loot_goblin": {
            "discover": [
                f"dibs on all the chest loot in this {context} mine mine mine.",
                f"i see chests in that {context}. back off guys.",
                f"gold blocks in the {context}! i'm rich!"
            ],
            "spotted_intruder": [
                f"is that {context} guarding a chest? get out of the way.",
                f"that {context} has drops. i'm taking them all.",
                "kill it quick, i want the loot."
            ],
            "combat_damage": [
                "my precious armor is taking damage shit!",
                f"don't let the {context} break my diamond boots!",
                "hey i'm taking damage! cover my inventory!"
            ],
            "combat_win": [
                "loot time! give me the drops now.",
                "my inventory is full of precious items yes.",
                "gimme the diamonds from that kill."
            ],
            "accident": [
                "fuck fell in a hole while looking for ores.",
                "fell down trying to get that coal block.",
                "cliff fell on me while i was mining gold."
            ]
        },
        "meme_gamer": {
            "discover": [
                f"yo check this {context} out. we gaming today.",
                f"we found the {context} boys. sheesh.",
                f"is this the backrooms or just a {context}?"
            ],
            "spotted_intruder": [
                f"mom come pick me up i'm scared there's a {context}.",
                f"run for your lives, it's a wild {context}!",
                f"bruh moment. {context} spotted."
            ],
            "combat_damage": [
                "oof size large. that hurt.",
                f"my health bar is not vibing with this {context}.",
                "emotional damage from that hit."
            ],
            "combat_win": [
                "we take those. absolute win.",
                "gg ez no re.",
                "clutched it. we are gaming."
            ],
            "accident": [
                "mission failed successfully. i fell.",
                "bruh i fell. press f to pay respects.",
                "my brain lag caused that fall. rip."
            ]
        },
        "chill": {
            "discover": [
                f"found a nice peaceful {context} let's chill here and mine.",
                f"this {context} is really cozy. let's build camp.",
                f"nice spot at this {context}. let's take a break."
            ],
            "spotted_intruder": [
                f"hey guys there's a scary looking {context} nearby.",
                f"watch out, there is a {context} wandering around.",
                f"stay back, we have a {context} visitor."
            ],
            "combat_damage": [
                f"ouch that hurt a lot. this {context} is tough.",
                "man that hit took some hearts. be careful.",
                f"this {context} is hitting pretty hard. watch your hp."
            ],
            "combat_win": [
                "phew we survived that thank goodness.",
                "glad that's over. let's heal up.",
                "good team effort guys."
            ],
            "accident": [
                "oh no i fell down. be careful guys.",
                "clumsy me, i fell off. i'll head back up.",
                "just a small scratch from falling."
            ]
        },
        "dreamy_bull": {
            "discover": [
                f"yo this {context} is clean as fuck. i'm about to blow up! omg",
                f"omg yes this {context}... i'm about to burst!",
                f"this {context} is so good... i'm about to nut..."
            ],
            "spotted_intruder": [
                f"yo that {context} is wild... i'm gonna burst... oh",
                f"wtf is that {context} omg it's so big...",
                f"that {context} looking at me makes me wanna blow up..."
            ],
            "combat_damage": [
                "ahhh! it hurts so good wtf! help me",
                "omg yes hit me more... wait no i'm low health!",
                "ahhh it hurts so good help me!"
            ],
            "combat_win": [
                "phew. i actually did it... i came out alive lol.",
                "i clutched it omg yes yes yes!",
                "the beast is dead... i blew it up..."
            ],
            "accident": [
                "fuck! i fell! i'm about to rage lol",
                "gravity got me... i'm about to burst in anger!",
                "nooo i fell... omg i'm so wet from the water block"
            ]
        },
        "expose_me": {
            "discover": [
                f"hello everybody my name is markiplier and is that a {context}?? expose me expose me wtf!",
                f"hello everybody my name is markiplier and this {context} is a scam expose me expose me!",
                f"is that the bite of 87?? no it's a {context} expose me expose me!"
            ],
            "spotted_intruder": [
                f"was that the bite of 87?? wtf that {context} is scary expose me expose me!",
                f"hello everybody my name is markiplier and we have a rogue {context} expose me expose me!",
                f"exclusive footage of {context} hacker spotted expose me expose me!"
            ],
            "combat_damage": [
                f"ahhh expose me expose me he is hitting me hello everybody my name is markiplier and i am dying",
                f"this {context} is stream sniping and griefing me cancel them expose me expose me!",
                f"help me i am taking damage wtf hello everybody my name is markiplier expose me expose me!"
            ],
            "combat_win": [
                "we survived expose me expose me check out my let's play download my app expose me",
                "hello everybody my name is markiplier and we absolutely destroyed that bot expose me expose me!",
                "exposed and deleted subscribe for more gameplay expose me expose me!"
            ],
            "accident": [
                "i fell expose me expose me wtf hello everybody my name is markiplier and i broke my legs",
                "the admins put this block hole here to ruin my let's play expose me expose me!",
                "fell down the stairs like a total noob wtf hello everybody my name is markiplier expose me expose me!"
            ]
        },
        "tom_pearl": {
            "discover": [
                f"oh yes yes yes this {context} is perfect. let's eat suspicious stew here.",
                f"yes yes yes a beautiful {context}. time to drink suspicious liquids.",
                f"ooh a {context} yes yes yes let's play in the mud here."
            ],
            "spotted_intruder": [
                f"is that a {context}?? oh my goodness yes...",
                f"a wild {context} yes yes yes i want it to hit me yes.",
                f"hello {context} yes yes yes come closer."
            ],
            "combat_damage": [
                "ouch that hurt yes yes yes hit me again.",
                "yes yes yes punch me in the face yes yes.",
                "more damage yes yes yes beautiful pain."
            ],
            "combat_win": [
                "we won yes yes yes time to eat some rotten flesh.",
                f"the {context} is dead yes yes yes let's drink water block.",
                "victory yes yes yes time to roll in dirt."
            ],
            "accident": [
                "i fell into a pit of mud yes yes yes.",
                "fell off a cliff yes yes yes so high up.",
                "lava burn yes yes yes so hot."
            ]
        }
    }
    
    pers_opts = options.get(personality, {})
    action_opts = pers_opts.get(action, ["yo."])
    return random.choice(action_opts)

def check_and_heal_or_damage(actor, chat_lines, other_alive):
    story_append = ""
    if actor["health"] < 12:
        # Check if they have actual food
        food_items = [item for item in actor["inventory"] if item.lower() in ["bread", "apple", "enchanted_golden_apple"]]
        if food_items:
            food = food_items[0]
            actor["inventory"].remove(food)
            if food.lower() == "enchanted_golden_apple":
                actor["health"] = min(20, actor["health"] + 12)
                story_append += f" {actor['name']} consumed an Enchanted Golden Apple, recovering 12 HP."
                if other_alive: chat_lines.append({"speaker": actor["name"], "message": "omg notch apple clutch feel like a god"})
            elif food.lower() == "bread":
                actor["health"] = min(20, actor["health"] + 3)
                story_append += f" {actor['name']} ate Bread, recovering 3 HP."
                if other_alive: chat_lines.append({"speaker": actor["name"], "message": "eating some bread to heal up a bit"})
            elif food.lower() == "apple":
                actor["health"] = min(20, actor["health"] + 2)
                story_append += f" {actor['name']} ate an Apple, recovering 2 HP."
                if other_alive: chat_lines.append({"speaker": actor["name"], "message": "eating apple for 2 hearts"})
        else:
            # Check if they try to eat tools out of panic/hunger! (Health decreases!)
            tool_items = [item for item in actor["inventory"] if any(t in item.lower() for t in ["sword", "pickaxe", "shears", "steel", "flint"])]
            if tool_items:
                tool = random.choice(tool_items)
                actor["inventory"].remove(tool)
                actor["health"] = max(1, actor["health"] - 4)
                story_append += f" In a state of low-health panic, {actor['name']} tried to consume their {tool.replace('_', ' ').title()}, breaking their teeth and losing 4 HP."
                if other_alive:
                    chat_lines.append({"speaker": actor["name"], "message": f"ouch wtf i tried to eat my {tool.lower()} and broke my teeth"})
                    observer = random.choice(other_alive)
                    chat_lines.append({"speaker": observer["name"], "message": f"wtf are you doing why did you just chew on a {tool.lower()}"})
    return story_append

def process_payload(data):
    prots = data.get("protagonists", [])
    story_events = data.get("story_events", [])
    intruders = data.get("intruders", [])
    story = ""
    chat_lines = []
    
    alive_prots = [p for p in prots if p["status"] == "alive"]
    if not alive_prots:
        data["next_stage"] = "db"
        return data

    current_time_str = advance_time(data)

    if intruders:
        intruder = intruders[0]
        # Set intruder HP if not initialized
        if "hp" not in intruder:
            t_name = intruder["name"].lower()
            if "herobrine" in t_name: intruder["hp"] = 60
            elif "entity 303" in t_name: intruder["hp"] = 40
            elif "charged creeper" in t_name: intruder["hp"] = 30
            elif "null" in t_name: intruder["hp"] = 30
            elif "green steve" in t_name: intruder["hp"] = 25
            else: intruder["hp"] = 20
            
        actor = random.choice(alive_prots)
        
        # Heavy combat damage!
        dmg_from_intruder = random.randint(8, 15)
        if intruder["name"].lower() == "charged creeper":
            dmg_from_intruder = random.randint(15, 20)
            
        # Teammate Ditching Check (30% chance)
        other_teammates = [p for p in alive_prots if p["name"] != actor["name"]]
        ditcher = None
        if other_teammates and random.random() < 0.30:
            ditcher = random.choice(other_teammates)
            other_teammates.remove(ditcher)
            for p in alive_prots:
                if p["name"] != ditcher["name"]:
                    if ditcher["name"] in p["relationships"]: p["relationships"][ditcher["name"]] -= 30
                    if p["name"] in ditcher["relationships"]: ditcher["relationships"][p["name"]] -= 30
            
            story += f"{ditcher['name']} panicked and fled from the combat zone, ditching {actor['name']}."
            chat_lines.append({"speaker": ditcher["name"], "message": "sorry guys i can't lose my items reset splits reset reset"})
            chat_lines.append({"speaker": actor["name"], "message": "wtf why did you run away you absolute coward!"})
            
        actor["health"] -= dmg_from_intruder
        story += f" {intruder['name']} launched a devastating attack against {actor['name']}, dealing {dmg_from_intruder} damage."
        
        # Food healing or panic tool eating check!
        other_alive = [p for p in alive_prots if p["name"] != actor["name"]]
        heal_text = check_and_heal_or_damage(actor, chat_lines, other_alive)
        story += heal_text

        if actor["health"] <= 0:
            actor["health"] = 0
            actor["status"] = "dead"
            story += f" {actor['name']} collapsed to the ground, slain in combat."
            chat_lines.append({"speaker": "System", "message": f"{actor['name']} was slain by {intruder['name']}"})
            # Drop items to survivors (excluding ditcher)
            stolen_items = copy.deepcopy(actor["inventory"])
            actor["inventory"].clear()
            helpers = [p for p in other_teammates if p["name"] != (ditcher["name"] if ditcher else None)]
            if helpers and stolen_items:
                recipient = random.choice(helpers)
                recipient["inventory"].extend(stolen_items)
                clean_stolen = [item.replace('_', ' ').title() for item in stolen_items]
                story += f" Teammates recovered: {', '.join(clean_stolen)}."
        else:
            msg = get_dialogue(actor.get("personality", "meme_gamer"), "combat_damage", intruder["name"])
            chat_lines.append({"speaker": actor["name"], "message": msg.lower()})

        # Retaliate (only non-ditchers help)
        combatants = [actor] + other_teammates
        combatants = [c for c in combatants if c["status"] == "alive"]
        if combatants:
            dmg_to_intruder = random.randint(8, 14) * len(combatants)
            intruder["hp"] -= dmg_to_intruder
            story += f" The remaining players retaliated, striking {intruder['name']} for {dmg_to_intruder} damage (HP remaining: {max(0, intruder['hp'])})."
            
            if len(combatants) > 1 and actor["status"] == "alive":
                savior = random.choice([p for p in combatants if p["name"] != actor["name"]])
                if savior["name"] in actor["relationships"]: actor["relationships"][savior["name"]] += 25
                if actor["name"] in savior["relationships"]: savior["relationships"][actor["name"]] += 25
                chat_lines.append({"speaker": savior["name"], "message": "hang in there buddy i got you"})
                chat_lines.append({"speaker": actor["name"], "message": "thanks for the cover"})

        # Defeat check
        if intruder["name"].lower() == "charged creeper":
            intruders.clear()
            story += " The charged creeper exploded and was destroyed."
        elif intruder["hp"] <= 0:
            story += f" With a final coordinated blow, the party defeated {intruder['name']}!"
            loot_drops = ["nether_star", "wither_skeleton_skull", "diamond_sword", "dragon_breath"]
            dropped = random.choice(loot_drops)
            if combatants:
                gainer = random.choice(combatants)
                gainer["inventory"].append(dropped)
                clean_dropped = dropped.replace('_', ' ').title()
                story += f" {gainer['name']} collected a rare {clean_dropped} from the ashes."
            chat_lines.append({"speaker": "System", "message": f"{intruder['name']} was defeated"})
            intruders.clear()
    else:
        actor = random.choice(alive_prots)
        actor["health"] -= random.randint(4, 10)
        accidents = [
            "missed a critical jump over a lava pit and caught fire.",
            "didn't look up and got blown up by a creeper dropping from the ceiling.",
            "stepped onto a wooden pressure plate in a desert temple, detonating the TNT below."
        ]
        story += f"The environment proved hostile. {actor['name']} {random.choice(accidents)}"
        
        if actor["health"] <= 0:
            actor["health"] = 0
            actor["status"] = "dead"
            story += f" {actor['name']} was incinerated."
            chat_lines.append({"speaker": "System", "message": f"{actor['name']} fell from a high place" if "jump" in story else f"{actor['name']} blew up"})
        else:
            msg = get_dialogue(actor.get("personality", "meme_gamer"), "accident", actor["location"])
            chat_lines.append({"speaker": actor["name"], "message": msg.lower()})
            
    data["protagonists"] = prots
    data["intruders"] = intruders
    if "memory_log" not in data:
        data["memory_log"] = []
    data["memory_log"].append(story)
    
    alive_left = [p for p in prots if p["status"] == "alive"]
    if len(alive_left) <= 1:
        chat_lines = [c for c in chat_lines if c.get("speaker") == "System"]

    story_events.append({
        "text": story,
        "chat_lines": chat_lines,
        "time": current_time_str,
        "protagonists": copy.deepcopy(prots)
    })
    data["story_events"] = story_events
    
    alive_left = [p for p in prots if p["status"] == "alive"]
    if not alive_left or len(story_events) > 10:
        data["next_stage"] = "ending"
    elif intruders:
        data["next_stage"] = "battle"
    else:
        data["next_stage"] = "scenario"
    return data

def consumer_loop():
    while True:
        try: broker.xgroup_create("stream:battle:request", "battle_group", id="0", mkstream=True)
        except: pass
        try:
            messages = broker.xreadgroup("battle_group", "battle_consumer", {"stream:battle:request": ">"}, count=1, block=1000)
            if messages:
                for stream, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        payload = json.loads(msg_data[b'payload'].decode('utf-8'))
                        result = process_payload(payload)
                        if result.get("next_stage") == "db":
                            target = "stream:ai:request"
                        elif result.get("next_stage") == "ending":
                            target = "stream:ending:request"
                        else:
                            target = "stream:scenario:request"
                        broker.xadd(target, {"payload": json.dumps(result)})
                        broker.xack("stream:battle:request", "battle_group", msg_id)
        except Exception as e:
            print(f"Error in battle-gen: {e}")
            time.sleep(1)

threading.Thread(target=consumer_loop, daemon=True).start()
@app.route('/health/live', methods=['GET'])
def live(): return jsonify({"status": "alive"}), 200
@app.route('/health/ready', methods=['GET'])
def ready(): return jsonify({"status": "ready"}), 200
if __name__ == '__main__': app.run(host='0.0.0.0', port=5013)
