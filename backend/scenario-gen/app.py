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
        "debater": {
            "discover": [
                f"yo facts don't care about your feelings i found a {context}.",
                f"let's logically analyze this {context} we just ran into.",
                f"anyone who claims this {context} is bad is objectively wrong."
            ],
            "spotted_intruder": [
                f"let's logically analyze why that {context} is standing there. it's violating server rules.",
                f"an intruder {context} has spawned. this is a clear violation of NAP.",
                f"that {context} cannot logically defend its presence here."
            ],
            "combat_damage": [
                f"fucking hell this {context} is debating my health bar with pure violence.",
                f"i am taking physical damage wtf. this is authoritarian violence.",
                f"this {context} is violating my rights, help me!"
            ],
            "combat_win": [
                "destroyed with facts and logic lmao.",
                "another logical debate won by force of arms.",
                "libertarian utopia restored."
            ],
            "accident": [
                "i fell. this gravity mechanic is literally socialism.",
                "physics is a statist construct wtf i fell.",
                "i took fall damage. who set this world border? literally 1984."
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

def get_arg_line(p_from, p_to, step):
    pers_from = p_from.get("personality", "meme_gamer")
    name_to = p_to["name"]
    
    if step == 1:
        options = {
            "debater": [
                "let's debate why you stole my resources. facts don't care about your feelings.",
                "logically speaking, you taking my ores is a direct violation of property rights.",
                "i have an empirical proof that you took my coal blocks. let's debate."
            ],
            "toxic_sweat": [
                f"yo {name_to} you trash noob you literally stole my iron.",
                f"give me my iron back you absolute bot {name_to}.",
                f"why are you touching my furnace loot you garbage player."
            ],
            "speedrunner": [
                "you are slowing down my speedrun by locking the chests wtf.",
                "your movement is blocking my routing. get out of the way.",
                "taking my obsidian is a time loss of 40 seconds. wtf are you doing."
            ],
            "confused_noob": [
                f"did you take my wood block {name_to}? i can't find it.",
                "hey, why did you break my crafting table? i was using that.",
                f"is my iron in your inventory {name_to}? i think it went missing."
            ],
            "salty": [
                "who griefed my wall? this server is absolute garbage.",
                "who took my coal? this community is full of griefers.",
                "someone stole my diamond. typical toxic server."
            ],
            "loot_goblin": [
                "you took the gold from the chest! that was my loot!",
                "hey! i saw you pick up that diamond! that was my chest!",
                "dibs means dibs, why are you holding my gold ingot!"
            ],
            "dreamy_bull": [
                "yo my diamonds are gone i'm about to blow up! wtf!",
                "who took my iron... oh my god i'm about to burst...",
                "no my items... i'm gonna burst if you don't return them..."
            ],
            "expose_me": [
                "hello everybody my name is markiplier and someone stole my raw porkchop expose me expose me!",
                "exclusive drama! someone looted my private chest expose me expose me!",
                "was that the theft of 87?? someone took my cobble expose me expose me!"
            ],
            "tom_pearl": [
                f"gimme that suspicious stew in the chest right now yes yes yes {name_to}.",
                "why did you drink my bucket of milk yes yes yes.",
                f"you took my raw mutton yes yes yes return it {name_to}."
            ]
        }
        return random.choice(options.get(pers_from, ["who took my stuff from the furnace?"]))

    elif step == 2:
        options = {
            "debater": [
                "scientifically speaking, resources in a shared furnace are public property.",
                "your claim to this iron has no logical foundation.",
                "i am simply allocating the capital to a more productive member."
            ],
            "toxic_sweat": [
                "stfu kid it's mine now. get good and mine your own.",
                "cry about it noob. i needed it for armor.",
                "lmao you are too slow trash. get good."
            ],
            "speedrunner": [
                "i needed it for the portal speedrun. routing optimization.",
                "world record pace requires this resource. skip the debate.",
                "i'm keeping it for the splits. do not waste time."
            ],
            "confused_noob": [
                "i didn't mean to! how do i drop items again?",
                "wait, was that yours? i thought it spawned on the floor.",
                "how do i open my inventory to check? help."
            ],
            "salty": [
                "who cares, the game is broken anyway. cry about it.",
                "the seed is garbage anyway. deal with it.",
                "i'm logging off anyway, take it or leave it."
            ],
            "loot_goblin": [
                "mine mine mine! i found it first!",
                "finders keepers! my inventory my rules!",
                "everything in this chunk is mine!"
            ],
            "dreamy_bull": [
                "i didn't take it... oh my god i'm about to burst...",
                "no please i didn't do it... ahhh it feels too intense...",
                "omg stop blaming me i'm about to nut..."
            ],
            "expose_me": [
                "was that the bite of 87?? expose me expose me i am innocent!",
                "hello everybody my name is markiplier and this is fake news expose me expose me!",
                "i am being framed by haters expose me expose me!"
            ],
            "tom_pearl": [
                "no it is my stew i made it with beautiful brown mushrooms yes yes yes.",
                "i ate it yes yes yes it tasted like dirt yes yes yes.",
                "yes yes yes it is in my tummy now yes yes."
            ]
        }
        return random.choice(options.get(pers_from, ["i needed it for crafting, chill out."]))

    elif step == 3:
        options = {
            "debater": [
                "taking my items without consent is literally socialism. i will dismantle your base.",
                "your action violates the NAP. i will file a complaint to the admins.",
                "i am building a cobblestone wall around your house as a logical counter-sanction."
            ],
            "toxic_sweat": [
                "i'm going to grief your house tonight trash kid.",
                "keep crying bot. i'm putting lava on your bed.",
                "i will spawn kill you until you quit."
            ],
            "speedrunner": [
                "you are literally throwing the run. i'm resetting.",
                "thrower. i'm leaving the server and deleting the map.",
                "this run is dead. terrible teammates."
            ],
            "confused_noob": [
                "please don't hit me! i don't want to lose my levels!",
                "are you going to kill me? please don't i have three wheat!",
                "how do i delete this server? you are mean."
            ],
            "salty": [
                "this server is shit. i'm burning your bed and logging off.",
                "garbage server with garbage players. i'm deleting client.",
                "trash community. i hope a creeper blows up your base."
            ],
            "loot_goblin": [
                "i'm stealing all your torches now. loot goblin active.",
                "i will empty every chest in your house. mine mine mine.",
                "i'm hiding all the diamond blocks. good luck finding them."
            ],
            "dreamy_bull": [
                "it hurts so good seeing you guys fight... ahhh help me",
                "omg the tension... i'm literally about to blow up...",
                "ahhh stop it guys i'm gonna burst..."
            ],
            "expose_me": [
                "hello everybody my name is markiplier and this is a scandal expose me expose me!",
                "i am recording this for my next expose video expose me expose me!",
                "the truth will come out on my let's play expose me expose me!"
            ],
            "tom_pearl": [
                "i am going to eat all the rotten flesh and suspicious stews yes yes yes.",
                "yes yes yes i will fill your house with mud blocks yes yes.",
                "i will jump in lava yes yes yes watch me burn yes yes."
            ]
        }
        return random.choice(options.get(pers_from, ["give it back or i'm leaving the game."]))
        
    return "whatever."

def get_chimer_line(speaker, p1, p2, level):
    pers = speaker.get("personality", "meme_gamer")
    if pers == "chill":
        return ["guys calm down it's just a game block", "stop fighting we need to survive", "let's just share the items please"][level - 1]
    elif pers == "toxic_sweat":
        return ["fight fight fight ez drops", "lmao look at these bots crying", "both of you are absolute trash"][level - 1]
    elif pers == "debater":
        return [f"logically {p1['name']} has the better point here", f"facts indicate {p2['name']} is wrong", "this conflict is highly unproductive"][level - 1]
    elif pers == "salty":
        return ["who cares the server is laggy garbage anyway", "i hope you both blow up", "typical day on this server"][level - 1]
    elif pers == "meme_gamer":
        return ["bruh moment live in 4k", "grab the popcorn boys", "this is cinema right here"][level - 1]
    elif pers == "expose_me":
        return ["expose them both markiplier style expose me!", "double expose video incoming expose me!", "was that the fight of 87?? expose me!"][level - 1]
    elif pers == "tom_pearl":
        return ["yes yes yes roll in the mud and fight yes yes", "drink suspicious soup and fight yes yes", "yes yes yes punch each other yes"][level - 1]
    else:
        return ["stop fighting", "this is crazy", "whatever"][level - 1]

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
                chat_lines.append({"speaker": actor["name"], "message": "omg notch apple clutch feel like a god"})
            elif food.lower() == "bread":
                actor["health"] = min(20, actor["health"] + 3)
                story_append += f" {actor['name']} ate Bread, recovering 3 HP."
                chat_lines.append({"speaker": actor["name"], "message": "eating some bread to heal up a bit"})
            elif food.lower() == "apple":
                actor["health"] = min(20, actor["health"] + 2)
                story_append += f" {actor['name']} ate an Apple, recovering 2 HP."
                chat_lines.append({"speaker": actor["name"], "message": "eating apple for 2 hearts"})
        else:
            # Check if they try to eat tools out of panic/hunger! (Health decreases!)
            tool_items = [item for item in actor["inventory"] if any(t in item.lower() for t in ["sword", "pickaxe", "shears", "steel", "flint"])]
            if tool_items:
                tool = tool_items[0]
                actor["inventory"].remove(tool)
                actor["health"] = max(1, actor["health"] - 4)
                story_append += f" In a state of low-health panic, {actor['name']} tried to consume their {tool.replace('_', ' ').title()}, chipping their teeth and losing 4 HP."
                chat_lines.append({"speaker": actor["name"], "message": f"ouch wtf i tried to eat my {tool.lower()} and broke my teeth"})
                if other_alive:
                    observer = random.choice(other_alive)
                    chat_lines.append({"speaker": observer["name"], "message": f"wtf are you doing why did you just chew on a {tool.lower()}"})
    return story_append

def generate_multi_member_argument(prots, alive_prots):
    p1, p2 = random.sample(alive_prots, 2)
    
    # 50% chance a third player chimes in
    chimer = None
    other_alive = [p for p in alive_prots if p["name"] not in [p1["name"], p2["name"]]]
    if other_alive and random.random() < 0.50:
        chimer = random.choice(other_alive)
        
    # Relationship drops
    if p2["name"] in p1["relationships"]: p1["relationships"][p2["name"]] -= 25
    if p1["name"] in p2["relationships"]: p2["relationships"][p1["name"]] -= 25
    
    # Inventory robbery
    stolen_item = None
    if p2["inventory"]:
        stolen_item = random.choice(p2["inventory"])
        p2["inventory"].remove(stolen_item)
        p1["inventory"].append(stolen_item)
        
    chat_lines = []
    
    # Level 1
    chat_lines.append({"speaker": p1["name"], "message": get_arg_line(p1, p2, 1).lower()})
    chat_lines.append({"speaker": p2["name"], "message": get_arg_line(p2, p1, 1).lower()})
    
    # Level 2
    if chimer:
        chat_lines.append({"speaker": chimer["name"], "message": get_chimer_line(chimer, p1, p2, 1).lower()})
    chat_lines.append({"speaker": p1["name"], "message": get_arg_line(p1, p2, 2).lower()})
    chat_lines.append({"speaker": p2["name"], "message": get_arg_line(p2, p1, 2).lower()})
    
    # Level 3
    if chimer:
        chat_lines.append({"speaker": chimer["name"], "message": get_chimer_line(chimer, p1, p2, 2).lower()})
    chat_lines.append({"speaker": p1["name"], "message": get_arg_line(p1, p2, 3).lower()})
    chat_lines.append({"speaker": p2["name"], "message": get_arg_line(p2, p1, 3).lower()})
    
    if stolen_item:
        clean_stolen = stolen_item.replace('_', ' ').title()
        chat_lines.append({"speaker": "System", "message": f"{p1['name']} stole {clean_stolen} from {p2['name']}'s chest!"})
        
    text = f"A fierce argument broke out between {p1['name']} and {p2['name']} at their campsite over shared resources."
    if chimer:
        text += f" {chimer['name']} tried to intervene in the dispute."
        
    # Check threshold for PvP fight (score <= -40)
    score = p1["relationships"].get(p2["name"], 0)
    if score <= -40:
        text += f" The tension crossed the threshold, and a PvP duel exploded between {p1['name']} and {p2['name']}!"
        chat_lines.append({"speaker": "System", "message": f"PvP has been enabled between {p1['name']} and {p2['name']}"})
        
        r = random.random()
        if r < 0.50:
            # One dead
            winner, loser = (p1, p2) if random.random() < 0.5 else (p2, p1)
            loser["health"] = 0
            loser["status"] = "dead"
            # Winner loots loser
            loser_loot = copy.deepcopy(loser["inventory"])
            loser["inventory"].clear()
            winner["inventory"].extend(loser_loot)
            clean_loot = [item.replace('_', ' ').title() for item in loser_loot]
            
            text += f" {winner['name']} drew a sword and struck down {loser['name']} in cold blood."
            if clean_loot:
                text += f" {winner['name']} looted their corpse: {', '.join(clean_loot)}."
            chat_lines.append({"speaker": "System", "message": f"{loser['name']} was slain by {winner['name']} in PvP"})
        elif r < 0.80:
            # One rage-quits
            leaver = random.choice([p1, p2])
            leaver["status"] = "left"
            text += f" Furious after the duel, {leaver['name']} rage-quit the server permanently, deleting their bed."
            chat_lines.append({"speaker": "System", "message": f"{leaver['name']} left the game (Ragequit)"})
        else:
            # Make up / truce
            p1["relationships"][p2["name"]] = -30
            p2["relationships"][p1["name"]] = -30
            text += f" Just before drawing blood, both players realized they needed each other to survive Herobrine and called a reluctant truce."
            chat_lines.append({"speaker": p1["name"], "message": "fine, whatever. let's just survive."})
            chat_lines.append({"speaker": p2["name"], "message": "deal. don't touch my stuff again."})
            
    return text, chat_lines

def process_payload(data):
    prots = data.get("protagonists", [])
    story_events = data.get("story_events", [])
    intruders = data.get("intruders", [])
    
    alive_prots = [p for p in prots if p["status"] == "alive"]
    if not alive_prots:
        data["next_stage"] = "db"
        return data

    current_time_str = advance_time(data)
    text = ""
    chat_lines = []
    
    # Check for super hostile relations
    super_hostile_pairs = []
    for p in alive_prots:
        for other in alive_prots:
            if p["name"] != other["name"]:
                if p["relationships"].get(other["name"], 0) <= -40:
                    super_hostile_pairs.append((p, other))
                    
    # Wrong Tool Usage Event (25% chance)
    if random.random() < 0.25 and len(alive_prots) >= 2:
        actor = random.choice(alive_prots)
        observer = random.choice([p for p in alive_prots if p["name"] != actor["name"]])
        
        mismatches = [
            ("Stone Sword", "to mine cobblestone", "why are you using a sword to mine stone you bot", "i don't have a pickaxe stfu"),
            ("Wooden Pickaxe", "to chop trees", "using a pickaxe to cut wood? absolute waste of durability", "speedrun tactics, you wouldn't understand"),
            ("Stone Sword", "to dig dirt blocks", "digging dirt with a sword? you are ruining the durability", "whatever i do what i want")
        ]
        tool_needed, action_desc, obs_msg, act_msg = random.choice(mismatches)
        
        has_tool = any(tool_needed.lower() in item.lower() for item in actor["inventory"])
        if has_tool:
            text = f"At camp, {observer['name']} frowned upon {actor['name']} using their {tool_needed} {action_desc}."
            chat_lines = [
                {"speaker": observer["name"], "message": obs_msg},
                {"speaker": actor["name"], "message": act_msg}
            ]
            if actor["name"] in observer["relationships"]: observer["relationships"][actor["name"]] -= 10
            if observer["name"] in actor["relationships"]: actor["relationships"][observer["name"]] -= 10
            
            data["protagonists"] = prots
            story_events.append({
                "text": text,
                "chat_lines": chat_lines,
                "time": current_time_str,
                "protagonists": copy.deepcopy(prots)
            })
            data["story_events"] = story_events
            data["next_stage"] = "scenario"
            return data

    # Reputation-based Sabotage or Theft (45% chance if hostile relations exist)
    if super_hostile_pairs and random.random() < 0.45:
        p_sub, p_vic = random.choice(super_hostile_pairs)
        r = random.random()
        if r < 0.50 and p_vic["inventory"]:
            # Theft
            stolen = random.choice(p_vic["inventory"])
            p_vic["inventory"].remove(stolen)
            p_sub["inventory"].append(stolen)
            clean_stolen = stolen.replace('_', ' ').title()
            text = f"Taking advantage of the night, {p_sub['name']} secretly raided {p_vic['name']}'s private chests and stole their {clean_stolen}."
            chat_lines = [{"speaker": "System", "message": f"someone stole {clean_stolen} from {p_vic['name']}'s chest!"}]
            
            # Caught red-handed!
            if random.random() < 0.50:
                text += f" However, {p_vic['name']} caught them red-handed, igniting a sudden confrontation!"
                chat_lines.append({"speaker": p_vic["name"], "message": "hey i saw that! drop my stuff right now!"})
                p_sub["relationships"][p_vic["name"]] = -80
                p_vic["relationships"][p_sub["name"]] = -80
                _, fight_chats = generate_multi_member_argument(prots, alive_prots)
                chat_lines.extend(fight_chats)
        else:
            # Sabotage base
            accidents = [
                f"{p_sub['name']} poured a bucket of lava near the campsite storage, burning several chests.",
                f"{p_sub['name']} placed TNT under the base crafting station, detonating it maliciously.",
                f"{p_sub['name']} locked the base nether portal with cobblestone blocks to trap the group."
            ]
            text = f"Tensions erupted at base. {random.choice(accidents)} {p_sub['name']}'s actions sabotaged the entire group."
            chat_lines = [{"speaker": "System", "message": f"{p_sub['name']} sabotaged the base!"}]
            for p in alive_prots:
                if p["name"] != p_sub["name"]:
                    dmg = random.randint(4, 8)
                    p["health"] -= dmg
                    text += f" {p['name']} took {dmg} damage from the sabotage."
                    if p["health"] <= 0:
                        p["health"] = 0
                        p["status"] = "dead"
                        text += f" {p['name']} was killed."
                        chat_lines.append({"speaker": "System", "message": f"{p['name']} was blown up by {p_sub['name']}"})
    elif len(alive_prots) >= 2 and random.random() < 0.55:
        # Multi-member, 3-level argument (55% chance)
        text, chat_lines = generate_multi_member_argument(prots, alive_prots)
    else:
        actor = random.choice(alive_prots)
        tod = data.get("time_of_day", "Morning")
        if tod == "Night":
            scenarios = [
                ("Spider Cave", f"{actor['name']} wandered into a pitch-black cave and heard the clicking sound of cave spiders.", "cave spiders"),
                ("Phantom Sky", f"Looking up at the night sky, {actor['name']} was suddenly swooped by phantoms due to lack of sleep.", "phantoms"),
                ("Creeper Ambush", f"A loud hiss echoed behind {actor['name']} as a creeper sneaked up on them in the dark.", "creeper"),
                ("Wandering Zombie Pack", f"A group of armored zombies surrounded {actor['name']} in a dark oak forest.", "zombies"),
                ("Nether Fortress Ruin", f"{actor['name']} took a wrong turn inside a Nether portal and was trapped inside a blazing Nether Fortress.", "wither skeleton")
            ]
        else:
            scenarios = [
                ("Nether Portal", f"Exploring a rocky hillside, {actor['name']} discovered a ruined Nether Portal with a chest of obsidian.", None),
                ("Desert Temple", f"{actor['name']} found a Desert Temple buried in the sand and prepared to loot the treasure chambers.", None),
                ("Abandoned Mineshaft", f"{actor['name']} dug straight down and broke into a massive, dusty abandoned mineshaft.", None),
                ("Ocean Monument", f"Sailing across a deep ocean biome, {actor['name']} spotted the glowing lanterns of an Ocean Monument.", None),
                ("Ancient City", f"{actor['name']} found a deep cavern leading down to an Ancient City covered in sculk blocks.", "the warden"),
                ("Witch Hut", f"{actor['name']} stumbled upon a creepy witch hut in the middle of a dark swamp biome.", "witch"),
                ("Woodland Mansion", f"{actor['name']} discovered a massive Woodland Mansion hidden in the dark forest trees.", "evoker")
            ]
        
        scenario = random.choice(scenarios)
        new_loc = scenario[0]
        text = scenario[1]
        actor["location"] = new_loc
        
        # Check proper tools for structures
        has_pick = any(any("pickaxe" in item.lower() for item in p["inventory"]) for p in alive_prots)
        has_sword = any(any("sword" in item.lower() for item in p["inventory"]) for p in alive_prots)
        has_shears = any(any("shears" in item.lower() for item in p["inventory"]) for p in alive_prots)
        has_flint = any(any("steel" in item.lower() for item in p["inventory"]) for p in alive_prots)
        
        failed_scenario = False
        failed_desc = ""
        dmg_to_all = 0
        
        if new_loc == "Desert Temple":
            if not (has_pick or has_shears):
                failed_scenario = True
                failed_desc = "Without a Pickaxe to mine the sandstone or Shears to defuse the pressure plate wires, they accidentally detonated the TNT traps, triggering an explosion!"
                dmg_to_all = 10
        elif new_loc == "Abandoned Mineshaft":
            if not (has_pick or has_sword):
                failed_scenario = True
                failed_desc = "Lacking a Pickaxe to tunnel or a Sword to slice the spider webs, they got tangled in thick cobwebs and bitten by venomous cave spiders."
                dmg_to_all = 4
        elif new_loc == "Nether Portal":
            if not (has_flint or has_pick):
                failed_scenario = True
                failed_desc = "Without a Flint and Steel or a Pickaxe to strike sparks, they failed to light the portal. A stray Ghast fireball detonated nearby, burning the area."
                dmg_to_all = 6
        elif new_loc == "Ancient City":
            if not has_shears:
                failed_scenario = True
                failed_desc = "Lacking Shears to collect wool blocks and muffle their footsteps, they triggered a sculk shrieker. The Warden emerged, launching a sonic boom!"
                dmg_to_all = 8
                
        if failed_scenario:
            text = f"{actor['name']} led the group to a {new_loc}. {failed_desc}"
            chat_lines.append({"speaker": "System", "message": f"Failed {new_loc} exploration due to lack of proper tools!"})
            for p in alive_prots:
                p["health"] -= dmg_to_all
                text += f" {p['name']} took {dmg_to_all} damage."
                if p["health"] <= 0:
                    p["health"] = 0
                    p["status"] = "dead"
                    text += f" {p['name']} died."
                    chat_lines.append({"speaker": "System", "message": f"{p['name']} met their end in the {new_loc}"})
        else:
            # Success! Loot chests
            loot = []
            if new_loc == "Desert Temple": loot = ["diamond", "emerald", "enchanted_golden_apple"]
            elif new_loc == "Abandoned Mineshaft": loot = ["iron_ingot", "coal", "diamond"]
            elif new_loc == "Nether Portal": loot = ["obsidian", "gold_block", "flint_and_steel"]
            elif new_loc == "Ocean Monument": loot = ["prismarine_shard", "gold_block"]
            elif new_loc == "Ancient City": loot = ["netherite_scrap", "enchanted_book"]
            
            if loot:
                found_loot = random.sample(loot, k=random.randint(1, min(2, len(loot))))
                actor["inventory"].extend(found_loot)
                clean_loot = [item.replace('_', ' ').title() for item in found_loot]
                text += f" {actor['name']} looted a chest and acquired {', '.join(clean_loot)}."
            
            if len(alive_prots) > 1:
                msg = get_dialogue(actor.get("personality", "meme_gamer"), "discover", new_loc)
                chat_lines.append({"speaker": actor["name"], "message": msg.lower()})
        
        # Decide the threat spawn
        threat_spawn = False
        selected_threat = None
        if len(scenario) > 2 and scenario[2]:
            threat_spawn = True
            selected_threat = scenario[2]
        elif (tod == "Night" or random.random() < 0.45) and not intruders:
            threat_spawn = True
            
        if threat_spawn and not intruders:
            if not selected_threat:
                threats = [
                    ("entity 303", ["hacker", "aggressive"], 0.25),
                    ("null", ["shadow", "blindness"], 0.25),
                    ("green steve", ["poisonous"], 0.20),
                    ("charged creeper", ["explosive"], 0.25),
                    ("herobrine", ["stalker", "inf_health"], 0.05)
                ]
                r = random.random()
                cumulative = 0.0
                for t_name, t_traits, t_weight in threats:
                    cumulative += t_weight
                    if r <= cumulative:
                        selected_threat = t_name
                        selected_traits = t_traits
                        break
            else:
                if selected_threat == "the warden":
                    selected_traits = ["sonic_boom", "heavy_hitting"]
                else:
                    selected_traits = ["aggressive"]

            intruders.append({"name": selected_threat, "traits": selected_traits})
            text += f" A terrifying threat emerged: {selected_threat} loomed ahead."
            chat_lines.append({"speaker": "System", "message": f"a wild {selected_threat} appeared..."})
            if len(alive_prots) > 1:
                msg = get_dialogue(actor.get("personality", "meme_gamer"), "spotted_intruder", selected_threat)
                chat_lines.append({"speaker": actor["name"], "message": msg.lower()})
        
        # Heal or panic-eat tools check
        heal_text = check_and_heal_or_damage(actor, chat_lines, [p for p in alive_prots if p["name"] != actor["name"]])
        text += heal_text
            
    data["protagonists"] = prots
    data["intruders"] = intruders
    story_events.append({
        "text": text,
        "chat_lines": chat_lines,
        "time": current_time_str,
        "protagonists": copy.deepcopy(prots)
    })
    data["story_events"] = story_events
    
    if intruders: data["next_stage"] = "battle"
    else: data["next_stage"] = random.choice(["scenario", "scenario", "battle"])
    return data

def consumer_loop():
    while True:
        try: broker.xgroup_create("stream:scenario:request", "scenario_group", id="0", mkstream=True)
        except: pass
        try:
            messages = broker.xreadgroup("scenario_group", "scenario_consumer", {"stream:scenario:request": ">"}, count=1, block=1000)
            if messages:
                for stream, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        payload = json.loads(msg_data[b'payload'].decode('utf-8'))
                        result = process_payload(payload)
                        broker.xadd("stream:battle:request", {"payload": json.dumps(result)})
                        broker.xack("stream:scenario:request", "scenario_group", msg_id)
        except Exception as e:
            print(f"Error in scenario-gen: {e}")
            time.sleep(1)

threading.Thread(target=consumer_loop, daemon=True).start()
@app.route('/health/live', methods=['GET'])
def live(): return jsonify({"status": "alive"}), 200
@app.route('/health/ready', methods=['GET'])
def ready(): return jsonify({"status": "ready"}), 200
if __name__ == '__main__': app.run(host='0.0.0.0', port=5012)
