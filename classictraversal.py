#! /usr/bin/env python

import copy
from common import Node, leafcalc, g, recursive_hash, compute_root, treehash

H = 8
AUTH = [None] * H
TREEHASH = [None] * H


class Treehash(object):

    def __init__(self, h, startidx=0, completed=False):
        self.next_idx = startidx
        self.stack = []
        self.completed = completed
        self.h = h

    def update(self):
        """Performs one unit of computation on the stack. This can imply either
        the introduction a new leaf node or the computation of a parent node"""
        if self.completed:
            return
        if len(self.stack) >= 2 and self.stack[-1].h == self.stack[-2].h:
            node_r = self.stack.pop()
            node_l = self.stack.pop()
            self.stack.append(Node(h=node_l.h + 1, v=g(node_l.v + node_r.v)))
        else:
            self.stack.append(Node(h=0, v=leafcalc(self.next_idx)))
            self.next_idx += 1
        if self.stack[-1].h == self.h:
            self.completed = True
        return


def keygen_and_setup():
    """Sets up TREEHASH and AUTH for the start of classic Merkle traversal."""
    for h in range(H):
        TREEHASH[h] = Treehash(h, completed=True)
    stack = []
    for j in range(2 ** H):
        node1 = Node(h=0, v=leafcalc(j))
        if j == 0:
            TREEHASH[0].stack = [node1]
        while stack and stack[-1].h == node1.h:
            if not AUTH[node1.h]:
                AUTH[node1.h] = node1
            node2 = stack.pop()
            node1 = Node(h=node1.h+1, v=g(node2.v + node1.v))
            if node1.h < H and not TREEHASH[node1.h].stack:
                TREEHASH[node1.h].stack.append(node1)
        stack.append(node1)
    return stack.pop()


def refresh_auth_nodes(s):
    """Gathers contents for AUTH and restarts Treehash instances."""
    for h in [h for h in range(H) if ((s + 1) % (2 ** h)) == 0]:
        if TREEHASH[h].stack:  # prevent going past 2^H'th leaf node
            AUTH[h] = TREEHASH[h].stack[0]
            startidx = (s + 1 + 2 ** h) ^ (2 ** h)
            if startidx < 2 ** H:
                TREEHASH[h].__init__(h, startidx)


def build_stacks():
    """Updates the Treehash instances."""
    for h in range(H):
        TREEHASH[h].update()
        TREEHASH[h].update()


def traverse(s):
    """Returns the auth nodes required for the next path."""
    authpath = copy.copy([x for x in AUTH])
    refresh_auth_nodes(s)
    build_stacks()
    return authpath


if __name__ == "__main__":
    correct_root = recursive_hash(H)
    print('Treehash function: {}'.format(treehash(H).v == correct_root))
    th = Treehash(H)
    for _ in range(2 ** (H + 1)):
        th.update()
    print('Treehash class: {}'.format(th.stack[0].v == correct_root))
    keygen_and_setup()
    for s in range(2 ** H):
        root = compute_root(H, s, traverse(s))
        print('iteration {}: {}'.format(s, root == correct_root))
