from __future__ import annotations

from typing import Any

from nbu.models.vm import VMAsset, VMwareSelection
from nbu.parsers.common import attributes, first_value, list_value, resource_id


VMWARE_SELECTION_PREFIX = "vmware:/filter="


def parse_vmware_selection(raw: str, odata_filter: str | None = None) -> VMwareSelection:
    filter_value = raw[len(VMWARE_SELECTION_PREFIX) :] if raw.startswith(VMWARE_SELECTION_PREFIX) else raw
    return VMwareSelection(raw=raw, filter=filter_value or None, odata_filter=odata_filter)


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
