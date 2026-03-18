# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Patient handover agent tools."""

import concurrent.futures
import pathlib
import re
from datetime import datetime, timedelta
from typing import Any

import yaml 
from google import genai 
from google.adk.tools import ToolContext
from google.genai import types

yaml.add_representer(
    data_type=type(None),
    representer=lambda self, _: self.represent_scalar("tag:yaml.org,2002:null", ""),
)

PATIENT_FILE_DIR = pathlib.Path(__file__).parent / "data"

PATTERN = r"(\d{2}/\d{2}/\d{4})\^(\d{2}:\d{2}:\d{2})\^(.*)\^(.*)\^(.*)"
MEDICAL_ORDERS_TEXT = "MEDICATION ORDERS"
MED_ORDER_PATTERN = r"(.+)-(.+)-(.*)-(\d+) Day\(s\)-([^-]*)-(\d{2}/\d{2}/\d{4})"

CONFIG_DIR = pathlib.Path(__file__).parent / "configs"
ISBAR_YAML = CONFIG_DIR / "isbar_config.yaml"
SITUATION_TEMPLATE = CONFIG_DIR / "situation_template.txt"
ASSESSMENT_TEMPLATE = CONFIG_DIR / "assessment_template.txt"
ID_AND_BACKGROUND_TEMPLATE = CONFIG_DIR / "id_and_background_template.txt"
RECO_AND_TRANSFER_TEMPLATE = CONFIG_DIR / "reco_and_transfer_template.txt"
ISBAR_TEMPLATE = CONFIG_DIR / "isbar_template.txt"


GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=0,
    top_p=0.95,
    candidate_count=1,
    system_instruction="""You are an expert in medical journaling and have in depth experience in creating medical documentation of patients admitted at your hospital. You will be given medical notes entered by doctors and nurses in the hospital management software. You always create accurate documentation based on the facts and information provided to you and never miss capturing any critical information""",
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
    ],
)


