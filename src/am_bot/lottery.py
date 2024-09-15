import random
import typing as ty

# for encoding/decoding messages in base64
from collections import deque


def generate_lottery(
    participants: list[str], disallowed_pairs: ty.Optional[list[tuple[str, str]]] = None
) -> dict[str, str]:
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
