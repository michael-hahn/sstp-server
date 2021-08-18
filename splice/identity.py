import ipaddress
MAX_USERS = 63


def empty_taint():
    return 0


class TaintSource(object):
    """Track everything about user taints."""
    MAX_USERS = MAX_USERS  # Maximum number of user allowed
    current_user_id = None
    current_user_taint = empty_taint()


def set_current_user_id(uid):
    TaintSource.current_user_id = uid
    set_taint_from_id(uid)


def set_current_user_taint(taint):
    TaintSource.current_user_taint = taint


def set_taint_from_id(uid):
    pos = uid % TaintSource.MAX_USERS
    taint = 1 << pos
    set_current_user_taint(taint)


# For int taint only
def get_taint_from_id(uid):
    pos = uid % TaintSource.MAX_USERS
    return 1 << pos


def taint_id_from_addr(address):
    # address is a tuple (ip, port) # FIXME: this is specific to TCP
    # TODO: a better way to assign taint
    taint = get_taint_from_id(int(ipaddress.IPv4Address(address[0])) + address[1])
    print("[splice] socket {} is tainted by ID: {}".format(address, taint))
    return taint


def to_int(taint):
    return taint


def to_bitarray(taint):
    """Converting an integer taint to a bitarray has no effect.
    For backward compatibility only.
    """
    return taint


def union(taint_1, taint_2):
    """Union two taints and return a union-ed taint.
    """
    return taint_1 | taint_2


def union_to_int(taint_1, taint_2):
    """Similar to union but return a union-ed integer.
    For backward compatibility only.
    """
    return union(taint_1, taint_2)


if __name__ == "__main__":
    pass
