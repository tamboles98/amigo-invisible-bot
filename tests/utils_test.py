import pytest
from faker import Faker
import random

import am_bot.utils as utils

@pytest.fixture
def get_guy() -> tuple[str, str]:
    faker = Faker()
    guy = faker.name()
    email = faker.free_email()
    return guy, email

@pytest.fixture
def participants() -> dict[str, str]:
    length = random.randint(13, 17)
    faker = Faker()
    return {faker.name(): faker.free_email() for _ in range(length)}

@pytest.fixture(name= "disallowed_pairs")
def disallowed_pairs_foo(participants: dict[str, str], length: int = 5
                         ) -> list[tuple[str, str]]:
    forbidden_givers = random.sample(participants.keys(), length)
    forbidden_receivers = random.sample(participants.keys(), length)
    return list(zip(forbidden_givers, forbidden_receivers))

@pytest.fixture
def impossible_disallowed_pairs(participants: dict[str, str]
                                ) -> list[tuple[str, str]]:
    #It generates a set of pairs where the first participant cannot gift
    # any other participant
    participants_names = list(participants.keys())
    return [(participants_names[0], other) for other in participants_names[1:]]
    

def sorteo_test(participants: dict[str, str],
                disallowed_pairs: list[tuple[str, str]]):
    participants_names = list(participants.keys())
    res = utils.sorteo(participants_names, disallowed_pairs)
    part_set = set(participants_names)
    givers_set = set(res.keys())
    receivers_set = set(res.values())
    # Check that all the participants are gifting someone
    assert part_set == givers_set
    # Check that all the participants are receiving gifts
    assert part_set == receivers_set
    # Check that no one is gifting itself
    assert not any(key == value for key, value in res.items())
    # Check that no one is gifted twice
    assert len(res.values()) == len(receivers_set)

def sorteo__empty_participants_errors_test(participants: dict[str, str]):
    #Second test, check that the appropiate errors are raised when there
    # are not enough participants for the lottery
    participants_names = list(participants.keys())
    with pytest.raises(ValueError):
        utils.sorteo([])
    with pytest.raises(ValueError):
        utils.sorteo(participants_names[0:1])
        
    #Third test, assert that an assertion is raised when there are duplicated names
    with pytest.raises(AssertionError):
        utils.sorteo([participants_names[0], participants_names[0],
                      participants_names[1]])

def sorteo__disallowed_pairs_test(participants: dict[str, str],
                disallowed_pairs: list[tuple[str, str]],
                impossible_disallowed_pairs: list[tuple[str, str]]):
    #Fourth test, assert that disallowed pairs don't appear after the lottery
    # try a bunch of times and check that no disallowed pairs appear
    participants_names = list(participants.keys())
    for _ in range(200):
        res = utils.sorteo(participants_names, disallowed_pairs)
        res_set = set((key, value) for key, value in res.items())
        assert not(set(disallowed_pairs).intersection(res_set))
        
    #Fifth test, assert that ValueError is raised if its impossible to generate
    # a valid lottery result
    with pytest.raises(ValueError):
        utils.sorteo(participants_names, impossible_disallowed_pairs)