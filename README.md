# TokenAuthDownload
BigFix Download Plug-In for Authenticated HTTPS downloads using token authentication (i.e. GitHub)

**This is not a supported BigFix tool and is for demonstration purposes.  Use at your own risk**

## To build the plugin (assuming Python is already installed)
* Install requirements
  - pip install -r requirements.txt
* Test script loads
  - python TokenAuthDownload.py -h
* Create executable
  - pyinstaller --onefile TokenAuthDownload.py
  - generates dist\TokenAuthDownload\TokenAuthDownload.exe
  - ref https://pyinstaller.org/en/v4.8/usage.html


## To Load Plugin on the BES Server:

Create json install file, ex. "plugin_TokenAuthDownload" (filename should begin with 'plugin_' and have no filename extension):

    {
       "message" : "add",
       "protocol" : "TokenAuthDownload",
       "location" : "C:\\Program Files (x86)\\BigFix Enterprise\\BES Server\\DownloadPlugins\\TokenAuthDownload\\TokenAuthDownload.exe"
    }

Place the file in C:\Program Files (x86)\BigFix Enterprise\BES Server\Mirror Server\Inbox.  The file is ingested by the BESRootServer and will be deleted from this directory when processed.

Create the target directory (`C:\Program Files (x86)\BigFix Enterprise\BES Server\DownloadPlugins\TokenAuthDownload` ) and copy `dist\TokenAuthDownload\TokenAuthDownload.exe` and `config.json` to that directory.

## To configure the plugin, 
* create (at least one) authentication token (assuming github.com, select your profile -> Settings -> Developer Options -> Personal Access Tokens).
* Create a config.json file based upon the example sample-config.json provided in this repository, and place config.json in the `BES Server\DownloadPlugins\TokenAuthDownload` directory.
* The config.json contains a stanza for `url_configs` allowing to specify multiple configurations.
  - Each url configuration contains a a `url_list` array.  Each element is a Regular Expression.  The requested download URL is compared to each regular expression in the `url_list`.  If the requested url matches multiple `url_list` entries, the longest regular expression matched is selected.
  - Update the `token` entry of each `url_config` when first installing the Download Plug-In, and whenever the given token is updated.
  - Provide a unique `config_name` value for each `url_configs` entry. The top-level `plugin_name` is combined with each `url_configs.config_name` to determine the name of the token that will be stored in the Keyring (Windows Credential Manager on Windows, by default).  I.e. `TokenAuthPlugin_configuration1`
  - Hint: To use the same token for _all_ urls, a default regex to 'match anything' is `.*`
  - Hint: In a Regular Expression, the '`.`' symbol is a wildcard that matches any character.  To literally match the '.' symbols in `server.domain.com` one must escape the '.' character as `server\.domain\.com`.  Further, in JSON the backslash character must be escaped as `\\`, so to match a URL of `"https://<anything>.example.com/<anything>"` the config.json entry should read `"https://.*\\.example\\.com/.*"`
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

## To test the plugin outside of BigFix
* Ensure a valid config.json exists in the directory of the script or executable version of TokenDownloadPlugin.
* Create a downloads.json file (see 'sample-downloads.json' in this repo for an example).
* Execute _either_ the compiled TokenAuthDownload.exe _or_ the Python script.  Use the command-line arguments `--downloads "path_to_sample_downloads.json"`.  i.e.
  - TokenAuthDownload.exe --downloads "c:\temp\sample-downloads.json"
* Script execution logs are displayed to the terminal as well as to whatever log location is specified in the configuration file.

Other useful info on GitHub downloads:
* https://docs.github.com/en/rest/releases/assets?apiVersion=2022-11-28#get-a-release-asset
* https://github.com/orgs/community/discussions/47453
* https://gist.github.com/josh-padnick/fdae42c07e648c798fc27dec2367da21
* https://stackoverflow.com/questions/20396329/how-to-download-github-release-from-private-repo-using-command-line

To-Do:
* Handle other authentication types (BASIC auth via username/password)
* Allow adding custom headers via config.json (as well as per-server/per-url headers)
