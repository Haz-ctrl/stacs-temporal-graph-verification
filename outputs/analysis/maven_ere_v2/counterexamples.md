# Counterexamples

## DeepSeek R1 7B

### DeepSeek R1 7B :: parse failure :: maven_ere_valid_72f377d680499b8c5466e35819dda1a0_0002757
- Task category: `maven_ere_temporal`
- Parse failure type: `invalid_edge_support`
- Error: `PredictionParseError("Invalid edge in 'supports': ['weakened', 'AFTER']. Invalid edge format (expected 3 items): ['weakened', 'AFTER']")`
### DeepSeek R1 7B :: parse failure :: maven_ere_valid_d8c798e1195d7b3c089be22027798924_0000383
- Task category: `maven_ere_temporal`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`

### DeepSeek R1 7B :: verification :: maven_ere_valid_760ca28a123fb082a2010239d8e3d981_0001842
- Category: `maven_ere_temporal`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['envisioned', 'recognize [7b59dffd2f050a2d71dcb26cdca449e7]', 'SIMULTANEOUS']]`
- Question: Title:
Tehran Conference

Passage:
Although the three leaders arrived with differing objectives, the main outcome of the Tehran Conference was the Western Allies' commitment to open a second front against Nazi Germany. The conference also addressed the 'Big Three' Allies' relations with Turkey and Iran, operations in Yugoslavia and against Japan, and the envisaged post-war settlement. A separate protocol signed at the conference pledged the Big Three to recognize Iran's independence.

Determine the temporal relation between the following mentions.
- envisaged [a16dcc9c6e850ebfaacb642b76896a0a]
- recognize [7b59dffd2f050a2d71dcb26cdca449e7]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### DeepSeek R1 7B :: verification :: maven_ere_valid_7a731419eb28b1d83f55a76798805de2_0002720
- Category: `maven_ere_temporal`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['influenced [c9a9b5e3ce6301688ca78a3ff88e2a20]', 'withdrawn [b5c4d5f74162b88589c46780bb7e6299]', 'BEFORE']]`
- Question: Title:
Cedar Revolution

Passage:
The popular movement was remarkable for its avoidance of violence, peaceful approach, and its total reliance on methods of civil resistance. The primary goals of the activists were the withdrawal of Syrian troops from Lebanon and the replacement of a government heavily influenced by Syrian interests with more independent leadership, the establishment of an international commission to investigate the assassination of Prime Minister Hariri, the resignation of security officials to ensure the success of the plan, and the organization of free parliamentary elections. The demonstrators demanded the end of the Syrian influence in Lebanese politics. At the start of the demonstrations, Syria had been maintaining a force of roughly 14,000 soldiers and intelligence agents in Lebanon. Following the demonstrations, the Syrian troops completely withdrew from Lebanon on 27 April 2005. With the disbanding of the Pro-Syrian government, the main goals of the revolution were achieved.

Determine the temporal relation between the following mentions.
- influenced [c9a9b5e3ce6301688ca78a3ff88e2a20]
- withdrew [b5c4d5f74162b88589c46780bb7e6299]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### DeepSeek R1 7B :: verification :: maven_ere_valid_bf2e372ff38b2a7204a3f6974514217c_0001497
- Category: `maven_ere_temporal`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['led [bfc6c38a85f274d4b2bfd4a6f024e4b6]', 'withdrawn', 'BEFORE']]`
- Question: Title:
Battle of Marj Ardabil

Passage:
Following their victory, the Khazars occupied Ardabil. The next year, however, Barjik led an army to Mosul and was defeated. According to Muhammad ibn Jarir al-Tabari and other Arab historians, the Muslims were so enraged by Barjik's desecration of their commander's head that they fought with extra vigor. The Khazar army at Mosul was defeated and withdrew north of the Caucasus Mountains.

Determine the temporal relation between the following mentions.
- led [bfc6c38a85f274d4b2bfd4a6f024e4b6]
- withdrew [3d56c7cce4f462ef12f4ec88f76f6cde]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Qwen 3.5 9B

