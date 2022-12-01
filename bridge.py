import subprocess
from random import randint

servers = ['89.44.10.210',
           '37.120.218.170',
           '37.120.205.226',
           '198.54.132.178',
           '217.138.199.106',
           '193.138.7.132',
           '146.70.117.130',
           '209.58.185.59',
           '91.193.7.98',
           '185.65.134.66',
           '91.90.44.10',
           '194.127.199.245',
           '5.253.206.194',
           '185.120.144.114',
           '94.198.43.114',
           '45.152.183.34',
           '185.213.154.117',
           '193.138.218.71',
           '45.83.220.117',
           '185.65.135.117',
           '193.32.127.117',
           '91.193.4.210',
           '141.98.252.66',
           '217.138.254.130',
           '194.37.96.162',
           '66.115.180.241',
           '174.127.113.18',
           '194.110.112.50',
           '89.45.90.249',
           '89.38.227.242',
           '86.106.143.249',
           '198.54.133.178',
           '198.54.130.178',
           '69.4.234.146',
           '198.54.134.178',
           '198.54.131.178',
           ]


def set_tor_proxy():
    # proxy_address = '127.0.0.1'
    # proxy_port = '9150'  # or 9050
    # check TOR availability or start it
    pass  # TODO: fill


def set_ssh_proxy():
    proxy_address = servers[randint(0, len(servers)-1)]
    proxy_port = '1234'
    ssh_password = 'mullvad'
    ssh_port = '22'
    ssh_key = subprocess.run(['ssh-keyscan', proxy_address], stdout=subprocess.PIPE)
    ssh_key = ssh_key.stdout.decode('utf-8').split('\n')
    known_hosts = subprocess.run('cat ~/.ssh/known_hosts', stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
    if proxy_address not in known_hosts:
        for line in ssh_key:
            if line and not line.startswith('#'):
                subprocess.run('echo' + " '" + line + "' " + '>> ~/.ssh/known_hosts', shell=True)
    subprocess.run(['mullvad-exclude', 'sshpass', '-p', ssh_password, 'ssh', '-f', '-N', '-D', proxy_port,
                    'mullvad@'+proxy_address, proxy_port])
    subprocess.run(['mullvad', 'bridge', 'set', 'custom', 'local', proxy_port, proxy_address, ssh_port])
    subprocess.run(['mullvad', 'relay', 'set', 'tunnel-protocol', 'openvpn'])
    subprocess.run(['mullvad', 'bridge', 'set', 'state', 'on'])


def set_remote_socks():  # not to be used regularly and to be removed later
    proxy_address = 'be filled with LAN IP of that device'
    proxy_port = '1080'
    proxy_username = 'a'
    proxy_password = 'a'
    subprocess.run(['mullvad', 'bridge', 'set', 'custom', 'remote',
                    proxy_address, proxy_port, proxy_username, proxy_password])
    subprocess.run(['mullvad', 'relay', 'set', 'tunnel-protocol', 'openvpn'])
    subprocess.run(['mullvad', 'bridge', 'set', 'state', 'on'])


def set_shadow_socks():
    proxy_address = servers[randint(0, len(servers)-1)]
    proxy_port = '443'
    ss_port = '1080'
    # TODO: wrote it based on mullvad tutorial but it's not assured
    subprocess.run(['mullvad-exclude', 'ss-local', '-s', proxy_address, '-p', proxy_port, '-l', ss_port, '-k',
                    'mullvad', '-m', 'chacha20-ietf-poly1305', '-b', '127.0.0.1', '--fast-open', '--no-delay',
                    '--plugin', 'ss-v2ray-plugin', '--plugin-opts', '''"mode=quic;host=$HOST"'''])
    subprocess.run(['mullvad', 'bridge', 'set', 'custom', 'local', ss_port, proxy_address, proxy_port])
    subprocess.run(['mullvad', 'relay', 'set', 'tunnel-protocol', 'openvpn'])
    subprocess.run(['mullvad', 'bridge', 'set', 'state', 'on'])


def ok(info=False):  # TODO: write for proxy: remote as well if needed
    bridge_status = subprocess.run(['mullvad', 'bridge', 'get'], stdout=subprocess.PIPE)
    bridge_state = str(bridge_status.stdout.split(b'\n')[0].split(b" ")[-1]).split("'")[1]
    if bridge_state == 'off':
        print("Bridge is set to OFF")
        return False
    else:
        bridge_proxy_type = str(bridge_status.stdout.split(b'\n')[1].split(b" ")[-1]).split("'")[1]
        bridge_local_port = str(bridge_status.stdout.split(b'\n')[2].split(b" ")[-1]).split("'")[1]
        bridge_proxy_address = str(bridge_status.stdout.split(b'\n')[3].split(b" ")[-1]).split("'")[1].split(":")[0]
        bridge_proxy_port = str(bridge_status.stdout.split(b'\n')[3].split(b" ")[-1]).split("'")[1].split(":")[1]
        if info is False:
            print("A", bridge_proxy_type, "Bridge is set to connect to", bridge_proxy_address+":"+bridge_proxy_port,
                  "via", bridge_local_port)
        listening_ports = subprocess.run(['lsof', '-i', '-P', '-n'], stdout=subprocess.PIPE)
        proxy_open_ports = list()
        for line in listening_ports.stdout.decode('utf-8').split('\n'):
            if ('127.0.0.1'+':'+bridge_local_port) in line:
                proxy_open_ports.append(line.split(" "))
        for i in range(0, len(proxy_open_ports)):
            proxy_open_ports[i] = [d for d in proxy_open_ports[i] if d != '']
        proxy_open_ports = [line for line in proxy_open_ports if line[-1] == '(LISTEN)']
        # ['COMMAND', 'PID', 'USER', 'FD', 'TYPE', 'DEVICE', 'SIZE/OFF', 'NODE', 'NAME']
        if proxy_open_ports:
            if info is True:
                return {'ip': bridge_proxy_address, 'port': bridge_proxy_port, 'listening': proxy_open_ports}
            print("and it is listening")
            return True
        else:
            print("but it is not listening")
            return False


def activate(bridge_type):  # TODO: set for TOR and remote
    if ok():
        listening = ok(info=True)['listening']
        for p in listening:
            subprocess.run(['kill', '-9', p[1]])
    if bridge_type == 'ssh':
        set_ssh_proxy()
    elif bridge_type == 'shadow':
        set_shadow_socks()
