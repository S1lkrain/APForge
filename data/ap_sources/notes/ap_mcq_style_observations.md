# AP MCQ Style Observations (from source PDFs)

Derived from `Mock_Midterm_MCQ.pdf` and `ap-precalculus-course-at-a-glance.pdf`. Use when authoring `data/style_patterns/mcq/*.json`.

## Wording patterns (high frequency)

- "Which of the following …"
- "Which of the following statements is true about …"
- "Which of the following could define … / could be true …"
- "Based on this information, which of the following models …"
- "In the xy-plane, …"
- "The figure shows …" / "The table gives …"
- "For …, which of the following is equivalent to …"
- "What are all values of …, for …, where …"

## Representation mix

| Representation | Example items |
|----------------|-----------------|
| Symbolic only | 2, 4, 5, 9, 20, 25 |
| Graph | 7, 11, 15, 16, 78, 87 |
| Table | 12, 17, 21, 76, 77, 83, 84 |
| Context/story | 7, 8, 18, 23, 86 |
| Polar | 10, 17, 24, 28, 85 |

Part B emphasizes calculator-friendly tables, regression output, and approximate answers.

## Distractor logic (recurring)

- **Model type**: linear vs quadratic vs exponential vs logarithmic (Q5, Q8, Q12, Q80).
- **Parameter confusion**: growth factor vs percent change vs initial value (Q8).
- **Transform confusion**: horizontal vs vertical shift/dilation for exponentials and trig (Q20, Q22).
- **Rational structure**: hole vs vertical asymptote vs x-intercept; multiplicity arguments (Q6, Q26, Q83).
- **Trig**: wrong quadrant, wrong interval for all solutions, identity algebra slip (Q3, Q9, Q19).
- **Regression/residuals**: overestimate vs underestimate; compare |residual| (Q27).
- **Composition**: reversing input/output meaning in applied composition (Q23).
- **Rates**: confusing function value with rate of change; concavity from decreasing tables (Q16, Q21, Q82).

## Topic slug → pattern (authoritative: `data/topic_registry.json`)

Primary UI/API slugs (stored in DB when generating from the dashboard):

| Slug | UI label | Pattern ID |
|------|----------|------------|
| `rates-of-change` | Rates of Change | `rates_of_change_mcq` |
| `end-behavior` | End Behavior | `polynomial_end_behavior_mcq` |
| `asymptotes` | Asymptotes | `rational_asymptotes_mcq` |
| `exponential-growth` | Exponential Growth & Decay | `exponential_growth_mcq` |
| `logarithms` | Logarithmic Expressions | `logarithmic_expressions_mcq` |
| `sinusoidal-functions` | Sinusoidal Functions | `periodic_amplitude_mcq` |
| `sinusoidal-modeling` | Sinusoidal Modeling | `sinusoidal_modeling_mcq` |
| `polar-functions` | Polar Functions | `polar_functions_mcq` |
| `data-modeling` | Data Modeling & Regression | `data_modeling_regression_mcq` |

Legacy slugs (API/backward compatibility only; not shown in the topic dropdown):

| Legacy slug | Pattern ID |
|-------------|------------|
| `limits`, `linear-functions` | `rates_of_change_mcq` |
| `polynomials` | `polynomial_end_behavior_mcq` |
| `trigonometry`, `amplitude-and-period` | `periodic_amplitude_mcq` |
| `exponential-functions`, `exponential-decay` | `exponential_growth_mcq` |
| `rational-functions` | `rational_asymptotes_mcq` |
| `log-expressions` | `logarithmic_expressions_mcq` |
| `polar` | `polar_functions_mcq` |
| `regression` | `data_modeling_regression_mcq` |

Aliases are built at runtime from the registry in `pattern_loader.py` (not hardcoded).
