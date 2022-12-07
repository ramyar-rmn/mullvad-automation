import subprocess


def login(account_number):
    logging = subprocess.run(['mullvad', 'account', 'login', account_number], stdout=subprocess.PIPE)
    if logging.stdout.decode('utf-8').split(' ')[2].split('"')[1] != account_number:
        login(account_number)
    else:
        return True


def logged(account_number):
    account_status = subprocess.run(['mullvad', 'account', 'get'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if account_number == account_status.stdout.decode('utf-8').split('\n')[0].split(' ')[-1]:
        return True
    else:
        return False


def logout():
    subprocess.run(['mullvad', 'account', 'logout'])
