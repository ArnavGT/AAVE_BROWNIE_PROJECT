from brownie import config, interface, network
from scripts.helpful_scripts import get_account, FORKED_LOCAL_ENVIRONMENTS, LOCAL_BLOCKCHAIN_NETWORKS


def main():
    get_weth()


def get_weth():
    '''
    Mints WETH by depositing ETH.
    '''
    # ABI, Address
    account = get_account()
    weth = interface.IWeth(
        config['networks'][network.show_active()]['weth_token'])
    tx = weth.deposit({'from': account, 'value': 0.1 * 10**18})
    print('Recieved ETH')
    tx.wait(1)
    return tx
