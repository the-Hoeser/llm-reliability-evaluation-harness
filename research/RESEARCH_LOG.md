# Research Log — LLM Uncertainty and Abstention

Project: LLM Reliability Evaluation Harness
Research track: Selective answering, epistemic uncertainty, and confidence calibration

## 2026-11-25 — Sprint 2 protocol established

### Research question

Can a language model recognize when the supplied evidence is insufficient, abstain instead of inventing an answer, and express confidence that tracks the correctness of answers it does provide?

### Operational scope

This first benchmark measures **closed-context answerability**, not whether a question is unknowable in the world. Each test case contains a question and a supplied context. The gold label states whether the context supports an answer, does not contain the answer, or is underspecified/ambiguous. This makes the target auditable and avoids treating the model's latent knowledge as directly observable.

Labels:

- `answerable`: the supplied context supports an answer and includes one or more acceptable reference strings.
- `unanswerable`: the requested information is absent from the context.
- `underspecified`: the question or context does not identify a unique answer (for example, an ambiguous person or choice).

### Experimental conditions

**Condition A — forced-answer baseline (`forced_answer_v1`)**

The model is instructed to return its best answer even when the context does not support one. It returns a JSON object containing an answer and a confidence estimate. This condition estimates unsupported-answer behaviour without an abstention option.

**Condition B — selective answering (`abstention_calibration_v1`)**

The model receives the same question and context but may abstain. It returns an answer, confidence from 0 to 1, and an explicit abstained flag. When abstaining, the answer must be null.

Both conditions request JSON output. The same dataset version, model configuration, and decoding parameters should be used in paired comparisons. Temperature 0 is a reasonable first control, but does not guarantee deterministic provider behaviour.

### Primary hypotheses

- H1: the abstention-enabled condition will reduce the false-answer rate on unanswerable and underspecified cases relative to the forced-answer baseline.
- H2: abstention will reduce coverage, creating a measurable coverage/accuracy trade-off.
- H3: self-reported confidence on attempted answers will not be perfectly calibrated; Brier score and equal-width 10-bin ECE will quantify the gap.
- H4: the model may over-abstain on answerable cases; unnecessary-abstention rate will quantify this cost.

These are hypotheses, not findings. No live provider experiment has been run yet.

### Metrics and definitions

| Metric | Definition |
|---|---|
| Coverage | Valid responses that attempted an answer / all valid responses |
| Decision accuracy | Correct answer-vs-abstain action / all valid responses |
| Answer accuracy on attempted answerable | Exact-match correct answers / attempted answerable cases |
| Unknown abstention recall | Correct abstentions / valid unanswerable and underspecified cases |
| False-answer rate on unknown | Answered cases / valid unanswerable and underspecified cases |
| Unnecessary-abstention rate | Abstentions / valid answerable cases |
| Brier score | Mean squared error between stated confidence and binary answer correctness on attempted answers |
| ECE (10 bins) | Weighted absolute difference between mean confidence and empirical accuracy across ten equal-width bins |

Confidence semantics are deliberately narrow: **the model's stated probability that its proposed answer is correct and supported by the supplied context**. Calibration metrics exclude abstentions because they contain no proposed answer. The current implementation reports empirical bins and sample size; with small datasets these statistics are unstable and must not be over-interpreted.

### Benchmark version

Dataset file: `datasets/abstention_context_v1.jsonl`

Initial composition: 6 answerable, 3 unanswerable, 3 underspecified cases. Contexts are deliberately short and self-contained. This is a smoke benchmark for pipeline development, not a representative or publication-grade sample.

### Known limitations and threats to validity

- Short exact-match references can penalize valid paraphrases; acceptable-answer lists are manually specified and should be expanded before substantive conclusions.
- The benchmark uses synthetic context notes. Results may not generalize to long documents, multi-hop evidence, retrieval errors, or specialist domains.
- Verbalized confidence can be strategic, prompt-sensitive, and miscalibrated. It is a measurement channel, not ground truth about internal model state.
- A single run is insufficient to characterize stochastic variation. Later work should repeat each condition, randomize run order, and report confidence intervals.
- Temperature 0 does not guarantee reproducibility across provider/model revisions.
- JSON formatting failures are recorded separately and must not be silently dropped from reporting.
- Closed-context unanswerability is not equivalent to global lack of knowledge.

### Next experiment

Run both policies on the same imported dataset with one fixed model configuration. Preserve all run IDs and raw responses. Compare false-answer rate, coverage, answer accuracy, unnecessary abstention, Brier score, and ECE. Follow with at least three repeated runs and a larger human-reviewed dataset before drawing conclusions.

### Literature notes

1. Xiong et al. (ICLR 2024), *Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs*. The paper studies black-box prompting, repeated sampling, and response aggregation; it reports overconfidence in verbalized self-confidence and highlights task-dependent calibration. https://proceedings.iclr.cc/paper_files/paper/2024/file/6733cf15e10e2cd1d59af033c3bb8507-Paper-Conference.pdf
2. *Causal evidence that language models use confidence to drive behaviour* (Nature Machine Intelligence, 2026). This work studies the relationship between calibrated confidence and abstention decisions, including a coverage/accuracy trade-off. https://www.nature.com/articles/s42256-026-01293-x
3. *A Survey on Uncertainty Quantification of Large Language Models: Taxonomy, Open Research Challenges, and Future Directions*. A broad survey of verbalized confidence, calibration, abstention, and semantic uncertainty. https://doi.org/10.1145/3744238
4. Guo et al. (2026), *LLMs Should Express Uncertainty Explicitly*. A recent preprint proposing explicit global confidence and local uncertainty signalling as interfaces for downstream control. https://arxiv.org/abs/2604.05306
5. Wang et al. (2026), *Are LLM Decisions Faithful to Verbal Confidence?* Introduces RiskEval to study whether stated uncertainty translates into risk-sensitive abstention. https://arxiv.org/abs/2601.07767

Literature notes are background, not evidence that this project's hypotheses are true.
