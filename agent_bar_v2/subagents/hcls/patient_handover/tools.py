"""Nurse handover agent tools."""

import pathlib
from datetime import datetime
from typing import Any

from google import genai
from google.adk.tools import ToolContext
from google.genai import types

from agents.nurse_handover import summary

PATIENT_FILE_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "data"


def list_available_shifts(tool_context: ToolContext) -> dict[str, Any]:
    """List all active shifts for the authenticated nurse.

    Returns:
        A list of shift dates and times.
    """

    shifts = tool_context.state.get("shifts")

    if shifts is None:
        return {"error": "No shifts found."}

    return {"success": "Shifts found.", "shifts": shifts}


def list_patients(tool_context: ToolContext) -> dict[str, Any]:
    """List all patients of the authenticated nurse.

    Returns:
        A list of patient IDs.
    """

    patients = tool_context.state.get("patients")

    if patients is None:
        return {"error": "No patients found."}

    return {"success": "Patients found.", "patients": patients}


async def generate_shift_endorsement(
    patient: str,
    start_time: str,
    end_time: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Generate a shift endorsement report for the given shift.

    Args:
        patient: The ID of the patient.
        start_time: The start time of the shift. Adhere to isoformat without any timezone, e.g. YYYY-MM-DDTHH:MM:SS
        end_time: The end time of the shift. Adhere to isoformat without any timezone, e.g. YYYY-MM-DDTHH:MM:SS

    Returns:
        The generated shift endorsement report.
    """

    if not any(pid == patient for pid in tool_context.state.get("patients", [])):
        return {"error": f"Patient not found: {patient}"}

    start_dt, end_dt = (
        datetime.fromisoformat(start_time),
        datetime.fromisoformat(end_time),
    )
    if not any(
        start_dt == datetime.fromisoformat(shift["start_time"])
        and end_dt == datetime.fromisoformat(shift["end_time"])
        for shift in tool_context.state.get("shifts", [])
    ):
        return {"error": f"Shift not found: {start_dt} - {end_dt}"}

    summarizer = summary.Summarizer(
        section_model=tool_context.state["section_model"],
        summary_model=tool_context.state["summary_model"],
        client=genai.Client(),
    )

    patient_file = PATIENT_FILE_DIR / f"{patient}.txt"

    inputs_filename = f"{patient}-{int(start_dt.timestamp())}-{int(end_dt.timestamp())}-raw-inputs.txt"
    _ = await tool_context.save_artifact(
        inputs_filename,
        artifact=types.Part.from_bytes(
            data=patient_file.read_text().encode(),
            mime_type="text/plain",
        ),
    )

    summary_content = summarizer.generate(
        file_path=patient_file,
        start_time=start_dt,
        end_time=end_dt,
    )

    if not (summary_report := summary_content.text):
        return {
            "error": "No summary generated.",
            "response": summary_content.model_dump(mode="json", exclude_none=True),
        }

    endorsement_filename = f"{patient}-{int(start_dt.timestamp())}-{int(end_dt.timestamp())}-endorsement.md"
    _ = await tool_context.save_artifact(
        endorsement_filename,
        artifact=types.Part.from_bytes(
            data=summary_report.encode(),
            mime_type="text/markdown",
        ),
    )

    return {
        "success": "Summary generated successfully. Please inform the user about the raw inputs and endorsement files. Raw inputs contains all of the source patient data used for the endorsement report.",
        "raw_inputs_file": inputs_filename,
        "endorsement_file": endorsement_filename,
        "report_content": summary_report,
    }