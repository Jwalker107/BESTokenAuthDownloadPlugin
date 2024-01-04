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
  - _Note_: Because the keyring is stored per-user, saving the token in the keyring *must* be performed by the user account of the BESRootServer service (LocalSystem, by default); so the key should be stored by issuing a BigFix Action that references the plug-in, to ensure the Download PlugIn is executed by the BESRootServer process.

## Example config.json:
The following example configuration defines three configurations.  The url_configs and token for 'default' will be used for any download that does not match one of the other two example url_configs entries.  Three tokens may be stored; they will be named `TokenAuthDownload_default`, `TokenAuthConfig_internal-server-1`, or `TokenAuthConfig_github`.  On first run, the "token" value in the 'default' stanza will be removed from the configuration file and stored in the system keyring.  

    {
      "plugin_name": "TokenAuthDownload",
      "log": "c:\\temp\\logfile.txt",
      "log_level": 20,
      "url_configs": [
        {
          "config_name": "default",
          "url_list": [
            ".*"
          ],
          "token": "pat_token_XXXXXXX"
        },
        {
          "config_name": "internal-server-1",
          "url_list": [
            "https://.*\\.mycompany\\.example\\.com(:\\d+){0,1}/.*"
          ],
          "token": null
        },
        
        {
          "config_name": "github",
          "url_list": [
            "https://.*\\.github\\.com/.*",
            "https://.*\\.githubusercontent\\.com/.*"
          ],
          "token": null
        }
      ]
    }

## To remove the download plugin from the BES Server, create file "plugin_TokenAuthDownload" and place in the Mirror Server\Inbox directory:

    {
       "message" : "remove",
       "protocol" : "TokenAuthDownload"
       
    }

To use the plugin, create a download action message such as
`prefetch bigfix.png sha1:9b84643d03b11e0d196c2967d7f870b1c212c165 size:4083 TokenAuthDownload://api.github.com/repos/Jwalker107/AuthDownloadPlugin/releases/assets/141569199 sha256:b658f7f01256d9f4a30270375050b829a99cc9ad8738463bc7c582fd6c3ee9bb`

To get the URL to a release asset for a GitHub repo, you may use a REST API client or curl command to retrieve, such as

    curl -H "Accept: application/json" -H "Authorization: token github_pat_XXX" https://api.github.com/repos/Jwalker107/BESTokenAuthDownloadPlugin/releases

For troubleshooting, check the logfile.txt in the download plugin directory.  For more detailed logging, modify config.json and set log_level to 20 or to 10 (lower log level = more messages)

## To test the plugin outside of BigFix
* Ensure a valid config.json exists in the directory of the script or executable version of TokenDownloadPlugin.
* Create a downloads.json file (see 'sample-downloads.json' in this repo for an example).
* Execute _either_ the compiled TokenAuthDownload.exe _or_ the Python script.  Use the command-line arguments `--downloads "path_to_sample_downloads.json"`.  i.e.
  - TokenAuthDownload.exe --downloads "c:\temp\sample-downloads.json"
* Script execution logs are displayed to the terminal as well as to whatever log location is specified in the configuration file.
* _Note_: Because the BESRootServer process executes in a distinct user context, you may need to test the plug-in by running in the same user account as the BESRootServer service; or repeat storing the personal access token to the keyring in both your own user account and in the BESRootServer service's account.

## Other useful info on GitHub downloads:
* https://docs.github.com/en/rest/releases/assets?apiVersion=2022-11-28#get-a-release-asset
* https://github.com/orgs/community/discussions/47453
* https://gist.github.com/josh-padnick/fdae42c07e648c798fc27dec2367da21
* https://stackoverflow.com/questions/20396329/how-to-download-github-release-from-private-repo-using-command-line

## Related:
* https://forum.bigfix.com/t/introduction-to-bigfix-download-plugins-technical/18867

## To-Do:
* Handle other authentication types (BASIC auth via username/password)
* Allow adding custom headers via config.json (as well as per-server/per-url headers)
