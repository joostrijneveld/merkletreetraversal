#! /usr/bin/env python

import struct
import copy
from hashlib import sha256
from collections import namedtuple

H = 8
AUTH = [None] * H
TREEHASH = [None] * H

Node = namedtuple('Node', ['h', 'v'])


def leafcalc(j):
    return sha256(struct.pack("I", j)).digest()


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


class Treehash(object):

    def __init__(self, startidx=0):
        self.next_idx = startidx
        self.stack = []
        self.node = None

    def update(self):
        if self.node and self.stack and self.stack[-1].h == self.node.h:
            node2 = self.stack.pop()
            self.node = Node(h=self.node.h+1, v=g(node2.v + self.node.v))
            return
        elif self.node:
            self.stack.append(self.node)
            self.next_idx += 1
        if self.next_idx >= 2 ** H:
            return  # this is a leftover update cycle at 2^h
        self.node = Node(h=0, v=leafcalc(self.next_idx))


def keygen_and_setup():
    """Sets up TREEHASH and AUTH for the start of classic_merkle_traversal."""
    for h in range(H):
        TREEHASH[h] = Treehash()
    stack = []
    for j in range(2 ** H):
        node1 = Node(h=0, v=leafcalc(j))
        if j == 0:
            TREEHASH[0].stack = [node1]
        if j == 1:
            AUTH[0] = node1
        while stack and stack[-1].h == node1.h:
            if not AUTH[node1.h]:
                AUTH[node1.h] = node1
            node2 = stack.pop()
            node1 = Node(h=node1.h+1, v=g(node2.v + node1.v))
            if node1.h < H and not TREEHASH[node1.h].stack:
                TREEHASH[node1.h].stack.append(node1)
        stack.append(node1)
    return stack.pop()


def classic_merkle_traversal(s):
    """Performs one traversal and two updates, returns the auth nodes."""
    authpath = copy.copy([x for x in AUTH])

    # refresh
    for h in [h for h in range(H) if ((s + 1) % (2 ** h)) == 0]:
        if TREEHASH[h].stack:  # prevent going past 2^H'th leaf node
            AUTH[h] = TREEHASH[h].stack[0]
            startidx = (s + 1 + 2 ** h) ^ (2 ** h)
            TREEHASH[h].__init__(startidx)

    # and build stacks
    for h in range(H):
        TREEHASH[h].update()
        TREEHASH[h].update()

    return authpath


def compute_root(idx, authpath):
    """Computes the root node of the tree from leaf idx using the auth path."""
    v = leafcalc(idx)
    for h in range(H):
        if idx & 1:
            v = g(authpath[h].v + v)
        else:
            v = g(v + authpath[h].v)
        idx >>= 1
    return v


if __name__ == "__main__":
    correct_root = recursive_hash(H)
    print('Treehash function: {}'.format(treehash(H).v == correct_root))
    th = Treehash()
    for _ in range(2 ** (H + 1)):
        th.update()
    print('Treehash class: {}'.format(th.stack[0].v == correct_root))
    keygen_and_setup()
    for s in range(2 ** H):
        root = compute_root(s, classic_merkle_traversal(s))
        print('iteration {}: {}'.format(s, root == correct_root))
