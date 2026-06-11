"""EFI Shell session: command parser that drives a MenuModel.

Wraps a MenuModel and exposes a small set of EFI Shell-flavoured commands:

    help                          list commands
    ls [page]                     list pages, or items on a page
    getvar <id>                   read current value of an item
    setvar <id> <value...>        set an option/numeric/password value
    dmpstore                      dump every NVRAM variable
    bcfg boot dump                show boot1/boot2/boot3 priorities
    bcfg boot mv <a> <b>          swap two boot priorities (1-based)
    time [hh:mm:ss]               show or set the RTC time
    date [mm/dd/yyyy]             show or set the RTC date
    map / memmap / dh / ver       environment information
    echo <text>                   print text
    reset cold                    save and reboot
    exit                          discard changes and reboot

The values written via `setvar` go to `model.values`; on `reset cold` the
caller is expected to inspect `wants_reboot`, persist the state, then run
the normal reboot transition.
"""

import datetime

from menu_model import iter_persistable


def _all_items():
    return list(iter_persistable())


def _item_by_id(item_id):
    for it in _all_items():
        if it["id"] == item_id:
            return it
    return None


def _is_option(item):
    return item["type"] == "option"


def _is_numeric(item):
    return item["type"] == "numeric"


def _is_password(item):
    return item["type"] == "password"


def _join_values(values):
    return ", ".join("%r" % v for v in values)


