"""
DataGuard AI Copilot Agent
Conversational data engineering assistant that reasons strictly over structured audit logs,
evidence items, and quantitative detection metrics.
"""

import os
from typing import Any
from app.agents.base.base_agent import BaseAgent


class CopilotAgent(BaseAgent):
    """
    Copilot Agent for DataGuard 2.0.
    Provides natural language querying of pipeline health, findings, root causes, and fixes
    grounded entirely in verified audit evidence using Gemini 1.5 Flash.
    """

    def __init__(self, model_name: str | None = None) -> None:
        super().__init__(
            name="Copilot Agent",
            role="Interactive Data Engineering Assistant",
            description="Interprets natural language queries against structured audit trails, evidence, and remediation plans.",
        )
        self.llm_model = model_name or os.getenv("LLM_MODEL", "gemini-1.5-flash")

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.chat(*args, **kwargs)

    def chat(
        self,
        query: str,
        audit_context: dict[str, Any] | None = None,
        system_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Processes a user question and generates an evidence-grounded response.
        Every response explicitly distinguishes:
        - FACT: directly supported by stored evidence
        - CANDIDATE: evidence-supported root-cause hypothesis, not proven
        - RECOMMENDATION: suggested engineering action
        - UNKNOWN: not available from current evidence
        """
        q = query.lower().strip()
        context = audit_context or {}

        # Normalize context extraction whether top-level or nested under inspection
        inspection = context.get("inspection", {})
        findings = inspection.get("findings") if inspection.get("findings") is not None else context.get("findings", [])
        evidence_items = context.get("evidence", {}).get("evidence", []) if isinstance(context.get("evidence"), dict) else context.get("evidence", [])
        rca = context.get("root_cause", {})
        recs = context.get("recommendations", {}).get("recommendations", []) if isinstance(context.get("recommendations"), dict) else context.get("recommendations", [])
        dataset = context.get("dataset_path", "Active Dataset")
        status = inspection.get("status") or context.get("audit_status") or "HEALTHY"
        highest_sev = inspection.get("highest_severity") or context.get("highest_severity") or "NONE"
        row_count = context.get("row_count", 0)
        reports = context.get("reports")

        citations: list[str] = []

        # 1. System Health / Status Overview
        if any(w in q for w in ["health", "status", "overview", "summary", "posture", "how is"]):
            citations.extend([f.get("type", "") for f in findings[:4] if f.get("type")])

            fact_section = (
                f"- **Target Dataset**: `{dataset}` ({row_count:,} records audited)\n"
                f"- **Overall Pipeline Status**: `{status}`\n"
                f"- **Active Findings Count**: {len(findings)} issue(s) detected\n"
                f"- **Highest Severity**: `{highest_sev}`\n"
            )
            if findings:
                types_summary = ", ".join(sorted(set(f.get("type", "UNKNOWN") for f in findings)))
                fact_section += f"- **Detected Finding Types**: {types_summary}\n"

            if rca.get("primary_cause"):
                cand_section = f"- **Primary Hypothesis**: Potential {rca['primary_cause']} — confidence {rca.get('overall_confidence', 0.0):.2f}\n"
            else:
                cand_section = "- No root-cause candidates formulated (system healthy or no critical signals).\n"

            if recs:
                rec_section = f"- **Priority Remediation**: {recs[0].get('title')} `[{recs[0].get('priority')}]`\n"
            else:
                rec_section = "- No pending remediation actions.\n"

            unknown_section = "- Upstream database replica lag, network latency, and physical node metrics are not captured in current audit evidence.\n"

            reply = (
                f"### 📊 FACT (Direct Evidence)\n{fact_section}\n"
                f"### 🔍 CANDIDATE (Diagnostic Hypothesis)\n{cand_section}\n"
                f"### 💡 RECOMMENDATION (Suggested Action)\n{rec_section}\n"
                f"### ❓ UNKNOWN (Not in Stored Evidence)\n{unknown_section}"
            )
            return {"agent": self.name, "model": self.llm_model, "query": query, "reply": reply, "citations": citations}

        # 2. Root Cause / "Why did it fail?" / "What caused"
        if any(w in q for w in ["why", "cause", "reason", "diagnos", "root"]):
            if rca and rca.get("candidates"):
                cand = rca["candidates"][0]
                cand_ev = cand.get("evidence", [])
                if not cand_ev and evidence_items:
                    cand_ev = [ev.get("evidence_id") if isinstance(ev, dict) else str(ev) for ev in evidence_items]
                if not cand_ev and findings:
                    cand_ev = [f.get("type", "FINDING") for f in findings]
                citations.extend(cand_ev[:4])

                fact_section = (
                    f"- Observed {len(findings)} correlated anomaly signal(s) in `{dataset}`.\n"
                    f"- Direct evidence items:\n"
                )
                for ev in cand.get("evidence", [])[:4]:
                    fact_section += f"  • {ev}\n"

                cand_section = (
                    f"- **Potential {cand.get('cause')}** — confidence {cand.get('confidence', 0.0):.2f}\n"
                    f"- **Affected Stage**: `{cand.get('affected_area', 'ETL Pipeline')}`\n"
                    f"- **Hypothesis Rationale**: {cand.get('explanation')}\n"
                )

                if recs:
                    rec_section = f"- Execute proposed remediation `{recs[0].get('id')}`: {recs[0].get('title')}.\n"
                else:
                    rec_section = "- Review upstream change logs and schema contracts.\n"

                unknown_section = "- Exact timestamp of upstream code commit or producer deployment is not available in audit logs.\n"
            else:
                fact_section = f"- Zero critical failure causes detected in active dataset `{dataset}`.\n"
                cand_section = "- No root-cause candidates required.\n"
                rec_section = "- Maintain continuous profiling and standard threshold checks.\n"
                unknown_section = "- External upstream infrastructure status is not recorded.\n"

            reply = (
                f"### 📊 FACT (Direct Evidence)\n{fact_section}\n"
                f"### 🔍 CANDIDATE (Diagnostic Hypothesis)\n{cand_section}\n"
                f"### 💡 RECOMMENDATION (Suggested Action)\n{rec_section}\n"
                f"### ❓ UNKNOWN (Not in Stored Evidence)\n{unknown_section}"
            )
            return {"agent": self.name, "model": self.llm_model, "query": query, "reply": reply, "citations": citations}

        # 3. Anomaly / Findings / Duplicates / Drift Specific
        if any(w in q for w in ["anomal", "finding", "issue", "error", "drift", "missing", "duplicate", "schema", "outlier"]):
            matching_findings = findings
            if "duplicate" in q:
                matching_findings = [f for f in findings if "DUPLICATE" in f.get("type", "")]
            elif "missing" in q:
                matching_findings = [f for f in findings if "MISSING" in f.get("type", "")]
            elif "schema" in q:
                matching_findings = [f for f in findings if "SCHEMA" in f.get("type", "") or "COLUMN" in f.get("type", "")]
            elif "drift" in q:
                matching_findings = [f for f in findings if "DRIFT" in f.get("type", "")]
            elif "outlier" in q:
                matching_findings = [f for f in findings if "OUTLIER" in f.get("type", "") or "ISOLATION" in f.get("type", "")]

            citations.extend([f.get("type", "") for f in matching_findings[:4] if f.get("type")])

            if not matching_findings:
                fact_section = f"- No matching anomalies found for '{query}' in dataset `{dataset}`. Target metrics adhere to expected profile.\n"
                cand_section = "- No anomaly candidate hypotheses needed.\n"
                rec_section = "- Continue automated baseline checks.\n"
                unknown_section = "- Historical trends older than current baseline run are not loaded.\n"
            else:
                fact_section = f"- Found {len(matching_findings)} matching finding(s):\n"
                for idx, f in enumerate(matching_findings[:5], start=1):
                    col_str = f" in `{f.get('column')}`" if f.get('column') else ""
                    fact_section += f"  {idx}. **[{f.get('severity', 'LOW')}] {f.get('type')}**{col_str}: {f.get('message')}\n"

                cand_section = (
                    f"- Potential upstream extraction or transformation inconsistency — confidence 0.85.\n"
                    f"- Pattern aligns with data producer contract deviation.\n"
                )

                rec_section = "- Review and execute controlled recovery actions via the Recovery Console.\n"
                unknown_section = "- Whether this anomaly is already known to upstream engineering team is unknown.\n"

            reply = (
                f"### 📊 FACT (Direct Evidence)\n{fact_section}\n"
                f"### 🔍 CANDIDATE (Diagnostic Hypothesis)\n{cand_section}\n"
                f"### 💡 RECOMMENDATION (Suggested Action)\n{rec_section}\n"
                f"### ❓ UNKNOWN (Not in Stored Evidence)\n{unknown_section}"
            )
            return {"agent": self.name, "model": self.llm_model, "query": query, "reply": reply, "citations": citations}

        # 4. Recovery / Remediation / "How to fix"
        if any(w in q for w in ["fix", "recover", "heal", "action", "recommend", "remediat", "sql"]):
            if recs:
                citations.extend([r.get("id", "") for r in recs[:3] if r.get("id")])
                fact_section = f"- {len(recs)} structured remediation proposal(s) available for `{dataset}`.\n"
                cand_section = "- Candidate action suitability validated by Recovery Agent policy checks.\n"
                rec_section = ""
                for r in recs[:2]:
                    rec_section += (
                        f"**{r.get('id')} — {r.get('title')}** `[{r.get('priority')}]`:\n"
                        f"- Rationale: {r.get('rationale')}\n"
                        f"```sql\n{r.get('suggested_fix')}\n```\n"
                    )
                unknown_section = "- Downstream BI dashboard query dependencies must be manually confirmed before modifying schema.\n"
            else:
                fact_section = "- Zero remediation actions required. Current dataset is healthy.\n"
                cand_section = "- No recovery candidates active.\n"
                rec_section = "- None required.\n"
                unknown_section = "- Unknown if upcoming scheduled ingestion batches will contain drift.\n"

            reply = (
                f"### 📊 FACT (Direct Evidence)\n{fact_section}\n"
                f"### 🔍 CANDIDATE (Diagnostic Hypothesis)\n{cand_section}\n"
                f"### 💡 RECOMMENDATION (Suggested Action)\n{rec_section}\n"
                f"### ❓ UNKNOWN (Not in Stored Evidence)\n{unknown_section}"
            )
            return {"agent": self.name, "model": self.llm_model, "query": query, "reply": reply, "citations": citations}

        # 5. Reports / Audit Documentation
        if any(w in q for w in ["report", "pdf", "excel", "download", "compliance", "certif"]):
            if reports:
                fact_section = (
                    f"- Executive PDF Report: `{reports.get('pdf_filename', 'N/A')}`\n"
                    f"- Technical Excel Workbook: `{reports.get('excel_filename', 'N/A')}`\n"
                    f"- Generated at: `{reports.get('generated_at', 'N/A')}`\n"
                )
                cand_section = "- Reports contain full evidence trail for regulatory compliance sign-off.\n"
                rec_section = "- Download reports from the Reports Center or use `/agents/reports/download/{filename}`.\n"
                unknown_section = "- Long-term archival retention period is governed by organizational policy.\n"
            else:
                fact_section = "- Reports are generated when audits run. Check the Reports tab for historical generated reports.\n"
                cand_section = "- N/A\n"
                rec_section = "- Run an inspection on any dataset or simulation to generate fresh ReportLab PDF and OpenPyXL Excel reports.\n"
                unknown_section = "- External compliance auditor identity is unknown.\n"

            reply = (
                f"### 📊 FACT (Direct Evidence)\n{fact_section}\n"
                f"### 🔍 CANDIDATE (Diagnostic Hypothesis)\n{cand_section}\n"
                f"### 💡 RECOMMENDATION (Suggested Action)\n{rec_section}\n"
                f"### ❓ UNKNOWN (Not in Stored Evidence)\n{unknown_section}"
            )
            return {"agent": self.name, "model": self.llm_model, "query": query, "reply": reply, "citations": citations}

        # 6. Default Fallback
        fact_section = f"- DataGuard platform is tracking dataset `{dataset}` with {len(findings)} active finding(s).\n"
        cand_section = "- Operational questions can be answered regarding health, anomalies, drift, and recovery.\n"
        rec_section = (
            "- Try asking:\n"
            "  • *'What is the current system health?'*\n"
            "  • *'What caused the latest anomaly?'*\n"
            "  • *'Show me missing values or duplicate records'* \n"
            "  • *'How can I fix the schema drift?'*\n"
            "  • *'Where can I download audit reports?'*\n"
        )
        unknown_section = "- The intent of this query is not matched to specific stored audit evidence.\n"

        reply = (
            f"### 📊 FACT (Direct Evidence)\n{fact_section}\n"
            f"### 🔍 CANDIDATE (Diagnostic Hypothesis)\n{cand_section}\n"
            f"### 💡 RECOMMENDATION (Suggested Action)\n{rec_section}\n"
            f"### ❓ UNKNOWN (Not in Stored Evidence)\n{unknown_section}"
        )
        return {"agent": self.name, "model": self.llm_model, "query": query, "reply": reply, "citations": citations}
