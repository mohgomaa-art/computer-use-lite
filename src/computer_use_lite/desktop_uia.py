# SPDX-License-Identifier: Apache-2.0
"""M1-Windows - UI Automation scoped strictly to one HWND, on a worker thread.

Uses IUIAutomation.FindAllBuildCache (one cross-process cache request) so the whole
tree costs a single round trip per snapshot. Never touches the Desktop Root.
"""
import ctypes
import hashlib
import threading
import time
import warnings
from ctypes import wintypes

import comtypes
import comtypes.client

_u32 = ctypes.WinDLL("user32", use_last_error=True)
if not _u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
    _u32.SetProcessDPIAware()

try:
    comtypes.client.GetModule("UIAutomationCore.dll")
    from comtypes.gen import UIAutomationClient as UIA
except Exception:  # pragma: no cover - fallback keeps the module importable
    UIA = None

_TYPE_NAMES = (
    {getattr(UIA, n): n[len("UIA_"):-len("ControlTypeId")]
     for n in dir(UIA) if n.startswith("UIA_") and n.endswith("ControlTypeId")}
    if UIA is not None else {}
)

WANTED = {
    "ButtonControl": "button", "MenuItemControl": "menuitem", "TabItemControl": "tab",
    "SplitButtonControl": "button", "HyperlinkControl": "link", "EditControl": "textbox",
    "DocumentControl": "textbox", "ComboBoxControl": "combobox", "CheckBoxControl": "checkbox",
    "RadioButtonControl": "radio", "ListItemControl": "listitem", "TreeItemControl": "treeitem",
    "TextControl": "text", "ToolBarControl": "toolbar", "MenuBarControl": "menubar",
}
INTERACTIVE = {
    "button", "menuitem", "tab", "link", "textbox", "combobox",
    "checkbox", "radio", "switch", "clickable", "listitem", "treeitem",
}

MOUSEEVENTF_MOVE, MOUSEEVENTF_ABSOLUTE, MOUSEEVENTF_VIRTUALDESK = 0x0001, 0x8000, 0x4000
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
KEYEVENTF_UNICODE, KEYEVENTF_KEYUP = 0x0004, 0x0002
SW_RESTORE = 9
WM_GETOBJECT = 0x003D
OBJID_CLIENT = -4
SMTO_ABORTIFHUNG = 0x0002
SPI_GETSCREENREADER = 0x0046
SPI_SETSCREENREADER = 0x0047
SPIF_SENDCHANGE = 0x0002
ULONG_PTR = wintypes.WPARAM


class _MI(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _KI(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _UN(ctypes.Union):
    _fields_ = [("mi", _MI), ("ki", _KI)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _UN)]


_u32.GetForegroundWindow.argtypes = []
_u32.GetForegroundWindow.restype = wintypes.HWND
_u32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_u32.ShowWindow.restype = wintypes.BOOL
_u32.SetForegroundWindow.argtypes = [wintypes.HWND]
_u32.SetForegroundWindow.restype = wintypes.BOOL
_u32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int]
_u32.SendInput.restype = wintypes.UINT
_u32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
_u32.GetCursorPos.restype = wintypes.BOOL
_u32.GetSystemMetrics.argtypes = [ctypes.c_int]
_u32.GetSystemMetrics.restype = ctypes.c_int
_u32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_u32.GetClassNameW.restype = ctypes.c_int
_u32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_u32.GetWindowTextLengthW.restype = ctypes.c_int
_u32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_u32.GetWindowTextW.restype = ctypes.c_int
_u32.SendMessageTimeoutW.argtypes = [
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
    wintypes.UINT, wintypes.UINT, ctypes.POINTER(wintypes.DWORD),
]
_u32.SendMessageTimeoutW.restype = ctypes.c_ssize_t
_u32.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
_u32.SystemParametersInfoW.restype = wintypes.BOOL
_u32.EnumChildWindows.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.LPARAM]
_u32.EnumChildWindows.restype = wintypes.BOOL


def cursor_pos():
    pt = wintypes.POINT()
    if not _u32.GetCursorPos(ctypes.byref(pt)):
        raise OSError(f"GetCursorPos failed: {ctypes.get_last_error()}")
    return (pt.x, pt.y)


class KillSwitch:
    """Abort if human moves physical cursor > tolerance px away from last commanded position."""

    def __init__(self, enabled=True, tolerance=5):
        self.enabled = enabled
        self.tolerance = tolerance
        self.armed = False
        self.last = None

    def pre_move(self):
        if not self.enabled or not self.armed:
            return
        pos = cursor_pos()
        if self.last and (abs(pos[0] - self.last[0]) > self.tolerance
                          or abs(pos[1] - self.last[1]) > self.tolerance):
            raise RuntimeError(f"HUMAN TAKEOVER: cursor at {pos}, last commanded {self.last}")

    def moved(self, xy):
        self.armed = True
        self.last = tuple(xy)


