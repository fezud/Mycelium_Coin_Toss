from json import load
from dotenv import load_dotenv
from brownie import Wei, accounts, config, network, CoinToss, Pool
from .helpful_scripts import get_account, get_contract, fund_with_link, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from time import sleep

load_dotenv()


def deploy_coin_toss():
    account = get_account()
    coin_toss = CoinToss.deploy(
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account})
    return coin_toss
    print("Deployed coin_toss\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')


def deploy_pool():
    account = get_account()
    coin_toss = CoinToss[-1]
    pool = Pool.deploy(coin_toss.address, {"from": account})
    print("Deployed pool\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')
    print(f'pool balance: {pool.balance()}\n')
    return pool


def fund_pool(pool_balance=None):
    account = get_account()
    coin_toss = CoinToss[-1]
    pool = Pool[-1]

    default_pool_balance = Wei("10 ether") if network.show_active(
    ) in LOCAL_BLOCKCHAIN_ENVIRONMENTS else Wei('0.01 ether')

    pool_balance = pool_balance if pool_balance else default_pool_balance

    tx = account.transfer(pool.address, pool_balance)
    tx.wait(1)
    print("funded pool\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')
    print(f'pool balance: {pool.balance()}\n')


def fund_coin_toss_with_link(amount=None):
    account = get_account()
    coin_toss = CoinToss[-1]
    tx = fund_with_link(coin_toss.address, amount=Wei("1 ether"))
    tx.wait(1)
    print("funded coin_toss with link\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')


def set_pool():
    account = get_account()
    coin_toss = CoinToss[-1]
    pool = Pool[-1]
    tx = coin_toss.setPool(pool.address, {"from": account})
    tx.wait(1)
    print("pool is set for coin_toss\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')
    print(f'pool balance: {pool.balance()}\n')


def flip(index=0, guess_value=0, bid=None):

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        account = get_account(index=index)
    else:
        account = accounts.add(config["wallets"]["from_key"][index])

    coin_toss = CoinToss[-1]
    pool = Pool[-1]
    default_bid = Wei("0.1 ether") if network.show_active(
    ) in LOCAL_BLOCKCHAIN_ENVIRONMENTS else Wei('0.0001 ether')

    bid = bid if bid else default_bid

    tx = coin_toss.flip(
        guess_value, {"from": account, "value": bid})
    tx.wait(1)

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        print(f"network is {network.show_active()}\n")
        request_id = tx.events["RequestedRandomness"]["requestId"]
        STATIC_RNG = 789
        account_to_mock_chainlink_node = get_account()
        vrf_coordinator = get_contract("vrf_coordinator")
        vrf_coordinator.callBackWithRandomness(
            request_id, STATIC_RNG, coin_toss.address, {"from": account_to_mock_chainlink_node})

    print(f"Result {coin_toss.result()} // guess \
     {guess_value}")

    print("coin was flipped\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')
    print(f'pool balance: {pool.balance()}\n')


def main():
    deploy_coin_toss()
    deploy_pool()

    fund_pool()
    fund_coin_toss_with_link()

    set_pool()

    # flip(index=1, guess_value=0)
