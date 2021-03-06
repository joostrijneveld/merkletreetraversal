#! /usr/bin/env python

from common import Node, leafcalc, g, recursive_hash, compute_root

H = 8
K = 4
assert K >= 2 and (H - K) % 2 == 0

STACK = []
AUTH = [None] * H
KEEP = [None] * (H // 2)
TREEHASH = [None] * (H - K)
RETAIN = [None] * ((1 << K) - K - 1)


class Treehash(object):

    def __init__(self, h, startidx=0, completed=False):
        self.next_idx = startidx
        self.node = None
        self.completed = completed
        self.h = h
        self.stackusage = 0  # if we would not keep track, nodes would be mixed

    def update(self):
        """Performs one iteration of Treehash, i.e. adds one leaf node.
        Note that this is different from Treehash.update() in the classic
        traversal algorithm, where only one computational unit is performed."""
        node1 = Node(h=0, v=leafcalc(self.next_idx))
        while self.stackusage > 0 and STACK[-1].h == node1.h:
            node2 = STACK.pop()
            self.stackusage -= 1
            node1 = Node(h=node1.h+1, v=g(node2.v + node1.v))
        STACK.append(node1)
        self.stackusage += 1
        self.next_idx += 1
        if self.stackusage == 1 and STACK[-1].h == self.h:
            self.completed = True
            self.node = STACK.pop()
            self.stackusage -= 1

    def height(self):
        r = H
        for node in STACK[-self.stackusage:]:
            if node.h < r:
                r = node.h
        return r


def keygen_and_setup():
    """Sets up TREEHASH, RETAIN and AUTH for the start of BDS traversal."""
    for h in range(H - K):
        TREEHASH[h] = Treehash(h, completed=True)
    stack = []
    for j in range(1 << H):
        node1 = Node(h=0, v=leafcalc(j))
        if node1.h < H - K and j == 3:
            TREEHASH[0].node = node1
        while stack and stack[-1].h == node1.h:
            if j >> node1.h == 1:
                AUTH[node1.h] = node1
            else:  # in this case node1 is a right-node with row-index 2j + 3
                if node1.h < H - K and j >> node1.h == 3:
                    TREEHASH[node1.h].node = node1
                elif node1.h >= H - K:
                    offset = (1 << (H - 1 - node1.h)) + node1.h - H
                    rowidx = ((j >> node1.h) - 3) >> 1
                    RETAIN[offset + rowidx] = node1
            node2 = stack.pop()
            node1 = Node(h=node1.h + 1, v=g(node2.v + node1.v))
        stack.append(node1)
    return stack.pop()


def traverse(s):
    """Returns the auth nodes for leaf s + 1."""
    for h in range(H):
        if not ((s >> h) & 1):
            tau = h
            break

    if tau > 0:
        tempKEEP = KEEP[(tau - 1) >> 1]  # prevent overwriting too soon

    if not ((s >> (tau+1)) & 1) and tau < H - 1:
        KEEP[tau >> 1] = AUTH[tau]

    if tau == 0:
        AUTH[0] = Node(h=0, v=leafcalc(s))

    else:
        AUTH[tau] = Node(h=0, v=g(AUTH[tau - 1].v + tempKEEP.v))
        for h in range(tau):
            if h < H - K:
                AUTH[h] = TREEHASH[h].node
            else:
                offset = (1 << (H - 1 - h)) + h - H
                rowidx = ((s >> h) - 1) >> 1
                AUTH[h] = RETAIN[offset + rowidx]
        for h in range(tau if (tau < H - K) else H - K):
            startidx = s + 1 + 3 * (1 << h)
            if startidx < 1 << H:
                TREEHASH[h].__init__(h, startidx)

    for _ in range((H - K) >> 1):
        l_min = H
        h = H - K
        for j in range(H - K):
            if TREEHASH[j].completed:
                low = H
            elif TREEHASH[j].stackusage == 0:
                low = j
            else:
                low = TREEHASH[j].height()
            if low < l_min:
                h = j
                l_min = low
        if h != H - K:
            TREEHASH[h].update()

    return AUTH


if __name__ == "__main__":
    correct_root = recursive_hash(H)
    keygen_and_setup()
    print('leaf 0: {}'.format(compute_root(H, 0, AUTH) == correct_root))
    for s in range((1 << H) - 1):
        root = compute_root(H, s + 1, traverse(s))
        print('leaf {}: {}'.format(s + 1, root == correct_root))
