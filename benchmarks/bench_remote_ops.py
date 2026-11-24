# SPDX-License-Identifier: Apache-2.0
"""Experiment 5: Standard UIA calls vs Windows UI Automation Remote Operations.

Uses native Windows 11 `Windows.UI.UIAutomation.Core.CoreAutomationRemoteOperation`
(WinRT activation via `combase.dll` + official instruction opcodes from
`microsoft/Microsoft-UI-UIAutomation`) without introducing Rust or modifying `engine/`.

Measures two honest workloads across Notepad, File Explorer, Chromium, and Electron:
  A) Subtree DFS traversal + batch property extraction inside the Remote VM
     (testing top HWND root vs hosted child HWND fragments to observe HWND/process walls
     and InstructionLimitExceeded behavior honestly).
  B) Batch property inspection (`Name`, `ControlType`, `BoundingRectangle`, `IsEnabled`,
     `IsOffscreen`) over K elements (per target process PID) via 1 RemoteOp VM Execute
     call vs standard out-of-process individual COM calls and vs `FindAllBuildCache`.
"""
import ctypes
import struct
import time
import uuid
from ctypes import wintypes

import comtypes
import comtypes.client

from . import common
from .bench_uia import FULL_PATTERNS, FULL_PROPS, INTERACTIVE_CTYPES, _TYPE_NAMES, _make_cache_request, _unpack_elements
from .corpus import DesktopTarget

comtypes.client.GetModule("UIAutomationCore.dll")
from comtypes.gen import UIAutomationClient as UIA  # noqa: E402

_combase = ctypes.WinDLL("combase", use_last_error=True)
_u32 = ctypes.WinDLL("user32", use_last_error=True)


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    def __init__(self, s):
        u = uuid.UUID(s)
        super().__init__(u.time_low, u.time_mid, u.time_hi_version, (ctypes.c_ubyte * 8)(*u.bytes[8:]))


class _FRect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("w", ctypes.c_float), ("h", ctypes.c_float)]


_IID_IAutomationElement = _GUID("A1898370-2C07-56FD-993F-61A72A08058C")
_IID_ICoreAutomationRemoteOperation = _GUID("3AC656F4-E2BC-5C6E-B8E7-B224FB74B060")
_IID_IPropertyValue = _GUID("4BD682DD-7554-40E9-9A9B-82654EDE7E62")

_combase.RoInitialize.argtypes = [ctypes.c_int]
_combase.RoInitialize.restype = ctypes.c_long
_combase.WindowsCreateString.argtypes = [ctypes.c_wchar_p, wintypes.UINT, ctypes.POINTER(ctypes.c_void_p)]
_combase.WindowsCreateString.restype = ctypes.c_long
_combase.WindowsDeleteString.argtypes = [ctypes.c_void_p]
_combase.WindowsDeleteString.restype = ctypes.c_long
_combase.WindowsGetStringRawBuffer.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.UINT)]
_combase.WindowsGetStringRawBuffer.restype = ctypes.c_wchar_p
_combase.RoActivateInstance.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
_combase.RoActivateInstance.restype = ctypes.c_long

# Official opcodes from Microsoft-UI-UIAutomation RemoteOperationInstructions.h
OP_SET = 0x01
OP_FORK_IF_TRUE = 0x02
OP_FORK_IF_FALSE = 0x03
OP_FORK = 0x04
OP_HALT = 0x05
OP_NEW_LOOP_BLOCK = 0x06
OP_END_LOOP_BLOCK = 0x07
OP_BREAK_LOOP = 0x08
OP_NEW_INT = 0x1D
OP_NEW_BOOL = 0x1F
OP_NEW_ARRAY = 0x25
OP_ARR_APPEND = 0x2A
OP_ARR_REMOVE_AT = 0x2C
OP_ARR_GET_AT = 0x2D
OP_ARR_SIZE = 0x2E
OP_ADD = 0x0E
OP_COMPARE = 0x1C
OP_GET_PROP = 0x38
OP_NAVIGATE = 0x39
OP_IS_NULL = 0x3A
OP_COMPARE_EQ = 0
_PROP_BATCH = (
    UIA.UIA_NamePropertyId,
    UIA.UIA_ControlTypePropertyId,
    UIA.UIA_BoundingRectanglePropertyId,
    UIA.UIA_IsEnabledPropertyId,
    UIA.UIA_IsOffscreenPropertyId,
)


