import os
import re
import requests
from bs4 import BeautifulSoup
import tarfile
from tqdm import tqdm
import configparser
import sys

# ==== Changelog: 1.2 ====
# - Will work with packages link that starts with rse or cde instead of only idcevo.

# ==== Changelog: 1.1 ====
# - Will download only SVTs mentioned in config file

# ==== Changelog: 1.0 ====
# - Will request for "-packages" link
# - Will use config.ini file for auth, main download location and ipk prefixes
# - Will create build folder with dirty name
# - Will construct necasarry links for: ipks, dm-verity, svts and pdx
# - Will download ipks, dm-verity, svts and pdx (with progress bar) in custom Subfolder tree

# ==== CONFIGURATION ====
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.ini")
config = configparser.ConfigParser()

# Try to read the config file
try:
    config.read(config_path)
    username = config["auth"]["username"]
    password = config["auth"]["password"]
    base_download_dir = config["download"]["base_download_dir"]
    prefixes = [p.strip() for p in config["ipks"]["prefixes"].split(",") if p.strip()]
    svt_variants = [v.strip() for v in config["svts"]["variants"].split(",") if v.strip()]
except KeyError as e:
    print(f"ERROR: Missing expected section or key in config.ini: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to read configuration: {e}")
    sys.exit(1)

# ==== STEP 1: Ask for the base packages folder ====
packages_url = input("Enter the packages folder URL (ending with '-packages/'): ").strip()
if not packages_url.endswith("/"):
    packages_url += "/"

# Extract dirty build name for folder
dirty_name = re.search(r'(idcevo|rse[^-]*|cde[^-]*)-hv-(.*?)-packages', packages_url).group(2)
main_download_folder = os.path.join(base_download_dir, f"{dirty_name}")
os.makedirs(main_download_folder, exist_ok=True)

# ==== STEP 2: Prepare IPK page URL ====
page_url = packages_url.replace("/ui/native/", "/artifactory/") + "cortexa76/"
ipk_folder = os.path.join(main_download_folder, "IPKs")
os.makedirs(ipk_folder, exist_ok=True)

# ==== FETCH IPK DIRECTORY LISTING ====
r = requests.get(page_url, auth=(username, password))
if r.status_code != 200:
    raise SystemExit(f"Failed to fetch IPK page (check Artifactory connection or auth in config.ini): HTTP {r.status_code}")

soup = BeautifulSoup(r.text, "html.parser")
links = [a["href"] for a in soup.find_all("a", href=True)]

# ==== DOWNLOAD IPKs ====
for prefix in prefixes:
    matches = [l for l in links if prefix in l and l.endswith(".ipk")]
    if not matches:
        print(f"No IPK found for prefix: {prefix}")
        continue

    for ipk_name in matches:
        ipk_url = page_url + ipk_name if not ipk_name.startswith("http") else ipk_name
        local_path = os.path.join(ipk_folder, os.path.basename(ipk_url))
        resp = requests.get(ipk_url, auth=(username, password), stream=True)
        if resp.status_code == 200:
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Saved: {os.path.basename(local_path)}")
        else:
            print(f"Failed to download {ipk_url}: HTTP {resp.status_code}")

# ==== DM-VERITY DOWNLOAD ====
dmverity_url = re.sub(r'linux/(idcevo|rse[^-]*|cde[^-]*)-hv/\1-hv-.*?-packages/', 'system-assembly/userdebug_DEV/', packages_url.replace('/ui/native/', '/artifactory/'))
dmverity_folder = os.path.join(main_download_folder, "dm-verity")
os.makedirs(dmverity_folder, exist_ok=True)

r = requests.get(dmverity_url, auth=(username, password))
if r.status_code == 200:
    soup = BeautifulSoup(r.text, "html.parser")
    dmverity_link = next((a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith("disable-dmverity-dev_signed.tar.gz")), None)
    if dmverity_link:
        dmverity_url_full = dmverity_url + dmverity_link if not dmverity_link.startswith("http") else dmverity_link
        local_dmverity = os.path.join(dmverity_folder, os.path.basename(dmverity_url_full))
        resp = requests.get(dmverity_url_full, auth=(username, password), stream=True)
        if resp.status_code == 200:
            with open(local_dmverity, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Dm-verity saved!")
            # Extract
            with tarfile.open(local_dmverity, "r:gz") as tar:
                def safe_filter(tarinfo, path):
                    # keep current behaviour: extract all files as-is
                    return tarinfo
                tar.extractall(dmverity_folder, filter=safe_filter)
            os.remove(local_dmverity)
            print(f"Dm-verity extracted!")
        else:
            print(f"Failed to download dm-verity: HTTP {resp.status_code}")
else:
    print(f"Failed to fetch dm-verity folder: HTTP {r.status_code}")

# ==== SVT DOWNLOAD ====
svt_url = dmverity_url + "pdx/"
svt_folder = os.path.join(main_download_folder, "SVT")
os.makedirs(svt_folder, exist_ok=True)

r = requests.get(svt_url, auth=(username, password))
if r.status_code == 200:
    soup = BeautifulSoup(r.text, "html.parser")
    svt_links = [a["href"] for a in soup.find_all("a", href=True) if a["href"] in svt_variants]
    for svt in svt_links:
        svt_url_full = svt_url + svt if not svt.startswith("http") else svt
        local_svt = os.path.join(svt_folder, os.path.basename(svt_url_full))
        resp = requests.get(svt_url_full, auth=(username, password), stream=True)
        if resp.status_code == 200:
            with open(local_svt, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Saved: {os.path.basename(local_svt)}")
        else:
            print(f"Failed to download SVT: HTTP {resp.status_code}")
else:
    print(f"Failed to fetch SVT folder: HTTP {r.status_code}")

# ==== DOWNLOAD PDX FILE ====
print("\nChecking for .pdx file...")
r = requests.get(svt_url, auth=(username, password))  # svt_url is the page where SVTs are
if r.status_code == 200:
    soup = BeautifulSoup(r.text, "html.parser")
    pdx_link = next((a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith(".pdx")), None)
    
    if pdx_link:
        pdx_url = svt_url.replace("/ui/native/", "/artifactory/") + pdx_link
        pdx_local_path = os.path.join(main_download_folder, os.path.basename(pdx_link))
        print(f"Downloading .pdx file: {os.path.basename(pdx_link)} ...")

        # Stream download with progress bar
        with requests.get(pdx_url, auth=(username, password), stream=True) as r_stream:
            r_stream.raise_for_status()
            total_size = int(r_stream.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1 MB
            with open(pdx_local_path, 'wb') as f, tqdm(
                total=total_size, unit='B', unit_scale=True, unit_divisor=1024,
                desc=os.path.basename(pdx_link)
            ) as bar:
                for chunk in r_stream.iter_content(chunk_size=block_size):
                    f.write(chunk)
                    bar.update(len(chunk))
        print(f"Saved: {os.path.basename(pdx_link)}")
    else:
        print("No .pdx file found in SVT folder.")
else:
    print(f"Failed to fetch SVT folder page for .pdx lookup (HTTP {r.status_code})")