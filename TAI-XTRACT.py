import os
import requests
import builtwith
import socket
import whois
import dns.resolver
import re
import json
import subprocess
from bs4 import BeautifulSoup
from termcolor import colored
from tqdm import tqdm
import time

# Disable SSL Warnings
requests.packages.urllib3.disable_warnings()

BASE_PATH = "/storage/emulated/0/XTRACT/"

def banner():
    """🚀 Eye-Catching Terminal Banner"""
    print(colored("\n=== XTRACT v13.0 | Ultimate Recon Tool ===", "cyan"))

def sanitize_filename(url):
    return re.sub(r'[\/:*?"<>|]', '_', url)

def create_website_folder(url):
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    folder_path = os.path.join(BASE_PATH, domain)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def get_filename(folder, name, extension):
    return os.path.join(folder, f"{name}.{extension}")

def get_ip_address(url):
    """Find IP Address of the Target"""
    try:
        ip = socket.gethostbyname(url.replace("https://", "").replace("http://", "").split("/")[0])
        print(colored(f"\n[+] IP Address: {ip}", "yellow"))
        return ip
    except:
        print(colored("[-] Could not resolve IP address", "red"))
        return None

def detect_cms(url):
    """Detect CMS & Technology Stack"""
    try:
        tech_info = builtwith.builtwith(url)
        print(colored("\n[+] CMS & Technologies:", "cyan"))
        for key, value in tech_info.items():
            print(colored(f"{key}: {', '.join(value)}", "yellow"))
        return tech_info
    except:
        print(colored("[-] Unable to detect CMS & Tech", "red"))
        return None

def find_subdomains(url):
    """Find Subdomains using CRT.sh"""
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    crt_url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        response = requests.get(crt_url, timeout=10)
        subdomains = set(entry["name_value"] for entry in json.loads(response.text))
        print(colored("\n[+] Found Subdomains:", "cyan"))
        for sub in subdomains:
            print(colored(sub, "yellow"))
        return subdomains
    except:
        print(colored("[-] Failed to retrieve subdomains", "red"))
        return []

def find_dns_records(url):
    """Find DNS Records"""
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    records = ["A", "AAAA", "CNAME", "MX", "TXT", "NS"]
    print(colored("\n[+] DNS Records:", "cyan"))
    for record in records:
        try:
            answers = dns.resolver.resolve(domain, record)
            for rdata in answers:
                print(colored(f"{record}: {rdata}", "yellow"))
        except:
            continue

def find_open_ports(url):
    """Scan Open Ports"""
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    ports = [21, 22, 25, 53, 80, 443, 3306, 8080]
    print(colored("\n[+] Open Ports:", "cyan"))
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((domain, port))
        if result == 0:
            print(colored(f"Port {port}: Open", "yellow"))
        sock.close()

def find_admin_panels(url):
    """Find Admin Panels & Login Pages"""
    common_panels = ["admin", "login", "wp-admin", "cpanel", "dashboard", "user/login"]
    print(colored("\n[+] Searching for Admin Panels...", "cyan"))
    for panel in tqdm(common_panels):
        full_url = f"{url}/{panel}"
        try:
            response = requests.get(full_url, timeout=5)
            if response.status_code == 200:
                print(colored(f"Found: {full_url}", "green"))
        except:
            continue

def find_waf(url):
    """Detect Web Application Firewall (WAF)"""
    try:
        response = requests.get(url, timeout=10)
        waf_headers = ["Server", "X-Security", "X-Powered-By", "CF-RAY"]
        print(colored("\n[+] WAF Detection:", "cyan"))
        for header in waf_headers:
            if header in response.headers:
                print(colored(f"{header}: {response.headers[header]}", "yellow"))
    except:
        print(colored("[-] Unable to detect WAF", "red"))

def find_js_endpoints(url):
    """Extract JavaScript Files & Endpoints"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        js_files = [script["src"] for script in soup.find_all("script", src=True)]
        print(colored("\n[+] JavaScript Files:", "cyan"))
        for js in js_files:
            print(colored(js, "yellow"))

        # Extract API Keys
        api_pattern = re.compile(r'(?i)(apikey|token|secret)[\s=:]+["\']?([A-Za-z0-9_\-]{10,})["\']?')
        found_keys = []
        for js_file in js_files:
            try:
                js_response = requests.get(js_file, timeout=5)
                found_keys.extend(api_pattern.findall(js_response.text))
            except:
                continue
        if found_keys:
            print(colored("\n[✔] API Keys Found!", "green"))
            for key in found_keys:
                print(colored(f"{key[0]}: {key[1]}", "yellow"))
    except:
        print(colored("[-] Failed to extract JS files", "red"))

def find_sql_vulnerabilities(url):
    """Basic SQL Injection Point Detection"""
    sql_payloads = ["'", "1' OR '1'='1", "';--", '" or ""="', "OR 1=1"]
    print(colored("\n[+] Testing for SQL Injection...", "cyan"))
    for payload in tqdm(sql_payloads):
        try:
            test_url = f"{url}/?id={payload}"
            response = requests.get(test_url, timeout=5)
            if "SQL syntax" in response.text or "mysql_fetch" in response.text:
                print(colored(f"Potential SQL Injection: {test_url}", "red"))
        except:
            continue

def extract_wayback_data(url):
    """Retrieve URLs from Wayback Machine"""
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    wayback_url = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json"
    try:
        response = requests.get(wayback_url, timeout=10)
        urls = [entry[2] for entry in json.loads(response.text)[1:]]
        print(colored("\n[+] Wayback Machine URLs:", "cyan"))
        for u in urls:
            print(colored(u, "yellow"))
    except:
        print(colored("[-] No Wayback Data Found", "red"))

def main():
    banner()
    target_url = input(colored("\n[?] Enter Target Website: ", "cyan")).strip()
    
    os.system("chmod -R 777 " + BASE_PATH)
    
    folder = create_website_folder(target_url)
    
    get_ip_address(target_url)
    detect_cms(target_url)
    find_subdomains(target_url)
    find_dns_records(target_url)
    find_open_ports(target_url)
    find_admin_panels(target_url)
    find_waf(target_url)
    find_js_endpoints(target_url)
    find_sql_vulnerabilities(target_url)
    extract_wayback_data(target_url)

    print(colored("\n[✔] Scan Complete!", "green"))

if __name__ == "__main__":
    main()