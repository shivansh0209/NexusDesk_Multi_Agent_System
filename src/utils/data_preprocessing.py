import json
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_CONFIG = {
    "company_policies": {
        "content_fields": ["content"]
    },
    "customer_profiles": {
        "content_fields": ["notes"]
    },
    "resolved_tickets": {
        "content_fields": ["reformulated_query", "resolution"]
    },
    "test_queries": None
}



def build_content(data: dict, content_fields: list) -> str:
    parts = []
    for field in content_fields:
        value = data.get(field)
        if value is None:
            continue
        if isinstance(value, list):
            parts.append(", ".join(str(v) for v in value))
        else:
            parts.append(str(value))
    return " | ".join(parts)


def preprocess_file(file_path: Path, content_fields: list) -> list:
    normalized = []
    try:
        with open(file_path, "r") as f:
            records = json.loads(f.read())

        for record in records:
            try:
                content = build_content(record, content_fields)
                if not content.strip():
                    logger.error(f"Empty content built for record ID {record.get('id')} in {file_path.name}. Skipping.")
                    continue

                normalized_record = {
                    "id": record["id"],
                    "content": content,
                    "metadata": {
                        field: json.dumps(record[field]) if isinstance(record[field], list) else record[field]
                        for field in record
                        if field not in content_fields and field != "id"
                    }
                }
                normalized.append(normalized_record)

            except Exception as e:
                logger.error(f"Error processing record ID {record.get('id', 'UNKNOWN')} in {file_path.name}: {e}")

    except Exception as e:
        logger.error(f"Error reading file {file_path.name}: {e}")

    return normalized


def preprocess_all(path_to_data: str, path_to_output: str):
    try:
        folder_path = Path(path_to_data)
        output_path = Path(path_to_output)
        output_path.mkdir(parents=True, exist_ok=True)

        for file_name in folder_path.iterdir():
            if not file_name.is_file():
                continue

            collection_name = file_name.stem
            config = SCHEMA_CONFIG.get(collection_name)

            if config is None:
                logger.info(f"Skipping {file_name.name} — marked as no-embed in config.")
                continue

            logger.info(f"Preprocessing {file_name.name}...")
            normalized = preprocess_file(file_name, config["content_fields"])

            if not normalized:
                logger.error(f"No valid records produced from {file_name.name}. Skipping output.")
                continue

            out_file = output_path / file_name.name
            with open(out_file, "w") as f:
                json.dump(normalized, f, indent=2)

            logger.info(f"Saved {len(normalized)} normalized records to {out_file}.")

    except Exception as e:
        logger.error(f"Critical error in preprocess_all: {e}")
    else:
        logger.info("Preprocessing completed successfully.")


if __name__ == "__main__":
    preprocess_all("data/knowledge_base", "data/processed")