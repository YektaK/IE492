# IE 492 — Sultanbeyli Disaster Response Container Location Optimization: Comprehensive Academic Documentation

**Team:** Elif Keles, Zumra Sancakli, Doga Yardemir, Semanur Aydin  
**Advisor:** Dr. Ahmet Yekta Kayman  
**Department:** Industrial Engineering  
**Date:** June 2026

---

## Table of Contents

1. [Academic Problem Formulation & Mathematical Model](#1-academic-problem-formulation--mathematical-model)
   - 1.1. [Problem Domain and Context](#11-problem-domain-and-context)
   - 1.2. [Stakeholder-Driven Multi-Criteria Decision Analysis](#12-stakeholder-driven-multi-criteria-decision-analysis)
   - 1.3. [Fuzzy Coverage as a Continuous Relaxation of Binary Covering](#13-fuzzy-coverage-as-a-continuous-relaxation-of-binary-covering)
   - 1.4. [Core 0-1 Mixed-Integer Linear Programming Model](#14-core-0-1-mixed-integer-linear-programming-model)
   - 1.5. [Constraint Subsystem Decomposition](#15-constraint-subsystem-decomposition)
   - 1.6. [Extended and Benchmark Optimization Models](#16-extended-and-benchmark-optimization-models)
2. [System Architecture & Codebase Reverse-Engineering](#2-system-architecture--codebase-reverse-engineering)
   - 2.1. [High-Level Architectural Overview](#21-high-level-architectural-overview)
   - 2.2. [Module Inventory and Interaction Map](#22-module-inventory-and-interaction-map)
   - 2.3. [The Seven-Stage Analytical Pipeline](#23-the-seven-stage-analytical-pipeline)
   - 2.4. [Solver Infrastructure and Orchestration](#24-solver-infrastructure-and-orchestration)
   - 2.5. [Algorithmic Flow: From Raw Data to Deployment Plan](#25-algorithmic-flow-from-raw-data-to-deployment-plan)
   - 2.6. [Translation of AI-Generated Logic into Academic Prose](#26-translation-of-ai-generated-logic-into-academic-prose)
3. [Parameter Deep-Dive & Sensitivity Analysis Guide](#3-parameter-deep-dive--sensitivity-analysis-guide)
   - 3.1. [Complete Parameter and Hyperparameter Catalog](#31-complete-parameter-and-hyperparameter-catalog)
   - 3.2. [Parameters by Solution-Phase Dependencies](#32-parameters-by-solution-phase-dependencies)
   - 3.3. [Sensitivity Analysis Framework](#33-sensitivity-analysis-framework)
4. [Literature Review & Academic References](#4-literature-review--academic-references)
   - 4.1. [Facility Location Theory](#41-facility-location-theory)
   - 4.2. [Multi-Criteria Decision Making (MCDM)](#42-multi-criteria-decision-making-mcdm)
   - 4.3. [Fuzzy Set Theory in Spatial Analysis](#43-fuzzy-set-theory-in-spatial-analysis)
   - 4.4. [Multi-Objective and Compromise Programming](#44-multi-objective-and-compromise-programming)
   - 4.5. [Disaster and Humanitarian Logistics](#45-disaster-and-humanitarian-logistics)

---

## 1. Academic Problem Formulation & Mathematical Model

### 1.1. Problem Domain and Context

The Sultanbeyli disaster response container location problem belongs to the class of **capacitated facility location problems under uncertainty** (CFLP-U) extended with **multi-criteria site evaluation** and **non-binary spatial coverage**. The core decision is: _Given a set $$J$$ of 140 candidate sites ($$|J| = 140$$), a set $$I$$ of 15 neighborhoods ($$|I| = 15$$), and an existing network of 12 already-deployed containers ($$M \subset J$$ with $$|M| = 12$$), determine the optimal subset of candidate sites at which to place new disaster-response containers such that aggregate risk-weighted coverage is maximized, spatial inequity is minimized, and site-level quality is rewarded._

The system supports three distinct operational paradigms:

1. **Incremental Augmentation:** New containers (typically 8) are added to the existing 12-container network ($$K_{\text{total}} = 20$$). This preserves sunk infrastructure investment.
2. **Greenfield Redeployment:** All containers are reallocated from scratch ($$K_{\text{total}} = 20$$, no retained existing containers), enabling potentially superior configurations at the cost of relocation.
3. **Flexible Partial Retention:** Any subset of existing containers can be designated as fixed (`KEPT_MEVCUT`), and any candidate can be hard-constrained into or out of the solution (`FIXED_ADAY`).

### 1.2. Stakeholder-Driven Multi-Criteria Decision Analysis

Four evaluation criteria, derived from stakeholder consultations and documented in the project report (`Bitirme Projesi son guncel 1.docx`), form the basis for site-level quality scoring:

| Code    | Criterion                                 | Description                                                                    | Direction            |
| ------- | ----------------------------------------- | ------------------------------------------------------------------------------ | -------------------- |
| $$C_1$$ | Population Density (Nüfus Yoğunluğu)      | Neighborhood-level persons/km² (Sultanbeyli Municipality 2024)                 | Max                  |
| $$C_2$$ | Earthquake Risk (Deprem Riski)            | IBB-KRDAE $$M_w=7.5$$ scenario damage and casualty index (0--50)               | Max                  |
| $$C_3$$ | Access Distance (Erişim Mesafesi)         | Haversine distance to nearest existing container (meters)                      | Max (far = priority) |
| $$C_4$$ | Infrastructure Quality (Ulaşım Altyapısı) | Composite site-level utility score (water, WC, generator, camera, comms; 0--1) | Max                  |

#### 1.2.1. Criteria Weighting: Analytic Hierarchy Process (AHP)

Three stakeholder-preference scenarios are formalized as Saaty (1980) pairwise comparison matrices, solved via the dominant eigenvector method (`src/02_ahp_weights.py:79--137`):

**Pairwise matrix for scenario $$s$$:** $$A^{(s)} \in \mathbb{R}^{4 \times 4}$$, with $$A^{(s)}_{ij} \in \{1/9, 1/8, \ldots, 1/2, 1, 2, \ldots, 8, 9\}$$.

**Step 1. Column normalization:**  
$$A^{(s)}_{\text{norm}} = A^{(s)} / \mathbf{1}^T A^{(s)}$$

**Step 2. Weight vector (row means):**  
$$w^{(s)} = \frac{1}{4} A^{(s)}_{\text{norm}} \mathbf{1}$$

**Step 3. Consistency verification:**  
$$\lambda_{\max}^{(s)} = \frac{1}{4} \sum_i \frac{(A^{(s)} w^{(s)})_i}{w^{(s)}_i}, \quad \text{CI}^{(s)} = \frac{\lambda_{\max}^{(s)} - 4}{3}, \quad \text{CR}^{(s)} = \frac{\text{CI}^{(s)}}{0.90}$$

where $$\text{RI}(n=4) = 0.90$$ (Saaty, 1980). All three scenarios satisfy $$\text{CR}^{(s)} < 0.10$$.

| Scenario              | $$w_{C_1}$$ (Population) | $$w_{C_2}$$ (Earthquake) | $$w_{C_3}$$ (Access) | $$w_{C_4}$$ (Infra.) | CR    |
| --------------------- | ------------------------ | ------------------------ | -------------------- | -------------------- | ----- |
| Baseline              | 0.5406                   | 0.2535                   | 0.1174               | 0.0885               | <0.10 |
| DamageFocused         | 0.6436                   | 0.1943                   | 0.0931               | 0.0690               | <0.10 |
| InfrastructureFocused | 0.4062                   | 0.4062                   | 0.1053               | 0.0823               | <0.10 |

#### 1.2.2. Alternative Weighting: Best-Worst Method (BWM)

As a robustness check, the system also implements the linear BWM formulation (Rezaei, 2015) in `src/02b_bwm_weights.py:52--106`. The optimization minimizes a consistency parameter $$\xi^*$$ via:

$$\begin{aligned}
\min \quad & \xi \\
\text{s.t.} \quad & |w_B - a_{Bj} w_j| \leq \xi \quad \forall j \\
& |w_j - a_{jW} w_W| \leq \xi \quad \forall j \\
& \sum_j w_j = 1, \quad w_j \geq 0
\end{aligned}$$

where $$a_{Bj}$$ are the Best-to-Others preference values and $$a_{jW}$$ are the Others-to-Worst values on the 1--9 scale.

#### 1.2.3. Entropy-Weighted Hybrid Adjustment

The AHP weights are combined with objective entropy weights to produce **hybrid weights** $$w^{\text{hyb}}_j$$ (`results/ahp/ahp_weights_hybrid.xlsx`). This mitigates the subjectivity inherent in purely expert-driven AHP by incorporating the information content of the criteria data themselves. The entropy $$E_j$$ for criterion $$j$$ is computed from the normalized decision matrix, and the hybrid weight is:

$$w_j^{\text{hyb}} = \frac{w_j^{\text{AHP}} \cdot (1 - E_j)}{\sum_k w_k^{\text{AHP}} \cdot (1 - E_k)}$$

#### 1.2.4. MCDM Scoring Methods

Four outranking/scoring methods are implemented, each producing a quality score $$q_j \in [0, 1]$$ for every candidate site $$j$$:

**TOPSIS** (`src/03a_topsis.py:54--81`): The Technique for Order Preference by Similarity to Ideal Solution (Hwang and Yoon, 1981). Two normalization variants are provided: $$L_2$$ (Euclidean vector norm) and Min-Max. The closeness coefficient is:

$$q_j^{\text{TOPSIS}} = \frac{D_j^-}{D_j^+ + D_j^-}$$

where $$D_j^+ = \sqrt{\sum_k (V_{jk} - V_k^+)^2}$$ and $$D_j^- = \sqrt{\sum_k (V_{jk} - V_k^-)^2}$$, with $$V_{jk} = w_k^{\text{hyb}} \cdot r_{jk}$$ being the weighted normalized decision matrix.

**PROMETHEE II** (`src/03b_promethee.py:57--85`): Preference Ranking Organization Method for Enrichment Evaluations (Brans and Vincke, 1985) with a Type V (V-shape) linear preference function. The indifference threshold $$q_k$$ for criterion $$k$$ is set to 20% of the criterion range. The net outranking flow is:

$$q_j^{\text{PROMETHEE}} = \phi(j) = \phi^+(j) - \phi^-(j)$$

where $$\phi^+(j) = \frac{1}{n-1} \sum_{a \neq j} \pi(j, a)$$, $$\phi^-(j) = \frac{1}{n-1} \sum_{a \neq j} \pi(a, j)$$, and $$\pi(a, b) = \sum_k w_k^{\text{hyb}} \cdot P_k(a, b)$$.

**VIKOR** (`src/03c_vikor.py:22--52`): VIseKriterijumska Optimizacija I Kompromisno Resenje (Opricovic and Tzeng, 2004). The compromise ranking index is:

$$Q_j = v \cdot \frac{S_j - S^*}{S^- - S^*} + (1 - v) \cdot \frac{R_j - R^*}{R^- - R^*}$$

where $$S_j = \sum_k w_k \frac{f_k^* - f_{jk}}{f_k^* - f_k^-}$$ and $$R_j = \max_k \left\{ w_k \frac{f_k^* - f_{jk}}{f_k^* - f_k^-} \right\}$$. The benefit-converted score is $$q_j^{\text{VIKOR}} = 1 - Q_j$$.

**ELECTRE** (`src/03d_electre.py:22--54`): ÉLimination Et Choix Traduisant la REalité. Rather than the classical binary outranking graph with strict thresholds, a net concordance flow approach is adopted. The concordance matrix $$C_{ik}$$ aggregates weighted criteria where site $$i$$ is at least as good as site $$k$$. A discordance penalty $$d_{\text{penalty}}$$ proportional to the maximum normalized deficit attenuates the net flow:

$$\phi_{\text{adj}}(j) = \phi_{\text{net}}(j) \cdot \left(1.0 - 0.5 \cdot \max_k D_{jk}\right)$$

which is then min-max normalized to $$[0, 1]$$ to produce $$q_j^{\text{ELECTRE}}$$.

All four MCDM methods are computed for each of the three AHP scenarios (Baseline, DamageFocused, InfrastructureFocused), yielding a total of 12 scoring vectors available to the downstream optimization models.

### 1.3. Fuzzy Coverage as a Continuous Relaxation of Binary Covering

A fundamental methodological contribution of this system is the replacement of classical binary covering (where a neighborhood is either "covered" or "not covered" based on a hard distance radius) with a **Gaussian fuzzy membership function** (`src/04_fuzzy_coverage.py:159--169`). This acknowledges the continuous degradation of service quality with distance—a container 300 meters away provides more effective coverage than one 799 meters away—while maintaining differentiability for solver compatibility.

#### 1.3.1. Gaussian Membership Function with Two-Tier Architecture

The coverage membership $$\mu_{ji} \in [0, 1]$$ of candidate site $$j$$ over neighborhood $$i$$ is:

$$\mu_{ji} = \begin{cases}
1.0, & d_{ji} \leq d_{\text{core}} \\
\exp\left(-\frac{(d_{ji} - d_{\text{core}})^2}{2\sigma_i^2}\right), & d_{ji} > d_{\text{core}} \text{ and } \mu_{ji} \geq \tau \\
0, & \text{otherwise}
\end{cases}$$

where:

- $$d_{ji}$$ is the great-circle (Haversine) or road-network distance from site $$j$$ to the centroid of neighborhood $$i$$
- $$d_{\text{core}} = 300\text{ m}$$ is the "full coverage" core radius (`CORE_DISTANCE`)
- $$\sigma_i$$ is the neighborhood-specific Gaussian decay parameter
- $$\tau = 0.15$$ is the truncation threshold below which membership is set to zero (`TRUNCATION_THRESHOLD`)

#### 1.3.2. Adaptive Sigma: Population-Density-Sensitive Decay

Rather than using a fixed $$\sigma$$, the system computes neighborhood-specific values via inverse linear interpolation against population density (`src/04_fuzzy_coverage.py:74--86`):

$$\sigma_i = \sigma_{\max} - \frac{p_i - p_{\min}}{p_{\max} - p_{\min}} \cdot (\sigma_{\max} - \sigma_{\min})$$

with $$\sigma_{\max} = 1200\text{ m}$$ and $$\sigma_{\min} = 400\text{ m}$$. This ensures that densely populated neighborhoods (where precise coverage targeting is more critical) receive a **narrower** Gaussian ($$\sigma \to 400\text{ m}$$), while sparsely populated areas receive a **wider** Gaussian ($$\sigma \to 1200\text{ m}$$). The physical intuition: in a dense urban core, even a small location error has large population consequences, so the model demands greater spatial precision.

#### 1.3.3. Fixed-Sigma and Composite Modes

Three additional sigma modes are supported:

- **Fixed (e.g., `800`):** All neighborhoods share $$\sigma = 800\text{ m}$$. This is the baseline reference.
- **Composite/Two-Tier (e.g., `800_300`):** The element-wise maximum of two Gaussian surfaces with $$\sigma = 800\text{ m}$$ and $$\sigma = 300\text{ m}$$ is taken (`src/04_fuzzy_coverage.py:177--188`), creating a hybrid surface that rewards very close proximity more sharply.
- **RoadNetwork:** Identical to the adaptive sigma calculation but uses OSMnx-derived road-network distances instead of Haversine distances (`src/04_fuzzy_coverage.py:131--146`).

#### 1.3.4. The Road-Access Multiplier $$Q_i$$

A scenario-dependent road-access penalty vector $$Q_i \in [0, 1]$$ is applied to each neighborhood's coverage contribution (`src/scenario_utils.py:13--47`):

- **Scenario A (Reference):** $$Q_i = 1.0$$ for all $$i$$. No road-closure effect.
- **Scenario B (Road Closures):** $$Q_i = p_{\text{road\_open}, i}$$, where $$p_{\text{road\_open}, i}$$ is the estimated probability that roads to neighborhood $$i$$ remain open post-earthquake.

This multiplier directly scales the effective coverage: a neighborhood with a 30% road-closure probability ($$Q_i = 0.70$$) receives only 70% of the nominal coverage benefit from any container placement.

### 1.4. Core 0-1 Mixed-Integer Linear Programming Model

The primary optimization model (implemented in `src/05_ip.py:124--176` and `src/solver_core.py:34--65`) is a bi-objective 0-1 MILP:

#### 1.4.1. Decision Variables

$$X_j \in \{0, 1\} \quad \forall j \in J \qquad \text{(1 if candidate site $$j$$ is selected, 0 otherwise)}$$

#### 1.4.2. Coverage Variables (Auxiliary)

$$C_i = Q_i \cdot \left( \sum_{m \in M^{\text{kept}}} \mu_{mi} + \sum_{j \in J} \mu_{ji} \cdot P_j \cdot X_j \right) \quad \forall i \in I$$

where:

- $$M^{\text{kept}} \subseteq M$$ is the subset of existing containers retained in the solution
- $$P_j \in [0, 1]$$ is the probability that the access road to candidate site $$j$$ is open ($$p_{\text{access\_road}}$$)
- The first term captures coverage from retained existing containers; the second captures coverage from newly selected candidates

#### 1.4.3. Objective Function

$$\max_{X} \quad Z = \underbrace{\sum_{i \in I} R_i \cdot C_i}_{\text{Risk-Weighted Coverage (RxC)}} \;+\; \beta \cdot \underbrace{\sum_{j \in J} q_j \cdot X_j}_{\text{Site Quality Bonus}}$$

where:

- $$R_i = \frac{r_i}{\max_k r_k} \in (0, 1]$$ is the normalized neighborhood risk score (or population weight)
- $$q_j \in [0, 1]$$ is the MCDM quality score for candidate site $$j$$
- $$\beta \geq 0$$ is the **quality-coverage tradeoff parameter** (`BETA_QUALITY`)

**Interpretation:** The first term $$\sum_i R_i C_i$$ (referred to in code as "RxC" — Risk times Coverage) aggregates the risk-weighted total coverage across all neighborhoods. This is the **primary operational objective**: maximizing how well at-risk populations are served. The second term $$\beta \sum_j q_j X_j$$ provides a **secondary site-quality incentive**: among solutions with similar aggregate coverage, prefer solutions that select higher-quality (better-infrastructure, more-accessible) candidate sites. When $$\beta = 0$$, the model reduces to pure coverage maximization; as $$\beta \to 1$$, site quality assumes increasing influence.

#### 1.4.4. Multiple Weight-Type Variants

The weight vector $$R_i$$ can be parametrized in three ways (`src/05_ip.py:63--73`):

1. **Risk-weighted** (`WEIGHT_TYPE="risk"`): $$R_i \propto r_i$$, the neighborhood earthquake risk score. Prioritizes the most seismically vulnerable neighborhoods.
2. **Population-weighted** (`WEIGHT_TYPE="population"`): $$R_i \propto p_i$$, the 2024 population. Prioritizes the most populous neighborhoods.
3. **Shelter-need-weighted** (`WEIGHT_TYPE="shelter"`): $$R_i \propto h_i$$, the estimated household shelter deficit. Prioritizes neighborhoods with greatest shelter demand.

All three weight vectors are proportionally scaled: $$R_i = \frac{w_i}{\max_k w_k}$$ (ensuring $$R_i \in (0, 1]$$).

### 1.5. Constraint Subsystem Decomposition

The constraint set (defined in `src/solver_core.py:45--65`) operates in five layers:

#### Layer 1: Cardinality Constraint

$$\sum_{j \in J} X_j = K_{\text{total}} - |M^{\text{kept}}|$$

This enforces that exactly enough new containers are selected to reach the total budget $$K_{\text{total}}$$, accounting for retained existing containers.

#### Layer 2: Fixed-Site Constraints

$$X_{j} = 1 \quad \forall j \in F$$

where $$F \subseteq J$$ is the set of candidate sites designated as `FIXED_ADAY` (mandatory inclusion). This enables scenario-specific hard constraints.

#### Layer 3: Minimum-One-per-Neighborhood Constraint

$$\sum_{j \in J_i} X_j + |M^{\text{kept}}_i| \geq 1 \quad \forall i \in I$$

where $$J_i = \{j \in J : \text{site } j \text{ is in neighborhood } i\}$$ and $$M^{\text{kept}}_i$$ is the count of retained existing containers in neighborhood $$i$$. This **equity constraint** ensures every neighborhood receives at least one container (existing or new). Enabled when `min_one=True` (default).

#### Layer 4: Risk-Proportional Minimum Coverage

$$C_i \geq \delta \cdot R_i \quad \forall i \in I$$

where $$\delta = 0.50$$ is the coverage threshold constant (`COVERAGE_THRESHOLD`). This enforces that higher-risk neighborhoods receive proportionally higher minimum coverage levels. The constraint is enabled when `risk_prop=True` (default).

#### Layer 5: Problem-Dependent Hard Minimums

Specific models add further hard constraints (e.g., $$\min_i C_i \geq 0.50$$ in the lexicographic and single-stage models), representing a societal consensus that no neighborhood should fall below a critical service floor.

### 1.6. Extended and Benchmark Optimization Models

Beyond the core MILP, the system implements six additional formulations that serve as either theoretical benchmarks, alternative decision paradigms, or Pareto-frontier exploration tools.

#### 1.6.1. Location Set Covering Problem (LSCP) — `src/08_lscp.py`

**Purpose:** Determine the minimum number of containers $$K_{\min}$$ required to achieve $$\mu \geq 0.50$$ coverage in every neighborhood. This serves as a **lower bound reference**: no feasible deployment with fewer than $$K_{\min}$$ containers can provide universal service.

**Formulation:**

$$\begin{aligned}
\min \quad & \sum_{j \in J} X_j \\
\text{s.t.} \quad & Q_i \cdot \left( \sum_{m \in M^{\text{kept}}} \mu_{mi} + \sum_{j \in J} \mu_{ji} \cdot X_j \right) \geq 0.50 \quad \forall i \in I \\
& X_j \in \{0, 1\}
\end{aligned}$$

The solver sequentially checks $$K = 1, 2, \ldots, K_{\max}$$ until feasibility is achieved (`src/08_lscp.py:69--100`).

#### 1.6.2. Maximal Covering Location Problem (MCLP) — `src/16_mclp.py`

**Purpose:** A **classical benchmark** against which the fuzzy-coverage model can be compared. Uses hard binary covering ($$a_{ji} = \mathbb{I}[d_{ji} \leq S]$$) rather than fuzzy membership.

**Formulation:**

$$\begin{aligned}
\max \quad & \sum_{i \in I} W_i \cdot Y_i \\
\text{s.t.} \quad & \sum_{j \in J} a_{ji} X_j + \sum_{m \in M^{\text{kept}}} a_{mi} \geq Y_i \quad \forall i \in I \\
& \sum_{j \in J} X_j = K_{\text{total}} - |M^{\text{kept}}| \\
& X_j, Y_i \in \{0, 1\}
\end{aligned}$$

where $$W_i$$ is the demand weight (population, shelter need, or risk) at neighborhood $$i$$, and $$Y_i = 1$$ if neighborhood $$i$$ is covered by at least one selected container.

#### 1.6.3. Two-Stage Lexicographic Maximin — `src/11_lexicographic.py`

**Purpose:** Find the Pareto-optimal solution that maximizes equity (the minimum neighborhood coverage) without sacrificing more than $$\varepsilon = 0.01$$ of the optimal total coverage.

**Stage 1 — Maximize Aggregate Coverage (RxC):**

$$\begin{aligned}
\max \quad & Z_1 = \sum_{i \in I} R_i \cdot C_i + \beta \sum_{j \in J} q_j \cdot X_j \\
\text{s.t.} \quad & \text{Layers 1--3}, \quad C_i \geq 0.50 \;\; \forall i
\end{aligned}$$

Let $$Z_1^*$$ be the optimal value.

**Stage 2 — Maximize Minimum Coverage:**

$$\begin{aligned}
\max \quad & t \\
\text{s.t.} \quad & C_i \geq t \quad \forall i \in I \\
& \sum_{i \in I} R_i \cdot C_i + \beta \sum_{j \in J} q_j \cdot X_j \geq Z_1^* - \varepsilon \\
& \text{Layers 1--3}, \quad C_i \geq 0.50 \;\; \forall i
\end{aligned}$$

This implements the **lexicographic maximin** (or _Rawlsian_) criterion: among all solutions with near-optimal total welfare, select the one that maximizes the welfare of the worst-off neighborhood.

#### 1.6.4. Epsilon-Constraint Pareto Frontier — `src/13_eps_constraint.py`

**Purpose:** Generate the **Pareto front** between total coverage (efficiency) and minimum neighborhood coverage (equity) using the augmented $$\varepsilon$$-constraint method (AUGMECON2; Mavrotas, 2009).

**Formulation for each $$\varepsilon$$:**

$$\begin{aligned}
\max \quad & \sum_{i \in I} R_i \cdot C_i + \beta \sum_{j \in J} q_j \cdot X_j + \rho \sum_{i \in I} s_i \\
\text{s.t.} \quad & C_i - s_i = \varepsilon \quad \forall i \in I \quad \text{(AUGMECON2 surplus)} \\
& s_i \geq 0, \quad \text{Layers 1--4} \\
& X_j \in \{0, 1\}
\end{aligned}$$

where $$\rho = 10^{-5}$$ is a small positive coefficient that ensures only _Pareto-efficient_ (non-weakly-dominated) solutions are generated. The $$\varepsilon$$ grid spans $$[0.80, 1.20]$$ in 20 increments (`src/13_eps_constraint.py:108`).

#### 1.6.5. Equity-Integrated Single-Stage MILP — `src/14_single_stage.py`

**Purpose:** Integrate equity directly into the objective function via binary "service indicator" variables, avoiding the two-stage solve.

**Formulation:**

$$\begin{aligned}
\max \quad & \sum_{i \in I} R_i \cdot C_i + \beta \sum_{j \in J} q_j \cdot X_j + \alpha \sum_{i \in I} W_i \\
\text{s.t.} \quad & C_i \geq \delta \cdot W_i \quad \forall i \in I \quad \text{(coverage-to-service linking)} \\
& \text{Layers 1--3} \\
& X_j \in \{0, 1\}, \quad W_i \in \{0, 1\}
\end{aligned}$$

where $$\alpha = 0.20$$ (`EQUITY_ALPHA`) and $$\delta = 0.50$$ (`COVERAGE_THRESHOLD`). $$W_i = 1$$ indicates neighborhood $$i$$ has been "adequately served." The model rewards solutions that serve more neighborhoods at the $$\delta$$ threshold level.

#### 1.6.6. Compromise Programming — `src/15_compromise.py`

**Purpose:** From the Pareto front generated by the $$\varepsilon$$-constraint method, identify the **ideal compromise solution** by minimizing $$L_p$$ distance from the utopia point (maximum RxC, maximum min-coverage).

**Formulation:** Let $$\mathbf{f}^* = (\text{RxC}^*, \text{min\_cov}^*)$$ be the ideal point (each objective independently maximized) and $$\mathbf{f}^- = (\text{RxC}^-, \text{min\_cov}^-)$$ be the anti-ideal point. For each Pareto solution $$k$$ with objective vector $$\mathbf{f}_k$$:

$$d_p(k) = \left[ \sum_{m \in \{\text{RxC}, \text{min\_cov}\}} \left( \frac{|f_m^* - f_{mk}|}{f_m^* - f_m^-} \right)^p \right]^{1/p}$$

for $$p = 1$$ (Manhattan, $$L_1$$), $$p = 2$$ (Euclidean, $$L_2$$), and $$p = \infty$$ (Chebyshev, $$L_\infty$$). The compromise solution is $$\arg\min_k d_p(k)$$ for each norm.

#### 1.6.7. Gini Inequality Analysis — `src/09_gini.py`

**Purpose:** Quantify the spatial equity of a container deployment using the Gini coefficient of neighborhood coverage values.

$$G = \frac{2 \sum_{i=1}^{n} i \cdot C_{(i)}}{n \sum_{i=1}^{n} C_{(i)}} - \frac{n + 1}{n}$$

where $$C_{(1)} \leq C_{(2)} \leq \ldots \leq C_{(n)}$$ are the sorted neighborhood coverage values. $$G = 0$$ indicates perfect equality; $$G = 1$$ indicates maximum inequality. This metric complements the optimization by providing a post-hoc equity diagnostic.

---

## 2. System Architecture & Codebase Reverse-Engineering

### 2.1. High-Level Architectural Overview

The system follows a **layered analytical pipeline** architecture, organized as a directed acyclic graph (DAG) of computational stages. At the highest level, there are three major layers:

1. **Data Preparation Layer** (Stage 1): Transforms raw municipal and seismological data (Excel spreadsheets, GeoJSON shapefiles, OSM street networks) into standardized, analysis-ready tabular formats.

2. **Analytical Pipeline Layer** (Stages 2--7): The core seven-stage processing pipeline that computes criteria weights, MCDM scores, fuzzy coverage matrices, optimal location selections, cross-model comparisons, and final reports.

3. **Presentation and Orchestration Layer** (`app.py`, `app_runner.py`, `run_all_scenarios.py`): A Streamlit web application with six interactive tabs, a job queue system, and an experiment configuration engine that can execute any combination of pipeline stages with any parameterization.

### 2.2. Module Inventory and Interaction Map

```
                    ┌──────────┐
                    │ config.py│  ← Global constants, paths, logging, utilities
                    └────┬─────┘
                         │ (imported by all modules)
    ┌────────────────────┼────────────────────────┐
    │                    │                        │
┌───▼──────┐     ┌──────▼──────┐        ┌────────▼────────┐
│01_data   │     │ 02_ahp      │        │04_fuzzy_coverage │
│_prep.py  │     │ _weights.py │        │     .py           │
│(raw→xls) │     │(AHP w, CR)  │        │(Gaussian μ_{ji})  │
└───┬──────┘     └──────┬──────┘        └────────┬────────┘
    │                   │                        │
    │        ┌──────────┼──────────┐             │
    │   ┌────▼───┐ ┌────▼───┐ ┌───▼────┐  ┌─────▼──────┐
    │   │ 03a    │ │ 03b    │ │ 03c,d  │  │scenario_   │
    │   │TOPSIS  │ │PROM... │ │VIKOR/  │  │utils.py Q_i│
    │   └────┬───┘ └────┬───┘ │ELECTRE │  └─────┬──────┘
    │        │          │     └───┬────┘        │
    │        │  MCDM    │         │             │
    │        └──────────┼─────────┘             │
    │                   │                       │
    │              ┌────▼────────┐         ┌────▼──────────┐
    │              │solver_core  │◄────────┤ 05_ip.py      │
    │              │(PuLP model  │         │(MILP 12×MCDM) │
    │              │ builders)   │         └───────┬────────┘
    │              └─────────────┘                 │
    │                                        ┌─────┴─────┐
    │   ┌─────────────────────────────────────┤06_compare │
    │   │  Extended Models:                   └───────────┘
    │   │  08_lscp → 11_lexicographic → 13_eps_constraint
    │   │  14_single_stage → 15_compromise → 16_mclp
    │   │  09_gini → 10_infra_score → 12_sigma_grid
    │   └──────────────────────────────────────────┘
    │                                     │
    └─────────────────┬───────────────────┘
                      │
               ┌──────▼──────┐
               │ 07_report   │  → Excel (report_generator.py)
               │  ing.py     │  → PDF  (excel_report_generator.py)
               └─────────────┘  → Maps (visualization.py)
```

### 2.3. The Seven-Stage Analytical Pipeline

#### Stage 1: Data Preparation (`01_data_prep.py`)

**Inputs:** Raw Excel files, GeoJSON shapefiles.  
**Outputs:** `data/processed/{adaylar_140, mevcut_12, criteria_matrix, mahalle_nufus, mahalle_risk, mahalle_barinma, mahalle_centroids, p_road_open}.xlsx`.  
**Function:** Standardizes Turkish character encoding, normalizes neighborhood names, computes Haversine distances, generates amplified (power-transformed) criteria columns ($$\text{C1\_hasar\_risk\_amp}$$, etc.) for better MCDM discriminability.

#### Stage 2: Criteria Weighting (`02_ahp_weights.py`, `02b_bwm_weights.py`, `01b_entropy_weights.py`)

**Inputs:** Hardcoded pairwise comparison matrices (AHP), synthetic BWM preference vectors.  
**Outputs:** `results/ahp/ahp_weights.xlsx`, `ahp_weights_hybrid.xlsx`, `ahp_pairwise_matrices.json`, `bwm_weights.xlsx`.  
**Function:** Solves the AHP dominant eigenvector for three scenarios, verifies CR < 0.10, combines with entropy for hybrid weights. BWM solves via SciPy SLSQP constrained optimization.

#### Stage 3: MCDM Scoring (`03a_topsis.py`, `03b_promethee.py`, `03c_vikor.py`, `03d_electre.py`)

**Inputs:** `criteria_matrix.xlsx`, `ahp_weights_hybrid.xlsx`.  
**Outputs:** `results/mcdm/{topsis_cc, promethee_phi, vikor_q, electre_net_flow}.xlsx`.  
**Function:** Each method computes 140 quality scores per AHP scenario (3 scenarios × 4 methods = 12 vectors). All scores are min-max normalized to $$[0, 1]$$.

#### Stage 4: Fuzzy Coverage (`04_fuzzy_coverage.py`, optionally `04b_coverage_boundary.py`)

**Inputs:** Candidate and existing container coordinates, neighborhood centroids, population data.  
**Outputs:** `results/fuzzy_coverage/{mu_aday, mu_mevcut, distance_aday, distance_mevcut, Q_i_vector, adaptive_sigmas}.xlsx`.  
**Function:** Computes the $$140 \times 15$$ fuzzy membership matrix $$\mu_{ji}$$ for candidates and the $$12 \times 15$$ matrix for existing containers, using the chosen sigma mode (Adaptive, RoadNetwork, fixed, or composite). Constructs the $$Q_i$$ vector.

#### Stage 5: Optimization (`05_ip.py` and all extended model scripts)

**Inputs:** Fuzzy coverage matrices, MCDM score vectors, weight data, configuration parameters ($$K$$, $$\beta$$, $$\sigma$$, truncation).  
**Outputs:** `results/models/summary_all_*.xlsx`, per-variant `ip_*.xlsx`, `coverage_*.xlsx`.  
**Function:** Iterates over all MCDM-method × AHP-scenario combinations (4 × 3 = 12 solves per run), builds and solves the 0-1 MILP, records objective values, selected sites, and neighborhood-level coverage.

#### Stage 6: Comparison (`06_compare.py`, `06b_ip_compare.py`)

**Inputs:** Model outputs from Stage 5.  
**Outputs:** `results/comparison/` — cross-tabulations of selected sites, agreement matrices, overlap percentages.  
**Function:** Quantifies the agreement between solutions from different MCDM methods and AHP scenarios, producing heatmaps and concordance statistics.

#### Stage 7: Reporting (`07_reporting.py`, `excel_report_generator.py`, `report_generator.py`, `visualization.py`)

**Inputs:** All upstream results.  
**Outputs:** Multi-sheet Excel reports, PDF reports with charts, interactive Folium HTML maps, Lorenz curves, radar charts.  
**Function:** Synthesizes all analytical outputs into presentation-ready deliverables.

### 2.4. Solver Infrastructure and Orchestration

The solver selection logic (`src/solver_core.py:14--22`) implements automatic solver detection:

```python
if "HiGHS" in available_solvers:
    return pulp.HiGHS(msg=msg, timeLimit=time_limit)
else:
    return pulp.PULP_CBC_CMD(msg=msg, timeLimit=time_limit)
```

**HiGHS** (Huangfu and Hall, 2018) is preferred when available due to its superior performance on 0-1 MILPs; **CBC** (COIN-OR Branch-and-Cut) serves as the fallback. Typical solve times are <100 ms for any single model instance (140 binary variables, 15 continuous auxiliary variables, ~45 constraints), making the system suitable for interactive use via the Streamlit web interface.

#### Experiment Configuration Engine (`experiments_config.json`)

Ten predefined experiments are specified declaratively:

| Experiment     | Scenario | $$\sigma$$ | $$\beta$$ | $$K_{\text{new}}$$ | Truncate | No Mevcut | Extended Models        |
| -------------- | -------- | ---------- | --------- | ------------------ | -------- | --------- | ---------------------- |
| Baseline_SA    | A        | 800        | 0.30      | 8                  | 0        | No        | LSCP, Lex, Eps, SS, CP |
| RoadClosure_SB | B        | 800        | 0.30      | 8                  | 0        | No        | LSCP, Lex, Eps, SS, CP |
| TwoTier_SA     | A        | 800_300    | 0.30      | 8                  | 0        | No        | LSCP, Lex, Eps, SS     |
| TwoTier_SB     | B        | 800_300    | 0.30      | 8                  | 0        | No        | LSCP, Lex, Eps, SS     |
| BetaGrid_SA    | A        | 800        | 0.0--1.0  | 8                  | 0        | No        | —                      |
| FullReloc_SA   | A        | 800        | 0.30      | 20                 | 0        | **Yes**   | —                      |
| FullReloc_SB   | B        | 800        | 0.30      | 20                 | 0        | **Yes**   | —                      |
| Truncation_SA  | A        | 800        | 0.30      | 8                  | 0.20     | No        | —                      |
| Truncation_SB  | B        | 800        | 0.30      | 8                  | 0.20     | No        | —                      |

The `run_all_scenarios.py` module reads this configuration and executes the specified steps sequentially, with the Streamlit front-end (`app.py`) providing a job queue (`jobs.json`) and execution log (`completed_jobs_log.json`).

### 2.5. Algorithmic Flow: From Raw Data to Deployment Plan

The complete algorithmic flow proceeds as follows:

```
1. DATA INGESTION
   ├── Load 140 candidate sites (AYDES registry) with lat/lon, neighborhood,
   │   access-road probability, and 4 amplified criteria scores
   ├── Load 12 existing containers with lat/lon, neighborhood
   ├── Load 15 neighborhood centroids, population (2024), risk scores (0-50),
   │   shelter needs, road-open probabilities (Scenario B)
   └── Standardize Turkish character encoding, normalize neighborhood names

2. CRITERIA WEIGHTING (AHP)
   ├── Define 3 Saaty pairwise comparison matrices (4×4 each)
   ├── For each scenario s:
   │   ├── Normalize columns: A_norm = A / col_sums
   │   ├── Compute weight vector: w = row_means
   │   ├── Solve for λ_max = mean(A·w / w)
   │   ├── Compute CI = (λ_max - 4) / 3, CR = CI / 0.90
   │   └── Assert CR < 0.10 (raise ValueError otherwise)
   └── Export weights to Excel + JSON

3. MCDM SCORING (×4 methods)
   ├── Load amplified criteria matrix (140×4)
   ├── For each AHP scenario s (Baseline, DamageFocused, InfrastructureFocused):
   │   ├── TOPSIS:      L₂ & MinMax normalization → CC ∈ [0,1] (q_j)
   │   ├── PROMETHEE:   V-shape pref. func., q_k=0.2×range → phi ∈ [-1,1] → [0,1]
   │   ├── VIKOR:       v=0.5, S & R → Q ∈ [0,1] → q_j = 1 - Q
   │   └── ELECTRE:     Concordance + discordance penalty → net flow → [0,1]
   └── Export 12 score vectors (4 methods × 3 scenarios)

4. FUZZY COVERAGE COMPUTATION
   ├── Choose sigma mode: Adaptive | Fixed(800) | Composite(800_300) | RoadNetwork
   ├── Compute distance matrices:
   │   ├── Haversine great-circle (default) or OSMnx road-network distances
   │   └── d_aday[140×15], d_mevcut[12×15]
   ├── If Adaptive:
   │   ├── Compute σ_i = 1200 - (pop_i - pop_min)/(pop_max - pop_min) × 800
   │   └── [400m, 1200m] range
   ├── Compute μ_ji = exp(-max(d_ji - 300, 0)² / (2 × σ_i²))
   ├── Apply truncation: μ_ji ← 0 if μ_ji < 0.15
   ├── If composite mode: μ_ji = max(μ_ji(σ₁), μ_ji(σ₂))
   └── Load Q_i vector (Scenario A: all 1.0; Scenario B: p_road_open)

5. 0-1 MILP FORMULATION AND SOLUTION
   ├── For each (MCDM method m, AHP scenario s):
   │   ├── Load q_j[m][s] score vector
   │   ├── Build LP problem: prob = LpProblem("Sultanbeyli_{m}_{s}", LpMaximize)
   │   ├── Declare X_j ∈ {0,1} (140 binary variables)
   │   ├── Compute C_i = Q_i × (Σ_{mevcut} μ_mi + Σ_j μ_ji × P_j × X_j)
   │   ├── Set objective: max Σ_i R_i·C_i + β·Σ_j q_j·X_j
   │   ├── Add cardinality: Σ X_j = K_total - |M_kept|
   │   ├── Add min-one-per-mahalle: Σ_{j∈J_i} X_j + |M_kept_i| ≥ 1  ∀i
   │   ├── Add risk-prop. coverage: C_i ≥ 0.50 × R_i  ∀i
   │   ├── Solve with HiGHS (preferred) or CBC
   │   └── Record: Z_total, Z_risk (RxC), Z_quality, selected_idx,
   │       coverage_vec, min/avg/max coverage, mahalle-below-threshold stats
   └── Export summary + per-variant detail Excel files

6. EXTENDED MODEL COMPUTATION (optional, per experiment config)
   ├── LSCP:     scan K=1..15 for minimum feasible deployment
   ├── Lexicographic: Stage 1 RxC-max → Stage 2 min-C_i-max (ε=0.01)
   ├── Epsilon-constraint: sweep ε ∈ [0.80, 1.20] in 20 steps → Pareto front
   ├── Single-Stage: add α·Σ W_i equity term to objective
   ├── Compromise: L₁/L₂/L∞ distance from utopia point on Pareto front
   └── MCLP:     classical binary covering benchmark

7. REPORTING AND VISUALIZATION
   ├── Excel: multi-sheet workbook (summary, by-model, by-mahalle, comparison)
   ├── PDF: full academic report with tables, charts (fpdf2)
   ├── Maps: interactive Folium HTML (color-coded containers, mahalle polygons,
   │         coverage heat overlays, OSM basemap tiles)
   ├── Charts: coverage bar charts, sensitivity plots, Pareto front graphs,
   │          Lorenz curves, radar charts, comparison scatter plots
   └── Gini:   post-hoc spatial inequality analysis of neighborhood coverage
```

### 2.6. Translation of AI-Generated Logic into Academic Prose

Several components of the codebase exhibit patterns characteristic of AI-assisted development. This section translates the most algorithmically significant instances.

#### 2.6.1. The Bi-Objective Aggregation ($$\beta$$-weighted sum)

The objective function `Z_risk + beta * Z_quality` (`src/05_ip.py:137`) is an instance of the **weighted sum method** (Cohon, 1978) for bi-objective optimization. It scalarizes the two objectives (risk-weighted coverage and site quality) into a single objective by assigning a relative weight $$\beta$$. The implications are well-understood in multi-objective optimization theory:

- For $$\beta = 0$$: Pure coverage maximization. Site quality is ignored entirely.
- For $$0 < \beta < \infty$$: Intermediate tradeoffs. Only **supported** Pareto-optimal solutions (those lying on the convex hull of the Pareto front) are reachable by the weighted sum method.
- For $$\beta \to \infty$$: Effectively a lexicographic ordering where quality dominates coverage.

The system's $$\beta \in [0, 1]$$ with a default of 0.30 is deliberately kept modest, recognizing that coverage (saving lives) is the primary objective and site quality is a secondary refinement. The beta-grid experiment (`BetaGrid_SA`, $$\beta \in \{0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0\}$$) provides empirical evidence for this tradeoff.

#### 2.6.2. The Core-Distance Two-Tier Architecture

The conditional logic:

```python
eff_dist = np.maximum(dist - core, 0)
mu_col = np.exp(-(eff_dist ** 2) / (2 * s ** 2))
```

(`src/04_fuzzy_coverage.py:165--166`) creates a **flat-topped Gaussian** (sometimes called a "Mexican hat" with a plateau). The physical interpretation: up to $$d_{\text{core}} = 300\text{ m}$$, coverage is perfect ($$\mu = 1$$). Beyond this, coverage decays according to the familiar Gaussian bell curve. This is more realistic than a pure Gaussian (which would assign $$\mu < 1$$ even at zero distance) and more nuanced than binary covering (which creates an artificial cliff at exactly $$S$$ meters).

#### 2.6.3. The Augmented $$\varepsilon$$-Constraint (AUGMECON2) Surplus Variables

The inclusion of surplus variables $$s_i$$ in the $$\varepsilon$$-constraint model (`src/13_eps_constraint.py:123--126`) with constraint $$C_i - s_i = \varepsilon$$ and a small positive coefficient ($$10^{-5}$$) in the objective implements the **AUGMECON2** method (Mavrotas, 2009). This technique:

1. Converts the inequality constraint $$C_i \geq \varepsilon$$ into an equality $$C_i - s_i = \varepsilon$$.
2. Adds the surplus variables $$s_i$$ to the objective with a negligible coefficient ($$\rho = 10^{-5}$$).
3. Guarantees that only **Pareto-efficient** (non-weakly-dominated) solutions are generated—the solver has an incentive to maximize the surplus beyond $$\varepsilon$$ when slack exists, avoiding the well-known problem of weakly-dominated solutions in classical $$\varepsilon$$-constraint.

#### 2.6.4. The Proportional Risk-Targeting Constraint

The constraint $$C_i \geq 0.50 \cdot R_i$$ (`src/solver_core.py:65`) operationalizes a **needs-proportionate equity principle**: neighborhoods with higher normalized risk scores $$R_i$$ must receive proportionally higher minimum coverage. This is an implementation of the Aristotelian distributive justice principle ("to each according to their need"), translated into a MILP constraint.

#### 2.6.5. The Inverse-Linear Adaptive Sigma

The formula:

$$\sigma_i = 1200 - \frac{p_i - p_{\min}}{p_{\max} - p_{\min}} \cdot (1200 - 400)$$

(`src/04_fuzzy_coverage.py:83`) implements an **inverse-population-density sensitivity scaling**. In densely populated areas ($$p_i \to p_{\max}$$), $$\sigma_i \to 400\text{ m}$$ (narrow Gaussian → precise targeting required). In sparsely populated areas ($$p_i \to p_{\min}$$), $$\sigma_i \to 1200\text{ m}$$ (wide Gaussian → broad reach acceptable). This is a novel heuristic that encodes the spatial precision-vs-reach tradeoff as a function of the demographic consequence of imprecision.

---

## 3. Parameter Deep-Dive & Sensitivity Analysis Guide

### 3.1. Complete Parameter and Hyperparameter Catalog

#### 3.1.1. Structural and Budgetary Parameters

| Parameter               | Variable             | Location                      | Default | Range                              | Effect                                                                                                         |
| ----------------------- | -------------------- | ----------------------------- | ------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Total containers        | $$K_{\text{total}}$$ | `05_ip.py:57` (arg `K_TOTAL`) | 20      | $$\geq 1$$                         | Budget constraint. Larger $$K$$ increases coverage but also cost. Diminishing returns observed above $$K=28$$. |
| New containers only     | `--K`                | `05_ip.py:237` (CLI)          | 8       | $$\geq 0$$                         | Interface convenience: $$K_{\text{total}} = K_{\text{new}} + \|M^{\text{kept}}\|$$.                            |
| Kept existing indices   | `KEPT_MEVCUT`        | `05_ip.py:43`, `config.py:82` | All 12  | Any subset of $$\{0,\ldots,11\}$$  | Empty list = full relocation. Partial subsets enable selective retention.                                      |
| Fixed candidate indices | `FIXED_ADAY`         | `05_ip.py:43` (arg)           | `[]`    | Any subset of $$\{0,\ldots,139\}$$ | Hard-constrain specific candidates into the solution.                                                          |

#### 3.1.2. Objective Function Parameters

| Parameter                 | Variable                      | Location                                | Default  | Range                               | Effect                                                                                                                                                    |
| ------------------------- | ----------------------------- | --------------------------------------- | -------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Quality-coverage tradeoff | $$\beta$$                     | `05_ip.py:57`, `config.py:20`           | 0.30     | $$[0, 1]$$ or higher                | At $$\beta=0$$: pure coverage; at $$\beta=1$$: 50--50 weight. Higher values increasingly prioritize MCDM-quality sites.                                   |
| Weight type               | `weight_type` / `WEIGHT_TYPE` | `05_ip.py:63--72`                       | `"risk"` | `{"risk", "population", "shelter"}` | Determines which vector populates $$R_i$$. Fundamentally changes which neighborhoods the model prioritizes.                                               |
| Equity term weight        | $$\alpha$$                    | `config.py:21`, `14_single_stage.py:31` | 0.20     | $$[0, 1]$$                          | Weight of the $$\sum W_i$$ equity term in single-stage model. Higher $$\alpha$$ favors solutions covering more neighborhoods at the $$\delta$$ threshold. |

#### 3.1.3. Fuzzy Coverage Parameters

| Parameter            | Variable                 | Location                                  | Default      | Range                                             | Effect                                                                                                                                                                               |
| -------------------- | ------------------------ | ----------------------------------------- | ------------ | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Sigma mode           | $$\sigma_{\text{mode}}$$ | `04_fuzzy_coverage.py:103--121`           | `"Adaptive"` | `{"Adaptive","RoadNetwork", "800","800_300",...}` | Controls spatial decay of coverage. `Adaptive`: population-sensitive $$[400,1200]\text{ m}$$. `800`: uniform. `800_300`: composite maximum. `RoadNetwork`: uses real road distances. |
| Core distance        | $$d_{\text{core}}$$      | `04_fuzzy_coverage.py:34`                 | 300 m        | $$\geq 0$$                                        | Radius of guaranteed $$\mu=1.0$$ coverage. Increasing flattens the peak; decreasing sharpens it.                                                                                     |
| Adaptive sigma max   | $$\sigma_{\max}$$        | `04_fuzzy_coverage.py:83`                 | 1200 m       | > $$\sigma_{\min}$$                               | Upper asymptote of adaptive sigma (for least-populated areas).                                                                                                                       |
| Adaptive sigma min   | $$\sigma_{\min}$$        | `04_fuzzy_coverage.py:83`                 | 400 m        | < $$\sigma_{\max}$$                               | Lower asymptote of adaptive sigma (for most-populated areas).                                                                                                                        |
| Truncation threshold | $$\tau$$                 | `config.py:19`, `04_fuzzy_coverage.py:33` | 0.15         | $$[0, 1)$$                                        | $$\mu_{ji}$$ values below $$\tau$$ are set to 0. $$0$$ = no truncation. Larger values sparsify the coverage matrix, forcing sites to be closer to neighborhoods to have any effect.  |

#### 3.1.4. Constraint Parameters

| Parameter               | Variable        | Location                   | Default          | Range         | Effect                                                                                                                                  |
| ----------------------- | --------------- | -------------------------- | ---------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Coverage threshold      | $$\delta$$      | `config.py:18`             | 0.50             | $$[0, 1]$$    | Risk-proportional floor: $$C_i \geq \delta \cdot R_i$$. Higher values mandate more uniform coverage. $$1.0$$ is infeasible in practice. |
| Min-one-per-mahalle     | `min_one`       | `solver_core.py:61`        | `True`           | Boolean       | Ensures geographic equity. Disabling allows the solver to concentrate containers in high-risk neighborhoods.                            |
| Risk-proportional       | `risk_prop`     | `solver_core.py:64`        | `True`           | Boolean       | Toggles the $$C_i \geq \delta \cdot R_i$$ constraint.                                                                                   |
| Lexicographic tolerance | $$\varepsilon$$ | `11_lexicographic.py:160`  | 0.01             | $$\geq 0$$    | Slack permitted in Stage 2 for the Z-keep constraint. Larger values relax the Stage-1 optimum preservation.                             |
| AUGMECON2 $$\rho$$      | $$\rho$$        | `13_eps_constraint.py:126` | $$10^{-5}$$      | $$(0, 0.01)$$ | Surplus variable coefficient. Must be small enough not to distort the primary objectives.                                               |
| Epsilon sweep range     | —               | `13_eps_constraint.py:108` | $$[0.80, 1.20]$$ | User-defined  | The $$\varepsilon$$ grid boundaries for the Pareto front. Should span from infeasible to over-constrained.                              |

#### 3.1.5. MCDM Method Parameters

| Parameter             | Variable    | Location               | Default                                 | Range              | Effect                                                                                                             |
| --------------------- | ----------- | ---------------------- | --------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------ |
| MCDM method           | —           | `05_ip.py:105`         | All (TOPSIS, PROMETHEE, VIKOR, ELECTRE) | Any subset         | Controls which quality vectors are used.                                                                           |
| AHP scenario focus    | —           | `05_ip.py:104`         | All three                               | Any subset         | Controls which weight scenarios are used.                                                                          |
| TOPSIS normalization  | `norm_type` | `03a_topsis.py:54--66` | MinMax (preferred)                      | `{"L2", "MinMax"}` | $$L_2$$ preserves distribution shape; MinMax preserves amplified-score discriminability.                           |
| PROMETHEE q-fraction  | `q_frac`    | `03b_promethee.py:40`  | 0.20                                    | $$(0, 1]$$         | V-shape threshold as fraction of criterion range. Larger values create fewer strict preferences.                   |
| VIKOR strategy weight | $$v$$       | `03c_vikor.py:22`      | 0.50                                    | $$[0, 1]$$         | $$v=0.5$$ balances group utility ($$S$$) and individual regret ($$R$$). $$v>0.5$$ favors majority; $$v<0.5$$ veto. |

#### 3.1.6. Solver and Orchestration Parameters

| Parameter        | Variable     | Location                | Default                      | Range                | Effect                                                                    |
| ---------------- | ------------ | ----------------------- | ---------------------------- | -------------------- | ------------------------------------------------------------------------- |
| Solver selection | —            | `solver_core.py:14--22` | HiGHS (auto-fallback to CBC) | `{HiGHS, CBC, GLPK}` | HiGHS is ~2× faster on this problem size.                                 |
| Time limit       | `time_limit` | `solver_core.py:14`     | 30 s                         | $$\geq 1$$           | Safety timeout. All solves complete in <100 ms; 30 s is a generous guard. |
| Solver verbosity | `msg`        | `solver_core.py:14`     | 0 (silent)                   | `{0, 1}`             | `1` enables solver output for debugging.                                  |

### 3.2. Parameters by Solution-Phase Dependencies

The parameters form a **hierarchical dependency graph**:

```
Level 0 (Data):  raw spreadsheets, GeoJSON shapefiles
                   ↓
Level 1 (Pre-processing):  sigma_mode, truncation_threshold, core_distance
                   ↓
Level 2 (Weighting):  AHP pairwise matrices, BWM BO/OW vectors, entropy toggle
                   ↓
Level 3 (MCDM):  TOPSIS norm_type, PROMETHEE q_frac, VIKOR v
                   ↓
Level 4 (Optimization):  K_TOTAL, beta, weight_type, KEPT_MEVCUT, FIXED_ADAY,
                         coverage_threshold, equity_alpha, epsilon range
                   ↓
Level 5 (Post-processing):  Gini computation, visualization parameters
```

**Key insight:** Changing any Level-1 parameter (e.g., switching sigma from `800` to `Adaptive`) **invalidates all downstream results**, because it changes the fuzzy coverage matrix $$\mu_{ji}$$ that feeds into the optimization. The system's caching mechanism (`cache/` directory) mitigates recomputation costs for repeated parameter combinations.

### 3.3. Sensitivity Analysis Framework

The `src/sensitivity.py` module provides a systematic sensitivity analysis infrastructure with three analysis modes:

#### 3.3.1. Beta Sensitivity (`run_beta_sensitivity` — `sensitivity.py:32--103`)

Sweeps $$\beta \in \{0.0, 0.1, \ldots, 1.0\}$$ at fixed $$K$$, $$\sigma$$, and weight type. Produces a dual-panel figure:

- **Left panel:** $$\beta$$ vs. RxC (total coverage utility). As $$\beta$$ increases and site quality receives more weight, RxC tends to **decrease slightly**, since the model is willing to sacrifice marginal coverage to select higher-quality sites.
- **Right panel:** $$\beta$$ vs. minimum and average neighborhood coverage. This reveals whether the quality incentive comes at an equity cost.

#### 3.3.2. Budget Sensitivity (`run_k_sensitivity` — `sensitivity.py:105--172`)

Sweeps $$K_{\text{total}} \in \{8, 12, 16, 20, 24, 28, 32\}$$ at fixed $$\beta$$, $$\sigma$$, and weight type. This quantifies the **marginal return on container investment**:

- **Left panel:** $$K$$ vs. RxC. Typically exhibits concave diminishing returns—the first 8 containers add the most coverage; each additional container contributes less.
- **Right panel:** $$K$$ vs. min/avg coverage. Reveals at what budget level the minimum-coverage constraint becomes binding.

#### 3.3.3. Full Grid Sweep (`generate_full_grid` — `sensitivity.py:174--224`)

Exhaustively sweeps all $$(K, \beta)$$ pairs in the Cartesian product $$\{8, 12, \ldots, 32\} \times \{0.0, 0.1, \ldots, 1.0\}$$ ($$7 \times 11 = 77$$ solves). Exports a complete grid to `results/models/sensitivity_grid_{weight_type}.xlsx`. This enables:

1. **Contour analysis:** Identifying the $$(K, \beta)$$ frontier at which specific coverage targets become achievable.
2. **Tradeoff surface visualization:** 3D or contour plots of the RxC response surface over the $$(K, \beta)$$ parameter space.
3. **Robustness assessment:** Sensitivity of the optimal solution (site selection overlap, objective stability) to parameter perturbations.

#### 3.3.4. Sigma Calibration (`12_sigma_grid.py`, `12b_sigma_calibration.py`)

These modules systematically explore the effect of the fuzzy coverage sigma parameter on solution quality and stability, providing empirical justification for the chosen default value (800 m for fixed mode, adaptive $$[400, 1200]\text{ m}$$ for adaptive mode).

---

## 4. Literature Review & Academic References

### 4.1. Facility Location Theory

The Sultanbeyli container optimization problem is fundamentally a **discrete facility location problem** (FLP). The classical taxonomy of FLPs (Daskin, 2013; Church and Murray, 2018) classifies location models along three dimensions: (1) the objective function (covering, median, or center), (2) the decision space (discrete vs. continuous), and (3) the temporal dimension (static vs. dynamic). The present system integrates two classical families:

**The Maximal Covering Location Problem (MCLP)** (Church and ReVelle, 1974) provides the foundational framework for the coverage-maximization objective. The classical MCLP maximizes the population covered within a fixed service radius $$S$$, given a budget of $$p$$ facilities:

$$\max \sum_i w_i Y_i \quad \text{s.t.} \quad \sum_{j \in N_i} X_j \geq Y_i \quad \forall i, \quad \sum_j X_j = p$$

where $$N_i = \{j : d_{ji} \leq S\}$$. The Sultanbeyli system generalizes this in two critical ways: (1) the binary covering indicator $$a_{ji} \in \{0, 1\}$$ is replaced by a continuous fuzzy membership $$\mu_{ji} \in [0, 1]$$, and (2) the objective function incorporates both risk-weighted coverage and site quality.

**The Location Set Covering Problem (LSCP)** (Toregas et al., 1971) provides the lower-bound reference: what is the minimum number of facilities to cover all demand? The system's `08_lscp.py` implements this directly as a benchmark.

**The $$p$$-Median Problem** (Hakimi, 1964; ReVelle and Swain, 1970), which minimizes the total (or average) weighted distance from demand points to facilities, is implicitly represented through the Gaussian distance-decay function: minimizing distance corresponds to maximizing $$\mu_{ji}$$.

The integration of these models into a unified framework reflects the **hierarchical facility location** paradigm (Sahin and Süral, 2007), where different service levels (core distance, adaptive sigma) correspond to different tiers of coverage intensity.

### 4.2. Multi-Criteria Decision Making (MCDM)

The site evaluation component draws on four well-established MCDM methods, each with distinct theoretical properties:

**AHP** (Saaty, 1980; 2008) remains the most widely adopted criteria-weighting method in engineering applications due to its intuitive pairwise comparison structure and built-in consistency verification ($$\text{CR} < 0.10$$). The implementation in `02_ahp_weights.py` follows Saaty's eigenvalue method precisely, including the Random Index (RI) lookup table for $$n = 4$$. The combination with entropy weights (Shannon, 1948; Zeleny, 1982) follows Hwang and Yoon's (1981) hybrid approach, producing weights that balance subjective expert judgment with objective data dispersion.

**TOPSIS** (Hwang and Yoon, 1981; Behzadian et al., 2012) is particularly suited to this application because the "closeness coefficient" $$CC_j \in [0, 1]$$ naturally maps to the $$q_j$$ quality score without additional transformation. The dual normalization ($$L_2$$ vs. Min-Max) reflects an ongoing methodological debate: $$L_2$$ (vector) normalization is the traditional TOPSIS standard, but can compress the distribution for amplified criteria; Min-Max normalization preserves the discriminability of the power-transformed scores (Chakraborty and Yeh, 2009).

**PROMETHEE II** (Brans and Vincke, 1985; Brans et al., 1986; Behzadian et al., 2010) with a Type V (V-shape) linear preference function avoids the rank-reversal problem that afflicts AHP and TOPSIS when new alternatives are added. The net flow $$\phi(j)$$ provides a complete ranking that is transitive and insensitive to the addition of dominated alternatives.

**VIKOR** (Opricovic and Tzeng, 2004; 2007) is specifically designed for compromise ranking in problems with conflicting criteria—a defining characteristic of this application, where population density and earthquake risk may point to different neighborhoods. The strategy weight $$v = 0.5$$ reflects the standard "consensus" compromise.

**ELECTRE** (Roy, 1968; 1991; Figueira et al., 2005) is the foundational outranking method. The implementation's net concordance flow variant simplifies the classical binary outranking graph while preserving ELECTRE's core insight: concordance (the weight of criteria supporting $$i \succcurlyeq k$$) and discordance (the magnitude of the largest criterion opposing $$i \succcurlyeq k$$) should be treated asymmetrically.

**BWM** (Rezaei, 2015; 2016) provides a more structured alternative to AHP, requiring only $$2n - 3$$ pairwise comparisons (rather than $$n(n-1)/2$$) while producing more consistent weights. Its inclusion as a robustness check strengthens the academic rigor.

For comprehensive surveys of MCDM applications in facility location, see Farahani et al. (2010) and Malczewski and Rinner (2015).

### 4.3. Fuzzy Set Theory in Spatial Analysis

The Gaussian fuzzy membership function represents a methodological contribution at the intersection of facility location and fuzzy set theory.

**Fuzzy facility location** extends classical covering by replacing binary membership $$a_{ji} \in \{0, 1\}$$ with a membership function $$\mu(d) : \mathbb{R}^+ \to [0, 1]$$ (Zimmermann, 1996; Kahraman et al., 2007). The choice of a **Gaussian** (radial basis) function specifically—rather than the more common triangular or trapezoidal fuzzy numbers—is justified by its smooth differentiability and its natural interpretation: service quality decays following a normal (bell-shaped) degradation curve centered at the facility, with the decay rate controlled by $$\sigma$$.

The **fuzzy MCLP** formulation (Daskin et al., 2013; Baskent and Jordan, 2002) generalizes the MCLP to accept fuzzy coverage parameters. The Sultanbeyli system goes further by making the fuzziness parameter ($$\sigma_i$$) **endogenous and spatially adaptive**—dense neighborhoods receive narrow Gaussians, sparse neighborhoods receive wide Gaussians. This population-sensitivity heuristic, while novel in its specific implementation, draws on the **spatially adaptive kernel density estimation** literature (Brunsdon, 1995; Fotheringham et al., 2002) and the concept of **geographically weighted models**.

The **two-tier architecture** (core distance of 300 m with Gaussian decay beyond) is related to the **ring-based coverage** models used in telecommunications (Amaldi et al., 2008) and to the **gradual covering** location problem (Berman et al., 2003; Berman and Krass, 2002), where coverage transitions through a piecewise linear function rather than a step function. The flat-topped Gaussian generalizes this to a smooth ($$C^\infty$$) transition.

### 4.4. Multi-Objective and Compromise Programming

The system employs a comprehensive suite of multi-objective optimization techniques:

**Weighted sum method** (Cohon, 1978; Marler and Arora, 2010): The $$\beta$$-parametric objective $$\max \sum R_i C_i + \beta \sum q_j X_j$$ scalarizes two objectives into one. Its limitation—it can only find supported (convex-hull) Pareto points—is mitigated by the $$\varepsilon$$-constraint method.

**$$\varepsilon$$-Constraint method** (Haimes et al., 1971; Chankong and Haimes, 1983): Transforming one objective (minimum coverage) into a constraint while optimizing the other (total coverage) guarantees Pareto optimality and can discover unsupported (concave-region) points unreachable by the weighted sum method. The augmented variant (AUGMECON2; Mavrotas, 2009; Mavrotas and Florios, 2013) used in `13_eps_constraint.py` ensures the generated points are Pareto-efficient rather than weakly efficient.

**Lexicographic optimization** (Fishburn, 1974): The two-stage solve—first maximize RxC, then maximize $$\min_i C_i$$ subject to $$\text{RxC} \geq \text{RxC}^* - \varepsilon$$—implements a strict priority ordering where equity is secondary but not entirely sacrificed. This is the **lexicographic maximin** (or _Rawlsian_) criterion applied to facility location.

**Compromise programming** (Zeleny, 1973; 1982): The $$L_1$$, $$L_2$$, and $$L_\infty$$ distance metrics from the utopia point operationalize different equity-efficiency compromise philosophies. The $$L_1$$ (Manhattan) norm represents additive compromise (each objective's deviation contributes linearly); the $$L_2$$ (Euclidean) norm penalizes large deviations more heavily; the $$L_\infty$$ (Chebyshev) norm minimizes the worst-case deviation, aligning with the Rawlsian maximin principle.

**Gini coefficient analysis** (Gini, 1912; Sen, 1973): Post-hoc quantification of spatial inequality. While originally developed for income distribution (Atkinson, 1970), the Gini has been adapted to spatial equity contexts in public facility location (Talen and Anselin, 1998; Tsou et al., 2005) and health service accessibility (McGrail and Humphreys, 2009). In the Sultanbeyli context, it provides a single-number summary of how evenly coverage is distributed across neighborhoods.

### 4.5. Disaster and Humanitarian Logistics

The application domain—pre-positioning disaster response assets—connects to a growing body of Operations Research literature on humanitarian logistics:

**Pre-positioning of emergency supplies** (Rawls and Turnquist, 2010; 2012; Balcik and Beamon, 2008; Duran et al., 2011) addresses the strategic decision of where to store relief items before a disaster strikes. The Sultanbeyli problem extends this by explicitly incorporating site-level quality assessment (MCDM) and fuzzy (rather than binary) coverage.

**Facility location under disruption risk** (Snyder and Daskin, 2005; Cui et al., 2010) considers the possibility that facilities themselves may become unavailable. The road-access probability parameters $$P_j$$ and $$Q_i$$ in the Sultanbeyli model (Scenario B) operationalize this: $$Q_i$$ captures neighborhood-level road closure, and $$P_j$$ captures site-level access failure.

**Equity in humanitarian logistics** (Holguín-Veras et al., 2013; Gutjahr and Nolz, 2016; Balcik et al., 2019) emphasizes that disaster response is inherently an equity-driven activity—the objective is to minimize suffering, not cost. The multiple equity mechanisms in the Sultanbeyli system (min-one-per-neighborhood constraint, min-coverage maximization in lexicographic Stage 2, Gini post-hoc inequality analysis, $$\varepsilon$$-constraint equity-efficiency Pareto front) reflect this philosophy.

**Multi-criteria humanitarian facility location** (Roh et al., 2015; Trivedi and Singh, 2017) has been identified as a critical research gap: most humanitarian logistics models rely on single-criterion (distance or cost) optimization. The Sultanbeyli system's integration of AHP-weighted MCDM with MILP facility location addresses this gap directly.

**Istanbul earthquake preparedness** specifically has been studied extensively following the 1999 Marmara earthquake (Erdik et al., 2003; AFAD, 2014; IBB-KRDAE, 2020). The Sultanbeyli district, with its dense informal settlements and high proportion of vulnerable populations, has been identified as a priority intervention zone in multiple municipal and national risk assessments. The IBB-KRDAE $$M_w = 7.5$$ scenario (source document: `docs/Sultanbeyli Deprem raporu IBB.pdf`) provides the seismological basis for the earthquake risk scores used in criteria $$C_2$$ and the neighborhood risk weights $$R_i$$.

---

## References

1. Amaldi, E., Capone, A., & Malucelli, F. (2008). Radio planning and coverage optimization of 3G cellular networks. *Wireless Networks*, 14(4), 435--447.
2. Atkinson, A. B. (1970). On the measurement of inequality. *Journal of Economic Theory*, 2(3), 244--263.
3. Balcik, B., & Beamon, B. M. (2008). Facility location in humanitarian relief. *International Journal of Logistics Research and Applications*, 11(2), 101--121.
4. Balcik, B., Silvestri, S., Rancourt, M. È., & Laporte, G. (2019). Collaborative prepositioning network design for regional disaster response. *Production and Operations Management*, 28(10), 2431--2455.
5. Baskent, E. Z., & Jordan, G. A. (2002). Forest landscape management modeling using simulated annealing. *Forest Ecology and Management*, 165(1--3), 29--45.
6. Behzadian, M., Kazemzadeh, R. B., Albadvi, A., & Aghdasi, M. (2010). PROMETHEE: A comprehensive literature review on methodologies and applications. *European Journal of Operational Research*, 200(1), 198--215.
7. Behzadian, M., Otaghsara, S. K., Yazdani, M., & Ignatius, J. (2012). A state-of-the-art survey of TOPSIS applications. *Expert Systems with Applications*, 39(17), 13051--13069.
8. Berman, O., & Krass, D. (2002). The generalized maximal covering location problem. *Computers & Operations Research*, 29(6), 563--581.
9. Berman, O., Krass, D., & Drezner, Z. (2003). The gradual covering decay location problem on a network. *European Journal of Operational Research*, 151(3), 474--480.
10. Brans, J. P., & Vincke, P. (1985). A preference ranking organisation method: The PROMETHEE method for MCDM. *Management Science*, 31(6), 647--656.
11. Brans, J. P., Vincke, P., & Mareschal, B. (1986). How to select and how to rank projects: The PROMETHEE method. *European Journal of Operational Research*, 24(2), 228--238.
12. Brunsdon, C. (1995). Estimating probability surfaces for geographical point data: An adaptive kernel algorithm. *Computers & Geosciences*, 21(7), 877--894.
13. Chakraborty, S., & Yeh, C. H. (2009). A simulation comparison of normalization procedures for TOPSIS. *Proceedings of the International Conference on Computers and Industrial Engineering*, 1815--1820.
14. Chankong, V., & Haimes, Y. Y. (1983). *Multiobjective Decision Making: Theory and Methodology*. North-Holland.
15. Church, R. L., & Murray, A. T. (2018). *Location Covering Models: History, Applications and Advancements*. Springer.
16. Church, R. L., & ReVelle, C. S. (1974). The maximal covering location problem. *Papers of the Regional Science Association*, 32(1), 101--118.
17. Cohon, J. L. (1978). *Multiobjective Programming and Planning*. Academic Press.
18. Cui, T., Ouyang, Y., & Shen, Z. J. M. (2010). Reliable facility location design under the risk of disruptions. *Operations Research*, 58(4), 998--1011.
19. Daskin, M. S. (2013). *Network and Discrete Location: Models, Algorithms, and Applications* (2nd ed.). Wiley.
20. Daskin, M. S., Snyder, L. V., & Berger, R. T. (2013). Facility location in supply chain design. In *Logistics Systems: Design and Optimization* (pp. 39--65). Springer.
21. Duran, S., Gutierrez, M. A., & Keskinocak, P. (2011). Pre-positioning of emergency items for CARE International. *Interfaces*, 41(3), 223--237.
22. Erdik, M., Aydinoglu, N., Fahjan, Y., Sesetyan, K., Demircioglu, M., Siyahi, B., ... & Yuzugullu, O. (2003). Earthquake risk assessment for Istanbul metropolitan area. *Earthquake Engineering and Engineering Vibration*, 2(1), 1--23.
23. Farahani, R. Z., SteadieSeifi, M., & Asgari, N. (2010). Multiple criteria facility location problems: A survey. *Applied Mathematical Modelling*, 34(7), 1689--1709.
24. Figueira, J., Mousseau, V., & Roy, B. (2005). ELECTRE methods. In *Multiple Criteria Decision Analysis: State of the Art Surveys* (pp. 133--162). Springer.
25. Fishburn, P. C. (1974). Lexicographic orders, utilities and decision rules: A survey. *Management Science*, 20(11), 1442--1471.
26. Fotheringham, A. S., Brunsdon, C., & Charlton, M. (2002). *Geographically Weighted Regression: The Analysis of Spatially Varying Relationships*. Wiley.
27. Gini, C. (1912). *Variabilità e Mutabilità*. Tipografia di Paolo Cuppini.
28. Gutjahr, W. J., & Nolz, P. C. (2016). Multicriteria optimization in humanitarian aid. *European Journal of Operational Research*, 252(2), 351--366.
29. Haimes, Y. Y., Lasdon, L. S., & Wismer, D. A. (1971). On a bicriterion formulation of the problems of integrated system identification and system optimization. *IEEE Transactions on Systems, Man, and Cybernetics*, 1(3), 296--297.
30. Hakimi, S. L. (1964). Optimum locations of switching centers and the absolute centers and medians of a graph. *Operations Research*, 12(3), 450--459.
31. Holguín-Veras, J., Pérez, N., Jaller, M., Van Wassenhove, L. N., & Aros-Vera, F. (2013). On the appropriate objective function for post-disaster humanitarian logistics models. *Journal of Operations Management*, 31(5), 262--280.
32. Huangfu, Q., & Hall, J. A. J. (2018). Parallelizing the dual revised simplex method. *Mathematical Programming Computation*, 10(1), 119--142.
33. Hwang, C. L., & Yoon, K. (1981). *Multiple Attribute Decision Making: Methods and Applications*. Springer.
34. Kahraman, C., Ruan, D., & Doğan, İ. (2003). Fuzzy group decision-making for facility location selection. *Information Sciences*, 157, 135--153.
35. Malczewski, J., & Rinner, C. (2015). *Multicriteria Decision Analysis in Geographic Information Science*. Springer.
36. Marler, R. T., & Arora, J. S. (2010). The weighted sum method for multi-objective optimization: New insights. *Structural and Multidisciplinary Optimization*, 41(6), 853--862.
37. Mavrotas, G. (2009). Effective implementation of the $$\varepsilon$$-constraint method in multi-objective mathematical programming problems. *Applied Mathematics and Computation*, 213(2), 455--465.
38. Mavrotas, G., & Florios, K. (2013). An improved version of the augmented $$\varepsilon$$-constraint method (AUGMECON2) for finding the exact Pareto set in multi-objective integer programming problems. *Applied Mathematics and Computation*, 219(18), 9652--9669.
39. McGrail, M. R., & Humphreys, J. S. (2009). Measuring spatial accessibility to primary care in rural areas: Improving the effectiveness of the two-step floating catchment area method. *Applied Geography*, 29(4), 533--541.
40. Opricovic, S., & Tzeng, G. H. (2004). Compromise solution by MCDM methods: A comparative analysis of VIKOR and TOPSIS. *European Journal of Operational Research*, 156(2), 445--455.
41. Opricovic, S., & Tzeng, G. H. (2007). Extended VIKOR method in comparison with outranking methods. *European Journal of Operational Research*, 178(2), 514--529.
42. Rawls, C. G., & Turnquist, M. A. (2010). Pre-positioning of emergency supplies for disaster response. *Transportation Research Part B*, 44(4), 521--534.
43. Rawls, C. G., & Turnquist, M. A. (2012). Pre-positioning and dynamic delivery planning for short-term response following a natural disaster. *Socio-Economic Planning Sciences*, 46(1), 46--54.
44. ReVelle, C. S., & Swain, R. W. (1970). Central facilities location. *Geographical Analysis*, 2(1), 30--42.
45. Rezaei, J. (2015). Best-worst multi-criteria decision-making method. *Omega*, 53, 49--57.
46. Rezaei, J. (2016). Best-worst multi-criteria decision-making method: Some properties and a linear model. *Omega*, 64, 126--130.
47. Roh, S., Pettit, S., Harris, I., & Beresford, A. (2015). The pre-positioning of warehouses at regional and local levels for a humanitarian relief organisation. *International Journal of Production Economics*, 170, 616--628.
48. Roy, B. (1968). Classement et choix en présence de points de vue multiples (la méthode ELECTRE). *RIRO*, 2(8), 57--75.
49. Roy, B. (1991). The outranking approach and the foundations of ELECTRE methods. *Theory and Decision*, 31(1), 49--73.
50. Saaty, T. L. (1980). *The Analytic Hierarchy Process*. McGraw-Hill.
51. Saaty, T. L. (2008). Decision making with the analytic hierarchy process. *International Journal of Services Sciences*, 1(1), 83--98.
52. Sahin, G., & Süral, H. (2007). A review of hierarchical facility location models. *Computers & Operations Research*, 34(8), 2310--2331.
53. Sen, A. (1973). *On Economic Inequality*. Oxford University Press.
54. Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27(3), 379--423.
55. Snyder, L. V., & Daskin, M. S. (2005). Reliability models for facility location: The expected failure cost case. *Transportation Science*, 39(3), 400--416.
56. Talen, E., & Anselin, L. (1998). Assessing spatial equity: An evaluation of measures of accessibility to public playgrounds. *Environment and Planning A*, 30(4), 595--613.
57. Toregas, C., Swain, R., ReVelle, C. S., & Bergman, L. (1971). The location of emergency service facilities. *Operations Research*, 19(6), 1363--1373.
58. Trivedi, A., & Singh, A. (2017). A hybrid multi-objective decision model for emergency shelter location-relocation projects using fuzzy TOPSIS. *International Journal of Disaster Risk Reduction*, 24, 472--485.
59. Tsou, K. W., Hung, Y. T., & Chang, Y. L. (2005). An accessibility-based integrated measure of relative spatial equity in urban public facilities. *Cities*, 22(6), 423--435.
60. Zeleny, M. (1973). Compromise programming. In *Multiple Criteria Decision Making* (pp. 262--301). University of South Carolina Press.
61. Zeleny, M. (1982). *Multiple Criteria Decision Making*. McGraw-Hill.
62. Zimmermann, H. J. (1996). *Fuzzy Set Theory and Its Applications* (3rd ed.). Kluwer.
