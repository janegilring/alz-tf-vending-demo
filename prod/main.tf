locals {
  subscription_name = format("sub-%s-%s", var.workload_name, var.environment)

  required_tags = {
    workload_name = var.workload_name
    environment   = var.environment
    owner         = var.owner
    cost_center   = var.cost_center
    connectivity  = var.connectivity_model
    managed_by    = "platform-vending"
  }

  subscription_tags = merge(local.required_tags, var.additional_subscription_tags)

  virtual_network_enabled = var.connectivity_model != "none"

  virtual_networks = local.virtual_network_enabled ? {
    spoke = {
      name          = format("vnet-%s-%s", var.workload_name, var.environment)
      address_space = var.spoke_address_space
      location      = var.location

      subnets = {
        workload = {
          name             = "snet-workload"
          address_prefixes = var.spoke_subnet_prefixes
        }
      }

      hub_peering_enabled     = var.connectivity_model == "hub_spoke"
      hub_network_resource_id = var.connectivity_model == "hub_spoke" ? var.hub_network_resource_id : null

      vwan_connection_enabled = var.connectivity_model == "vwan"
      vwan_hub_resource_id    = var.connectivity_model == "vwan" ? var.vwan_hub_resource_id : null
    }
  } : {}

  role_assignments = {
    workload_owner = {
      principal_id   = var.owner_principal_id
      definition     = "Owner"
      relative_scope = ""
      principal_type = "Group"
    }
    platform_reader = {
      principal_id   = var.platform_ops_group_object_id
      definition     = "Reader"
      relative_scope = ""
      principal_type = "Group"
    }
  }

  budgets = {
    primary = {
      name              = format("budget-%s-%s", var.workload_name, var.environment)
      amount            = var.budget_amount
      time_grain        = var.budget_time_grain
      time_period_start = var.budget_start_date
      time_period_end   = var.budget_end_date
      notifications = {
        threshold = {
          enabled        = true
          operator       = "GreaterThan"
          threshold      = var.budget_threshold_percent
          threshold_type = "Actual"
          contact_emails = var.budget_contact_emails
        }
      }
    }
  }
}

module "lz_vending" {
  source  = "Azure/avm-ptn-alz-sub-vending/azure"
  version = "~> 0.2.1"

  location = var.location

  subscription_alias_enabled = true
  subscription_alias_name    = local.subscription_name
  subscription_display_name  = local.subscription_name
  subscription_billing_scope = var.subscription_billing_scope
  subscription_workload      = var.subscription_workload

  subscription_management_group_association_enabled = true
  subscription_management_group_id                  = var.subscription_management_group_id

  subscription_tags = local.subscription_tags

  role_assignment_enabled = true
  role_assignments        = local.role_assignments

  budget_enabled = true
  budgets        = local.budgets

  virtual_network_enabled = local.virtual_network_enabled
  virtual_networks        = local.virtual_networks
}

resource "azurerm_subscription_policy_assignment" "policy_scope" {
  for_each = var.policy_assignments

  name                 = each.value.name
  subscription_id      = module.lz_vending.subscription_id
  policy_definition_id = each.value.policy_definition_id
  display_name         = coalesce(try(each.value.display_name, null), each.value.name)
  description          = try(each.value.description, null)
  enforce              = try(each.value.enforcement_mode, "Default") == "Default"
  parameters           = try(jsonencode(each.value.parameters), null)
  location             = try(each.value.identity_type, null) != null ? try(each.value.location, var.location) : null

  dynamic "identity" {
    for_each = try(each.value.identity_type, null) != null ? [1] : []

    content {
      type         = each.value.identity_type
      identity_ids = each.value.identity_type == "UserAssigned" ? try(each.value.identity_ids, []) : null
    }
  }

  depends_on = [module.lz_vending]
}