### Qwen 3.5 9B :: parse failure :: maven_ere_valid_72f377d680499b8c5466e35819dda1a0_0002757
- Task category: `maven_ere_temporal`
- Parse failure type: `transport_timeout`
- Error: `OllamaTransportError("Ollama request timed out after 4 attempt(s): HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)")`
### Qwen 3.5 9B :: parse failure :: maven_ere_valid_31fd3808e8fe6b0e88ca7d9abd1a6199_0000739
- Task category: `maven_ere_temporal`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError('Invalid JSON: Could not find balanced JSON object in model output:\n{\n  "answer": "SIMULTANEOUS",\n  "events": ["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]"],\n  "relations": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n  "reasoning_steps": [\n    {\n      "step_id": 1,\n      "text": "The passage states \'The strike had also disrupted services\', indicating that the disruption occurred to the services as part of the same event description.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 1,\n      "text": "The phrase \'disrupted services\' describes a single event where the disruption action applies to the services simultaneously.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 2,\n      "text": "Since the disruption and services are mentioned together in the same clause describing the strike\'s effect, they occur at the same time.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 3,\n      "text": "Therefore, the temporal relation between disrupted and services is SIMULTANEOUS.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 4,\n      "text": "The disruption of services is described as a single event in the passage.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 5,\n      "text": "Both mentions refer to the same temporal occurrence.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 6,\n      "text": "The relation is SIMULTANEOUS.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 7,\n      "text": "Final conclusion based on passage analysis.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 8,\n      "text": "The disruption happened to services at the same time.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 9,\n      "text": "This confirms SIMULTANEOUS relation.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 10,\n      "text": "The answer is SIMULTANEOUS.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 11,\n      "text": "Reasoning complete.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 12,\n      "text": "Final step.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 13,\n      "text": "Done.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 14,\n      "text": "End.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 15,\n      "text": "Finish.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 16,\n      "text": "Complete.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 17,\n      "text": "End of reasoning.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 18,\n      "text": "Final.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 19,\n      "text": "Done.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 20,\n      "text": "End.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 21,\n      "text": "Finish.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 22,\n      "text": "Complete.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e91777052eb]", "services [5794ac7e4020fc5ba84aef4409d6869e]", "SIMULTANEOUS"]],\n      "step_id": 23,\n      "text": "End.",\n      "supports": [["disrupted [a17b72edd36cefd7f57c1e9177705')`

### Qwen 3.5 9B :: verification :: maven_ere_valid_384f1e5ac0eb675eb433c993efcd8837_0002858
- Category: `maven_ere_temporal`
- First violation step: `2`
- Invariant violations: `none`
- LTL violations: `ltl_unsupported_final_commitment`
- Predicted edges: `[['divided [f82b8795433d81ee0e7e34af25438307]', 'succeeded [5981cce99a8ac57fd64bb586a16266ca]', 'SIMULTANEOUS']]`
- Question: Title:
Second EDSA Revolution

Passage:
The Second EDSA Revolution (EDSA II or EDSA Dos) was a three-day political protest from January 17–20, 2001 that peacefully overthrew the government of Joseph Estrada, the thirteenth President of the Philippines. Estrada resigned and was succeeded by his Vice-President, Gloria Macapagal-Arroyo, who was sworn into office by then-Chief Justice Hilario Davide Jr. at around noon on January 20, 2001, several hours before Estrada fled Malacañang Palace. EDSA is an acronym derived from Epifanio de los Santos Avenue, the major thoroughfare connecting five cities in Metro Manila, namely Pasay, Makati, Mandaluyong, Quezon City, and Caloocan, with the revolution's epicentre at the EDSA Shrine church at the northern tip of Ortigas Center, a business district. Advocates described EDSA II as "popular" but critics view the uprising as a conspiracy among political and business elites, military top brass and Catholic Cardinal Jaime Sin. International reaction to the revolt was mixed, with some foreign nations including the United States immediately recognising the legitimacy of Arroyo's presidency, and foreign commentators describing it as "a defeat for due process of law", "mob rule", and a ""de facto" coup". The only means of legitimizing the event was the last-minute Supreme Court ruling that "the welfare of the people is the supreme law." But by then, the Armed Forces of the Philippines had already withdrawn support for the president, which some analysts called unconstitutional, and most foreign political analysts agreeing with this assessment. William Overholt, a Hong Kong-based political economist said that "It is either being called mob rule or mob rule as a cover for a well-planned coup, ... but either way, it's not democracy." It should also be noted that opinion was divided during EDSA II about whether Gloria Macapagal-Arroyo as the incumbent Vice President should be President if Joseph Estrada was ousted; many groups who participated in EDSA II expressly stated that they did not want Arroyo for president either, and some of them would later participate in EDSA III. The prevailing Constitution of the Philippines calls for the Vice President of the Philippines, Arroyo at the time, to act as interim president only when the sitting President dies, resigns, or becomes incapacitated, none of which occurred during EDSA II.

Determine the temporal relation between the following mentions.
- divided [f82b8795433d81ee0e7e34af25438307]
- succeeded [5981cce99a8ac57fd64bb586a16266ca]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Qwen 3.5 9B :: verification :: maven_ere_valid_4d3bba0b937af1ce165c9954ac588498_0000590
- Category: `maven_ere_temporal`
- First violation step: `2`
- Invariant violations: `none`
- LTL violations: `ltl_unsupported_final_commitment`
- Predicted edges: `[['Wars [6efac9dea2111cd97389f6f212d5f88b]', 'War [121d2fe947e6bc5d725ca54d77f06f60]', 'SIMULTANEOUS']]`
- Question: Title:
Battle of Monastir

Passage:
The Battle of Monastir took place near the town of Bitola, Macedonia (then known as Monastir) during the First Balkan War, from the 16th to 19th November 1912. As an ongoing part of the Balkan Wars, the Ottoman Vardar Army retreated from the defeat at Kumanovo and regrouped around Bitola. The Serbian 1st Army, marching for Bitola, encountered heavy Ottoman artillery fire and had to wait for its own artillery to arrive.

Determine the temporal relation between the following mentions.
- Wars [6efac9dea2111cd97389f6f212d5f88b]
- War [121d2fe947e6bc5d725ca54d77f06f60]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Qwen 3.5 9B :: verification :: maven_ere_valid_d69d964fc88ea4ec923cddbbb26af83d_0001751
- Category: `maven_ere_temporal`
- First violation step: `2`
- Invariant violations: `none`
- LTL violations: `ltl_unsupported_final_commitment`
- Predicted edges: `[['cancelled [f71d4426f1dc81defab1a756d09481e7]', 'emerging [0316efdfebfc51ea4cc7743407b436d4]', 'AFTER']]`
- Question: Title:
Hurricane Kate (1985)

Passage:
A favorable atmospheric pattern allowed the newly developed system to intensify to hurricane intensity on November 16, and further to Category 2 intensity three days later. Kate made its first landfall on the northern coast of Cuba at this intensity prior to emerging as a slightly weaker storm during the evening hours of November 19. Once clear of land, it began to strengthen quickly, becoming a Category 3 and reaching its peak intensity of 120 mph (195 km/h) the following day. On November 21, a cold front moving across the Mississippi Valley resulted in a north and eventual northeast turn of the cyclone, and on November 22, Kate came ashore near Mexico Beach, Florida, as a minimal Category 2 hurricane with winds of 100 mph (160 km/h) . Gradual weakening ensued as the cyclone moved along the Southeast United States coastline, and Kate transitioned to an extratropical cyclone on November 23, a day after exiting the coastline of North Carolina. The threat of Hurricane Kate in Cuba prompted the evacuation of 360,000 people. Heavy rainfall in Cuba caused numerous mudslides and flooding, killing 10 people and leading to severe agriculture damage. Wind gusts over hurricane intensity resulted in widespread power outages, significant building damage, and major crop damage. Damage totaled roughly $400 million, making it the most damaging hurricane to strike the island in many decades. In preparation for the system's arrival, many hurricane watches and warnings were put into effect. Hundreds of thousands of residents were evacuated, and Florida governor Bob Graham declared a state of emergency for six counties; this was later cancelled following the relatively minor impacts of Kate. In addition, many shelters were opened.

Determine the temporal relation between the following mentions.
- cancelled [f71d4426f1dc81defab1a756d09481e7]
- emerging [0316efdfebfc51ea4cc7743407b436d4]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Llama 3.1 8B

### Llama 3.1 8B :: parse failure :: maven_ere_valid_4d79690291c4ab2f22e4c05077ffa68c_0001361
- Task category: `maven_ere_temporal`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`

