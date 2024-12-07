import random
import typing as ty

# for encoding/decoding messages in base64
from collections import deque


def generate_lottery(
    participants: list[str], disallowed_pairs: ty.Optional[list[tuple[str, str]]] = None
) -> dict[str, str]:
    """
    Generates a secret Santa lottery assignment.

    Each participant is assigned another participant to give a gift to, ensuring no
    participant is assigned to themselves and no disallowed pairs are assigned.

    Args:
        participants (list[str]): A list of participant names.
        disallowed_pairs (Optional[list[tuple[str, str]]], optional): An optional list
            of tuples representing pairs of participants that should not be assigned
            to each other. Defaults to None.

    Returns:
        dict[str, str]: A dictionary where keys are givers and values are receivers.

    Raises:
        ValueError: If there are less than 2 participants or if no valid lottery
            could be found after 200 attempts.
        AssertionError: If there are duplicate participants in the list.
    """
    if disallowed_pairs is None:
        disallowed_pairs = []
    assert len(set(participants)) == len(participants), 'Duplicate participants'
    if len(participants) < 2:
        raise ValueError('Cannot create assignments with less than 2 participants!')
    idxs = [i for i in range(len(participants))]
    # Try to generate a valid lottery, strop trying after 200 attempts. If the
    # limit is breached we assume that a valid lottery is not possible
    #! This approach is an approximation, if the number of disallowed pairs is
    # high its possible that this method will fail even if the lottery is
    # theoretically possible
    for _ in range(200):
        invalid = False
        random.shuffle(idxs)
        givers = idxs
        receivers = deque(givers)
        receivers.rotate(1)
        # Check that the lottery is valid
        res = {participants[g]: participants[r] for g, r in zip(givers, receivers)}
        for giver, receiver in disallowed_pairs:
            if res[giver] == receiver:
                invalid = True
                break
        if invalid:
            continue
        else:
            return res
    raise ValueError('No valid lottery could be found')
