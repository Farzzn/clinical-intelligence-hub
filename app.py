import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
import streamlit.components.v1 as components
import json
from PIL import Image
from io import BytesIO
from src.schemas import ClinicalIntelligenceReport, UrgencyLevel, BiomarkerStatus
from src.extractor import extract_multi_document_intelligence
from src.parser import extract_text_from_file

st.set_page_config(
    page_title="Clinical Document Intelligence Hub",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling & Responsive Cards
st.markdown("""
<style>
    .badge-critical { background-color: #fee2e2; color: #991b1b; font-weight: 700; padding: 6px 12px; border-radius: 6px; display: inline-block; font-size: 0.9rem; }
    .badge-high { background-color: #ffedd5; color: #9a3412; font-weight: 700; padding: 6px 12px; border-radius: 6px; display: inline-block; font-size: 0.9rem; }
    .badge-moderate { background-color: #fef9c3; color: #854d0e; font-weight: 700; padding: 6px 12px; border-radius: 6px; display: inline-block; font-size: 0.9rem; }
    .badge-routine { background-color: #dcfce7; color: #166534; font-weight: 700; padding: 6px 12px; border-radius: 6px; display: inline-block; font-size: 0.9rem; }
    
    .meta-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 12px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .meta-title {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 2px;
    }
    .meta-val {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        word-break: break-word;
        line-height: 1.25;
    }
    .quote-box { border-left: 3px solid #64748b; padding-left: 10px; font-size: 0.88rem; color: #475569; font-style: italic; margin-top: 6px; }
    .doc-pill { background-color: #e2e8f0; padding: 4px 8px; border-radius: 4px; font-size: 0.82rem; margin: 2px; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# Synthetic Presets
SAMPLE_DOCS = {
    "Sample 1: Discharge Summary (Sepsis & AKI)": """PATIENT DISCHARGE SUMMARY
Patient Name: Arthur Pendelton | MRN: 948210
Age: 68 | Gender: Male
Admission Date: 2026-08-18 | Discharge Date: 2026-08-24
Attending Physician: Dr. Sarah Bennett, MD

PRIMARY DIAGNOSIS:
1. Urosepsis secondary to E. coli UTI (Resolved)
2. Acute Kidney Injury (Stage 2, resolving)
3. Essential Hypertension

HOSPITAL COURSE & VITALS AT DISCHARGE:
Patient presented with fever (39.1°C), BP 85/55 mmHg, and elevated lactate. Treated with IV Ceftriaxone.
Discharge Vitals: BP: 128/78 mmHg | HR: 74 bpm | RR: 16 bpm | Temp: 36.8°C | SpO2: 98% on room air.

DISCHARGE LAB HIGHLIGHTS:
- Serum Creatinine: 1.6 mg/dL (Baseline 1.0 mg/dL, Peak 2.8 mg/dL) -> Elevated
- Serum Potassium: 4.8 mEq/L -> Normal (Ref: 3.5 - 5.0 mEq/L)
- WBC Count: 9.4 x10^3/uL -> Normal (Peak 19.8 x10^3/uL)
- eGFR: 45 mL/min/1.73m2 -> Low

DISCHARGE MEDICATIONS:
- Ciprofloxacin 500 mg PO BID (Complete 3 more days)
- Lisinopril 10 mg PO Daily (HOLD until renal panel repeat)
- Amlodipine 5 mg PO Daily (Continued)

FOLLOW-UP INSTRUCTIONS:
Repeat Comprehensive Metabolic Panel (CMP) in 5 days with PCP.""",

    "Sample 2: Emergency Lab Alert (Severe Hyperkalemia)": """STAT CRITICAL LAB ALERT & TRIAGE REPORT
Patient: Maria Gonzales | Age: 54 | Gender: Female | MRN: 110934
Encounter Date: 2026-08-25 09:30 AM
Location: Outpatient Renal Clinic

URGENT LAB VALUES:
- Serum Potassium: 6.7 mEq/L [CRITICAL HIGH] (Reference: 3.5 - 5.1 mEq/L)
- Serum Sodium: 134 mEq/L (Reference: 135 - 145 mEq/L)
- BUN: 58 mg/dL [HIGH] (Reference: 7 - 20 mg/dL)
- Serum Creatinine: 3.4 mg/dL [HIGH] (Reference: 0.6 - 1.2 mg/dL)

CLINICAL NOTES:
Patient reports mild muscle weakness and nausea. Currently taking Spironolactone 25 mg daily and Losartan 50 mg daily.
Baseline vitals: BP: 142/90 mmHg, HR: 52 bpm (Bradycardic), SpO2: 96%.
ALERT: High risk for fatal cardiac arrhythmias. Immediate intervention required.""",

    "Sample 3: Outpatient Intake (Type 2 Diabetes)": """CLINICAL INTAKE FORM - ENDOCRINOLOGY
Patient: David Vance | Age: 46 | Gender: Male
Date of Encounter: 2026-08-25

CHIEF COMPLAINT:
"Follow-up for poorly controlled blood sugars and tingling in both feet."

VITALS:
BP: 136/84 mmHg | HR: 80 bpm | Temp: 36.6°C | SpO2: 99% | BMI: 31.4 kg/m2

POINT-OF-CARE LABS:
- HbA1c: 9.8% (Target < 7.0%) -> ABNORMAL HIGH
- Fasting Blood Glucose: 215 mg/dL -> HIGH
- Microalbumin/Creatinine Ratio: 45 mcg/mg (Mildly Elevated)

CURRENT REGIMEN:
- Metformin 1000 mg PO BID
- Glipizide 5 mg PO Daily

ASSESSMENT & PLAN:
Uncontrolled T2D with early neuropathy. Add Empagliflozin 10 mg daily. Schedule podiatry screening."""
}

text_payloads = []
image_payloads = []

with st.sidebar:
    st.title("🩺 Control Panel")
    st.markdown("Ingest multiple clinical documents, lab PDFs, and prescription images simultaneously.")
    
    input_source = st.radio(
        "Choose Input Source:",
        ["Preloaded Sample Scenarios", "Upload Document(s) (Multi-File Support)", "Manual Text Input"]
    )
    
    if input_source == "Preloaded Sample Scenarios":
        selected_scenario = st.selectbox("Select Scenario:", list(SAMPLE_DOCS.keys()))
        text_payloads = [SAMPLE_DOCS[selected_scenario]]
        
    elif input_source == "Upload Document(s) (Multi-File Support)":
        uploaded_files = st.file_uploader(
            "Upload Clinical Files (PDF, TXT, PNG, JPG)", 
            type=["pdf", "txt", "png", "jpg", "jpeg"],
            accept_multiple_files=True
        )
        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} File(s) Staged:**")
            for f in uploaded_files:
                st.markdown(f'<span class="doc-pill">📄 {f.name}</span>', unsafe_allow_html=True)
                ext = f.name.split(".")[-1].lower()
                if ext in ["png", "jpg", "jpeg"]:
                    image_payloads.append({
                        "filename": f.name,
                        "bytes": f.read(),
                        "mime_type": "image/png" if ext == "png" else "image/jpeg"
                    })
                else:
                    text_payloads.append(f"Document [{f.name}]:\n" + extract_text_from_file(f))
                    
    else:
        pasted = st.text_area("Paste Clinical Document Text Here:", height=250)
        if pasted.strip():
            text_payloads = [pasted]
            
    process_btn = st.button("⚡ Reconcile & Extract Intelligence", type="primary", use_container_width=True)

st.title("Clinical Document Intelligence Hub")
st.caption("AI-powered multi-document clinical reconciliation, handwritten prescription OCR, and decision support.")

def render_urgency_badge(level: UrgencyLevel):
    mapping = {
        UrgencyLevel.CRITICAL: '<span class="badge-critical">CRITICAL URGENCY</span>',
        UrgencyLevel.HIGH: '<span class="badge-high">HIGH URGENCY</span>',
        UrgencyLevel.MODERATE: '<span class="badge-moderate">MODERATE URGENCY</span>',
        UrgencyLevel.ROUTINE: '<span class="badge-routine">ROUTINE</span>'
    }
    return mapping.get(level, str(level))

# Process All Files Together
if process_btn:
    if not text_payloads and not image_payloads:
        st.warning("Please provide or upload at least one document or image.")
    else:
        with st.spinner(f"Reconciling intelligence across {len(text_payloads) + len(image_payloads)} document source(s)..."):
            try:
                report = extract_multi_document_intelligence(text_payloads, image_payloads)
                st.session_state["report"] = report
                st.session_state["text_payloads"] = text_payloads
                st.session_state["image_payloads"] = image_payloads
                st.session_state["auto_collapse_sidebar"] = True
            except Exception as e:
                st.error(f"Intelligence Extraction Error: {str(e)}")

# Display Split Screen View
if "report" in st.session_state:
    # Auto-collapse sidebar on first extraction
    if st.session_state.get("auto_collapse_sidebar", False):
        components.html(
            """
            <script>
                const doc = window.parent.document;
                const collapseBtn =
                    doc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                    doc.querySelector('[data-testid="stSidebarCollapseButton"]') ||
                    doc.querySelector('button[title="Collapse sidebar"]');
                if (collapseBtn) {
                    collapseBtn.click();
                }
            </script>
            """,
            height=0,
            width=0
        )
        st.session_state["auto_collapse_sidebar"] = False

    report: ClinicalIntelligenceReport = st.session_state["report"]
    texts = st.session_state.get("text_payloads", [])
    imgs = st.session_state.get("image_payloads", [])
    
    col_left, col_right = st.columns([1, 1.3], gap="large")

    with col_left:
        st.subheader(f"📄 Raw Clinical Sources ({len(texts) + len(imgs)})")
        
        # Display all images
        for img_item in imgs:
            st.markdown(f"**Attachment: `{img_item['filename']}`**")
            im = Image.open(BytesIO(img_item["bytes"]))
            st.image(im, use_container_width=True)
            
        # Display all text/PDF files
        for idx, txt in enumerate(texts, 1):
            st.text_area(f"Document Text Content #{idx}", value=txt, height=280, disabled=True)

    with col_right:
        st.subheader("📊 Reconciled Structured Intelligence")
        
        # Responsive Meta Card Grid (No Text Truncation)
        h_col1, h_col2, h_col3 = st.columns([1.1, 1.8, 0.9])
        with h_col1:
            st.markdown(f'<div class="meta-card"><div class="meta-title">Triage Urgency</div>{render_urgency_badge(report.overall_urgency)}</div>', unsafe_allow_html=True)
        with h_col2:
            st.markdown(f'<div class="meta-card"><div class="meta-title">Synthesis Type</div><div class="meta-val">{report.document_type}</div></div>', unsafe_allow_html=True)
        with h_col3:
            st.markdown(f'<div class="meta-card"><div class="meta-title">Confidence</div><div class="meta-val">{int(report.confidence_score * 100)}%</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
        st.info(f"**Clinical Summary:** {report.executive_summary}")

        tabs = st.tabs(["👤 Patient & Vitals", "⚠️ Risk Alerts", "🧪 Labs & Biomarkers", "💊 Medications & Actions", "🔍 JSON Output"])

        with tabs[0]:
            p = report.demographics
            st.markdown(f"**Patient Name:** {p.name or 'N/A'} | **Age:** {p.age or 'N/A'} | **Gender:** {p.gender or 'N/A'} | **MRN:** {p.patient_id or 'N/A'}")
            st.markdown(f"**Admission / Date:** {p.admission_date or 'N/A'} | **Discharge:** {p.discharge_date or 'N/A'}")
            
            if report.diagnoses:
                st.markdown("**Diagnoses Identified:**")
                for d in report.diagnoses:
                    st.markdown(f"- {d}")

            if report.vitals:
                st.markdown("**Extracted Vitals:**")
                v = report.vitals
                v_cols = st.columns(4)
                v_cols[0].metric("Blood Pressure", v.blood_pressure or "N/A")
                v_cols[1].metric("Heart Rate", f"{v.heart_rate_bpm} bpm" if v.heart_rate_bpm else "N/A")
                v_cols[2].metric("Temp (°C)", f"{v.temperature_celsius}°C" if v.temperature_celsius else "N/A")
                v_cols[3].metric("SpO2", f"{v.spo2_percentage}%" if v.spo2_percentage else "N/A")

        with tabs[1]:
            if not report.risk_flags:
                st.success("No critical or elevated risk flags identified.")
            else:
                for flag in report.risk_flags:
                    border_color = "#ef4444" if flag.severity in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH] else "#f59e0b"
                    st.markdown(f"""
                    <div style="border-left: 4px solid {border_color}; padding: 8px 12px; margin-bottom: 12px; background-color: #ffffff; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                        <strong style="font-size: 1.05rem;">{flag.flag_title}</strong> — <span style="font-weight: 600;">{flag.severity.value}</span>
                        <p style="margin: 4px 0; font-size: 0.92rem; color: #334155;">{flag.rationale}</p>
                        {f'<div class="quote-box">Source Citation: "{flag.source_quote}"</div>' if flag.source_quote else ''}
                    </div>
                    """, unsafe_allow_html=True)

        with tabs[2]:
            if not report.lab_biomarkers:
                st.write("No lab biomarker data extracted.")
            else:
                lab_table = []
                for lab in report.lab_biomarkers:
                    status_display = "⚠️ Critical" if lab.status == BiomarkerStatus.CRITICAL else (
                        "🔺 High" if lab.status == BiomarkerStatus.ABNORMAL_HIGH else (
                            "🔻 Low" if lab.status == BiomarkerStatus.ABNORMAL_LOW else "✅ Normal"
                        )
                    )
                    lab_table.append({
                        "Test Name": lab.test_name,
                        "Observed Value": lab.observed_value,
                        "Reference Range": lab.reference_range or "N/A",
                        "Status": status_display,
                        "Clinical Relevance": lab.clinical_note or ""
                    })
                st.dataframe(lab_table, use_container_width=True)

        with tabs[3]:
            st.markdown("#### Reconciled Medications (Prescription + Records)")
            if report.medications:
                med_data = [{"Drug Name": m.drug_name, "Dosage": m.dosage or "N/A", "Frequency": m.frequency or "N/A", "Status": m.status} for m in report.medications]
                st.dataframe(med_data, use_container_width=True)
            else:
                st.write("No medications extracted.")

            st.markdown("#### Recommended Action Plan")
            if report.recommended_actions:
                for act in sorted(report.recommended_actions, key=lambda x: x.priority):
                    st.markdown(f"**Priority {act.priority}** ({act.assigned_role}): {act.action}")
            else:
                st.write("No specific action items generated.")

        with tabs[4]:
            st.json(report.model_dump())
            st.download_button(
                "📥 Export Unified JSON Report",
                data=json.dumps(report.model_dump(), indent=2),
                file_name="reconciled_clinical_report.json",
                mime="application/json"
            )