class ShellSession:
    """Stateful command line wrapped around a MenuModel."""

    def __init__(self, model):
        self.model = model
        self.scrollback = []          # list of strings (rendered top-down)
        self.buffer = ""               # current input line
        self.history = []              # past commands (UP/DOWN)
        self.history_idx = None        # index while browsing history
        self.cursor_visible = True     # toggled by external blink timer
        self.wants_reboot = False      # set by `reset cold`
        self.discard_on_reboot = False # set by `exit`
        self.wants_quit = False        # set by ESC after confirmation
        self.print_welcome()

    # ------------------------------------------------------------ display
    def print_welcome(self):
        from vendors import efi
        for line in efi.WELCOME:
            self.scrollback.append(line)
        self.scrollback.append("")

    def println(self, line=""):
        if isinstance(line, str) and "\n" in line:
            for sub in line.split("\n"):
                self.scrollback.append(sub)
        else:
            self.scrollback.append(line)
        # Cap scrollback to avoid unbounded growth
        if len(self.scrollback) > 200:
            del self.scrollback[:50]

    # ------------------------------------------------------------ input
    def handle_char(self, ch):
        if ch and ch.isprintable() and len(self.buffer) < 80:
            self.buffer += ch

    def backspace(self):
        self.buffer = self.buffer[:-1]

    def history_prev(self):
        if not self.history:
            return
        if self.history_idx is None:
            self.history_idx = len(self.history) - 1
        elif self.history_idx > 0:
            self.history_idx -= 1
        self.buffer = self.history[self.history_idx]

    def history_next(self):
        if self.history_idx is None:
            return
        self.history_idx += 1
        if self.history_idx >= len(self.history):
            self.history_idx = None
            self.buffer = ""
        else:
            self.buffer = self.history[self.history_idx]

    def submit(self):
        """Echo the prompt, run the command, clear the buffer."""
        cmd = self.buffer.strip()
        self.println("Shell> " + self.buffer)
        self.buffer = ""
        self.history_idx = None
        if not cmd:
            return
        self.history.append(cmd)
        try:
            output = self.execute(cmd)
        except ValueError as e:
            output = ["Error: %s" % e]
        for line in output:
            self.println(line)
        self.println("")

    # ------------------------------------------------------------ commands
    def execute(self, cmd):
        """Parse and run one command. Returns a list of output lines."""
        # Tokenize, respecting one level of double-quoted strings.
        tokens = self._tokenize(cmd)
        if not tokens:
            return []
        op = tokens[0].lower()
        args = tokens[1:]

        if op == "help":
            return self._help()
        if op == "ls":
            return self._ls(args)
        if op == "getvar":
            return self._getvar(args)
        if op == "setvar":
            return self._setvar(args)
        if op == "dmpstore":
            return self._dmpstore()
        if op == "bcfg":
            return self._bcfg(args)
        if op == "time":
            return self._time(args)
        if op == "date":
            return self._date(args)
        if op == "map":
            return self._map()
        if op == "memmap":
            return self._memmap()
        if op == "dh":
            return self._dh()
        if op == "ver":
            return self._ver()
        if op == "echo":
            return [" ".join(args)]
        if op == "reset":
            return self._reset(args)
        if op == "exit":
            self.discard_on_reboot = True
            self.wants_reboot = True
            return ["Exiting shell. Discarding pending changes."]
        if op == "clear" or op == "cls":
            self.scrollback = []
            return []
        return ["Unknown command: %r. Type 'help' for a list." % op]

    @staticmethod
    def _tokenize(cmd):
        out, cur, in_q = [], "", False
        for ch in cmd:
            if ch == '"':
                in_q = not in_q
            elif ch == " " and not in_q:
                if cur:
                    out.append(cur)
                    cur = ""
            else:
                cur += ch
        if cur:
            out.append(cur)
        return out

    # ------------------------------------------------------------ help
    def _help(self):
        return [
            "Available commands:",
            "  help                       Display this list",
            "  ls [page]                  List pages, or items on a page",
            "  getvar <id>                Read the current value of <id>",
            "  setvar <id> <value...>     Write a new value to <id>",
            "  dmpstore                   Dump all NVRAM variables",
            "  bcfg boot dump             Show boot priorities",
            "  bcfg boot mv <a> <b>       Swap two boot priorities",
            "  time [hh:mm:ss]            Show or set the RTC time",
            "  date [mm/dd/yyyy]          Show or set the RTC date",
            "  map                        Show the device mapping table",
            "  memmap                     Show the UEFI memory map",
            "  dh                         Dump the handle database",
            "  ver                        Show shell and UEFI versions",
            "  echo <text>                Print text",
            "  reset cold                 Persist changes and reboot",
            "  exit                       Discard pending changes and quit",
            "  cls / clear                Clear the scrollback",
        ]

    # ------------------------------------------------------------ info
    def _ver(self):
        return [
            "UEFI Interactive Shell v2.2",
            "EDK II",
            "UEFI v2.70 (American Megatrends, 0x0005000B)",
        ]

    def _map(self):
        return [
            "Mapping table",
            "      FS0: Alias(s):HD0a65535a1:;BLK1:",
            "          PciRoot(0x0)/Pci(0x17,0x0)/Sata(0x0,0xFFFF,0x0)/"
            "HD(1,GPT,8E3D...)",
            "     BLK0: Alias(s):",
            "          PciRoot(0x0)/Pci(0x17,0x0)/Sata(0x0,0xFFFF,0x0)",
            "     BLK2: Alias(s):",
            "          PciRoot(0x0)/Pci(0x17,0x0)/Sata(0x1,0xFFFF,0x0)",
        ]

    def _memmap(self):
        return [
            "Type       Start            End              # Pages  Attributes",
            "Available  0000000000000000-000000000009FFFF 000000A0 000000000000000F",
            "BS_Data    00000000000A0000-00000000000FFFFF 00000060 0000000000000000",
            "Available  0000000000100000-00000000CFFFFFFF 000CFF00 000000000000000F",
            "Reserved   00000000D0000000-00000000FFFFFFFF 00030000 0000000000000001",
            "Available  0000000100000000-000000042FFFFFFF 00330000 000000000000000F",
            "",
            "  16,384 MB total memory detected",
        ]

    def _dh(self):
        return [
            "Handle dump",
            "  1: Image(DxeCore)",
            "  2: FirmwareVolume FirmwareVolumeBlock",
            "  3: DevicePath(PciRoot(0x0))",
            "  4: BlockIO DevicePath(..Sata(0x0,0xFFFF,0x0))",
            "  5: BlockIO DevicePath(..Sata(0x1,0xFFFF,0x0))",
            "  6: SimpleTextIn SimpleTextOut",
        ]

    def _dmpstore(self):
        out = []
        for it in _all_items():
            v = self.model.values.get(it["id"], "")
            tag = " [grayed]" if not self.model.is_enabled(it) else ""
            out.append("Variable NV+BS '%s' = %r%s" % (it["id"], v, tag))
        return out

    # ------------------------------------------------------------ clock
    def _time(self, args):
        now = datetime.datetime.now()
        cur = now + self.model.time_offset
        if not args:
            return [cur.strftime("%H:%M:%S")]
        try:
            parts = [int(p) for p in args[0].split(":")]
            h, m, s = (parts + [0, 0])[:3]
            new = cur.replace(hour=h, minute=m, second=s)
        except ValueError:
            return ["Invalid time. Use: time hh:mm:ss"]
        self.model.time_offset = new - now
        return ["Time: %s (RTC updated)" % new.strftime("%H:%M:%S")]

    def _date(self, args):
        now = datetime.datetime.now()
        cur = now + self.model.time_offset
        if not args:
            return [cur.strftime("%m/%d/%Y")]
        try:
            mth, day, yr = (int(p) for p in args[0].split("/"))
            if yr < 100:
                yr += 2000
            new = cur.replace(year=yr, month=mth, day=day)
        except ValueError:
            return ["Invalid date. Use: date mm/dd/yyyy"]
        self.model.time_offset = new - now
        return ["Date: %s (RTC updated)" % new.strftime("%m/%d/%Y")]

    # ------------------------------------------------------------ ls
    def _ls(self, args):
        if not args:
            out = ["Pages:"]
            for i, page in enumerate(self.model.pages):
                out.append("  %d  %s" % (i + 1, page["title"]))
            return out
        try:
            n = int(args[0]) - 1
        except ValueError:
            n = None
            for i, p in enumerate(self.model.pages):
                if p["title"].lower().startswith(args[0].lower()):
                    n = i
                    break
            if n is None:
                return ["No such page: %r" % args[0]]
        if n < 0 or n >= len(self.model.pages):
            return ["Page index out of range."]
        page = self.model.pages[n]
        out = ["Page %d: %s" % (n + 1, page["title"]), ""]
        for it in iter_persistable(page["items"]):
            tag = "[grayed]" if not self.model.is_enabled(it) else ""
            label = self.model.display_label(it)
            val = self.model.values.get(it["id"], "")
            out.append("  %-20s  %s  %s" % (it["id"], val, tag and (" " + tag) or ""))
            out[-1] += "" if not label else "   ; %s" % label
        return out

    # ------------------------------------------------------------ getvar/setvar
    def _getvar(self, args):
        if not args:
            return ["Usage: getvar <id>"]
        item = _item_by_id(args[0])
        if not item:
            return ["No such variable: %r" % args[0]]
        v = self.model.values.get(item["id"], "")
        return ["%s = %r" % (item["id"], v)]

    def _setvar(self, args):
        if len(args) < 2:
            return ["Usage: setvar <id> <value...>"]
        item = _item_by_id(args[0])
        if not item:
            return ["No such variable: %r" % args[0]]
        if not self.model.is_enabled(item):
            return ["Variable %r is currently disabled (grayed)." % args[0]]
        value = " ".join(args[1:])
        if _is_option(item):
            # Allow case-insensitive match and substring among allowed values.
            choices = item["values"]
            match = None
            for v in choices:
                if v.lower() == value.lower():
                    match = v
                    break
            if not match:
                for v in choices:
                    if value.lower() in v.lower():
                        match = v
                        break
            if not match:
                return ["Invalid value %r for %s. Valid: %s" %
                        (value, item["id"], _join_values(choices))]
            self.model.values[item["id"]] = match
            return ["%s := %r" % (item["id"], match)]
        if _is_numeric(item):
            try:
                n = int(value)
            except ValueError:
                return ["Numeric value expected for %s." % item["id"]]
            lo = item.get("min", 0)
            hi = item.get("max", 1 << 30)
            if not (lo <= n <= hi):
                return ["Out of range: %d (allowed %d..%d)." % (n, lo, hi)]
            self.model.values[item["id"]] = n
            return ["%s := %d" % (item["id"], n)]
        if _is_password(item):
            self.model.values[item["id"]] = value
            return ["%s := <set>" % item["id"]]
        return ["Cannot set %r from the shell." % item["id"]]

    # ------------------------------------------------------------ bcfg
    def _bcfg(self, args):
        if len(args) < 2 or args[0].lower() != "boot":
            return ["Usage: bcfg boot dump | bcfg boot mv <a> <b>"]
        sub = args[1].lower()
        if sub == "dump":
            out = ["Boot Options:"]
            for slot in ("boot1", "boot2", "boot3"):
                v = self.model.values.get(slot, "")
                out.append("  %s : %s" % (slot, v))
            return out
        if sub == "mv" and len(args) >= 4:
            try:
                a, b = int(args[2]), int(args[3])
            except ValueError:
                return ["Invalid indices."]
            if a not in (1, 2, 3) or b not in (1, 2, 3):
                return ["Indices must be 1, 2, or 3."]
            ka, kb = "boot%d" % a, "boot%d" % b
            va = self.model.values.get(ka, "")
            vb = self.model.values.get(kb, "")
            item_a = _item_by_id(ka)
            item_b = _item_by_id(kb)
            if not (item_a and item_b):
                return ["Boot slots unavailable on this machine."]
            # Make sure each slot allows the other's value
            if vb not in item_a["values"] or va not in item_b["values"]:
                return ["Refused: values incompatible across slots."]
            self.model.values[ka] = vb
            self.model.values[kb] = va
            return ["Swapped %s <-> %s" % (ka, kb)]
        return ["Unknown bcfg subcommand."]

    # ------------------------------------------------------------ reset
    def _reset(self, args):
        kind = args[0].lower() if args else ""
        if kind not in ("cold", "warm"):
            return ["Usage: reset cold"]
        self.wants_reboot = True
        return ["Rebooting in cold reset mode..."]