class Summarizer:
    """Extracts and creates Summary"""

    def __init__(
        self,
        section_model: str,
        summary_model: str,
        client: genai.Client | None = None,
    ):
        self.client = client or genai.Client()
        self.section_model = section_model
        self.summary_model = summary_model
        self.generation_config = GENERATION_CONFIG

        self.situation_prompt = SITUATION_TEMPLATE.read_text()
        self.assessment_prompt = ASSESSMENT_TEMPLATE.read_text()
        self.id_and_background_prompt = ID_AND_BACKGROUND_TEMPLATE.read_text()
        self.reco_and_transfer_prompt = RECO_AND_TRANSFER_TEMPLATE.read_text()
        self.isbar_prompt = ISBAR_TEMPLATE.read_text()

        with open(ISBAR_YAML, "r") as file:
            yaml_file = yaml.safe_load(file)
            identification_list = yaml.dump(yaml_file["identification"], indent=2)
            situation_list = yaml.dump(yaml_file["situation"], indent=2)
            background_list = yaml.dump(yaml_file["background"], indent=2)
            assessment_list = yaml.dump(yaml_file["assessment"], indent=2)
            recommendation_list = yaml.dump(yaml_file["recommendation"], indent=2)
            transfer_list = yaml.dump(yaml_file["patient_transfer"], indent=2)

        self.situation_prompt = self.situation_prompt.format("{}", "{}", situation_list)
        self.assessment_prompt = self.assessment_prompt.format("{}", assessment_list)
        self.id_and_background_prompt = self.id_and_background_prompt.format(
            "{}", identification_list, background_list
        )
        self.reco_and_transfer_prompt = self.reco_and_transfer_prompt.format(
            "{}", recommendation_list, transfer_list
        )

    def _find_nearest_timestamp(
        self,
        data: dict[datetime, str],
        target_datetime: datetime,
    ) -> datetime | None:
        """
        Finds the key in a dictionary with datetime objects as keys that is
        closest to a given target datetime.

        Args:
          data: A dictionary with datetime objects as keys.
          target_datetime: The target datetime object.

        Returns:
          The datetime object from the dictionary's keys that is closest to
          the target_datetime, or None if the dictionary is empty.
        """

        if not data:
            return None  # Handle empty dictionary case

        # Calculate time differences and store in a list of tuples (datetime, difference)
        time_diffs = [(dt, abs(dt - target_datetime)) for dt in data.keys()]

        # Sort by time difference
        time_diffs.sort(key=lambda item: item[1])

        # Return the datetime object with the smallest difference
        return time_diffs[0][0]

    def _extract_log_times(self) -> dict[datetime, str]:
        dt_dict = {}
        matches = re.finditer(PATTERN, self.document)
        for match in matches:
            date = match.group(1)
            time = match.group(2)
            start_pos = match.start()
            end_pos = match.end()
            datetime_str = f"{date} {time}"
            datetime_object = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M:%S")
            dt_dict[datetime_object] = self.document[start_pos:end_pos]
        return dt_dict

    def _extract_med_orders(self) -> list[dict[str, str]]:
        split_texts = self.document.split(MEDICAL_ORDERS_TEXT)
        med_text = split_texts[1].strip()
        med_text_lines = med_text.split("\n")
        # med_text_lines

        med_order_data = []
        for line in med_text_lines:
            match = re.match(MED_ORDER_PATTERN, line)
            if match:
                # print(match.groups())
                # fields = re.split(pattern, line)
                order = {
                    "Drug/Generic Item": match.group(1).strip(),
                    "Frequency": match.group(2).strip(),
                    "Instructions/Notes": match.group(3).strip(),
                    "Duration": match.group(4).strip(),
                    "OrderedBy": match.group(5).strip(),
                    "OrderedDate": match.group(6).strip(),
                }
                med_order_data.append(order)
        return med_order_data

    def _filter_by_order_date(
        self,
        data: list[dict[str, str]],
        target_date: str,
    ) -> list[dict[str, str]]:
        """
        Filters a list of dictionaries based on the 'OrderedDate' key,
        returning items with OrderedDate less than or equal to the target_date.

        Args:
            data: A list of dictionaries, where each dictionary represents an item
                with an 'OrderedDate' key.
            target_date: The date to filter by, in the format 'DD/MM/YYYY'.

        Returns:
            A new list containing only the dictionaries where 'OrderedDate' is
            less than or equal to the target_date.
        """
        filtered_data = []
        target_date_dt = datetime.strptime(target_date, "%Y-%m-%d")
        order_start_dt = target_date_dt - timedelta(days=2)
        for item in data:
            # Convert dates to datetime objects for comparison
            item_date = datetime.strptime(item["OrderedDate"], "%d/%m/%Y")
            if item_date <= target_date_dt and item_date >= order_start_dt:
                filtered_data.append(item)
        return filtered_data

    def _get_context(
        self,
        dt_dict: dict[datetime, str],
        start_dt: datetime,
        end_dt: datetime,
    ) -> str:
        nn_start = self._find_nearest_timestamp(dt_dict, start_dt)
        assert nn_start, "Start time not found in log times"

        nn_end = self._find_nearest_timestamp(dt_dict, end_dt)
        assert nn_end, "End time not found in log times"

        start_time_string = dt_dict[nn_start]
        end_time_string = dt_dict[nn_end]
        context_data = (
            self.document.split(start_time_string)[1].split(end_time_string)[0].strip()
        )
        return context_data

    def generate(
        self,
        patient: str,
        start_time: datetime,
        end_time: datetime,
    ) -> types.GenerateContentResponse:
        """Extracts invoice information from a PDF file.

        Args:
            start_time: The start time of the shift.
            end_time: The end time of the shift.

        Returns:
            genai.types.GenerateContentResponse: A response object containing the shift summary.
        """

        # with open(file_path, "r") as txt_file:
        #     self.document = txt_file.read()
        self.document = patient

        with concurrent.futures.ThreadPoolExecutor() as executor:
            log_times_future = executor.submit(self._extract_log_times)
            med_orders_future = executor.submit(self._extract_med_orders)

            log_times = log_times_future.result()
            med_orders = med_orders_future.result()

        time_bound_document = self._get_context(log_times, start_time, end_time)
        end_date = str(end_time.date())

        time_bound_med_orders = self._filter_by_order_date(med_orders, end_date)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = executor.map(
                lambda prompt: self.client.models.generate_content(
                    model=self.section_model,
                    contents=prompt,
                    config=self.generation_config,
                ),
                [
                    self.id_and_background_prompt.format(self.document),
                    self.situation_prompt.format(
                        time_bound_document, time_bound_med_orders
                    ),
                    self.assessment_prompt.format(time_bound_document),
                    self.reco_and_transfer_prompt.format(time_bound_document),
                ],
            )
            id_and_background, situation, assessment, reco_and_transfer = tuple(futures)

        final_summary = self.client.models.generate_content(
            model=self.summary_model,
            contents=self.isbar_prompt.format(
                situation_text=situation.text,
                assessment_text=assessment.text,
                id_and_background_text=id_and_background.text,
                reco_and_transfer_text=reco_and_transfer.text,
                start_time=start_time,
                end_time=end_time,
            ),
            config=self.generation_config,
        )

        return final_summary


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

    patients = [x['name'].rsplit('/', 1)[1].replace('.txt', '') for x in tool_context.state.get("patients")]

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
    patients = [x['name'].rsplit('/', 1)[1].replace('.txt', '') for x in tool_context.state.get("patients")]
    if not any(pid == patient for pid in patients):
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

    summarizer = Summarizer(
        section_model=tool_context.state["section_model"],
        summary_model=tool_context.state["summary_model"],
        client=genai.Client(),
    )
# this is going to be hard
    # patient_file = PATIENT_FILE_DIR / f"{patient}.txt"

    inputs_filename = f"{patient}-{int(start_dt.timestamp())}-{int(end_dt.timestamp())}-raw-inputs.txt"
    _ = await tool_context.save_artifact(
        inputs_filename,
        # artifact=tool_context.load_artifact("patient_data")
        artifact=types.Part(text=tool_context.state.get("patient_data"))
        # artifact=types.Part.from_bytes(
        #     data=patient_file.read_text().encode(),
        #     mime_type="text/plain",
        # ),
    )

    summary_content = summarizer.generate(
        # file_path=tool_context.load_artifact(patient),
        patient = tool_context.state.get("patient_data"),
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