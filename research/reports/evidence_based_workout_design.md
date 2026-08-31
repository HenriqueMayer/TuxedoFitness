# Evidence-Based Workout Design for General-Population Adults: Independent Deep Research Synthesis

## Scope, evidence hierarchy, and the most defensible conclusions

This review was conducted **independently from the report you already generated**. I used only the research problem and population defined in your prompt to establish scope; I did not use, infer, or attempt to reproduce the conclusions of the previous report. The evidence search was centered on healthy or generally active adults, sedentary/untrained adults where available, adults with overweight/obesity, and common musculoskeletal conditions relevant to recreational exercise. Competitive-athlete-specific optimization was deliberately deprioritized.

The strongest current umbrella source is the **2026 American College of Sports Medicine Position Stand on resistance training**, the first major ACSM update since 2009. It synthesized **137 systematic reviews representing more than 30,000 participants** and concluded that, for the average healthy adult, the largest benefit comes from progressing from no resistance training to consistent resistance training; sophisticated periodization, specific equipment choices, and routinely training to momentary failure are substantially less important than regular participation, adequate effort, and sufficient volume. ACSM specifically highlights approximately **≥80% 1RM and 2–3 sets per exercise for maximizing strength**, approximately **10 weekly sets per muscle group for hypertrophy**, and training the major muscle groups **at least twice weekly** as a strong general framework. citeturn18view3

That position is consistent with Currier et al.'s large 2023 Bayesian network meta-analysis of randomized trials: its strength network included **178 studies and 5,097 participants**, while its hypertrophy network included **119 studies and 3,364 participants**. Every tested resistance-training prescription outperformed no training. Higher loads, particularly ≥80% 1RM, ranked best for maximal-strength development, whereas hypertrophy was produced by a much broader spectrum of loading prescriptions as long as sufficient training was performed. Multiset prescriptions ranked particularly well for hypertrophy. Currier et al., 2023, *British Journal of Sports Medicine*, DOI **10.1136/bjsports-2023-106807**. citeturn19search0

A newer dose-response analysis by Pelland et al., published in the 2026 volume of *Sports Medicine*, adds an important nuance: **weekly volume has a positive but diminishing-return relationship with both hypertrophy and strength**, whereas increased frequency appears more independently useful for strength than hypertrophy. The study analyzed 67 studies and 2,058 participants, but approximately 79% of participants were male and average age was only about 25 years, illustrating a recurring limitation in the literature. Pelland et al., 2026, *Sports Medicine*, DOI **10.1007/s40279-025-02344-w**. citeturn21search6

This leads to the first major conclusion for an application:

> **There is substantially more evidence for flexible programming ranges than for one universally “optimal” workout.**

For the general population, a good algorithm should therefore optimize **adherence, appropriate effort, recoverable weekly volume, exercise tolerance, and progressive overload**, rather than attempt to identify a mathematically perfect split, rep range, or exercise. The 2026 ACSM synthesis explicitly emphasizes individualization and notes that bands, bodyweight exercise, machines, free weights, and home-based resistance training can all produce meaningful adaptations. citeturn18view3

A second major conclusion is equally important:

> **Anthropometric and clinical information should modify exercise execution and exercise selection, but it should not be used to impose rigid “body-type” rules.**

The empirical literature does not justify common deterministic rules such as “long femurs mean you must squat wide,” “long arms mean you must conventional-deadlift,” or “tall people should avoid deep squats.” Anthropometry changes the mechanics of a movement, but current studies are generally small and frequently demonstrate modest or inconsistent predictive relationships rather than validated decision thresholds. Cholewa et al.'s deadlift study, for example, measured multiple body dimensions in 47 deadlift-naïve adults and found only one statistically significant anthropometric association with relative sumo versus conventional performance—a modest association involving sitting-height-to-height ratio. Cholewa et al., 2019, *Journal of Sports Science & Medicine*. citeturn18view0

A third conclusion is critical for clinical users:

> **A history of musculoskeletal pain or injury should trigger an individualized loading branch, not automatic exclusion from resistance training.**

Exercise is an evidence-based intervention for several highly prevalent musculoskeletal conditions, including chronic low-back pain and patellofemoral pain. The correct algorithmic response is usually to alter load, range of motion, exercise variation, volume, or progression while monitoring symptoms, rather than simply disable entire movement categories. Chronic-pain evidence also does **not** support a universal requirement that therapeutic exercise be completely pain-free. citeturn22search0turn24search0

The evidence strength behind different app decisions can therefore be summarized as follows:

| App decision | Evidence strength | Appropriate algorithmic interpretation |
|---|---:|---|
| Resistance training versus none | **Very high** | Strong default recommendation for eligible adults. citeturn18view3turn19search0 |
| Heavy loading for maximal strength | **High** | Prefer ≥80% 1RM for at least some primary strength work when technically and medically appropriate. citeturn18view3turn19search0 |
| Higher weekly volume for hypertrophy | **High** | Approximately 10 weekly sets/muscle is a defensible general target, with individual adjustment and diminishing returns. citeturn18view3turn21search6 |
| Failure required for hypertrophy | **Moderate-high evidence against requirement** | Most sets do not need to reach failure. citeturn19search3turn19search5 |
| Full-body versus split routine | **Moderate-high** | Primarily a scheduling decision when weekly volume is matched. citeturn17search0 |
| Exact “best” RIR | **Moderate** | Close-to-failure matters more for hypertrophy than strength, but there is no validated universal RIR optimum. citeturn19search1 |
| Limb-length-specific exercise prescription | **Low-moderate** | Use anthropometry to generate variations to test, not hard exclusions. citeturn18view0 |
| BMI-specific sets/reps | **Low / unsupported** | BMI should influence accessibility, tolerance and clinical screening, not create an independent rep prescription. citeturn23search2turn23search7 |
| Exact universal pain cutoff during exercise | **Low / unsupported** | Use symptom trajectory and clinical context rather than a single rigid number. citeturn24search0 |

## Resistance-training dose: sets, repetitions, rest, effort, and progression

The most useful way to model resistance training is to separate **goal-specific variables** from variables that simply need to fall within an effective range. Load specificity is very important for maximal strength, but much less restrictive for hypertrophy. Weekly volume is important for hypertrophy, but its returns diminish. Failure is unnecessary. Frequency is largely a way of distributing stimulus and practicing lifts rather than an independent hypertrophy driver. citeturn19search0turn21search6turn19search5

### Goal-specific prescription

For maximal strength, Currier et al. found that higher-load prescriptions produced the greatest strength gains, and the ACSM 2026 recommendation specifically highlights **≥80% 1RM for approximately 2–3 sets per exercise** when strength is the priority. This does not mean every exercise needs to be performed that heavily; rather, some of the specific movements in which the user wants maximal strength should be exposed to high loads. citeturn19search0turn18view3

