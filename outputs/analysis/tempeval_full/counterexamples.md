# Counterexamples

## DeepSeek R1 7B

### DeepSeek R1 7B :: parse failure :: te3_test_AP_20130322_l7
- Task category: `tempeval_relation`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`
### DeepSeek R1 7B :: parse failure :: te3_test_CNN_20130321_821_l5
- Task category: `tempeval_relation`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`

### DeepSeek R1 7B :: verification :: te3_test_nyt_20130321_women_senate_l7
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference, unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency, ltl_hallucinated_node`
- Predicted edges: `[['marched', 'cast', 'AFTER']]`
- Question: Title:
Once Few, Women Hold More Power in Senate

Passage:
An hour before her colleagues gathered for their first vote of a new Congress, Senator Kelly Ayotte slipped into an empty Senate chamber to savor the grandeur of her legislative home. As Ms. Ayotte, a freshman Republican from New Hampshire, sat down at the wooden desk where generations of lawmakers from her state had cast their votes, a doorman marched toward her with purpose.

Determine the temporal relation between the following event mentions.
- cast [ei5]
- marched [ei6]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### DeepSeek R1 7B :: verification :: te3_test_CNN_20130321_821_l104
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference, unsupported_reasoning_step`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['tries', 'undermine', 'BEFORE']]`
- Question: Title:
How Obama has weaponized wit

Passage:
Obama's humor is often delivered the way a comedian dealing with a heckler would do it. He tries to undermine his opponents with it and get the crowd -- in this case the public -- on his side. I can assure you that having a crowd laugh at your critic/heckler is not only effective in dominating them, it's also very satisfying.

Determine the temporal relation between the following event mentions.
- undermine [ei1003]
- tries [ei1002]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### DeepSeek R1 7B :: verification :: te3_test_CNN_20130322_1003_l20
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference, unsupported_reasoning_step`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['learned', 'showed', 'BEFORE']]`
- Question: Title:
New York man admits faking his death

Passage:
Raymond Roth, 48, of Massapequa, New York, was first reported missing in the waters off Jones Beach late last July by his 22-year-old son, Jonathan Roth. Several days into an extensive search involving multiple agencies, New York State Park Police said, authorities learned the missing man was in South Carolina, where he had been pulled over for speeding. The day before Raymond Roth was pulled over, his wife, Evana, showed authorities e-mails she had discovered that appeared to detail a plan between him and his son to fake his death. Raymond Roth wanted his wife and son to collect at least $410,000 in life insurance benefits while he started a new life in Florida, Rice said.

Determine the temporal relation between the following event mentions.
- learned [ei10]
- showed [ei13]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Qwen 3.5 9B

### Qwen 3.5 9B :: parse failure :: te3_test_AP_20130322_l17
- Task category: `tempeval_relation`
- Parse failure type: `transport_timeout`
- Error: `OllamaTransportError("Ollama request timed out after 1 attempt(s): HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)")`
### Qwen 3.5 9B :: parse failure :: te3_test_AP_20130322_l38
- Task category: `tempeval_relation`
- Parse failure type: `transport_timeout`
- Error: `OllamaTransportError("Ollama request timed out after 1 attempt(s): HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)")`

### Qwen 3.5 9B :: verification :: te3_test_WSJ_20130318_731_l15
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['expanding', 'selected', 'AFTER']]`
- Question: Title:
A New Game for Microsoft's Kinect

Passage:
Microsoft is expanding into China with a company-funded incubator program for outside developers to build products based on Kinect technology for a range of industries including health care and retail. In the U.S., 11 companies were selected last year for the accelerator's first three-month class in Seattle, out of nearly 500 applicants. Microsoft said it has identified three companies for the China program to run through June.

Determine the temporal relation between the following event mentions.
- expanding [ei9]
- selected [ei10]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Qwen 3.5 9B :: verification :: te3_test_WSJ_20130322_159_l61
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['visit', 'said', 'BEFORE']]`
- Question: Title:
Netanyahu Apologizes to Turkey for Deadly Ship Raid

Passage:
He said he discussed the issue with Mr. Netanyahu during his visit to Israel this week, and that they agreed the timing was good for a discussion with the Turkish leader.

Determine the temporal relation between the following event mentions.
- visit [ei48]
- said [ei46]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Qwen 3.5 9B :: verification :: te3_test_bbc_20130322_1353_l40
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['fire', 'said', 'BEFORE']]`
- Question: Title:
Israel PM apologies for Gaza flotilla deaths

