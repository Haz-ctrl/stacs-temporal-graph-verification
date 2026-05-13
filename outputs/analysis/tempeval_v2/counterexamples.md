# Counterexamples

## DeepSeek R1 7B

### DeepSeek R1 7B :: parse failure :: te3_test_AP_20130322_l7
- Task category: `tempeval_relation`
- Parse failure type: `invalid_edge_support`
- Error: `PredictionParseError("Invalid edge in 'supports': ['started [ei3]']. Invalid edge format (expected 3 items): ['started [ei3]']")`
### DeepSeek R1 7B :: parse failure :: te3_test_CNN_20130322_1003_l5
- Task category: `tempeval_relation`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`

### DeepSeek R1 7B :: verification :: te3_test_WSJ_20130322_159_l26
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference, unsupported_reasoning_step`
- LTL violations: `ltl_hallucinated_node, ltl_unsupported_final_commitment`
- Predicted edges: `[['said [ei19]', 'seek [ei20]', 'BEFORE']]`
- Question: Title:
Netanyahu Apologizes to Turkey for Deadly Ship Raid

Passage:
Mr. Netanyahu's office confirmed that the Israeli leader, in a conversation with Mr. Erdogan, "agreed to restore normalization between Israel and Turkey, including the dispatch of ambassadors and the cancellation of legal steps against [Israeli Defense Forces] soldiers." Mr. Erdogan accepted the Israeli apology, the prime minister's office said. Mr. Erdogan has long sought an apology for the raid in May 2010 on the Mavi Marmara, which was part of a flotilla that sought to break Israel's blockade of Gaza. An Israeli raid on the ship left nine passengers dead, all of them Turkish or of Turkish descent.

Determine the temporal relation between the following event mentions.
- said [ei19]
- sought [ei20]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### DeepSeek R1 7B :: verification :: te3_test_AP_20130322_l6
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['started [ei3]', 'sparkling [ei4]', 'BEFORE']]`
- Question: Title:
105 U.S. Kids Died From Flu, CDC Says

Passage:
The season started about a month earlier than usual, sparking concerns it might turn into the worst in a decade. It ended up being very hard on the elderly, but was moderately severe overall, according to the Centers for Disease Control and Prevention.

Determine the temporal relation between the following event mentions.
- sparking [ei4]
- started [ei3]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### DeepSeek R1 7B :: verification :: te3_test_AP_20130322_l54
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['Event A', 'Event B', 'BEFORE']]`
- Question: Title:
105 U.S. Kids Died From Flu, CDC Says

Passage:
This flu season started in early December, a month earlier than usual, and peaked by the end of year. Since then, flu reports have been dropping off throughout the country.

Determine the temporal relation between the following event mentions.
- started [ei1000027]
- started [ei27]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Qwen 3.5 9B

### Qwen 3.5 9B :: parse failure :: te3_test_AP_20130322_l11
- Task category: `tempeval_relation`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError('Invalid JSON: Could not find JSON object in model output:\n')`
### Qwen 3.5 9B :: parse failure :: te3_test_AP_20130322_l38
- Task category: `tempeval_relation`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError('Invalid JSON: Could not find JSON object in model output:\n')`

### Qwen 3.5 9B :: verification :: te3_test_WSJ_20130322_159_l57
- Category: `tempeval_relation`
- First violation step: `2`
- Invariant violations: `none`
- LTL violations: `ltl_unsupported_final_commitment`
- Predicted edges: `[['restore [ei45]', 'said [ei42]', 'AFTER']]`
- Question: Title:
Netanyahu Apologizes to Turkey for Deadly Ship Raid

Passage:
Mr. Obama said later at a news conference in Amman that he had spoken to both leaders over the past two years about how it was in the interests of both countries to restore normal relations.

Determine the temporal relation between the following event mentions.
- restore [ei45]
- said [ei42]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Qwen 3.5 9B :: verification :: te3_test_bbc_20130322_1150_l9
- Category: `tempeval_relation`
- First violation step: `2`
- Invariant violations: `none`
- LTL violations: `ltl_unsupported_final_commitment`
- Predicted edges: `[['died [ei3]', 'helped [ei4]', 'AFTER']]`
- Question: Title:
Last 1953 Everest team member George Lowe dies, aged 89

Passage:
George Lowe, 89, died in Ripley on Wednesday after a long-term illness, with his wife Mary by his side. New Zealand-born Mr Lowe was part of the team that helped Sir Edmund Hillary and Tenzing Norgay to the summit in 1953.

Determine the temporal relation between the following event mentions.
- died [ei3]
- helped [ei4]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Qwen 3.5 9B :: verification :: te3_test_bbc_20130322_1150_l18
- Category: `tempeval_relation`
- First violation step: `2`
- Invariant violations: `none`
- LTL violations: `ltl_unsupported_final_commitment`
- Predicted edges: `[['crossing [ei11]', 'took [ei8]', 'SIMULTANEOUS']]`
- Question: Title:
Last 1953 Everest team member George Lowe dies, aged 89

Passage:
Mr Lowe also took part in the trans-Antarctic expedition of 1957-58, which made the first successful overland crossing of Antarctica via the South Pole.

Determine the temporal relation between the following event mentions.
- crossing [ei11]
- took [ei8]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

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

### Mistral 7B :: verification :: te3_test_CNN_20130322_1003_l209
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['uncovered [ei36]', 'unaware [ei2003]', 'BEFORE']]`
- Question: Title:
New York man admits faking his death

Passage:
Evana Roth told CNN in August she thought her husband devised the plan after he was fired from his job in July. Her attorney, Lenard Leeds, said she had been unaware of the ruse before she uncovered the e-mail correspondence.

Determine the temporal relation between the following event mentions.
- uncovered [ei36]
- unaware [ei2003]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Mistral 7B :: verification :: te3_test_nyt_20130321_cyprus_l22
- Category: `tempeval_relation`
- First violation step: `1`
- Invariant violations: `unsupported_reasoning_step`
- LTL violations: `ltl_contradiction, ltl_temporal_inconsistency`
- Predicted edges: `[['make [ei14]', 'forming [ei15]', 'BEFORE']]`
- Question: Title:
For Euro Zone, a Cyprus Exit Would Have Little Impact

Passage:
As debts in Europe mount in inverse proportion to the ability of its citizens, companies and governments to make good on them, the view is forming in Berlin and Brussels that a signal must be sent that citizens and investors must start accepting losses for the euro zone to survive in the long run.

Determine the temporal relation between the following event mentions.
- make [ei14]
- forming [ei15]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Mistral 7B :: verification :: te3_test_CNN_20130322_314_l11
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['sected [ei8]', 'eased [ei9]', 'BEFORE']]`
- Question: Title:
Obama gets diplomatic coup before heading to refugee-flooded Jordan

Passage:
The apology, long sought by Turkish Prime Minister Recep Erdogan, eased strained feelings between Turkey and Israel, two vital U.S. allies in the Middle East.

Determine the temporal relation between the following event mentions.
- sought [ei8]
- eased [ei9]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Gemma 3 12B

### Gemma 3 12B :: verification :: te3_test_CNN_20130322_248_l106
- Category: `tempeval_relation`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['announced [ei1]', 's sparing [ei3]', 'BEFORE']]`
- Question: Title:
FAA to close 149 regional airport control towers, spare 40 others

Passage:
The FAA on Friday announced it will close 149 regional airport control towers because of forced spending cuts -- sparing 40 others that the FAA had been expected to shutter.

Determine the temporal relation between the following event mentions.
- sparing [ei3]
- announced [ei1]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
