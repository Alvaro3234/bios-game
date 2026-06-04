"""Procedural ticket generator for Shift mode.

A "shift" is a list of N challenge dicts (same schema as `challenges.py`)
built from a curated set of sabotage templates. Generation is deterministic
given a seed.

Compatibility:
- vendor_id is selected from the template's `vendors` list
- cpu_brand from `cpu_brands`
- EFI shell can only mutate option/numeric/password (no datetime),
  so EFI-compatible templates avoid clock sabotage

Output dicts pass `validate_challenges` exactly like hand-written ones.
"""

import random

from challenges import WINDOWS_SSD, USB_DRIVE, NIC_IPV4, RST_MODE


# --- Briefing fragments by symptom area ---------------------------------

_TICKETS_PREFIX = ["TICKET #%(num)d - %(summary)s"]
_FLAVORS_BOOT = [
    "Reception PC stuck at 'No bootable media'.",
    "Open-floor workstation reboots into a network boot loop.",
    "Engineering bench machine refuses to find its OS drive.",
]
_FLAVORS_VIRT = [
    "Devops sandbox can't start its VM lab. Hypervisor returns 'CPU does not support virtualization'.",
    "Training rig fails to enable nested virtualization for student labs.",
]
_FLAVORS_AUDIO = [
    "Conference room PC: speakers report 'No output device' in Windows.",
    "Editor workstation: DAW lost its onboard audio after a firmware flash.",
]
_FLAVORS_USB = [
    "DOS-era diagnostic tool can't see the USB keyboard during early boot.",
    "Service workstation lost POST keyboard input after the last update.",
]
_FLAVORS_STORAGE = [
    "Windows install reports INACCESSIBLE_BOOT_DEVICE on this rebuilt box.",
    "Linux installer can't find SATA disks on this freshly-shipped chassis.",
]
_FLAVORS_NET = [
    "Network deployment fails to PXE-load the OS image during overnight rollout.",
    "Branch office desktop can't pull its Wake-on-LAN patch schedule.",
]


def _ticket_num(rng):
    return rng.randint(5000, 9999)


def _fail_lines_boot():
    return ["Reboot and Select proper Boot device",
            "or Insert Boot Media in selected Boot device",
            "and press a key"]


def _fail_lines_secureboot():
    return ["Secure Boot Violation",
            "",
            "Invalid signature detected. Check Secure Boot Policy",
            "in Setup."]


def _fail_lines_vmx():
    return ["hypervisor-init.sh",
            "  CPU virtualization extensions : MISSING",
            "  Reason: VMX / SVM disabled in firmware."]


def _fail_lines_storage():
    return ["INACCESSIBLE_BOOT_DEVICE",
            "Storage stack failed to enumerate during boot."]


# --- Sabotage templates --------------------------------------------------

