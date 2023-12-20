
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
import logging

def init_logging(logfile:str, level:int=20 ):
    # Creates the global 'logging' module and 'statuslog' variable - for debug and status logs
    # Creates the directories if they do not exist
    # Logs are created in the 'log' directory relative to the running script
  
    # FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(
        # level=logging.info,
        # Default log level is INFO but overridden by the config file after it is read
        level=level,
        format="[%(asctime)s] %(funcName)20s() [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(logfile), logging.StreamHandler()],
    )
    logging.info('Logging started to "%s"', logfile)



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

def get_options(filepath):
    with open(filepath, "r") as file:
        options = json.load(file)
    return options

def sendResults(results, options):
    message = {}
    message["message"] = "status"
    message["id"] = options["id"]
    message["status"] = results
        
    # status_filepath=tempfile.NamedTemporaryFile(
    #         delete=False,
    #         dir=options["inbox"],
    #         prefix="plugin_" + str(options["id"]) + "_"
    #     ).name
    plugin_id=options['id']
    inbox_path=options['inbox']
    results_file=os.path.join(inbox_path, f"plugin_{plugin_id}")
    logging.info(f'Saving results to file {results_file} : {str(message)}')
    with open(
        results_file, "w"
    ) as status_file:
        json.dump(results, status_file)

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
    parser.add_argument("--verbose", "-v", action="store_true")
    args=parser.parse_args(argv)
    return args


def main():
    plugin_system_name = "TokenAuthDownload"

        # If the application is run as a bundle, the PyInstaller bootloader
        # # extends the sys module by a flag frozen=True and sets the app
        # # path into variable _MEIPASS'.
        # print("Using frozen config")
    if getattr(sys, "frozen", False):
 
        scriptPath = os.path.dirname(os.path.abspath(sys.executable))
    else:
        scriptPath = os.path.dirname(os.path.abspath(__file__))
    init_logging( os.path.join(scriptPath, 'logfile.txt') )
    
    ##############
    # examples of simulated command-line arguments, for use in a python debugger:
    # args=get_args(["--set_token"])

    
    # args = get_args(
    #     ["--downloads"
    #      , os.path.join(os.path.dirname(os.path.realpath(__file__)), "downloads.json")
    #      , "--verbose"
    #      ]
    # )

    #execute using the default command-line arguments
    args=get_args()
    ##################    
    if args.verbose:
        logging.getLogger().setLevel(10)

    if args.set_token:
        keyring.set_password(
            plugin_system_name,
            "",
            prompt_password("Enter Token to store:"),
        )
    
    if args.downloads is not None:
        logging.info(f"Processing downloads from {args.downloads}")
        logging.info(f"Retrieving keyring credential for {plugin_system_name}")
        token_container=keyring.get_credential(plugin_system_name, "")
        if token_container is None:
            raise ValueError("No stored token was found, try --set_token")
        token=token_container.password

        options = get_options(args.downloads)

        results = []
        logging.info("Creating requests.Session")
        session = requests.Session()
        session.headers.update({"User-Agent": "Wget/1.14 (linux-gnu)"})
        session.headers.update({"Authorization": f"token {token}"})

        # This is tuned for ease-of-use rather than performance.
        # Currently each download is performed sequentially, not in parallel
        for download in options.get("downloads", {}):
            result = {}
            result["id"] = download["id"]
            logging.info(f"Processing download id {result['id']}")
            url = download.get("url").replace(plugin_system_name, "https")
            logging.info(f"Download URL: {url}")
            logging.info(f"Output file: {download.get('file')}")
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
                logging.info(f"Download failed with {str(e)}")
                result["success"] = False
                result["error"] = str(e)
            results.append(result)
        # Send download status results to the downloads_listing file, where it will be read by the Server to provide action status / error messages to the console
        logging.info(f"Results: {str(results)}")
        
        logging.info(f"Preparing results to {results}")
        sendResults(results, options)
    logging.info("Plugin finished")

if __name__ == "__main__":
    main()