For hypertrophy, the load range is substantially wider. Schoenfeld et al.'s systematic review and meta-analysis found significantly larger improvements in 1RM strength with high loads but no significant difference in hypertrophy between high- and low-load conditions when effort was sufficiently high. Schoenfeld et al., 2017, *Journal of Strength and Conditioning Research*, DOI **10.1519/JSC.0000000000002200**. citeturn21search8

Low-load training is therefore not “bad for muscle growth,” but it commonly requires substantially more repetitions and closer proximity to failure to provide an efficient stimulus. A practical app can consequently use a relatively moderate repetition range for most hypertrophy training—not because, for example, 8–12 repetitions has unique biological properties, but because moderate loads provide an efficient compromise among stimulus, time, cardiovascular fatigue, technical consistency, and joint loading. The evidence supports a broad effective loading spectrum rather than a magical hypertrophy rep range. citeturn21search8turn19search1

For local muscular endurance, load specificity works in the opposite direction. High-repetition, lower-load work produces greater adaptation to high-repetition endurance tests than exclusively heavy training; in one controlled trial comparing heavier and lighter loading, the lighter group improved high-repetition bench-press endurance substantially more while the heavier condition produced superior maximal-strength gains. citeturn19search8

An algorithm-friendly prescription is therefore:

| Primary objective | Main working range | Sets | Effort | Rest | Confidence |
|---|---|---|---|---|---|
| **Maximal strength** | Mostly ~3–6 reps on primary lifts, with substantial work ≥80% 1RM | Usually 2–3 hard work sets/exercise | Commonly leave ~2–4 RIR during routine training; occasional closer work is optional | Usually ~2–4 min on heavy compounds | **High** for heavy-load principle; specific rep/RIR boundaries are implementation ranges. citeturn18view3turn19search0turn19search1 |
| **Hypertrophy** | Broadly effective; ~6–15 reps is a practical default, not a physiological “magic zone” | Build toward ~10 direct-equivalent weekly sets/muscle where appropriate | Primarily ~1–3 RIR | Often ~1–3 min, with longer rest if repetitions or technique deteriorate | **High** for volume/broad loading; moderate for exact ranges. citeturn18view3turn21search6turn21search8turn19search2 |
| **Local muscular endurance** | Usually ≥15 reps with lighter loading | ~2–3 sets | Relatively close to task-specific fatigue | Short-to-moderate rest | **Moderate**; adaptations are test/load specific. citeturn19search8 |
| **General health / novice** | Mostly moderate loads and controllable reps | Often 1–3 sets/exercise initially | Preserve several RIR while learning, then progress effort | Enough rest to maintain form | **High** that simple RT works; exact starting dose should be individualized. citeturn18view3turn19search0 |

The ~6–15-repetition hypertrophy recommendation above should therefore be interpreted as an **engineering default**, not an “optimal physiological zone.” Users who prefer 15–25 repetitions can grow muscle with lighter loads, while users who enjoy somewhat heavier loading can obtain hypertrophy with lower repetitions; a moderate range is simply easier to implement for most non-athletes. citeturn21search8

### Weekly volume

Volume is one of the variables for which a true dose-response relationship is reasonably well supported. Pelland et al.'s 2026 meta-regression found positive relationships between weekly volume and both hypertrophy and strength, but importantly found **diminishing returns** as volume increased. Strength showed particularly pronounced diminishing returns. citeturn21search6

That is consistent with ACSM's current practical recommendation of approximately **10 sets per muscle group per week for hypertrophy** rather than advocating indefinitely increasing volume. citeturn18view3

For an app, “10 sets” should not be treated as an exact threshold at which muscle growth suddenly changes. A better interpretation is:

**Low-volume starting point → observe adaptation → progress toward approximately 10 challenging sets per muscle/week when hypertrophy is prioritized → increase further only when recovery, adherence, time, and progress justify it.** The diminishing-return model means there is little reason for a general-population application to automatically prescribe bodybuilding-style extreme volumes. citeturn21search6turn18view3

There is also a measurement problem: a bench-press set is clearly a direct set for the chest, but it is simultaneously an indirect stimulus for the triceps and anterior deltoid. Pelland et al. found that models treating indirect sets as fractional volume predicted adaptations better than simply classifying all sets as either zero or one full set. Their primary model treated an indirect set as approximately **0.5 set**. This is particularly valuable for software because it can prevent an algorithm from accidentally assigning excessive arm or shoulder work after already prescribing substantial pressing and pulling volume. citeturn21search6

A useful internal volume model would therefore be:

`effective weekly muscle sets ≈ direct sets + 0.5 × strongly involved indirect sets`

This should be viewed as a **programming approximation inspired by Pelland et al.'s modeling**, not a biological law applicable identically to every exercise and every individual. citeturn21search6

### Proximity to failure and RIR

The literature has moved clearly away from the idea that every set needs to reach complete muscular failure.

Grgic et al.'s 2022 meta-analysis of 15 studies found no significant overall advantage of failure over non-failure training for either strength or hypertrophy. All included studies involved young adults, which is a generalizability limitation, but the evidence nevertheless makes routine failure difficult to justify as a requirement. Grgic et al., 2022, *Journal of Sport and Health Science*, DOI **10.1016/j.jshs.2021.01.007**. citeturn19search5

Refalo et al.'s 2023 hypertrophy meta-analysis similarly found **no evidence that momentary muscular failure was superior to non-failure training** and suggested that the relationship between proximity to failure and hypertrophy is probably nonlinear. Refalo et al., 2023, *Sports Medicine*, DOI **10.1007/s40279-022-01784-y**. citeturn19search3

The important newer nuance comes from Robinson et al.'s 2024 meta-regressions. Strength gains showed little relationship to estimated RIR across a broad range, whereas hypertrophy tended to increase as sets were terminated closer to failure. The authors explicitly cautioned that the precise shape of this relationship remains uncertain because RIR often had to be estimated from study descriptions rather than directly standardized. Robinson et al., 2024, *Sports Medicine*, DOI **10.1007/s40279-024-02069-2**. citeturn19search1

A 2024 randomized study by Refalo and colleagues offers a useful practical result: stopping at approximately **1–2 RIR produced quadriceps hypertrophy similar to training to momentary failure over eight weeks**, while failure generated greater acute neuromuscular fatigue and larger repetition losses across sets. citeturn19search4

For a general-population algorithm, I would therefore use:

| Context | Default RIR | Rationale |
|---|---:|---|
| Novice learning a compound exercise | **3–4 RIR** | Provides practice while minimizing fatigue and technical breakdown; progression can bring effort closer over time. This is a safety-oriented implementation of evidence showing failure is unnecessary. citeturn19search5turn18view3 |
| Routine hypertrophy compound sets | **~1–3 RIR** | Close enough to failure to obtain a strong stimulus without requiring complete failure. citeturn19search1turn19search4 |
| Machine/isolation hypertrophy work | **~0–2 RIR** if desired | Failure can be used selectively when technical/safety cost is low, but remains optional. citeturn19search3turn19search5 |
| Maximal-strength training | **~2–4 RIR for most volume work** | Strength does not appear strongly dependent on close proximity to failure, while high load and movement specificity matter more. citeturn19search0turn19search1 |
| Rehabilitation / symptomatic exercise | **Do not use RIR alone** | Symptoms, movement confidence, range, clinical restrictions and next-day response must also control progression. citeturn22search0turn24search0 |