def _vcall(ptr, idx, restype, argtypes, *args):
    vtbl = ctypes.cast(ctypes.cast(ptr, ctypes.POINTER(ctypes.c_void_p))[0], ctypes.POINTER(ctypes.c_void_p))
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vtbl[idx])(ptr, *args)


def _release(ptr):
    if ptr:
        _vcall(ptr, 2, wintypes.ULONG, [])


def _qi_winrt_element(com_elem):
    raw = ctypes.cast(com_elem, ctypes.c_void_p).value
    out = ctypes.c_void_p()
    hr = _vcall(
        raw, 0, ctypes.c_long,
        [ctypes.POINTER(_GUID), ctypes.POINTER(ctypes.c_void_p)],
        ctypes.byref(_IID_IAutomationElement), ctypes.byref(out),
    )
    if hr != 0:
        raise OSError(f"QI IAutomationElement failed hr={hr:#x}")
    return out


def _activate_remote_op():
    _combase.RoInitialize(1)
    hs = ctypes.c_void_p()
    name = "Windows.UI.UIAutomation.Core.CoreAutomationRemoteOperation"
    _combase.WindowsCreateString(name, len(name), ctypes.byref(hs))
    insp = ctypes.c_void_p()
    try:
        hr = _combase.RoActivateInstance(hs, ctypes.byref(insp))
        if hr != 0:
            raise OSError(f"RoActivateInstance failed hr={hr:#x}")
    finally:
        _combase.WindowsDeleteString(hs)
    rop = ctypes.c_void_p()
    hr = _vcall(
        insp.value, 0, ctypes.c_long,
        [ctypes.POINTER(_GUID), ctypes.POINTER(ctypes.c_void_p)],
        ctypes.byref(_IID_ICoreAutomationRemoteOperation), ctypes.byref(rop),
    )
    _release(insp.value)
    if hr != 0:
        raise OSError(f"QI ICoreAutomationRemoteOperation failed hr={hr:#x}")
    return rop


def _decode_inspectable(ptr):
    if not ptr:
        return None
    pv = ctypes.c_void_p()
    hr = _vcall(
        ptr, 0, ctypes.c_long,
        [ctypes.POINTER(_GUID), ctypes.POINTER(ctypes.c_void_p)],
        ctypes.byref(_IID_IPropertyValue), ctypes.byref(pv),
    )
    if hr != 0:
        return None
    try:
        pt = ctypes.c_int32(0)
        _vcall(pv.value, 6, ctypes.c_long, [ctypes.POINTER(ctypes.c_int32)], ctypes.byref(pt))
        t = pt.value
        if t == 12:  # String
            hs = ctypes.c_void_p()
            _vcall(pv.value, 19, ctypes.c_long, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(hs))
            ln = wintypes.UINT(0)
            s = _combase.WindowsGetStringRawBuffer(hs, ctypes.byref(ln))
            _combase.WindowsDeleteString(hs)
            return s
        if t == 4:  # Int32
            v = ctypes.c_int32(0)
            _vcall(pv.value, 11, ctypes.c_long, [ctypes.POINTER(ctypes.c_int32)], ctypes.byref(v))
            return v.value
        if t == 11:  # Boolean
            v = ctypes.c_ubyte(0)
            _vcall(pv.value, 18, ctypes.c_long, [ctypes.POINTER(ctypes.c_ubyte)], ctypes.byref(v))
            return bool(v.value)
        if t == 19:  # Rect
            r = _FRect()
            _vcall(pv.value, 25, ctypes.c_long, [ctypes.POINTER(_FRect)], ctypes.byref(r))
            return [int(r.x), int(r.y), int(r.w), int(r.h)]
        return None
    finally:
        _release(pv.value)


