import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List


def _error(message: str) -> None:
    raise ValueError(message)


def _expect_type(value: Any, expected_type: type, field: str) -> None:
    if not isinstance(value, expected_type):
        _error(f"Field '{field}' must be of type {expected_type.__name__}.")


def _expect_required(data: Dict[str, Any], field: str) -> Any:
    if field not in data:
        _error(f"Missing required field '{field}'.")
    return data[field]


def _validate_regex(value: str, pattern: str, field: str) -> None:
    if re.fullmatch(pattern, value) is None:
        _error(f"Field '{field}' does not match required pattern '{pattern}'.")


def _validate_in(value: str, allowed: List[str], field: str) -> None:
    if value not in allowed:
        _error(f"Field '{field}' must be one of: {', '.join(allowed)}.")


def _validate_contract_schema(data: Dict[str, Any]) -> None:
    required_top = [
        "workload_name",
        "environment",
        "owner",
        "cost_center",
        "connectivity_model",
        "subscription",
        "governance",
        "rbac",
        "budget",
    ]

    for key in required_top:
        _expect_required(data, key)

    workload_name = data["workload_name"]
    _expect_type(workload_name, str, "workload_name")
    _validate_regex(workload_name, r"^[a-z0-9-]{2,24}$", "workload_name")

    environment = data["environment"]
    _expect_type(environment, str, "environment")
    _validate_in(environment, ["dev", "test", "prod"], "environment")

    owner = data["owner"]
    _expect_type(owner, str, "owner")

    cost_center = data["cost_center"]
    _expect_type(cost_center, str, "cost_center")
    _validate_regex(cost_center, r"^[A-Z0-9-]{2,20}$", "cost_center")

    connectivity_model = data["connectivity_model"]
    _expect_type(connectivity_model, str, "connectivity_model")
    _validate_in(connectivity_model, ["none", "hub_spoke", "vwan"], "connectivity_model")

    subscription = data["subscription"]
    _expect_type(subscription, dict, "subscription")
    for sub_key in ["billing_scope", "management_group_id", "location"]:
        _expect_required(subscription, sub_key)
    _validate_regex(
        subscription["billing_scope"],
        r"^/providers/Microsoft\.Billing/billingAccounts/.+",
        "subscription.billing_scope",
    )

    governance = data["governance"]
    _expect_type(governance, dict, "governance")
    _expect_required(governance, "subscription_tags")
    _expect_required(governance, "policy_assignments")
    _expect_type(governance["subscription_tags"], dict, "governance.subscription_tags")
    _expect_type(governance["policy_assignments"], list, "governance.policy_assignments")

    for idx, pa in enumerate(governance["policy_assignments"]):
        _expect_type(pa, dict, f"governance.policy_assignments[{idx}]")
        name = _expect_required(pa, "name")
        policy_definition_id = _expect_required(pa, "policy_definition_id")
        _expect_type(name, str, f"governance.policy_assignments[{idx}].name")
        _expect_type(
            policy_definition_id,
            str,
            f"governance.policy_assignments[{idx}].policy_definition_id",
        )
        _validate_regex(
            policy_definition_id,
            r"^/providers/Microsoft\.Authorization/policy(Definitions|SetDefinitions)/.+",
            f"governance.policy_assignments[{idx}].policy_definition_id",
        )

    rbac = data["rbac"]
    _expect_type(rbac, list, "rbac")
    if len(rbac) == 0:
        _error("Field 'rbac' must include at least one role assignment.")

    for idx, role in enumerate(rbac):
        _expect_type(role, dict, f"rbac[{idx}]")
        principal_id = _expect_required(role, "principal_id")
        definition = _expect_required(role, "definition")
        _expect_type(principal_id, str, f"rbac[{idx}].principal_id")
        _expect_type(definition, str, f"rbac[{idx}].definition")
        _validate_regex(principal_id, r"^[0-9a-fA-F-]{36}$", f"rbac[{idx}].principal_id")

    budget = data["budget"]
    _expect_type(budget, dict, "budget")
    for bkey in ["amount", "time_grain", "start", "end", "contact_emails"]:
        _expect_required(budget, bkey)

    _validate_in(budget["time_grain"], ["Monthly", "Quarterly", "Annually"], "budget.time_grain")
    _expect_type(budget["contact_emails"], list, "budget.contact_emails")
    if len(budget["contact_emails"]) == 0:
        _error("Field 'budget.contact_emails' must include at least one recipient.")

    network = data.get("network", {})
    if network is not None:
        _expect_type(network, dict, "network")

    if connectivity_model == "hub_spoke" and not network.get("hub_network_resource_id"):
        _error("network.hub_network_resource_id is required when connectivity_model is 'hub_spoke'.")

    if connectivity_model == "vwan" and not network.get("vwan_hub_resource_id"):
        _error("network.vwan_hub_resource_id is required when connectivity_model is 'vwan'.")


def _hcl_quote(value: str) -> str:
    return json.dumps(value)


def _hcl_list(values: List[str]) -> str:
    return "[" + ", ".join(_hcl_quote(v) for v in values) + "]"


def _dict_to_hcl_map(data: Dict[str, Any], indent: int = 2) -> str:
    pad = " " * indent
    lines = ["{"]
    for key, value in data.items():
        if isinstance(value, dict):
            nested = _dict_to_hcl_map(value, indent + 2)
            lines.append(f"{pad}{key} = {nested}")
        elif isinstance(value, list):
            if all(isinstance(x, str) for x in value):
                lines.append(f"{pad}{key} = {_hcl_list(value)}")
            else:
                lines.append(f"{pad}{key} = {json.dumps(value)}")
        elif isinstance(value, str):
            lines.append(f"{pad}{key} = {_hcl_quote(value)}")
        elif isinstance(value, bool):
            lines.append(f"{pad}{key} = {'true' if value else 'false'}")
        else:
            lines.append(f"{pad}{key} = {value}")
    lines.append(" " * (indent - 2) + "}")
    return "\n".join(lines)


