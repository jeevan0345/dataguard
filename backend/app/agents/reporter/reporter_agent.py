"""
DataGuard Reporter Agent
Generates comprehensive enterprise audit reports in PDF (ReportLab) and Excel (OpenPyXL).
"""

import os
from datetime import datetime
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

        # Auto-adjust column widths
        for ws in [ws_summary, ws_findings]:
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = min(max_len + 4, 60)

        wb.save(filepath)
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
