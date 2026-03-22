import subprocess
import os
import sys
import glob
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import argparse
import time
import base64
def normalize_url(url):
    url = url.strip()
    if url.endswith('/'):
        url = url[:-1]
    return url
def process_single_domain(target, cookie, use_headers):
    if not target:
        return None
    target = target.strip()
    if not target.startswith("http://") and not target.startswith("https://"):
        target = "https://" + target
    parsed = urlparse(target)
    if not parsed.hostname:
        print(f"ERROR: URL tidak valid: {target}")
        return None
    domain = parsed.hostname
    if parsed.port:
        domain = f"{domain}_{parsed.port}"
    output_dir = domain
    os.makedirs(output_dir, exist_ok=True)
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
            print(f"[INFO] [{domain}] Menjalankan Katana...")
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
            print(f"[INFO] [{domain}] Katana selesai")
            return True
        except Exception as e:
            print(f"[WARNING] [{domain}] Katana gagal: {e}")
            return False
    def run_gospider():
        try:
            print(f"[INFO] [{domain}] Menjalankan Gospider...")
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
                print(f"[INFO] [{domain}] Gospider selesai")
                return True
            else:
                print(f"[WARNING] [{domain}] Folder Gospider tidak ditemukan")
                return False
        except Exception as e:
            print(f"[WARNING] [{domain}] Gospider gagal: {e}")
            return False
    def run_hakrawler():
        try:
            print(f"[INFO] [{domain}] Menjalankan Hakrawler...")
            cmd = ["hakrawler", "-u", target, "-d", "5", "-wayback"]
            with open(hakrawler_file, "w") as f:
                subprocess.run(cmd, stdout=f, check=True, timeout=300)
            print(f"[INFO] [{domain}] Hakrawler selesai")
            return True
        except Exception as e:
            print(f"[WARNING] [{domain}] Hakrawler gagal: {e}")
            return False
    def run_waymore():
        try:
            print(f"[INFO] [{domain}] Menjalankan Waymore...")
            cmd = ["waymore", "-i", target, "-mode", "U", "-oU", waymore_file]
            subprocess.run(cmd, check=True, timeout=300)
            print(f"[INFO] [{domain}] Waymore selesai")
            return True
        except Exception as e:
            print(f"[WARNING] [{domain}] Waymore gagal: {e}")
            return False
    def run_urlfinder():
        try:
            print(f"[INFO] [{domain}] Menjalankan Urlfinder...")
            cmd = ["urlfinder", "-d", target, "-o", urlfinder_file]
            subprocess.run(cmd, check=True, timeout=300)
            print(f"[INFO] [{domain}] Urlfinder selesai")
            return True
        except Exception as e:
            print(f"[WARNING] [{domain}] Urlfinder gagal: {e}")
            return False
    print(f"[INFO] [{domain}] Starting crawling...")
    all_result_files = []
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
                    print(f"[INFO] [{domain}] {name} berhasil")
                    if name == "katana" and os.path.exists(katana_file):
                        all_result_files.append(katana_file)
                    elif name == "gospider" and os.path.exists(gospider_file):
                        all_result_files.append(gospider_file)
                    elif name == "hakrawler" and os.path.exists(hakrawler_file):
                        all_result_files.append(hakrawler_file)
                    elif name == "waymore" and os.path.exists(waymore_file):
                        all_result_files.append(waymore_file)
                    elif name == "urlfinder" and os.path.exists(urlfinder_file):
                        all_result_files.append(urlfinder_file)
                else:
                    print(f"[WARNING] [{domain}] {name} gagal")
            except Exception as e:
                print(f"[WARNING] [{domain}] {name} error: {e}")
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
    def collect_urls(file_list):
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
        unique_urls = {}
        for url in filtered_lines:
            normalized = normalize_url(url)
            if normalized not in unique_urls:
                unique_urls[normalized] = url
        return list(unique_urls.values())
    def run_httpx(urls, output_dir, cookie):
        if not urls:
            print(f"[INFO] [{domain}] Tidak ada URL untuk di-scan dengan httpx")
            return False
        temp_input = os.path.join(output_dir, "temp_urls.txt")
        with open(temp_input, "w") as f:
            for url in urls:
                f.write(url + "\n")
        print(f"[INFO] [{domain}] Menjalankan httpx untuk {len(urls)} URL...")
        cmd = ["httpx", "-l", temp_input, "-json", "-silent"]
        if cookie:
            cmd.extend(["-H", f"Cookie: {cookie}"])
        excluded_status_codes = {304, 400, 404, 408, 410, 429, 502, 503, 504}
        files = {
            200: open(os.path.join(output_dir, "200.txt"), "w"),
            300: open(os.path.join(output_dir, "300.txt"), "w"),
            400: open(os.path.join(output_dir, "400.txt"), "w"),
            500: open(os.path.join(output_dir, "500.txt"), "w")
        }
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            for line in process.stdout:
                try:
                    data = json.loads(line.strip())
                    url = data.get("url")
                    code = data.get("status_code")
                    if not url or code is None or code in excluded_status_codes:
                        continue
                    if 200 <= code < 300:
                        files[200].write(url + "\n")
                    elif 300 <= code < 400:
                        files[300].write(url + "\n")
                    elif 400 <= code < 500:
                        files[400].write(url + "\n")
                    elif 500 <= code < 600:
                        files[500].write(url + "\n")
                except:
                    continue
            process.wait()
        finally:
            for f in files.values():
                f.close()
            if os.path.exists(temp_input):
                os.remove(temp_input)
        for code in [200, 300, 400, 500]:
            filepath = os.path.join(output_dir, f"{code}.txt")
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    count = len(f.read().splitlines())
                    print(f"[INFO] [{domain}] {code}.txt: {count} URLs")
        return True
    if all_result_files:
        urls = collect_urls(all_result_files)
        print(f"[INFO] [{domain}] Total URL setelah filter: {len(urls)}")
        if urls:
            run_httpx(urls, output_dir, cookie)
        else:
            print(f"[WARNING] [{domain}] Tidak ada URL yang lolos filter")
    else:
        print(f"[WARNING] [{domain}] Tidak ada hasil dari crawling tools")
    temp_files = [katana_file, gospider_file, hakrawler_file, waymore_file, urlfinder_file]
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists(gospider_dir):
        import shutil
        shutil.rmtree(gospider_dir)
    print(f"[INFO] [{domain}] Selesai, hasil disimpan di folder {output_dir}/")
    return output_dir
