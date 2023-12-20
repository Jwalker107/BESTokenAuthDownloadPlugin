# TokenAuthDownload
BigFix Download Plug-In for Authenticated HTTPS downloads using token authentication (i.e. GitHub)

To build the plugin (assuming Python is already installed)
* Install requirements
  - pip install -r requirements.txt
* Test script loads
  - python TokenAuthDownload.py -h
* Create executable
  - pyinstaller --onefile TokenAuthDownload.py
  - generates dist\TokenAuthDownload\TokenAuthDownload.exe


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
* create an authentication token (assuming github.com, select your profile -> Settings -> Developer Options -> Personal Access Tokens).

* On the first run, and whenever your API token changes, update config.json and supply your token in the 'token' field.  The next time the plugin runs, the token will be removed from the config.json and stored in the system keyring (Windows Credential Manager, by default, on Windows; see Python Keyring module docs for info on other platforms)

To remove the download plugin, create file "plugin_TokenAuthDownload" and place in the Mirror Server\Inbox directory:

    {
       "message" : "remove",
       "protocol" : "TokenAuthDownload"
       
    }

To use the plugin, create a download action message such as
`prefetch bigfix.png sha1:9b84643d03b11e0d196c2967d7f870b1c212c165 size:4083 TokenAuthDownload://api.github.com/repos/Jwalker107/AuthDownloadPlugin/releases/assets/141569199 sha256:b658f7f01256d9f4a30270375050b829a99cc9ad8738463bc7c582fd6c3ee9bb`

To get the URL to a release asset for a GitHub repo, you may use a REST API client or curl command to retrieve, such as

    curl -H "Accept: application/json" -H "Authorization: token github_pat_XXX" https://api.github.com/repos/Jwalker107/AuthDownloadPlugin/releases

For troubleshooting, check the logfile.txt in the download plugin directory.  For more detailed logging, modify config.json and set log_level to 20 or to 10 (lower log level = more messages)