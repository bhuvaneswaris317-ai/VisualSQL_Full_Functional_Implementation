import io
import re
import pandas as pd
import database as db
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
from reportlab.lib import colors

Q = (
    "SELECT e.id, e.query_name, e.dataset_size, e.created_at, c.name as config, "
    "r.index_config, r.avg_ms, r.min_ms, r.max_ms, r.row_count, r.improvement_pct, "
    "r.access_type, r.status "
    "FROM benchmark_results r "
    "JOIN benchmark_experiments e ON e.id=r.experiment_id "
    "JOIN optimization_configurations c ON c.id=r.config_id"
)


def rows(exp_id=None):
    """Fetches benchmark results for a single experiment or all experiments."""
    sql = Q + (" WHERE e.id=%s" if exp_id else "") + " ORDER BY e.id DESC, r.id ASC"
    return db.fetch(sql, (exp_id,) if exp_id else None)


def csv_bytes(exp_id=None):
    """Generates CSV bytes of benchmark results."""
    data = rows(exp_id)
    if not data:
        return b"id,query_name,dataset_size,created_at,config,index_config,avg_ms,min_ms,max_ms,row_count,improvement_pct,access_type,status\n"
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode("utf-8")


def format_report_text(text):
    """Converts markdown text to ReportLab XML safely with balanced tags."""
    if not text:
        return ""
    # Strip emojis or unsupported symbols for standard fonts
    # Replace common emoji symbols with clean text equivalents
    replacements = {
        "⚡": "[Speedup]",
        "ℹ️": "[Notice]",
        "🚨": "[Alert]",
        "🎯": "[Projection]",
        "⚖️": "[Trade-off]",
        "💎": "[Optimal]",
        "🔬": "[Note]",
        "⚠️": "[Warning]"
    }
    for emo, tag in replacements.items():
        text = text.replace(emo, tag)

    # Escape XML entities
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Balanced bold formatting
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Balanced code formatting
    text = re.sub(r"`(.*?)`", r'<font name="Courier">\1</font>', text)
    return text


def pdf_bytes(exp_id):
    """Generates an executive-grade PDF benchmark report."""
    from recommendation import recommend

    data = rows(exp_id)
    if not data:
        raise ValueError(f"Experiment #{exp_id} not found.")

    exp_rows = db.fetch("SELECT * FROM benchmark_experiments WHERE id=%s", (exp_id,))
    if not exp_rows:
        raise ValueError(f"Experiment metadata for #{exp_id} not found.")
    exp = exp_rows[0]

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=0,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    sql_style = ParagraphStyle(
        "SQLBox",
        parent=styles["Code"],
        fontSize=8,
        leading=11,
        fontName="Courier",
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=4,
        spaceAfter=8
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    def fmt_num(v, decimals=2):
        if v is None:
            return "-"
        try:
            return f"{float(v):.{decimals}f}"
        except (ValueError, TypeError):
            return str(v)

    # Document Header
    elements = [
        Paragraph("VisualSQL Performance Benchmark Report", title_style),
        Paragraph(
            f"Experiment #{exp_id} &bull; Workload: <b>{exp['query_name']}</b> &bull; "
            f"Dataset: <b>{exp['dataset_size']:,} records</b> &bull; "
            f"Repetitions: <b>{exp['repetitions']} passes</b> &bull; Generated: {exp['created_at']}",
            subtitle_style
        ),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceBefore=0, spaceAfter=10),
    ]

    # SQL Statement Block
    safe_sql = exp["sql_text"].replace("<", "&lt;").replace(">", "&gt;")
    elements.extend([
        Paragraph("Tested SQL Statement", heading_style),
        Paragraph(safe_sql, sql_style),
        Spacer(1, 4)
    ])

    # Measurements Table
    headers = ["Configuration", "Index Setup", "Avg (ms)", "Min (ms)", "Max (ms)", "Rows", "Gain %", "Status"]
    table_rows = [headers]
    for d in data:
        table_rows.append([
            d.get("config", ""),
            d.get("index_config", "none"),
            fmt_num(d.get("avg_ms")),
            fmt_num(d.get("min_ms")),
            fmt_num(d.get("max_ms")),
            str(d.get("row_count", 0)),
            fmt_num(d.get("improvement_pct"), 1) + "%" if d.get("improvement_pct") is not None else "-",
            d.get("status", "ok")
        ])

    col_widths = [100, 110, 52, 48, 48, 45, 55, 55]
    t = Table(table_rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (2, 0), (6, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
    ]))

    elements.extend([
        Paragraph("Empirical Execution Metrics", heading_style),
        t,
        Spacer(1, 8)
    ])

    # Recommendations
    fake_results = [
        {
            "config": d["config"],
            "avg": d["avg_ms"] or 0.0,
            "improvement": d["improvement_pct"] or 0.0,
            "status": d["status"],
            "index": [] if d["index_config"] == "none" else [d["index_config"]]
        }
        for d in data
    ]
    recs = recommend(fake_results)

    elements.extend([
        Paragraph("Optimization Insights & Recommendations", heading_style)
    ])
    for r in recs:
        formatted = format_report_text(r)
        elements.append(Paragraph(f"&bull; {formatted}", body_style))
        elements.append(Spacer(1, 2))

    elements.extend([
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=4, spaceAfter=6),
        Paragraph("Report generated by VisualSQL Intelligence Engine. Measurements reflect actual execution on active backend.", subtitle_style)
    ])

    doc.build(elements)
    return buf.getvalue()
