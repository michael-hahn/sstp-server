import ctypes
from ctypes import pythonapi as api
import sys
from types import (BuiltinFunctionType, GetSetDescriptorType,
                   MemberDescriptorType, MethodType)

import guppy
from guppy.heapy import Path

hp = guppy.hpy()


def _w(x):
    def f():
        x
    return f


CellType = type(_w(0).__closure__[0])

del _w

# -----------------------------------------------------------------------------


def _write_struct_attr(addr, value, add_offset):
        ptr_size = ctypes.sizeof(ctypes.py_object)
        ptrs_in_struct = (3 if hasattr(sys, "getobjects") else 1) + add_offset
        offset = ptrs_in_struct * ptr_size + ctypes.sizeof(ctypes.c_ssize_t)
        ref = ctypes.byref(ctypes.py_object(value))
        ctypes.memmove(addr + offset, ref, ptr_size)


def _replace_attribute(source, rel, new):
    if isinstance(source, (MethodType, BuiltinFunctionType)):
        if rel == "__self__":
            # Note: PyMethodObject->im_self and PyCFunctionObject->m_self
            # have the same offset
            _write_struct_attr(id(source), new, 1)
            return
        if rel == "im_self":
            return  # Updated via __self__
    if isinstance(source, type):
        if rel == "__base__":
            return  # Updated via __bases__
        if rel == "__mro__":
            return  # Updated via __bases__ when important, otherwise futile
    if isinstance(source, (GetSetDescriptorType, MemberDescriptorType)):
        if rel == "__objclass__":
            _write_struct_attr(id(source), new, 0)
            return
    try:
        setattr(source, rel, new)
    except TypeError as exc:
        print("Unknown R_ATTRIBUTE (read-only): {} ({})".format(rel, type(source)))


def _replace_indexval(source, rel, new):
    if isinstance(source, tuple):
        # !!!SPLICE =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
        # FIXME: Unfortunately, replacing tuple objects lead to errors difficult to
        #  debug. We will leave this for future work. For now, to avoid this issue,
        #  we should avoid e.g., saving tuples in data structures in evaluation.
        #  The next three lines of code cause the error and thus commented out.
        # temp = list(source)
        # temp[rel] = new
        # replace(source, tuple(temp))
        # =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
        return
    source[rel] = new


def _replace_indexkey(source, rel, new):
    # !!!SPLICE =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
    # 'dict_keys' object is not subscriptable in Python
    # 3, so we convert it into a list first.
    # source[new] = source.pop(source.keys()[rel])
    source[new] = source.pop(list(source.keys())[rel])
    # =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=


def _replace_interattr(source, rel, new):
    if isinstance(source, CellType):
        api.PyCell_Set(ctypes.py_object(source), ctypes.py_object(new))
        return
    if rel == "ob_type":
        source.__class__ = new
        return
    print("Unknown R_INTERATTR: {} ({})".format(rel, type(source)))


def _replace_local_var(source, rel, new):
    source.f_locals[rel] = new
    api.PyFrame_LocalsToFast(ctypes.py_object(source), ctypes.c_int(0))


_RELATIONS = {
    Path.R_ATTRIBUTE: _replace_attribute,
    Path.R_INDEXVAL: _replace_indexval,
    Path.R_INDEXKEY: _replace_indexkey,
    Path.R_INTERATTR: _replace_interattr,
    Path.R_LOCAL_VAR: _replace_local_var
}


def _path_key_func(path):
    reltype = type(path.path[1]).__bases__[0]
    return 1 if reltype is Path.R_ATTRIBUTE else 0


def get_objects():
    """
    Get all live objects in the heap using guppy.
    This is the same as GC's get_objects().
    """
    return hp.heap().nodes


def set_heap_start_point():
    """
    Set a starting point to traverse the heap. Only
    objects created *after* this function call will be
    included when get_objects() is called after this
    function call. This is used in "extended heap"
    traversal when registered files are loaded from
    disk for taint inspection and value synthesis.
    We use this function *before* loading files into
    memory and then call get_objects() to only inspect
    objects from the loaded files (instead of the
    entire heap again). See pickle.py and lsm.py for context.
    """
    hp.setrelheap()


def get_path_map(objs):
    """
    Return a dict that maps an object ID to all the paths that refer the object.
    We should have an entry for each object in "objs".
    """
    d = dict()
    paths = hp.iso(*objs).pathsin
    for path in paths:
        obj_id = id(path.path[2].theone)
        if obj_id not in d:
            d[obj_id] = [path]
        else:
            d[obj_id].append(path)
    return d


def replace(new, paths):
    """
    Replace all paths to point to new.
    Path should be the output of hp.iso().pathsin.
    """
    for path in sorted(paths, key=_path_key_func):
        relation = path.path[1]
        try:
            func = _RELATIONS[type(relation).__bases__[0]]
        except KeyError:
            print("Unknown relation: {} ({})".format(relation, type(path.src.theone)))
            continue
        func(path.src.theone, relation.r, new)

# !!!SPLICE =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
# This is a different implementation where each 'old' object is replaced by the 'new'
# object. It will call hp.iso().pathsin every time an object needs to be replaced, which
# results in many scans of the heap if we want to replace a number of objects (i.e.,
# calling this function in a loop), which incurs lots of overhead. We therefore use
# get_path_map() and replace() instead to minimize heap walks.
# =+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
def replace_single(old, new):
    for path in sorted(hp.iso(old).pathsin, key=_path_key_func):
        relation = path.path[1]
        try:
            func = _RELATIONS[type(relation).__bases__[0]]
        except KeyError:
            print("Unknown relation: {} ({})".format(relation, type(path.src.theone)))
            continue
        func(path.src.theone, relation.r, new)


if __name__ == "__main__":
    pass
    # from django.splice.splicetypes import SpliceMixin
    # i = SpliceInt(5)
    # s = SpliceStr("Hi")
    # hp = guppy.hpy()
    # hpo = hp.iso(i, s)
    # paths = hpo.pathsin
    # for path in paths:
    #     rel = path.path[1]
    #     src = path.path[0].theone
    #     dst = path.path[2]
    # for i in range(len(heap.bytype)):
    #     t = heap.bytype[i]
    #     if issubclass(t.kind.arg, SpliceMixin):
    #         for j in range(len(t.byid)):
    #             obj = t.byid[j].theone