### Llama 3.1 8B :: verification :: maven_ere_valid_3cc342ad98551ff38d465560405c56eb_0000479
- Category: `maven_ere_temporal`
- First violation step: `0`
- Invariant violations: `hallucinated_node, unsupported_reasoning_reference`
- LTL violations: `ltl_hallucinated_node`
- Predicted edges: `[['released [87e108e8b916dc8570fd0e267b3468b8]', 'debut [c9878a6792f92af878a68f989f3c909b]', 'AFTER']]`
- Question: Title:
V (Anna Abreu album)

Passage:
V is the fifth studio album by Finnish singer Anna Abreu, released in Finland by Warner Bros. Records on May 30, 2014. The album was preceded by the lead single "Ra-Ta Ta-Ta" and followed by the single "Right In Front Of You". The album marked Abreu's first studio album in three years, following her fourth album "Rush". It was also Abreu's first album released under Warner Bros. Records, which she signed with in 2012 after deciding not to renew her contract with Sony Music and RCA. The album was produced by Jonas Karlsson, Jarkko Ehnqvist and Hank Solo, and features collaborations with Danish pop singer Christopher and Finnish rapper Gracias. The album debuted and peaked at number 4 on the Finnish Albums Chart, becoming Abreu's first album to miss the top two. However, the album continued to be a commercial and critical success for Abreu, being certified gold for sales in excess of 10,000 copies.

