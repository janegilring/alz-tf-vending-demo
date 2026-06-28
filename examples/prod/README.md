# Terraform Landing Zone Vending (prod example)

This example implements a subscription vending contract with `Azure/avm-ptn-alz-sub-vending/azure` and applies the following during creation:

- Subscription placement in the target management group
- Subscription-level RBAC assignments
- Subscription budget and notifications
- Required governance tags plus custom tags
- Subscription-level policy scope via policy assignments

## Required contract inputs

- `workload_name`
- `environment`
- `owner`
- `cost_center`
- `connectivity_model` (`none`, `hub_spoke`, `vwan`)

## Usage

1. Copy `terraform.tfvars.example` to `terraform.tfvars` and update values.
2. Run the workflow:

```powershell
terraform init
terraform validate
terraform plan
terraform apply -auto-approve
```

## Connectivity model behavior

- `none`: no virtual network resources are deployed.
- `hub_spoke`: creates a spoke VNet and peers it to `hub_network_resource_id`.
- `vwan`: creates a spoke VNet and connects it to `vwan_hub_resource_id`.

## Contract schema

The JSON schema for the request contract is at:

- `../../schemas/subscription-vending.request.schema.json`

Use it in your request pipeline to validate incoming subscription requests before creating `tfvars` files.
