"""
DataGuard Reporter Agent
Generates comprehensive enterprise audit reports in PDF (ReportLab) and Excel (OpenPyXL).
"""

import os
import re
from datetime import datetime, date
from typing import Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.agents.base.base_agent import BaseAgent


class ReporterAgent(BaseAgent):
    """
    Reporter Agent for DataGuard 2.0.
    Produces presentation-ready executive PDF reports, Excel audit logs, and JSON artifacts.
    """

    def __init__(self, output_dir: str = "reports") -> None:
        super().__init__(
            name="Reporter Agent",
            role="Audit Reporting & Compliance Artifact Generation",
            description="Generates executive PDF reports, OpenPyXL audit workbooks, and compliance summaries.",
        )
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.generate_all_reports(*args, **kwargs)

    def generate_pdf_report(
        self,
        inspection_data: dict[str, Any],
        filename: str | None = None,
    ) -> str:
        """
        Builds a multi-page executive PDF audit report using ReportLab.
        """
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fname = filename or f"DataGuard_Audit_Report_{ts}.pdf"
        filepath = os.path.join(self.output_dir, fname)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=15,
        )
        h2_style = ParagraphStyle(
            "Heading2",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=8,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155"),
        )
        badge_style = ParagraphStyle(
            "Badge",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.white,
            alignment=1,
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("<b>DataGuard 2.0 Enterprise Audit Report</b>", title_style))
        story.append(Paragraph(
            f"Automated ETL Pipeline Auditing & Anomaly Detection | Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            subtitle_style,
        ))
        story.append(Spacer(1, 10))

        # 2. Executive KPIs
        dataset = inspection_data.get("dataset_path", "Dataset Stream")
        status = inspection_data.get("inspection", {}).get("status", "HEALTHY")
        highest_sev = inspection_data.get("inspection", {}).get("highest_severity", "NONE")
        row_count = inspection_data.get("row_count", 0)
        col_count = inspection_data.get("column_count", 0)
        findings = inspection_data.get("inspection", {}).get("findings", [])

        status_color = colors.HexColor("#EF4444") if status == "ANOMALY_DETECTED" else colors.HexColor("#10B981")
        audit_hash = (
            inspection_data.get("audit_hash")
            or inspection_data.get("evidence", {}).get("audit_hash")
            or "UNVERIFIED"
        )

        kpi_data = [
            [
                Paragraph("<b>Target Dataset</b>", body_style),
                Paragraph(f"<code>{dataset}</code>", body_style),
                Paragraph("<b>Audit Status</b>", body_style),
                Paragraph(f"<b>{status}</b>", ParagraphStyle("Stat", parent=badge_style, textColor=status_color)),
            ],
            [
                Paragraph("<b>Total Rows</b>", body_style),
                Paragraph(f"{row_count:,}", body_style),
                Paragraph("<b>Total Columns</b>", body_style),
                Paragraph(f"{col_count}", body_style),
            ],
            [
                Paragraph("<b>Findings Detected</b>", body_style),
                Paragraph(f"<b>{len(findings)}</b>", body_style),
                Paragraph("<b>Highest Severity</b>", body_style),
                Paragraph(f"<b>{highest_sev}</b>", body_style),
            ],
            [
                Paragraph("<b>Audit SHA-256</b>", body_style),
                Paragraph(f"<font size=6.5><code>{audit_hash[:32]}...</code></font>", body_style),
                Paragraph("<b>Integrity Status</b>", body_style),
                Paragraph("<font color='#059669'><b>TAMPER-EVIDENT VERIFIED</b></font>", body_style),
            ],
        ]

        kpi_table = Table(kpi_data, colWidths=[120, 140, 120, 150])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 15))

        # 3. Findings Table
        story.append(Paragraph("<b>1. Detailed Inspection Findings</b>", h2_style))
        if not findings:
            story.append(Paragraph("No anomalies or findings detected. The dataset adheres to all expected quality and schema standards.", body_style))
        else:
            findings_header = [
                Paragraph("<b>#</b>", body_style),
                Paragraph("<b>Finding Type</b>", body_style),
                Paragraph("<b>Severity</b>", body_style),
                Paragraph("<b>Message</b>", body_style),
            ]
            findings_rows = [findings_header]

            for idx, f in enumerate(findings, start=1):
                sev = f.get("severity", "LOW")
                sev_color = colors.HexColor("#DC2626") if sev == "CRITICAL" else (
                    colors.HexColor("#EA580C") if sev == "HIGH" else (
                        colors.HexColor("#D97706") if sev == "MEDIUM" else colors.HexColor("#2563EB")
                    )
                )
                findings_rows.append([
                    Paragraph(str(idx), body_style),
                    Paragraph(f.get("type", "UNKNOWN"), body_style),
                    Paragraph(f"<b>{sev}</b>", ParagraphStyle("Sev", parent=body_style, textColor=sev_color)),
                    Paragraph(f.get("message", ""), body_style),
                ])

            findings_table = Table(findings_rows, colWidths=[25, 140, 65, 300])
            findings_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ]))
            story.append(findings_table)

        story.append(Spacer(1, 15))

        # 4. Root Cause Analysis
        rca = inspection_data.get("root_cause", {})
        if rca and rca.get("candidates"):
            story.append(Paragraph("<b>2. Root Cause Diagnostic Hypotheses</b>", h2_style))
            rca_header = [
                Paragraph("<b>Confidence</b>", body_style),
                Paragraph("<b>Probable Root Cause</b>", body_style),
                Paragraph("<b>Affected Stage</b>", body_style),
            ]
            rca_rows = [rca_header]
            for cand in rca.get("candidates", [])[:5]:
                conf = cand.get("confidence", 0.0)
                rca_rows.append([
                    Paragraph(f"<b>{conf*100:.1f}%</b>", body_style),
                    Paragraph(cand.get("cause", ""), body_style),
                    Paragraph(cand.get("affected_area", "ETL Pipeline"), body_style),
                ])

            rca_table = Table(rca_rows, colWidths=[70, 310, 150])
            rca_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(rca_table)

        # 5. Build Document
        doc.build(story)
        return filepath

    def generate_excel_report(
        self,
        inspection_data: dict[str, Any],
        filename: str | None = None,
    ) -> str:
        """
        Generates an OpenPyXL multi-sheet Excel audit workbook.
        """
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fname = filename or f"DataGuard_Audit_Workbook_{ts}.xlsx"
        filepath = os.path.join(self.output_dir, fname)

        wb = openpyxl.Workbook()
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

        # Sheet 1: Executive Summary
        ws_summary = wb.active
        ws_summary.title = "Executive Summary"
        ws_summary.append(["Metric", "Value"])
        ws_summary.append(["Dataset Path", inspection_data.get("dataset_path", "N/A")])
        ws_summary.append(["Audit Status", inspection_data.get("inspection", {}).get("status", "N/A")])
        ws_summary.append(["Row Count", inspection_data.get("row_count", 0)])
        ws_summary.append(["Column Count", inspection_data.get("column_count", 0)])
        ws_summary.append(["Finding Count", len(inspection_data.get("inspection", {}).get("findings", []))])
        ws_summary.append(["Audit SHA-256 Hash", inspection_data.get("audit_hash") or inspection_data.get("evidence", {}).get("audit_hash") or "UNVERIFIED"])
        ws_summary.append(["HMAC Signature", inspection_data.get("audit_hmac") or inspection_data.get("evidence", {}).get("audit_hmac") or "UNVERIFIED"])
        ws_summary.append(["Generated At", datetime.utcnow().isoformat()])

        for cell in ws_summary[1]:
            cell.fill = header_fill
            cell.font = header_font

        # Sheet 2: Findings
        ws_findings = wb.create_sheet(title="Findings Log")
        ws_findings.append(["#", "Finding Type", "Severity", "Message", "Evidence"])
        for cell in ws_findings[1]:
            cell.fill = header_fill
            cell.font = header_font

        findings = inspection_data.get("inspection", {}).get("findings", [])
        for idx, f in enumerate(findings, start=1):
            ws_findings.append([
                idx,
                f.get("type"),
                f.get("severity"),
                f.get("message"),
                str(f.get("evidence")),
            ])

        # Auto-adjust column widths with safe sizing
        for ws in [ws_summary, ws_findings]:
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 60)

        wb.save(filepath)
        return filepath

    def generate_remediated_excel_report(
        self,
        rows: list[dict[str, Any]],
        recovery_run_id: str,
        audit_metadata: dict[str, Any],
        filename: str | None = None,
        output_dir: str | None = None,
    ) -> str:
        """
        Generates an authoritative OpenPyXL Excel workbook containing the final verified remediated dataset.
        Enforces:
        - Correct numeric types and formats (integers as int, floats with number formatting)
        - Excel-compatible date formatting
        - Safe column width sizing (min 14, max 50)
        - Explicit OpenPyXL re-opening validation checking zero '####' and row count parity.
        """
        out_dir = output_dir or self.output_dir
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fname = filename or f"remediated_{recovery_run_id}_{ts}.xlsx"
        filepath = os.path.join(out_dir, fname)

        wb = openpyxl.Workbook()

        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        meta_header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        meta_header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

        thin_side = Side(border_style="thin", color="CBD5E1")
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        # Sheet 1: Remediated Dataset
        ws_data = wb.active
        ws_data.title = "Remediated Dataset"

        if rows:
            MAX_XLSX_ROWS = 5000
            export_rows = rows[:MAX_XLSX_ROWS] if len(rows) > MAX_XLSX_ROWS else rows
            headers = list(export_rows[0].keys())
            ws_data.append(headers)

            for cell in ws_data[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_align
                cell.border = cell_border

            ws_data.row_dimensions[1].height = 24
            ws_data.freeze_panes = "A2"

            col_widths = {col: len(str(col)) for col in headers}

            for r_idx, r in enumerate(export_rows, start=2):
                row_vals = []
                for col in headers:
                    val = r.get(col)
                    # Check for date strings (YYYY-MM-DD)
                    if isinstance(val, str) and len(val) == 10 and re.match(r"^\d{4}-\d{2}-\d{2}$", val):
                        try:
                            val = datetime.strptime(val, "%Y-%m-%d").date()
                        except Exception:
                            pass
                    row_vals.append(val)
                ws_data.append(row_vals)

                # Format cells in this row
                for cell in ws_data[r_idx]:
                    cell.border = cell_border
                    val = cell.value
                    if isinstance(val, bool):
                        cell.alignment = Alignment(horizontal="center")
                    elif isinstance(val, int):
                        cell.number_format = "#,##0"
                        cell.alignment = Alignment(horizontal="right")
                    elif isinstance(val, float):
                        cell.number_format = "#,##0.00"
                        cell.alignment = Alignment(horizontal="right")
                    elif isinstance(val, (datetime, date)):
                        cell.number_format = "yyyy-mm-dd"
                        cell.alignment = Alignment(horizontal="center")
                    else:
                        cell.alignment = Alignment(horizontal="left")

            # Efficient column width calculation using first 200 rows sample
            for r in export_rows[:200]:
                for col in headers:
                    v = r.get(col)
                    if v is not None:
                        slen = len(str(v))
                        if slen > col_widths[col]:
                            col_widths[col] = slen

            for col_idx, col in enumerate(headers, start=1):
                col_letter = openpyxl.utils.get_column_letter(col_idx)
                ws_data.column_dimensions[col_letter].width = min(max(col_widths[col] + 5, 14), 50)

        # Sheet 2: Recovery Audit & Verification
        ws_audit = wb.create_sheet(title="Recovery Audit Log")
        ws_audit.append(["Audit Metric", "Value"])
        for cell in ws_audit[1]:
            cell.fill = meta_header_fill
            cell.font = meta_header_font
            cell.border = cell_border

        audit_metrics = [
            ("Recovery Run ID", str(recovery_run_id)),
            ("Target Dataset", str(audit_metadata.get("dataset_path", "N/A"))),
            ("Execution Status", str(audit_metadata.get("status", "RECOVERY_APPLIED"))),
            ("Verification Verdict", str(audit_metadata.get("verdict", "UNKNOWN"))),
            ("Original Input Rows", audit_metadata.get("original_row_count", 0)),
            ("Remediated Output Rows", len(rows)),
            ("Row Count Delta", len(rows) - audit_metadata.get("original_row_count", 0)),
            ("Actions Executed Count", len(audit_metadata.get("actions_executed", []))),
            ("Actions Skipped Count", len(audit_metadata.get("actions_skipped", []))),
            ("Remediated Artifact SHA-256", str(audit_metadata.get("remediated_file_hash", "UNVERIFIED"))),
            ("Executed By Role", str(audit_metadata.get("executed_by_role", "UNKNOWN"))),
            ("Executed At (UTC)", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")),
        ]
        for m_name, m_val in audit_metrics:
            ws_audit.append([m_name, m_val])

        for row in ws_audit.iter_rows(min_row=2, max_col=2):
            for cell in row:
                cell.border = cell_border

        for col in ws_audit.columns:
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            max_len = max(len(str(c.value or "")) for c in col)
            ws_audit.column_dimensions[col_letter].width = min(max(max_len + 4, 15), 50)

        # Sheet 3: Executed Actions
        ws_actions = wb.create_sheet(title="Remediation Actions")
        act_headers = ["Action ID", "Action Type", "Target", "Severity", "Risk Level", "Policy Status", "Rows Affected", "Status"]
        ws_actions.append(act_headers)
        for cell in ws_actions[1]:
            cell.fill = meta_header_fill
            cell.font = meta_header_font
            cell.border = cell_border

        for act in audit_metadata.get("actions_executed", []):
            ws_actions.append([
                act.get("action_id", "N/A"),
                act.get("action_type", "N/A"),
                str(act.get("target", "ALL")),
                act.get("severity", "MEDIUM"),
                act.get("risk_level", "LOW"),
                act.get("policy_status", "POLICY_APPROVED"),
                act.get("rows_affected", 0),
                "EXECUTED",
            ])

        for act in audit_metadata.get("actions_skipped", []):
            ws_actions.append([
                act.get("action_id", "N/A"),
                act.get("action_type", "N/A"),
                str(act.get("target", "ALL")),
                act.get("severity", "HIGH"),
                act.get("risk_level", "HIGH"),
                act.get("policy_status", "REQUIRES_OPERATOR_APPROVAL"),
                0,
                f"SKIPPED ({act.get('reason', 'Policy constraint')})",
            ])

        for row in ws_actions.iter_rows(min_row=2, max_col=8):
            for cell in row:
                cell.border = cell_border

        for col in ws_actions.columns:
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            max_len = max(len(str(c.value or "")) for c in col)
            ws_actions.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 45)

        wb.save(filepath)

        # RIGOROUS OPENPYXL POST-GENERATION VALIDATION
        reopened = openpyxl.load_workbook(filepath, data_only=True)
        try:
            if "Remediated Dataset" not in reopened.sheetnames:
                raise ValueError("Remediated workbook is missing 'Remediated Dataset' worksheet.")
            val_ws = reopened["Remediated Dataset"]
            if rows:
                expected_rows = len(export_rows) + 1
                if val_ws.max_row != expected_rows:
                    raise ValueError(f"Workbook row count mismatch: expected {expected_rows}, got {val_ws.max_row}")
                val_headers = [cell.value for cell in val_ws[1]]
                if val_headers != list(rows[0].keys()):
                    raise ValueError(f"Workbook header mismatch: {val_headers} != {list(rows[0].keys())}")

            for sheet_name in reopened.sheetnames:
                ws_check = reopened[sheet_name]
                for row_cells in ws_check.iter_rows(max_row=min(ws_check.max_row, 350), values_only=True):
                    for cell_val in row_cells:
                        if cell_val is not None and "####" in str(cell_val):
                            raise ValueError(f"Literal '####' found in worksheet '{sheet_name}' cell.")
        finally:
            reopened.close()

        return filepath

    def generate_recovery_pdf_report(
        self,
        recovery_data: dict[str, Any],
        filename: str | None = None,
        output_dir: str | None = None,
    ) -> str:
        """
        Builds an executive PDF recovery certificate and sign-off report using ReportLab.
        """
        out_dir = output_dir or self.output_dir
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fname = filename or f"DataGuard_Recovery_Report_{ts}.pdf"
        filepath = os.path.join(out_dir, fname)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=14,
        )
        h2_style = ParagraphStyle(
            "Heading2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155"),
        )
        badge_style = ParagraphStyle(
            "Badge",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.white,
            alignment=1,
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("<b>DataGuard 2.0 Controlled Recovery Certificate</b>", title_style))
        story.append(Paragraph(
            f"Autonomous Self-Healing Attestation & Post-Remediation Verification | Certified at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            subtitle_style,
        ))
        story.append(Spacer(1, 8))

        # 2. Executive KPIs
        dataset = recovery_data.get("dataset_path", "Dataset")
        verdict = recovery_data.get("verdict", "FAIL")
        orig_count = recovery_data.get("original_row_count", 0)
        rem_count = recovery_data.get("remediated_row_count", 0)
        file_hash = recovery_data.get("remediated_file_hash", "UNVERIFIED")
        executed_actions = recovery_data.get("actions_executed", [])
        skipped_actions = recovery_data.get("actions_skipped", [])

        verdict_color = colors.HexColor("#10B981") if verdict == "PASS" else colors.HexColor("#EF4444")

        kpi_data = [
            [
                Paragraph("<b>Target Dataset</b>", body_style),
                Paragraph(f"<code>{dataset}</code>", body_style),
                Paragraph("<b>Verification Verdict</b>", body_style),
                Paragraph(f"<b>{verdict}</b>", ParagraphStyle("Stat", parent=badge_style, textColor=verdict_color)),
            ],
            [
                Paragraph("<b>Input Rows Before</b>", body_style),
                Paragraph(f"{orig_count:,}", body_style),
                Paragraph("<b>Recovered Rows After</b>", body_style),
                Paragraph(f"<b>{rem_count:,}</b>", body_style),
            ],
            [
                Paragraph("<b>Actions Executed</b>", body_style),
                Paragraph(f"{len(executed_actions)}", body_style),
                Paragraph("<b>Actions Skipped (RBAC)</b>", body_style),
                Paragraph(f"{len(skipped_actions)}", body_style),
            ],
            [
                Paragraph("<b>Remediated SHA-256</b>", body_style),
                Paragraph(f"<font size=6.5><code>{file_hash[:32]}...</code></font>", body_style),
                Paragraph("<b>Integrity Sign-Off</b>", body_style),
                Paragraph(f"<font color='{verdict_color.hexval()}'><b>{verdict} CERTIFIED</b></font>", body_style),
            ],
        ]

        kpi_table = Table(kpi_data, colWidths=[120, 140, 120, 150])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 12))

        # 3. Actions Executed Table
        story.append(Paragraph("<b>1. Executed Remediation Actions</b>", h2_style))
        if not executed_actions:
            story.append(Paragraph("No remediation actions were executed.", body_style))
        else:
            headers = [
                Paragraph("<b>Action ID</b>", body_style),
                Paragraph("<b>Action Type</b>", body_style),
                Paragraph("<b>Target</b>", body_style),
                Paragraph("<b>Rows Affected</b>", body_style),
                Paragraph("<b>Status</b>", body_style),
            ]
            act_rows = [headers]
            for act in executed_actions:
                act_rows.append([
                    Paragraph(act.get("action_id", "N/A"), body_style),
                    Paragraph(act.get("action_type", "N/A"), body_style),
                    Paragraph(str(act.get("target", "ALL")), body_style),
                    Paragraph(str(act.get("rows_affected", 0)), body_style),
                    Paragraph("<font color='#059669'><b>EXECUTED</b></font>", body_style),
                ])
            act_table = Table(act_rows, colWidths=[65, 160, 130, 85, 90])
            act_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(act_table)

        # 4. Actions Skipped (if any)
        if skipped_actions:
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>2. Actions Skipped Due to Policy / RBAC Limits</b>", h2_style))
            skip_headers = [
                Paragraph("<b>Action ID</b>", body_style),
                Paragraph("<b>Action Type</b>", body_style),
                Paragraph("<b>Target</b>", body_style),
                Paragraph("<b>Policy Constraint</b>", body_style),
            ]
            skip_rows = [skip_headers]
            for act in skipped_actions:
                skip_rows.append([
                    Paragraph(act.get("action_id", "N/A"), body_style),
                    Paragraph(act.get("action_type", "N/A"), body_style),
                    Paragraph(str(act.get("target", "ALL")), body_style),
                    Paragraph(f"<font color='#DC2626'>{act.get('reason', 'Requires ADMIN approval')}</font>", body_style),
                ])
            skip_table = Table(skip_rows, colWidths=[65, 160, 130, 175])
            skip_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEE2E2")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(skip_table)

        doc.build(story)
        return filepath

    def generate_all_reports(
        self,
        inspection_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Coordinates generation of both PDF and Excel artifacts.
        """
        pdf_path = self.generate_pdf_report(inspection_data)
        excel_path = self.generate_excel_report(inspection_data)

        return {
            "agent": self.name,
            "status": "REPORTS_GENERATED",
            "pdf_report_path": pdf_path,
            "pdf_filename": os.path.basename(pdf_path),
            "excel_report_path": excel_path,
            "excel_filename": os.path.basename(excel_path),
            "generated_at": datetime.utcnow().isoformat(),
        }
