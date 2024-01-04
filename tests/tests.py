"""
automated test for TokenAuthDownload.py
"""

import json
import os
import sys

# add repo root path to be available for import
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# import the main python module for this repo TokenAuthDownload.py
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

    print(f"writing test config file {config_path_test}")
    with open(config_path_test, "w", encoding='utf-8') as f:
        json.dump(config_json, f, indent=2)

    print("run test")
    results = TokenAuthDownload.main(downloads="tests/test-downloads.json")

    print("cleanup test config file")
    os.remove(config_path_test)

    print("validate results.")
    print(results)
    # examine each result:
    for result in results:
        # if any result returns FALSE, exit with -1
        if not result["success"]:
            sys.exit(-1)


if __name__ == "__main__":
    main()
