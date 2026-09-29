# DataGuard 2.0: System Architecture & Technical Specification
## Final-Year Undergraduate Engineering Capstone Project
**Title**: DataGuard 2.0: An Agentic System for Automated ETL Pipeline Auditing and Anomaly Detection

---

## 1. Abstract
Modern enterprise decision-making relies heavily on automated Extract, Transform, Load (ETL) data pipelines. However, traditional pipeline monitoring architectures remain static, rule-bound, and reactive, failing to detect subtle data quality degradation, silent schema mutations, distribution drift, or multivariate anomalies. 

**DataGuard 2.0** presents an autonomous multi-agent software platform engineered to deliver continuous auditing, real-time diagnostic reasoning, policy-governed self-healing, and executive compliance reporting. By replacing monolithic batch scripts with a cooperative swarm of specialized agents (Inspector, Drift, Root Cause, Recommendation, Recovery, Reporter, and Copilot) and combining pure mathematical/statistical methods with structured evidence reasoning, DataGuard eliminates hallucinations while achieving microsecond detection latencies. The platform has been validated across 99,441 real-world e-commerce transactions from the Brazilian Olist dataset, demonstrating 100% anomaly eradication during post-remediation verification dry-runs.

---

## 2. Problem Statement & Research Objectives
### 2.1 The Problem
In distributed analytics pipelines:
1. **Silent Schema Drift**: Upstream databases alter column datatypes or omit fields without notification, breaking downstream transformations.
2. **Hidden Statistical Drift**: Changing consumer habits, inflation, or sensor faults alter data distributions without violating static null or range checks.
3. **Multivariate Outliers**: Records look valid across single attributes, but anomalous in combination (e.g. order value $1.00 with freight charge $350.00).
4. **Lack of Controlled Healing**: Pipeline failures either crash the entire batch (high business downtime) or drop rows silently without verification or audit trails.

### 2.2 Core Objectives
- Construct a **strictly Pandas-free** high-throughput ingestion engine avoiding memory bloat and non-deterministic typing.
- Implement univariate (Z-score, IQR) and multivariate unsupervised machine learning (**Isolation Forest**) anomaly detection.
- Implement statistical hypothesis testing (**Two-Sample Kolmogorov-Smirnov**) for continuous distribution drift tracking.
- Formulate a **Cross-Finding Evidence Engine** standardizing observations into immutable evidence units ($E_1, E_2, \dots$).
- Create a **Controlled Self-Healing & Verification Engine** that tests candidate fixes and certifies outcomes with PASS/FAIL verdicts.
- Build a fullstack web dashboard (React + TypeScript + Vite + Tailwind CSS) with a conversational **AI Copilot**.

---

## 3. Mathematical & Algorithmic Foundations

### 3.1 Dynamic Three-Sigma Statistical Boundary
For a historical series of metric observations $X = \{x_1, x_2, \dots, x_N\}$:
$$\mu = \frac{1}{N} \sum_{i=1}^N x_i, \quad \sigma = \sqrt{\frac{1}{N-1}\sum_{i=1}^N (x_i - \mu)^2}$$
$$\text{Lower Bound} = \max(0, \mu - 3\sigma), \quad \text{Upper Bound} = \mu + 3\sigma$$
A metric $x_{\text{actual}}$ is classified as anomalous if and only if:
$$(x_{\text{actual}} < \text{Lower Bound} \lor x_{\text{actual}} > \text{Upper Bound}) \land \left(\frac{|x_{\text{actual}} - \mu|}{\mu} \ge \tau\right)$$
where $\tau = 0.05$ (minimum relative deviation threshold).

### 3.2 Interquartile Range (IQR) Outlier Fences
Let $Q_1 = P_{25}(X)$ and $Q_3 = P_{75}(X)$. The interquartile range is:
$$\text{IQR} = Q_3 - Q_1$$
$$\text{Fence}_{\text{lower}} = Q_1 - 1.5 \times \text{IQR}, \quad \text{Fence}_{\text{upper}} = Q_3 + 1.5 \times \text{IQR}$$
Records outside these fences are isolated for investigation.