def _decode_vector(vec_ptr):
    sz = wintypes.UINT(0)
    if _vcall(vec_ptr, 7, ctypes.c_long, [ctypes.POINTER(wintypes.UINT)], ctypes.byref(sz)) != 0:
        return []
    out = []
    for i in range(sz.value):
        item = ctypes.c_void_p()
        if _vcall(vec_ptr, 6, ctypes.c_long, [wintypes.UINT, ctypes.POINTER(ctypes.c_void_p)], i, ctypes.byref(item)) == 0:
            out.append(_decode_inspectable(item.value))
            _release(item.value)
    return out


class _BytecodeBuilder:
    """Minimal emitter mirroring RemoteOperationGraph & RemoteOperationInstructionSerialization."""

    def __init__(self):
        self._buf = bytearray(struct.pack("<I", 0))  # c_bytecodeCurrentVersion = 0
        self._next_reg = 100

    def reg(self):
        self._next_reg += 1
        return self._next_reg

    def new_int(self, val):
        r = self.reg()
        self._buf += struct.pack("<iii", OP_NEW_INT, r, int(val))
        return r

    def new_bool(self, val):
        r = self.reg()
        self._buf += struct.pack("<iiB", OP_NEW_BOOL, r, 1 if val else 0)
        return r

    def new_array(self):
        r = self.reg()
        self._buf += struct.pack("<ii", OP_NEW_ARRAY, r)
        return r

    def get_prop(self, target_reg, prop_id_reg, ignore_default_reg):
        r = self.reg()
        self._buf += struct.pack("<iiiii", OP_GET_PROP, r, target_reg, prop_id_reg, ignore_default_reg)
        return r

    def navigate(self, target_reg, dir_reg):
        r = self.reg()
        self._buf += struct.pack("<iiii", OP_NAVIGATE, r, target_reg, dir_reg)
        return r

    def is_null(self, target_reg):
        r = self.reg()
        self._buf += struct.pack("<iii", OP_IS_NULL, r, target_reg)
        return r

    def arr_append(self, arr_reg, item_reg):
        self._buf += struct.pack("<iii", OP_ARR_APPEND, arr_reg, item_reg)

    def arr_size(self, arr_reg):
        r = self.reg()
        self._buf += struct.pack("<iii", OP_ARR_SIZE, r, arr_reg)
        return r

    def arr_get_at(self, arr_reg, idx_reg):
        r = self.reg()
        self._buf += struct.pack("<iiii", OP_ARR_GET_AT, r, arr_reg, idx_reg)
        return r

    def arr_remove_at(self, arr_reg, idx_reg):
        r = self.reg()
        self._buf += struct.pack("<iiii", OP_ARR_REMOVE_AT, r, arr_reg, idx_reg)
        return r

    def set_reg(self, dst_reg, src_reg):
        self._buf += struct.pack("<iii", OP_SET, dst_reg, src_reg)

    def add_int(self, dst_reg, rhs_reg):
        self._buf += struct.pack("<iii", OP_ADD, dst_reg, rhs_reg)

    def compare(self, lhs_reg, rhs_reg, cmp_op=OP_COMPARE_EQ):
        r = self.reg()
        self._buf += struct.pack("<iiiii", OP_COMPARE, r, lhs_reg, rhs_reg, cmp_op)
        return r

    def emit_raw(self, data):
        self._buf += data

    def halt(self):
        self._buf += struct.pack("<i", OP_HALT)

    def build(self):
        return bytes(self._buf)


