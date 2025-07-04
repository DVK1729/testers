import streamlit as st
import requests
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Page setup
st.set_page_config(page_title="AI Market Analyst", layout="centered")

st.markdown("<h1>🧠 AI Market Analyst</h1>", unsafe_allow_html=True)
st.markdown("Analyze your <b>market</b> or <b>competitor</b> using real-time AI insights. Get a clean, structured SWOT breakdown.", unsafe_allow_html=True)

# Input
query = st.text_input("🔍 Enter Market or Competitor Name")

# Extract SWOT sections
def extract_sections(text):
    sections = {}
    pattern = r"(Strengths|Weaknesses|Opportunities|Threats):"
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
    for i, match in enumerate(matches):
        section = match.group(1).capitalize()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip().lstrip(":").strip()
        sections[section] = content
    return sections

# Show section in UI
def show_section(header, content, emoji):
    st.markdown(f"### {emoji} {header}")
    for line in content.split("\n"):
        clean_line = line.strip().lstrip("•-").strip()
        if clean_line:
            st.markdown(f"- {clean_line}")

# PDF generator
def create_pdf(swot_data):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"SWOT Report: {query}")
    y -= 30

    p.setFont("Helvetica", 12)
    for section, content in swot_data.items():
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, f"{section}:")
        y -= 20
        p.setFont("Helvetica", 12)
        for line in content.split("\n"):
            clean_line = line.strip().lstrip("•-").strip()
            if clean_line:
                if y < 50:
                    p.showPage()
                    y = height - 50
                p.drawString(60, y, f"- {clean_line}")
                y -= 15
        y -= 20

    p.save()
    buffer.seek(0)
    return buffer

# API and render
if st.button("Generate SWOT") and query:
    with st.spinner("Analyzing..."):
        try:
            response = requests.post("http://localhost:8000/analyze", json={"query": query})
            response.raise_for_status()
            swot = response.json().get("swot_report", "")

            if not swot:
                st.error("❌ Empty SWOT analysis received.")
            else:
                st.success("✅ SWOT Analysis Generated")
                st.markdown("### 📝 SWOT Analysis Report")
                sections = extract_sections(swot)

                if not sections:
                    st.warning("Could not detect standard SWOT sections.")
                else:
                    for sec, emoji in zip(["Strengths", "Weaknesses", "Opportunities", "Threats"],
                                          ["🟩", "🟥", "🟦", "🟨"]):
                        if sec in sections:
                            show_section(sec, sections[sec], emoji)

                    # PDF Download
                    pdf_buffer = create_pdf(sections)
                    st.download_button("📥 Download PDF Report", data=pdf_buffer, file_name="SWOT_Report.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"❌ Error: {e}")
