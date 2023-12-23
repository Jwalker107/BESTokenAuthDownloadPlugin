# TokenAuthDownload
BigFix Download Plug-In for Authenticated HTTPS downloads using token authentication (i.e. GitHub)

**This is not a supported BigFix tool and is for demonstration purposes.  Use at your own risk**

To build the plugin (assuming Python is already installed)
* Install requirements
  - pip install -r requirements.txt
* Test script loads
  - python TokenAuthDownload.py -h
* Create executable
  - pyinstaller --onefile TokenAuthDownload.py
  - generates dist\TokenAuthDownload\TokenAuthDownload.exe
  - ref https://pyinstaller.org/en/v4.8/usage.html


To Load Plugin on the BES Server:

Create json install file, ex. "plugin_TokenAuthDownload" (filename should begin with 'plugin_' and have no filename extension):

    {
       "message" : "add",
       "protocol" : "TokenAuthDownload",
       "location" : "C:\\Program Files (x86)\\BigFix Enterprise\\BES Server\\DownloadPlugins\\TokenAuthDownload\\TokenAuthDownload.exe"
    }

Place the file in C:\Program Files (x86)\BigFix Enterprise\BES Server\Mirror Server\Inbox.  The file is ingested by the BESRootServer and will be deleted from this directory when processed.

Create the target directory (`C:\Program Files (x86)\BigFix Enterprise\BES Server\DownloadPlugins\TokenAuthDownload` ) and copy `dist\TokenAuthDownload\TokenAuthDownload.exe` and `config.json` to that directory.

To configure the plugin, 
* create (at least one) authentication token (assuming github.com, select your profile -> Settings -> Developer Options -> Personal Access Tokens).
* Create a config.json file based upon the example sample-config.json provided in this repository, and place config.json in the `BES Server\DownloadPlugins\TokenAuthDownload` directory.
* The config.json contains a stanza for `url_configs` allowing to specify multiple configurations.
  - Each url configuration contains a a `url_list` array.  Each element is a Regular Expression.  The requested download URL is compared to each regular expression in the `url_list`.  If the requested url matches multiple `url_list` entries, the longest regular expression matched is selected.
  - Update the `token` entry of each `url_config` when first installing the Download Plug-In, and whenever the given token is updated.
  - Provide a unique `config_name` value for each `url_configs` entry. The top-level `plugin_name` is combined with each `url_configs.config_name` to determine the name of the token that will be stored in the Keyring (Windows Credential Manager on Windows, by default).  I.e. `TokenAuthPlugin_configuration1`
  - Hint: To use the same token for _all_ urls, a default regex to 'match anything' is `.*`
* The next time the plugin runs (triggered by a download command in an Action Script), the all provided token values will be removed from the config.json and stored in the system keyring (Windows Credential Manager, by default, on Windows; see Python Keyring module docs for info on other platforms)

To remove the download plugin from the BES Server, create file "plugin_TokenAuthDownload" and place in the Mirror Server\Inbox directory:

    {
       "message" : "remove",
       "protocol" : "TokenAuthDownload"
       
    }

To use the plugin, create a download action message such as
`prefetch bigfix.png sha1:9b84643d03b11e0d196c2967d7f870b1c212c165 size:4083 TokenAuthDownload://api.github.com/repos/Jwalker107/AuthDownloadPlugin/releases/assets/141569199 sha256:b658f7f01256d9f4a30270375050b829a99cc9ad8738463bc7c582fd6c3ee9bb`

To get the URL to a release asset for a GitHub repo, you may use a REST API client or curl command to retrieve, such as

    curl -H "Accept: application/json" -H "Authorization: token github_pat_XXX" https://api.github.com/repos/Jwalker107/AuthDownloadPlugin/releases

For troubleshooting, check the logfile.txt in the download plugin directory.  For more detailed logging, modify config.json and set log_level to 20 or to 10 (lower log level = more messages)

Other useful info on GitHub downloads:
* https://docs.github.com/en/rest/releases/assets?apiVersion=2022-11-28#get-a-release-asset
* https://github.com/orgs/community/discussions/47453
* https://gist.github.com/josh-padnick/fdae42c07e648c798fc27dec2367da21
* https://stackoverflow.com/questions/20396329/how-to-download-github-release-from-private-repo-using-command-line

To-Do:
* More error handling & logging.  If a plugin exception occurs (such as 'no saved token in keyring') the exception is not logged to the log file.
* Docs on testing with a manually-crafted download.json file
* Return exception messages (such as 'no saved token in keyring') as download message info files so they may be displayed in Console download status
* Handle other authentication types (BASIC auth via username/password)
* Handle different credentials per server / per URL
* Allow adding custom headers via config.json (as well as per-server/per-url headers)
