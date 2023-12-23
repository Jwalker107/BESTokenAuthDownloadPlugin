
"""
THIS TOOL IS UNSUPPORTED
Demonstrates a custom download-plugin for the BigFix Root Server.
This sample demonstrates performing downloads using a GitHub User Token to authenticate and download file(s)
"""
#curl --header "Authorization: token github_pat_XXXXXXX" https://raw.githubusercontent.com/Jwalker107/AuthDownloadPlugin/main/README.md
#curl -L -H "Accept: application/octet-stream" -H "Authorization: token github_pat_XXX" https://api.github.com/repos/Jwalker107/AuthDownloadPlugin/releases/assets/141569199 -O

import os
import sys
import json
import re
import argparse
import keyring
import requests
import logging

def init_logging(logfile:str, level:int=20 ) -> None:
    """Initializes the logging module to log to terminal and a log file"""
    logging.basicConfig(
        # level=logging.info,
        # Default log level is INFO but overridden by the config file
        level=level,
        format="[%(asctime)s] %(funcName)20s() [%(levelname)s] %(message)s",
        # Log to both a file and to stdout
        handlers=[logging.FileHandler(logfile), logging.StreamHandler()],
    )
    logging.info('Logging started to "%s"', logfile)



def get_options(filepath:str) -> dict:
    """Loads the options from the file specified in the --downloads argument"""
    # the --downloads <file> references a JSON configuration file generally stored in the TEMP directory, i.e.
    # c:\windows\temp\big97A8.tmp
    # see sample-downloads.json in this repo for a sample of the file syntax
    with open(filepath, "r") as file:
        options = json.load(file)
    return options

def sendResults(results:list[dict], options:dict) -> None:
    """Create a message file detailing download results to the server"""
    # sample message: 
    #  {"message": "status", "id": 1702650720, "status": [{"id": 57, "success": true, "error": null}]}
    message = {}
    message["message"] = "status"
    message["id"] = options["id"]
    message["status"] = results
       
    # results file must be named `plugin_MESSAGEID` and must be stored in the Mirror Server/Inbox path (as specified in the original request options)
    results_file=os.path.join(options['inbox'], f"plugin_{options['id']}")
    logging.info(f'Saving results to file {results_file} : {str(message)}')
    with open(results_file, "w") as status_file:
        json.dump(message, status_file)

def get_args() -> argparse.Namespace:
    """Configure and read command-line parameters"""
    # when invoked by the root server, the '--downloads <download_message_file>' arguments will be passed
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads", "-d", type=str, required=True)
    args=parser.parse_args()
    return args

def get_config(config_file:str) -> dict:
    """Read configuration from config.json"""
    # config.json stores options such as the download plugin name, log file name & log level, and optionally may have a 'token' value to store
    try:
        with open(config_file, 'r') as json_file:
            config=json.load(json_file)
    except Exception as e:
        print (f'Error loading configuration file {config_file} : {str(e)}')
        # Config not loaded, run with defaults
        config= {}
    return config

def get_token_identifier(config:dict, url_config:dict) -> str:
    """Return a token identifier name for one url_config section of the config"""
    return f"{config.get('plugin_name', 'TokenAuthDownload')}_{url_config.get('config_name', 'UnNamed')}"

def update_token(config:dict, config_file:str) -> None:
    """Checks whether an updated token is present in the configuration file.  If so, update the keyring and remove the token from the file."""
    updates_found=False
    for url_config in config.get('url_configs', []):
        token_identifier=get_token_identifier(config, url_config)
        if url_config.get('token', None) is not None:
            updates_found=True
            logging.info(f'Storing token to keyring for {token_identifier}')
            keyring.set_password(
                token_identifier,
                "",
                url_config.get('token')
            )
            url_config['token']=None
            logging.info(f'Removing token from config file for config {token_identifier}')
    
    if updates_found:
        set_config(config, config_file)

