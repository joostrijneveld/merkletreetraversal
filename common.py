import struct
from hashlib import sha256
from collections import namedtuple
from functools import wraps

Node = namedtuple('Node', ['h', 'v'])

cost = 0


def countcost(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global cost
        cost += 1
        return fn(*args, **kwargs)
    return wrapper


@countcost
def leafcalc(j):
    return sha256(struct.pack("I", j)).digest()


@countcost
def g(v):
    return sha256(v).digest()


def recursive_hash(h, i=0):
    """Computes the root node of a hashtree naively."""
    if h == 0:
        return leafcalc(i)
    return g(recursive_hash(h - 1, i) + recursive_hash(h-1, i + (2 ** (h-1))))


def treehash(h):
    """Computes the root node using treehash."""
    stack = []
    for j in range(2 ** h):
        node1 = Node(h=0, v=leafcalc(j))
        while stack and stack[-1].h == node1.h:
            node2 = stack.pop()
            node1 = Node(h=node1.h+1, v=g(node2.v + node1.v))
        stack.append(node1)
    return stack.pop()


def compute_root(H, idx, authpath):
    """Computes the root node of the tree from leaf idx using the auth path."""
    v = leafcalc(idx)
    for authnode in authpath:
        if idx & 1:
            v = g(authnode.v + v)
        else:
            v = g(v + authnode.v)
        idx >>= 1
    return v