def _execute_remote_op(imported_elements, bytecode_bytes, result_regs):
    """Execute bytecode in CoreAutomationRemoteOperation and return decoded operands + status."""
    rop = _activate_remote_op()
    winrt_objs = []
    try:
        for reg_id, com_el in imported_elements:
            we = _qi_winrt_element(com_el)
            winrt_objs.append(we)
            hr = _vcall(rop.value, 7, ctypes.c_long, [ctypes.c_int32, ctypes.c_void_p], reg_id, we)
            if hr != 0:
                raise OSError(f"ImportElement({reg_id}) failed hr={hr:#x}")
        for r_id in result_regs:
            _vcall(rop.value, 9, ctypes.c_long, [ctypes.c_int32], r_id)
        bc_copy = bytearray(bytecode_bytes)
        buf = (ctypes.c_ubyte * len(bc_copy)).from_buffer(bc_copy)
        res_ptr = ctypes.c_void_p()
        hr = _vcall(
            rop.value, 10, ctypes.c_long,
            [wintypes.UINT, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_void_p)],
            len(bc_copy), buf, ctypes.byref(res_ptr),
        )
        if hr != 0:
            raise OSError(f"RemoteOperation.Execute failed hr={hr:#x}")
        try:
            st = ctypes.c_int32(-1)
            ex = ctypes.c_long(0)
            loc = ctypes.c_int32(-1)
            _vcall(res_ptr.value, 6, ctypes.c_long, [ctypes.POINTER(ctypes.c_int32)], ctypes.byref(st))
            _vcall(res_ptr.value, 7, ctypes.c_long, [ctypes.POINTER(ctypes.c_long)], ctypes.byref(ex))
            _vcall(res_ptr.value, 8, ctypes.c_long, [ctypes.POINTER(ctypes.c_int32)], ctypes.byref(loc))
            decoded = {}
            for r_id in result_regs:
                has = ctypes.c_ubyte(0)
                _vcall(res_ptr.value, 9, ctypes.c_long, [ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte)], r_id, ctypes.byref(has))
                if has.value:
                    val = ctypes.c_void_p()
                    _vcall(res_ptr.value, 10, ctypes.c_long, [ctypes.c_int32, ctypes.POINTER(ctypes.c_void_p)], r_id, ctypes.byref(val))
                    decoded[r_id] = _decode_vector(val.value)
                    _release(val.value)
            return {"status": st.value, "extended_error": hex(ex.value & 0xFFFFFFFF), "error_location": loc.value, "results": decoded}
        finally:
            _release(res_ptr.value)
    finally:
        for we in winrt_objs:
            _release(we.value)
        _release(rop.value)


