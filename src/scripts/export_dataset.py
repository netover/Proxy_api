#!/usr/bin/env python3
"""
Dataset Export Script for Fine-tuning

This script exports datasets from log files in JSONL format suitable for fine-tuning AI models.
It processes log entries, extracts conversation data, and formats them for training.

Usage:
    python -m src.scripts.export_dataset --log-file logs/app.log --output dataset.jsonl
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.logging import ContextualLogger, setup_logging
from src.services.logging import iterate_logs, validate_record

logger = ContextualLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments with environment variable defaults."""
    parser = argparse.ArgumentParser(
        description="Export datasets from log files for fine-tuning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.scripts.export_dataset --log-file logs/app.log --output dataset.jsonl
  python -m src.scripts.export_dataset --log-file logs/app.log --output dataset.jsonl --max-records 1000 --successful-only

Environment Variables:
  PROXY_API_EXPORT_DEFAULT_LOG_FILE    Default log file path
  PROXY_API_EXPORT_DEFAULT_OUTPUT_DIR  Default output directory
  PROXY_API_EXPORT_DEFAULT_OUTPUT_FILE Default output filename
  PROXY_API_EXPORT_MAX_RECORDS         Maximum records to export
  PROXY_API_EXPORT_SUCCESSFUL_ONLY     Export only successful records (true/false)
  PROXY_API_EXPORT_EXPORT_ALL          Export all records (true/false)
  PROXY_API_EXPORT_START_DATE          Start date filter
  PROXY_API_EXPORT_END_DATE            End date filter
  PROXY_API_EXPORT_MODEL_FILTER        Model filter
  PROXY_API_EXPORT_LOG_LEVEL           Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        """,
    )

    # Set default output path from environment variables
    default_output = (
        settings.export_default_output_dir
        / settings.export_default_output_file
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        default=settings.export_default_log_file,
        help=f"Path to the log file to process (default: {settings.export_default_log_file})",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Output file path for the JSONL dataset (default: {default_output})",
    )

    parser.add_argument(
        "--max-records",
        type=int,
        default=settings.export_max_records,
        help=f"Maximum number of records to export (default: {settings.export_max_records or 'all'})",
    )

    parser.add_argument(
        "--successful-only",
        action="store_true",
        default=settings.export_successful_only,
        help=f"Export only successful completion records (default: {settings.export_successful_only})",
    )

    parser.add_argument(
        "--export-all",
        action="store_true",
        default=settings.export_export_all,
        help=f"Export all valid log records (not just conversations) (default: {settings.export_export_all})",
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default=settings.export_start_date,
        help=f"Start date for filtering records (ISO format: YYYY-MM-DDTHH:MM:SS) (default: {settings.export_start_date})",
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default=settings.export_end_date,
        help=f"End date for filtering records (ISO format: YYYY-MM-DDTHH:MM:SS) (default: {settings.export_end_date})",
    )

    parser.add_argument(
        "--model-filter",
        type=str,
        default=settings.export_model_filter,
        help=f"Filter records by specific model name (default: {settings.export_model_filter})",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (overrides PROXY_API_EXPORT_LOG_LEVEL)",
    )

    return parser.parse_args()


def validate_date(date_str: str) -> datetime:
    """Validate and parse ISO date string."""
    try:
        # Handle timezone-aware dates
        if "Z" in date_str:
            date_str = date_str.replace("Z", "+00:00")
        elif (
            "+" not in date_str and "-" not in date_str[-6:]
        ):  # No timezone info
            date_str += "+00:00"  # Assume UTC if no timezone

        dt = datetime.fromisoformat(date_str)
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: {date_str}. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
        ) from e


def filter_record_by_date(
    record: Dict[str, Any],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> bool:
    """Filter record based on timestamp."""
    if not start_date and not end_date:
        return True

    timestamp_str = record.get("timestamp")
    if not timestamp_str:
        return False

    try:
        if "Z" in timestamp_str:
            timestamp_str = timestamp_str.replace("Z", "+00:00")
        record_date = datetime.fromisoformat(timestamp_str)

        if start_date and record_date < start_date:
            return False
        if end_date and record_date > end_date:
            return False

        return True
    except (ValueError, AttributeError):
        logger.warning(f"Invalid timestamp in record: {timestamp_str}")
        return False


def filter_record_by_model(
    record: Dict[str, Any], model_filter: Optional[str]
) -> bool:
    """Filter record based on model name."""
    if not model_filter:
        return True

    # Check in extra_data first
    extra_data = record.get("extra_data", {})
    if isinstance(extra_data, dict):
        model = extra_data.get("model")
        if model and model_filter.lower() in model.lower():
            return True

    # Check in message
    message = record.get("message", "").lower()
    if model_filter.lower() in message:
        return True

    return False


def extract_conversation_data(
    record: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Extract conversation data from a log record for fine-tuning."""
    extra_data = record.get("extra_data", {})

    # Extract messages and response
    messages = extra_data.get("messages", [])
    response = extra_data.get("response", "")

    if messages and response:
        # Format for fine-tuning (OpenAI chat format)
        conversation = {
            "messages": messages + [{"role": "assistant", "content": response}]
        }

        # Add metadata
        conversation["metadata"] = {
            "timestamp": record.get("timestamp"),
            "model": extra_data.get("model"),
            "provider": extra_data.get("provider"),
            "response_time": extra_data.get("response_time"),
            "tokens": extra_data.get("tokens"),
        }

        return conversation

    return None


def extract_general_log_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract general log data for export."""
    extra_data = record.get("extra_data", {})

    # Create a general log entry
    log_entry = {
        "timestamp": record.get("timestamp"),
        "level": record.get("level"),
        "logger": record.get("logger"),
        "message": record.get("message"),
        "module": record.get("module"),
        "function": record.get("function"),
        "line": record.get("line"),
    }

    # Add extra data if present
    if extra_data:
        log_entry["extra_data"] = extra_data

    return log_entry


def export_dataset(args: argparse.Namespace) -> None:
    """Main export function."""
    # Setup logging - use verbose flag to override environment variable
    if args.verbose:
        log_level = "DEBUG"
    else:
        log_level = settings.export_log_level

    setup_logging(log_level)

    logger.info(
        "Starting dataset export",
        log_file=str(args.log_file),
        output=str(args.output),
    )

    # Validate inputs
    if not args.log_file.exists():
        logger.warning(
            f"Log file does not exist: {args.log_file}. Using default or checking if it should be created."
        )
        # For now, we'll still raise an error but could be made more flexible
        raise FileNotFoundError(f"Log file does not exist: {args.log_file}")

    # Parse date filters
    start_date = None
    end_date = None
    if args.start_date:
        start_date = validate_date(args.start_date)
    if args.end_date:
        end_date = validate_date(args.end_date)

    # Create output directory if needed
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Collect records
    records = []
    total_processed = 0
    filtered_count = 0

    logger.info("Processing log file...")

    # Use tqdm for progress if available
    if tqdm and args.max_records:
        progress_bar = tqdm(total=args.max_records, desc="Processing records")
    elif tqdm:
        progress_bar = tqdm(desc="Processing records")
    else:
        progress_bar = None

    try:
        for record in iterate_logs(args.log_file, args.max_records):
            total_processed += 1

            if progress_bar:
                progress_bar.update(1)

            # Validate record
            if not validate_record(record):
                continue

            # Apply filters
            if not filter_record_by_date(record, start_date, end_date):
                filtered_count += 1
                continue

            if not filter_record_by_model(record, args.model_filter):
                filtered_count += 1
                continue

            # Extract data based on export mode
            if args.export_all:
                # Export all valid records
                log_data = extract_general_log_data(record)
                records.append(log_data)
            else:
                # Extract only conversation data
                conversation = extract_conversation_data(record)
                if conversation:
                    records.append(conversation)
                else:
                    filtered_count += 1

            # Check max records limit
            if args.max_records and len(records) >= args.max_records:
                break

    except Exception as e:
        logger.error(f"Error processing log file: {e}")
        raise
    finally:
        if progress_bar:
            progress_bar.close()

    # Filter successful records if requested
    if args.successful_only:
        logger.info("Filtering for successful records...")
        original_count = len(records)
        records = [
            r
            for r in records
            if any(
                indicator in json.dumps(r).lower()
                for indicator in [
                    "successful",
                    "completed",
                    "success",
                    "ok",
                    "200",
                ]
            )
        ]
        filtered_count += original_count - len(records)

    # Write to JSONL file
    logger.info(f"Writing {len(records)} records to {args.output}")

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            for record in records:
                json.dump(record, f, ensure_ascii=False)
                f.write("\n")
    except Exception as e:
        logger.error(f"Error writing to output file: {e}")
        raise

    # Summary
    logger.info(
        "Export completed successfully",
        **{
            "total_processed": total_processed,
            "exported_records": len(records),
            "filtered_records": filtered_count,
            "output_file": str(args.output),
        },
    )


def main():
    """Main entry point."""
    try:
        args = parse_arguments()
        export_dataset(args)
    except KeyboardInterrupt:
        logger.info("Export interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