def main():
    parser = argparse.ArgumentParser(description='Crawl Runner')
    parser.add_argument('-t', '--target', help='Target URL atau domain (single)')
    parser.add_argument('-l', '--list', help='File berisi list target')
    parser.add_argument('-c', '--cookie', help='Cookie string (optional)', default='')
    parser.add_argument('--use-headers', action='store_true', help='Use additional headers')
    args = parser.parse_args()
    if not args.target and not args.list:
        target = os.getenv("TARGET", "").strip()
        cookie = os.getenv("COOKIE", "").strip()
        use_headers = os.getenv("USE_HEADERS", "false").lower() == "true"
        if target:
            process_single_domain(target, cookie, use_headers)
        else:
            print("ERROR: TARGET atau list tidak ditemukan")
            sys.exit(1)
    elif args.list:
        cookie = args.cookie if args.cookie else os.getenv("COOKIE", "").strip()
        use_headers = args.use_headers or os.getenv("USE_HEADERS", "false").lower() == "true"
        try:
            with open(args.list, 'r') as f:
                targets = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"ERROR: Gagal membaca file list: {e}")
            sys.exit(1)
        print(f"[INFO] Memproses {len(targets)} target dengan max_workers=5")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for target in targets:
                time.sleep(1)
                futures[executor.submit(process_single_domain, target, cookie, use_headers)] = target
            for future in as_completed(futures):
                target = futures[future]
                try:
                    result = future.result()
                    if result:
                        print(f"[INFO] {target} selesai")
                except Exception as e:
                    print(f"[ERROR] {target} gagal: {e}")
    else:
        cookie = args.cookie if args.cookie else os.getenv("COOKIE", "").strip()
        use_headers = args.use_headers or os.getenv("USE_HEADERS", "false").lower() == "true"
        process_single_domain(args.target, cookie, use_headers)
if __name__ == "__main__":
    main()