def _ensure_foreground(hwnd):
    if not hwnd:
        return
    fg = _u32.GetForegroundWindow()
    if fg == hwnd:
        return
    _u32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)
    _u32.SetForegroundWindow(wintypes.HWND(hwnd))
    time.sleep(0.05)
    fg = _u32.GetForegroundWindow()
    if fg != hwnd:
        raise RuntimeError(f"Foreground safety abort: expected hwnd={hwnd}, active foreground={fg}")


def _send_mouse(nx, ny, flags):
    inp = _INPUT(0, _UN(mi=_MI(nx, ny, 0, flags, 0, 0)))
    sent = _u32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))
    if sent != 1:
        raise OSError(f"SendInput failed: {ctypes.get_last_error()}")
    return sent


def _abs_coords(x, y):
    vx, vy = _u32.GetSystemMetrics(76), _u32.GetSystemMetrics(77)
    vw, vh = _u32.GetSystemMetrics(78), _u32.GetSystemMetrics(79)
    nx = int(round((x - vx) * 65535 / max(vw - 1, 1)))
    ny = int(round((y - vy) * 65535 / max(vh - 1, 1)))
    return nx, ny


def move_mouse(x, y, hwnd=None, kill_switch=None):
    if hwnd is not None:
        _ensure_foreground(hwnd)
    if kill_switch is not None:
        if not kill_switch.armed:
            try:
                kill_switch.moved(cursor_pos())
            except OSError:
                pass
        kill_switch.pre_move()
    nx, ny = _abs_coords(x, y)
    sent = _send_mouse(nx, ny, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK)
    if kill_switch is not None:
        kill_switch.moved((x, y))
    return sent


def click_at(x, y, hwnd=None, kill_switch=None):
    move_mouse(x, y, hwnd=hwnd, kill_switch=kill_switch)
    nx, ny = _abs_coords(x, y)
    arr = (_INPUT * 2)(
        _INPUT(0, _UN(mi=_MI(nx, ny, 0, MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK, 0, 0))),
        _INPUT(0, _UN(mi=_MI(nx, ny, 0, MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK, 0, 0))),
    )
    sent = _u32.SendInput(2, arr, ctypes.sizeof(_INPUT))
    if sent != 2:
        raise OSError(f"SendInput click failed: {ctypes.get_last_error()}")
    return "sendinput_click"


VK_CONTROL, VK_A, VK_DELETE = 0x11, 0x41, 0x2E


def type_unicode(text, hwnd=None, kill_switch=None):
    """Real keystrokes via SendInput KEYEVENTF_UNICODE."""
    if hwnd is not None:
        _ensure_foreground(hwnd)
    if kill_switch is not None:
        kill_switch.pre_move()
    for ch in str(text):
        for flags in (KEYEVENTF_UNICODE, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP):
            inp = _INPUT(1, _UN(ki=_KI(0, ord(ch), flags, 0, 0)))
            sent = _u32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))
            if sent != 1:
                raise OSError(f"SendInput key failed: {ctypes.get_last_error()}")


def _key(vk, up=False):
    inp = _INPUT(1, _UN(ki=_KI(vk, 0, KEYEVENTF_KEYUP if up else 0, 0, 0)))
    sent = _u32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))
    if sent != 1:
        raise OSError(f"SendInput vk failed: {ctypes.get_last_error()}")
    return sent


def press(vk, mods=(), hwnd=None):
    if hwnd is not None:
        _ensure_foreground(hwnd)
    for m in mods:
        _key(m)
    _key(vk)
    _key(vk, up=True)
    for m in reversed(mods):
        _key(m, up=True)


def _window_title(hwnd):
    n = _u32.GetWindowTextLengthW(wintypes.HWND(hwnd))
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    _u32.GetWindowTextW(wintypes.HWND(hwnd), buf, n + 1)
    return buf.value


def _window_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    _u32.GetClassNameW(wintypes.HWND(hwnd), buf, 256)
    return buf.value


