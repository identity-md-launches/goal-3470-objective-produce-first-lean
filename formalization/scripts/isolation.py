"""Linux syscall-level network isolation, installed before running supplied tools."""
import ctypes
import errno
import socket
from common import Failure, require


def deny_network():
    """Inherited seccomp filter; no dead-proxy or reachability-test fallback.

    All socket creation/use is denied, as are io_uring (which can submit socket
    operations) and cross-process fd acquisition. This is network isolation,
    not a sandbox for hostile compiler binaries or arbitrary native code.
    """
    try:
        lib = ctypes.CDLL("libseccomp.so.2", use_errno=True)
    except OSError as exc:
        raise Failure("UNVERIFIED network isolation: Linux libseccomp.so.2 required") from exc
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_rule_add.restype = ctypes.c_int
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_load.restype = ctypes.c_int
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7FFF0000)  # SCMP_ACT_ALLOW
    require(bool(ctx), "UNVERIFIED network isolation: seccomp_init failed")
    try:
        for name in ("socket", "socketpair", "connect", "bind", "listen", "accept", "accept4",
                     "sendto", "sendmsg", "sendmmsg", "recvfrom", "recvmsg", "recvmmsg", "shutdown",
                     "io_uring_setup", "io_uring_enter", "io_uring_register", "pidfd_getfd", "ptrace"):
            number = lib.seccomp_syscall_resolve_name(name.encode())
            require(number >= 0, f"UNVERIFIED network isolation: unknown syscall {name}")
            require(lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, number, 0) == 0,
                    f"UNVERIFIED network isolation: cannot filter {name}")
        require(lib.seccomp_load(ctx) == 0, "UNVERIFIED network isolation: seccomp_load denied")
    finally:
        lib.seccomp_release(ctx)
    for family in (socket.AF_INET, socket.AF_INET6, socket.AF_UNIX):
        try:
            probe = socket.socket(family, socket.SOCK_STREAM)
        except OSError as exc:
            require(exc.errno == errno.EPERM, f"UNVERIFIED network probe: {exc}")
        else:
            probe.close()
            raise Failure("network isolation failed: socket creation succeeded")
    print("network isolation: PASS (inherited Linux seccomp; IPv4/IPv6/Unix socket probes denied with EPERM)", flush=True)
