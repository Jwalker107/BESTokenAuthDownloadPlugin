"""
automated test for TokenAuthDownload.py
"""

import json
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import TokenAuthDownload

def main() -> None:
    """execution of tests starts here."""
    print("starting tests")

    # get absolute path to config file relative to the tests.py file location
    config_path_test = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-config.json")
    with open(config_path_test, "rb") as f:
        config_json = json.load(f)

    # get the github token from the ENV, will be populated in github action automatically.
    github_token = os.getenv('GITHUB_TOKEN', "testing")

    config_json["url_configs"][1]["token"] = github_token

    config_path_test = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

    print("writing test config file")
    with open(config_path_test, "w") as f:
        json.dump(config_json, f, indent=2)

    print("run test")
    TokenAuthDownload.main(downloads="tests/test-downloads.json")

    print("cleanup test config file")
    os.remove(config_path_test)


if __name__ == "__main__":
    main()
