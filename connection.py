import subprocess
import account
import bridge
from time import sleep
from urllib.request import urlopen
import json
from sys import argv
# import tor


def reconnect(bridge_type):
    if bridge.ok():
        print("bridge to", bridge.ok(info=True)['ip'], "will be killed")
        listening = bridge.ok(info=True)['listening']
        for p in listening:
            subprocess.run(['kill', '-9', p[1]])
        subprocess.run(['mullvad', 'bridge', 'set', 'state', 'off'], stdout=subprocess.PIPE)
    bridge.activate(bridge_type)
    subprocess.run(['mullvad', 'reconnect'], stdout=subprocess.PIPE)


# python connection.py <mullvad acc number> <bridge type: ssh or shadow>
shell_args = argv  # TODO: or to be passed by a file consisting acc, bridge_type, network_quality_criteria, ...
mullvad_account = shell_args[1]
bridge_to_be = shell_args[2]

while True:
    vpn_status = subprocess.run(['mullvad', 'status'], stdout=subprocess.PIPE)
    vpn_connection = vpn_status.stdout.decode('utf-8').split(" ")
    if vpn_connection[0] == "Connected":  # reporting connection
        print("######### Mullvad states Connected #########")
        print("You are supposed to be connected to", vpn_connection[-3])
        try:
            connection_state = json.loads(urlopen('https://am.i.mullvad.net/json').read().decode())
        except:  # TODO: write it more detailed
            print("BUT connection to mullvad API failed")
            reconnect(bridge_to_be)
            continue
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
            print("BUT pinging is failed")
            reconnect(bridge_to_be)
            continue
        print('PING to mullvad.net takes:', ping_time_mullvad)
        print('PING to vpn server takes:', ping_time_vpn)
        print('PING to proxy server takes:', ping_time_proxy)
        # reconnect for 1.leaked connection 2.blacklisted IP
        # 3.high ping
        # TODO: need far better criteria
        if connection_state["mullvad_exit_ip"] is False \
                or connection_state["blacklisted"]["blacklisted"] is True \
                or (int(ping_time_mullvad.split("=")[1]) + int(ping_time_vpn.split("=")[1])
                    + int(ping_time_proxy.split("=")[1])) > 3000:
            print("BUT bad connection is established")
            reconnect(bridge_to_be)
            continue
        sleep(30)
    elif vpn_connection[0].startswith("Disconnecting"):  # it happens when the proxy bridge is failing
        print("------ Mullvad states Disconnecting -------")
        print("bridge is failing and reconnect to mullvad")
        reconnect(bridge_to_be)
    elif vpn_connection[0] == "Disconnected\n":
        print("******* Mullvad is disconnected ***********")
        with account.logged(mullvad_account) as a:  # TODO: the problem with logging-in persists then can be deleted
            if a:  # connect
                print("Mullvad acc is logged in")
                if not bridge.ok():
                    print("Trying to run the bridge")
                    bridge.activate(bridge_to_be)
                subprocess.run(['mullvad', 'connect'])
                vpn_status = subprocess.run(['mullvad', 'status'], stdout=subprocess.PIPE)
                vpn_connection = vpn_status.stdout.decode('utf-8').split(" ")
            elif not a:  # login
                print("trying to log in")
                if not bridge.ok():
                    bridge.activate(bridge_to_be)
                account.logout()
                account.login(mullvad_account)
    elif vpn_connection[0].startswith("Connecting"):
        print("+++++++++ Mullvad claim is connecting +++++++++++")
        if bridge.ok():
            continue  # have no idea why to stick here
        else:
            bridge.activate(bridge_to_be)
