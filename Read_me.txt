### Install dependencies: ###
 - Install Python from https://www.python.org/ (Tested with Python 3.10.11 and Python 3.13.7)
 - Install Python modules via Cmd: pip install requests bs4 tqdm (for linux use: python3 -m pip install beautifulsoup4 requests tqdm)

### Configure the config.ini file ###
 - Copy config.ini.template to config.ini
 - Insert Artifactory username and password (token generated in artifactory)
 - Set your destination folder where the build subfolder will be created (Ex: D:\Builds\Idcevo)

### Changelog: 1.2 ###
 - Will work with packages link that starts with rse or cde instead of only idcevo.

### Changelog: 1.1 ###
 - Will download only SVTs mentioned in config file

### Changelog: 1.0 ###
 - Will request for "-packages" link
 - Will use config.ini file for auth, main download location and ipk prefixes
 - Will create build folder with dirty name
 - Will construct necasarry links for: ipks, dm-verity, svts and pdx
 - Will download ipks, dm-verity, svts and pdx (with progress bar) in custom Subfolder tree

### Troubleshooting: ###
 - Python is missing error:
'py' is not recognized as an internal or external command,
operable program or batch file.
Press any key to continue . . .
 - Solution: Install Python from https://www.python.org/
(Tested with Python 3.10.11 and Python 3.13.7)

 - Python module is missing error:
  File "D:\Idcevo_build_downloader\BMW_Artifactory_Build_Downloader_requests_1.1.py", line 3, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
Press any key to continue . . .
 - Solution: Install Python modules needed via Cmd using the following command: pip install requests bs4 tqdm
 (for linux use: python3 -m pip install beautifulsoup4 requests tqdm)

### Disclaimer ###
Script was vibe-coded by non-programmers. Something is broken means you are on your own. Just mannualy download your build like a normal person. ;)