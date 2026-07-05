from __future__ import annotations

from typing import Any

from nbu.models.vm import VMAsset
from nbu.parsers.common import attributes, first_value, list_value, resource_id


def parse_vm_asset(payload: dict[str, Any], source: str = "api") -> VMAsset:
    attrs = attributes(payload)
    return VMAsset(
        name=first_value(attrs, "displayName", "display_name", "name", "vmName", "vm_name")
        or resource_id(payload),
        uuid=first_value(attrs, "uuid", "instanceUuid", "instance_uuid"),
        vcenter=first_value(attrs, "vCenter", "vcenter"),
        policies=[str(policy) for policy in list_value(attrs.get("policies"))],
        last_backup=first_value(attrs, "lastBackup", "last_backup"),
        backup_status=first_value(attrs, "backupStatus", "backup_status"),
        protected=attrs.get("protected"),
        raw=payload,
        source=source,
    )
