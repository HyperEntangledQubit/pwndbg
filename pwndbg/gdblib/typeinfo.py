"""
Common types, and routines for manually loading types from file
via GCC.
"""

from __future__ import annotations

import sys
from typing import Any

import gdb

import pwndbg.lib.cache
import pwndbg.lib.gcc
import pwndbg.lib.tempfile

module = sys.modules[__name__]
ptrsize: int


def lookup_types(*types: str) -> gdb.Type:
    for type_str in types:
        try:
            return gdb.lookup_type(type_str)
        except Exception as e:
            exc = e
    raise exc


def update():
    # Workaround for Rust stuff, see https://github.com/pwndbg/pwndbg/issues/855
    lang = gdb.execute("show language", to_string=True)
    if "rust" not in lang:
        restore_lang = None
    else:
        gdb.execute("set language c")
        if '"auto;' in lang:
            restore_lang = "auto"
        else:
            restore_lang = "rust"

    module.char = gdb.lookup_type("char")
    module.ulong = lookup_types("unsigned long", "uint", "u32", "uint32")
    module.long = lookup_types("long", "int", "i32", "int32")
    module.uchar = lookup_types("unsigned char", "ubyte", "u8", "uint8")
    module.ushort = lookup_types("unsigned short", "ushort", "u16", "uint16", "uint16_t")
    module.uint = lookup_types("unsigned int", "uint", "u32", "uint32")
    module.void = lookup_types("void", "()")

    module.uint8 = module.uchar
    module.uint16 = module.ushort
    module.uint32 = module.uint
    module.uint64 = lookup_types("unsigned long long", "ulong", "u64", "uint64")
    module.unsigned = {
        1: module.uint8,
        2: module.uint16,
        4: module.uint32,
        8: module.uint64,
    }

    module.int8 = lookup_types("char", "i8", "int8")
    module.int16 = lookup_types("short", "short int", "i16", "int16")
    module.int32 = lookup_types("int", "i32", "int32")
    module.int64 = lookup_types("long long", "long long int", "long", "i64", "int64")
    module.signed = {1: module.int8, 2: module.int16, 4: module.int32, 8: module.int64}

    module.pvoid = void.pointer()
    module.ppvoid = pvoid.pointer()
    module.pchar = char.pointer()

    module.ptrsize = pvoid.sizeof

    if pvoid.sizeof == 4:
        module.ptrdiff = module.uint32
        module.size_t = module.uint32
        module.ssize_t = module.int32
    elif pvoid.sizeof == 8:
        module.ptrdiff = module.uint64
        module.size_t = module.uint64
        module.ssize_t = module.int64
    else:
        raise Exception("Pointer size not supported")
    module.null = gdb.Value(0).cast(void)

    # Rust workaround part 2
    if restore_lang:
        gdb.execute(f"set language {restore_lang}")


# TODO: Remove this global initialization, or move it somewhere else
# Call it once so we load all of the types
update()


def load(name: str):
    """Load a GDB symbol; note that new symbols can be added with `add-symbol-file` functionality"""
    try:
        return gdb.lookup_type(name)
    except gdb.error:
        return None


def read_gdbvalue(type_name: str, addr):
    """Read the memory contents at addr and interpret them as a GDB value with the given type"""
    gdb_type = pwndbg.gdblib.typeinfo.load(type_name)
    return gdb.Value(addr).cast(gdb_type.pointer()).dereference()


def get_type(size: int) -> Any:
    return {
        1: pwndbg.gdblib.typeinfo.uint8,
        2: pwndbg.gdblib.typeinfo.uint16,
        4: pwndbg.gdblib.typeinfo.uint32,
        8: pwndbg.gdblib.typeinfo.uint64,
    }[size]
