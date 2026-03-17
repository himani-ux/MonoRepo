# logbook/utils.py
import socket
import struct

def get_local_ip():
    """
    Attempts to determine the machine's local IP address on the LAN.
    This method connects to a remote address (doesn't actually send data)
    to figure out which local interface would be used for that connection,
    thereby revealing the local IP associated with that interface.
    """
    try:
        # Connect to a remote address (e.g., Google's DNS, or even a non-routable IP)
        # This doesn't actually send data over the network due to UDP.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use a non-routable IP to ensure it doesn't leave the local network
        s.connect(("10.254.254.254", 1)) # This IP is non-routable, just for interface detection
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP using socket connect: {e}")
        # Fallback: Try to get hostname and resolve it (might return 127.0.0.1 if hostname maps to loopback)
        try:
            hostname = socket.gethostname()
            # Get all addresses associated with the hostname
            addr_info_list = socket.getaddrinfo(hostname, None)
            # Filter for IPv4 addresses not starting with 127 (loopback)
            for addr_info in addr_info_list:
                 family, _, _, _, sockaddr = addr_info
                 if family == socket.AF_INET: # IPv4
                     ip = sockaddr[0]
                     if not ip.startswith("127."): # Exclude loopback
                         return ip
            # If no non-loopback found via hostname, return the first one (likely 127.0.0.1)
            return socket.gethostbyname(hostname)
        except Exception as e2:
            print(f"Error getting local IP using hostname: {e2}")
            return "127.0.0.1" # Ultimate fallback

