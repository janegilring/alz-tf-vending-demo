# Request Validation and tfvars Generation

Use this script to validate a subscription vending request against the contract and generate `terraform.tfvars` for the prod example.

## Input files

- Request schema: `../schemas/subscription-vending.request.schema.json`
- Sample request: `../requests/request.prod.example.json`
- Production intake drop zone: `../requests/prod/incoming/`

## Command

```powershell
python .\scripts\generate_tfvars.py `
  --schema .\schemas\subscription-vending.request.schema.json `
  --request .\requests\prod\incoming\request-20260629-CHG123456.json `
  --out .\examples\prod\terraform.tfvars
```

## What this does

- Validates required request fields and key constraints used by the vending contract
- Enforces connectivity-specific requirements
- Generates a `terraform.tfvars` file compatible with the files under `examples/prod`

## Notes

- The script uses only Python standard library modules.
- If validation fails, the script exits with a clear error describing the failing field.