Passage:
The activists said the troops had opened fire as soon as they boarded the vessel, which was in international waters at the time.

Determine the temporal relation between the following event mentions.
- fire [ei30]
- said [ei28]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Llama 3.1 8B

### Llama 3.1 8B :: verification :: te3_test_AP_20130322_l7
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['turn', 'started', 'BEFORE']]`
- Question: Title:
105 U.S. Kids Died From Flu, CDC Says

Passage:
The season started about a month earlier than usual, sparking concerns it might turn into the worst in a decade. It ended up being very hard on the elderly, but was moderately severe overall, according to the Centers for Disease Control and Prevention.

Determine the temporal relation between the following event mentions.
- turn [ei5]
- started [ei3]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Llama 3.1 8B :: verification :: te3_test_AP_20130322_l33
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['vaccinated', 'said', 'AFTER']]`
- Question: Title:
105 U.S. Kids Died From Flu, CDC Says

Passage:
All but four of the children who died were old enough to be vaccinated, but 90 percent of them did not get vaccinated, CDC officials said.

Determine the temporal relation between the following event mentions.
- vaccinated [ei17]
- said [ei20]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Llama 3.1 8B :: verification :: te3_test_AP_20130322_l35
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['vaccinated', 'said', 'AFTER']]`
- Question: Title:
105 U.S. Kids Died From Flu, CDC Says

Passage:
All but four of the children who died were old enough to be vaccinated, but 90 percent of them did not get vaccinated, CDC officials said.

Determine the temporal relation between the following event mentions.
- vaccinated [ei19]
- said [ei20]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Mistral 7B

### Mistral 7B :: parse failure :: te3_test_nyt_20130321_china_pollution_l27
- Task category: `tempeval_relation`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`

### Mistral 7B :: verification :: te3_test_CNN_20130322_1003_l207
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `hallucinated_node, unsupported_reasoning_step`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['ruse [ei35]', 'fake [ei20001]', 'BEFORE']]`
- Question: Title:
New York man admits faking his death

Passage:
The day before Raymond Roth was pulled over, his wife, Evana, showed authorities e-mails she had discovered that appeared to detail a plan between him and his son to fake his death. Raymond Roth wanted his wife and son to collect at least $410,000 in life insurance benefits while he started a new life in Florida, Rice said. State police arrested both men in early August on charges of insurance fraud, conspiracy and filing a false report. Raymond Roth on Thursday agreed to plead guilty to the conspiracy charge in exchange for a sentence of 90 days in jail and five years' probation, the district attorney's office said. He also must pay restitution for the cost of the search -- $27,445 to the U.S. Coast Guard and $9,109 to the Nassau County Police Department. Evana Roth told CNN in August she thought her husband devised the plan after he was fired from his job in July. Her attorney, Lenard Leeds, said she had been unaware of the ruse before she uncovered the e-mail correspondence.

Determine the temporal relation between the following event mentions.
- ruse [ei35]
- fake [ei2001]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Mistral 7B :: verification :: te3_test_CNN_20130322_1003_l209
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `hallucinated_node, unsupported_reasoning_step`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['uncovered [ei36]', 'unaware [ei20003]', 'BEFORE']]`
- Question: Title:
New York man admits faking his death

Passage:
Evana Roth told CNN in August she thought her husband devised the plan after he was fired from his job in July. Her attorney, Lenard Leeds, said she had been unaware of the ruse before she uncovered the e-mail correspondence.

Determine the temporal relation between the following event mentions.
- uncovered [ei36]
- unaware [ei2003]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Mistral 7B :: verification :: te3_test_CNN_20130322_1243_l63
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['filling [ei42]', 'gives [ei43]', 'BEFORE']]`
- Question: Title:
Google Keep is a note-taking app with great potential

Passage:
In filling a minor, but important gap in its mobile ecosystem, Google gives the competition one less claim of superiority over Android.

Determine the temporal relation between the following event mentions.
- filling [ei42]
- gives [ei43]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Gemma 3 12B

### Gemma 3 12B :: verification :: te3_test_nyt_20130321_cyprus_l204
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['bAILED [ei6]', 'havoc [ei4]', 'BEFORE']]`
- Question: Title:
For Euro Zone, a Cyprus Exit Would Have Little Impact

Passage:
ut for the broader financial system in Europe, the losses resulting from a Cypriot banking collapse and the country's return to its former currency would be minimal compared with the havoc that Greece would have created had it not been bailed out.

Determine the temporal relation between the following event mentions.
- bailed [ei6]
- havoc [ei4]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
