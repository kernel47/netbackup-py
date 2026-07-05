from __future__ import annotations

import re
from typing import Any

from nbu.models.vm import VMAsset, VMwareSelection
from nbu.parsers.common import attributes, first_value, list_value, resource_id


VMWARE_SELECTION_PREFIX = "vmware:/filter="
_VIP_CONDITION_RE = re.compile(
    r"(?P<field>[A-Za-z_][A-Za-z0-9_.-]*)\s+"
    r"(?P<operator>NotEqual|NotContains|StartsWith|EndsWith|GreaterEqual|LessEqual|"
    r"Greater|Less|Equal|Contains)\s+"
    r"(?P<value>\"[^\"]*\"|'[^']*'|[^()\s]+)",
    re.IGNORECASE,
)


def vip_filter_to_odata(filter_value: str) -> str | None:
    if not filter_value:
        return None

    def replacement(match: re.Match[str]) -> str:
        field = match.group("field")
        operator = match.group("operator").lower()
        value = _odata_value(match.group("value"))
        if operator == "equal":
            return f"{field} eq {value}"
        if operator == "notequal":
            return f"{field} ne {value}"
        if operator == "contains":
            return f"contains({field},{value})"
        if operator == "notcontains":
            return f"not contains({field},{value})"
        if operator == "startswith":
            return f"startswith({field},{value})"
        if operator == "endswith":
            return f"endswith({field},{value})"
        if operator == "greater":
            return f"{field} gt {value}"
        if operator == "greaterequal":
            return f"{field} ge {value}"
        if operator == "less":
            return f"{field} lt {value}"
        if operator == "lessequal":
            return f"{field} le {value}"
        return match.group(0)

    converted = _VIP_CONDITION_RE.sub(replacement, filter_value)
    converted = re.sub(r"\bAND\b", "and", converted, flags=re.IGNORECASE)
    converted = re.sub(r"\bOR\b", "or", converted, flags=re.IGNORECASE)
    return converted if converted != filter_value or _VIP_CONDITION_RE.search(filter_value) else None


def _odata_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        value = value[1:-1]
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def parse_vmware_selection(raw: str, odata_filter: str | None = None) -> VMwareSelection:
    filter_value = raw[len(VMWARE_SELECTION_PREFIX) :] if raw.startswith(VMWARE_SELECTION_PREFIX) else raw
    return VMwareSelection(
        raw=raw,
        filter=filter_value or None,
        odata_filter=odata_filter or vip_filter_to_odata(filter_value),
    )


def parse_vm_asset(payload: dict[str, Any], source: str = "api") -> VMAsset:
    attrs = attributes(payload)
    common_attrs = attrs.get("commonAssetAttributes")
    if isinstance(common_attrs, dict):
        attrs = common_attrs | attrs
    return VMAsset(
        name=first_value(attrs, "displayName", "display_name", "name", "vmName", "vm_name")
        or resource_id(payload),
        uuid=first_value(attrs, "uuid", "instanceUuid", "instance_uuid"),
        vcenter=first_value(attrs, "vCenter", "vcenter"),
        asset_type=first_value(attrs, "assetType", "asset_type") or payload.get("type"),
        cluster=first_value(attrs, "cluster", "clusterName", "cluster_name"),
        esx_server=first_value(attrs, "esxServer", "esxiServer", "esx_server", "host"),
        policies=[str(policy) for policy in list_value(attrs.get("policies"))],
        last_backup=first_value(attrs, "lastBackup", "last_backup"),
        backup_status=first_value(attrs, "backupStatus", "backup_status"),
        protected=attrs.get("protected"),
        raw=payload,
        source=source,
    )