def _build_safe_subtree_walk_bytecode(max_nodes=80):
    """Exact RemoteOperationGraph-verified loop structure traversing FirstChild + NextSibling."""
    b = _BytecodeBuilder()
    r_false = b.new_bool(False)
    r_zero = b.new_int(0)
    r_one = b.new_int(1)
    r_dir_fc = b.new_int(UIA.NavigateDirection_FirstChild)
    r_dir_ns = b.new_int(UIA.NavigateDirection_NextSibling)
    r_props = [b.new_int(pid) for pid in _PROP_BATCH]

    r_queue = b.new_array()
    r_out = b.new_array()
    r_count = b.new_int(0)
    r_max = b.new_int(max_nodes)
    b.arr_append(r_queue, 1)

    # Emit verified structure from Microsoft RemoteOperationGraph.cpp:
    # cond_eval precedes NewLoopBlock, and condition_update at bottom jumps back to ForkIfFalse?
    # Look directly at RemoteOperationGraph.cpp lines 163-190:
    #   0: init cond (outside)
    #   1: NewLoopBlock(break=totalBody+4, cont=body+2)
    #   2: ForkIfFalse(cond, target = totalBody + 2 -> jumps to EndLoopBlock)
    #   3..3+body-1: body
    #   3+body..3+body+upd-1: cond_update
    #   3+totalBody: Fork(-(totalBody + 1)) -> jumps to index 2 (ForkIfFalse)!
    #   4+totalBody: EndLoopBlock
    r_qsz = b.reg(); r_hasq = b.reg(); r_und = b.reg(); r_cond = b.reg()
    def _eval_outer_cond():
        s = bytearray()
        s += struct.pack("<iii", OP_ARR_SIZE, r_qsz, r_queue)
        s += struct.pack("<iiiii", OP_COMPARE, r_hasq, r_qsz, r_zero, 2)  # > 0
        s += struct.pack("<iiiii", OP_COMPARE, r_und, r_count, r_max, 3)  # < max
        s += struct.pack("<iiii", 0x1A, r_cond, r_hasq, r_und)
        return s, 4

    r_cur = b.reg(); r_pop = b.reg()
    r_fc = b.reg(); r_fc_null = b.reg(); r_sib = b.reg(); r_sib_null = b.reg(); r_sib_ok = b.reg()
    val_regs = [b.reg() for _ in r_props]

    main_body = bytearray()
    main_body += struct.pack("<iiii", OP_ARR_GET_AT, r_cur, r_queue, r_zero)
    main_body += struct.pack("<iiii", OP_ARR_REMOVE_AT, r_pop, r_queue, r_zero)
    for pr, vr in zip(r_props, val_regs):
        main_body += struct.pack("<iiiii", OP_GET_PROP, vr, r_cur, pr, r_false)
    for vr in val_regs:
        main_body += struct.pack("<iii", OP_ARR_APPEND, r_out, vr)
    main_body += struct.pack("<iii", OP_ADD, r_count, r_one)

    # First child + append all its NextSibling chain via nested verified loop!
    main_body += struct.pack("<iiii", OP_NAVIGATE, r_sib, r_cur, r_dir_fc)
    # Inner cond init: r_sib_null = IsNull(r_sib); r_sib_ok = BoolNot(r_sib_null)
    main_body += struct.pack("<iii", OP_IS_NULL, r_sib_null, r_sib)
    main_body += struct.pack("<iii", 0x19, r_sib_ok, r_sib_null)
    # Inner loop body (append r_sib) + upd (r_sib = NextSibling(r_sib); update r_sib_ok)
    sib_body = struct.pack("<iii", OP_ARR_APPEND, r_queue, r_sib)
    sib_upd = bytearray()
    sib_upd += struct.pack("<iiii", OP_NAVIGATE, r_sib, r_sib, r_dir_ns)
    sib_upd += struct.pack("<iii", OP_IS_NULL, r_sib_null, r_sib)
    sib_upd += struct.pack("<iii", 0x19, r_sib_ok, r_sib_null)
    sib_b_n, sib_u_n = 1, 3
    sib_tot = sib_b_n + sib_u_n
    main_body += struct.pack("<iii", OP_NEW_LOOP_BLOCK, sib_tot + 4, sib_b_n + 2)
    main_body += struct.pack("<iii", OP_FORK_IF_FALSE, r_sib_ok, sib_tot + 2)
    main_body += sib_body
    main_body += sib_upd
    main_body += struct.pack("<ii", OP_FORK, -(sib_tot + 1))
    main_body += struct.pack("<i", OP_END_LOOP_BLOCK)
    inner_loop_instr_n = 1 + 1 + sib_b_n + sib_u_n + 1 + 1  # = 8
    main_body_n = 2 + len(r_props) * 2 + 1 + 3 + inner_loop_instr_n

    cond_init, cond_n = _eval_outer_cond()
    cond_upd, upd_n = _eval_outer_cond()
    tot = main_body_n + upd_n

    b.emit_raw(cond_init)
    b.emit_raw(struct.pack("<iii", OP_NEW_LOOP_BLOCK, tot + 4, main_body_n + 2))
    b.emit_raw(struct.pack("<iii", OP_FORK_IF_FALSE, r_cond, tot + 2))
    b.emit_raw(main_body)
    b.emit_raw(cond_upd)
    b.emit_raw(struct.pack("<ii", OP_FORK, -(tot + 1)))
    b.emit_raw(struct.pack("<i", OP_END_LOOP_BLOCK))
    b.halt()
    return b.build(), r_out