def _activate_accessibility(hwnd):
    """Nudge Chromium/Electron accessibility via WM_GETOBJECT and temporary SPI_SETSCREENREADER."""
    targets = [hwnd]

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(child, _):
        targets.append(child)
        return True

    _u32.EnumChildWindows(wintypes.HWND(hwnd), cb, 0)
    res = wintypes.DWORD()
    for t in targets[:32]:
        _u32.SendMessageTimeoutW(wintypes.HWND(t), WM_GETOBJECT, 0, OBJID_CLIENT,
                                 SMTO_ABORTIFHUNG, 300, ctypes.byref(res))
    time.sleep(0.25)


def _pulse_screenreader(hwnd):
    orig = ctypes.c_bool(False)
    _u32.SystemParametersInfoW(SPI_GETSCREENREADER, 0, ctypes.byref(orig), 0)
    if orig.value:
        _activate_accessibility(hwnd)
        return
    try:
        _u32.SystemParametersInfoW(SPI_SETSCREENREADER, 1, None, SPIF_SENDCHANGE)
        _activate_accessibility(hwnd)
    finally:
        _u32.SystemParametersInfoW(SPI_SETSCREENREADER, 0, None, SPIF_SENDCHANGE)


class DesktopSession:
    """UIA session bound to one window; all COM calls run on a single worker thread."""

    name = "desktop"

    def __init__(self, hwnd):
        self.hwnd = hwnd
        self._q = []
        self._cv = threading.Condition()
        self._uia = None
        self._cache = None
        self._err = None
        self._dead = False
        self._init_done = threading.Event()
        self._kill = KillSwitch(enabled=True, tolerance=5)
        self.revision = 0
        self._last = {}
        self._a11y_tried = False
        self.last_warning = None

        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        if not self._init_done.wait(timeout=5.0):
            raise TimeoutError("UIA worker failed to initialize within 5 s")
        if self._err is not None:
            raise self._err

    # -- worker plumbing --------------------------------------------------------
    def _worker(self):
        try:
            comtypes.CoInitialize()
            self._init_uia()
        except Exception as exc:
            self._err = exc
            self._dead = True
            self._init_done.set()
            return
        self._init_done.set()
        while True:
            with self._cv:
                while not self._q:
                    self._cv.wait()
                fn = self._q.pop(0)
            try:
                fn()
            except Exception as exc:
                self._err = exc
                self._dead = True
                return

    def _call(self, fn):
        if self._dead or self._err is not None:
            raise self._err or RuntimeError("UIA worker terminated")
        done = threading.Event()
        box = {}

        def run():
            try:
                box["value"] = fn()
            except Exception as exc:
                box["error"] = exc
            finally:
                done.set()

        with self._cv:
            self._q.append(run)
            self._cv.notify()
        if not done.wait(20):
            raise self._err or TimeoutError("UIA worker did not answer in 20 s")
        if "error" in box:
            raise box["error"]
        return box.get("value")

    def _init_uia(self):
        if UIA is None:
            raise RuntimeError("UIAutomationClient typelib unavailable")
        self._uia = comtypes.client.CreateObject(UIA.CUIAutomation, interface=UIA.IUIAutomation)
        cr = self._uia.CreateCacheRequest()
        for pid in (
            UIA.UIA_NamePropertyId, UIA.UIA_ControlTypePropertyId,
            UIA.UIA_AutomationIdPropertyId, UIA.UIA_BoundingRectanglePropertyId,
            UIA.UIA_IsEnabledPropertyId, UIA.UIA_IsOffscreenPropertyId,
            UIA.UIA_RuntimeIdPropertyId, UIA.UIA_IsPasswordPropertyId,
            UIA.UIA_HasKeyboardFocusPropertyId,
            UIA.UIA_IsInvokePatternAvailablePropertyId,
            UIA.UIA_IsValuePatternAvailablePropertyId,
            UIA.UIA_IsSelectionItemPatternAvailablePropertyId,
            UIA.UIA_IsTogglePatternAvailablePropertyId,
            UIA.UIA_IsExpandCollapsePatternAvailablePropertyId,
            UIA.UIA_IsTextPatternAvailablePropertyId,
        ):
            cr.AddProperty(pid)
        for pat in (
            UIA.UIA_InvokePatternId, UIA.UIA_ValuePatternId,
            UIA.UIA_SelectionItemPatternId, UIA.UIA_TogglePatternId,
            UIA.UIA_ExpandCollapsePatternId, UIA.UIA_TextPatternId,
        ):
            cr.AddPattern(pat)
        self._cache = cr

    # -- geometry ---------------------------------------------------------------
    def bounds(self):
        from . import snapshot
        return snapshot.window(self.hwnd, bump=False)["bounds"]

    # -- discovery --------------------------------------------------------------
    def _scan(self):
        root = self._uia.ElementFromHandle(self.hwnd)
        found = root.FindAllBuildCache(UIA.TreeScope_Subtree,
                                       self._uia.CreateTrueCondition(), self._cache)
        out = []
        for i in range(found.Length):
            el = found.GetElement(i)
            ctype = _TYPE_NAMES.get(el.CachedControlType, "Unknown")
            role = WANTED.get(ctype + "Control", "")
            r = el.CachedBoundingRectangle
            box = [int(r.left), int(r.top), int(r.right) - int(r.left), int(r.bottom) - int(r.top)]
            patterns = []
            for pname, pid in (
                ("invoke", UIA.UIA_IsInvokePatternAvailablePropertyId),
                ("value", UIA.UIA_IsValuePatternAvailablePropertyId),
                ("selection", UIA.UIA_IsSelectionItemPatternAvailablePropertyId),
                ("toggle", UIA.UIA_IsTogglePatternAvailablePropertyId),
                ("expand_collapse", UIA.UIA_IsExpandCollapsePatternAvailablePropertyId),
            ):
                if el.GetCachedPropertyValue(pid):
                    patterns.append(pname)
            raw_rid = el.GetCachedPropertyValue(UIA.UIA_RuntimeIdPropertyId)
            rid = list(raw_rid) if raw_rid else list(el.GetRuntimeId())
            out.append({
                "source": "uia",
                "role": role or ctype,
                "ctype": ctype,
                "name": (el.CachedName or "")[:80],
                "automation_id": el.CachedAutomationId or "",
                "box": box,
                "enabled": bool(el.CachedIsEnabled),
                "offscreen": bool(el.CachedIsOffscreen),
                "is_password": bool(el.CachedIsPassword),
                "patterns": patterns,
                "runtime_id": rid,
                "_element": el,
                "ref": {"kind": "uia", "runtime_id": rid},
            })
        return out

    def discover(self):
        nodes = self._call(self._scan)
        has_doc = any(n["ctype"] == "Document" for n in nodes)
        inter_n = sum(1 for n in nodes if n["role"] in INTERACTIVE)
        cls = _window_class(self.hwnd)
        is_chromium = cls.startswith("Chrome_WidgetWin")
        if not self._a11y_tried and ((is_chromium and not has_doc) or inter_n < 6):
            self._a11y_tried = True
            _activate_accessibility(self.hwnd)
            nodes2 = self._call(self._scan)
            if len(nodes2) <= len(nodes) and is_chromium and not has_doc:
                _pulse_screenreader(self.hwnd)
                nodes2 = self._call(self._scan)
            nodes = nodes2
            inter_n = sum(1 for n in nodes if n["role"] in INTERACTIVE)
        if inter_n < 6:
            self.last_warning = (
                f"UIA returned suspiciously few interactive nodes ({inter_n} interactive / {len(nodes)} total); "
                "Chromium/Electron windows may need --force-renderer-accessibility"
            )
            warnings.warn(self.last_warning)
        else:
            self.last_warning = None

        self._last = {tuple(n["runtime_id"]): n for n in nodes}
        return [{k: v for k, v in n.items() if k != "_element"} for n in nodes]

    # -- actions ---------------------------------------------------------------
    def _element(self, el):
        key = tuple(el["ref"]["runtime_id"])
        node = self._last.get(key)
        if node is None:
            raise LookupError("element not in the last cached snapshot")
        return node["_element"]

    def perform(self, el, action, value=None):
        def run():
            e = self._element(el)
            if action == "type":
                try:
                    self._pattern(e, UIA.UIA_ValuePatternId,
                                  UIA.IUIAutomationValuePattern).SetValue(str(value or ""))
                    return "value_pattern"
                except Exception:
                    _ensure_foreground(self.hwnd)
                    e.SetFocus()
                    type_unicode(value or "", hwnd=self.hwnd, kill_switch=self._kill)
                    return "sendinput"
            if action in ("click", "invoke"):
                for pat_id, iface, label in (
                    (UIA.UIA_InvokePatternId, UIA.IUIAutomationInvokePattern, "invoke_pattern"),
                    (UIA.UIA_TogglePatternId, UIA.IUIAutomationTogglePattern, "toggle_pattern"),
                    (UIA.UIA_SelectionItemPatternId, UIA.IUIAutomationSelectionItemPattern, "selection_item_pattern"),
                ):
                    try:
                        p = self._pattern(e, pat_id, iface)
                        if label == "invoke_pattern":
                            p.Invoke()
                        elif label == "toggle_pattern":
                            p.Toggle()
                        else:
                            p.Select()
                        return label
                    except Exception:
                        pass
                try:
                    ec = self._pattern(e, UIA.UIA_ExpandCollapsePatternId, UIA.IUIAutomationExpandCollapsePattern)
                    state = ec.CurrentExpandCollapseState
                    if state in (0, 2):  # Collapsed or PartiallyExpanded
                        ec.Expand()
                        return "expand_collapse_pattern"
                    if state == 1:  # Expanded
                        ec.Collapse()
                        return "expand_collapse_pattern"
                except Exception:
                    pass
                x, y, w, h = el["box"]
                return click_at(int(x + w / 2), int(y + h / 2), hwnd=self.hwnd,
                                kill_switch=getattr(self, "_kill", None))
            if action == "hover":
                x, y, w, h = el["box"]
                move_mouse(int(x + w / 2), int(y + h / 2), hwnd=self.hwnd,
                           kill_switch=getattr(self, "_kill", None))
                return "hover"
            e.SetFocus()
            return "focus"

        return {"mechanism": self._call(run)}

    def hover(self, el):
        x, y, w, h = el["box"]
        cx, cy = int(x + w / 2), int(y + h / 2)
        move_mouse(cx, cy, hwnd=self.hwnd, kill_switch=getattr(self, "_kill", None))
        return {"x": cx, "y": cy}

    def clear(self, el):
        def run():
            e = self._element(el)
            try:
                self._pattern(e, UIA.UIA_ValuePatternId,
                              UIA.IUIAutomationValuePattern).SetValue("")
                return "value_pattern_clear"
            except Exception:
                _ensure_foreground(self.hwnd)
                e.SetFocus()
                press(VK_A, (VK_CONTROL,), hwnd=self.hwnd)
                press(VK_DELETE, hwnd=self.hwnd)
                return "ctrl+a, delete"
        return self._call(run)

    def _pattern(self, element, pid, iface):
        """GetCurrentPattern returns IUnknown; cast it to the real pattern interface."""
        return element.GetCurrentPattern(pid).QueryInterface(iface)

    def _safe_element_value(self, e):
        try:
            if e.CurrentIsPassword:
                return "[REDACTED]"
        except Exception:
            pass
        try:
            return self._pattern(e, UIA.UIA_ValuePatternId,
                                 UIA.IUIAutomationValuePattern).CurrentValue[:400]
        except Exception:
            pass
        try:
            return self._pattern(e, UIA.UIA_TextPatternId,
                                 UIA.IUIAutomationTextPattern).DocumentRange.GetText(-1)[:400]
        except Exception:
            return None

    def read_value(self, el):
        if el.get("is_password"):
            return "[REDACTED]"
        def run():
            return self._safe_element_value(self._element(el))
        return self._call(run)

    def signature(self, target=None):
        """Lightweight O(1) signature without running a full UIA tree scan."""
        def run():
            focus_fp = ""
            try:
                foc = self._uia.GetFocusedElement()
                if foc:
                    f_name = (foc.CurrentName or "")[:40]
                    f_type = _TYPE_NAMES.get(foc.CurrentControlType, "")
                    f_val = self._safe_element_value(foc) or ""
                    if f_val == "[REDACTED]":
                        focus_fp = f"{f_type}:{f_name}:[REDACTED]"
                    else:
                        vh = hashlib.sha256(f_val.encode("utf-8")).hexdigest()[:12] if f_val else ""
                        focus_fp = f"{f_type}:{f_name}:len={len(f_val)}:h={vh}"
            except Exception:
                pass
            tgt_fp = ""
            if target is not None:
                try:
                    te = self._element(target)
                    tv = self._safe_element_value(te) or ""
                    if tv == "[REDACTED]":
                        tgt_fp = "[REDACTED]"
                    else:
                        th = hashlib.sha256(tv.encode("utf-8")).hexdigest()[:12] if tv else ""
                        tgt_fp = f"len={len(tv)}:h={th}"
                except Exception:
                    pass
            return {
                "title": _window_title(self.hwnd),
                "focus": focus_fp,
                "target_value": tgt_fp,
                "n": len(self._last),
                "text": "",
            }
        return self._call(run)

    def close(self):
        pass


def find_by_pid(pid, timeout=15.0):
    """Top-level visible window owned by pid."""
    deadline = time.time() + timeout

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if not _u32.IsWindowVisible(hwnd):
            return True
        owner = wintypes.DWORD()
        _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and _u32.GetWindowTextLengthW(hwnd):
            found.append(hwnd)
            return False
        return True

    while time.time() < deadline:
        found = []
        _u32.EnumWindows(cb, 0)
        if found:
            return found[0]
        time.sleep(0.3)
    return None
