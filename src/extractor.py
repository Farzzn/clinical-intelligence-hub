import os
from typing import List
from google import genai
from google.genai import types
from dotenv import load_dotenv
from src.schemas import ClinicalIntelligenceReport

load_dotenv()

SYSTEM_INSTRUCTION = """
You are an expert Clinical Intelligence & Multi-Document Reconciliation Agent.
Your objective is to ingest one or MORE clinical documents (which may include a combination of PDF/text lab reports, doctor consultation notes, and scanned/handwritten prescriptions) and synthesize them into a single, unified, structured medical intelligence report.

Reconciliation Guidelines:
1. Cross-Document Synthesis: If a lab report shows an abnormal biomarker and a prescription image lists medications, reconcile them together into one patient record.
2. Structured Extraction: Extract patient demographics, vital signs, all lab biomarkers with ranges, active medications, and prioritize clinical risk flags with citations.
3. Medical Grounding: Quote source text directly in `source_quote` whenever possible.
4. No Hallucinations: If certain fields are absent across all provided files, leave them as null/empty.
"""

def extract_multi_document_intelligence(
    text_contents: List[str], 
    image_parts: List[dict]
) -> ClinicalIntelligenceReport:
    """
    Ingests multiple text documents and image byte payloads simultaneously,
    synthesizing them into a single unified ClinicalIntelligenceReport.
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    contents = []
    
    # 1. Add all parsed text/PDF contents
    for idx, text in enumerate(text_contents, 1):
        contents.append(f"--- CLINICAL DOCUMENT #{idx} (TEXT/PDF) ---\n{text}\n")
        
    # 2. Add all image parts (handwritten notes, scanned prescriptions)
    for idx, img in enumerate(image_parts, 1):
        contents.append(f"--- CLINICAL ATTACHMENT #{idx} (IMAGE/SCANNED NOTE) ---")
        contents.append(types.Part.from_bytes(data=img["bytes"], mime_type=img["mime_type"]))
        
    contents.append("Synthesize all provided documents and attachments into a unified, reconciled ClinicalIntelligenceReport.")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ClinicalIntelligenceReport,
            temperature=0.1,
        ),
    )
    return ClinicalIntelligenceReport.model_validate_json(response.text)