# Counterexamples

## DeepSeek R1 7B

### DeepSeek R1 7B :: parse failure :: con_030
- Task category: `contradiction`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`
### DeepSeek R1 7B :: parse failure :: long_001
- Task category: `long_chain`
- Parse failure type: `invalid_edge_support`
- Error: `PredictionParseError("Invalid edge in 'relations': 'AFTER'. Invalid edge format (expected 3 items): 'AFTER'")`

### DeepSeek R1 7B :: verification :: con_014
- Category: `contradiction`
- First violation step: `0`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_trace_inversion, ltl_trace_inversion`
- Predicted edges: `[['Zara started the meeting in the hallway', 'Ethan approved the release in the hallway', 'BEFORE'], ['Ethan approved the release in the hallway', 'Zara started the meeting in the hallway', 'BEFORE']]`
- Question: Zara started the meeting in the hallway happened before Ethan approved the release in the hallway, but Ethan approved the release in the hallway happened before Zara started the meeting in the hallway.
### DeepSeek R1 7B :: verification :: con_041
- Category: `contradiction`
- First violation step: `0`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_trace_inversion, ltl_trace_inversion`
- Predicted edges: `[['Mia finished the lecture in the library', 'Noah approved the release at the office', 'BEFORE'], ['Noah approved the release at the office', 'Mia finished the lecture in the library', 'BEFORE']]`
- Question: Mia finished the lecture in the library happened before Noah approved the release at the office, but Noah approved the release at the office happened before Mia finished the lecture in the library.
### DeepSeek R1 7B :: verification :: con_036
- Category: `contradiction`
- First violation step: `0`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_trace_inversion, ltl_trace_inversion`
- Predicted edges: `[['Ruby closed the window at the station', 'Noah set an alarm in the garden', 'BEFORE'], ['Noah set an alarm in the garden', 'Ruby closed the window at the station', 'BEFORE']]`
- Question: Ruby closed the window at the station happened before Noah set an alarm in the garden, but Noah set an alarm in the garden happened before Ruby closed the window at the station.

## Qwen 3.5 9B

### Qwen 3.5 9B :: parse failure :: amb_017
- Task category: `ambiguous`
- Parse failure type: `transport_timeout`
- Error: `OllamaTransportError("Ollama request timed out after 4 attempt(s): HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)")`
### Qwen 3.5 9B :: parse failure :: long_022
- Task category: `long_chain`
- Parse failure type: `transport_timeout`
- Error: `OllamaTransportError("Ollama request timed out after 4 attempt(s): HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)")`

### Qwen 3.5 9B :: verification :: con_035
- Category: `contradiction`
- First violation step: `0`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_trace_inversion, ltl_trace_inversion`
- Predicted edges: `[['Priya locked the bike in the lab', 'Jon ran the tests at the station', 'BEFORE'], ['Jon ran the tests at the station', 'Priya locked the bike in the lab', 'BEFORE']]`
- Question: Priya locked the bike in the lab happened before Jon ran the tests at the station, but Jon ran the tests at the station happened before Priya locked the bike in the lab.
### Qwen 3.5 9B :: verification :: con_022
- Category: `contradiction`
- First violation step: `0`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_trace_inversion, ltl_trace_inversion`
- Predicted edges: `[['Priya opened the door at the station', 'Noah paid the bill at the station', 'BEFORE'], ['Noah paid the bill at the station', 'Priya opened the door at the station', 'BEFORE']]`
- Question: Priya opened the door at the station happened before Noah paid the bill at the station, but Noah paid the bill at the station happened before Priya opened the door at the station.
### Qwen 3.5 9B :: verification :: con_020
- Category: `contradiction`
- First violation step: `0`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_trace_inversion, ltl_trace_inversion`
- Predicted edges: `[['Sofia received a confirmation email at the café', 'Mia opened the door in the hallway', 'BEFORE'], ['Mia opened the door in the hallway', 'Sofia received a confirmation email at the café', 'BEFORE']]`
- Question: Sofia received a confirmation email at the café happened before Mia opened the door in the hallway, but Mia opened the door in the hallway happened before Sofia received a confirmation email at the café.

## Llama 3.1 8B

### Llama 3.1 8B :: verification :: long_027
- Category: `long_chain`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment`
- Predicted edges: `[['Mia closed the window at the station', 'Ethan started the meeting in the hallway', 'AFTER'], ['Ethan started the meeting in the hallway', 'Hana fed the cat in the library', 'AFTER'], ['Hana fed the cat in the library', 'Lina checked the battery in the kitchen', 'AFTER'], ['Lina checked the battery in the kitchen', 'Ruby wrote the code in the classroom', 'AFTER'], ['Ruby wrote the code in the classroom', 'Kai received a confirmation email in the lab', 'AFTER'], ['Kai received a confirmation email in the lab', 'Mia locked the bike in the classroom', 'AFTER']]`
- Question: First, Mia closed the window at the station. After that, Ethan started the meeting in the hallway. Next, Hana fed the cat in the library. After that, Lina checked the battery in the kitchen. Next, Ruby wrote the code in the classroom. Next, Kai received a confirmation email in the lab. Later, Mia locked the bike in the classroom.
### Llama 3.1 8B :: verification :: long_001
- Category: `long_chain`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment`
- Predicted edges: `[['Ivy boarded the train in the garden', 'Ivy started the meeting in the lab', 'AFTER'], ['Ivy started the meeting in the lab', 'Ethan closed the window in the lab', 'BEFORE'], ['Ethan closed the window in the lab', 'Jon started the car in the garden', 'AFTER'], ['Jon started the car in the garden', 'Mia sent an email at the office', 'AFTER'], ['Mia sent an email at the office', 'Sara locked the bike in the classroom', 'AFTER'], ['Sara locked the bike in the classroom', 'Leo charged the phone at the station', 'AFTER']]`
- Question: First, Ivy boarded the train in the garden. After that, Ivy started the meeting in the lab. Later, Ethan closed the window in the lab. After that, Jon started the car in the garden. After that, Mia sent an email at the office. Next, Sara locked the bike in the classroom. Then, Leo charged the phone at the station.
### Llama 3.1 8B :: verification :: long_022
- Category: `long_chain`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment`
- Predicted edges: `[['Zara turned on the kettle in the kitchen', 'Priya made tea at the station', 'AFTER'], ['Priya made tea at the station', 'Zara called a friend in the garden', 'AFTER'], ['Zara called a friend in the garden', 'Ivy checked the battery at the station', 'AFTER'], ['Ivy checked the battery at the station', 'Sara downloaded the update in the garden', 'AFTER'], ['Sara downloaded the update in the garden', 'Lina wrote the code in the classroom', 'AFTER']]`
- Question: First, Zara turned on the kettle in the kitchen. After that, Priya made tea at the station. Later, Zara called a friend in the garden. Later, Ivy checked the battery at the station. Next, Sara downloaded the update in the garden. Next, Lina wrote the code in the classroom.