def _policy_assignments_to_tfvar_map(assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for idx, item in enumerate(assignments):
        key = item["name"].replace("-", "_")
        if key in result:
            key = f"{key}_{idx + 1}"

        result[key] = {
            "name": item["name"],
            "policy_definition_id": item["policy_definition_id"],
            "display_name": item.get("display_name", item["name"]),
            "enforcement_mode": item.get("enforcement_mode", "Default"),
            "parameters": json.loads(item.get("parameters_json", "{}")) if item.get("parameters_json") else {},
        }

        if "description" in item:
            result[key]["description"] = item["description"]

    return result


def _rbac_to_role_map(rbac: List[Dict[str, Any]]) -> Dict[str, Any]:
    role_map: Dict[str, Any] = {}
    for idx, item in enumerate(rbac):
        scope = item.get("relative_scope", "")
        key = f"assignment_{idx + 1}"
        role_map[key] = {
            "principal_id": item["principal_id"],
            "definition": item["definition"],
            "relative_scope": scope,
        }
        if "principal_type" in item:
            role_map[key]["principal_type"] = item["principal_type"]
    return role_map


def generate_tfvars(contract: Dict[str, Any]) -> str:
    subscription = contract["subscription"]
    governance = contract["governance"]
    budget = contract["budget"]
    network = contract.get("network", {})

    lines: List[str] = []
    lines.append(f"workload_name      = {_hcl_quote(contract['workload_name'])}")
    lines.append(f"environment        = {_hcl_quote(contract['environment'])}")
    lines.append(f"owner              = {_hcl_quote(contract['owner'])}")
    lines.append(f"cost_center        = {_hcl_quote(contract['cost_center'])}")
    lines.append(f"connectivity_model = {_hcl_quote(contract['connectivity_model'])}")
    lines.append("")

    lines.append(f"location                         = {_hcl_quote(subscription['location'])}")
    lines.append(f"subscription_billing_scope       = {_hcl_quote(subscription['billing_scope'])}")
    lines.append(f"subscription_management_group_id = {_hcl_quote(subscription['management_group_id'])}")
    lines.append(
        f"subscription_workload            = {_hcl_quote('Production' if contract['environment'] == 'prod' else 'DevTest')}"
    )
    lines.append("")

    lines.append(
        f"hub_network_resource_id = {_hcl_quote(network.get('hub_network_resource_id')) if network.get('hub_network_resource_id') else 'null'}"
    )
    lines.append(
        f"vwan_hub_resource_id    = {_hcl_quote(network.get('vwan_hub_resource_id')) if network.get('vwan_hub_resource_id') else 'null'}"
    )

    spoke_address_space = network.get("spoke_address_space", ["10.140.0.0/24"])
    spoke_subnet_prefixes = network.get("spoke_subnet_prefixes", ["10.140.0.0/26"])
    lines.append(f"spoke_address_space   = {_hcl_list(spoke_address_space)}")
    lines.append(f"spoke_subnet_prefixes = {_hcl_list(spoke_subnet_prefixes)}")
    lines.append("")

    if len(contract["rbac"]) < 2:
        _error("At least two RBAC entries are required to map owner_principal_id and platform_ops_group_object_id.")

    lines.append(f"owner_principal_id           = {_hcl_quote(contract['rbac'][0]['principal_id'])}")
    lines.append(f"platform_ops_group_object_id = {_hcl_quote(contract['rbac'][1]['principal_id'])}")
    lines.append("")

    lines.append(f"budget_amount            = {budget['amount']}")
    lines.append(f"budget_time_grain        = {_hcl_quote(budget['time_grain'])}")
    lines.append(f"budget_start_date        = {_hcl_quote(budget['start'])}")
    lines.append(f"budget_end_date          = {_hcl_quote(budget['end'])}")
    lines.append(f"budget_contact_emails    = {_hcl_list(budget['contact_emails'])}")
    lines.append(f"budget_threshold_percent = {budget.get('threshold_percent', 80)}")
    lines.append("")

    lines.append("additional_subscription_tags = " + _dict_to_hcl_map(governance["subscription_tags"]))
    lines.append("")

    policy_map = _policy_assignments_to_tfvar_map(governance["policy_assignments"])
    lines.append("policy_assignments = " + _dict_to_hcl_map(policy_map))

    return "\n".join(lines) + "\n"


def load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _error(f"Invalid JSON in '{path}': {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a subscription vending request JSON and generate terraform.tfvars."
    )
    parser.add_argument(
        "--request",
        required=True,
        help="Path to request JSON file.",
    )
    parser.add_argument(
        "--schema",
        required=False,
        help="Path to schema JSON file. Presence is checked, validation is implemented in script.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Path for generated terraform.tfvars output.",
    )

    args = parser.parse_args()

    request_path = Path(args.request)
    out_path = Path(args.out)

    if not request_path.exists():
        _error(f"Request file not found: {request_path}")

    if args.schema:
        schema_path = Path(args.schema)
        if not schema_path.exists():
            _error(f"Schema file not found: {schema_path}")

    contract = load_json(request_path)
    _validate_contract_schema(contract)

    tfvars_content = generate_tfvars(contract)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tfvars_content, encoding="utf-8")

    print(f"Generated tfvars: {out_path}")


if __name__ == "__main__":
    main()