SABOTAGE_TEMPLATES = [
    {
        "id": "tpl_boot_misorder",
        "vendors": ["ami", "award", "efi"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 1,
        "flavors": _FLAVORS_BOOT,
        "sabotage_fn": lambda r: {"boot1": r.choice([NIC_IPV4, USB_DRIVE])},
        "goal_fn":     lambda r: {"boot1": WINDOWS_SSD},
        "fail_style":  "black",
        "fail_lines":  _fail_lines_boot(),
        "success":     ["Windows Boot Manager",
                        "  Loading kernel...",
                        "  Booting Windows..."],
    },
    {
        "id": "tpl_vmx_off",
        "vendors": ["ami", "award", "efi"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 1,
        "flavors": _FLAVORS_VIRT,
        "sabotage_fn": lambda r: {"vmx": "Disabled"},
        "goal_fn":     lambda r: {"vmx": "Enabled"},
        "fail_style":  "black",
        "fail_lines":  _fail_lines_vmx(),
        "success":     ["KVM module loaded.",
                        "Hypervisor sandbox accepting jobs."],
    },
    {
        "id": "tpl_audio_off",
        "vendors": ["ami", "award"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 1,
        "flavors": _FLAVORS_AUDIO,
        "sabotage_fn": lambda r: {"hd_audio": "Disabled"},
        "goal_fn":     lambda r: {"hd_audio": "Enabled"},
        "fail_style":  "black",
        "fail_lines":  ["AudioEndpointService: no output device found."],
        "success":     ["Default Audio Device: Realtek HD Audio (Speakers)",
                        "Output OK."],
    },
    {
        "id": "tpl_legacy_usb_off",
        "vendors": ["ami", "award"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 1,
        "flavors": _FLAVORS_USB,
        "sabotage_fn": lambda r: {"legacy_usb": "Disabled"},
        "goal_fn":     lambda r: {"legacy_usb": "Enabled"},
        "fail_style":  "black",
        "fail_lines":  ["DOS diagnostic: USB keyboard not detected.",
                        "Boot aborted."],
        "success":     ["DOS diagnostic loaded. Keyboard responsive."],
    },
    {
        "id": "tpl_sata_mode",
        "vendors": ["ami", "efi"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 2,
        "flavors": _FLAVORS_STORAGE,
        "sabotage_fn": lambda r: {"sata_mode": RST_MODE},
        "goal_fn":     lambda r: {"sata_mode": "AHCI"},
        "fail_style":  "bsod",
        "fail_lines":  _fail_lines_storage(),
        "success":     ["Windows: storage controller AHCI. Disks OK."],
    },
    {
        "id": "tpl_secure_boot_blocks_usb",
        "vendors": ["ami"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 2,
        "flavors": ["Signed recovery USB rejected at boot."],
        "sabotage_fn": lambda r: {"secure_boot": "Enabled",
                                  "boot1": WINDOWS_SSD,
                                  "boot2": USB_DRIVE},
        "goal_fn":     lambda r: {"secure_boot": "Disabled",
                                  "boot1": USB_DRIVE},
        "fail_style":  "secureboot",
        "fail_lines":  _fail_lines_secureboot(),
        "success":     ["Recovery USB diagnostic v3.2",
                        "  Image signature : OK"],
    },
    {
        "id": "tpl_pxe_chain",
        "vendors": ["ami", "efi"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 3,
        "flavors": _FLAVORS_NET,
        "sabotage_fn": lambda r: {"net_stack": "Disabled",
                                  "pxe4": "Disabled",
                                  "boot1": WINDOWS_SSD},
        "goal_fn":     lambda r: {"net_stack": "Enabled",
                                  "pxe4": "Enabled",
                                  "boot1": NIC_IPV4},
        "fail_style":  "black",
        "fail_lines":  ["PXE-E61: Media test failure, check cable",
                        "PXE-M0F: Exiting Intel Boot Agent"],
        "success":     ["PXE-MOF: Loading boot image...",
                        "Image transfer complete."],
    },
    {
        "id": "tpl_perf_speedstep",
        "vendors": ["ami", "award", "efi"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 2,
        "flavors": ["CPU benchmark suite reports half the expected MIPS."],
        "sabotage_fn": lambda r: {"speedstep": "Disabled",
                                  "turbo": "Disabled"},
        "goal_fn":     lambda r: {"speedstep": "Enabled",
                                  "turbo": "Enabled"},
        "fail_style":  "black",
        "fail_lines":  ["benchmark.exe: CPU frequency capped.",
                        "  SpeedStep : DISABLED"],
        "success":     ["benchmark.exe: scores within expected range."],
    },
    {
        "id": "tpl_wake_on_lan",
        "vendors": ["ami", "efi"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 2,
        "flavors": ["Patch deployment server can't wake this client."],
        "sabotage_fn": lambda r: {"pch_lan": "Disabled",
                                  "wake_on_lan": "Disabled"},
        "goal_fn":     lambda r: {"pch_lan": "Enabled",
                                  "wake_on_lan": "Enabled"},
        "fail_style":  "black",
        "fail_lines":  ["wol-probe: target did not respond to magic packet."],
        "success":     ["wol-probe: target responded. Patch session opened."],
    },
    {
        "id": "tpl_tpm_off",
        "vendors": ["ami"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 2,
        "flavors": ["Win11 upgrade refuses to start: TPM not detected."],
        "sabotage_fn": lambda r: {"tpm_enable": "Disable"},
        "goal_fn":     lambda r: {"tpm_enable": "Enable"},
        "fail_style":  "black",
        "fail_lines":  ["WindowsSetup: PC does not meet TPM 2.0 requirement."],
        "success":     ["WindowsSetup: requirements met. Continuing install."],
    },
    {
        "id": "tpl_above_4g",
        "vendors": ["ami", "efi"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 2,
        "flavors": ["GPU passthrough fails on this workstation."],
        "sabotage_fn": lambda r: {"vtd": "Disabled", "above_4g": "Disabled"},
        "goal_fn":     lambda r: {"vtd": "Enabled", "above_4g": "Enabled"},
        "fail_style":  "black",
        "fail_lines":  ["vfio-pci: IOMMU disabled. Aborting bind."],
        "success":     ["vfio-pci: device bound. VM ready."],
    },
    {
        "id": "tpl_igpu_off",
        "vendors": ["ami", "award"],
        "cpu_brands": ["intel"],
        "difficulty": 1,
        "flavors": ["Multi-monitor setup: second display is dead."],
        "sabotage_fn": lambda r: {"igfx": "Disabled"},
        "goal_fn":     lambda r: {"igfx": "Enabled"},
        "fail_style":  "black",
        "fail_lines":  ["Display manager: only 1 GPU detected."],
        "success":     ["Display manager: 2 GPUs detected. Extended OK."],
    },
    {
        "id": "tpl_xhci_off",
        "vendors": ["ami"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 1,
        "flavors": ["USB 3.0 ports dead after firmware update."],
        "sabotage_fn": lambda r: {"xhci_handoff": "Disabled"},
        "goal_fn":     lambda r: {"xhci_handoff": "Enabled"},
        "fail_style":  "black",
        "fail_lines":  ["Host: XHCI controller did not respond at boot."],
        "success":     ["Host: USB 3.0 devices enumerated."],
    },
    {
        "id": "tpl_hotplug_off",
        "vendors": ["ami"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 2,
        "flavors": ["Hot-swap bay forces reboots."],
        "sabotage_fn": lambda r: {"sata_p1_hotplug": "Disabled"},
        "goal_fn":     lambda r: {"sata_p1_hotplug": "Enabled"},
        "fail_style":  "black",
        "fail_lines":  ["Disk swap detected. Reboot required."],
        "success":     ["Disk swap detected. Hot-swap OK."],
    },
    {
        "id": "tpl_admin_pwd_unset",
        "vendors": ["ami"],
        "cpu_brands": ["intel", "amd"],
        "difficulty": 1,
        "flavors": ["Security audit flagged 'no setup password' on this PC."],
        "sabotage_fn": lambda r: {"admin_pwd": ""},
        "goal_fn":     lambda r: {"admin_pwd": "__nonempty__"},
        "fail_style":  "black",
        "fail_lines":  ["compliance-check: setup password = NOT SET. FAIL."],
        "success":     ["compliance-check: setup password = SET. PASS."],
    },
]


# --- Generator ----------------------------------------------------------

def _make_briefing(rng, summary, flavor):
    num = _ticket_num(rng)
    title = "Generated #%d" % num
    return title, [
        "TICKET #%d - %s" % (num, summary),
        "",
        flavor,
        "",
        "The user filed the ticket without a clear repro. You'll need",
        "to find the BIOS knob that brings the machine back.",
    ]


def generate_ticket(rng, vendor_pool=None, cpu_pool=None,
                    max_difficulty=3, _exclude=None):
    """Build a single challenge dict from a randomly-chosen template."""
    _exclude = _exclude or set()
    pool = [t for t in SABOTAGE_TEMPLATES
            if t["id"] not in _exclude
            and t["difficulty"] <= max_difficulty
            and (vendor_pool is None
                 or any(v in t["vendors"] for v in vendor_pool))
            and (cpu_pool is None
                 or any(c in t["cpu_brands"] for c in cpu_pool))]
    if not pool:
        raise ValueError("No template matches the supplied pools.")
    tpl = rng.choice(pool)
    vendors_ok = (tpl["vendors"] if vendor_pool is None
                  else [v for v in tpl["vendors"] if v in vendor_pool])
    cpus_ok = (tpl["cpu_brands"] if cpu_pool is None
               else [c for c in tpl["cpu_brands"] if c in cpu_pool])
    vendor = rng.choice(vendors_ok)
    cpu = rng.choice(cpus_ok)
    summary = rng.choice(tpl["flavors"])
    title, briefing = _make_briefing(rng, summary, summary)
    return {
        "id": "gen_%s_%d" % (tpl["id"], _ticket_num(rng)),
        "_template": tpl["id"],
        "title": title,
        "tier": "advanced",
        "vendor": vendor,
        "cpu_brand": cpu,
        "briefing": briefing,
        "hints": [],
        "sabotage": tpl["sabotage_fn"](rng),
        "goal":     tpl["goal_fn"](rng),
        "fail": {"style": tpl["fail_style"], "lines": tpl["fail_lines"]},
        "success_lines": tpl["success"],
    }


def generate_shift(seed, n=5, vendor_pool=None, cpu_pool=None):
    """Deterministic shift generator: returns a list of N challenges.

    Difficulty curve: first half easier, last half can go up to 3.
    No template repeats inside a single shift.
    """
    rng = random.Random(seed)
    out = []
    used = set()
    for i in range(n):
        max_diff = 1 if i < n // 3 else (2 if i < 2 * n // 3 else 3)
        try:
            ch = generate_ticket(rng, vendor_pool=vendor_pool,
                                 cpu_pool=cpu_pool, max_difficulty=max_diff,
                                 _exclude=used)
        except ValueError:
            ch = generate_ticket(rng, vendor_pool=vendor_pool,
                                 cpu_pool=cpu_pool, max_difficulty=3,
                                 _exclude=used)
        used.add(ch["_template"])
        out.append(ch)
    return out