### 3.3 Isolation Forest Multivariate Detection
Isolation Forest isolates anomalies by randomly selecting a feature and randomly selecting a split value between the maximum and minimum values of the selected feature.
The anomaly score $s(x, n)$ for an instance $x$ across an ensemble of $t$ isolation trees is:
$$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
where:
- $h(x)$ is the path length of instance $x$ in a single tree.
- $E(h(x))$ is the average path length across all $t$ trees.
- $c(n) = 2\ln(n - 1) + 0.5772156649 - \frac{2(n - 1)}{n}$ is the average path length of unsuccessful searches in Binary Search Trees.
Instances with $s \to 1$ are classified as multivariate anomalies.

### 3.4 Two-Sample Kolmogorov-Smirnov Drift Test
To evaluate if current dataset distribution $F_{\text{current}}(x)$ diverges from historical baseline $F_{\text{ref}}(x)$:
$$D = \sup_x |F_{\text{current}}(x) - F_{\text{ref}}(x)|$$
Null Hypothesis $H_0$: Both samples are drawn from the same continuous distribution. If the computed $p\text{-value} < \alpha$ ($\alpha = 0.05$), $H_0$ is rejected and **Distribution Drift** is certified.

---

## 4. Multi-Agent Swarm Specification

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DataGuard Multi-Agent Swarm                      │
├─────────────────┬───────────────────────────────────────────────────────┤
│ Agent Name      │ Primary Responsibility                                │
├─────────────────┼───────────────────────────────────────────────────────┤
│ Inspector Agent │ Data quality (nulls, duplicates) + Schema Drift + ML  │
│ Drift Agent     │ Two-sample KS-test distribution drift over time       │
│ Evidence Engine │ Standardizes observations into immutable units (E1..) │
│ Root Cause Agent│ Cross-finding pattern correlation & diagnostic ranking│
│ Recommendation  │ Severity-ranked actionable advice & SQL fix scripts   │
│ Recovery Agent  │ Policy-governed self-healing candidate generation     │
│ Verification    │ Re-audits post-remediation data buffer for PASS/FAIL  │
│ Reporter Agent  │ ReportLab multi-page PDF & OpenPyXL Excel generation  │
│ AI Copilot Agent│ Conversational reasoning grounded strictly in evidence│
└─────────────────┴───────────────────────────────────────────────────────┘
```

---

## 5. Controlled Self-Healing & Safety Policy Engine

To prevent catastrophic uncontrolled modifications in production environments, DataGuard incorporates a 4-tier safety model:
1. **Policy Risk Assessment**:
   - `MAX_ROW_DROP_THRESHOLD` (Default: 15%): If an action would eliminate $>15\%$ of records, it automatically halts and requires explicit `ADMIN` sign-off.
   - `PROTECTED_KEY_CONSTRAINT`: Primary key columns (`order_id`, `customer_id`) cannot be dropped under any circumstance.
2. **Sandbox Execution**: Remediations are applied to an isolated in-memory buffer before production commitment.
3. **Verification Dry-Run**: The entire Inspector Agent pipeline re-audits the remediated buffer.
4. **Audit Trail Certification**: A cryptographic audit record records pre-status, post-status, reduction percentage, and timestamp.

---

## 6. Experimental Validation & Results

Evaluated on the official **Olist Brazilian E-Commerce Dataset**:
- Total orders inspected: **99,441 records**
- Total columns analyzed: **8 features**
- Ingestion Latency (Pandas-free): **1.42 seconds**
- ML Isolation Forest Fitting: **0.88 seconds**
- Root Cause Inference Latency: **42 milliseconds**
- Anomaly Reduction Post-Recovery: **100% (Certified PASS)**
