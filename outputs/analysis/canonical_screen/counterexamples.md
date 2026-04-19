# Counterexamples

### Qwen 3.5 9B :: con_018
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Question: Leo watered the plants in the library happened before Sam set an alarm in the lab, but Sam set an alarm in the lab happened before Leo watered the plants in the library.
### Qwen 3.5 9B :: con_015
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Question: Lina approved the release in the lab happened before Sara boarded the train in the kitchen, but Sara boarded the train in the kitchen happened before Lina approved the release in the lab.
### Qwen 3.5 9B :: amb_030
- Category: `ambiguous`
- First violation step: `5`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `none`
- Question: Noah finished the lecture at home. Ben installed the update in the classroom. Ruby called a friend at the office.

### Llama 3.1 8B :: con_018
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Question: Leo watered the plants in the library happened before Sam set an alarm in the lab, but Sam set an alarm in the lab happened before Leo watered the plants in the library.
### Llama 3.1 8B :: con_015
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Question: Lina approved the release in the lab happened before Sara boarded the train in the kitchen, but Sara boarded the train in the kitchen happened before Lina approved the release in the lab.
### Llama 3.1 8B :: con_009
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Question: Hana made tea in the classroom happened before Ivy sent an email in the library, but Ivy sent an email in the library happened before Hana made tea in the classroom.

### Mistral 7B :: lc_038
- Category: `linear_chain`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Question: Hana read the note in the kitchen. Afterwards, Ivy left the station in the kitchen. After that, Zara received a confirmation email at home.
### Mistral 7B :: con_018
- Category: `contradiction`
- First violation step: `1`
- Invariant violations: `contradiction, cycle, temporal_inconsistency`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Question: Leo watered the plants in the library happened before Sam set an alarm in the lab, but Sam set an alarm in the lab happened before Leo watered the plants in the library.
### Mistral 7B :: tr_039
- Category: `transitive_reasoning`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `none`
- Question: Amir fed the cat in the library happened before Ethan boarded the train in the classroom. Ethan boarded the train in the classroom happened before Hana locked the bike at the café. Hana locked the bike at the café happened before Hana approved the release in the library.

### Gemma 3 12B :: tr_035
- Category: `transitive_reasoning`
- First violation step: `3`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `none`
- Question: Ava set an alarm in the library happened before Ruby made tea at home. Ruby made tea at home happened before Leo turned on the kettle at home.
