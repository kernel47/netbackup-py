"""Minimal NetBackup REST usage for Python 3.6.

This script is intentionally standalone. It avoids the main nbu package because
the package uses modern Python and Pydantic v2.
"""

from __future__ import print_function

import requests


class NetBackupLegacyClient(object):
    def __init__(
        self,
        master,
        username,
        password,
        domain_type="",
        domain_name="",
        api_version="7.0",
        verify_ssl=True,
        page_limit=100,
    ):
        self.base_url = "https://{0}/netbackup".format(master)
        self.username = username
        self.password = password
        self.domain_type = domain_type
        self.domain_name = domain_name
        self.api_version = api_version
        self.verify_ssl = verify_ssl
        self.page_limit = page_limit
        self.session = requests.Session()
        self.token = None

    def media_type(self):
        return "application/vnd.netbackup+json;version={0}".format(self.api_version)

    def login(self):
        response = self.session.post(
            self.base_url + "/login",
            headers={"Content-Type": self.media_type(), "Accept": self.media_type()},
            json={
                "userName": self.username,
                "password": self.password,
                "domainType": self.domain_type,
                "domainName": self.domain_name,
            },
            verify=self.verify_ssl,
            timeout=30,
        )
        response.raise_for_status()
        self.token = response.json()["token"]
        return self.token

    def get(self, path, params=None):
        if not self.token:
            self.login()
        response = self.session.get(
            self.base_url + path,
            headers={"Accept": self.media_type(), "Authorization": self.token},
            params=params or {},
            verify=self.verify_ssl,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def iter_jobs(self, filter_value=None, limit=None):
        params = {"page[limit]": self.page_limit, "sort": "-startTime"}
        if filter_value:
            params["filter"] = filter_value

        seen = set()
        yielded = 0
        while True:
            payload = self.get("/admin/jobs", params=params)
            for item in payload.get("data", []):
                if limit is not None and yielded >= limit:
                    return
                yielded += 1
                yield item

            pagination = payload.get("meta", {}).get("pagination", {})
            next_cursor = pagination.get("next")
            if not next_cursor or next_cursor in seen:
                break
            seen.add(next_cursor)
            params["page[after]"] = next_cursor

    def iter_images(self, filter_value=None, limit=None):
        params = {"page[limit]": self.page_limit}
        if filter_value:
            params["filter"] = filter_value

        seen = set()
        yielded = 0
        while True:
            payload = self.get("/catalog/images", params=params)
            for item in payload.get("data", []):
                if limit is not None and yielded >= limit:
                    return
                yielded += 1
                yield item

            pagination = payload.get("meta", {}).get("pagination", {})
            next_offset = pagination.get("next")
            if next_offset is None or next_offset == "" or next_offset in seen:
                break
            seen.add(next_offset)
            params["page[offset]"] = next_offset


if __name__ == "__main__":
    nb = NetBackupLegacyClient(
        master="master.company.com",
        username="user",
        password="password",
        domain_type="unixpwd",
        domain_name="master.company.com",
        api_version="7.0",  # NetBackup 10.0. Use "14.0" for NetBackup 11.2.
        verify_ssl=False,
    )

    job_filter = "startTime ge '2026-07-01' and endTime le '2026-07-02'"
    for job in nb.iter_jobs(filter_value=job_filter, limit=100):
        attrs = job.get("attributes", {})
        print(attrs.get("jobId"), attrs.get("clientName"), attrs.get("policyName"), attrs.get("status"))

