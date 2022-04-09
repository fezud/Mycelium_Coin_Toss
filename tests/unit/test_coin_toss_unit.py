from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
)
from brownie import network, exceptions, Wei
from scripts.deploy import deploy_coin_toss, set_pool, deploy_pool, fund_pool, fund_coin_toss_with_link, flip
import pytest


def test_cant_flip_unless_pool_is_set():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    deploy_coin_toss()
    deploy_pool()

    fund_coin_toss_with_link()

    fund_pool()

    with pytest.raises(exceptions.VirtualMachineError):
        flip()


def test_can_flip_if_pool_is_set():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    deploy_coin_toss()
    deploy_pool()

    set_pool()

    fund_coin_toss_with_link()

    fund_pool()

    flip()


def test_cant_flip_with_a_big_bid():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    deploy_coin_toss()
    pool = deploy_pool()

    set_pool()

    fund_coin_toss_with_link()

    initial_pool_balance = Wei('9999999999 wei')
    fund_pool(pool_balance=initial_pool_balance)

    pool_balance = pool.balance()
    bid = int(pool.balance() / 50) + 1

    print(pool_balance, bid)

    with pytest.raises(exceptions.VirtualMachineError):
        flip(bid=bid)


def test_can_flip():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    deploy_coin_toss()
    pool = deploy_pool()

    set_pool()

    fund_coin_toss_with_link()

    initial_pool_balance = Wei('9999999999 wei')
    fund_pool(pool_balance=initial_pool_balance)

    pool_balance = pool.balance()
    bid = int(pool.balance() / 50) - 1

    print(pool_balance, bid)
    flip(bid=bid)


def test_cant_set_pool_by_an_unauthorized_account():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    coin_toss = deploy_coin_toss()
    pool = deploy_pool()

    unauthorized_account = get_account(index=1)

    with pytest.raises(exceptions.VirtualMachineError):
        coin_toss.setPool(pool.address, {"from": unauthorized_account})


def test_multiple_users_cant_flip_coin():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    coin_toss = deploy_coin_toss()
    deploy_pool()

    set_pool()

    fund_coin_toss_with_link()

    fund_pool(pool_balance=Wei("5 ether"))

    first_user = get_account()
    second_user = get_account(index=1)

    coin_toss.flip(0, {"from": first_user, "value": Wei("0.1 ether")})

    with pytest.raises(exceptions.VirtualMachineError):
        coin_toss.flip(0, {"from": second_user, "value": Wei("0.1 ether")})


def test_same_user_cant_flip_coin_twice_before_the_result():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    coin_toss = deploy_coin_toss()
    deploy_pool()

    set_pool()

    fund_coin_toss_with_link()

    fund_pool(pool_balance=Wei("5 ether"))

    first_user = get_account()

    coin_toss.flip(0, {"from": first_user, "value": Wei("0.1 ether")})

    with pytest.raises(exceptions.VirtualMachineError):
        coin_toss.flip(0, {"from": first_user, "value": Wei("0.1 ether")})


def test_guess_value_format():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    coin_toss = deploy_coin_toss()
    deploy_pool()

    set_pool()

    fund_coin_toss_with_link()

    fund_pool(pool_balance=Wei("5 ether"))

    STATIC_GUESS_VALUE = 11

    with pytest.raises(exceptions.VirtualMachineError):
        coin_toss.flip(STATIC_GUESS_VALUE, {
            "from": get_account(), "value": Wei("0.1 ether")})


@pytest.mark.parametrize("guess_value, random_number", [(1, 789), (0, 660), (0, 789), (1, 660)])
def test_account_payments(guess_value, random_number):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    coin_toss = deploy_coin_toss()
    deploy_pool()

    set_pool()
    fund_coin_toss_with_link()
    fund_pool(pool_balance=Wei("5 ether"))

    account = get_account()

    bid = Wei("0.1 ether")

    starting_balance_of_account = account.balance()

    tx = coin_toss.flip(guess_value, {"from": account, "value": bid})
    tx.wait(1)

    balance_of_account_after_bid = account.balance()
    assert balance_of_account_after_bid == starting_balance_of_account - bid

    request_id = tx.events["RequestedRandomness"]["requestId"]

    vrf_coordinator = get_contract("vrf_coordinator")
    tx = vrf_coordinator.callBackWithRandomness(
        request_id, random_number, coin_toss.address, {"from": account})
    tx.wait(1)

    if (random_number % 2 == guess_value):
        assert account.balance() == bid*2 + balance_of_account_after_bid
    else:
        assert account.balance() == balance_of_account_after_bid


@pytest.mark.parametrize("guess_value, random_number", [(1, 789), (0, 660), (0, 789), (1, 660)])
def test_pool_balance(guess_value, random_number):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    coin_toss = deploy_coin_toss()
    pool = deploy_pool()

    set_pool()
    fund_coin_toss_with_link()
    fund_pool(pool_balance=Wei("5 ether"))

    account = get_account()

    bid = Wei("0.1 ether")

    starting_balance_of_pool = pool.balance()

    tx = coin_toss.flip(guess_value, {"from": account, "value": bid})
    tx.wait(1)

    pool_balance_after_bid = pool.balance()
    assert pool_balance_after_bid == starting_balance_of_pool + bid

    request_id = tx.events["RequestedRandomness"]["requestId"]

    vrf_coordinator = get_contract("vrf_coordinator")
    tx = vrf_coordinator.callBackWithRandomness(
        request_id, random_number, coin_toss.address, {"from": account})
    tx.wait(1)

    if (random_number % 2 == guess_value):
        assert pool.balance() == pool_balance_after_bid - bid*2
    else:
        assert pool.balance() == pool_balance_after_bid


@pytest.mark.parametrize("guess_value, random_number", [(1, 789), (0, 660), (0, 789), (1, 660)])
def test_coin_toss_balance(guess_value, random_number):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    coin_toss = deploy_coin_toss()
    deploy_pool()

    set_pool()
    fund_coin_toss_with_link()
    fund_pool(pool_balance=Wei("5 ether"))

    account = get_account()

    bid = Wei("0.1 ether")

    assert coin_toss.balance() == 0

    tx = coin_toss.flip(guess_value, {"from": account, "value": bid})
    tx.wait(1)
    assert coin_toss.balance() == 0

    request_id = tx.events["RequestedRandomness"]["requestId"]

    vrf_coordinator = get_contract("vrf_coordinator")
    tx = vrf_coordinator.callBackWithRandomness(
        request_id, random_number, coin_toss.address, {"from": account})
    tx.wait(1)

    assert coin_toss.balance() == 0
