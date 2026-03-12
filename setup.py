import os
import subprocess
import time
import sys
import shutil

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================

FRP_CONFIG = {
    "server_addr": "18.141.195.132",  # Your Singapore Server IP
    "server_port": 7000,            # Control Port
    "token":       "gg.gg",         # Auth Token
    "remote_port": 6000,            # Juice Port (TCP & UDP)
    "local_port":  43210            # Internal Port
}

# ==========================================
# ⚙️ UTILS
# ==========================================

def log(msg):
    print(f"\033[92m{msg}\033[0m")  # Green text

def run_live(command):
    print(f"\033[94m🔹 {command}\033[0m")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end='', flush=True)
    process.wait()
    return process.returncode

def cleanup():
    log("\n🧹 Cleaning up old processes...")
    subprocess.run("pkill -9 agent", shell=True, stderr=subprocess.DEVNULL)
    subprocess.run("pkill -9 frpc", shell=True, stderr=subprocess.DEVNULL)
    if os.path.exists("frpc.toml"): os.remove("frpc.toml")
    if os.path.exists("frpc"): os.remove("frpc")  # Force update

def optimize_network():
    log("\n🚀 Optimizing Network Stack for Low Latency...")
    # Increase buffers for high-speed UDP gaming
    cmds = [
        "sysctl -w net.core.rmem_max=26214400",
        "sysctl -w net.core.wmem_max=26214400",
        "sysctl -w net.ipv4.udp_mem='8388608 12582912 16777216'"
    ]
    for cmd in cmds:
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL)

def get_nvidia_version():
    try:
        return subprocess.check_output("nvidia-smi --query-gpu=driver_version --format=csv,noheader", shell=True).decode().strip().split('.')[0]
    except:
        return "535"

# ==========================================
# 🛠️ MAIN AUTOMATION
# ==========================================

def main():
    log("====================================================")
    log("   JUICE SERVER: MASTER EDITION (Region Optimized)  ")
    log("====================================================")

    # 1. CLEANUP & NETWORK TUNE
    cleanup()
    optimize_network()

    # 2. PING CHECK (Verify Region Fix)
    log(f"\n📡 VERIFYING LATENCY to {FRP_CONFIG['server_addr']}...")
    try:
        # Check ping count 4
        ping_out = subprocess.check_output(f"ping -c 4 {FRP_CONFIG['server_addr']}", shell=True, text=True)
        print(ping_out)
        if "time=" in ping_out:
            import re
            ms = float(re.search(r'time=([\d\.]+)', ping_out).group(1))
            if ms < 40: log(f"✅ EXCELLENT LATENCY: {ms}ms (60 FPS Possible)")
            else: print(f"⚠️ WARNING: Latency is {ms}ms. FPS may still be limited.")
    except:
        print("⚠️ Could not ping server.")

    # 3. INSTALL DRIVERS & VULKAN
    log("\n🎮 Installing Graphics Libraries...")
    run_live("dpkg --add-architecture i386 && apt-get update -qq")
    drv = get_nvidia_version()
    libs = f"libvulkan1 libvulkan1:i386 vulkan-tools libnvidia-gl-{drv} libnvidia-gl-{drv}:i386"

    if run_live(f"DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends {libs}") != 0:
        log("⚠️ Retrying install...")
        run_live("apt-get --fix-broken install -y")
        run_live(f"DEBIAN_FRONTEND=noninteractive apt-get install -y {libs}")

    # 4. SETUP FRP v0.66 (Raw Mode)
    log("\n🔗 Setting up FRP Tunnel...")
    frp_url = "https://github.com/fatedier/frp/releases/download/v0.66.0/frp_0.66.0_linux_amd64.tar.gz"
    run_live(f"wget -q -O frp.tar.gz {frp_url} && tar -zxf frp.tar.gz --strip-components=1")
    os.chmod("frpc", 0o755)

    # Create Config (TCP + UDP)
    config = f"""
serverAddr = "{FRP_CONFIG['server_addr']}"
serverPort = {FRP_CONFIG['server_port']}
auth.method = "token"
auth.token = "{FRP_CONFIG['token']}"

# Tunnel 1: TCP (Handshake)
[[proxies]]
name = "juice-tcp"
type = "tcp"
localIP = "127.0.0.1"
localPort = {FRP_CONFIG['local_port']}
remotePort = {FRP_CONFIG['remote_port']}
transport.useCompression = false
transport.useEncryption = false

# Tunnel 2: UDP (Gaming Stream)
[[proxies]]
name = "juice-udp"
type = "udp"
localIP = "127.0.0.1"
localPort = {FRP_CONFIG['local_port']}
remotePort = {FRP_CONFIG['remote_port']}
transport.useCompression = false
transport.useEncryption = false
    """
    with open("frpc.toml", "w") as f: f.write(config)

    # Start FRP
    log("🔹 Starting FRP...")
    with open("frp.log", "w") as f:
        subprocess.Popen(["./frpc", "-c", "frpc.toml"], stdout=f, stderr=f)
    time.sleep(3)

    if int(subprocess.getoutput("pgrep -c frpc")) == 0:
        log("❌ FRP FAILED. Logs:"); run_live("cat frp.log")
        return
    log("✅ FRP Connected!")

    # 5. START JUICE AGENT
    log("\n🍊 Downloading & Launching Juice Agent...")
    if not os.path.exists("agent"):
        os.makedirs("agent")  # Create the agent folder if it doesn't exist

    # Download and extract Juice
    run_live("curl -L -o Juice.tar.gz https://github.com/Juice-Labs/Juice-Labs/releases/download/2023.06.07-0136.d9bc8ad1/JuiceServer-linux.tar.gz")
    run_live("tar -zxf Juice.tar.gz -C agent --strip-components=1")  # Extract to the 'agent' folder
    os.chmod("agent/setup.sh", 0o755)  # Make setup.sh executable

    # Run the setup script
    log("\n🚀 Running Setup...")
    run_live("./agent/setup.sh")

    # Run Juice Agent
    log("\n🚀 Running Juice Agent...")
    os.chmod("agent/run.sh", 0o755)  # Make run.sh executable
    run_live("./agent/run.sh")

    log(f"\n🚀 SERVER READY ON: {FRP_CONFIG['server_addr']}:{FRP_CONFIG['remote_port']}")
    log("--- LIVE LOGS ---")

    try:
        # High Priority + 0.0.0.0 Bind
        cmd = "nice -n -20 ./setu"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in iter(process.stdout.readline, ""):
            if line:
                clean = line.strip()
                if "Info" in clean: print(f"\033[92m[INFO]\033[0m {clean}")
                elif "Error" in clean: print(f"\033[91m[ERROR]\033[0m {clean}")
                else: print(f"🍊 {clean}")
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
