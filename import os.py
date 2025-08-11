import os

ENABLE_ENCOUNTER_TYPE = os.getenv("ENABLE_ENCOUNTER_TYPE", "false").lower() == "true"

...

if ENABLE_ENCOUNTER_TYPE:
    for type in resource.get("type", []):
        for coding in type.get("coding", []):
            encounter_type = pgEncounterType(
                ...
            )
            encounter_objects.append(encounter_type)