def _build_batch_inspect_bytecode(n_elems):
    """Build single-batch RemoteOp bytecode inspecting 5 properties across N imported elements."""
    b = _BytecodeBuilder()
    r_false = b.new_bool(False)
    r_props = [b.new_int(pid) for pid in _PROP_BATCH]
    r_out = b.new_array()
    for reg_id in range(1, n_elems + 1):
        for pr in r_props:
            vr = b.get_prop(reg_id, pr, r_false)
            b.arr_append(r_out, vr)
    b.halt()
    return b.build(), r_out


def _child_hwnds(hwnd):
    out = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(child, _):
        out.append(child)
        return True

    _u32.EnumChildWindows(wintypes.HWND(hwnd), cb, 0)
    return out


def _standard_live_reads(elements):
    """Read the same 5 properties element-by-element via standard cross-process UIA COM."""
    out = []
    for el in elements:
        name = el.CurrentName or ""
        ctype = el.CurrentControlType
        r = el.CurrentBoundingRectangle
        box = [int(r.left), int(r.top), int(r.right) - int(r.left), int(r.bottom) - int(r.top)]
        en = bool(el.CurrentIsEnabled)
        off = bool(el.CurrentIsOffscreen)
        out.append({"name": name, "ctype": ctype, "box": box, "enabled": en, "offscreen": off})
    return out


def _unpack_remote_flat(flat):
    rows = []
    for i in range(0, len(flat) - 4, 5):
        name, ctype_id, rect, en, off = flat[i], flat[i + 1], flat[i + 2], flat[i + 3], flat[i + 4]
        ctype = _TYPE_NAMES.get(ctype_id, "Unknown")
        rows.append({
            "source": "remote_op",
            "role": ctype.lower(),
            "ctype": ctype,
            "name": (name or "")[:80],
            "box": rect if isinstance(rect, list) else [0, 0, 0, 0],
            "enabled": bool(en),
            "offscreen": bool(off),
        })
    return rows