def set_config(config:dict, config_file:str) -> None:
    """Write updated configuration to config.json"""
    # If the config file contained a 'token' value, we will re-write the file to remove that value after storing it in the keyring
    with open(config_file, 'w') as file:
        json.dump(config, file, indent=2)


def get_token(identifier:str) -> str:
    logging.info(f"Retrieving keyring credential for {identifier}")
    token_container=keyring.get_credential(identifier, "")
    if token_container is None:
        return None
    
    return token_container.password
    
def match_url_to_config(url:str, config:dict) -> dict:
    """Given a download URL and a configuration dictionary, return the url_config dictionary that most closely matches the URL""" 
    if not config.get('url_configs', False):
        return None
    longest_match_length=0
    matched_config=None
    logging.debug(f'Finding best match for url {url}')
    for url_config in config.get('url_configs',[]):
        logging.debug(f'...checking config {url_config.get("config_name")}')
        for url_pattern in url_config.get('url_list', None):
            logging.debug(f'...checking pattern "{url_pattern}"')
            if not re.fullmatch(url_pattern, url, flags=re.IGNORECASE):
                logging.debug('....not matched.')
            else:
                logging.debug(f"url {url} matched pattern {url_pattern}")
                if not len(url_pattern) > longest_match_length:
                    logging.debug(f'....ignoring match, a better match already exists')
                else:
                    logging.debug(f'url "{url_pattern}" is the best match so far')
                    longest_match_length=len(url_pattern)
                    matched_config=url_config
    return matched_config

    pass
    

def get_script_path() -> str:
    # Get path to the script's parent directory
    # If the application is run as a an executable bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sys.executable reflects the path
    # otherwise if running as a .py script use the path to __file__
    if getattr(sys, "frozen", False):
         scriptPath = os.path.dirname(os.path.abspath(sys.executable))
    else:
        scriptPath = os.path.dirname(os.path.abspath(__file__))
    return scriptPath

def download_file_stream(
    session:requests.Session = requests.Session(),
    url:str = None,
    output_file_path:str = None,
    chunk_size:int = 8192,
    block_count:int = 4,
) -> None:
    """
    Use an established requests.Session to download a file, streaming in blocks of chunk_size and flushing to disk every block_count chunks.
    If any error occurs raise an error to be handled by the caller.
    """
    # Perform a streaming download to reduce memory footprint (otherwise the entire file download loads in RAM)
    if url is None or output_file_path is None:
        raise ValueError(f"url or output_file_path not defined")
    
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

def replace_url(url:str, plugin_system_name:str) -> str:
    """Replace the given plugin_system_name:// with https:// in a download url"""
    # Yes, this is a simple thing to do in a function but we call this in a few places.
    # Considering changing this to just strip DownloadPluginName: off the front so we could allow things like scp or git commands
    # instead of only https://
    return url.replace(f"{plugin_system_name}://", "https://")

def process_download(download_request:dict, plugin_system_name:str, session:requests.Session) -> dict:
    """Process a single download request and return a dictionary describing success/failure status"""
    result = {}
    logging.info(f"Processing download id {download_request['id']}")
    url = replace_url(download_request.get("url"), plugin_system_name)
    logging.info(f"Download URL: {url}")
    logging.info(f"Output file: {download_request.get('file')}")
    # download_file_stream will raise an exception on HTTP errors in addition to connection errors
    # so any response other than 'ok' will be caught by this exception handler
    try:
        download_file_stream(
            session=session,
            url=url,
            output_file_path=download_request.get("file"),
            chunk_size=65536
        )
        result["success"] = True
        result["error"] = None

    except Exception as e:
        logging.info(f"Download failed with {str(e)}")
        result["success"] = False
        result["error"] = str(e)
    return result