Determine the temporal relation between the following mentions.
- released [87e108e8b916dc8570fd0e267b3468b8]
- debuted [c9878a6792f92af878a68f989f3c909b]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.

## Mistral 7B

### Mistral 7B :: parse failure :: maven_ere_valid_71e430c5d69a41cb7f08df35dc391b31_0001645
- Task category: `maven_ere_temporal`
- Parse failure type: `invalid_json`
- Error: `PredictionParseError("Invalid JSON: Expecting ',' delimiter")`

### Mistral 7B :: verification :: maven_ere_valid_876f8af5e82d25ca356bd61ac3216aea_0002969
- Category: `maven_ere_temporal`
- First violation step: `1`
- Invariant violations: `hallucinated_node, unsupported_reasoning_step`
- LTL violations: `ltl_hallucinated_node, ltl_unsupported_final_commitment`
- Predicted edges: `[['ceremony [c128883ba5c134a71323fce2dd4528faa]', 'ceremony [4bbaff68946fbe040d0dfc3391e08388]', 'BEFORE']]`
- Question: Title:
2012 Summer Paralympics closing ceremony

Passage:
The closing ceremony of the 2012 Summer Paralympics, also known as The Festival of the Flame, was held on 9 September at the Olympic Stadium in London. Kim Gavin (who also directed the closing ceremony of the 2012 Summer Olympics) served as director for the ceremony, while Stephen Daldry served as its executive producer. The ceremony was themed around festivals and the four seasons, and was set to music performed live by the British rock group Coldplay, also joined by special guest performers such as the British Paraorchestra, Rihanna and Jay-Z.

Determine the temporal relation between the following mentions.
- ceremony [c12883ba5c134a71323fce2dd4528faa]
- ceremony [4bbaff68946fbe040d0dfc3391e08388]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Mistral 7B :: verification :: maven_ere_valid_cac47d54e0f18373496381e30d1fb71d_0000207
- Category: `maven_ere_temporal`
- First violation step: `1`
- Invariant violations: `hallucinated_node`
- LTL violations: `ltl_hallucinated_node, ltl_unsupported_final_commitment`
- Predicted edges: `[['taking place [3834b84ed3ef9eef600bb9762d2656de]', 'tying [03012f6ce0bb916ebf521512dd086d8e]', 'BEFORE']]`
- Question: Title:
2014 US Open (tennis)

Passage:
It was the 134th edition of the US Open, the fourth and final Grand Slam event of the year. It took place at the USTA Billie Jean King National Tennis Center. Rafael Nadal was the defending champion in the men's event; however, on 18 August, the Spaniard announced his withdrawal from the event after failing to recover from a wrist injury, while Serena Williams was the two-time defending champion in the women's event. In the men's singles competition, Marin Čilić won his maiden grand slam title; while, Serena Williams won her Open era record tying sixth title in the women's singles competition tying Chris Evert, and it was her eighteenth grand slam title tying Evert and Martina Navratilova. Winning the men's doubles, Bob Bryan and Mike Bryan became the most victorious doubles team in Open era history at the tournament, and this was the team's 100th title together and sixteenth grand slam title tying Todd Woodbridge for the Open era record.

Determine the temporal relation between the following mentions.
- took place [3834b84ed3ef9eef600bb9762d2656de]
- tying [03012f6ce0bb916ebf521512dd086d8e]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
### Mistral 7B :: verification :: maven_ere_valid_156426a35e873b9201745dec7c97d251_0001114
- Category: `maven_ere_temporal`
- First violation step: `1`
- Invariant violations: `hallucinated_node`
- LTL violations: `ltl_hallucinated_node, ltl_unsupported_final_commitment`
- Predicted edges: `[['becoming [decb7e6607fe4edfd10d8c3a0a70736b]', 'leaving [035af44c5ea71ca1cdc42a127ed7fc2d]', 'BEFORE']]`
- Question: Title:
Tropical Storm Beryl (2012)

Passage:
It quickly weakened to a tropical depression, dropping heavy rainfall while moving slowly across the southeastern United States. A cold front turned Beryl to the northeast, and the storm became extratropical on May 30. The precursor to Beryl produced heavy rainfall in Cuba, causing flooding, mudslides and two deaths. Torrential rain also affected south Florida and the Bahamas. After forming, Beryl produced rough surf along the US southeastern coast, leaving one person from Folly Beach, South Carolina missing. Upon making landfall in Florida, the storm produced strong winds that left 38,000 people without power.

Determine the temporal relation between the following mentions.
- became [decb7e6607fe4edfd10d8c3a0a70736b]
- leaving [035af44c5ea71ca1cdc42a127ed7fc2d]

Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.
