
"""Demonstrates a custom download-plugin for the BigFix Root Server.  This sample demonstrates performing downloads using a GitHub User Token to authenticate and download file(s)"""
#curl --header "Authorization: token github_pat_XXXXXXX" https://raw.githubusercontent.com/Jwalker107/AuthDownloadPlugin/main/README.md

import os
import sys
import tempfile
import json
import argparse
import keyring
import requests
import getpass

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

def get_args(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--downloads", "-d", type=str)
    group.add_argument("--set_token", "-s", help="Save authentication token to keyring", action="store_true")
    args=parser.parse_args(argv)
    return args


def main():
  
    # examples of simulated command-line arguments, for use in a python debugger:
    # args=get_args(["--set_token"])

    # args = get_args(
    #     ["--downloads", os.path.join(os.path.dirname(os.path.realpath(__file__)), "downloads.json"), "--verbose"]
    # )

    # execute using the default command-line arguments
    args=get_args()

    if args.set_token:
        keyring.set_password(
            "TokenDownloadPlugin",
            "",
            prompt_password("Enter Token to store:"),
        )
        
     
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

        # This is tuned for ease-of-use rather than performance.
        # Currently each download is performed sequentially, not in parallel
        for download in downloads_listing.get("downloads", {}):
            result = {}
            result["id"] = download["id"]
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
        # Send download status results to the downloads_listing file, where it will be read by the Server to provide action status / error messages to the console
        sendResults(results, downloads_listing)

if __name__ == "__main__":
    main()

