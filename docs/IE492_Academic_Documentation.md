# IE492 — Sultanbeyli Disaster Response Container Location Optimization

## Comprehensive Academic Documentation

**Course:** IE492 — Graduation Project II  
**Institution:** Istanbul Technical University, Industrial Engineering Department  
**Date:** June 2026  

---

# Table of Contents

- [§1 Academic Problem Formulation & Mathematical Model](#1-academic-problem-formulation--mathematical-model)
  - [1.1 Problem Context and Motivation](#11-problem-context-and-motivation)
  - [1.2 Problem Classification](#12-problem-classification)
  - [1.3 Sets, Indices, and Parameters](#13-sets-indices-and-parameters)
  - [1.4 Raw Data Sources and Schema](#14-raw-data-sources-and-schema)
  - [1.5 Data Preprocessing Pipeline](#15-data-preprocessing-pipeline)
  - [1.6 AHP Weight Derivation](#16-ahp-weight-derivation)
  - [1.7 TOPSIS Multi-Criteria Ranking](#17-topsis-multi-criteria-ranking)
  - [1.8 Gaussian Fuzzy Coverage Model](#18-gaussian-fuzzy-coverage-model)
  - [1.9 Road Accessibility Factor Q_i — Deep Analysis](#19-road-accessibility-factor-q_i--deep-analysis)
  - [1.10 Main Integer Programming Model](#110-main-integer-programming-model)
  - [1.11 Alternative Optimization Models](#111-alternative-optimization-models)
  - [1.12 Equity and Fairness Metrics](#112-equity-and-fairness-metrics)
- [§2 System Architecture & Codebase Reverse-Engineering](#2-system-architecture--codebase-reverse-engineering)
  - [2.1 Architectural Overview](#21-architectural-overview)
  - [2.2 Module-by-Module Analysis](#22-module-by-module-analysis)
  - [2.3 Data Flow and File Dependencies](#23-data-flow-and-file-dependencies)
  - [2.4 Code Quality Observations](#24-code-quality-observations)
- [§3 Parameter Deep-Dive & Sensitivity Analysis Guide](#3-parameter-deep-dive--sensitivity-analysis-guide)
  - [3.1 Parameter Taxonomy](#31-parameter-taxonomy)
  - [3.2 Core Tuning Parameters](#32-core-tuning-parameters)
  - [3.3 Scenario Parameters](#33-scenario-parameters)
  - [3.4 Sensitivity Analysis Procedures](#34-sensitivity-analysis-procedures)
  - [3.5 Cross-Parameter Interaction Matrix](#35-cross-parameter-interaction-matrix)
- [§4 Literature Review & Academic References](#4-literature-review--academic-references)
  - [4.1 Facility Location Theory](#41-facility-location-theory)
  - [4.2 Fuzzy Coverage Models](#42-fuzzy-coverage-models)
  - [4.3 Multi-Criteria Decision Making in Facility Location](#43-multi-criteria-decision-making-in-facility-location)
  - [4.4 Equity in Location Analysis](#44-equity-in-location-analysis)
  - [4.5 Disaster Logistics and Emergency Facility Location](#45-disaster-logistics-and-emergency-facility-location)
  - [4.6 References](#46-references)
- [Appendix A: Notation Summary](#appendix-a-notation-summary)
- [Appendix B: Worked Numerical Examples](#appendix-b-worked-numerical-examples)

---

# §1 Academic Problem Formulation & Mathematical Model

## 1.1 Problem Context and Motivation

Istanbul, situated along the North Anatolian Fault, faces a projected earthquake of magnitude 7.0+ within the next decades. The Sultanbeyli district, located on the Asian side of Istanbul, is a densely urbanized municipality with a population exceeding 350,000 across 17 neighborhoods (*mahalleler*). The district's rapid urbanization, combined with its location on alluvial soil formations, creates elevated seismic vulnerability requiring systematic disaster preparedness infrastructure.

The problem addressed in this project is the **optimal pre-positioning of disaster response containers** — portable units containing emergency supplies (blankets, first-aid kits, food, water, communication equipment) — across the Sultanbeyli district. The municipality currently operates 12 existing containers and plans to deploy $K$ additional units across 140 candidate parcel locations identified by urban planners.

This is a **facility location optimization problem** with the following distinguishing characteristics:

1. **Hybrid intelligence:** Multi-criteria decision-making (MCDM) preprocessing feeds risk scores into mathematical optimization, combining expert judgment with algorithmic optimization.
2. **Continuous coverage:** Unlike classical binary coverage models, a Gaussian fuzzy membership function models the gradual decay of service quality with distance.
3. **Equity consideration:** The model explicitly addresses spatial equity — ensuring that no neighborhood is disproportionately underserved.
4. **Scenario robustness:** Road accessibility uncertainty is modeled through a probabilistic penalty factor $Q_i$ that reduces effective coverage when roads may be blocked.

The system produces 12 solution variants (3 MCDM methods × 3 AHP scenarios × TOPSIS MinMax normalization) and supports multiple optimization paradigms including integer programming, set covering, lexicographic max-min, ε-constraint Pareto analysis, and compromise programming.

## 1.2 Problem Classification

The Sultanbeyli container location problem is formally classified according to the taxonomy of ReVelle et al. (2008) and Daskin (1995):

| Dimension | Classification | Justification |
|-----------|---------------|---------------|
| **Spatial structure** | Discrete | 140 candidate parcel locations |
| **Temporal structure** | Static, single-period | One-time pre-positioning decision |
| **Objective** | Maximization | Risk-weighted coverage + quality bonus |
| **Coverage model** | Continuous (Gaussian fuzzy) | Smooth decay beyond 300m core radius |
| **Facility type** | Identical, capacitated | All containers are interchangeable |
| **Demand model** | Node-based | 140 parcels serve as both demand and candidate sites |
| **Candidate sites** | 140 + 12 fixed | 140 new candidates + 12 existing fixed |
| **Constraint type** | Budget, fixed, minimum | $K$ total, existing preserved, min coverage |
| **Uncertainty** | Stochastic (road accessibility) | $Q_i$ as probabilistic penalty |

This classification places the problem at the intersection of the **Maximal Covering Location Problem (MCLP)** (Church & ReVelle, 1974) and **set covering** (Toregas et al., 1971), extended with continuous fuzzy membership functions and multi-criteria preprocessing.

## 1.3 Sets, Indices, and Parameters

### 1.3.1 Sets

| Symbol | Description | Cardinality |
|--------|-------------|-------------|
| $I$ | Set of demand points (candidate parcels) | $\|I\| = 140$ |
| $J$ | Set of candidate facility locations | $\|J\| = 140$ |
| $J_F \subseteq J$ | Set of existing (fixed) facilities | $\|J_F\| = 12$ |
| $M$ | Set of neighborhoods (*mahalleler*) | $\|M\| = 17$ |
| $I_m \subseteq I$ | Set of demand points belonging to neighborhood $m$ | varies by mahalle |

### 1.3.2 Parameters

| Symbol | Description | Source / Range |
|--------|-------------|----------------|
| $K$ | Budget: number of new containers to place | User-defined (default: 5) |
| $R_i$ | MCDM risk score for parcel $i$ | TOPSIS output, $[0, 1]$ |
| $Q_i$ | Road accessibility penalty for parcel $i$ | Scenario-dependent, $[0, 1]$ |
| $P_j$ | Population weight of candidate site $j$ | Per-parcel road accessibility, $[0, 1]$ |
| $\mu_{ij}$ | Fuzzy coverage membership from site $j$ to demand $i$ | Gaussian model, $[0, 1]$ |
| $\mu_{i}^{\text{mev}}$ | Coverage from existing fixed facilities | Precomputed, $[0, 1]$ |
| $\beta$ | Quality weight parameter | $[0, 1]$, default $0.30$ |
| $q_j$ | Quality score of candidate site $j$ | Infrastructure composite |
| $\alpha$ | Equity weight parameter | Default $0.20$ |
| $\varepsilon_{\text{trunc}}$ | Fuzzy membership truncation threshold | Default $0.15$ |
| $\tau$ | Minimum neighborhood coverage threshold | Default $0.50$ |
| $\sigma_m$ | Adaptive Gaussian spread for neighborhood $m$ | $[400, 1200]$ m |
| $d_{\text{core}}$ | Core coverage radius (full membership) | $300$ m |

### 1.3.3 Derived Parameters

The road accessibility factor $Q_i$ is scenario-dependent:

$$Q_i = \begin{cases} 1 & \text{Scenario A (no road closure risk)} \\ 1 - p_i^{\text{close}} & \text{Scenario B (with road closure penalty)} \end{cases}$$

where $p_i^{\text{close}}$ is the estimated probability of road inaccessibility at parcel $i$, computed as a synthetic indicator from infrastructure features (slope, road width, building density) using a seeded random process ($\text{seed} = 42$) for reproducibility.

The adaptive Gaussian spread $\sigma_m$ is determined by neighborhood population:

$$\sigma_m = \sigma_{\min} + (\sigma_{\max} - \sigma_{\min}) \cdot \frac{P_m - P_{\min}}{P_{\max} - P_{\min}}$$

where $\sigma_{\min} = 400$ m, $\sigma_{\max} = 1200$ m, and $P_m$ is the population of neighborhood $m$.

## 1.4 Raw Data Sources and Schema

The system consumes five primary data sources, each providing essential inputs to the optimization pipeline.

### 1.4.1 Parcel Geometry (Shapefile)

**File:** `parsel_boundaries.shp`  
**Content:** Polygon geometries for 140 candidate parcels in Sultanbeyli  
**Key fields:**
- `PARSEL_ID`: Unique parcel identifier (1–140)
- `MAHALLE`: Neighborhood name (Turkish, with special characters)
- `geometry`: Shapely Polygon object

**Processing:** Centroids are computed from polygon geometry using the `centroid` attribute of Shapely objects. For non-convex polygons, the centroid may fall outside the parcel boundary, but this is acceptable for distance calculations given the scale (~100m parcel dimensions).

### 1.4.2 Population Data (Excel)

**File:** `population.xlsx`  
**Content:** Population counts per neighborhood  
**Key fields:**
- `mahalle`: Neighborhood name
- `nufus`: Population count
- `hane_ihtiyaci`: Household need metric (shelter proxy)

**Usage:** Population determines adaptive sigma ($\sigma_m$) and serves as the basis for the shelter need criterion ($C_4$).

### 1.4.3 Infrastructure Scores (Excel)

**File:** `infrastructure.xlsx`  
**Content:** Four infrastructure sub-criteria per parcel  
**Key fields:**
- `PARSEL_ID`: Parcel identifier
- `Su`: Water infrastructure score
- `Jen`: Generator/power infrastructure score
- `WC`: Sanitation infrastructure score
- `Kamera`: Surveillance/camera infrastructure score

**Composite formula:**

$$C_2 = 0.35 \cdot \text{Su} + 0.30 \cdot \text{Jen} + 0.20 \cdot \text{WC} + 0.15 \cdot \text{Kamera}$$

The weights (0.35, 0.30, 0.20, 0.15) reflect the relative importance of infrastructure types for disaster response operations, with water supply being most critical.

### 1.4.4 Seismic Damage Risk (Excel)

**File:** `seismic_risk.xlsx`  
**Content:** Geological hazard ratings per neighborhood  
**Key fields:**
- `mahalle`: Neighborhood name
- `risk_score`: Normalized damage risk value $[0, 1]$

**Usage:** The damage risk is assigned to all parcels within a neighborhood — all parcels in the same mahalle share the same $C_1$ value.

### 1.4.5 Existing Container Locations (Excel)

**File:** `existing_containers.xlsx`  
**Content:** 12 fixed disaster response container locations  
**Key fields:**
- `PARSEL_ID`: Parcel identifier of existing container
- `mevcut`: Boolean flag (always TRUE)

**Usage:** These 12 locations are fixed ($X_j = 1$ for all $j \in J_F$) and their coverage contributions are precomputed as $\mu_{i}^{\text{mev}}$.

## 1.5 Data Preprocessing Pipeline

### 1.5.1 Centroid Computation

For each parcel polygon $g_i$, the centroid $\mathbf{c}_i = (x_i, y_i)$ is computed:

$$\mathbf{c}_i = \text{centroid}(g_i) = \left(\frac{1}{|V_i|}\sum_{v \in V_i} v_x, \frac{1}{|V_i|}\sum_{v \in V_i} v_y\right)$$

where $V_i$ is the set of vertices of polygon $g_i$. Coordinates are in WGS84 (EPSG:4326) — latitude/longitude pairs. All distance calculations use the **Haversine formula** to account for Earth's curvature:

$$d_{ij} = 2R \arcsin\sqrt{\sin^2\!\left(\frac{\phi_j - \phi_i}{2}\right) + \cos\phi_i \cos\phi_j \sin^2\!\left(\frac{\lambda_j - \lambda_i}{2}\right)}$$

where $R = 6{,}371{,}000$ m is Earth's radius, $(\phi_i, \lambda_i)$ are the latitude/longitude of point $i$ in radians.

### 1.5.2 Synthetic Road Accessibility Generation

Two road accessibility parameters are generated synthetically using a deterministic random process ($\text{seed} = 42$) to ensure reproducibility:

**Per-parcel road accessibility ($p_i^{\text{access\_road}}$):**

1. For each mahalle $m$, compute a base accessibility from normalized latitude:
   $$\text{base}_m = 0.55 + 0.40 \cdot \frac{\text{lat}_m - \text{lat}_{\min}}{\text{lat}_{\max} - \text{lat}_{\min}}$$
2. Add Gaussian noise per parcel:
   $$p_i^{\text{access\_road}} = \text{clip}(\text{base}_m + \epsilon_i, \; 0.30, \; 0.99), \quad \epsilon_i \sim \mathcal{N}(0, 0.05^2)$$

This produces **per-parcel variation** — two parcels in the same mahalle have different $p_i^{\text{access\_road}}$ values.

**Per-mahalle road open probability ($p_m^{\text{road\_open}}$):**

1. Same base formula as above:
   $$\text{base}_m = 0.55 + 0.40 \cdot \frac{\text{lat}_m - \text{lat}_{\min}}{\text{lat}_{\max} - \text{lat}_{\min}}$$
2. Add Gaussian noise per mahalle:
   $$p_m^{\text{road\_open}} = \text{clip}(\text{base}_m + \epsilon_m, \; 0.40, \; 0.99), \quad \epsilon_m \sim \mathcal{N}(0, 0.05^2)$$

This produces **one value per mahalle** — all parcels in the same neighborhood share the same $p_m^{\text{road\_open}}$.

### 1.5.3 Criteria Matrix Construction

A 4-criteria decision matrix $\mathbf{D} \in \mathbb{R}^{140 \times 4}$ is constructed:

| Criterion | Symbol | Direction | Source | Scope |
|-----------|--------|-----------|--------|-------|
| Seismic damage risk | $C_1$ | Cost (minimize) | `seismic_risk.xlsx` | Per-mahalle |
| Infrastructure quality | $C_2$ | Benefit (maximize) | `infrastructure.xlsx` | Per-parcel |
| Gap distance to nearest existing | $C_3$ | Benefit (maximize) | Computed | Per-parcel |
| Shelter need | $C_4$ | Benefit (maximize) | `population.xlsx` | Per-mahalle |

**$C_1$ (Damage Risk):** Assigned from mahalle-level risk scores — all parcels in the same neighborhood receive identical $C_1$ values.

**$C_2$ (Infrastructure Quality):** The weighted composite:
$$C_2 = 0.35 \cdot \text{Su} + 0.30 \cdot \text{Jen} + 0.20 \cdot \text{WC} + 0.15 \cdot \text{Kamera}$$
This is computed per-parcel, providing fine-grained discrimination.

**$C_3$ (Gap Distance):** Haversine distance from parcel $i$ to its nearest existing container:
$$C_3^{(i)} = \min_{j \in J_F} d_{ij}$$
Larger values indicate greater need for new infrastructure.

**$C_4$ (Shelter Need):** Derived from household need metrics at the mahalle level.

### 1.5.4 Min-Max Normalization

Each criterion is normalized to $[0, 1]$ using min-max normalization:

$$C_k^{\text{norm}}(i) = \frac{C_k(i) - \min_j C_k(j)}{\max_j C_k(j) - \min_j C_k(j)}$$

For cost criteria (like $C_1$), the normalized value is inverted: $C_1^{\text{norm}} = 1 - C_1^{\text{raw\_norm}}$.

### 1.5.5 Power Transform Amplification

A power transform with exponent $\alpha = 2$ is applied to amplify score separation:

$$C_k^{\text{amp}}(i) = \left(C_k^{\text{norm}}(i)\right)^2$$

This transformation compresses low scores and amplifies high scores, enhancing discrimination between alternatives. For example, a normalized score of 0.5 becomes 0.25, while 0.9 becomes 0.81 — the gap between good and excellent alternatives widens.

## 1.6 AHP Weight Derivation

### 1.6.1 The Analytic Hierarchy Process

The Analytic Hierarchy Process (Saaty, 1980) structures the weight elicitation problem as a hierarchy: the goal (container placement) at the top, four criteria ($C_1$–$C_4$) at the intermediate level, and 140 alternatives at the bottom. Experts provide pairwise comparisons on the **Saaty 1–9 scale**:

| Intensity | Definition |
|-----------|------------|
| 1 | Equal importance |
| 3 | Moderate importance |
| 5 | Strong importance |
| 7 | Very strong importance |
| 9 | Extreme importance |
| 2, 4, 6, 8 | Intermediate values |

### 1.6.2 Pairwise Comparison Matrices

Three expert-defined pairwise comparison matrices encode different prioritization philosophies:

**Baseline Matrix ($\mathbf{A}_{\text{BL}}$):**

$$\mathbf{A}_{\text{BL}} = \begin{pmatrix} 1 & 3 & 5 & 7 \\ 1/3 & 1 & 3 & 5 \\ 1/5 & 1/3 & 1 & 3 \\ 1/7 & 1/5 & 1/3 & 1 \end{pmatrix}$$

Interpretation: Damage risk ($C_1$) is "strongly" more important than infrastructure ($C_2$), "very strongly" more important than gap distance ($C_3$), and "extremely" more important than shelter need ($C_4$).

**DamageFocused Matrix ($\mathbf{A}_{\text{DF}}$):**

$$\mathbf{A}_{\text{DF}} = \begin{pmatrix} 1 & 4 & 7 & 9 \\ 1/4 & 1 & 3 & 5 \\ 1/7 & 1/3 & 1 & 3 \\ 1/9 & 1/5 & 1/3 & 1 \end{pmatrix}$$

Interpretation: Damage risk dominates even more strongly — "extremely" more important than gap distance ($C_3$) and shelter need ($C_4$).

**InfrastructureFocused Matrix ($\mathbf{A}_{\text{IF}}$):**

$$\mathbf{A}_{\text{IF}} = \begin{pmatrix} 1 & 1 & 5 & 7 \\ 1 & 1 & 5 & 7 \\ 1/5 & 1/5 & 1 & 3 \\ 1/7 & 1/7 & 1/3 & 1 \end{pmatrix}$$

Interpretation: Damage risk ($C_1$) and infrastructure ($C_2$) are equally important, both "strongly" more important than gap distance.

### 1.6.3 Eigenvalue Method — Step-by-Step

Given a pairwise comparison matrix $\mathbf{A} \in \mathbb{R}^{n \times n}$:

**Step 1: Column normalization**

$$\bar{a}_{ij} = \frac{a_{ij}}{\sum_{k=1}^{n} a_{kj}}$$

Each column sums to 1.

**Step 2: Row averaging (weight computation)**

$$w_i = \frac{1}{n}\sum_{j=1}^{n} \bar{a}_{ij}$$

The resulting weight vector $\mathbf{w} = (w_1, w_2, w_3, w_4)^T$ is the priority vector.

**Step 3: Principal eigenvalue computation**

$$\lambda_{\max} = \frac{1}{n}\sum_{i=1}^{n} \frac{(\mathbf{A}\mathbf{w})_i}{w_i}$$

This estimates the largest eigenvalue of $\mathbf{A}$.

### 1.6.4 Consistency Ratio Validation

The Consistency Index (CI) and Consistency Ratio (CR) measure the logical coherence of expert judgments:

$$\text{CI} = \frac{\lambda_{\max} - n}{n - 1}, \quad \text{CR} = \frac{\text{CI}}{\text{RI}}$$

where RI is the Random Index for matrix size $n$:

| $n$ | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|-----|---|---|---|---|---|---|---|
| RI | 0.00 | 0.00 | 0.58 | 0.90 | 1.12 | 1.24 | 1.32 |

**Validation rule:** $\text{CR} < 0.10$ is required. For $n = 4$ criteria, $\text{RI} = 0.90$.

**Resulting weights for Baseline scenario:**

$$\mathbf{w}_{\text{BL}} = (0.5406, 0.2535, 0.1174, 0.0885)^T$$

$\lambda_{\max} \approx 4.12$, $\text{CI} \approx 0.04$, $\text{CR} \approx 0.044 < 0.10$ ✓

### 1.6.5 Entropy Weight Adjustment

To reduce subjectivity in AHP-derived weights, Shannon entropy weights are computed from the decision matrix:

$$e_k = -\frac{1}{\ln n}\sum_{i=1}^{n} p_{ik} \ln p_{ik}, \quad p_{ik} = \frac{C_k^{\text{amp}}(i)}{\sum_j C_k^{\text{amp}}(j)}$$

$$d_k = 1 - e_k \quad \text{(degree of divergence)}$$

$$w_k^{\text{entropy}} = \frac{d_k}{\sum_l d_l}$$

The **hybrid weight** combines AHP and entropy:

$$w_k^{\text{hybrid}} = \frac{w_k^{\text{AHP}} \cdot w_k^{\text{entropy}}}{\sum_l w_l^{\text{AHP}} \cdot w_l^{\text{entropy}}}$$

This ensures that criteria with both high expert priority AND high data-driven discrimination receive the highest weights.

## 1.7 TOPSIS Multi-Criteria Ranking

### 1.7.1 The TOPSIS Method

The Technique for Order of Preference by Similarity to Ideal Solution (Hwang & Yoon, 1981) ranks alternatives by their geometric distance from the ideal and anti-ideal points.

### 1.7.2 Normalization Variants

**L2 (Vector) Normalization:**

$$r_{ij} = \frac{x_{ij}}{\sqrt{\sum_{k=1}^{n} x_{kj}^2}}$$

This preserves the relative magnitude of scores and is the standard TOPSIS normalization.

**Min-Max Normalization:**

$$r_{ij} = \frac{x_{ij} - \min_k x_{kj}}{\max_k x_{kj} - \min_k x_{kj}}$$

This maps all criteria to $[0, 1]$, enabling direct comparison across criteria with different scales.

### 1.7.3 TOPSIS Algorithm — Step-by-Step

**Step 1: Normalize the decision matrix** $\mathbf{R} = [r_{ij}]_{n \times m}$

**Step 2: Compute weighted matrix** $\mathbf{V} = [v_{ij}]$ where $v_{ij} = w_j \cdot r_{ij}$

**Step 3: Determine ideal and anti-ideal points:**

$$A^+ = \{\max_i v_{ij} \mid j \in \text{benefit}\} \cup \{\min_i v_{ij} \mid j \in \text{cost}\}$$
$$A^- = \{\min_i v_{ij} \mid j \in \text{benefit}\} \cup \{\max_i v_{ij} \mid j \in \text{cost}\}$$

**Step 4: Compute separation measures:**

$$D_i^+ = \sqrt{\sum_{j=1}^{m}(v_{ij} - A_j^+)^2}, \quad D_i^- = \sqrt{\sum_{j=1}^{m}(v_{ij} - A_j^-)^2}$$

**Step 5: Compute relative closeness:**

$$CC_i = \frac{D_i^-}{D_i^+ + D_i^-} \in [0, 1]$$

Higher $CC_i$ indicates closer proximity to the ideal point.

### 1.7.4 Variant Matrix

The system produces 6 ranking variants:

| MCDM Method | AHP Scenario | Normalization | Output |
|-------------|-------------|---------------|--------|
| TOPSIS | Baseline | L2 | `CC_topsis_baseline_l2` |
| TOPSIS | Baseline | MinMax | `CC_topsis_baseline_minmax` |
| TOPSIS | DamageFocused | L2 | `CC_topsis_damagefocused_l2` |
| TOPSIS | DamageFocused | MinMax | `CC_topsis_damagefocused_minmax` |
| TOPSIS | InfrastructureFocused | L2 | `CC_topsis_infrastructurefocused_l2` |
| TOPSIS | InfrastructureFocused | MinMax | `CC_topsis_infrastructurefocused_minmax` |

The optimization model uses the **MinMax** variants as risk scores $R_i$.

## 1.8 Gaussian Fuzzy Coverage Model

### 1.8.1 Motivation for Continuous Coverage

Classical covering models use binary coverage: $a_{ij} = 1$ if $d_{ij} \leq S$ (service radius), and $a_{ij} = 0$ otherwise. This creates a sharp boundary — a demand point at distance $S + 1$ receives zero coverage, while one at $S - 1$ receives full coverage. This is unrealistic for disaster response, where:

- A container 350m away still provides meaningful assistance
- The quality of service degrades gradually with distance
- Population density varies, requiring adaptive service radii

### 1.8.2 Distance Computation

Pairwise Euclidean distances are computed from parcel centroids:

$$d_{ij} = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}$$

For geographic coordinates (WGS84), the **Haversine formula** is used:

$$d_{ij} = 2R \arcsin\sqrt{\sin^2\!\left(\frac{\phi_j - \phi_i}{2}\right) + \cos\phi_i \cos\phi_j \sin^2\!\left(\frac{\lambda_j - \lambda_i}{2}\right)}$$

where $R = 6{,}371{,}000$ m.

### 1.8.3 Adaptive Sigma Computation

The Gaussian spread $\sigma_m$ adapts to neighborhood population density:

$$\sigma_m = \sigma_{\max} - \frac{P_m - P_{\min}}{P_{\max} - P_{\min}} \cdot (\sigma_{\max} - \sigma_{\min})$$

where:
- $\sigma_{\min} = 400$ m (for the most densely populated neighborhood)
- $\sigma_{\max} = 1200$ m (for the least densely populated neighborhood)
- $P_m$ is the population of neighborhood $m$

**Rationale:** Densely populated neighborhoods need tighter coverage (smaller $\sigma$) because demand is concentrated — a container close to many people should not "waste" coverage on distant areas. Sparsely populated neighborhoods need broader coverage (larger $\sigma$) because demand points are scattered.

### 1.8.4 Two-Tier Coverage Structure

The coverage membership $\mu_{ij}$ follows a two-tier structure:

$$\mu_{ij} = \begin{cases} 1 & \text{if } d_{ij} \leq d_{\text{core}} \\ \exp\!\left(-\dfrac{(d_{ij} - d_{\text{core}})^2}{2\,\sigma_m^2}\right) & \text{if } d_{ij} > d_{\text{core}} \end{cases}$$

where:
- $d_{\text{core}} = 300$ m is the core radius within which coverage is guaranteed at full strength
- $\sigma_m$ is the adaptive spread for the neighborhood containing demand point $i$

**Physical interpretation:** Within 300m, emergency responders can reach the demand point quickly regardless of obstacles. Beyond 300m, the Gaussian function models increasing uncertainty and response time.

### 1.8.5 Truncation

Memberships below the truncation threshold are set to zero:

$$\mu_{ij}^{\text{trunc}} = \begin{cases} \mu_{ij} & \text{if } \mu_{ij} \geq \varepsilon_{\text{trunc}} \\ 0 & \text{otherwise} \end{cases}$$

The threshold $\varepsilon_{\text{trunc}} = 0.15$ corresponds to a maximum effective coverage radius:

$$d_{\max} = d_{\text{core}} + \sigma_m \sqrt{-2 \ln(\varepsilon_{\text{trunc}})} = 300 + \sigma_m \cdot 1.953$$

| $\sigma_m$ (m) | $d_{\max}$ (m) |
|-----------------|----------------|
| 400 | 1,081 |
| 600 | 1,472 |
| 800 | 1,862 |
| 1,000 | 2,253 |
| 1,200 | 2,644 |

### 1.8.6 Coverage Modes

The system supports four coverage computation modes:

| Mode | Description | $\sigma$ Source |
|------|-------------|-----------------|
| **Adaptive** | Population-dependent spread | $\sigma_m$ per mahalle |
| **RoadNetwork** | Adjusted by road accessibility | $\sigma_m \cdot p_i^{\text{access\_road}}$ |
| **Fixed** | Uniform spread for all | Constant (e.g., 800m) |
| **Composite** | Two-tier with fixed parameters | 800m outer, 300m core |

### 1.8.7 Composite Coverage Expression

The total coverage at demand point $i$ aggregates contributions from all facilities:

$$C_i = Q_i \cdot \left(\mu_{i}^{\text{mev}} + \sum_{j \in J \setminus J_F} \mu_{ij}^{\text{trunc}} \cdot P_j \cdot X_j \right)$$

where:
- $\mu_{i}^{\text{mev}} = \max_{j \in J_F} \mu_{ij}$ is the best coverage from existing facilities
- $P_j$ is the per-parcel road accessibility weight
- $X_j$ is the binary decision variable for new container placement
- $Q_i$ is the road accessibility penalty (see §1.9)

## 1.9 Road Accessibility Factor Q_i — Deep Analysis

### 1.9.1 Overview and Purpose

The road accessibility factor $Q_i$ models the probability that roads leading to demand point $i$ are passable after an earthquake. In Scenario A, all roads are assumed passable ($Q_i = 1$). In Scenario B, a per-mahalle penalty reduces effective coverage, reflecting the reality that some neighborhoods may have higher road closure risk due to building density, slope, or infrastructure age.

### 1.9.2 p_road_open Generation Algorithm

The road open probability $p_m^{\text{road\_open}}$ is generated in `01_data_prep.py` (lines 132–144):

```python
# Base probability from normalized latitude
base = 0.55 + 0.40 * normalized_latitude

# Add Gaussian noise per mahalle
np.random.seed(42)
noise = np.random.normal(0, 0.05, size=n_mahalle)

# Clip to valid range
p_road_open = np.clip(base + noise, 0.40, 0.99)
```

**Step 1: Base probability from latitude.** The formula $0.55 + 0.40 \cdot \hat{\text{lat}}_m$ assigns higher road-open probability to northern neighborhoods (higher latitude), reflecting the assumption that newer urban development in the north has better infrastructure.

**Step 2: Gaussian noise.** Random noise $\epsilon_m \sim \mathcal{N}(0, 0.05^2)$ is added to each mahalle, creating variation between neighborhoods that would otherwise have identical probabilities if they share similar latitudes.

**Step 3: Clipping.** The result is clipped to $[0.40, 0.99]$ — no neighborhood is assigned zero road accessibility (some roads always exist), and none reaches perfect 1.0.

**Key characteristic:** This is a **per-mahalle parameter** — all parcels within the same neighborhood receive the same $p_m^{\text{road\_open}}$ value. Two parcels in different mahalles will generally have different values, but two parcels in the same mahalle will always have the same value.

### 1.9.3 Q_i Construction

In `04_fuzzy_coverage.py` (lines 193–212), the Q_i vector is constructed:

```python
Q_i = p_road_open[mahalle_index[i]]  # for each parcel i
```

For Scenario A: $Q_i = 1.0$ for all $i$ (no penalty).  
For Scenario B: $Q_i = p_m^{\text{road\_open}}$ where $m$ is the mahalle of parcel $i$.

The Q_i vector is saved to `results/fuzzy_coverage/Q_i_vector.xlsx` for reuse across all models.

### 1.9.4 Q_i in the Coverage Expression

In `solver_core.py` (line 40), the coverage expression is built:

```python
coverage[i] = Q_i[i] * (mu_mev_sum[i] + sum(MU_matrix[j,i] * P_j[j] * X[j] for j in candidates))
```

Mathematically:

$$C_i = Q_i \cdot \underbrace{\mu_{i}^{\text{mev}}}_{\text{existing containers}} + Q_i \cdot \underbrace{\sum_{j \in J \setminus J_F} \mu_{ij}^{\text{trunc}} \cdot P_j \cdot X_j}_{\text{new containers}}$$

**Critical observation:** $Q_i$ multiplies the **entire** coverage expression, including the contribution from existing containers. This means that in Scenario B, even the coverage from the 12 already-placed containers is reduced by the road closure probability. This models the realistic assumption that existing containers are also affected by road closures.

### 1.9.5 Mathematical Effect on the Objective Function

The main IP objective is:

$$\max \quad Z = \sum_{i \in I} R_i \cdot C_i + \beta \cdot \sum_{j \in J \setminus J_F} q_j \cdot X_j$$

Substituting the coverage expression:

$$Z = \sum_{i \in I} R_i \cdot Q_i \cdot \left(\mu_{i}^{\text{mev}} + \sum_{j} \mu_{ij}^{\text{trunc}} \cdot P_j \cdot X_j\right) + \beta \cdot \sum_{j} q_j \cdot X_j$$

Expanding:

$$Z = \underbrace{\sum_{i} R_i \cdot Q_i \cdot \mu_{i}^{\text{mev}}}_{\text{fixed (existing containers)}} + \underbrace\sum_{i} \sum_{j} R_i \cdot Q_i \cdot \mu_{ij}^{\text{trunc}} \cdot P_j \cdot X_j}_{\text{decision-dependent}} + \beta \cdot \sum_{j} q_j \cdot X_j$$

The first term is constant (existing facilities are fixed). The optimization focuses on the second and third terms. The coefficient of $X_j$ in the decision-dependent term is:

$$\text{coeff}(X_j) = \sum_{i \in I} R_i \cdot Q_i \cdot \mu_{ij}^{\text{trunc}} \cdot P_j + \beta \cdot q_j$$

**Impact of $Q_i$:** When $Q_i < 1$ (Scenario B), the effective weight $R_i \cdot Q_i$ is reduced. Demand points in neighborhoods with low road-open probability contribute less to the objective, making the optimizer prefer locations that serve demand points with higher $Q_i$ (better road accessibility).

### 1.9.6 Q_i Across All Optimization Models

The $Q_i$ factor is used identically in all optimization models:

| Model | File | Q_i Usage |
|-------|------|-----------|
| Main IP | `05_ip.py` | $C_i = Q_i \cdot (\mu_{\text{mev}} + \sum \mu \cdot P \cdot X)$ |
| LSCP | `08_lscp.py` | Same coverage expression, used in feasibility constraints |
| Lexicographic | `11_lexicographic.py` | Phase 1: same as Main IP; Phase 2: $C_i \geq t$ with Q_i in C_i |
| ε-Constraint | `13_eps_constraint.py` | $C_i - s_i = \varepsilon$ with Q_i in C_i |
| Single-Stage | `14_single_stage.py` | $C_i$ with Q_i, plus $W_i$ indicator |
| MCLP | `16_mclp.py` | Binary coverage, Q_i not directly used (different model) |

### 1.9.7 Per-Parcel vs. Per-Mahalle Distinction

The system uses **two distinct** road accessibility parameters:

| Parameter | Scope | Generation | Used As |
|-----------|-------|------------|---------|
| $p_i^{\text{access\_road}}$ | Per-parcel | Mahalle base + per-parcel Gaussian noise | Weight $P_j$ inside coverage sum |
| $p_m^{\text{road\_open}}$ | Per-mahalle | Mahalle base + per-mahalle Gaussian noise | Penalty $Q_i$ scaling entire coverage |

**$P_j$ (per-parcel):** Used as a multiplicative weight inside the coverage sum. Two parcels in the same mahalle have different $P_j$ values, reflecting parcel-level infrastructure differences.

**$Q_i$ (per-mahalle):** Used as an external multiplier on the entire coverage. All parcels in the same mahalle share the same $Q_i$, reflecting neighborhood-level road network characteristics.

### 1.9.8 Scenario Comparison

| Aspect | Scenario A | Scenario B |
|--------|------------|------------|
| $Q_i$ values | All 1.0 | $[0.40, 0.99]$ per mahalle |
| Coverage penalty | None | Up to 60% reduction |
| Existing container coverage | Full | Reduced by Q_i |
| Optimizer behavior | Pure risk-weighted | Biases toward accessible neighborhoods |
| Result interpretation | Best case (all roads open) | Realistic case (road closure risk) |

## 1.10 Main Integer Programming Model

### 1.10.1 Decision Variables

$$X_j \in \{0, 1\} \quad \forall j \in J \setminus J_F$$

where $X_j = 1$ if a new container is placed at candidate site $j$, and $0$ otherwise. For existing facilities $j \in J_F$, $X_j = 1$ is fixed.

### 1.10.2 Objective Function

$$\max \quad Z = \sum_{i \in I} R_i \cdot C_i + \beta \cdot \sum_{j \in J \setminus J_F} q_j \cdot X_j$$

**First term:** Risk-weighted total coverage. Each demand point's coverage $C_i$ is weighted by its MCDM risk score $R_i$, prioritizing high-risk areas.

**Second term:** Quality bonus. Each selected site contributes a quality score $q_j$ weighted by $\beta$, rewarding placement at well-equipped locations.

### 1.10.3 Constraints

**Budget constraint:**

$$\sum_{j \in J \setminus J_F} X_j = K$$

Exactly $K$ new containers must be placed.

**Fixed facility preservation:**

$$X_j = 1 \quad \forall j \in J_F$$

Existing containers cannot be relocated.

**Minimum one new container:**

$$\sum_{j \in J \setminus J_F} X_j \geq 1$$

At least one new container must be placed (redundant when $K \geq 1$).

**Risk-proportional allocation** (optional):

$$\sum_{j \in I_m} X_j \geq \left\lfloor K \cdot \frac{\bar{R}_m}{\sum_{m'} \bar{R}_{m'}} \right\rfloor \quad \forall m \in M$$

where $\bar{R}_m = \frac{1}{|I_m|}\sum_{i \in I_m} R_i$ is the mean risk score in neighborhood $m$. This ensures each neighborhood receives at least a proportional share of containers based on its risk level.

### 1.10.4 Complete Formulation

$$\max \quad Z = \sum_{i \in I} R_i \cdot Q_i \cdot \left(\mu_{i}^{\text{mev}} + \sum_{j \in J \setminus J_F} \mu_{ij}^{\text{trunc}} \cdot P_j \cdot X_j \right) + \beta \cdot \sum_{j \in J \setminus J_F} q_j \cdot X_j$$

subject to:

$$\sum_{j \in J \setminus J_F} X_j = K$$

$$X_j \in \{0, 1\} \quad \forall j \in J$$

This is a **binary linear program (BLP)** solvable exactly via branch-and-bound for the problem sizes encountered ($\|J\| = 140$).

### 1.10.5 Solver Infrastructure

The PuLP library interfaces with the HiGHS solver (preferred) or CBC (fallback). HiGHS is a high-performance open-source LP/MIP solver that handles the 140-variable binary problem in seconds.

### 1.10.6 Variant Execution

The main IP is executed as 12 variants:

| MCDM Method | AHP Scenario | Normalization | Output Suffix |
|-------------|-------------|---------------|---------------|
| TOPSIS | Baseline | MinMax | `topsis_baseline_minmax` |
| TOPSIS | DamageFocused | MinMax | `topsis_damagefocused_minmax` |
| TOPSIS | InfrastructureFocused | MinMax | `topsis_infrastructurefocused_minmax` |
| PROMETHEE | Baseline | — | `promethee_baseline` |
| PROMETHEE | DamageFocused | — | `promethee_damagefocused` |
| PROMETHEE | InfrastructureFocused | — | `promethee_infrastructurefocused` |
| VIKOR | Baseline | — | `vikor_baseline` |
| VIKOR | DamageFocused | — | `vikor_damagefocused` |
| VIKOR | InfrastructureFocused | — | `vikor_infrastructurefocused` |
| ELECTRE | Baseline | — | `electre_baseline` |
| ELECTRE | DamageFocused | — | `electre_damagefocused` |
| ELECTRE | InfrastructureFocused | — | `electre_infrastructurefocused` |

## 1.11 Alternative Optimization Models

### 1.11.1 Maximal Covering Location Problem — MCLP (Model 16_mclp)

The MCLP (Church & ReVelle, 1974) replaces fuzzy coverage with binary coverage:

$$\max \quad Z_{\text{MCLP}} = \sum_{i \in I} w_i \cdot Y_i$$

subject to:

$$Y_i \leq \sum_{j \in J} a_{ij} \cdot X_j + \text{mevcut}_i \quad \forall i \in I$$

$$\sum_{j \in J \setminus J_F} X_j = K$$

$$X_j \in \{0, 1\}, \quad Y_i \in \{0, 1\}$$

where $a_{ij} = \mathbb{1}[d_{ij} \leq S]$ is the binary coverage indicator with service radius $S$, $w_i$ is the weight (risk, population, or shelter need), and $\text{mevcut}_i$ is the existing coverage indicator.

**Difference from main IP:** Binary coverage creates a sharp service boundary. Demand points just inside $S$ receive full weight; those just outside receive zero. This benchmarks the value of the fuzzy approach.

### 1.11.2 Location Set Covering Problem — LSCP (Model 08_lscp)

The LSCP (Toregas et al., 1971) finds the minimum number of facilities needed to achieve universal coverage:

$$\min \quad \sum_{j \in J \setminus J_F} X_j$$

subject to:

$$C_i \geq \tau \quad \forall i \in I$$

$$X_j \in \{0, 1\}$$

The system scans $K = 1, 2, \ldots, 15$ to find the minimum $K^*$ achieving neighborhood-level coverage above $\tau = 0.50$.

**Implementation detail:** For each $K$ value, the model is solved as a feasibility problem. The first $K$ achieving all-neighborhood coverage above $\tau$ is reported as $K^*$.

### 1.11.3 Lexicographic Max-Min (Model 11_lexicographic)

A two-phase approach ensuring both efficiency and equity:

**Phase 1:** Solve the main IP to obtain optimal objective $Z^*$:

$$Z^* = \max \quad Z = \sum_{i \in I} R_i \cdot C_i + \beta \cdot \sum_{j} q_j \cdot X_j$$

**Phase 2:** Maximize the minimum coverage across demand points, subject to a tolerance on the primary objective:

$$\max \quad t$$

subject to:

$$C_i \geq t \quad \forall i \in I$$

$$Z \geq Z^* - 0.01$$

$$\sum_{j} X_j = K, \quad X_j \in \{0, 1\}$$

The tolerance $\varepsilon_{\text{opt}} = 0.01$ allows a 1% sacrifice of the primary objective for equity.

### 1.11.4 ε-Constraint Pareto Front (Model 13_eps_constraint)

Generates the Pareto frontier between total coverage and minimum coverage:

$$\max \quad Z_{\varepsilon} = \sum_{i} R_i \cdot C_i + \beta \cdot \sum_{j} q_j \cdot X_j + M \cdot \sum_{i} s_i$$

subject to:

$$C_i + s_i = \varepsilon_k \quad \forall i \in I$$

$$\sum_{j} X_j = K, \quad X_j \in \{0, 1\}, \quad s_i \geq 0$$

**AUGMECON2 method:** The parameter $\varepsilon$ is swept from $0.80$ to $1.20$ over 20 discrete points. The surplus variable $s_i$ ensures that $C_i \leq \varepsilon_k$, and the penalty $M \cdot \sum s_i$ in the objective drives the solution to the Pareto frontier by minimizing slack.

### 1.11.5 Single-Stage MILP with Equity (Model 14_single_stage)

Integrates equity directly into the objective via binary service indicators $W_i$:

$$\max \quad Z_{\text{SS}} = Z_{R \times C} + \beta \cdot Z_{\text{quality}} + \alpha \cdot \sum_{i \in I} W_i$$

subject to:

$$W_i \leq \sum_{j} a_{ij} \cdot X_j + \text{mevcut}_i \quad \forall i$$

$$W_i \in \{0, 1\}, \quad \sum_{j} X_j = K, \quad X_j \in \{0, 1\}$$

where $W_i = 1$ if demand point $i$ receives at least threshold-level service. The term $\alpha \cdot \sum W_i$ maximizes the number of served demand points.

### 1.11.6 Compromise Programming (Model 15_compromise)

Selects the best solution from the Pareto front by minimizing the $L_p$ distance to the ideal point $Z^* = (Z_1^*, Z_2^*)$:

$$\min \quad L_p = \left( \left|\frac{Z_1 - Z_1^*}{Z_1^*}\right|^p + \left|\frac{Z_2 - Z_2^*}{Z_2^*}\right|^p \right)^{1/p}$$

for $p \in \{1, 2, \infty\}$, where $Z_1$ is total RxC coverage and $Z_2$ is the minimum neighborhood coverage.

**Metric interpretation:**
- $p = 1$: Manhattan distance — minimizes average deviation
- $p = 2$: Euclidean distance — balances average and worst-case
- $p = \infty$: Chebyshev distance — minimizes maximum deviation

## 1.12 Equity and Fairness Metrics

### 1.12.1 Gini Coefficient (Model 09_gini)

Coverage inequality across neighborhoods is measured by the Gini coefficient, adapted from income inequality analysis:

**Lorenz curve construction:**
1. Compute mean coverage per neighborhood: $C_m = \frac{1}{|I_m|}\sum_{i \in I_m} C_i$
2. Sort neighborhoods by ascending coverage: $C_{(1)} \leq C_{(2)} \leq \ldots \leq C_{(M)}$
3. Compute cumulative shares: $L_k = \frac{\sum_{i=1}^{k} C_{(i)}}{\sum_{i=1}^{M} C_{(i)}}$

**Gini coefficient:**

$$G = \frac{2\sum_{k=1}^{M} k \cdot C_{(k)}}{M \sum_{k=1}^{M} C_{(k)}} - \frac{M+1}{M}$$

A perfectly equitable solution has $G = 0$ (all neighborhoods have equal coverage). A perfectly inequitable solution has $G = 1$ (one neighborhood has all coverage).

**Interpretation for disaster response:** $G < 0.20$ indicates high equity; $G > 0.40$ indicates significant inequality requiring corrective action.

---

# §2 System Architecture & Codebase Reverse-Engineering

## 2.1 Architectural Overview

The system follows a **modular pipeline architecture** where each stage produces artifacts consumed by downstream stages. The pipeline is orchestrated by `app.py`, a Streamlit web application that serves as both the user interface and the execution engine.

### 2.1.1 High-Level Data Flow

```
Raw Data (Excel/Shapefile)
        │
        ▼
┌──────────────────┐
│ 01_data_prep.py  │ ──► normalized_criteria_matrix.csv
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ 02_ahp_weights.py│ ──► ahp_weights_*.json
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ 03a_topsis.py    │ ──► topsis_scores_*.csv
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ 04_fuzzy_coverage│ ──► mu_ij matrix (pkl/csv)
└──────────────────┘
        │
        ▼
┌──────────────────────────────────────────────┐
│          Optimization Solvers                │
│  05_ip │ 08_lscp │ 11_lex │ 13_eps │ ...    │
└──────────────────────────────────────────────┘
        │
        ▼
┌──────────────────┐
│ app.py Dashboard │ ──► Maps, Charts, PDF, Excel
└──────────────────┘
```

## 2.2 Module-by-Module Analysis

### 2.2.1 `src/config.py` — Central Configuration

**Purpose:** Single source of truth for all system constants and hyperparameters.

**Key constants:**

| Constant | Value | Role |
|----------|-------|------|
| `MAHALLE_COUNT` | 15 | Expected neighborhood count |
| `COVERAGE_THRESHOLD` | 0.50 | Minimum acceptable coverage |
| `TRUNCATION_THRESHOLD` | 0.15 | Fuzzy membership cutoff |
| `DEFAULT_BETA` | 0.30 | Quality weight in objective |
| `EQUITY_ALPHA` | 0.20 | Equity weight in single-stage model |
| `EARTH_RADIUS` | 6,371,000 m | Haversine constant |

**Key functions:**
- `norm_mahalle(name)`: Turkish character normalization using `str.maketrans` for deterministic filename generation
- `get_mevcut_indices()`: Reads `mevcut_12.xlsx` to identify existing container parcel indices

**Design note:** The file uses a custom Turkish character normalization function rather than the standard `unidecode` library, ensuring deterministic filename generation across platforms.

### 2.2.2 `src/01_data_prep.py` — Data Preparation

**Purpose:** Reads 5 raw data sources, computes spatial features, and produces the normalized criteria matrix.

**Data sources consumed:**
1. Parcel geometry (shapefile) — polygon boundaries
2. Population data (Excel) — per-neighborhood census
3. Infrastructure scores (Excel) — Su, Jen, WC, Kamera per parcel
4. Seismic damage risk (Excel) — geological hazard ratings
5. Existing container locations (Excel) — 12 fixed sites

**Processing pipeline:**
1. Compute parcel centroids from polygon geometry
2. Generate synthetic road accessibility indicators ($p_i^{\text{access\_road}}$, $p_m^{\text{road\_open}}$) with $\text{seed} = 42$
3. Build 4-criteria matrix: $C_1$ (damage), $C_2$ (infra composite), $C_3$ (gap distance), $C_4$ (shelter)
4. Apply power transform: $C_k \leftarrow C_k^2$
5. Min-max normalize each criterion to $[0, 1]$

**Outputs:** `normalized_criteria_matrix.csv`, parcel centroids, neighborhood assignments.

### 2.2.3 `src/02_ahp_weights.py` — AHP Weight Computation

**Purpose:** Derives criteria weights from expert pairwise comparison matrices.

**Method:** Eigenvalue decomposition of the comparison matrix $\mathbf{A}$:

$$\mathbf{A} \mathbf{w} = \lambda_{\max} \mathbf{w}$$

where $\lambda_{\max}$ is the principal eigenvalue and $\mathbf{w}$ is the normalized eigenvector (weights).

**Implementation details:**
- Column normalization → row averaging → weight vector
- $\lambda_{\max}$ computed as mean of $(\mathbf{A}\mathbf{w})_i / w_i$
- CR validation: $\text{CR} < 0.10$ with $\text{RI} = 0.90$ for $n = 4$

**Outputs:** `ahp_weights_baseline.json`, `ahp_weights_damagefocused.json`, `ahp_weights_infrastructurefocused.json`

### 2.2.4 `src/03a_topsis.py` — TOPSIS Ranking

**Purpose:** Ranks 140 parcels using TOPSIS with AHP-Entropy hybrid weights.

**Normalization variants:**
- **L2:** $v_{ij} = x_{ij} / \sqrt{\sum_i x_{ij}^2}$
- **Min-Max:** $v_{ij} = (x_{ij} - \min_j) / (\max_j - \min_j)$

**Weight fusion:** AHP weights are combined with Shannon entropy weights:

$$w_k^{\text{hybrid}} = \frac{w_k^{\text{AHP}} \cdot w_k^{\text{entropy}}}{\sum_l w_l^{\text{AHP}} \cdot w_l^{\text{entropy}}}$$

**Outputs:** 6 TOPSIS score files (3 scenarios × 2 normalizations).

### 2.2.5 `src/04_fuzzy_coverage.py` — Gaussian Fuzzy Coverage

**Purpose:** Computes the $\mu_{ij}$ coverage matrix using the Gaussian fuzzy model.

**Algorithm:**
1. Compute pairwise Euclidean distances $d_{ij}$ from parcel centroids
2. For each demand point $i$, determine $\sigma_m$ based on neighborhood population
3. Apply two-tier membership: $\mu_{ij} = 1$ if $d_{ij} \leq 300$ m, else Gaussian decay
4. Truncate memberships below $0.15$
5. Store sparse matrix

**Coverage modes:**

| Mode | $\sigma$ | Description |
|------|----------|-------------|
| Adaptive | $400$–$1200$ m | Population-dependent spread |
| RoadNetwork | Varies | Adjusted by road accessibility |
| Fixed | Constant (e.g., 800 m) | Uniform spread |
| Composite | 800 m with 300 m core | Two-tier structure |

**Outputs:** Coverage matrix as pickle or CSV, distance matrices, Q_i vector.

### 2.2.6 `src/solver_core.py` — PuLP Solver Infrastructure

**Purpose:** Central helper functions for all optimization models.

**Key functions:**

- `get_solver()`: Returns a PuLP solver instance (HiGHS preferred, CBC fallback)
- `dict_to_matrix()`: Converts dictionary results to matrix format
- `build_base_variables_and_coverage()`: Creates binary decision variables $X_j$ and coverage expressions $C_i$
- `add_base_constraints()`: Adds budget, fixed-facility, and minimum constraints

**Solver configuration:** HiGHS is preferred for its speed on binary LPs; CBC serves as open-source fallback.

### 2.2.7 `src/05_ip.py` — Main Integer Programming Solver

**Purpose:** Solves the primary container location optimization model.

**Model:** As defined in §1.10.

**Variant matrix:** 12 runs = 3 MCDM methods × 3 AHP scenarios × TOPSIS MinMax normalization.

**Batch mode:** Supports parallel execution of all variants with configurable $\beta$.

**Outputs:** Selected parcel IDs, objective value, coverage statistics per neighborhood, solution maps.

### 2.2.8 `src/08_lscp.py` — Location Set Covering

**Purpose:** Determines the minimum budget $K^*$ needed for universal coverage.

**Algorithm:** Sequential solve for $K = 1, 2, \ldots, 15$, reporting the first $K$ achieving coverage $\geq \tau$ for all neighborhoods.

### 2.2.9 `src/09_gini.py` — Gini Coefficient Calculator

**Purpose:** Computes coverage inequality across neighborhoods using the Gini coefficient.

**Formula:** As defined in §1.12.1.

### 2.2.10 `src/11_lexicographic.py` — Lexicographic Max-Min

**Purpose:** Two-phase optimization balancing efficiency and equity.

**Phase 1:** Solve main IP for $Z^*$.  
**Phase 2:** Maximize $\min_i C_i$ subject to $Z \geq Z^* - 0.01$.

### 2.2.11 `src/13_eps_constraint.py` — ε-Constraint Pareto Front

**Purpose:** Generates the Pareto frontier between total coverage and minimum coverage.

**Method:** AUGMECON2 — sweeps $\varepsilon$ from $0.80$ to $1.20$ over 20 points, introducing surplus variables to eliminate weakly Pareto-optimal solutions.

### 2.2.12 `src/14_single_stage.py` — Single-Stage MILP

**Purpose:** Integrates equity directly into the objective function via binary service indicators.

**Model:** As defined in §1.11.5.

### 2.2.13 `src/15_compromise.py` — Compromise Programming

**Purpose:** Selects the best Pareto-optimal solution using $L_p$ distance metrics.

**Metrics:** $L_1$ (sum of deviations), $L_2$ (Euclidean), $L_\infty$ (Chebyshev).

### 2.2.14 `src/16_mclp.py` — MCLP Benchmark

**Purpose:** Classic MCLP implementation for comparison with the fuzzy model.

**Model:** As defined in §1.11.1.

### 2.2.15 `app.py` — Streamlit Dashboard

**Purpose:** Interactive web application for experiment design, job execution, and result visualization.

**Tabs:**
1. **Experiment Design:** Configure $\beta$, $K$, MCDM method, AHP scenario, coverage mode
2. **Job Queue:** Background thread execution with real-time status
3. **Solution Details:** Selected parcels, coverage maps, neighborhood statistics
4. **Multi-Comparison:** Side-by-side comparison of solution variants
5. **Sensitivity Analysis:** Parameter sweeps and tornado diagrams
6. **Neighborhood Profile:** Per-neighborhood deep-dive with infrastructure breakdown

**Technical stack:** Streamlit + PuLP + Folium (maps) + Plotly (charts) + ReportLab (PDF) + Pandas (data).

## 2.3 Data Flow and File Dependencies

```
data/raw/
  ├── parsel_boundaries.shp
  ├── population.xlsx
  ├── infrastructure.xlsx
  ├── seismic_risk.xlsx
  └── existing_containers.xlsx
        │
        ▼ 01_data_prep.py
data/processed/
  ├── normalized_criteria_matrix.csv
  ├── parcel_centroids.csv
  └── neighborhood_assignments.csv
        │
        ▼ 02_ahp_weights.py
data/weights/
  ├── ahp_weights_baseline.json
  ├── ahp_weights_damagefocused.json
  └── ahp_weights_infrastructurefocused.json
        │
        ▼ 03a_topsis.py
data/scores/
  ├── topsis_scores_baseline_minmax.csv
  ├── topsis_scores_damagefocused_minmax.csv
  └── topsis_scores_infrastructurefocused_minmax.csv
        │
        ▼ 04_fuzzy_coverage.py
data/coverage/
  ├── mu_matrix_adaptive.pkl
  ├── distance_matrix.pkl
  └── Q_i_vector.xlsx
        │
        ▼ 05_ip.py / 08_lscp.py / ...
data/results/
  ├── solution_05_ip_topsis_baseline.json
  ├── lscp_k_scan.csv
  └── pareto_front_eps.csv
```

## 2.4 Code Quality Observations

| Issue | Severity | Location |
|-------|----------|----------|
| Haversine function duplicated in 6 files | Medium | config.py, scenario_utils.py, 01_data_prep.py, 04_fuzzy_coverage.py, app.py, others |
| Deprecated seaborn API usage | Low | app.py |
| Bare `except:` clauses | Medium | Multiple modules |
| No `pyproject.toml` or dependency lockfile | Medium | Project root |
| Minimal test coverage | High | Only integration tests in `tests/` |
| `config.py` reports `MAHALLE_COUNT=15` but data has 17 | Medium | config.py vs actual data |

---

# §3 Parameter Deep-Dive & Sensitivity Analysis Guide

## 3.1 Parameter Taxonomy

Parameters are classified into three categories based on their role in the optimization:

1. **Structural parameters:** Define the problem instance (sets, distances, scores)
2. **Tuning parameters:** Control model behavior ($\beta$, $\sigma$, $\alpha$, thresholds)
3. **Scenario parameters:** Switch between modeling assumptions (AHP scenario, Q_i mode, MCDM method)

## 3.2 Core Tuning Parameters

### 3.2.1 Quality Weight $\beta$

| Property | Value |
|----------|-------|
| Symbol | $\beta$ |
| Range | $[0, 1]$ |
| Default | $0.30$ |
| Role | Balances coverage maximization ($\sum R_i C_i$) vs. site quality ($\sum q_j X_j$) |
| Effect | $\beta = 0$: pure coverage maximization; $\beta = 1$: equal weight to quality |

**Sensitivity characterization:** The objective function is linear in $\beta$, so the Pareto frontier between coverage and quality is piecewise linear. Critical values of $\beta$ correspond to breakpoints where the optimal solution changes (basis changes in the LP relaxation).

**Recommended analysis:** Sweep $\beta \in \{0, 0.1, 0.2, \ldots, 1.0\}$ and plot:
- Total RxC coverage vs. $\beta$
- Number of selected parcels at high-quality sites vs. $\beta$
- Gini coefficient vs. $\beta$

### 3.2.2 Gaussian Spread $\sigma$

| Property | Value |
|----------|-------|
| Symbol | $\sigma_m$ |
| Range | $[400, 1200]$ m (adaptive) |
| Fixed options | 400, 600, 800, 1000, 1200 m |
| Role | Controls how quickly coverage decays beyond the core radius |
| Effect | Larger $\sigma$: broader, smoother coverage; smaller $\sigma$: sharper, localized coverage |

**Sensitivity characterization:** The coverage function $\mu_{ij} = \exp(-(d_{ij}-300)^2 / 2\sigma^2)$ is nonlinear in $\sigma$. Increasing $\sigma$ increases coverage for distant demand points but may reduce the marginal value of additional facilities.

**Recommended analysis:** Fix all other parameters, vary $\sigma \in \{400, 600, 800, 1000, 1200\}$, and report:
- Total coverage $\sum C_i$
- Number of demand points with $C_i > 0.5$
- Gini coefficient
- Optimal solution composition (which parcels selected)

### 3.2.3 Equity Weight $\alpha$

| Property | Value |
|----------|-------|
| Symbol | $\alpha$ |
| Range | $[0, 1]$ |
| Default | $0.20$ |
| Role | Weight of the equity term $\sum W_i$ in the single-stage MILP |
| Effect | Higher $\alpha$: more emphasis on serving all demand points |

**Interaction with $\beta$:** The single-stage objective $Z = Z_{R \times C} + \beta \cdot Z_q + \alpha \cdot \sum W_i$ involves two competing objectives (coverage vs. equity). The $(\alpha, \beta)$ parameter space defines a 2D trade-off surface.

### 3.2.4 Truncation Threshold $\varepsilon_{\text{trunc}}$

| Property | Value |
|----------|-------|
| Symbol | $\varepsilon_{\text{trunc}}$ |
| Range | $[0, 1]$ |
| Default | $0.15$ |
| Role | Sets fuzzy memberships below this value to zero |
| Effect | Lower threshold: denser coverage matrix, more candidate connections; higher: sparser, faster solve |

**Distance correspondence:** The truncation at $\varepsilon_{\text{trunc}} = 0.15$ corresponds to a maximum effective coverage radius of approximately:

$$d_{\max} = d_{\text{core}} + \sigma_m \sqrt{-2 \ln(\varepsilon_{\text{trunc}})} \approx 300 + 1.91\,\sigma_m$$

For $\sigma_m = 800$ m: $d_{\max} \approx 1828$ m.

### 3.2.5 Coverage Threshold $\tau$

| Property | Value |
|----------|-------|
| Symbol | $\tau$ |
| Range | $[0, 1]$ |
| Default | $0.50$ |
| Role | Minimum acceptable neighborhood-level coverage in LSCP |
| Effect | Higher $\tau$: more containers needed for feasibility |

## 3.3 Scenario Parameters

### 3.3.1 AHP Scenario

Three expert-defined weight profiles shift the MCDM emphasis:

| Scenario | $w_{C_1}$ | $w_{C_2}$ | $w_{C_3}$ | $w_{C_4}$ |
|----------|-----------|-----------|-----------|-----------|
| Baseline | 0.541 | 0.254 | 0.117 | 0.088 |
| DamageFocused | 0.609 | 0.223 | 0.109 | 0.059 |
| InfrastructureFocused | 0.391 | 0.391 | 0.140 | 0.078 |

**Baseline:** Balanced weights reflecting general disaster preparedness priorities.  
**DamageFocused:** Emphasizes seismic risk — for areas with high geological vulnerability.  
**InfrastructureFocused:** Equal weight to damage and infrastructure — for areas where infrastructure quality is the bottleneck.

### 3.3.2 Road Accessibility Scenario

#### 1.9.2.1 Q_i Generation Algorithm

The road open probability $p_m^{\text{road\_open}}$ is generated in `01_data_prep.py` (lines 132–144):

```python
# Base probability from normalized latitude
base = 0.55 + 0.40 * normalized_latitude

# Add Gaussian noise per mahalle
np.random.seed(42)
noise = np.random.normal(0, 0.05, size=n_mahalle)

# Clip to valid range
p_road_open = np.clip(base + noise, 0.40, 0.99)
```

**Step 1: Base probability from latitude.** The formula $0.55 + 0.40 \cdot \hat{\text{lat}}_m$ assigns higher road-open probability to northern neighborhoods (higher latitude), reflecting the assumption that newer urban development in the north has better infrastructure.

**Step 2: Gaussian noise.** Random noise $\epsilon_m \sim \mathcal{N}(0, 0.05^2)$ is added to each mahalle, creating variation between neighborhoods that would otherwise have identical probabilities if they share similar latitudes.

**Step 3: Clipping.** The result is clipped to $[0.40, 0.99]$ — no neighborhood is assigned zero road accessibility (some roads always exist), and none reaches perfect 1.0.

**Key characteristic:** This is a **per-mahalle parameter** — all parcels within the same neighborhood receive the same $p_m^{\text{road\_open}}$ value.

#### 1.9.2.2 Q_i Construction

In `04_fuzzy_coverage.py` (lines 193–212), the Q_i vector is constructed:

For Scenario A: $Q_i = 1.0$ for all $i$ (no penalty).  
For Scenario B: $Q_i = p_m^{\text{road\_open}}$ where $m$ is the mahalle of parcel $i$.

#### 1.9.2.3 Q_i in the Coverage Expression

In `solver_core.py` (line 40):

$$C_i = Q_i \cdot \left(\mu_{i}^{\text{mev}} + \sum_{j \in J \setminus J_F} \mu_{ij}^{\text{trunc}} \cdot P_j \cdot X_j \right)$$

**Critical observation:** $Q_i$ multiplies the **entire** coverage expression, including the contribution from existing containers. This models the realistic assumption that existing containers are also affected by road closures.

#### 1.9.2.4 Mathematical Effect on the Objective

The coefficient of $X_j$ in the objective is:

$$\text{coeff}(X_j) = \sum_{i \in I} R_i \cdot Q_i \cdot \mu_{ij}^{\text{trunc}} \cdot P_j + \beta \cdot q_j$$

When $Q_i < 1$ (Scenario B), the effective weight $R_i \cdot Q_i$ is reduced. Demand points in neighborhoods with low road-open probability contribute less to the objective, making the optimizer prefer locations that serve demand points with higher $Q_i$.

#### 1.9.2.5 Q_i Across All Models

| Model | File | Q_i Usage |
|-------|------|-----------|
| Main IP | `05_ip.py` | $C_i = Q_i \cdot (\mu_{\text{mev}} + \sum \mu \cdot P \cdot X)$ |
| LSCP | `08_lscp.py` | Same coverage expression, used in feasibility constraints |
| Lexicographic | `11_lexicographic.py` | Phase 1: same as Main IP; Phase 2: $C_i \geq t$ with Q_i |
| ε-Constraint | `13_eps_constraint.py` | $C_i - s_i = \varepsilon$ with Q_i in C_i |
| Single-Stage | `14_single_stage.py` | $C_i$ with Q_i, plus $W_i$ indicator |

#### 1.9.2.6 Per-Parcel vs. Per-Mahalle Distinction

| Parameter | Scope | Generation | Used As |
|-----------|-------|------------|---------|
| $p_i^{\text{access\_road}}$ | Per-parcel | Mahalle base + per-parcel Gaussian noise | Weight $P_j$ inside coverage sum |
| $p_m^{\text{road\_open}}$ | Per-mahalle | Mahalle base + per-mahalle Gaussian noise | Penalty $Q_i$ scaling entire coverage |

#### 1.9.2.7 Scenario Comparison Table

| Aspect | Scenario A | Scenario B |
|--------|------------|------------|
| $Q_i$ values | All 1.0 | $[0.40, 0.99]$ per mahalle |
| Coverage penalty | None | Up to 60% reduction |
| Existing container coverage | Full | Reduced by Q_i |
| Optimizer behavior | Pure risk-weighted | Biases toward accessible neighborhoods |
| Result interpretation | Best case (all roads open) | Realistic case (road closure risk) |

### 3.3.3 MCDM Method

The system supports four MCDM methods, each producing different risk scores $R_i$:
- TOPSIS (primary, used in optimization)
- PROMETHEE
- VIKOR
- ELECTRE

## 3.4 Sensitivity Analysis Procedures

### 3.4.1 One-at-a-Time (OAT) Sensitivity

For parameter $\theta$ with nominal value $\theta_0$:

$$S_{\theta} = \frac{\partial Z / Z}{\partial \theta / \theta_0} = \frac{\Delta Z / Z_0}{\Delta \theta / \theta_0}$$

**Procedure:**
1. Solve with nominal parameters → $Z_0$
2. For each parameter $\theta$:
   a. Set $\theta = \theta_0 + \Delta\theta$
   b. Resolve → $Z^+$
   c. Set $\theta = \theta_0 - \Delta\theta$
   d. Resolve → $Z^-$
   e. Compute $S_\theta = \frac{(Z^+ - Z^-) / (2 Z_0)}{\Delta\theta / \theta_0}$

### 3.4.2 Tornado Diagram Construction

1. Select parameters: $\{\beta, \sigma, \alpha, \varepsilon_{\text{trunc}}, \tau\}$
2. For each parameter, define low/high range (±20% or logical bounds)
3. Solve at low and high values, holding others at nominal
4. Plot horizontal bars sorted by $|S_\theta|$

### 3.4.3 Pareto Front Analysis

The $\varepsilon$-constraint method (Model 13) generates the Pareto frontier between:
- **Objective 1:** Total risk-weighted coverage $\sum R_i C_i$
- **Objective 2:** Minimum neighborhood coverage $\min_m C_m$

**Interpretation:** Solutions on the frontier are non-dominated — improving one objective necessarily worsens the other.

### 3.4.4 Budget Sensitivity

Vary $K \in \{1, 2, \ldots, 15\}$ and track:
- Marginal coverage gain: $\Delta Z(K) = Z(K) - Z(K-1)$
- Diminishing returns curve
- Minimum $K$ for universal coverage (LSCP result)
- Gini coefficient trajectory

## 3.5 Cross-Parameter Interaction Matrix

| | $\beta$ | $\sigma$ | $\alpha$ | $\varepsilon_{\text{trunc}}$ | $\tau$ |
|---|---------|----------|----------|-------------------------------|--------|
| $\beta$ | — | Weak | Medium | Weak | None |
| $\sigma$ | Weak | — | Weak | Strong | Medium |
| $\alpha$ | Medium | Weak | — | Weak | Weak |
| $\varepsilon_{\text{trunc}}$ | Weak | Strong | Weak | — | Medium |
| $\tau$ | None | Medium | Weak | Medium | — |

**Strong interaction ($\sigma$, $\varepsilon_{\text{trunc}}$):** Both control the coverage matrix density. Changing $\sigma$ shifts the distribution of $\mu_{ij}$ values, which directly interacts with the truncation threshold.

---

# §4 Literature Review & Academic References

## 4.1 Facility Location Theory

The mathematical foundation of facility location theory was established by Weber (1909) and formalized by Hakimi (1964), who showed that optimal facility locations on a network can always be found at nodes. The covering-based approach originated with Toregas et al. (1971) for the **Location Set Covering Problem (LSCP)** and was extended by Church & ReVelle (1974) with the **Maximal Covering Location Problem (MCLP)**, which relaxes the full-coverage requirement to maximize coverage within a budget.

The $p$-median problem (ReVelle & Swain, 1970) minimizes total weighted distance, representing a different objective paradigm. Daskin (1995) provides a comprehensive unification of these models. For disaster logistics specifically, Jia et al. (2007) extended covering models to handle multiple facility types and demand uncertainty.

## 4.2 Fuzzy Coverage Models

Classical coverage models employ binary membership ($a_{ij} \in \{0, 1\}$), which fails to capture the gradual degradation of service quality with distance. Fuzzy set theory (Zadeh, 1965) provides a natural framework for continuous coverage modeling.

Bennell et al. (2011) and Murray (2013) surveyed continuous coverage functions in location analysis. The Gaussian decay function used in this system follows the "coverage by opportunities" paradigm (Drezner et al., 2004), where the probability of service decreases smoothly with distance. The two-tier structure (core + Gaussian) is analogous to the "coverage with partial backup" model of ReVelle & Hogan (1989).

Adaptive sigma based on population density connects to the **demand-density-dependent coverage** concept in Berman et al. (2009), where service capacity is allocated proportionally to local demand intensity.

## 4.3 Multi-Criteria Decision Making in Facility Location

The integration of MCDM with facility location optimization addresses the "soft" factors (risk, equity, accessibility) that pure mathematical programming cannot capture. The AHP-TOPSIS combination used here follows the established "hierarchical weighting + ranking" paradigm:

- **AHP** (Saaty, 1980): Structured pairwise comparison for weight elicitation, with consistency ratio validation ensuring rational expert judgments.
- **TOPSIS** (Hwang & Yoon, 1981): Distance-based ranking from ideal and anti-ideal points, robust to the scale of criteria.
- **Entropy weighting** (Shannon, 1948): Data-driven weight adjustment reducing subjectivity in the AHP-derived weights.

The power transform amplification ($C_k \rightarrow C_k^2$) is a form of **criteria stretching** commonly used in GIS-MCDA (Malczewski, 2006) to enhance discrimination between alternatives.

## 4.4 Equity in Location Analysis

Equity considerations in facility location have been studied extensively. The **Gini coefficient** adaptation for spatial service distribution follows the work of Marsh & Schilling (1994), who proposed various equity measures for public facility location. The lexicographic max-min approach (Rawls, 1971) ensures that the worst-off demand point is prioritized, reflecting the "maximin" fairness criterion.

The $\varepsilon$-constraint method for Pareto generation follows the AUGMECON2 framework of Mavrotas & Florios (2013), which eliminates weakly Pareto-optimal solutions through surplus variable augmentation.

Compromise programming (Zeleny, 1973) with $L_p$ metrics provides a principled way to select from the Pareto front, where $p = 1$ emphasizes average performance, $p = 2$ balances average and worst-case, and $p = \infty$ focuses on the worst-off.

## 4.5 Disaster Logistics and Emergency Facility Location

The specific application domain — earthquake preparedness in Istanbul — connects to a rich literature on disaster logistics. Jia et al. (2007) and Mete & Zabinsky (2010) addressed pre-positioning of disaster relief supplies under uncertainty. Bozorgi-Amiri et al. (2013) extended these models with robust optimization.

The Sultanbeyli case study is particularly relevant given Istanbul's seismic risk profile. Erdik et al. (2003) estimated potential earthquake losses for Istanbul, while the 1999 İzmit earthquake provided empirical validation of vulnerability models. The synthetic road closure probability ($p_i^{\text{close}}$) used in Scenario B reflects the post-earthquake accessibility analysis framework of Sohn et al. (2003).

## 4.6 References

### Primary References

Bennell, J. A., Mesgari, M. S., & Sáiz, M. E. (2011). Continuous approximations for facility location problems. In *Foundations of Location Analysis* (pp. 417–434). Springer.

Berman, O., Drezner, Z., & Krass, D. (2009). Generalized coverage: New developments in covering location models. *Computers & Operations Research*, 37(1), 59–73.

Bozorgi-Amiri, A., Jabalameli, M. S., & Mirzapour Al-e-Hashem, S. M. J. (2013). A multi-objective robust stochastic programming model for disaster relief logistics under uncertainty. *OR Spectrum*, 35(4), 905–933.

Church, R. L., & ReVelle, C. S. (1974). The maximal covering location problem. *Papers of the Regional Science Association*, 32(1), 101–118.

Daskin, M. S. (1995). *Network and Discrete Location: Models, Algorithms, and Applications*. Wiley.

Drezner, T., Drezner, Z., & Salhi, S. (2004). Solving the multiple competitive facilities location problem. *European Journal of Operational Research*, 154(1), 151–164.

Erdik, M., Aydinoglu, N., Fahjan, Y., Sesetyan, K., Demircioglu, M., Siyahi, B., ... & Biro, T. (2003). Earthquake risk assessment for Istanbul metropolitan area. *Earthquake Engineering and Engineering Vibration*, 2(1), 1–23.

Hakimi, S. L. (1964). Optimum locations of switching centers and the absolute centers and medians of a graph. *Operations Research*, 12(3), 450–459.

Hwang, C. L., & Yoon, K. (1981). *Multiple Attribute Decision Making: Methods and Applications*. Springer.

Jia, H., Ordóñez, F., & Dessouky, M. M. (2007). A modeling framework for facility location of medical services for large-scale emergencies. *IIE Transactions*, 39(1), 41–55.

Malczewski, J. (2006). GIS-based multicriteria decision analysis: A survey of the literature. *International Journal of Geographical Information Science*, 20(7), 703–726.

Marsh, M. T., & Schilling, D. A. (1994). Equity measurement in facility location analysis: A review and framework. *European Journal of Operational Research*, 74(1), 1–17.

Mavrotas, G., & Florios, K. (2013). An improved version of the augmented epsilon-constraint method (AUGMECON2) for finding the exact Pareto set in multi-objective integer programming problems. *Applied Mathematics and Computation*, 219(18), 9652–9669.

Mete, H. O., & Zabinsky, Z. B. (2010). Stochastic optimization of medical supply location and distribution in disaster management. *International Journal of Production Economics*, 126(1), 76–84.

Murray, A. T. (2013). Coverage models. In *Encyclopedia of Operations Research and Management Science* (pp. 332–339). Springer.

Rawls, J. (1971). *A Theory of Justice*. Harvard University Press.

ReVelle, C. S., & Hogan, K. (1989). The maximum reliability location problem and α-reliable p-center problem: Derivatives of the probabilistic location set covering problem. *Annals of Operations Research*, 18(1), 155–174.

ReVelle, C. S., & Swain, R. W. (1970). Central facilities location. *Geographical Analysis*, 2(1), 30–42.

Saaty, T. L. (1980). *The Analytic Hierarchy Process*. McGraw-Hill.

Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27(3), 379–423.

Sohn, J., Kim, T., Hewings, G. J. S., Lee, J. S., & Jang, S. G. (2003). Retrofit priority of transport network links under an earthquake. *Journal of Urban Planning and Development*, 129(4), 195–210.

Toregas, C., Swain, R., ReVelle, C. S., & Bergman, L. (1971). The location of emergency service facilities. *Operations Research*, 19(6), 1363–1373.

Weber, A. (1909). *Über den Standort der Industrien*. Mohr Siebeck.

Zadeh, L. A. (1965). Fuzzy sets. *Information and Control*, 8(3), 338–353.

Zeleny, M. (1973). Compromise programming. In *Multiple Criteria Decision Making* (pp. 262–301). University of South Carolina Press.

### Application-Specific References

Baray, J., & Cliquet, G. (2013). Optimizing store locations: A multi-criteria approach. *Journal of Retailing and Consumer Services*, 20(3), 305–313.

Current, J., Min, H., & Schilling, D. A. (1990). Multiobjective analysis of facility location decisions. *European Journal of Operational Research*, 49(3), 295–307.

Drezner, Z., & Hamacher, H. W. (Eds.). (2002). *Facility Location: Applications and Theory*. Springer.

Farahani, R. Z., & Hekmatfar, M. (Eds.). (2009). *Facility Location: Concepts, Models, Algorithms and Case Studies*. Springer.

Kariv, O., & Hakimi, S. L. (1979). An algorithmic approach to network location problems. *SIAM Journal on Applied Mathematics*, 37(3), 539–560.

Owen, S. H., & Daskin, M. S. (1998). Strategic facility location: A review. *European Journal of Operational Research*, 111(3), 423–447.

ReVelle, C. S., Eiselt, H. A., & Daskin, M. S. (2008). A bibliography for some fundamental problem categories in discrete location science. *European Journal of Operational Research*, 184(3), 817–848.

---

# Appendix A: Notation Summary

| Symbol | Type | Description |
|--------|------|-------------|
| $I$ | Set | Demand points (140 parcels) |
| $J$ | Set | Candidate facility sites |
| $J_F$ | Set | Existing fixed facilities (12) |
| $M$ | Set | Neighborhoods (17) |
| $K$ | Parameter | Budget (new containers) |
| $R_i$ | Parameter | MCDM risk score |
| $Q_i$ | Parameter | Road accessibility penalty |
| $P_j$ | Parameter | Population weight |
| $\mu_{ij}$ | Parameter | Fuzzy coverage membership |
| $\beta$ | Parameter | Quality weight |
| $q_j$ | Parameter | Site quality score |
| $\alpha$ | Parameter | Equity weight |
| $\sigma_m$ | Parameter | Adaptive Gaussian spread |
| $\varepsilon_{\text{trunc}}$ | Parameter | Truncation threshold |
| $\tau$ | Parameter | Coverage threshold |
| $X_j$ | Variable | Binary placement decision |
| $C_i$ | Expression | Composite coverage at demand $i$ |
| $Z$ | Expression | Objective function value |
| $G$ | Metric | Gini coefficient |

---

# Appendix B: Worked Numerical Examples

## B.1 AHP Weight Computation — Baseline Scenario

Given the Baseline pairwise comparison matrix:

$$\mathbf{A} = \begin{pmatrix} 1 & 3 & 5 & 7 \\ 1/3 & 1 & 3 & 5 \\ 1/5 & 1/3 & 1 & 3 \\ 1/7 & 1/5 & 1/3 & 1 \end{pmatrix}$$

**Step 1: Column sums**

| | Col 1 | Col 2 | Col 3 | Col 4 |
|---|-------|-------|-------|-------|
| Sum | 1.676 | 4.533 | 9.333 | 16.000 |

**Step 2: Column normalization**

$$\bar{\mathbf{A}} = \begin{pmatrix} 0.597 & 0.662 & 0.536 & 0.438 \\ 0.199 & 0.221 & 0.321 & 0.313 \\ 0.119 & 0.074 & 0.107 & 0.188 \\ 0.085 & 0.044 & 0.036 & 0.063 \end{pmatrix}$$

**Step 3: Row averaging (weights)**

$$\mathbf{w} = (0.558, 0.263, 0.122, 0.057)^T$$

**Step 4: Consistency check**

$$\mathbf{A}\mathbf{w} = (2.291, 1.089, 0.503, 0.234)^T$$

$$\lambda_{\max} = \frac{1}{4}\left(\frac{2.291}{0.558} + \frac{1.089}{0.263} + \frac{0.503}{0.122} + \frac{0.234}{0.057}\right) = 4.12$$

$$\text{CI} = \frac{4.12 - 4}{4 - 1} = 0.040, \quad \text{CR} = \frac{0.040}{0.90} = 0.044 < 0.10 \checkmark$$

## B.2 Gaussian Coverage Computation

Given:
- Demand point $i$ at coordinates $(40.85, 29.27)$
- Facility $j$ at coordinates $(40.86, 29.28)$
- $d_{ij} = 1{,}200$ m (Haversine)
- $\sigma_m = 800$ m (adaptive spread for neighborhood $m$)
- $d_{\text{core}} = 300$ m

**Coverage computation:**

$$d_{ij} = 1200 > d_{\text{core}} = 300 \implies \mu_{ij} = \exp\!\left(-\frac{(1200 - 300)^2}{2 \cdot 800^2}\right) = \exp\!\left(-\frac{810{,}000}{1{,}280{,}000}\right) = e^{-0.633} = 0.531$$

Since $0.531 > \varepsilon_{\text{trunc}} = 0.15$, the membership is kept: $\mu_{ij} = 0.531$.

## B.3 Q_i Effect on Coverage

Given:
- Demand point $i$ in a mahalle with $p_m^{\text{road\_open}} = 0.70$
- $\mu_{i}^{\text{mev}} = 0.30$ (existing container coverage)
- One new candidate $j$ with $\mu_{ij} = 0.50$, $P_j = 0.80$

**Scenario A ($Q_i = 1.0$):**

$$C_i = 1.0 \cdot (0.30 + 0.50 \cdot 0.80 \cdot X_j) = 0.30 + 0.40 \cdot X_j$$

If $X_j = 1$: $C_i = 0.70$

**Scenario B ($Q_i = 0.70$):**

$$C_i = 0.70 \cdot (0.30 + 0.50 \cdot 0.80 \cdot X_j) = 0.21 + 0.28 \cdot X_j$$

If $X_j = 1$: $C_i = 0.49$

**Impact:** The road closure penalty reduces coverage from 0.70 to 0.49 — a 30% reduction that reflects the realistic risk of road inaccessibility.
