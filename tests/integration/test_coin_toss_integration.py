from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
)
from brownie import network, exceptions, Wei, accounts, config
from scripts.deploy import deploy_coin_toss, set_pool, deploy_pool, fund_pool, fund_coin_toss_with_link, flip
import pytest
from time import sleep


def test_coin_toss():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    coin_toss = deploy_coin_toss()
    pool = deploy_pool()

    guess_value = 1
    fund_coin_toss_with_link()
    fund_pool()

    set_pool()

    account = accounts.add(config["wallets"]["from_key"][1])
    starting_balance_of_account = account.balance()

    bid = Wei("0.01 ether")

    coin_toss.flip(guess_value, {"from": account})

    sleep(120)

    if coin_toss.result() == guess_value:
        assert account.balance() > starting_balance_of_account
    else:
        assert account.balance() < starting_balance_of_account
