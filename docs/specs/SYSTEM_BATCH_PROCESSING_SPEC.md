# SYSTEM_BATCH_PROCESSING_SPEC

## Purpose

Define the MVP contract for sequentially processing multiple jobs and producing a final report.

## Inputs

- CLI call with `--batch <jobs.csv>`
- one row or item per job

## Outputs

- one isolated workspace per generated `job_id`
- `output/batch_reports/latest_report.json`

## Required behavior

- Batch processing is sequential in the MVP.
- Each batch item must be converted into the same validated single-job contract used by normal execution.
- Each batch item must receive its own `job_id`.
- A failure in one batch item must not delete outputs from earlier successful items.
- The batch runner must continue to the next item after a failed item.
- The batch runner must produce one final report covering all attempted items.

## Batch report contract

`latest_report.json` must contain:

- `started_at`
- `finished_at`
- `total_jobs`
- `succeeded_jobs`
- `failed_jobs`
- `items`

Each `items` entry must contain:

- `job_id`
- `input_ref`
- `status`
- `output_file` or `null`
- `error_message` or `null`

## Failure conditions

- batch file is unreadable;
- a row cannot be parsed into a valid job;
- the report file cannot be written.

## Acceptance tests

- A batch with 3 valid items produces 3 job folders and a report with 3 successes.
- A batch with 2 valid items and 1 invalid item continues processing and reports 2 successes and 1 failure.
- Every report item contains `job_id`, `status`, and either an output path or error message.
