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

### DeepSeek R1 7B :: verification :: te3_test_WSJ_20130322_159_l26
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference, unsupported_reasoning_step`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['said [ei19]', 'seek [ei20]', 'BEFORE']]`
- Question: Title:
Netanyahu Apologizes to Turkey for Deadly Ship Raid

Passage:
Mr. Netanyahu's office confirmed that the Israeli leader, in a conversation with Mr. Erdogan, "agreed to restore normalization between Israel and Turkey, including the dispatch of ambassadors and the cancellation of legal steps against [Israeli Defense Forces] soldiers." Mr. Erdogan accepted the Israeli apology, the prime minister's office said. Mr. Erdogan has long sought an apology for the raid in May 2010 on the Mavi Marmara, which was part of a flotilla that sought to break Israel's blockade of Gaza. An Israeli raid on the ship left nine passengers dead, all of them Turkish or of Turkish descent.

Determine the temporal relation between the following event mentions.
- said [ei19]
- sought [ei20]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### DeepSeek R1 7B :: verification :: te3_test_nyt_20130321_women_senate_l7
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['marched [ei6]', 'cast [ei5]', 'AFTER']]`
- Question: Title:
Once Few, Women Hold More Power in Senate

Passage:
An hour before her colleagues gathered for their first vote of a new Congress, Senator Kelly Ayotte slipped into an empty Senate chamber to savor the grandeur of her legislative home. As Ms. Ayotte, a freshman Republican from New Hampshire, sat down at the wooden desk where generations of lawmakers from her state had cast their votes, a doorman marched toward her with purpose.

Determine the temporal relation between the following event mentions.
- cast [ei5]
- marched [ei6]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### DeepSeek R1 7B :: verification :: te3_test_CNN_20130322_1003_l526
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['russe', 'unaware [ei2003]', 'BEFORE']]`
- Question: Title:
New York man admits faking his death

Passage:
Evana Roth told CNN in August she thought her husband devised the plan after he was fired from his job in July. Her attorney, Lenard Leeds, said she had been unaware of the ruse before she uncovered the e-mail correspondence.

Determine the temporal relation between the following event mentions.
- ruse [ei35]
- unaware [ei2003]

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


## Llama 3.1 8B

### Llama 3.1 8B :: verification :: te3_test_WSJ_20130318_731_l8
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['broke [ei1]', 'hopping [ei7]', 'AFTER']]`
- Question: Title:
A New Game for Microsoft's Kinect

Passage:
Microsoft Corp. broke sales records in 2010 when it released its Kinect - a movement-tracking device that enabled Xbox users to play their favorite games through gestures alone, without need of a controller. Now, with the help of outside developers, the software giant is hoping to move the Kinect beyond gaming.

Determine the temporal relation between the following event mentions.
- broke [ei1]
- hoping [ei7]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Llama 3.1 8B :: verification :: te3_test_WSJ_20130318_731_l9
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['help [ei6]', 'hopping [ei7]', 'AFTER']]`
- Question: Title:
A New Game for Microsoft's Kinect

Passage:
Now, with the help of outside developers, the software giant is hoping to move the Kinect beyond gaming.

Determine the temporal relation between the following event mentions.
- help [ei6]
- hoping [ei7]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Llama 3.1 8B :: verification :: te3_test_WSJ_20130318_731_l12
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['hopping [ei7]', 'expanding [ei9]', 'AFTER']]`
- Question: Title:
A New Game for Microsoft's Kinect

Passage:
Now, with the help of outside developers, the software giant is hoping to move the Kinect beyond gaming. Microsoft is expanding into China with a company-funded incubator program for outside developers to build products based on Kinect technology for a range of industries including health care and retail.

Determine the temporal relation between the following event mentions.
- hoping [ei7]
- expanding [ei9]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Mistral 7B

### Mistral 7B :: parse failure :: te3_test_nyt_20130321_china_pollution_l27
- Task category: `tempeval_relation`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`

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
### Mistral 7B :: verification :: te3_test_WSJ_20130322_159_l15
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['confirmed [ei12]', 'outcome [ei8]', 'BEFORE']]`
- Question: Title:
Netanyahu Apologizes to Turkey for Deadly Ship Raid

Passage:
The call, which happened as President Barack Obama wrapped up his first presidential visit to Israel, was an unexpected outcome from a Mideast trip that seemed to yield few concrete steps. Mr. Netanyahu's office confirmed that the Israeli leader, in a conversation with Mr. Erdogan, "agreed to restore normalization between Israel and Turkey, including the dispatch of ambassadors and the cancellation of legal steps against [Israeli Defense Forces] soldiers." Mr. Erdogan accepted the Israeli apology, the prime minister's office said.

Determine the temporal relation between the following event mentions.
- outcome [ei8]
- confirmed [ei12]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Mistral 7B :: verification :: te3_test_AP_20130322_l17
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['ei6', 'ei9', 'BEFORE']]`
- Question: Title:
105 U.S. Kids Died From Flu, CDC Says

Passage:
The season started about a month earlier than usual, sparking concerns it might turn into the worst in a decade. It ended up being very hard on the elderly, but was moderately severe overall, according to the Centers for Disease Control and Prevention. Six of the pediatric deaths were reported in the last week, and it's possible there will be more, said the CDC's Dr. Michael Jhung said Friday.

Determine the temporal relation between the following event mentions.
- ended [ei6]
- said [ei9]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
