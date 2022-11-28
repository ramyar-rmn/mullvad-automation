import subprocess
import account
import bridge
from time import sleep
from urllib.request import urlopen
import json
from sys import argv


# python connection.py <mullvad acc number> <bridge type: ssh or shadow>
shell_args = argv
mullvad_account = shell_args[1]
bridge_to_be = shell_args[2]

while True:
    vpn_status = subprocess.run(['mullvad', 'status'], stdout=subprocess.PIPE)
    vpn_connection = vpn_status.stdout.decode('utf-8').split(" ")
    while vpn_connection[0] == "Connected":
        bridge.ok()
        print("You are supposed to be connected to", vpn_connection[-3])
        connection_state = json.loads(urlopen('https://am.i.mullvad.net/json').read().decode())
        print('https://mullvad.net shows your connection to mullvad is:', connection_state["mullvad_exit_ip"])
        print('That is using protocol:', connection_state["mullvad_server_type"])
        print('from address:', connection_state["ip"])
        print('located in:', connection_state["country"])
        print('and blacklisted status is:', connection_state["blacklisted"]["blacklisted"])
        print('PING to mullvad.net takes:',
              subprocess.run(['ping', '-c', '1', 'mullvad.net'],
                             stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')[1].split(' ')[-2])
        print('PING to vpn server takes:',
              subprocess.run(['ping', '-c', '1', connection_state["ip"]],
                             stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')[1].split(' ')[-2])
        print('PING to proxy server takes:',
              subprocess.run(['ping', '-c', '1',
                              subprocess.run(['mullvad', 'bridge', 'get'], stdout=subprocess.PIPE).stdout.decode(
                                  'utf-8').split('\n')[3].split(" ")[-1].split(":")[0]],
                             stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')[1].split(' ')[-2])
        if str(connection_state["mullvad_exit_ip"]) == 'false' \
                or str(connection_state["blacklisted"]["blacklisted"]) == 'true':
            subprocess.run(['mullvad', 'disconnect'])
            break
        sleep(30)
        vpn_status = subprocess.run(['mullvad', 'status'], stdout=subprocess.PIPE)
        vpn_connection = vpn_status.stdout.decode('utf-8').split(" ")
    while account.logged(mullvad_account) and vpn_connection[0] == "Disconnected\n":  # connect
        if bridge.ok():
            subprocess.run(['mullvad', 'connect'])
            vpn_status = subprocess.run(['mullvad', 'status'], stdout=subprocess.PIPE)
            vpn_connection = vpn_status.stdout.decode('utf-8').split(" ")
            while vpn_connection[0] == "Connecting":
                vpn_status = subprocess.run(['mullvad', 'status'], stdout=subprocess.PIPE)
                vpn_connection = vpn_status.stdout.decode('utf-8').split(" ")
                continue
            if vpn_connection[0] == "Connected":
                break
        else:  # TODO: set for TOR and remote
            print("Trying to run the bridge")
            if bridge_to_be == 'ssh':
                bridge.set_ssh_proxy()
            elif bridge_to_be == 'shadow':
                bridge.set_shadow_socks()
    while vpn_connection[0].startswith("Disconnecting"):
        subprocess.run(['mullvad', 'disconnect'])
        vpn_status = subprocess.run(['mullvad', 'status'], stdout=subprocess.PIPE)
        vpn_connection = vpn_status.stdout.decode('utf-8').split(" ")
    while not account.logged(mullvad_account):  # login
        if bridge.ok():
            account.logout()
            account.login(mullvad_account)
        else:  # TODO: set for TOR and remote
            if bridge_to_be == 'ssh':
                bridge.set_ssh_proxy()
            elif bridge_to_be == 'shadow':
                bridge.set_shadow_socks()