The application should therefore **never equate “effective training” with “reaching failure.”**

### Rest intervals

Rest is best modeled around **performance preservation**, not a universal stopwatch value.

A 2024 Bayesian meta-analysis found a small hypertrophy advantage for rest intervals **longer than 60 seconds**, plausibly because longer rests allow greater repetition and training-volume preservation. Singer et al., 2024, PMID **39205815**. citeturn19search2

Earlier evidence similarly found that both short and long rest can produce hypertrophy, while longer rest generally becomes more useful when strength, heavier loading, or repeated performance is the priority. citeturn21search25

Thus an algorithmic default of approximately **2–3 minutes after demanding compound sets** and **1–2 minutes after moderate-load accessory work** is defensible. For heavy strength work, extending beyond three minutes can be appropriate; for lighter isolation or endurance work, shorter recovery may be acceptable. These intervals are a synthesis of performance and hypertrophy evidence rather than rigid biological thresholds. citeturn19search2turn21search25

A superior dynamic rule is:

> **If the next set loses substantially more repetitions than expected, technique changes, or the user cannot remain within the programmed RIR, increase rest before reducing load.**

This operationalizes the evidence that rest matters partly through its effect on subsequent work capacity. citeturn19search2

### Progression

Progression should occur after the current prescription has become easier, rather than increasing weight every session regardless of performance. The most robust practical implementation is a **rep-range plus RIR progression model**.

For example, an exercise could be prescribed as `2 × 8–12 @ 2 RIR`. The user keeps the current load until he or she can reach the upper portion of the range while retaining approximately the target RIR and acceptable technique. The application then uses the smallest practical load increase and allows repetitions to fall toward the lower end of the range. This is an engineering implementation of progressive overload compatible with current evidence; the exact percentage increase is not itself established as a universally optimal value. citeturn18view3turn21search6

The algorithm should **not automatically add sets whenever progress stalls**. Because volume exhibits diminishing returns, the first diagnostic questions should include adherence, effort, load progression, sleep/recovery, exercise execution, and whether actual weekly volume was completed. Only then should set volume be increased. citeturn21search6

## Frequency, workout splits, and time-constrained programming

One of the clearest opportunities for simplifying a workout-generation application is to stop treating the split itself as a major physiological determinant.

A 2024 systematic review and meta-analysis comparing **split routines with full-body resistance training** found no significant difference in either strength or hypertrophy when weekly training volume was matched. In practical terms, “full body,” “upper/lower,” and more distributed splits are primarily different methods of organizing the same weekly training stimulus. citeturn17search0

The newer Pelland dose-response work strengthens that interpretation for hypertrophy: frequency itself had an effect compatible with being negligible once other factors were considered, whereas frequency showed a clearer positive relationship with strength, probably because frequent exposures provide additional opportunities for specific high-quality strength practice and weekly work distribution. citeturn21search6

ACSM's current practical recommendation is nevertheless to expose each major muscle group approximately **twice per week or more**, which provides a useful default while leaving substantial freedom in how those exposures are organized. citeturn18view3

### Split selection by days available

For a general-population application, the following framework follows the evidence more closely than trying to rank splits from “best” to “worst”:

| Availability | Preferred default | Why |
|---|---|---|
| **1 day/week** | Full body | A split would leave many muscle groups untrained for long periods; one full-body exposure is still better than no resistance training. citeturn19search0turn18view3 |
| **2 days/week** | Full body A/B | Efficiently reaches approximately two weekly exposures per major muscle group. citeturn18view3 |
| **3 days/week** | Full body A/B/C, or rotating upper/lower/full-body | Excellent balance of stimulus, recovery and scheduling; no evidence requires a body-part split. citeturn17search0turn21search6 |
| **4 days/week** | Upper/lower ×2 is a strong default | Makes moderate-to-high weekly volume easier to distribute without long sessions. Split is organizational, not inherently anabolic. citeturn17search0 |
| **5 days/week** | Upper/lower plus a shorter full-body or priority session | Useful when the user enjoys frequent sessions or needs to distribute volume. Frequency is not automatically superior for hypertrophy. citeturn21search6 |
| **6 days/week** | Distributed push/pull/lower, upper/lower variants, or short full-body rotations | Suitable by preference or high volume, but **not necessary** for ordinary health or hypertrophy. citeturn18view3turn17search0 |

This means availability should be treated as a **constraint**, not a marker of training quality. A person who can reliably train for 45 minutes three times per week may have a better program than someone who nominally schedules six sessions but regularly skips them. ACSM's 2026 position explicitly prioritizes consistency over needless complexity. citeturn18view3

### Minimal-dose training

The network meta-analysis evidence establishes that even relatively modest resistance-training prescriptions improve strength and hypertrophy relative to no exercise. Therefore, low availability should lead the application to **compress training rather than abandon it**. citeturn19search0

A low-frequency program should prioritize exercises that cover large amounts of musculature and remove redundant work before cutting the essential movement patterns. For example, a one- or two-day program benefits more from a squat/leg-press pattern, hinge, press and pull than from several variations of curls or lateral raises. That movement-priority hierarchy is an application-design principle rather than proof that a particular list of lifts is uniquely superior.

### Supersets

Supersets have substantially stronger support as a time-saving strategy than they did a decade ago.

A 2025 systematic review/meta-analysis concluded that supersets **reduce session duration without compromising training volume or muscle activation**, making them a useful time-efficient alternative to traditional straight sets. citeturn21search1

Another 2025 review reported that chronic adaptations in strength, hypertrophy, endurance and power are generally comparable between properly programmed superset and traditional training, while session duration can be reduced substantially—often on the order of ~50%. Supersets are, however, more metabolically and perceptually demanding. citeturn21search7

A randomized trial of whole-body supersets similarly found that the method could nearly halve training duration, although the additional acute fatigue means exercise pairing matters. citeturn21search4

For general-population users, the best default is therefore **non-competing supersets**, such as an upper-body press paired with a row or a lower-body exercise paired with an upper-body exercise, rather than pairing two technically difficult exercises that heavily fatigue the same muscles.

The physiological claim—supersets can save time—is evidence-based; recommending non-competing exercise pairs as the default is a safety/performance-oriented programming inference. citeturn21search1turn21search7

### Drop sets

Drop sets also appear useful when time is the dominant constraint, especially for relatively stable exercises.

