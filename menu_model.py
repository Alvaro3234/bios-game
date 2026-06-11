"""Runtime menu model: values, navigation cursor, submenu stack."""

import datetime

from menu_data import MENU
from theme import VISIBLE_ROWS

SELECTABLE_TYPES = {"option", "numeric", "datetime", "password", "submenu",
                    "action"}

# Free-text info fields whose value depends on the active CPU brand.
# Items in menu_data.py reference a key here via `dynamic: "cpu_brand:<key>"`.
CPU_BRAND_INFO = {
    "type":  {"intel": "Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz",
              "amd":   "AMD Ryzen(TM) 7 3700X 8-Core Processor"},
    "vmx":   {"intel": "Supported", "amd": "Supported"},
    "vtd":   {"intel": "Supported", "amd": "Supported"},
    "speed": {"intel": "3600 MHz", "amd": "3600 MHz"},
}

# Hardware sensor/info readouts referenced via `dynamic: "hw:<key>"`.
# Each entry is either a plain string, or a reactive dict resolved
# against the live values:  {"by": "<setting_id>", "map": {value: text},
# "default": text}.  Tickets override these per-machine (`hw_info` in the
# challenge dict) to plant diagnostic clues.
DEFAULT_HW_INFO = {
    "cpu_temp": "+47.0 C",
    "mb_temp": "+34.0 C",
    "cpu_fan_rpm": {"by": "cpu_fan_profile",
                    "map": {"Standard": "1280 RPM", "Silent": "830 RPM",
                            "Turbo": "2160 RPM", "Disabled": "N/A"},
                    "default": "1280 RPM"},
    "chassis_fan_rpm": {"by": "chassis_fan_profile",
                        "map": {"Standard": "940 RPM", "Silent": "620 RPM",
                                "Turbo": "1750 RPM", "Disabled": "N/A"},
                        "default": "940 RPM"},
    "vcore": {"by": "vcore_offset",
              "map": {"Auto": "+1.200 V", "-0.10V": "+1.104 V",
                      "-0.05V": "+1.152 V", "+0.00V": "+1.200 V",
                      "+0.05V": "+1.248 V", "+0.10V": "+1.296 V",
                      "+0.15V": "+1.344 V", "+0.20V": "+1.392 V"},
              "default": "+1.200 V"},
    "v33": "+3.312 V",
    "v5": "+5.080 V",
    "v12": "+12.192 V",
    "vbat": "+3.040 V",
    "dram_freq_now": {"by": "xmp",
                      "map": {"Disabled": "2666 MHz",
                              "Profile 1": "3200 MHz",
                              "Profile 2": "3600 MHz"},
                      "default": "2666 MHz"},
    "target_dram": {"by": "xmp",
                    "map": {"Disabled": "2133 MT/s (JEDEC)",
                            "Profile 1": "3200 MT/s 16-18-18-38 1.35V",
                            "Profile 2": "3600 MT/s 17-19-19-39 1.45V"},
                    "default": "2133 MT/s (JEDEC)"},
}


def iter_persistable(items=None):
    """Yield every option/numeric/password item (recursing into submenus)."""
    if items is None:
        items = [it for page in MENU for it in page["items"]]
    for it in items:
        if it["type"] in ("option", "numeric", "password"):
            yield it
        elif it["type"] == "submenu":
            yield from iter_persistable(it["items"])


class Level:
    """One level of the navigation stack (a page or an open submenu)."""

    def __init__(self, items, title):
        self.items = items
        self.title = title
        self.cursor = 0
        self.scroll = 0


