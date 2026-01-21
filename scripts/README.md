# SSOM — Executable Structural Origin Tests

This folder contains the **public, deterministic reference scripts** used to validate
**Shunyaya Structural Origin Mathematics (SSOM)**.

Each script demonstrates how **structural posture at origin** can differ
even when classical mathematical results remain correct.

No script modifies classical mathematics.
All scripts are **observation-only**, deterministic, and reproducible.

---

## Note on Test Numbering

Tests `1a` and `1b` are two structural variants of the same foundational phenomenon:
**derivative behavior at origin**.

Subsequent test numbers (`a3`–`a9`) correspond **conceptually** to Appendix A.3–A.9
in the SSOM specification document.

Not every appendix item is represented as a standalone executable script.
Some items remain **theoretical or compositional cases** documented only in the specification.

There is **no standalone “Test 2” or “Test 8”**.
Numbering reflects **conceptual grouping**, not chronology or completeness.

---

## Script Overview

### ssom_test1a_derivative_sqrt0.py  
**Derivative at singular origin (√x at x = 0)**  
Demonstrates:
- classical derivative failure
- structural abstention at origin
- clean collapse back to classical meaning

---

### ssom_test1b_derivative_x2sin1x_at0.py  
**Derivative exists, neighborhood is structurally violent**  
Demonstrates:
- derivative exists classically
- refinement oscillation near origin
- early structural reliability horizon

---

### ssom_test_a3_limit_path_posture.py  
**Path-dependent limit posture**  
Demonstrates:
- identical classical limits
- distinct structural posture depending on approach path
- calm vs oscillatory origin behavior

---

### ssom_test_a4_integral_equal_area.py  
**Equal integrals, unequal accumulation posture**  
Demonstrates:
- same total area
- different structural strain during accumulation
- origin-aware integration reliability

---

### ssom_test_a5_integral_cancellation.py  
**Cancellation hides structural cost**  
Demonstrates:
- net-zero classical result
- non-zero structural accumulation
- why cancellation does not imply safety

---

### ssom_test_a6_derivative_refinement_fatigue_cos.py  
**Refinement fatigue under repeated differentiation**  
Demonstrates:
- correct derivatives at every step
- gradual structural resistance buildup
- reliability horizon before classical failure

---

### ssom_test_a7_derivative_stiffness_exp.py  
**Derivative stiffness and exponential sensitivity**  
Demonstrates:
- rapidly increasing refinement stress
- stiffness emerging before numeric instability
- structural denial without value failure

---

### ssom_test_a9_derivative_geometry_invariance.py  
**Geometric invariance under coordinate change**  
Demonstrates:
- structural posture invariance
- independence from parameterization
- origin structure as geometric, not numeric

---

## Outputs

Each script writes deterministic CSV traces to its corresponding
`out_ssom_*` folder.

Output files record:
- classical magnitude `m`
- structural alignment `a`
- structural resistance `s`
- posture classification

These traces are **evidence**, not training data.

---

## Determinism Guarantee

Given identical inputs, these scripts always produce:

- identical traces
- identical structural classifications
- identical reliability horizons

No randomness.  
No tuning.  
No learning.  
No heuristics.