Sødal et al.'s 2023 systematic review/meta-analysis found **no significant hypertrophy difference between drop-set and traditional training**, while several included protocols required only approximately one-half to one-third as much time. Sødal et al., 2023, *Sports Medicine – Open*. citeturn21search2

A newer 2026 meta-analysis similarly concluded that drop sets appear to produce **comparable long-term hypertrophy and strength** to traditional sets while reducing training time, though they impose higher acute perceived exertion and metabolic stress. citeturn21search5

The application should therefore treat drop sets as an **optional time-saving tool**, not as a superior hypertrophy method. For the general population, they are more defensibly deployed on stable machine or isolation exercises than on highly technical barbell movements. The former conclusion is directly evidence-supported; the latter is a conservative safety-design inference. citeturn21search2turn21search5

### A defensible forty-minute framework

A time-restricted session does not need to become a maximal-intensity circuit. The evidence favors maintaining productive resistance work while removing unnecessary rest, redundancy and exercise transitions. Superset evidence supports this approach. citeturn21search1turn21search7

A useful **~40-minute general hypertrophy/strength-health template** would be:

| Approx. time | Work | Prescription |
|---:|---|---|
| 0–5 min | Movement-specific warm-up | Brief general movement plus progressively heavier practice sets for the first major exercise |
| 5–15 min | Pair A | Knee-dominant exercise + upper-body pull, ~2–3 work sets each |
| 15–25 min | Pair B | Horizontal/vertical press + hip hinge, ~2–3 work sets each |
| 25–33 min | Pair C | Secondary pull/press + unilateral leg or leg-curl pattern, ~2 sets each |
| 33–38 min | Trunk / optional priority work | ~2 focused sets |
| 38–40 min | Logging / transition buffer | Record load, reps, RIR, symptoms |

Most sets would terminate approximately **1–3 repetitions in reserve for hypertrophy-oriented users**, with sufficient inter-round recovery to maintain technique. The precise exercise menu should be generated from equipment, anthropometry, clinical status and preferences rather than hard-coded. The prescription is a synthesis of current volume, RIR and superset evidence rather than an RCT-tested 40-minute protocol as a single unit. citeturn19search1turn19search4turn21search1

For a novice, the algorithm should generally use fewer total work sets than shown at the upper end of this template and gradually expand workload. Because moving from no resistance exercise to even relatively modest resistance exercise produces substantial benefits, there is no evidence-based reason to immediately prescribe maximal recoverable volume. citeturn18view3turn19search0

## Cardiorespiratory and core training

Resistance training should not be treated as a complete substitute for cardiorespiratory activity in a general-health application.

The WHO 2020 evidence-based physical-activity guideline recommends that adults accumulate **150–300 minutes per week of moderate-intensity aerobic activity, 75–150 minutes of vigorous-intensity activity, or an equivalent combination**, while also performing regular muscle-strengthening activity and reducing sedentary time. Bull et al., 2020, *British Journal of Sports Medicine*, DOI **10.1136/bjsports-2020-102955**. citeturn23search0

For an application focused on sustainable general-population exercise rather than endurance competition, the WHO target is a much stronger anchor than attempting to prescribe a single “optimal” running program. Cardio modality can therefore be chosen according to preference, orthopedic tolerance, equipment and current conditioning. citeturn23search0

### Combining resistance and cardio

The traditional fear that cardio will substantially eliminate strength or muscle gains is overstated for ordinary recreational exercisers.

Schumann et al.'s 2022 updated systematic review/meta-analysis included **43 studies** and found essentially no detrimental effect of concurrent aerobic and strength training on maximal strength or whole-muscle hypertrophy. The standardized effects were approximately −0.06 for maximal strength and −0.01 for hypertrophy, neither statistically meaningful. Explosive-strength development showed a small negative effect, particularly when aerobic and resistance training occurred in the same session. Separating modalities by at least three hours removed that detectable explosive-strength interference signal in subgroup analysis. citeturn17search3

For the target population in this project, this is highly actionable:

**Health-focused users should generally perform both resistance and aerobic training without worrying about meaningful muscle-loss “interference.”** Separation becomes more relevant when maximal power/explosive performance becomes an explicit priority, which is outside the main non-athlete target. citeturn17search3

A muscle-fiber-level meta-analysis did detect a small concurrent-training interference effect on individual fiber hypertrophy, potentially greater with running for type-I fibers, but the same research literature acknowledges that whole-muscle hypertrophy and maximal-strength outcomes generally remain unaffected. This is another reason not to translate mechanistic concerns into broad warnings against cardio for recreational users. Lundberg et al., 2022, *Sports Medicine*, DOI **10.1007/s40279-022-01688-x**. citeturn17search7turn17search9

For software, a reasonable priority rule would be:

| User objective | Same-day scheduling |
|---|---|
| General health / weight management | Combine when necessary; adherence matters more than separation. citeturn17search3turn23search0 |
| Hypertrophy | Same-day cardio is acceptable; avoid adding unnecessary exhaustive endurance volume immediately before high-priority lifting. citeturn17search3turn17search7 |
| Maximal strength | Both can coexist; prioritize the strength work when it is the session's main objective. citeturn17search3 |
| Explosive power | Prefer separate sessions or ≥3 h separation when feasible. citeturn17search3 |

### What “core training” should mean

“Core” is a useful programming category, but the scientific literature does **not** provide anything comparable to the ~10-set hypertrophy recommendation establishing one optimum weekly number of planks, crunches or anti-rotation sets for healthy adults.

The strongest clinical evidence pertains to people with back pain. The 2021 Cochrane review by Hayden et al. found **moderate-certainty evidence that exercise therapy improves chronic low-back pain compared with no treatment, usual care or placebo**, with an average pain difference of approximately −15.2 points on a 0–100 scale at earliest follow-up. Improvements in functional limitation were smaller. Importantly, this evidence supports exercise broadly rather than proving that one specialized “core stability” method is universally superior. citeturn22search0

The application should therefore avoid presenting “core” as a special anatomical system requiring a separate workout. Instead, direct trunk training can complement the trunk loading already present in squats, hinges, loaded carries and presses.

For a healthy user, a sensible engineering implementation would include a small amount of direct trunk work across several functional directions:

| Function | Example class | Purpose |
|---|---|---|
| Resist extension | dead-bug/plank family | Trunk control |
| Resist rotation | Pallof/anti-rotation family | Rotational control |
| Resist lateral flexion | side-plank/carry family | Lateral trunk endurance |
| Controlled spinal motion when appropriate | trunk flexion/extension exercise | Direct trunk strength through tolerated ROM |

No evidence establishes that every user needs all four categories every week. A few direct sets distributed across the week are a reasonable application default, but the exact number should be presented as **program architecture rather than an empirically identified optimum**. In people with chronic low-back pain, exercise selection should follow the individual's tolerances, functional goals and clinician restrictions rather than a generic “weak core” diagnosis. citeturn22search0