def process_download_list(options:dict, config:dict, session:requests.Session) -> list[dict]:
    """
    Process the download requests provided in 'options' dictionary, using url configurations defined in 'config', with a reusable requsts.Session.
    Return a list of download result dictionary entries.
    """
    # TODO: This is tuned for ease-of-use rather than performance.
    # Currently each download is performed sequentially, not in parallel; room for improvement
    plugin_system_name = config.get('plugin_name', "TokenAuthDownload")
    results = []
    for download in options.get("downloads", []):
        # report a download error if the config.json file could not be loaded (missing or bad JSON syntax)
        if not config:
            download_result={'id': download['id'], 'success': False, 'error': f'Failed to load configuration file, check existence and syntax'}
            results.append(download_result)
            continue
        # report a download error if the requested URL could not be matched to an entry in config.url_configs
        url = replace_url(download.get("url"), plugin_system_name)
        url_config=match_url_to_config(url, config)
        if url_config is None:
            download_result={'id': download['id'], 'success': False, 'error': f'Failed to match requested url {download.get("url")} to a url_config in config.json'}
            results.append(download_result)
            continue
        # report a download error if an auth token could not be retrieved for the matched url_configs entry
        token_identifier=get_token_identifier(config, url_config)
        token=get_token(token_identifier)
        if token is None:
            download_result={'id': download['id'], 'success': False, 'error': f'Failed to retrieve auth token for {token_identifier}, try adding token to config.json'}
            results.append(download_result)
            continue
        
        # Attempt to perform the download and report the actual download result
        session.headers.update({"Authorization": f"token {token}"})
        download_result=process_download(download, plugin_system_name, session)
        download_result['id']=download['id']
        results.append(download_result)
    return results

def setup_session() -> requests.Session:
    """Return a requests.Session object with default headers applied"""
    
    # TODO - providing Accept: application/octet-stream is necessary for GitHub; consider moving headers to config.url_configs    
    headers={
             "User-Agent": "Wget/1.14 (linux-gnu)",
             "Accept": "application/octet-stream"
             }
    session = requests.Session()
    session.headers.update(headers)
    return session

def main() -> None:
    
    # read the config from config.json, relative to the script/executable
    scriptPath=get_script_path()
    config_file=os.path.join(scriptPath, 'config.json')
    config=get_config(config_file)
    
    # it would be *nice* to init logging earlier, but...currently allow the config_file to specify an alternate log file so need to read config first
    # supply a default of 'scriptPath\\logfile.txt' in case the config file could not be loaded or is missing this entry
    log_file=config.get('log', os.path.join(scriptPath, 'logfile.txt'))
    init_logging(log_file, level=config.get('log_level', 20))
    
    # note: we need to continue the script even if the config could not be downloaded;
    # we want to process the downloads.json in order to report the 'cannot load config' status to the server as if it were a download result 
    if not config:
        logging.warning(f'Configuration file not found or cannot be loaded at {config_file}')

    

    # If 'token' has a value in any url_configs stanza in config.json, use keyring to encrypt the token and then remove it from the config file
    # Note - we want to update *all* tokens *anywhere* in the config, before attempting downloads, so we can be sure the plaintext
    # token is removed from the config file as soon as possible
    update_token(config, config_file)
        
    # process command-line arguments to get the --downloads parameter - the path to a json file containing a list of downloads
    args=get_args()

    logging.info(f"Processing download request from file {args.downloads}")
    # options is the dictionary provided by the BES Server, which contains the message ID, path to Inbox, and a list of download requests
    try:
        options = get_options(args.downloads)
    except Exception as e:
        logging.error(f'Failed to load file {args.downloads} with {str(e)}')
        raise e

    session=setup_session()
    results=process_download_list(options, config, session)
    # Send download status results to the message file, where it will be read by the Server to provide action status / error messages to the console
    # currently we only update status when the downloads have completed or failed; but it is possible to update status for downloads-in-progress.
    logging.info(f"Results: {str(results)}")
    sendResults(results, options)
    logging.info("Plugin finished")

if __name__ == "__main__":
    main()