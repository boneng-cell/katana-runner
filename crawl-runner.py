import subprocess
import os
import sys
import glob
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

target = os.getenv("TARGET", "").strip()
cookie = os.getenv("COOKIE", "").strip()
use_headers = os.getenv("USE_HEADERS", "false").lower() == "true"

if not target:
    print("ERROR: TARGET tidak boleh kosong")
    sys.exit(1)

if not target.startswith("http://") and not target.startswith("https://"):
    target = "https://" + target

parsed = urlparse(target)
if not parsed.hostname:
    print("ERROR: URL tidak valid")
    sys.exit(1)

domain = parsed.hostname
if parsed.port:
    domain = f"{domain}_{parsed.port}"

active_output = f"{domain}_active.txt"
passive_output = f"{domain}_passive.txt"

headers = []
if use_headers:
    headers.extend([
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language: en-US,en;q=0.9",
        "Referer: https://google.com"
    ])

if cookie:
    headers.append(f"Cookie: {cookie}")

go_bin = os.path.expanduser("~/go/bin")
os.environ["PATH"] += os.pathsep + go_bin

katana_file = f"{domain}_katana.txt"
gospider_file = f"{domain}_gospider.txt"
hakrawler_file = f"{domain}_hakrawler.txt"
waymore_file = f"{domain}_waymore.txt"
urlfinder_file = f"{domain}_urlfinder.txt"
gospider_dir = f"gospider_{domain}"

def run_katana():
    try:
        print(f"[INFO] Menjalankan Katana...")
        cmd = ["katana", "-u", target]
        for h in headers:
            cmd.extend(["-H", h])
        cmd.extend([
            "-fr", "(logout|log-out|signout|sign-out|sign_off|exit|destroy|terminate|delete-session|invalidate)",
            "-jc", "-xhr", "-fx",
            "-d", "5",
            "-c", "5",
            "-rl", "3",
            "-rd", "2",
            "-timeout", "15",
            "-retry", "2",
            "-tlsi",
            "-aff",
            "-s", "breadth-first",
            "-o", katana_file
        ])
        subprocess.run(cmd, check=True, timeout=300)
        print(f"[INFO] Katana selesai")
        return True
    except Exception as e:
        print(f"[WARNING] Katana gagal: {e}")
        return False

def run_gospider():
    try:
        print(f"[INFO] Menjalankan Gospider...")
        if os.path.exists(gospider_dir):
            import shutil
            shutil.rmtree(gospider_dir)
        cmd = [
            "gospider",
            "-s", target,
            "-o", gospider_dir,
            "-d", "5",
            "-c", "5",
            "-t", "3"
        ]
        subprocess.run(cmd, check=True, timeout=300)
        if os.path.exists(gospider_dir):
            with open(gospider_file, "w") as outfile:
                txt_files = glob.glob(f"{gospider_dir}/*.txt")
                for txt_file in txt_files:
                    try:
                        with open(txt_file, "r") as infile:
                            outfile.write(infile.read())
                    except:
                        pass
            print(f"[INFO] Gospider selesai")
            return True
        else:
            print(f"[WARNING] Folder Gospider tidak ditemukan")
            return False
    except Exception as e:
        print(f"[WARNING] Gospider gagal: {e}")
        return False

def run_hakrawler():
    try:
        print(f"[INFO] Menjalankan Hakrawler...")
        cmd = ["hakrawler", "-u", target, "-d", "5", "-wayback"]
        with open(hakrawler_file, "w") as f:
            subprocess.run(cmd, stdout=f, check=True, timeout=300)
        print(f"[INFO] Hakrawler selesai")
        return True
    except Exception as e:
        print(f"[WARNING] Hakrawler gagal: {e}")
        return False

def run_waymore():
    try:
        print(f"[INFO] Menjalankan Waymore...")
        cmd = ["waymore", "-i", target, "-mode", "U", "-oU", waymore_file]
        subprocess.run(cmd, check=True, timeout=300)
        print(f"[INFO] Waymore selesai")
        return True
    except Exception as e:
        print(f"[WARNING] Waymore gagal: {e}")
        return False

def run_urlfinder():
    try:
        print(f"[INFO] Menjalankan Urlfinder...")
        cmd = ["urlfinder", "-d", target, "-o", urlfinder_file]
        subprocess.run(cmd, check=True, timeout=300)
        print(f"[INFO] Urlfinder selesai")
        return True
    except Exception as e:
        print(f"[WARNING] Urlfinder gagal: {e}")
        return False

print("[INFO] Starting crawling...")

active_results = []
passive_results = []

if cookie:
    print("[INFO] Cookie detected → hanya menjalankan Katana")
    success = run_katana()
    if success and os.path.exists(katana_file):
        active_results = [katana_file]
    else:
        print("[ERROR] Katana gagal menjalankan tugas")
        sys.exit(1)
else:
    print("[INFO] No cookie → menjalankan semua crawler paralel")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(run_katana): "katana",
            executor.submit(run_gospider): "gospider",
            executor.submit(run_hakrawler): "hakrawler",
            executor.submit(run_waymore): "waymore",
            executor.submit(run_urlfinder): "urlfinder"
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if result:
                    print(f"[INFO] {name} berhasil")
                    if name == "katana" and os.path.exists(katana_file):
                        active_results.append(katana_file)
                    elif name == "gospider" and os.path.exists(gospider_file):
                        active_results.append(gospider_file)
                    elif name == "hakrawler" and os.path.exists(hakrawler_file):
                        active_results.append(hakrawler_file)
                    elif name == "waymore" and os.path.exists(waymore_file):
                        passive_results.append(waymore_file)
                    elif name == "urlfinder" and os.path.exists(urlfinder_file):
                        passive_results.append(urlfinder_file)
                else:
                    print(f"[WARNING] {name} gagal")
            except Exception as e:
                print(f"[WARNING] {name} error: {e}")

static_extensions = (
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff', '.psd',
    '.css', '.scss', '.sass', '.less',
    '.js', '.jsx', '.ts', '.tsx', '.vue',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.mp4', '.mp3', '.avi', '.mov', '.wmv', '.flv', '.mkv',
    '.xml', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.txt', '.md', '.log'
)

def process_files(file_list, output_file):
    if not file_list:
        return []
    all_lines = []
    for fname in file_list:
        if os.path.exists(fname):
            try:
                with open(fname, "r") as infile:
                    all_lines.extend(infile.readlines())
            except:
                pass
    filtered_lines = []
    for line in all_lines:
        line_stripped = line.strip()
        if line_stripped:
            if any(line_stripped.lower().endswith(ext) for ext in static_extensions):
                continue
            if any(f"/{ext.lstrip('.')}/" in line_stripped.lower() for ext in static_extensions[:10]):
                continue
            filtered_lines.append(line_stripped)
    unique_lines = sorted(set(filtered_lines))
    with open(output_file, "w") as f:
        for line in unique_lines:
            f.write(line + "\n")
    return unique_lines

if active_results:
    active_urls = process_files(active_results, active_output)
    print(f"[INFO] Active URLs: {len(active_urls)} disimpan ke {active_output}")
if passive_results:
    passive_urls = process_files(passive_results, passive_output)
    print(f"[INFO] Passive URLs: {len(passive_urls)} disimpan ke {passive_output}")

temp_files = [katana_file, gospider_file, hakrawler_file, waymore_file, urlfinder_file]
for f in temp_files:
    if os.path.exists(f):
        os.remove(f)

if os.path.exists(gospider_dir):
    import shutil
    shutil.rmtree(gospider_dir)

print(f"[INFO] Selesai")
