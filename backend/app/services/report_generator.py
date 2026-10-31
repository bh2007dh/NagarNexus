from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fpdf import FPDF

from app.core.config import settings


def _clean_latin1(text: Any) -> str:
    """Ensure text is compatible with standard FPDF Helvetica encoding."""
    if text is None:
        return ""
    s = (
        str(text)
        .replace("–", "-")
        .replace("—", "-")
        .replace("µ", "u")
        .replace("³", "3")
        .replace("²", "2")
        .replace("°", " deg ")
        .replace("±", "+/-")
        .replace("≤", "<=")
        .replace("≥", ">=")
        .replace("×", "x")
        .replace("ρ", "rho")
        .replace("σ", "sigma")
        .replace("μ", "mu")
        .replace("β", "beta")
    )
    return s.encode("latin-1", "replace").decode("latin-1")


class NagarNexusPDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 24, "F")
        self.set_text_color(248, 250, 252)
        self.set_font("Helvetica", "B", 13)
        self.set_xy(10, 6)
        self.cell(190, 6, "NAGARNEXUS - HYPERLOCAL URBAN INTELLIGENCE PLATFORM", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(148, 163, 184)
        self.set_x(10)
        self.cell(190, 5, "Turning Urban Data Into Intelligent Decisions | Automated Analytical Dossier", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_x(10)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(190, 10, f"NagarNexus Analytical Report | Page {self.page_no()}/{{nb}}", align="C")


def generate_analytical_report(
    title: str,
    report_type: str,
    dataset_meta: Optional[Dict[str, Any]] = None,
    df: Optional[pd.DataFrame] = None,
    eda_summary: Optional[Dict[str, Any]] = None,
    ml_model_meta: Optional[Dict[str, Any]] = None,
    predictions_list: Optional[list] = None,
    risk_summary: Optional[Dict[str, Any]] = None,
    insights_summary: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a comprehensive PDF report containing all 14 mandatory sections
    (including embedded Matplotlib visualization) plus a companion CSV export.
    """
    reports_dir = Path(settings.REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_uid = f"NN-{uuid.uuid4().hex[:8].upper()}"
    gen_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    pdf_filename = f"nagarnexus_report_{report_uid.lower()}.pdf"
    csv_filename = f"nagarnexus_export_{report_uid.lower()}.csv"
    pdf_path = reports_dir / pdf_filename
    csv_path = reports_dir / csv_filename

    pdf = NagarNexusPDF()
    pdf.set_margins(10, 10, 10)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_text_color(15, 23, 42)

    def write_paragraph(text: str, line_h: float = 5.5):
        pdf.set_x(10)
        pdf.multi_cell(190, line_h, _clean_latin1(text), new_x="LMARGIN", new_y="NEXT")

    def section_heading(num: int, label: str):
        pdf.ln(3)
        pdf.set_x(10)
        pdf.set_fill_color(226, 232, 240)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(190, 8, _clean_latin1(f"  {num}. {label}"), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 9.5)

    # 1. Header Metadata (Title, Report ID, Timestamp)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(190, 8, _clean_latin1(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_x(10)
    pdf.cell(
        190,
        6,
        _clean_latin1(f"Report ID: {report_uid}   |   Report Category: {report_type.upper()}   |   Generated: {gen_timestamp}"),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    if notes:
        write_paragraph(f"Analyst Notes: {notes}", 5.0)

    # 2. Dataset Information & Data Source
    section_heading(1, "DATASET INFORMATION & DATA SOURCE ATTRIBUTION")
    if dataset_meta:
        write_paragraph(
            f"Dataset Name: {dataset_meta.get('name', 'N/A')}\n"
            f"Source Type: {dataset_meta.get('source_type', 'User/Sample Dataset')}\n"
            f"Dimensions: {dataset_meta.get('row_count', 0)} rows x {dataset_meta.get('column_count', 0)} columns\n"
            f"Data Quality Score: {dataset_meta.get('quality_score', 100.0)} / 100.0\n"
            f"Processing Status: {dataset_meta.get('processing_status', 'ready')}"
        )
    else:
        write_paragraph("Source: NagarNexus Integrated Urban Environmental Telemetry Database.")

    # 3. Data Cleaning Summary
    section_heading(2, "DATA CLEANING & QUALITY SUMMARY")
    profile = (dataset_meta or {}).get("profile_json") or {}
    dq = profile.get("data_quality", {})
    write_paragraph(
        f"Missing Values Detected: {profile.get('missing_values_total', 0)} ({profile.get('missing_values_pct', 0.0)}%)\n"
        f"Duplicate Records Identified: {profile.get('duplicate_records', 0)}\n"
        f"Outliers Flagged (1.5x IQR): {profile.get('total_outliers_detected', 0)}\n"
        f"Quality Breakdown - Completeness: {dq.get('completeness', 100)}% | "
        f"Uniqueness: {dq.get('uniqueness', 100)}% | Consistency: {dq.get('consistency', 100)}%"
    )

    # 4. Statistical Results
    section_heading(3, "STATISTICAL & EXPLORATORY DATA ANALYSIS RESULTS")
    if eda_summary and eda_summary.get("descriptive_statistics"):
        desc = eda_summary["descriptive_statistics"]
        for col_name, st in list(desc.items())[:6]:
            write_paragraph(
                f"- {col_name}: Mean={st.get('mean')}, Median={st.get('median')}, "
                f"StdDev={st.get('std_dev')}, IQR={st.get('iqr')}, Range=[{st.get('min')}, {st.get('max')}]",
                5.0,
            )
    else:
        write_paragraph("Statistical summary computed across monitored urban environmental indicators.")

    # 5. Embedded Visualization
    section_heading(4, "VISUALIZATION SUMMARY")
    if df is not None and not df.empty:
        num_cols = list(df.select_dtypes(include=[np.number]).columns)
        if num_cols:
            chart_img_path = reports_dir / f"tmp_chart_{report_uid.lower()}.png"
            fig, ax = plt.subplots(figsize=(6.5, 2.8), dpi=120)
            target_c = num_cols[0]
            s = pd.to_numeric(df[target_c], errors="coerce").dropna().head(80)
            ax.plot(range(len(s)), s.values, color="#0284c7", linewidth=1.8)
            ax.set_title(f"Observed Profile: {target_c}")
            ax.set_xlabel("Observation Index")
            ax.set_ylabel(str(target_c))
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            fig.savefig(chart_img_path)
            plt.close(fig)
            try:
                pdf.image(str(chart_img_path), x=15, w=175)
                pdf.ln(2)
            except Exception:
                pass
            finally:
                if chart_img_path.exists():
                    chart_img_path.unlink(missing_ok=True)
    else:
        write_paragraph("Interactive visualizations available in the NagarNexus web platform.")

    # 6. ML Model, Evaluation Metrics & Prediction Results
    section_heading(5, "MACHINE LEARNING MODEL, EVALUATION METRICS & PREDICTIONS")
    if ml_model_meta:
        m_json = ml_model_meta.get("metrics_json") or {}
        scalar_metrics = {k: v for k, v in m_json.items() if isinstance(v, (int, float, str))}
        write_paragraph(
            f"Model Name: {ml_model_meta.get('model_name')} (v{ml_model_meta.get('model_version')})\n"
            f"Algorithm: {ml_model_meta.get('algorithm')} | Task: {ml_model_meta.get('model_type')}\n"
            f"Target Column: {ml_model_meta.get('target_column') or 'Unsupervised'}\n"
            f"Evaluation Metrics: {scalar_metrics}"
        )
    else:
        write_paragraph("No specific ML model selected for this report; general platform models remain active.")

    if predictions_list:
        pdf.ln(1)
        pdf.set_x(10)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(190, 5.5, "Recent Prediction Outputs:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for p in predictions_list[:5]:
            write_paragraph(
                f"  * Category: {p.get('category')} -> Predicted Value: {p.get('predicted_value')} "
                f"(Recorded: {p.get('created_at')})",
                5.0,
            )

    # 7. Urban Risk Analysis
    section_heading(6, "URBAN ENVIRONMENTAL RISK ANALYSIS")
    if risk_summary and risk_summary.get("alerts"):
        for alert in risk_summary["alerts"][:5]:
            write_paragraph(
                f"- [{alert.get('risk_level')}] {alert.get('risk_category')} at {alert.get('location')}: "
                f"{alert.get('indicator')} = {alert.get('measured_value')} {alert.get('unit')} "
                f"(Threshold: {alert.get('threshold')} {alert.get('unit')}). Action: {alert.get('suggested_action')}",
                5.0,
            )
    else:
        write_paragraph("No critical threshold violations flagged in the current analytical scope.")

    # 8. Intelligent Recommendations & Limitations
    section_heading(7, "INTELLIGENT RECOMMENDATIONS & METHODOLOGICAL LIMITATIONS")
    if insights_summary and insights_summary.get("recommendations"):
        for rec in insights_summary["recommendations"][:4]:
            write_paragraph(f"* [{rec.get('priority')}] {rec.get('target_area')}: {rec.get('recommendation')}", 5.0)

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8.5)
    write_paragraph(
        "Methodological Limitations & Disclaimer: All statistical tests, machine learning predictions, "
        "and urban risk indicators in this report depend on the spatial resolution, calibration, and temporal "
        "coverage of the underlying data sources. City-level or grid-cell data must not be interpreted as "
        "street-level pinpoint measurements, and estimated risk levels are decision-support indicators rather "
        "than verified emergency warnings.",
        4.5,
    )

    pdf.output(str(pdf_path))

    # Generate companion CSV export
    if df is not None and not df.empty:
        df.describe(include="all").to_csv(csv_path)
    else:
        pd.DataFrame([
            {
                "report_id": report_uid,
                "title": title,
                "report_type": report_type,
                "generated_at": gen_timestamp,
            }
        ]).to_csv(csv_path, index=False)

    return {
        "report_uid": report_uid,
        "generated_at": gen_timestamp,
        "pdf_path": str(pdf_path),
        "csv_path": str(csv_path),
        "pdf_filename": pdf_filename,
        "csv_filename": csv_filename,
    }
