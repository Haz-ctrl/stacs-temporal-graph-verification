# Counterexamples

## DeepSeek R1 7B

### DeepSeek R1 7B :: parse failure :: lc_038
- Task category: `linear_chain`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`
### DeepSeek R1 7B :: parse failure :: amb_005
- Task category: `ambiguous`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`


## Qwen 3.5 9B

### Qwen 3.5 9B :: parse failure :: long_014
- Task category: `long_chain`
- Parse failure type: `other_failure`
- Error: `ReadTimeout(ReadTimeoutError("HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)"))`
### Qwen 3.5 9B :: parse failure :: amb_022
- Task category: `ambiguous`
- Parse failure type: `schema_violation`
- Error: `PredictionParseError("reasoning step at index 0 must include integer 'step_id'.")`

### Qwen 3.5 9B :: verification :: con_015
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Lina approved the release in the lab', 'Sara boarded the train in the kitchen', 'BEFORE'], ['Sara boarded the train in the kitchen', 'Lina approved the release in the lab', 'BEFORE']]`
- Question: Lina approved the release in the lab happened before Sara boarded the train in the kitchen, but Sara boarded the train in the kitchen happened before Lina approved the release in the lab.
### Qwen 3.5 9B :: verification :: con_018
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Leo watered the plants in the library', 'Sam set an alarm in the lab', 'UNKNOWN']]`
- Question: Leo watered the plants in the library happened before Sam set an alarm in the lab, but Sam set an alarm in the lab happened before Leo watered the plants in the library.
### Qwen 3.5 9B :: verification :: con_009
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Hana made tea in the classroom', 'Ivy sent an email in the library', 'UNKNOWN']]`
- Question: Hana made tea in the classroom happened before Ivy sent an email in the library, but Ivy sent an email in the library happened before Hana made tea in the classroom.

## Llama 3.1 8B

### Llama 3.1 8B :: verification :: con_018
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Leo watered the plants in the library', 'Sam set an alarm in the lab', 'BEFORE'], ['Sam set an alarm in the lab', 'Leo watered the plants in the library', 'BEFORE']]`
- Question: Leo watered the plants in the library happened before Sam set an alarm in the lab, but Sam set an alarm in the lab happened before Leo watered the plants in the library.
### Llama 3.1 8B :: verification :: con_015
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Lina approved the release in the lab', 'Sara boarded the train in the kitchen', 'BEFORE'], ['Sara boarded the train in the kitchen', 'Lina approved the release in the lab', 'BEFORE']]`
- Question: Lina approved the release in the lab happened before Sara boarded the train in the kitchen, but Sara boarded the train in the kitchen happened before Lina approved the release in the lab.
### Llama 3.1 8B :: verification :: con_009
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Hana made tea in the classroom', 'Ivy sent an email in the library', 'BEFORE'], ['Ivy sent an email in the library', 'Hana made tea in the classroom', 'BEFORE']]`
- Question: Hana made tea in the classroom happened before Ivy sent an email in the library, but Ivy sent an email in the library happened before Hana made tea in the classroom.

## Mistral 7B

### Mistral 7B :: parse failure :: amb_029
- Task category: `ambiguous`
- Parse failure type: `invalid_edge_support`
- Error: `PredictionParseError("Invalid edge in 'supports': 'Noah sent an email at the office'. Invalid edge format (expected 3 items): 'Noah sent an email at the office'")`

### Mistral 7B :: verification :: con_018
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Leo watered the plants in the library', 'Sam set an alarm in the lab', 'BEFORE'], ['Sam set an alarm in the lab', 'Leo watered the plants in the library', 'BEFORE']]`
- Question: Leo watered the plants in the library happened before Sam set an alarm in the lab, but Sam set an alarm in the lab happened before Leo watered the plants in the library.
### Mistral 7B :: verification :: con_010
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Omar charged the phone in the library', 'Hana printed the handouts in the kitchen', 'BEFORE'], ['Hana printed the handouts in the kitchen', 'Omar charged the phone in the library', 'BEFORE']]`
- Question: Omar charged the phone in the library happened before Hana printed the handouts in the kitchen, but Hana printed the handouts in the kitchen happened before Omar charged the phone in the library.
### Mistral 7B :: verification :: lc_038
- Category: `linear_chain`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['Hana read the note in the kitchen', 'Ivy left the station in the kitchen', 'AFTER'], ['Ivy left the station in the kitchen', 'Zara received a confirmation email at home', 'AFTER']]`
- Question: Hana read the note in the kitchen. Afterwards, Ivy left the station in the kitchen. After that, Zara received a confirmation email at home.

## Gemma 3 12B

### Gemma 3 12B :: verification :: tr_035
- Category: `transitive_reasoning`
- First violation step: `3`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `none`
- Predicted edges: `[['Ava set an alarm in the library', 'Ruby made tea at home', 'BEFORE'], ['Ruby made tea at home', 'Leo turned on the kettle at home', 'BEFORE']]`
- Question: Ava set an alarm in the library happened before Ruby made tea at home. Ruby made tea at home happened before Leo turned on the kettle at home.
