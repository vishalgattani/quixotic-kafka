import socket
import subprocess

def get_hostip()->str:
    # Get the hostname
    hostname = socket.gethostname()

    # Get the IP address
    try:
        # Run the 'hostname -I' command and capture its output
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, check=True)
        # Split the output and take the first IP address
        ip_address = result.stdout.split()[0]
    except subprocess.CalledProcessError:
        # If 'hostname -I' fails, fall back to socket method
        ip_address = socket.gethostbyname(hostname)

    print(f"Hostname: {hostname}")
    print(f"IP Address: {ip_address}")
    return str(ip_address)