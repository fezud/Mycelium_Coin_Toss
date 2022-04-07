from json import load
from dotenv import load_dotenv
from brownie import Wei, config, network, CoinToss, Pool
from .helpful_scripts import get_account, get_contract, fund_with_link
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
    print("Deployed coin_toss\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')


def deploy_pool():
    account = get_account()
    coin_toss = CoinToss[-1]
    pool = Pool.deploy(coin_toss.address, {"from": account})
    print("Deployed pool\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')
    print(f'pool balance: {pool.balance()}\n')


def fund_pool():
    account = get_account(index=1)
    coin_toss = CoinToss[-1]
    pool = Pool[-1]
    tx = account.transfer(pool.address, Wei('10 ether'))
    tx.wait(1)
    print("funded pool\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')
    print(f'pool balance: {pool.balance()}\n')


def fund_coin_toss_with_link():
    account = get_account(index=1)
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


def flip(index=2, guess_value=1):
    account = get_account(index=index)
    coin_toss = CoinToss[-1]
    pool = Pool[-1]
    tx = coin_toss.flip(
        guess_value, {"from": account, "value": Wei('0.1 ether')})
    tx.wait(1)

    # ONLY for purposes of development network deploying
    request_id = tx.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 789
    account_to_mock_chainlink_node = get_account()
    vrf_coordinator = get_contract("vrf_coordinator")
    vrf_coordinator.callBackWithRandomness(
        request_id, STATIC_RNG, coin_toss.address, {"from": account_to_mock_chainlink_node})
    # code below is universal

    print("coin was flipped\n")
    print(f'coin_toss balance: {coin_toss.balance()}\n')
    print(f'pool balance: {pool.balance()}\n')


def main():
    deploy_coin_toss()
    deploy_pool()

    fund_pool()
    fund_coin_toss_with_link()

    set_pool()

    flip()
    flip(index=2, guess_value=1)
    flip(index=3, guess_value=1)
    flip(index=4)
