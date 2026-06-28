variable "workload_name" {
  type        = string
  description = "Workload short name, used in naming and tags."

  validation {
    condition     = can(regex("^[a-z0-9-]{2,24}$", var.workload_name))
    error_message = "workload_name must be 2-24 chars and use lowercase letters, numbers, or dashes."
  }
}

variable "environment" {
  type        = string
  description = "Environment tier: dev, test, or prod."

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be one of: dev, test, prod."
  }
}

variable "owner" {
  type        = string
  description = "Owner alias or email used in governance tags and budget notifications."
}

variable "cost_center" {
  type        = string
  description = "Cost center value used for governance and FinOps reporting."

  validation {
    condition     = can(regex("^[A-Z0-9-]{2,20}$", var.cost_center))
    error_message = "cost_center must be 2-20 chars and use uppercase letters, numbers, or dashes."
  }
}

variable "connectivity_model" {
  type        = string
  description = "Connectivity model applied at vending time: none, hub_spoke, or vwan."

  validation {
    condition     = contains(["none", "hub_spoke", "vwan"], var.connectivity_model)
    error_message = "connectivity_model must be one of: none, hub_spoke, vwan."
  }
}

variable "location" {
  type        = string
  description = "Default location for module resources."
}

variable "subscription_billing_scope" {
  type        = string
  description = "Billing scope used when creating the subscription alias."
}

variable "subscription_management_group_id" {
  type        = string
  description = "Target management group ID for subscription placement."
}

variable "subscription_workload" {
  type        = string
  description = "Subscription workload type for Azure billing metadata."
  default     = "Production"

  validation {
    condition     = contains(["Production", "DevTest"], var.subscription_workload)
    error_message = "subscription_workload must be Production or DevTest."
  }
}

variable "hub_network_resource_id" {
  type        = string
  description = "Hub VNet resource ID for hub-spoke connectivity. Required when connectivity_model is hub_spoke."
  default     = null
}

variable "vwan_hub_resource_id" {
  type        = string
  description = "vWAN hub resource ID for virtual WAN connectivity. Required when connectivity_model is vwan."
  default     = null
}

variable "spoke_address_space" {
  type        = list(string)
  description = "Address spaces for the vended spoke VNet."
  default     = ["10.140.0.0/24"]
}

variable "spoke_subnet_prefixes" {
  type        = list(string)
  description = "Subnet prefixes for the workload subnet in the spoke VNet."
  default     = ["10.140.0.0/26"]
}

variable "owner_principal_id" {
  type        = string
  description = "Object ID for the workload owner role assignment."
}

variable "platform_ops_group_object_id" {
  type        = string
  description = "Object ID for platform operations role assignment."
}

variable "budget_amount" {
  type        = number
  description = "Budget amount for the vended subscription."
}

variable "budget_time_grain" {
  type        = string
  description = "Budget time grain: Monthly, Quarterly, or Annually."
  default     = "Monthly"

  validation {
    condition     = contains(["Monthly", "Quarterly", "Annually"], var.budget_time_grain)
    error_message = "budget_time_grain must be Monthly, Quarterly, or Annually."
  }
}

variable "budget_start_date" {
  type        = string
  description = "RFC3339 UTC start date for the budget, e.g. 2026-01-01T00:00:00Z."
}

variable "budget_end_date" {
  type        = string
  description = "RFC3339 UTC end date for the budget, e.g. 2028-12-31T23:59:59Z."
}

variable "budget_contact_emails" {
  type        = list(string)
  description = "Email recipients for budget alerts."
}

variable "budget_threshold_percent" {
  type        = number
  description = "Budget notification threshold percentage."
  default     = 80
}

variable "additional_subscription_tags" {
  type        = map(string)
  description = "Additional tags merged with the required vending tags."
  default     = {}
}

variable "policy_assignments" {
  description = "Policy and initiative assignments created at subscription scope after vending."
  type = map(object({
    name                 = string
    policy_definition_id = string
    display_name         = optional(string)
    description          = optional(string)
    enforcement_mode     = optional(string, "Default")
    parameters           = optional(map(any), {})
    identity_type        = optional(string)
    identity_ids         = optional(list(string), [])
    location             = optional(string)
  }))
  default = {}
}