## Biomechanics and anthropometric individualization

This is the part of the proposed application where caution is most important, because fitness culture contains many biomechanical claims that are more precise than the research justifies.

The most defensible principle is:

> **Use anthropometry to predict where an exercise might need modification; use actual movement, comfort, stability and performance to decide whether the modification is appropriate.**

Height alone is particularly weak information. Two people of equal height can have meaningfully different femur, tibia, torso and arm proportions. Conversely, two people of very different height can have similar relative segment proportions. Therefore, the useful inputs are **segment proportions, usable joint range of motion, stance/grip comfort, current symptoms and technique**, rather than “tall versus short” as a binary classification.

### Squat mechanics

Squat technique is not one immutable geometry. Changing stance changes joint positions and loading distribution.

A 2025 biomechanics experiment in recreationally trained men compared a relatively narrow stance (~0.7 times acromial width) with a wide stance (~1.7 times acromial width). The wider stance produced **less knee flexion and lower knee-extension moments/vastus muscle-force estimates**, while increasing hip-abduction demands. Larsen et al., 2025, *Journal of Strength and Conditioning Research*, DOI **10.1519/JSC.0000000000004949**. citeturn7search3

This is useful clinically because it demonstrates a general truth: technique modifications tend to **redistribute mechanical demand rather than simply make an exercise globally “safer.”**

Consequently, a knee-sensitive user might tolerate a different stance, depth or squat variation better—but moving wider can shift demand elsewhere. The app should therefore test modifications and monitor response rather than assume that one position reduces all joint stress. citeturn7search3

For users with relatively long thighs or a relatively short torso, maintaining the combined system over the base of support may require different amounts of trunk inclination, knee travel, stance width or ankle motion than it does for another individual. The correct software response is not “long femur = bad squat.” It is to make several controlled variants available: conventional squat, slightly wider stance, heel-elevated variation, front/goblet-loaded variation, box-limited range, machine/hack squat or leg press depending equipment and tolerance. The availability of these options is a biomechanical design strategy; current evidence does not validate a limb-ratio threshold that automatically selects one of them.

Therefore, the app should record the outcome of a trial:

`variation → load → ROM → perceived joint discomfort → stability → RIR → next-day symptom response`

That feedback is more valuable than height alone.

### Deadlift mechanics

The available anthropometric deadlift evidence strongly argues **against hard-coded body-proportion rules**.

Cholewa et al. examined conventional and sumo deadlift performance in 47 deadlift-naïve men and women while measuring arm length, hand length, seated height, thigh length, lower-leg length and several girths. They found no significant difference in overall 1RM between styles, and the only significant anthropometric predictor of the sumo-to-conventional strength ratio was sitting-height relative to total height. The correlation was modest, and the authors interpreted their findings as suggesting only a **slight potential advantage** for sumo in individuals with relatively longer torsos and conventional in those with relatively shorter torsos. Cholewa et al., 2019, *Journal of Sports Science & Medicine*. citeturn18view0

That is nowhere near enough evidence to justify popular rules such as:

“long arms → conventional,”  
“short arms → sumo,” or  
“long femurs → never conventional.”

For a general-population application, conventional, sumo, trap-bar, Romanian deadlift and machine hinge patterns should instead be considered **candidate solutions to the same general hip-extension training objective**.

The selection score should be based primarily on whether the user can achieve a controlled starting position, tolerate the range, progress loading and perform the lift without an unfavorable symptom response.

### Bench-press and pressing mechanics

Grip width similarly redistributes joint demand.

Mausehund and colleagues' biomechanical review found high shoulder and elbow muscular demand across bench-press variations, with narrower grip positions increasing elbow net-joint moments. In other words, a grip modification does not simply make the lift “safer”; it changes where the mechanical demand is expressed. Mausehund et al., 2022. citeturn17search1

More recent kinetic work likewise reports that wider and narrower grips systematically change shoulder and elbow ranges and net joint moments: wider grips reduce elbow moment in parts of the lift whereas narrower positions can reduce shoulder moment while increasing elbow demand. citeturn17search18

For a user with a long wingspan, the bar travels a greater absolute distance at a given conventional touch point than it does for someone with shorter arms, but that fact alone does not justify prescribing an extreme grip. The algorithm should instead allow moderate changes in grip width, dumbbell or neutral-grip pressing, machine pressing, or a tolerated ROM based on shoulder/elbow response.

Again:

> **Anthropometry proposes the experiment; performance and tolerance determine the answer.**

### Tall versus short

The application should therefore avoid a `height > X → exercise Y` logic.

A better model is:

`height → segment measurements/proxies → likely movement constraint → candidate variation → trial → feedback`

An exceptionally tall user might need rack adjustments, different bench or machine dimensions, a raised deadlift starting position during early skill acquisition, or different stance options simply because commercial equipment has fixed dimensions. These are legitimate usability issues, but they should not be confused with evidence that tall people biologically require different hypertrophy rep ranges or lower training volumes.

There is currently no strong evidence supporting **height-specific sets, repetitions, RIR or weekly frequency**. Training-dose variables should be driven by goals, experience, recovery and response. Anthropometry should primarily modify **exercise geometry**.

### Overweight and obesity as an anthropometric variable

BMI or body-fat category should not independently determine repetitions or intensity.

Resistance training has strong evidence of benefit in adults with overweight or obesity. In a 2025 systematic review/meta-analysis of 25 randomized controlled trials involving adults with BMI ≥25 kg/m² undergoing dietary weight loss, adding resistance exercise significantly **protected fat-free mass**, increased fat-mass loss and improved strength relative to diet alone. Binmahfoz et al., 2025, *BMJ Open Sport & Exercise Medicine*, DOI **10.1136/bmjsem-2024-002363**. citeturn23search2

An overview of 12 systematic reviews and 149 studies similarly found favorable effects of exercise on body weight, body fat and visceral fat; resistance training attenuated lean-mass loss during weight reduction. Bellicha et al., 2021, *Obesity Reviews*, DOI **10.1111/obr.13256**. citeturn23search7

What obesity can change is **movement accessibility**. Abdominal or thigh soft tissue, joint symptoms, balance, deconditioning, equipment dimensions and the energetic cost of supporting greater body mass can make some exercises less comfortable or practical. Evidence for precise BMI-specific biomechanical prescriptions is limited, however, so the application should not pretend otherwise.

A high-body-mass user should therefore be offered scalable choices such as supported squats/sit-to-stands, leg press, machines, supported rows, cycling or other lower-impact aerobic modalities when those improve tolerance. Those are **accessibility options**, not mandatory “obesity exercises.”

Likewise, someone who is underweight should not receive a fundamentally different squat based solely on BMI. Body mass by itself is an inadequate biomechanical classifier. In the workout-generation layer, recovery, health screening, nutrition context, strength level and symptoms are more informative.

