output "subscription_id" {
  description = "The vended subscription ID."
  value       = module.lz_vending.subscription_id
}

output "subscription_resource_id" {
  description = "The vended subscription resource ID."
  value       = module.lz_vending.subscription_resource_id
}

output "management_group_association_id" {
  description = "Management group association ID for placement verification."
  value       = module.lz_vending.management_group_subscription_association_id
}

output "budget_ids" {
  description = "Budget resource IDs created during vending."
  value       = module.lz_vending.budget_resource_id
}
