from nbu.parsers import bpdbjobs, bpimagelist, bppllist, bpstulist, nbstl


def test_bpdbjobs_key_value_parser() -> None:
    jobs = bpdbjobs.parse(
        """
        Job ID: 123
        Type: Backup
        State: Done
        Status: 0
        Policy: linux-prod
        Client: app01
        """
    )
    assert jobs[0].job_id == "123"
    assert jobs[0].policy == "linux-prod"


def test_policy_parser() -> None:
    policies = bppllist.parse(
        """
        Policy Name: vmware-prod
        Policy Type: VMware
        Active: yes
        Clients: vm01, vm02
        Backup Selections: ALL_LOCAL_DRIVES
        """
    )
    assert policies[0].name == "vmware-prod"
    assert policies[0].clients == ["vm01", "vm02"]


def test_image_parser() -> None:
    images = bpimagelist.parse(
        """
        Backup ID: app01_1234567890
        Client: app01
        Policy: linux-prod
        Copy Number: 1
        """
    )
    assert images[0].image_id == "app01_1234567890"


def test_storage_parser() -> None:
    units = bpstulist.parse(
        """
        Storage Unit: stu-msdp
        Media Server: media01
        Status: OK
        """
    )
    assert units[0].name == "stu-msdp"


def test_slp_parser() -> None:
    slps = nbstl.parse(
        """
        Storage Lifecycle Policy: gold-copy
        Status: active
        """
    )
    assert slps[0].name == "gold-copy"