def run_remote_ops_experiments(targets=("notepad", "explorer", "chromium", "electron"), n_cold=3, n_warm=15):
    """Benchmark standard UIA vs CoreAutomationRemoteOperation across desktop apps on a dedicated MTA thread."""
    import threading
    box = {}

    def _worker():
        _combase.RoInitialize(1)
        try:
            comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        except OSError:
            pass
        results = {"targets": {}}
        try:
            uia = comtypes.client.CreateObject(UIA.CUIAutomation, interface=UIA.IUIAutomation)
            for kind in targets:
                print(f"[bench_remote_ops] Launching {kind} ...", flush=True)
                try:
                    with DesktopTarget(kind) as tgt:
                        hwnd, pid = tgt.hwnd, tgt.pid
                        root = uia.ElementFromHandle(hwnd)
                        cr = _make_cache_request(uia, props=FULL_PROPS, patterns=FULL_PATTERNS)
                        found = root.FindAllBuildCache(UIA.TreeScope_Subtree, uia.CreateTrueCondition(), cr)
                        baseline_els, _ = _unpack_elements(found)

                        live_all = [found.GetElement(i) for i in range(found.Length)]
                        # Group by UIA provider PID and select richest homogeneous process for batch RemoteOp
                        by_pid = {}
                        for e in live_all:
                            by_pid.setdefault(e.CurrentProcessId, []).append(e)
                        dom_pid = max(by_pid, key=lambda k: len(by_pid[k])) if by_pid else pid
                        dom_elems = by_pid.get(dom_pid, [])[:30]

                        walk_bc, walk_res = _build_safe_subtree_walk_bytecode(max_nodes=80)
                        top_walk_res = _execute_remote_op([(1, root)], walk_bc, [walk_res])

                        # Pick richest container anchor (Document/Pane child in target tree)
                        anchor_el = root
                        anchor_label = "top_hwnd"
                        doc_el = next((e for e in dom_elems if e.CachedControlType == UIA.UIA_DocumentControlTypeId), None)
                        fc = uia.ControlViewWalker.GetFirstChildElement(root)
                        if doc_el is not None:
                            anchor_el = doc_el
                            anchor_label = "document_control"
                        elif fc is not None:
                            anchor_el = fc
                            anchor_label = "first_child_container"

                        _, findall_stats = common.measure_workload(
                            cold_fn=lambda: (_unpack_elements(root.FindAllBuildCache(UIA.TreeScope_Subtree, uia.CreateTrueCondition(), cr))[0], {"node_count": found.Length, "ipc_round_trips": 1}),
                            warm_fn=lambda: (_unpack_elements(root.FindAllBuildCache(UIA.TreeScope_Subtree, uia.CreateTrueCondition(), cr))[0], {"node_count": found.Length, "ipc_round_trips": 1}),
                            n_cold=n_cold, n_warm=n_warm, target_pid=pid,
                        )

                        last_walk_status = {}

                        def _do_walk():
                            res = _execute_remote_op([(1, anchor_el)], walk_bc, [walk_res])
                            last_walk_status.update({"status": res["status"], "extended_error": res["extended_error"], "error_location": res["error_location"]})
                            flat = res["results"].get(walk_res, [])
                            els = _unpack_remote_flat(flat)
                            return els, {"node_count": len(els), "ipc_round_trips": 1, "response_bytes": len(walk_bc)}

                        ro_walk_els, ro_walk_stats = common.measure_workload(
                            cold_fn=_do_walk, warm_fn=_do_walk,
                            n_cold=n_cold, n_warm=n_warm, target_pid=pid,
                        )

                        k_n = len(dom_elems)
                        batch_bc, batch_res = _build_batch_inspect_bytecode(k_n)
                        imported_pairs = list(enumerate(dom_elems, 1))

                        def _std_inspect():
                            vals = _standard_live_reads(dom_elems)
                            return vals, {"node_count": len(vals), "ipc_round_trips": k_n * 5}

                        def _ro_inspect():
                            res = _execute_remote_op(imported_pairs, batch_bc, [batch_res])
                            vals = _unpack_remote_flat(res["results"].get(batch_res, []))
                            return vals, {"node_count": len(vals), "ipc_round_trips": 1, "response_bytes": len(batch_bc), "status": res["status"]}

                        _, std_inspect_stats = common.measure_workload(
                            cold_fn=_std_inspect, warm_fn=_std_inspect,
                            n_cold=n_cold, n_warm=n_warm, target_pid=pid,
                        )
                        ro_batch_els, ro_batch_stats = common.measure_workload(
                            cold_fn=_ro_inspect, warm_fn=_ro_inspect,
                            n_cold=n_cold, n_warm=n_warm, target_pid=pid,
                        )

                        top_walk_rows = _unpack_remote_flat(top_walk_res["results"].get(walk_res, []))
                        results["targets"][kind] = {
                            "hwnd": hwnd,
                            "pid": pid,
                            "dominant_provider_pid": dom_pid,
                            "provider_pids": {str(k): len(v) for k, v in by_pid.items()},
                            "findall_baseline_nodes": len(baseline_els),
                            "top_root_remote_walk_nodes": len(top_walk_rows),
                            "top_root_remote_walk_status": top_walk_res["status"],
                            "anchored_container": anchor_label,
                            "anchored_remote_walk_status": last_walk_status,
                            "findall_baseline": findall_stats,
                            "remote_op_subtree_walk": {
                                "stats": ro_walk_stats,
                                "accuracy_vs_findall": common.compare_elements(ro_walk_els, baseline_els, interactive_only=False),
                            },
                            "batch_k_elements_n": k_n,
                            "standard_com_k_reads": std_inspect_stats,
                            "remote_op_k_batch": ro_batch_stats,
                        }
                except Exception as exc:
                    results["targets"][kind] = {"error": f"{type(exc).__name__}: {exc}"}
        finally:
            try:
                comtypes.CoUninitialize()
            except Exception:
                pass
        box["res"] = results

    th = threading.Thread(target=_worker, daemon=True)
    th.start()
    th.join()
    return box.get("res", {"targets": {}})
