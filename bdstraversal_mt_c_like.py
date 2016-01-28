#! /usr/bin/env python

from common import Node, leafcalc, g, recursive_hash, compute_root, end_of_tree

H = 4  # this is the height of the subtrees
K = 2
D = 3
assert K >= 2 and (H - K) % 2 == 0
if (H - K) / 2 < D - 1:
    print("(H-K) / 2 >= D-1 does not hold; not enough updates to link trees!")


class Treehash(object):

    def __init__(self, h, stack, startidx=0, completed=False):
        self.next_idx = startidx
        self.node = None
        self.completed = completed
        self.h = h
        self.stack = stack
        self.stackusage = 0  # if we would not keep track, nodes would be mixed

    def restart(self, startidx):
        self.__init__(h=self.h, stack=self.stack, startidx=startidx)

    def update(self):
        """Performs one iteration of Treehash, i.e. adds one leaf node.
        Note that this is different from Treehash.update() in the classic
        traversal algorithm, where only one computational unit is performed."""
        node1 = Node(h=0, v=leafcalc(self.next_idx))
        while self.stackusage > 0 and self.stack[-1].h == node1.h:
            node2 = self.stack.pop()
            self.stackusage -= 1
            node1 = Node(h=node1.h+1, v=g(node2.v + node1.v))
        self.stack.append(node1)
        self.stackusage += 1
        self.next_idx += 1
        if self.stackusage == 1 and self.stack[-1].h == self.h:
            self.completed = True
            self.node = self.stack.pop()
            self.stackusage -= 1

    def height(self):
        r = H
        for node in self.stack[-self.stackusage:]:
            if node.h < r:
                r = node.h
        return r


class BDSState(object):

    def __init__(self):
        self.stack = []
        self.auth = [None] * H
        self.keep = [None] * (H // 2)
        self.treehash = [None] * (H - K)
        self.retain = [None] * ((1 << K) - K - 1)
        self.nextidx = 0
        for h in range(H - K):
            self.treehash[h] = Treehash(h, self.stack, completed=True)

    def stack_update(self, idx):
        node1 = Node(h=0, v=leafcalc(idx))
        if node1.h < H - K and idx == 3:
            self.treehash[0].node = node1
        while self.stack and self.stack[-1].h == node1.h:
            if idx >> node1.h == 1:
                self.auth[node1.h] = node1
            else:  # node1 is a right-node with row-index 2idx + 3
                if node1.h < H - K and idx >> node1.h == 3:
                    self.treehash[node1.h].node = node1
                elif node1.h >= H - K:
                    offset = (1 << (H - 1 - node1.h)) + node1.h - H
                    rowidx = ((idx >> node1.h) - 3) >> 1
                    self.retain[offset + rowidx] = node1
            node2 = self.stack.pop()
            node1 = Node(h=node1.h + 1, v=g(node2.v + node1.v))
        self.stack.append(node1)

    def keygen_and_setup(self):
        """Sets up the state for the start of BDS traversal."""
        for j in range(1 << H):
            self.stack_update(j)
        return self.stack.pop()

    def traverse(self, s):
        """Returns the auth nodes for leaf s + 1."""
        for h in range(H):
            if not ((s >> h) & 1):
                tau = h
                break
        if tau > 0:
            tempkeep = self.keep[(tau - 1) >> 1]  # prevent overwriting

        if not ((s >> (tau+1)) & 1) and tau < H - 1:
            self.keep[tau >> 1] = self.auth[tau]

        if tau == 0:
            self.auth[0] = Node(h=0, v=leafcalc(s))

        else:
            self.auth[tau] = Node(h=0, v=g(self.auth[tau - 1].v + tempkeep.v))
            for h in range(tau):
                if h < H - K:
                    self.auth[h] = self.treehash[h].node
                else:
                    offset = (1 << (H - 1 - h)) + h - H
                    rowidx = ((s >> h) - 1) >> 1
                    self.auth[h] = self.retain[offset + rowidx]
            for h in range(tau if (tau < H - K) else H - K):
                startidx = s + 1 + 3 * (1 << h)
                if startidx < 1 << H:
                    self.treehash[h].restart(startidx)
        return self.auth

    def update(self, n):
        for _ in range(n):
            l_min = H
            h = H - K
            for j in range(H - K):
                if self.treehash[j].completed:
                    low = H
                elif self.treehash[j].stackusage == 0:
                    low = j
                else:
                    low = self.treehash[j].height()
                if low < l_min:
                    h = j
                    l_min = low
            if h == H - K:
                break
            self.treehash[h].update()
            n -= 1
        return n

    def traverse_and_update(self, s):
        auth = self.traverse(s)
        self.update((H - K) >> 1)
        return auth


class MTBDSState(object):

    def __init__(self):
        self.currstates = [BDSState() for _ in range(D)]
        self.nextstates = [BDSState() for _ in range(D)]

    def keygen_and_setup(self):
        for state in self.currstates:
            root = state.keygen_and_setup()
        return root

    def authpaths(self):
        return [state.auth for state in self.currstates]

    def traverse(self, s):
        needswap_upto = -1
        updates = H - K >> 1
        self.nextstates[0].stack_update(self.nextstates[0].nextidx)
        self.nextstates[0].nextidx += 1
        for i in range(D):
            if not end_of_tree(s, H, i):
                if i == needswap_upto+1:
                    self.currstates[i].traverse((s >> (H*i)) & ((1<<H)-1))
                updates = self.currstates[i].update(updates)
                nxt = self.nextstates[i]
                if i > 0 and updates > 0 and nxt.nextidx < (1 << H):
                    nxt.stack_update(nxt.nextidx)
                    nxt.nextidx += 1
                    updates -= 1
            else:
                needswap_upto = i
                self.currstates[i] = self.nextstates[i]
                self.nextstates[i] = BDSState()
                updates -= 1  # a scheme like XMSS^MT would spend 1 to link
