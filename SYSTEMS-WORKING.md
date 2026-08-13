## How the App Works

To understand the backend, we can trace the entire lifecycle of a story generation from the very moment a user clicks **"Play"** on the React frontend.

### Stage 1: The Request & Handshake (Frontend to Orchestrator)
1. **The User Clicks "Play":** The React frontend sends an HTTP `POST` request to the **API Gateway** at `/api/generate`.
2. **Gateway Forwarding:** The API Gateway acts as a traffic director and forwards this request directly to the **Story Orchestrator** at `/generate`.
3. **Session Ticket Creation:** The Story Orchestrator generates a unique UUID `correlation_id` (this acts as a ticket to identify this specific story session).
4. **State Initialization:** The Orchestrator constructs the initial JSON state payload (defining an empty event log, active day count, and empty inventory list).
5. **Kicking off the Stream:** The Orchestrator publishes this initial payload to the first Redis Stream: `stream:character:request` using the Redis `XADD` command.
6. **Immediate Response:** Rather than keeping the frontend waiting for a slow process to finish, the Orchestrator immediately responds with:
   `{"status": "processing", "correlation_id": "YOUR-UUID"}`.

### Stage 2: The Polling Loop (Frontend Waiting Phase)
1. **Frontend Polling:** Upon receiving the `correlation_id`, the frontend configures a timer to request the status from the API Gateway (`GET /api/status/YOUR-UUID`) every **200ms**.
2. **Cache Check:** The API Gateway forwards this query to the Orchestrator, which checks the **Redis Cache** for a key matching `story:YOUR-UUID`.
3. **Waiting State:** If the key is not in the cache (because the generator pipeline is still running), the Orchestrator returns `{"status": "processing"}` and the frontend keeps waiting.

### Stage 3: The Asynchronous Redis Stream Pipeline (The Generators)
While the frontend is polling, the backend workers are running a relay race, processing the payload step-by-step:

1. **Step 1: Spawning Players (`character-gen`):**
   * A worker for the Character Generator reads the message from `stream:character:request`.
   * It randomly spawns 3 to 5 Minecraft players, determines their location, assigns personalities, generates initial relationships, and adds the first event line: *"The adventure begins!"*
   * It pushes the modified state payload to `stream:scenario:request` and acknowledges (`XACK`) the character queue message.

2. **Step 2: Advancing the Map & Events (`scenario-gen`):**
   * A worker reads the payload from `stream:scenario:request`.
   * It advances the game time (Morning $\rightarrow$ Afternoon $\rightarrow$ Night).
   * It triggers environment checks: does the group visit a Desert Temple or Ancient City? Does a player try to steal from another's chest? Do two players trigger a PvP duel?
   * If a threat (e.g. Herobrine) is encountered, it schedules a battle.
   * It writes the updated state payload to `stream:battle:request` and acknowledges the scenario queue message.

3. **Step 3: Simulating Combat (`battle-gen`):**
   * A worker reads the payload from `stream:battle:request`.
   * If an intruder is present, it calculates battle damage, checks if a teammate deserts the fight (which drops relationship scores), and runs recovery/retaliation code. If no intruder is present, it calculates random environmental hazards.
   * **The Loop check:** If all players have died, or the history reaches 10 events, it sets `next_stage` to `"ending"` and pushes the payload to `stream:ending:request`.
   * If the adventure continues, it sets `next_stage` to `"scenario"` and loops the payload **back to `stream:scenario:request`** to repeat the event cycle.

4. **Step 4: Writing the Epilogue (`endings-gen`):**
   * A worker reads the final payload from `stream:ending:request`.
   * If all players died, it appends a *"Game Over"* text. If there are survivors, it writes a random victory ending (e.g. slaying the Ender Dragon).
   * It loops over the entire history of events and compiles all player dialogues and system warnings into a single, clean markdown transcript.
   * It pushes this compiled story to `stream:db:request` and acknowledges the ending queue message.

### Stage 4: Caching and Database Storage (`story-db-service`)
1. **Saving to Cache:** The Story DB Service consumes the message from `stream:db:request`. 
2. It takes the finished story JSON and saves it in the **Redis Cache** under the key `story:YOUR-UUID` with a 1-hour expiration.
3. It acknowledges the final stream message, terminating the generator pipeline.

### Stage 5: The Final Retrieval & Render
1. On the frontend's next 200ms poll request, the Orchestrator checks the **Redis Cache** and finds the key `story:YOUR-UUID` (which now holds the finished story).
2. It returns `{"status": "done", "story": ...}` to the frontend.
3. The React client stops polling, takes the payload, and dynamically renders the typewriter narrative text and player chat history onto the user's screen.

### Behavioral & Gameplay Mechanics

#### 1. Personalities & Dialogue Matching
Dialogues are dynamically selected depending on the player's personality (`debater`, `toxic_sweat`, `speedrunner`, `confused_noob`, `salty`, `loot_goblin`, `meme_gamer`, `chill`, `dreamy_bull`, `expose_me`, `tom_pearl`).
*   A `toxic_sweat` encountering an intruder says: *"wtf is that standing there. i'm gonna ez drop him."*
*   A `confused_noob` taking damage says: *"help help help how do i block with shield shit!"*

#### 2. Relationship Engine & PvP
*   Players start with random relationship scores. Certain pairs spawn with custom modifiers (e.g. *CharlieKirk* and *xX_NoobSlayer_Xx* spawn with a PvP settings argument, setting their relationship to `-40`).
*   Actions (stealing items, running away from battles, or using the wrong tools) decrease relationships.
*   Saving a teammate in a fight increases relationships by `+25`.
*   If a relationship drops to **`-40` or below**, a PvP fight is triggered. This can result in one player killing the other (and looting their inventory), a player rage-quitting, or calling a reluctant truce to survive.

#### 3. Tool Verification (Survival Mechanics)
When exploring, the group must possess specific tools in their collective inventory:
*   **Desert Temple:** Requires a `pickaxe` (to dig) or `shears` (to defuse wire). If missing, the TNT trap detonates, dealing `10` damage to everyone.
*   **Ancient City:** Requires `shears` to collect wool and muffle footsteps. If missing, they trigger a sculk shrieker and *The Warden* sonic-booms the group for `8` damage.

#### 4. Low-Health Panic (Tool Eating)
When a player's health drops below `12`, they search their inventory for food (e.g. bread, apple, enchanted golden apple) to heal. If they are out of food but possess tools (like swords or pickaxes), they will panic-eat their tools in desperation, breaking their teeth and losing `4 HP`.