### The anthropometric decision matrix

A defensible app architecture would look like this:

| Input | Do use it for | Do **not** use it for |
|---|---|---|
| Height | Equipment fit; flag potential ROM/setup issues | Automatically selecting squat/deadlift style |
| Femur:tibia/torso proportions | Generating squat stance/load-position variants to test | Declaring one squat technique biomechanically mandatory |
| Arm span / arm length | Press/deadlift setup candidate generation | Assuming a fixed grip width or deadlift style |
| Body mass / obesity | Accessibility, supported exercise options, cardio modality, joint-tolerance considerations | Automatically reducing training quality or prescribing unique rep ranges |
| Joint ROM | Exercise depth, stance, grip and variation selection | Assuming passive ROM directly determines functional capability |
| Pain / previous injury | Clinical branch, load/ROM modification and monitoring | Permanently banning a movement pattern solely from injury history |
| Actual exercise feedback | **Primary selector** among acceptable variants | — |

This hierarchy is consistent with the relatively weak direct anthropometric prediction seen in deadlift research and the evidence that technique changes redistribute rather than simply eliminate joint demand. citeturn18view0turn7search3turn17search1

## Common musculoskeletal limitations, obesity, pain, and safety

An application designed for ordinary adults will inevitably encounter people with knee pain, low-back pain, shoulder pain, osteoarthritis or previous injury. A “healthy athlete” decision tree is therefore insufficient.

The most important architecture is to distinguish:

**medical contraindication / red flag → clinician-directed limitation → manageable chronic symptoms → healthy training.**

ACSM's preparticipation screening framework uses three core domains: the person's **current physical-activity level, presence of signs/symptoms or known cardiovascular/metabolic/renal disease, and intended exercise intensity**. Its purpose was specifically to avoid unnecessary medical barriers while still identifying users who warrant clearance. Riebe et al., 2015, *Medicine & Science in Sports & Exercise*, DOI **10.1249/MSS.0000000000000664**. citeturn23search3

This means the application should not indiscriminately send every older, overweight or previously injured user to a physician. Nor should it allow known warning symptoms to be bypassed merely because the user wants a workout.

### Chronic low-back pain

The best-supported message is **exercise, not avoidance**.

Hayden et al.'s 2021 Cochrane review found moderate-certainty evidence that exercise probably reduces chronic low-back pain compared with no treatment/usual care/placebo, although average functional improvements are smaller and no single exercise approach emerges as universally necessary. citeturn22search0

Accordingly, “history of low-back pain” should not automatically eliminate every squat, deadlift or loaded carry.

Instead, the application should reduce complexity and permit modification of:

`load → range → exercise variation → external support → set count → effort → weekly frequency`

A user who does poorly with a floor barbell deadlift might tolerate a Romanian deadlift, elevated deadlift, cable pull-through, machine hip extension or other hinge. The evidence supports continued exercise broadly; choosing among these variants should depend on individualized response rather than a diagnosis-independent rule. citeturn22search0

### Patellofemoral pain

This area has relatively strong exercise evidence.

A 2024 best-practice guide synthesized **65 high-quality RCTs involving 3,796 participants** and concluded that management should start with individualized assessment and education, with knee-targeted exercise and, when appropriate, hip-targeted exercise forming a central part of treatment. Neal et al., 2024. citeturn22search1

Nascimento et al.'s systematic review/meta-analysis found combined **hip and knee strengthening superior to knee strengthening alone** for decreasing pain and improving activity in people with patellofemoral pain. Nascimento et al., 2018. citeturn24search1

A PFP branch should therefore not read `knee pain → no squats`. It should allow tolerable knee loading while incorporating hip and knee strengthening and adjusting depth, load, exercise choice and progression according to symptoms. citeturn22search1turn24search1

### Knee osteoarthritis

Strength training is appropriate in knee OA, but the idea that “heavier must be better” is not supported.

The large START randomized clinical trial compared high-intensity resistance training, lower-intensity resistance training and an attention-control condition in adults with knee osteoarthritis. At 18 months, **high-intensity training did not produce significantly greater reductions in knee pain or knee-joint compressive forces** than low-intensity training or control. Messier et al., 2021. citeturn22search2

A subsequent systematic review likewise found no clear superiority of high-intensity over lower-intensity resistance training for pain, physical function or quality-of-life outcomes in knee OA. citeturn22search4

For a general-population algorithm, the implication is substantial: an OA user can train progressively, but there is no need to force heavy loading when a more moderate prescription is tolerated and effective.

### Rotator-cuff-related shoulder pain

Clinical guidelines for rotator-cuff disorders consistently emphasize **active treatment and exercise** rather than rest alone. A systematic review of clinical practice guidelines found exercise programs recommended across the included guidelines, despite variation in recommendations for imaging, injections and other interventions. citeturn22search7

More recent evidence-based clinical-practice guidance continues to treat exercise and nonsurgical active management as central components of rotator-cuff tendinopathy care. citeturn22search5

For the app, a history of shoulder pain should therefore open alternatives in grip, pressing angle, range, load and exercise modality. It should **not** interpret every shoulder symptom as evidence that all pressing is forbidden.

### Is pain during training automatically dangerous?

No.

Smith et al.'s 2017 systematic review/meta-analysis specifically compared therapeutic exercise in which pain was allowed with pain-free exercise in chronic musculoskeletal pain. Painful-exercise protocols produced a small short-term pain benefit and **no clear medium- or long-term disadvantage**. The authors concluded that pain during therapeutic exercise need not prevent successful outcomes. Smith et al., 2017, *British Journal of Sports Medicine*, DOI **10.1136/bjsports-2016-097383**. citeturn24search0

That does **not** mean “ignore pain” or “pain is always safe.”

It means that the app should not use a simplistic:

`pain > 0 → stop all exercise`

rule.

Nor does the research establish one universal “safe” threshold such as exactly 3/10 for every pathology. A stronger system would monitor **pain behavior over time**:

| Response | Algorithm action |
|---|---|
| No symptoms or familiar mild symptoms that remain stable | Continue planned progression |
| Symptoms rise modestly during exercise but settle afterward and baseline is maintained | Maintain or progress conservatively depending diagnosis and history |
| Symptoms progressively increase set-to-set | Reduce range, load, effort or change variation |
| Significant worsening persists after training or repeatedly worsens across sessions | Regress dose and flag for reassessment |
| New concerning signs/symptoms or medical warning symptoms | Stop automated progression and route to appropriate professional evaluation |

The middle rows are conservative application logic derived from symptom-management principles rather than validated universal numeric cutoffs. The evidence specifically supports the narrower conclusion that pain-free exercise is **not always necessary** in chronic musculoskeletal rehabilitation. citeturn24search0

### Users with overweight or obesity

Resistance training should remain a central part of programming.