class MenuModel:
    def __init__(self, cpu_brand="intel", home_items=None):
        """`home_items` replaces the tabbed pages with a single home menu
        (vendor-specific page grouping, e.g. Award's category grid). The
        item dicts must reference the shared menu_data items so values
        and ids stay common across vendors."""
        self.pages = MENU
        self.page_idx = 0
        self.cpu_brand = cpu_brand   # "intel" | "amd" -> drives label_variants
        self.home_items = home_items
        self.values = {}            # id -> value (str for option, int for numeric)
        self.hw_info = dict(DEFAULT_HW_INFO)
        self.time_offset = datetime.timedelta(0)
        self.dt_field = 0           # active sub-field of the date/time item
        if home_items is not None:
            self.stack = [Level(home_items, "home")]
        else:
            self.stack = [Level(self.pages[0]["items"],
                                self.pages[0]["title"])]
        self.load_defaults()
        self._snapshot = dict(self.values)   # for F2 "Previous Values"
        for level in self.stack:
            self._init_cursor(level)

    # ------------------------------------------------------------ values
    def load_defaults(self):
        for it in iter_persistable():
            if it["type"] == "option":
                self.values[it["id"]] = it["values"][it.get("default", 0)]
            elif it["type"] == "numeric":
                self.values[it["id"]] = it.get("default", it.get("min", 0))
            elif it["type"] == "password":
                self.values[it["id"]] = ""

    def apply_saved(self, saved):
        """Overlay persisted values; ignore unknown/invalid entries."""
        if isinstance(saved.get("_time_offset_s"), (int, float)):
            self.time_offset = datetime.timedelta(
                seconds=saved["_time_offset_s"])
        for it in iter_persistable():
            if it["id"] not in saved:
                continue
            v = saved[it["id"]]
            if it["type"] == "option" and v in it["values"]:
                self.values[it["id"]] = v
            elif it["type"] == "numeric" and isinstance(v, int) \
                    and it.get("min", 0) <= v <= it.get("max", 1 << 30):
                self.values[it["id"]] = v
            elif it["type"] == "password" and isinstance(v, str):
                self.values[it["id"]] = v

    def export_values(self):
        """Values plus CMOS clock offset, for persistence."""
        return dict(self.values,
                    _time_offset_s=self.time_offset.total_seconds())

    def set_hw_info(self, overrides):
        """Defaults plus the ticket's per-machine sensor overrides."""
        self.hw_info = dict(DEFAULT_HW_INFO)
        if overrides:
            self.hw_info.update(overrides)

    def snapshot(self):
        self._snapshot = dict(self.values)

    def restore_snapshot(self):
        self.values = dict(self._snapshot)

    def is_dirty(self):
        return self.values != self._snapshot

    # ------------------------------------------------------------ display
    def display_label(self, item):
        """Label resolved against cpu_brand via optional label_variants."""
        variants = item.get("label_variants")
        if variants:
            return variants.get(self.cpu_brand, item.get("label", ""))
        return item.get("label", "")

    def display_value(self, item):
        t = item["type"]
        if t == "info":
            dyn = item.get("dynamic")
            if dyn:
                if dyn.startswith("pwd_status:"):
                    pwd = self.values.get(dyn.split(":")[1], "")
                    return "Installed" if pwd else "Not Installed"
                if dyn.startswith("cpu_brand:"):
                    key = dyn.split(":", 1)[1]
                    return CPU_BRAND_INFO.get(key, {}).get(self.cpu_brand, "")
                if dyn.startswith("hw:"):
                    return self._resolve_hw(dyn.split(":", 1)[1])
                return ""
            variants = item.get("value_variants")
            if variants:
                return variants.get(self.cpu_brand, item.get("value", ""))
            return item.get("value", "")
        if t == "option":
            return "[%s]" % self.values[item["id"]]
        if t == "numeric":
            return "[%s]" % self.values[item["id"]]
        if t == "datetime":
            now = datetime.datetime.now() + self.time_offset
            if item["id"] == "sys_date":
                return now.strftime("[%a %m/%d/%Y]")
            return now.strftime("[%H:%M:%S]")
        return ""

    def _resolve_hw(self, key):
        entry = self.hw_info.get(key, "")
        if isinstance(entry, dict):
            cur = self.values.get(entry.get("by"))
            return entry.get("map", {}).get(cur, entry.get("default", ""))
        return entry

    # ------------------------------------------------------------ state
    def is_enabled(self, item):
        if item.get("disabled"):
            return False
        dep = item.get("depends_on")
        if dep:
            cur = self.values.get(dep[0])
            if isinstance(dep[1], (list, tuple)):
                return cur in dep[1]
            return cur == dep[1]
        return True

    def is_selectable(self, item):
        return item["type"] in SELECTABLE_TYPES and self.is_enabled(item)

    # ------------------------------------------------------------ nav
    @property
    def level(self):
        return self.stack[-1]

    @property
    def in_submenu(self):
        return len(self.stack) > 1

    def current_item(self):
        items = self.level.items
        if 0 <= self.level.cursor < len(items):
            it = items[self.level.cursor]
            if self.is_selectable(it):
                return it
        return None

    def _init_cursor(self, level):
        level.cursor = 0
        for i, it in enumerate(level.items):
            if self.is_selectable(it):
                level.cursor = i
                break
        self._clamp_scroll(level)

    def move(self, delta):
        level = self.level
        items = level.items
        n = len(items)
        i = level.cursor
        for _ in range(n):
            i = (i + delta) % n
            if self.is_selectable(items[i]):
                level.cursor = i
                break
        self.dt_field = 0
        self._clamp_scroll(level)

    def _clamp_scroll(self, level):
        if level.cursor < level.scroll:
            level.scroll = level.cursor
        elif level.cursor >= level.scroll + VISIBLE_ROWS:
            level.scroll = level.cursor - VISIBLE_ROWS + 1

    def switch_page(self, delta):
        if self.home_items is not None:
            # Home-menu mode has no pages; LEFT/RIGHT jump columns instead.
            if not self.in_submenu:
                self._jump_column()
            return
        self.page_idx = (self.page_idx + delta) % len(self.pages)
        page = self.pages[self.page_idx]
        self.stack = [Level(page["items"], page["title"])]
        self._init_cursor(self.level)

    def _jump_column(self):
        """Two-column home grid: move the cursor to the other column."""
        level = self.level
        n = len(level.items)
        half = (n + 1) // 2
        c = level.cursor
        target = c - half if c >= half else min(c + half, n - 1)
        if 0 <= target < n and self.is_selectable(level.items[target]):
            level.cursor = target
        self._clamp_scroll(level)

    def enter_submenu(self, item):
        self.stack.append(Level(item["items"], item["label"]))
        self._init_cursor(self.level)

    def leave_submenu(self):
        if self.in_submenu:
            self.stack.pop()
            return True
        return False

    # ------------------------------------------------------------ editing
    def change(self, item, delta):
        """+/- in-place value change."""
        t = item["type"]
        if t == "option":
            vals = item["values"]
            i = vals.index(self.values[item["id"]])
            self.values[item["id"]] = vals[(i + delta) % len(vals)]
        elif t == "numeric":
            lo, hi = item.get("min", 0), item.get("max", 1 << 30)
            self.values[item["id"]] = max(lo, min(hi, self.values[item["id"]] + delta))
        elif t == "datetime":
            self._adjust_datetime(item, delta)

    def set_option_index(self, item, index):
        self.values[item["id"]] = item["values"][index]

    def _adjust_datetime(self, item, delta):
        now = datetime.datetime.now()
        cur = now + self.time_offset
        f = self.dt_field % 3
        try:
            if item["id"] == "sys_date":
                if f == 0:
                    m = (cur.month - 1 + delta) % 12 + 1
                    new = cur.replace(month=m, day=min(cur.day, 28))
                elif f == 1:
                    new = cur + datetime.timedelta(days=delta)
                else:
                    new = cur.replace(year=max(1998, min(9999, cur.year + delta)))
            else:
                step = (3600, 60, 1)[f]
                new = cur + datetime.timedelta(seconds=step * delta)
        except ValueError:
            return
        self.time_offset = new - now
