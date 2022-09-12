from brownie import config, interface, network
from scripts.helpful_scripts import get_account, FORKED_LOCAL_ENVIRONMENTS, LOCAL_BLOCKCHAIN_NETWORKS, get_pf_address
from scripts.get_weth import get_weth
from web3 import Web3

amount = 0.1*10**18


def main():
    account = get_account()
    weth_Address = interface.IWeth(
        config['networks'][network.show_active()]['weth_token'])

    if network.show_active() not in LOCAL_BLOCKCHAIN_NETWORKS:
        get_weth()

    # ABI, Address
    # since we need to have the ABI and Address of the lending pool contract (main contract of aave)
    lending_pool = get_lending_pool()

    # We need to approve our sending of ERC20 tokens.
    # Can't use weth gateway since its only a smartcontract for wrapping ETH to WETH and not authorized for approving all types of token, only autorized for WETH.
    # Need a ERC20 contract to approve any Token.
    approve_erc20(amount, lending_pool.address, weth_Address, account)
    # tx_app = weth_Address.approve(
    #    lending_pool.address, amount, {'from': account})
    # tx_app.wait(1)

    print('Depositing...')
    tx = lending_pool.deposit(weth_Address, amount,
                              account.address, 0, {'from': account})
    tx.wait(1)
    print('Deposited!')

    total_debt, availableToBorrow = get_borrowable_data(lending_pool, account)

    print('Lets Borrow!')
    dai_eth_price_feed = get_pf_address('dai_eth')
    dai_eth_price = get_asset_price(dai_eth_price_feed)

    amount_dai_to_borrow = (1/dai_eth_price) * (availableToBorrow)
    #         borrowable_eth -> borrowable_dai, then, * availableToBorrow because there is a set amount we can borrow
    print(f'We are gonna borrow {amount_dai_to_borrow} DAI.')

    dai_address = config['networks'][network.show_active()]['dai_address']
    print(Web3.toWei(amount_dai_to_borrow, 'ether'))
    borrow_tx = lending_pool.borrow(
        dai_address, Web3.toWei(amount_dai_to_borrow, 'ether'), 1, 0, account.address, {'from': account})
    borrow_tx.wait(1)
    print('BORROWED! HELL YEAH.')
    get_borrowable_data(lending_pool, account)

    # now we are gonna repay everything back
    print('We are gonna repay everything back...')
    repay_all(amount, lending_pool, account, dai_address)
    get_borrowable_data(lending_pool, account)


def repay_all(amount, lending_pool, account, dai_Address):
    approve_erc20(amount, lending_pool, dai_Address,
                  account)
    # We have to approve the use of dai tokens since we just borrowed it and not approved it before
    # Like the weth token.

    repay_tx = lending_pool.repay(
        dai_Address, amount, 1, account.address, {'from': account})
    repay_tx.wait(1)
    print('REPAYED! HELL YEAH.')


def get_asset_price(priceFeed_address):
    priceFeed = interface.AggregatorV3Interface(priceFeed_address)
    latest_price = priceFeed.latestRoundData()[1]
    converted_price = Web3.fromWei(latest_price, 'ether')
    print(f'The DAI/ETH Price is {converted_price}')
    return float(converted_price)


def get_borrowable_data(lending_pool, account):
    data = lending_pool.getUserAccountData(account)
    print(f'Collateral ETH: {data[0]/10**18}, Debt: {data[1] / 10**18}, Borrowable Amount: {data[2] / 10**18}, Liquidation Threshold: {data[3]/100}%, Loan_to_value: {data[4]/100}%, Health Factor: {data[5]}')
    return data[1] / 10**18, data[2] / 10**18


def approve_erc20(amount, spender, erc20_address, account):
    '''
    Approves Tokens
    '''
    print('Approving tokens')
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {'from': account})
    tx.wait(1)
    print('Approved!')
    return tx


def get_lending_pool():
    # Lending pool has a changing address (different markets) so we have a different contract which can provide us the main lending pool address
    # Called LendingPoolAddressProvider
    LenPoolAddProv = interface.ILendingPoolAddressesProvider(
        config['networks'][network.show_active()]['LendingPoolAddressesProvider'])

    LendingPoolAddress = LenPoolAddProv.getLendingPool()
    LendingPool = interface.ILendingPool(LendingPoolAddress)
    return LendingPool
