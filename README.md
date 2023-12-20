# AuthDownloadPlugin
BigFix Download Plug-In for Authenticated HTTPS downloads using token authentication (i.e. GitHub)

To build the plugin (assuming Python is already installed)
* Install requirements
  - pip install -r requirements.txt
* Test script loads
  - python TokenAuthDownload.py -h
* Create executable
  - pyinstaller TokenAuthDownload.py
  - generates build\TokenAuthDownload\TokenAuthDownload.exe


To Load Plugin on the BES Server:

Create json install file, ex. "plugin_TokenAuthDownload":

    {
       "message" : "add",
       "protocol" : "TokenAuthDownload",
       "location" : "C:\\Program Files (x86)\\BigFix Enterprise\\BES Server\\DownloadPlugins\\TokenDownloadPlugin\\TokenDownloadPlugin.exe"
    }

Place the file in C:\Program Files (x86)\BigFix Enterprise\BES Server\Mirror Server\Inbox.  The file is ingested by the BESRootServer and will be deleted from this directory when processed.
Create the target directory (`C:\Program Files (x86)\BigFix Enterprise\BES Server\DownloadPlugins\TokenDownloadPlugin` ) and copy `build\TokenDownloadPlugin\TokenDownloadPlugin.exe` to that directory.

To remove the download plugin, create file "plugin_TokenAuthDownload" and place in the Mirror Server\Inbox directory:

    {
       "message" : "remove",
       "protocol" : "TokenAuthDownload"
       
    }

To configure the plugin, 
* create an authentication token (assuming github.com, select your profile -> Settings -> Developer Options -> Personal Access Tokens).
* Execute TokenAuthDownload.exe --set_token
* When prompted, paste the Personal Access Token into the input field (the token will not be displayed on the screen)
* If you wish to remove the saved token later, delete it using the Windows Credential Manager interface

To use the plugin, create a download action message such as
`prefetch MyReadme.md size:79 sha1:f919f61f325ff604e9359f8f448d3d1120cc81f2 url:TokenAuthDownload://raw.githubusercontent.com/Jwalker107/AuthDownloadPlugin/main/README.md sha256:82c9427a5aa78a76c5c89d003427b8f692a45a91c7aa50a09b93bb1cf3ace8d7`
