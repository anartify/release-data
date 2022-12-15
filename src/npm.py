from glob import glob
import os
import re
import sys
import json
import frontmatter
import urllib.request

DEFAULT_TAG_TEMPLATE = (
    "{{major}}{% if minor %}.{{minor}}{% if patch %}.{{patch}}{%endif%}{%endif%}"
)
REGEX = r"^(?:(\d+\.(?:\d+\.)*\d+))$"


def fetch_releases(npm_id, regex):
    releases = {}

    if not isinstance(regex, list):
        regex = [regex]

    url = f"https://registry.npmjs.org/{npm_id}"
    with urllib.request.urlopen(url, data=None, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
        for version in data["time"]:
            matches = False
            for r in regex:
                if re.match(r, version):
                    matches = True

            release_datetime = data["time"][version]
            if matches and release_datetime:
                releases[version] = release_datetime.split("T")[0]
                print(f"{version}: {releases[version]}")

    return releases


def update_releases(product_filter=None):
    for product_file in glob("website/products/*.md"):
        product_name = os.path.splitext(os.path.basename(product_file))[0]
        if product_filter and product_name != product_filter:
            continue

        with open(product_file, "r") as f:
            data = frontmatter.load(f)
            if "auto" in data:
                for config in data["auto"]:
                    for key, d_id in config.items():
                        if key == "npm":
                            update_product(product_name, config)


def update_product(product_name, config):
    if "npm" in config:
        print(f"::group::{product_name}")
        config = {"regex": REGEX} | config
        r = fetch_releases(config["npm"], config["regex"])
        print("::endgroup::")

        with open(f"releases/{product_name}.json", "w") as f:
            f.write(json.dumps(r, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        update_releases(sys.argv[1])
    else:
        update_releases()