The 2025 Binmahfoz meta-analysis is particularly relevant because it included only randomized trials in adults with overweight/obesity undergoing dietary weight loss. Resistance exercise did not meaningfully change total weight loss relative to diet alone, but it **preserved more fat-free mass (SMD 0.40), increased fat loss (SMD −0.36), and substantially improved muscular strength**. Evidence certainty was moderate for fat-free mass and high for fat-mass loss. citeturn23search2

That distinction matters for a fitness application: **scale weight is not a sufficient success metric**. During weight loss, maintaining muscle and strength is valuable even when total body-mass reduction is unchanged. citeturn23search2turn23search7

Therefore, an overweight/obese branch should generally modify **accessibility and recovery**, not remove progressive resistance training.

## Algorithm-ready framework and evidence map

The evidence supports a hierarchical generator rather than a database that blindly matches “body type” to predefined workouts.

The fundamental logic should be:

`Safety → Goal → Availability → Recoverable volume → Exercise candidate selection → Anthropometric/clinical filtering → Effort prescription → Progression → Feedback → Adaptation`

That order matters. For example, whether a person's femurs are long is much less important than whether that person has symptomatic knee OA, can train only twice per week, wants primarily hypertrophy, and can comfortably perform a particular squat variation.

### User inputs that genuinely change programming

| Input | High-value program effect |
|---|---|
| Goal: general health / hypertrophy / strength / endurance | Changes load, volume, RIR and cardio emphasis. citeturn19search0turn18view3 |
| Days/week and minutes/session | Determines how weekly volume is distributed, not whether results are possible. citeturn17search0turn21search6 |
| Training experience | Determines exercise complexity, starting volume and how aggressively effort/load should progress. ACSM emphasizes individualization rather than one prescription for all adults. citeturn18view3 |
| Equipment | Selects exercise candidates; machines, free weights, bands and bodyweight can all be effective. citeturn18view3 |
| Current symptoms / diagnosis | Activates clinical modifications and possible screening. citeturn23search3turn22search0 |
| Previous injury | Informs testing and progression rather than automatically banning a pattern |
| Segment proportions / ROM | Ranks exercise variants based on likely geometry, then requires real-world confirmation. citeturn18view0turn7search3 |
| Body mass / obesity | Influences accessibility, cardio modality and possibly joint-tolerance choices, while retaining resistance training. citeturn23search2turn23search7 |
| Exercise-specific response | Should become the strongest personalization signal over time |

### Proposed resistance-training rule engine

For a healthy general-population user, a reasonable initial rule set would be:

**General-health mode:** train the major muscle groups approximately twice weekly, commonly through two to three full-body sessions; use moderate, technically manageable loads; perform roughly 1–3 work sets per exercise; and progressively increase resistance or repetitions. Simplicity and adherence are prioritized. citeturn18view3turn19search0

**Hypertrophy mode:** accumulate volume toward approximately **10 challenging direct-equivalent sets per muscle per week** where recovery and experience permit, distribute that volume over convenient sessions, use a broad loading spectrum with moderate repetitions as the default, and perform most work approximately **1–3 RIR** rather than routinely going to failure. citeturn18view3turn21search6turn19search1turn19search3

**Strength mode:** retain adequate weekly volume but emphasize **≥80% 1RM loading on priority lifts**, longer recovery, fewer repetitions and more movement-specific practice. Training to failure is unnecessary. citeturn19search0turn18view3turn19search1

**Endurance mode:** emphasize lighter loading and higher repetitions for the specific musculature/tasks in which local muscular endurance is desired, while retaining some resistance work outside the endurance range for broader strength development. citeturn19search8

### Proposed split rule engine

A particularly clean implementation would be:

```text
days = 1:
    full_body

days = 2:
    full_body_A_B

days = 3:
    full_body_A_B_C
    OR rotate full/upper/lower according to preference

days = 4:
    upper_lower_upper_lower
    OR four full-body sessions with lower per-session volume

days >= 5:
    distribute existing required weekly volume across shorter sessions
    do NOT automatically increase volume simply because more days are available
```

The key evidence-based property is not the labels used above; it is that **weekly volume and high-quality exposure are preserved**. Full-body and split routines show comparable adaptations when volume is matched, while additional frequency is more clearly relevant to strength practice than to hypertrophy itself. citeturn17search0turn21search6

### Proposed exercise-selection scoring

Rather than outputting `best exercise = X`, each candidate exercise can receive a score.

An example internal architecture could be:

```text
candidate_score =
    goal_match
  + equipment_match
  + user_preference
  + movement_competence
  + progression_potential
  + anthropometric_fit
  + clinical_tolerance
  - current_symptom_penalty
  - setup_complexity_penalty
  - unnecessary_fatigue_penalty
```

The relative numerical weights would need validation in real-world app data; they are not currently available from biomechanics research.

Anthropometry should have a **moderate ranking effect**, while observed pain/tolerance and progression should have a stronger effect. This follows directly from the limited predictive power seen in anthropometric studies such as Cholewa et al. versus the stronger evidence for individualized exercise modification in musculoskeletal conditions. citeturn18view0turn22search1turn22search0

### Proposed adaptive feedback loop

The most important personalization opportunity begins **after** the first workout rather than before it.

For each exercise, store:

```text
load
repetitions per set
reported RIR
range of motion
technical-confidence score
pain/discomfort location and magnitude
session RPE
next-session or next-day symptom response
```

Then:

```text
if target reps achieved
and RIR >= target
and technique stable
and symptoms acceptable:
    progress reps or smallest practical load step

elif reps below target but technique stable:
    maintain load or increase rest

elif symptoms increase:
    modify ROM/load/variation before increasing effort

elif multiple exercises show performance decline:
    investigate recovery / total volume before adding workload
```

This structure is particularly consistent with three robust pieces of evidence: volume has diminishing returns; rest can influence the ability to preserve work; and complete failure is not necessary for adaptation. citeturn21search6turn19search2turn19search5

### What the application should explicitly *not* claim

Several claims commonly seen in fitness applications would exceed current evidence.

The application should not claim that **8–12 reps is the uniquely optimal hypertrophy range**, because comparable hypertrophy can occur across a wide spectrum of loads. citeturn21search8

It should not claim that **training to failure is necessary**, because multiple meta-analyses and experimental studies contradict that proposition. citeturn19search3turn19search5turn19search4

It should not claim that **six training days are superior to three for hypertrophy** when weekly volume is equivalent. citeturn17search0turn21search6

It should not claim that **a specific workout split is intrinsically anabolic**. Split versus full-body evidence does not support that. citeturn17search0

It should not claim that **long femurs, long arms, height or BMI uniquely determine an exercise**. Direct anthropometric evidence is too limited for deterministic rules. citeturn18view0

It should not claim that **all exercise-related pain represents tissue damage or means an exercise must be stopped permanently**. Chronic musculoskeletal rehabilitation evidence does not support a universally pain-free requirement. citeturn24search0

