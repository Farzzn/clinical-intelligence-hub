from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class UrgencyLevel(str, Enum):
    ROUTINE = "ROUTINE"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BiomarkerStatus(str, Enum):
    NORMAL = "NORMAL"
    ABNORMAL_HIGH = "ABNORMAL_HIGH"
    ABNORMAL_LOW = "ABNORMAL_LOW"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class PatientDemographics(BaseModel):
    patient_id: Optional[str] = Field(
        None, description="Patient identifier or MRN if mentioned"
    )
    name: Optional[str] = Field(
        None, description="Full name of the patient"
    )
    age: Optional[int] = Field(
        None, description="Patient age in years", ge=0, le=125
    )
    gender: Optional[str] = Field(
        None, description="Patient gender (Male/Female/Other/Unknown)"
    )
    admission_date: Optional[str] = Field(
        None, description="Date of admission/encounter (YYYY-MM-DD or formatted text)"
    )
    discharge_date: Optional[str] = Field(
        None, description="Date of discharge if applicable"
    )


class VitalSigns(BaseModel):
    blood_pressure: Optional[str] = Field(None, description="e.g., '140/90 mmHg'")
    heart_rate_bpm: Optional[int] = Field(None, description="Pulse rate in bpm")
    respiratory_rate_bpm: Optional[int] = Field(None, description="Breaths per minute")
    temperature_celsius: Optional[float] = Field(None, description="Body temperature in °C")
    spo2_percentage: Optional[int] = Field(None, description="Oxygen saturation percentage", ge=0, le=100)


class LabBiomarker(BaseModel):
    test_name: str = Field(description="Name of lab test (e.g., Serum Potassium, Serum Creatinine, WBC)")
    observed_value: str = Field(description="Measured value with unit (e.g., '6.2 mEq/L', '18,500 /uL')")
    reference_range: Optional[str] = Field(None, description="Standard normal range (e.g., '3.5 - 5.0 mEq/L')")
    status: BiomarkerStatus = Field(
        default=BiomarkerStatus.NORMAL,
        description="Clinical flag indicator for this biomarker"
    )
    clinical_note: Optional[str] = Field(
        None, description="Brief note on clinical relevance or risk"
    )


class MedicationItem(BaseModel):
    drug_name: str = Field(description="Brand or generic name of medication")
    dosage: Optional[str] = Field(None, description="Dose and route (e.g., '10 mg PO')")
    frequency: Optional[str] = Field(None, description="e.g., 'Once daily at bedtime', 'TID'")
    status: str = Field(
        default="Continued",
        description="Status: 'New', 'Continued', 'Discontinued', or 'Adjusted'"
    )


class ClinicalRiskFlag(BaseModel):
    flag_title: str = Field(description="Concise name of the identified risk (e.g., 'Severe Hyperkalemia Risk', 'Sepsis Alert')")
    severity: UrgencyLevel = Field(description="Assigned severity level for triage")
    rationale: str = Field(description="Clinical reason explaining why this risk flag was triggered")
    source_quote: Optional[str] = Field(
        None, description="Verbatim text snippet from raw document confirming this finding"
    )


class ActionItem(BaseModel):
    priority: int = Field(description="Priority ranking (1 = Immediate/Highest)")
    action: str = Field(description="Recommended medical or administrative step")
    assigned_role: str = Field(
        default="Attending Physician",
        description="Target role: 'Attending Physician', 'Triage Nurse', 'Pharmacist', 'Care Coordinator'"
    )


class ClinicalIntelligenceReport(BaseModel):
    document_type: str = Field(
        description="Type of document (e.g., 'Discharge Summary', 'Lab Report', 'Emergency Intake', 'Consult Note')"
    )
    overall_urgency: UrgencyLevel = Field(
        description="Highest urgency level calculated across all clinical findings"
    )
    confidence_score: float = Field(
        description="Model confidence score in overall structured extraction (0.00 to 1.00)",
        ge=0.0,
        le=1.0
    )
    executive_summary: str = Field(
        description="2-3 sentence high-level summary written for clinical and administrative staff"
    )
    demographics: PatientDemographics
    vitals: Optional[VitalSigns] = None
    diagnoses: List[str] = Field(default_factory=list, description="Primary and secondary diagnosed conditions")
    lab_biomarkers: List[LabBiomarker] = Field(default_factory=list, description="Extracted lab tests and biomarker flags")
    medications: List[MedicationItem] = Field(default_factory=list, description="Active or reconciled medications")
    risk_flags: List[ClinicalRiskFlag] = Field(default_factory=list, description="Active medical and triage risk alerts")
    recommended_actions: List[ActionItem] = Field(default_factory=list, description="Prioritized clinical action plan")