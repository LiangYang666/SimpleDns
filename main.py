import socket
import logging
from logging.handlers import RotatingFileHandler
import sys


# 绑定的本机地址
bind_server = '192.168.1.2'

# 需要自定义的dns列表
domain_name_map = {
    "exapple.com": "192.168.1.3"
    }

# 默认dns服务器，非指定解析映射表内的直接转发给默认dns服务器
default_dns_server = "192.168.1.1"

# Create a rotating file handler with a maximum size of 10MB
handler = RotatingFileHandler('dns.log', maxBytes=10*1024*1024, backupCount=10)

# Create a stream handler to display logs in the terminal
stream_handler = logging.StreamHandler(sys.stdout)


# Define the log format with date, time, log level, and message
log_format = '%(asctime)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)

# Set the formatter for both the file and stream handlers
handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Configure the logger with the rotating file handler
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
# TODO 使用时注释该行
logger.addHandler(stream_handler)


def dns_server():
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Bind the socket to a specific IP address and port
    server_address = (bind_server, 53)  # DNS server listens on port 53
    server_socket.bind(server_address)

    server_socket.settimeout(60)

    logger.info('DNS server is running...')
    while True:
        try:
            # Receive DNS query packet and client address
            dns_query, client_address = server_socket.recvfrom(1024)

        except socket.timeout:
            logger.warning('DNS server timed out')
            continue

        # Extract the domain name from the DNS query
        domain_name = extract_domain_name(dns_query)
        
        logger.info(f'Received DNS query for {domain_name} from {client_address[0]}')
        
        # Check if the requested domain is home.com
        if domain_name in domain_name_map:
            dns_response = build_dns_response(dns_query, domain_name, domain_name_map[domain_name])
            server_socket.sendto(dns_response, client_address)
            logger.info(f'Sending DNS response for {domain_name} to {client_address[0]}')
            
        else:
            # If requested domain is not home.com, forward the DNS query to the gateway DNS server
            gateway_dns_server_address = (default_dns_server, 53)  # Replace with actual gateway DNS server IP
            forward_dns_query(dns_query, gateway_dns_server_address, client_address, server_socket)
            logger.info(f'Sending DNS response for {domain_name} to {client_address[0]}')


def extract_domain_name(dns_query):
    domain_name = ''
    domain_length = dns_query[12]  # Length of the domain name
    
    pointer = 12  # Start of the domain name
    
    while domain_length != 0:
        domain_name += dns_query[pointer+1:pointer+1+domain_length].decode("utf-8") + '.'
        pointer += domain_length + 1
        domain_length = dns_query[pointer]
    
    return domain_name[:-1]  # Remove the trailing '.'


def build_dns_response(dns_query, domain_name, ip_address):
    dns_response = dns_query[:2] + b'\x81\x80'  # Transaction ID and Flags
    dns_response += dns_query[4:6] + dns_query[4:6] + b'\x00\x00\x00\x00'  # Questions and Answers Counts
    dns_response += dns_query[12:]  # Original DNS query
    dns_response += b'\xc0\x0c'  # Pointer to domain name
    dns_response += b'\x00\x01'  # Type (A) - IPv4 address
    dns_response += b'\x00\x01'  # Class (IN)
    dns_response += b'\x00\x00\x00\x3c'  # TTL (60 seconds)
    dns_response += b'\x00\x04'  # Data length (4 bytes)
    
    # Convert IP address to 4 bytes in network byte order
    ip_parts = ip_address.split('.')
    ip_bytes = bytes(map(int, ip_parts))
    
    dns_response += ip_bytes  # IP address
    
    return dns_response


def forward_dns_query(dns_query, gateway_dns_server_address, client_address, server_socket):
    # Create a socket to communicate with gateway DNS server
    gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Forward the DNS query to the gateway DNS server
    gateway_socket.sendto(dns_query, gateway_dns_server_address)
    
    # Wait for the DNS response from the gateway DNS server
    dns_response, _ = gateway_socket.recvfrom(1024)
    
    # Send the DNS response back to the client
    server_socket.sendto(dns_response, client_address)
    
    gateway_socket.close()


dns_server()