It should not claim that **higher-intensity strength training is automatically better for a painful joint**, since knee-OA evidence provides a clear counterexample. citeturn22search2turn22search4

And it should not claim that **cardio destroys muscle growth** in recreational users. Whole-muscle hypertrophy and maximal-strength evidence from concurrent-training meta-analysis does not support that generalization. citeturn17search3

### High-priority evidence base for the application

| Source | Most important contribution |
|---|---|
| **ACSM Position Stand, 2026**, *Medicine & Science in Sports & Exercise*, DOI **10.1249/MSS.0000000000003897** | Current umbrella synthesis of 137 reviews/30,000+ participants; strength ≥80%1RM/2–3 sets; hypertrophy ~10 sets/muscle/week; consistency and individualization emphasized. citeturn18view3 |
| **Currier et al., 2023**, *British Journal of Sports Medicine*, DOI **10.1136/bjsports-2023-106807** | Network meta-analysis: 178 strength studies and 119 hypertrophy studies; heavy loads maximize strength while hypertrophy occurs across many prescriptions. citeturn19search0 |
| **Pelland et al., 2026**, *Sports Medicine*, DOI **10.1007/s40279-025-02344-w** | Volume-frequency dose response; increasing volume produces diminishing returns; hypertrophy less frequency-dependent than strength. citeturn21search6 |
| **Schoenfeld et al., 2017**, *Journal of Strength and Conditioning Research*, DOI **10.1519/JSC.0000000000002200** | Heavy loads better for maximal strength; hypertrophy possible across low and high loads. citeturn21search8 |
| **Grgic et al., 2022**, *Journal of Sport and Health Science*, DOI **10.1016/j.jshs.2021.01.007** | Failure versus non-failure meta-analysis; failure not required for strength or hypertrophy. citeturn19search5 |
| **Refalo et al., 2023**, *Sports Medicine*, DOI **10.1007/s40279-022-01784-y** | Momentary failure not superior for hypertrophy; proximity relationship probably nonlinear. citeturn19search3 |
| **Robinson et al., 2024**, *Sports Medicine*, DOI **10.1007/s40279-024-02069-2** | Strength relatively insensitive to RIR; hypertrophy tends to improve closer to failure, exact optimum uncertain. citeturn19search1 |
| **Singer et al., 2024**, PMID **39205815** | Small hypertrophy advantage to inter-set rests >60 s. citeturn19search2 |
| **2024 split vs full-body meta-analysis**, *Journal of Strength and Conditioning Research*, PMID **38595233** | Split and full-body routines produce comparable strength and hypertrophy when volume is equated. citeturn17search0 |
| **Zhang et al., 2025** | Superset meta-analysis supporting shorter sessions without sacrificing training volume. citeturn21search1 |
| **Sødal et al., 2023**, *Sports Medicine – Open* | Drop sets produce comparable hypertrophy while potentially requiring markedly less training time. citeturn21search2 |
| **Bull et al., 2020**, *British Journal of Sports Medicine*, DOI **10.1136/bjsports-2020-102955** | WHO aerobic and strength physical-activity framework. citeturn23search0 |
| **Schumann et al., 2022**, *Sports Medicine* | Concurrent cardio + strength does not meaningfully impair maximal strength or whole-muscle hypertrophy; possible explosive-strength interference. citeturn17search3 |
| **Lundberg et al., 2022**, *Sports Medicine*, DOI **10.1007/s40279-022-01688-x** | Small fiber-level concurrent-training interference nuance. citeturn17search7turn17search9 |
| **Cholewa et al., 2019**, *Journal of Sports Science & Medicine* | Shows the limited predictive power of anthropometry for sumo versus conventional deadlift performance. citeturn18view0 |
| **Larsen et al., 2025**, *Journal of Strength and Conditioning Research*, DOI **10.1519/JSC.0000000000004949** | Squat stance changes knee and hip mechanics, demonstrating redistribution rather than elimination of joint demand. citeturn7search3 |
| **Mausehund et al., 2022** | Bench-press grip changes shoulder/elbow joint demands; no single grip eliminates loading. citeturn17search1 |
| **Hayden et al., 2021**, Cochrane Review | Moderate-certainty evidence that exercise improves chronic low-back pain versus no exercise/usual care/placebo. citeturn22search0 |
| **Neal et al., 2024** | 65 high-quality RCTs informing patellofemoral-pain best practice; education plus knee/hip-targeted exercise central. citeturn22search1 |
| **Nascimento et al., 2018** | Hip + knee strengthening superior to knee strengthening alone in patellofemoral pain. citeturn24search1 |
| **Messier et al., 2021** | High-intensity strength training did not outperform low intensity for knee-OA pain/joint-force outcomes. citeturn22search2 |
| **Smith et al., 2017**, *British Journal of Sports Medicine*, DOI **10.1136/bjsports-2016-097383** | Therapeutic exercise need not always be completely pain-free in chronic musculoskeletal conditions. citeturn24search0 |
| **Binmahfoz et al., 2025**, *BMJ Open Sport & Exercise Medicine*, DOI **10.1136/bmjsem-2024-002363** | Resistance training during weight loss in overweight/obesity preserves fat-free mass, improves strength and increases fat loss. citeturn23search2 |
| **Bellicha et al., 2021**, *Obesity Reviews*, DOI **10.1111/obr.13256** | Overview of 12 systematic reviews/149 studies supporting exercise for body-composition improvement and RT for lean-mass preservation. citeturn23search7 |
| **Riebe et al., 2015**, *Medicine & Science in Sports & Exercise*, DOI **10.1249/MSS.0000000000000664** | Evidence-informed preparticipation screening framework suitable for an app safety gate. citeturn23search3 |

The resulting evidence base supports a workout generator built around **ranges, constraints and feedback rather than rigid templates**. The strongest scientific rules are relatively simple: train consistently; use sufficiently challenging resistance; use heavier loads when maximal strength matters; accumulate adequate but recoverable weekly volume for hypertrophy; do not require failure; distribute training according to available time; include aerobic activity for health; modify exercises according to actual geometry and tolerance rather than stereotypes; and treat chronic musculoskeletal limitations as problems of individualized loading rather than automatic exercise prohibition. citeturn18view3turn19search0turn21search6turn23search0turn22search0

The most significant unresolved research gap for the proposed application is **not sets versus reps**. Those variables are comparatively well studied. It is the translation from individual anthropometry and musculoskeletal history into reliable exercise-specific decisions. Existing biomechanics studies can explain *why* two users move differently, but they generally cannot yet provide validated thresholds such as “femur-to-torso ratio X requires stance Y.” For that reason, the scientifically strongest application would combine the population-level evidence above with **within-user longitudinal learning**: prescribe a plausible variant, observe execution and symptoms, and progressively learn which exercises that particular person can load, recover from, and adhere to successfully. citeturn18view0turn7search3turn17search1
