#! /usr/bin/env python

import binascii
import struct
from hashlib import sha256


def leafcalc(j):
    return sha256(struct.pack("I", j)).digest()


def g(v):
    return sha256(v).digest()


def recursive_hash(H, i=0):
    if H == 0:
        return leafcalc(i)
    return g(recursive_hash(H - 1, i) + recursive_hash(H-1, i + (2 ** (H-1))))


def treehash(H):
    stack = []
    for j in range(2 ** H):
        node1 = {'h': 0, 'v': leafcalc(j)}
        while stack and stack[-1]['h'] == node1['h']:
            node2 = stack.pop()
            node1 = {'h': node1['h']+1, 'v': g(node2['v'] + node1['v'])}
        stack.append(node1)
    return stack.pop()


def b2hex(b):
    return binascii.hexlify(b).decode('utf8')

print(b2hex(recursive_hash(8)))
print(b2hex(treehash(8)['v']))