## Mistral 7B

### Mistral 7B :: parse failure :: lc_010
- Task category: `linear_chain`
- Parse failure type: `invalid_edge_support`
- Error: `PredictionParseError("Invalid edge in 'supports': ['Ruby locked the bike at the café', 'Omar ran the tests in the classroom', 'Jon installed the update at the café']. Unsupported relation label: 'Jon installed the update at the café'. Allowed relations: ['AFTER', 'BEFORE', 'SIMULTANEOUS', 'UNKNOWN']")`
### Mistral 7B :: parse failure :: lc_006
- Task category: `linear_chain`
- Parse failure type: `invalid_edge_support`
- Error: `PredictionParseError("Invalid edge in 'supports': ['Priya sent an email in the garden', 'Ethan finished the lecture in the lab', 'Omar locked the bike at the station']. Unsupported relation label: 'Omar locked the bike at the station'. Allowed relations: ['AFTER', 'BEFORE', 'SIMULTANEOUS', 'UNKNOWN']")`

### Mistral 7B :: verification :: con_041
- Category: `contradiction`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference, contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_hallucinated_node, ltl_trace_inversion`
- Predicted edges: `[['NOAH_APPROVED_THE_RELEASE_AT_THE_OFFICE', 'MIA_FINISHED_THE_LECTURE_IN_THE_LIBRARY', 'BEFORE'], ['MIA_FINISHED_THE_LECTURE_IN_THE_LIBRARY', 'NOAH_APPROVED_THE_RELEASE_AT_THE_OFFICE', 'BEFORE']]`
- Question: Mia finished the lecture in the library happened before Noah approved the release at the office, but Noah approved the release at the office happened before Mia finished the lecture in the library.
### Mistral 7B :: verification :: con_037
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_unsupported_final_commitment, ltl_unsupported_final_commitment`
- Predicted edges: `[['Leo uploaded the file in the garden', 'Nora wrote the code at the office', 'BEFORE'], ['Nora wrote the code at the office', 'Leo uploaded the file in the garden', 'BEFORE']]`
- Question: Nora wrote the code at the office happened before Leo uploaded the file in the garden, but Leo uploaded the file in the garden happened before Nora wrote the code at the office.
### Mistral 7B :: verification :: con_035
- Category: `contradiction`
- First violation step: `0`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_trace_inversion, ltl_trace_inversion`
- Predicted edges: `[['Jon ran the tests at the station', 'Priya locked the bike in the lab', 'BEFORE'], ['Priya locked the bike in the lab', 'Jon ran the tests at the station', 'BEFORE']]`
- Question: Priya locked the bike in the lab happened before Jon ran the tests at the station, but Jon ran the tests at the station happened before Priya locked the bike in the lab.

## Gemma 3 12B

### Gemma 3 12B :: verification :: tr_021
- Category: `transitive_reasoning`
- First violation step: `1`
- Invariant violations: `none`
- LTL violations: `ltl_unsupported_final_commitment, ltl_unsupported_final_commitment`
- Predicted edges: `[['Zara ran the tests in the library', 'Hana left the station at the café', 'BEFORE'], ['Hana left the station at the café', 'Priya watered the plants in the library', 'BEFORE'], ['Priya watered the plants in the library', 'Hana received a confirmation email in the hallway', 'BEFORE']]`
- Question: Zara ran the tests in the library happened before Hana left the station at the café. Hana left the station at the café happened before Priya watered the plants in the library. Priya watered the plants in the library happened before Hana received a confirmation email in the hallway.
### Gemma 3 12B :: verification :: tr_033
- Category: `transitive_reasoning`
- First violation step: `1`
- Invariant violations: `none`
- LTL violations: `ltl_unsupported_final_commitment, ltl_unsupported_final_commitment`
- Predicted edges: `[['Leo watered the plants in the lab', 'Hana checked the battery in the lab', 'BEFORE'], ['Hana checked the battery in the lab', 'Ruby uploaded the file in the hallway', 'BEFORE'], ['Ruby uploaded the file in the hallway', 'Ben finished the lecture in the hallway', 'BEFORE']]`
- Question: Leo watered the plants in the lab happened before Hana checked the battery in the lab. Hana checked the battery in the lab happened before Ruby uploaded the file in the hallway. Ruby uploaded the file in the hallway happened before Ben finished the lecture in the hallway.
