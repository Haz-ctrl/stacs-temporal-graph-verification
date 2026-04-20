# Counterexamples

## deepseek-r1:7b

### deepseek-r1:7b :: parse failure :: long_014
- Task category: `long_chain`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`
### deepseek-r1:7b :: parse failure :: lc_022
- Task category: `linear_chain`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`

### deepseek-r1:7b :: verification :: con_019
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Nora ran the tests at the station', 'Kai printed the handouts in the hallway', 'BEFORE'], ['Kai printed the handouts in the hallway', 'Nora ran the tests at the station', 'BEFORE']]`
- Question: Nora ran the tests at the station happened before Kai printed the handouts in the hallway, but Kai printed the handouts in the hallway happened before Nora ran the tests at the station.
### deepseek-r1:7b :: verification :: con_014
- Category: `contradiction`
- First violation step: `0`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Mia finished the lecture in the garden', 'Sara checked the battery in the library', 'UNKNOWN']]`
- Question: Mia finished the lecture in the garden happened before Sara checked the battery in the library, but Sara checked the battery in the library happened before Mia finished the lecture in the garden.
### deepseek-r1:7b :: verification :: lc_010
- Category: `linear_chain`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['Event A', 'Event B', 'BEFORE'], ['Event B', 'Event C', 'BEFORE']]`
- Question: Ruby locked the bike at the café. Then, Omar ran the tests in the classroom. After that, Jon installed the update at the café.

## qwen3.5:9b

### qwen3.5:9b :: parse failure :: amb_029
- Task category: `ambiguous`
- Parse failure type: `transport_timeout`
- Error: `OllamaTransportError("Ollama request timed out after 1 attempt(s): HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)")`
### qwen3.5:9b :: parse failure :: amb_008
- Task category: `ambiguous`
- Parse failure type: `transport_timeout`
- Error: `OllamaTransportError("Ollama request timed out after 1 attempt(s): HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)")`

### qwen3.5:9b :: verification :: con_018
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Leo watered the plants in the library', 'Sam set an alarm in the lab', 'BEFORE'], ['Sam set an alarm in the lab', 'Leo watered the plants in the library', 'BEFORE']]`
- Question: Leo watered the plants in the library happened before Sam set an alarm in the lab, but Sam set an alarm in the lab happened before Leo watered the plants in the library.
### qwen3.5:9b :: verification :: con_015
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Lina approved the release in the lab', 'Sara boarded the train in the kitchen', 'BEFORE'], ['Sara boarded the train in the kitchen', 'Lina approved the release in the lab', 'BEFORE']]`
- Question: Lina approved the release in the lab happened before Sara boarded the train in the kitchen, but Sara boarded the train in the kitchen happened before Lina approved the release in the lab.
### qwen3.5:9b :: verification :: con_013
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Ethan left the station at home', 'Omar checked the battery in the classroom', 'BEFORE'], ['Omar checked the battery in the classroom', 'Ethan left the station at home', 'BEFORE']]`
- Question: Ethan left the station at home happened before Omar checked the battery in the classroom, but Omar checked the battery in the classroom happened before Ethan left the station at home.

## llama3.1:8b

### llama3.1:8b :: verification :: con_018
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Leo watered the plants in the library', 'Sam set an alarm in the lab', 'BEFORE'], ['Sam set an alarm in the lab', 'Leo watered the plants in the library', 'BEFORE']]`
- Question: Leo watered the plants in the library happened before Sam set an alarm in the lab, but Sam set an alarm in the lab happened before Leo watered the plants in the library.
### llama3.1:8b :: verification :: con_009
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Hana made tea in the classroom', 'Ivy sent an email in the library', 'BEFORE'], ['Ivy sent an email in the library', 'Hana made tea in the classroom', 'BEFORE']]`
- Question: Hana made tea in the classroom happened before Ivy sent an email in the library, but Ivy sent an email in the library happened before Hana made tea in the classroom.
### llama3.1:8b :: verification :: con_010
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Omar charged the phone in the library', 'Hana printed the handouts in the kitchen', 'BEFORE'], ['Hana printed the handouts in the kitchen', 'Omar charged the phone in the library', 'BEFORE']]`
- Question: Omar charged the phone in the library happened before Hana printed the handouts in the kitchen, but Hana printed the handouts in the kitchen happened before Omar charged the phone in the library.

## mistral:7b

### mistral:7b :: parse failure :: amb_001
- Task category: `ambiguous`
- Parse failure type: `invalid_edge_support`
- Error: `PredictionParseError("Invalid edge in 'supports': ['Sofia made tea in the classroom', 'Hana opened the door in the garden', 'NOT SIMULTANEOUS']. Unsupported relation label: 'NOT SIMULTANEOUS'. Allowed relations: ['AFTER', 'BEFORE', 'SIMULTANEOUS', 'UNKNOWN']")`
### mistral:7b :: parse failure :: lc_036
- Task category: `linear_chain`
- Parse failure type: `invalid_edge_support`
- Error: `PredictionParseError("Invalid edge in 'supports': ['Lina fed the cat at the café', 'Nora ran the tests at home', 'Nora started the car at the station']. Unsupported relation label: 'Nora started the car at the station'. Allowed relations: ['AFTER', 'BEFORE', 'SIMULTANEOUS', 'UNKNOWN']")`

### mistral:7b :: verification :: con_018
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Leo watered the plants in the library', 'Sam set an alarm in the lab', 'BEFORE'], ['Sam set an alarm in the lab', 'Leo watered the plants in the library', 'BEFORE']]`
- Question: Leo watered the plants in the library happened before Sam set an alarm in the lab, but Sam set an alarm in the lab happened before Leo watered the plants in the library.
### mistral:7b :: verification :: con_010
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Omar charged the phone in the library', 'Hana printed the handouts in the kitchen', 'BEFORE'], ['Hana printed the handouts in the kitchen', 'Omar charged the phone in the library', 'BEFORE']]`
- Question: Omar charged the phone in the library happened before Hana printed the handouts in the kitchen, but Hana printed the handouts in the kitchen happened before Omar charged the phone in the library.
### mistral:7b :: verification :: con_013
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Omar checked the battery in the classroom', 'Ethan left the station at home', 'BEFORE'], ['Ethan left the station at home', 'Omar checked the battery in the classroom', 'BEFORE']]`
- Question: Ethan left the station at home happened before Omar checked the battery in the classroom, but Omar checked the battery in the classroom happened before Ethan left the station at home.
