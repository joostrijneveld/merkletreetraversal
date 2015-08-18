#! /usr/bin/env python

import copy
from classictraversal import (recursive_hash, compute_root, refresh_auth_nodes,
                              Treehash, keygen_and_setup, H, AUTH, TREEHASH)


# monkey patch a bound function that enables easily using STACK_h.low
Treehash.low = lambda self: min(node.h for node in self.stack)


def traverse(s):
    """Returns the auth nodes by updating the most needed stacks first."""
    authpath = copy.copy([x for x in AUTH])
    refresh_auth_nodes(s)

    # build stacks
    for _ in range(2*H - 1):
        l_min = float('inf')
        focus = None
        for h in range(H):
            if TREEHASH[h].completed:
                low = float('inf')
            elif len(TREEHASH[h].stack) == 0:
                low = h
            else:
                low = TREEHASH[h].low()
            if low < l_min:
                focus = h
                l_min = low
        if focus is not None:
            TREEHASH[focus].update()

    return authpath


if __name__ == "__main__":
    correct_root = recursive_hash(H)
    keygen_and_setup()
    for s in range(2 ** H):
        root = compute_root(s, traverse(s))
        print('iteration {}: {}'.format(s, root == correct_root))
