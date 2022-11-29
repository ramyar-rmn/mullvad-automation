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
    while vpn_connection[0] == "Connected":  # reporting connection
        bridge.ok()
        print("You are supposed to be connected to", vpn_connection[-3])
        try:
            connection_state = json.loads(urlopen('https://am.i.mullvad.net/json').read().decode())
        except:  # TODO: write it more detailed
            print("BUT connection to mullvad API failed")
            subprocess.run(['mullvad', 'disconnect'])
            break
        print('https://mullvad.net shows your connection to mullvad is:', connection_state["mullvad_exit_ip"])
        print('That is using protocol:', connection_state["mullvad_server_type"])
        print('from address:', connection_state["ip"])
        print('located in:', connection_state["country"])
        print('and blacklisted status is:', connection_state["blacklisted"]["blacklisted"])
        ping_time_mullvad = subprocess.run(['ping', '-c', '1', 'mullvad.net'], stdout=subprocess.PIPE)
        ping_time_vpn = subprocess.run(['ping', '-c', '1', connection_state["ip"]], stdout=subprocess.PIPE)
        ping_time_proxy = subprocess.run(['ping', '-c', '1', bridge.ok(info=True)['ip']], stdout=subprocess.PIPE)
        try:
            ping_time_mullvad = ping_time_mullvad.stdout.decode('utf-8').split('\n')[1].split(' ')[-2]
            ping_time_vpn = ping_time_vpn.stdout.decode('utf-8').split('\n')[1].split(' ')[-2]
            ping_time_proxy = ping_time_proxy.stdout.decode('utf-8').split('\n')[1].split(' ')[-2]
        except IndexError:
            break
        print('PING to mullvad.net takes:', ping_time_mullvad)
        print('PING to vpn server takes:', ping_time_vpn)
        print('PING to proxy server takes:', ping_time_proxy)
        # reconnect for 1.leaked connection 2.blacklisted IP
        # 3.high ping to mullvad 4.high ping to vpn server 5.high ping to proxy server
        if connection_state["mullvad_exit_ip"] is False \
                or connection_state["blacklisted"]["blacklisted"] is True \
                or int(ping_time_mullvad.split("=")[1]) > 1000 \
                or int(ping_time_vpn.split('=')[1]) > 1000 \
                or int(ping_time_proxy.split('=')[1]) > 1000:
            subprocess.run(['mullvad', 'disconnect'])
            break
        sleep(30)
        vpn_status = subprocess.run(['mullvad', 'status'], stdout=subprocess.PIPE)
        vpn_connection = vpn_status.stdout.decode('utf-8').split(" ")
    while account.logged(mullvad_account) and vpn_connection[0] == "Disconnected\n":  # connect
        print("Mullvad is disconnected")
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
        else:
            print("Trying to run the bridge")
            bridge.activate(bridge_to_be)
    while vpn_connection[0].startswith("Disconnecting"):  # it happens when the proxy bridge is failing
        print("disconnecting from mullvad and checking the bridge")
        subprocess.run(['mullvad', 'disconnect'])
        vpn_status = subprocess.run(['mullvad', 'status'], stdout=subprocess.PIPE)
        vpn_connection = vpn_status.stdout.decode('utf-8').split(" ")
    while not account.logged(mullvad_account):  # login
        print("trying to log in")
        if bridge.ok():
            account.logout()
            account.login(mullvad_account)
        else:
            bridge.activate(bridge_to_be)
