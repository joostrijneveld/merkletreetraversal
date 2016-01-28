from common import recursive_hash, compute_root


def test_traversal():
    from bdstraversal import traverse, H, AUTH, keygen_and_setup
    correct_root = recursive_hash(H)
    keygen_and_setup()
    assert compute_root(H, 0, AUTH) == correct_root
    for s in range(2 ** H - 1):
        assert compute_root(H, s + 1, traverse(s)) == correct_root


def test_traversal_clike():
    from bdstraversal_c_like import traverse, H, AUTH, keygen_and_setup
    correct_root = recursive_hash(H)
    keygen_and_setup()
    assert compute_root(H, 0, AUTH) == correct_root
    for s in range(2 ** H - 1):
        assert compute_root(H, s + 1, traverse(s)) == correct_root


def test_state_traversal():
    from bdstraversal_mt_c_like import BDSState, H
    correct_root = recursive_hash(H)
    state = BDSState()
    state.keygen_and_setup()
    assert compute_root(H, 0, state.auth) == correct_root
    for s in range(2 ** H - 1):
        auth = state.traverse_and_update(s)
        assert compute_root(H, s + 1, auth) == correct_root


def test_mt_state_traversal():
    from bdstraversal_mt_c_like import MTBDSState, H, D
    correct_root = recursive_hash(H)
    states = MTBDSState()
    states.keygen_and_setup()
    for s in range(2 ** (D*H)):
        authpaths = states.authpaths()
        for i, path in enumerate(authpaths):
            idx = (s >> (H*i)) & ((1 << H) - 1)
            assert compute_root(H, idx, path) == correct_root
        states.traverse(s)
