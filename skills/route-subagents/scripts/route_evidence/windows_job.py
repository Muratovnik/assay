"""Small stdlib binding to Windows kernel job ownership (Windows 8+).

The gate process reads no command before assignment, so no target can spawn
outside the job. No breakaway flags are enabled. Closing the final job handle
kills every member, including descendants of an already exited worker.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

SIZE_T = ctypes.c_size_t
DWORD = wintypes.DWORD


class BasicLimits(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                ("flags", DWORD), ("min_working_set", SIZE_T), ("max_working_set", SIZE_T),
                ("active_process_limit", DWORD), ("affinity", SIZE_T),
                ("priority", DWORD), ("scheduling_class", DWORD)]


class IOCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in
                ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", BasicLimits), ("io", IOCounters), ("process_memory", SIZE_T),
                ("job_memory", SIZE_T), ("peak_process_memory", SIZE_T), ("peak_job_memory", SIZE_T)]


kernel = ctypes.WinDLL("kernel32", use_last_error=True)
for name, args, result in (
    ("CreateJobObjectW", [ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
    ("SetInformationJobObject", [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, DWORD], wintypes.BOOL),
    ("AssignProcessToJobObject", [wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
    ("OpenProcess", [DWORD, wintypes.BOOL, DWORD], wintypes.HANDLE),
    ("TerminateJobObject", [wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
    ("CloseHandle", [wintypes.HANDLE], wintypes.BOOL),
):
    function = getattr(kernel, name)
    function.argtypes, function.restype = args, result


def checked(value):
    if not value:
        raise ctypes.WinError(ctypes.get_last_error())
    return value


class Job:
    def __init__(self):
        self.handle = checked(kernel.CreateJobObjectW(None, None))
        try:
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            checked(kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits),
                                                   ctypes.sizeof(limits)))
        except BaseException:
            self.close()
            raise

    def assign(self, pid):
        # Only the direct gate's PID is opened, while it is alive and awaiting
        # stdin. No process enumeration or ancestor-based ownership inference.
        handle = checked(kernel.OpenProcess(0x0100 | 0x0001, False, pid))
        try:
            checked(kernel.AssignProcessToJobObject(self.handle, handle))
        finally:
            kernel.CloseHandle(handle)

    def terminate(self):
        if self.handle:
            checked(kernel.TerminateJobObject(self.handle, 1))

    def close(self):
        if self.handle:
            handle, self.handle = self.handle, None
            checked(kernel.CloseHandle(handle))
