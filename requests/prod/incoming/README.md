# Production intake drop zone

This folder is the landing area for JSON files coming from your intake/request system.

## Where JSON files should land

- Drop all approved production request payloads in this folder:
  - `requests/prod/incoming/`

## Naming convention

Use one file per request with a stable, sortable name:

- `request-<yyyyMMdd>-<ticket-or-request-id>.json`
- Example: `request-20260629-CHG123456.json`

## Processing flow

1. Intake system writes a validated request JSON into `requests/prod/incoming/`.
2. GitHub Actions workflow `.github/workflows/process-intake-requests.yml` detects changed JSON files and runs the generator script.
3. Script validates the payload against the request schema and generates `examples/prod/terraform.tfvars`.
4. Terraform plan/apply runs from `examples/prod`.

## GitHub Actions output

- Workflow run uploads generated files as artifact: `generated-tfvars`
- Each request file produces one matching output file: `<request-name>.tfvars`

## Example command

```powershell
python .\scripts\generate_tfvars.py `
  --schema .\schemas\subscription-vending.request.schema.json `
  --request .\requests\prod\incoming\request-20260629-CHG123456.json `
  --out .\examples\prod\terraform.tfvars
```

## Operational notes

- Keep exactly one request per file.
- Archive or remove processed files after successful deployment to avoid accidental re-processing.
- Keep secrets out of request payloads; use IDs/references only.
