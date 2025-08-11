"""
Given an array of pgEncounter objects, convert them to mongo Encounter objects
"""
import datetime as dt
import logging
IndexModel
Added a new line
from azure.storage.blob import BlobServiceClient

from pymongo import ASCENDING, IndexModel
from rhythmx.helpers.azure_config import get_conf_value_withcred, try_get_credential
from rhythmx.helpers.rx_db_models.rx_db_models.rxcdm.models import Encounter as mEncounter, DataSourceEnum
from rhythmx.helpers.clarity.common import convert_dt_str, stripstr_or_none, get_flexenum

azlogger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
azlogger.setLevel(logging.WARNING)

async def convert_encounters(pg_objects_arr, rx_patient_id):
    m_encounters = []
    converted_pg_objects = []

    CDC_VAL_MAP = {'U': 'cdc_u', 'I': 'cdc_i'}
    today_dt_str = dt.datetime.now(dt.UTC).strftime("'%Y%m%d'")

    for pg_encounter in pg_objects_arr:
        thistags = [today_dt_str]
        cdc_tag = CDC_VAL_MAP.get(pg_encounter.CDC)
        if cdc_tag:
            thistags.append(cdc_tag)

        # Step 1: Extract reasonCode safely from the pg_encounter
        reason_codes = []

        try:
            raw_rc = getattr(pg_encounter, 'REASON_CODE', None)
            if raw_rc:
                if isinstance(raw_rc, str):  # If it comes as a JSON string
                    import json
                    raw_rc = json.loads(raw_rc)

                for rc in raw_rc:
                    coding = rc.get("coding", [])
                    if coding:
                        reason_codes.append({
                            "system": coding[0].get("system"),
                            "code": coding[0].get("code"),
                            "display": coding[0].get("display")
                        })
                    elif rc.get("text"):
                        reason_codes.append({"text": rc.get("text")})
        except Exception as e:
            logging.warning(f"Failed to parse reasonCode for Encounter {pg_encounter.ENCOUNTER_ID}: {e}")

        m_encounter = mEncounter(
            fhir_id=stripstr_or_none(pg_encounter.FHIR_ID),
            encounter_id=stripstr_or_none(pg_encounter.ENCOUNTER_ID),
            encounter_fhir_id=stripstr_or_none(pg_encounter.FHIR_ID),
            encounter_csn=stripstr_or_none(pg_encounter.ENCOUNTER_CSN),
            status=stripstr_or_none(pg_encounter.STATUS),
            patient_id=patient_id
            rx_patient_id=rx_patient_id,
            practitioner_id=stripstr_or_none(pg_encounter.PRACTITIONER_ID),
            practitioner_display=stripstr_or_none(pg_encounter.PRACTITIONER_DISPLAY),
            specialty=stripstr_or_none(pg_encounter.SPECIALTY),
            location_id=stripstr_or_none(pg_encounter.LOCATION_ID),
            start_dt=convert_dt_str(pg_encounter.START_DT),
            end_dt=convert_dt_str(pg_encounter.END_DT),
            encounter_type=stripstr_or_none(pg_encounter.ENCOUNTER_TYPE),
            service_type=stripstr_or_none(pg_encounter.SERVICE_TYPE),
            class_display=stripstr_or_none(pg_encounter.CLASS_DISPLAY),
            class_code=stripstr_or_none(pg_encounter.CLASS_CODE),
            class_system=stripstr_or_none(pg_encounter.CLASS_SYSTEM),
            tags=thistags,
            data_source=DataSourceEnum.fhir,
            reason_code=reason_codes,

        )

        m_encounters.append(m_encounter)
        converted_pg_objects.append(pg_encounter)

    return m_encounters, converted_pg_objects
