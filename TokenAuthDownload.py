
#curl --header "Authorization: token github_pat_XXXXXXX" https://raw.githubusercontent.com/Jwalker107/AuthDownloadPlugin/main/README.md
# requires "pip install requests"
import requests
import os
import tempfile

# to suppress SSL "untrusted certificate" warnings
import warnings
import json

# For testing download timings
import time

import argparse
import keyring
import getpass
# Suppress InsecureRequestWarning warnings from requests module
#  These are generated when we do not have a trusted CA certificate on the BES Server
from requests.packages.urllib3.exceptions import InsecureRequestWarning  # type: ignore

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def download_file_stream(
    session=requests.Session(),
    url=None,
    output_file_path=None,
    chunk_size=8192,
    block_count=4,
):
    # Perform a streaming download to reduce memory footprint
    if url is None or output_file_path is None:
        raise ValueError(f"url or output_file_path not declared")
    with session.get(url, stream=True, allow_redirects=True) as response:
        if not response.ok:
            raise ValueError(
                f"Download connection failed for {url} with HTTP {response.status_code}"
            )
        response.raise_for_status()
        with open(output_file_path, "wb") as f:
            chunk_number = 0
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                # It's nice to show progress in the OS, by flushing to disk and syncing the filesystem so the file can be seen
                # to "grow", but it's also much slower.  So don't flush on every write, only flush at block_count interval
                chunk_number += 1
                if chunk_number % block_count == 0:
                    f.flush()
                    os.fsync(f.fileno())
                    # print(".")

def read_config(config_file):
    with open(config_file, "r") as json_file:
        config = json.load(json_file)
    return config

def write_config(config, config_file):
    json_object = json.dumps(config, indent=4)
    with open(config_file, "w") as json_file:
        json_file.write(json_object)

def get_downloads(filepath):
    with open(filepath, "r") as file:
        downloads = json.load(file)
    return downloads

def sendResults(results, options):
    message = {}
    message["message"] = "status"
    message["id"] = options["id"]
    message["status"] = results
        
    status_filepath=tempfile.NamedTemporaryFile(
            delete=False,
            dir=options["inbox"],
            prefix="plugin_" + str(options["id"]) + "_"
        ).name
    
    with open(
        status_filepath, "w"
    ) as status_file:
        json.dump(message, status_file)

def prompt_password(prompt="Enter password:", confirm=None):
    # Prompts the user to enter a password
    # 'prompt' and 'confirm' are the strings presented to the user for prompting
    # if 'confirm' is not None, the user is prompted twice and the two passwords must match
    #   or the prompts are repeated until the same password is typed twice
    password = getpass.getpass(prompt)
    if confirm is not None:
        password2=getpass.getpass(confirm)
        if password == password2:
            return password
        else:
            print("Passwords did not match, retry...")
            return prompt_password(prompt,confirm)
    return password

def main():
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    # todo - check config file existence, replace with keyring

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--downloads", "-d", type=str)
    group.add_argument("--set_token", "-s", help="Save authentication token to keyring", action="store_true")

    parser.add_argument(
        "--verbose",
        "-v",
        help="Provide verbose output",
        default=False,
        action="store_true",
    )
    
    # Read args from command line
    # args = parser.parse_args()

    # or... pass a list to parse_args to test parse as if it were the command-line options for debugging
    # args = parser.parse_args(
    #     ["--set_token"]
    # )
    
    args = parser.parse_args(
        ["--downloads", os.path.join(scriptPath, "downloads.json"), "--verbose"]
    )

    if args.set_token:
        keyring.set_password(
            "TokenDownloadPlugin",
            "",
            prompt_password("Enter Token to store:"),
        )
    
    config_file = os.path.join(scriptPath, "config.json")
    config = read_config(config_file)

    verbose = args.verbose
    
    plugin_system_name = "TokenAuthDownload"
    
    if args.downloads is not None:
        token_container=keyring.get_credential("TokenDownloadPlugin", "")
        if token_container is None:
            raise ValueError("No stored token was found, try --set_token")
        token=token_container.password

        downloads_listing = get_downloads(args.downloads)
        results = []

        session = requests.Session()
        session.headers.update({"User-Agent": "Wget/1.14 (linux-gnu)"})
        session.headers.update({"Authorization": f"token {token}"})

        for download in downloads_listing.get("downloads", {}):
            result = {}
            result["id"] = download["id"]
            ## Sample download here
            # replace TokenAuthDownload://raw.githubusercontent.com/Jwalker107/AuthDownloadPlugin/main/README.md
            # with https://raw.githubusercontent.com/Jwalker107/AuthDownloadPlugin/main/README.md

            url = download.get("url").replace(plugin_system_name, "https")
            # download_file_stream will raise an exception on HTTP errors in addition to connection errors
            # so any response other than 'ok' will be caught by this exception handler
            try:
                download_file_stream(
                    session=session,
                    url=url,
                    output_file_path=download.get("file"),
                    chunk_size=65536
                )
                result["success"] = True
                result["error"] = None

            except Exception as e:
                result["success"] = False
                result["error"] = str(e)
            results.append(result)
        sendResults(results, downloads_listing)

if __name__ == "__main__":
    main()

