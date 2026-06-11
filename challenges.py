"""Challenge definitions for the campaign (data only).

Schema per challenge:
  id, title:     identifiers
  briefing:      list of paragraphs shown on the ticket screen
  hints:         progressive hints (one more revealed per failed attempt)
  sabotage:      {item_id: value} merged over defaults when the level starts
                 ("_time_offset_s" sets the CMOS clock offset in seconds)
  goal:          {item_id: value | [values] | "__nonempty__"} — all must hold
                 AND each item must be effectively enabled (depends_on chain)
  goal_offset:   {"max_abs_days": n} — require |CMOS offset| below n days
  fail:          {"style": "black"|"bsod"|"secureboot", "lines": [...]}
  success_lines: shown on the successful-boot screen

Value strings are imported from menu_data to stay typo-proof.
"""

from menu_data import BOOT_DEVICES

WINDOWS_SSD = BOOT_DEVICES[0]
USB_DRIVE = BOOT_DEVICES[1]
NIC_IPV4 = BOOT_DEVICES[2]

RST_MODE = ("Intel RST Premium With Intel Optane System "
            "Acceleration")  # menu_data SATA_CONFIG sata_mode values[1]

CHALLENGES = [
    {
        "id": "ch01_boot_order",
        "title": "No Operating System",
        "briefing": [
            "TICKET #4811 - Front desk PC won't start",
            "",
            "\"I turned on my computer this morning and Windows never "
            "comes up. The screen just says something about selecting a "
            "proper boot device. Nobody touched anything, I swear! "
            "(Well... my nephew was playing with it yesterday.)\"",
            "",
            "The PC powers on and passes self-test. The Windows SSD is "
            "detected and healthy.",
        ],
        "hints": [
            "The machine is trying to start from the wrong device.",
            "Check the Boot screen: what is Boot Option #1?",
            "Set Boot Option #1 to 'Windows Boot Manager' and save with "
            "F10.",
        ],
        "sabotage": {"boot1": NIC_IPV4},
        "goal": {"boot1": WINDOWS_SSD},
        "fail": {"style": "black", "lines": [
            "Reboot and Select proper Boot device",
            "or Insert Boot Media in selected Boot device and press a key",
        ]},
        "success_lines": [
            "Windows Boot Manager",
            "Starting Windows...",
            "",
            "The front desk PC boots straight to the login screen.",
        ],
    },
    {
        "id": "ch02_sata_mode",
        "title": "Blue Screen After Maintenance",
        "briefing": [
            "TICKET #4823 - BSOD on every boot",
            "",
            "A technician reset the BIOS to 'performance defaults' on a "
            "workstation. Since then Windows crashes instantly at startup "
            "with a blue screen: INACCESSIBLE_BOOT_DEVICE.",
            "",
            "Windows was originally installed with the standard AHCI "
            "storage driver.",
        ],
        "hints": [
            "Windows can't find its own disk driver at boot. Something "
            "changed in how the storage controller presents the disk.",
            "Look under Advanced > SATA And RST Configuration.",
            "Set 'SATA Mode Selection' back to AHCI and save.",
        ],
        "sabotage": {"sata_mode": RST_MODE},
        "goal": {"sata_mode": "AHCI"},
        "fail": {"style": "bsod", "lines": [
            "Your PC ran into a problem and needs to restart. We're just",
            "collecting some error info, and then we'll restart for you.",
            "",
            "0% complete",
            "",
            "Stop code: INACCESSIBLE_BOOT_DEVICE",
        ]},
        "success_lines": [
            "Windows Boot Manager",
            "Starting Windows...",
            "",
            "The storage driver loads normally. No more blue screens.",
        ],
    },
    {
        "id": "ch03_secure_boot_usb",
        "title": "Linux USB Refuses to Boot",
        "briefing": [
            "TICKET #4831 - Can't boot the recovery USB stick",
            "",
            "A developer needs to boot a Linux live USB (SanDisk Ultra) "
            "to recover files, but the machine blocks it with a 'Secure "
            "Boot Violation' message and falls back to Windows.",
            "",
            "The live image is unsigned, and the stick must be FIRST in "
            "the boot order so it starts automatically.",
        ],
        "hints": [
            "Two things are needed: allow unsigned images, and put the "
            "USB stick first in the boot order.",
            "Secure Boot lives under Security > Secure Boot.",
            "Disable Secure Boot, then on the Boot screen set Boot Option "
            "#1 to the UEFI SanDisk USB drive. Save with F10.",
        ],
        "sabotage": {},
        "goal": {"secure_boot": "Disabled", "boot1": USB_DRIVE},
        "fail": {"style": "secureboot", "lines": [
            "Secure Boot Violation",
            "",
            "Invalid signature detected.",
            "Check Secure Boot Policy in Setup.",
        ]},
        "success_lines": [
            "SYSLINUX 6.04 EDD Copyright (C) 1994-2015 H. Peter Anvin et al",
            "Booting the Linux live environment...",
            "",
            "The recovery USB starts and the files are saved.",
        ],
    },
    {
        "id": "ch04_vtx",
        "title": "Virtual Machines Won't Start",
        "briefing": [
            "TICKET #4840 - VirtualBox error on new build",
            "",
            "\"Every time I start a virtual machine I get:",
            "",
            "  VT-x is disabled in the BIOS for all CPU modes",
            "  (VERR_VMX_MSR_ALL_VMX_DISABLED).",
            "",
            "The CPU definitely supports virtualization - it's an i7!\"",
        ],
        "hints": [
            "The CPU feature exists but the firmware is hiding it from "
            "the operating system.",
            "Look in Advanced > CPU Configuration.",
            "Enable 'Intel (VMX) Virtualization Technology' and save.",
        ],
        "sabotage": {"vmx": "Disabled"},
        "goal": {"vmx": "Enabled"},
        "fail": {"style": "black", "lines": [
            "VirtualBox - Error",
            "",
            "Failed to open a session for the virtual machine DevBox.",
            "",
            "VT-x is disabled in the BIOS for all CPU modes",
            "(VERR_VMX_MSR_ALL_VMX_DISABLED).",
        ]},
        "success_lines": [
            "Starting Windows...",
            "",
            "VirtualBox launches the DevBox VM without errors.",
            "Hardware virtualization is available again.",
        ],
    },
    {
        "id": "ch05_cmos_date",
        "title": "Every Website Is 'Not Secure'",
        "briefing": [
            "TICKET #4852 - Browser blocks every site",
            "",
            "\"Since the weekend power outage, every website shows:",
            "",
            "  Your connection is not private",
            "  NET::ERR_CERT_DATE_INVALID",
            "",
            "Even google.com! The PC also asked for the time once at "
            "startup.\"",
            "",
            "A flat CMOS battery was replaced this morning, but the "
            "clock was never corrected.",
        ],
        "hints": [
            "TLS certificates are only valid within their date range. "
            "What does the machine think today's date is?",
            "Check System Date on the Main screen - it is years off.",
            "Select System Date, use +/- to fix month/day/year (Tab "
            "switches fields), then save with F10.",
        ],
        "sabotage": {"_time_offset_s": -94608000},  # about -3 years
        "goal": {},
        "goal_offset": {"max_abs_days": 1},
        "fail": {"style": "black", "lines": [
            "Your connection is not private",
            "",
            "Attackers might be trying to steal your information.",
            "",
            "NET::ERR_CERT_DATE_INVALID",
        ]},
        "success_lines": [
            "Starting Windows...",
            "",
            "The clock is correct. Certificates validate and every site "
            "loads normally.",
        ],
    },
    {
        "id": "ch06_legacy_usb",
        "title": "Dead Keyboard in the Installer",
        "vendor": "award",
        "briefing": [
            "TICKET #4860 - Keyboard works in BIOS but not in the tool",
            "",
            "An older Pentium III bench (Award/Phoenix BIOS) is being used "
            "to flash some legacy EEPROM cartridges. The technician boots "
            "an old DOS-based flashing tool from USB. The tool starts, but "
            "the USB keyboard is completely dead inside it - although it "
            "works fine here in Setup.",
            "",
            "Old pre-boot environments rely on the firmware to emulate "
            "USB keyboards as legacy PS/2 devices.",
        ],
        "hints": [
            "The tool has no USB drivers of its own: the firmware must "
            "translate USB input for it.",
            "On this Award firmware the USB options live under "
            "INTEGRATED PERIPHERALS.",
            "Set 'Legacy USB Support' to Enabled and save with F10.",
        ],
        "sabotage": {"legacy_usb": "Disabled"},
        "goal": {"legacy_usb": "Enabled"},
        "fail": {"style": "black", "lines": [
            "FlashTool/DOS v3.2",
            "",
            "Press any key to begin flashing...",
            "",
            "(the keyboard does not respond)",
        ]},
        "success_lines": [
            "FlashTool/DOS v3.2",
            "Press any key to begin flashing... OK",
            "",
            "Keystrokes register. The firmware update completes.",
        ],
    },
    {
        "id": "ch07_admin_pwd",
        "title": "Security Audit Finding",
        "briefing": [
            "TICKET #4871 - Compliance: unprotected firmware setup",
            "",
            "The quarterly security audit flagged this machine:",
            "",
            "  FINDING SEC-112: UEFI Setup is not password protected.",
            "  Anyone with physical access can alter boot settings.",
            "",
            "Company policy requires an administrator password on the "
            "firmware setup of every workstation.",
        ],
        "hints": [
            "You need to install a supervisor password, not change a "
            "setting.",
            "Look on the Security screen.",
            "Select 'Administrator Password', type a new password and "
            "press Enter, then save with F10.",
        ],
        "sabotage": {"admin_pwd": ""},
        "goal": {"admin_pwd": "__nonempty__"},
        "fail": {"style": "black", "lines": [
            "compliance-scan.exe --target localhost --uefi",
            "",
            "FINDING SEC-112 still open:",
            "Administrator Password : Not Installed",
            "",
            "AUDIT RESULT: FAILED",
        ]},
        "success_lines": [
            "compliance-scan.exe --target localhost --uefi",
            "",
            "Administrator Password : Installed",
            "",
            "AUDIT RESULT: PASSED",
        ],
    },
    {
        "id": "ch08_win11",
        "title": "This PC Can't Run Windows 11",
        "briefing": [
            "TICKET #4885 - Windows 11 upgrade blocked",
            "",
            "The upgrade assistant refuses to install Windows 11:",
            "",
            "  This PC doesn't currently meet Windows 11 system",
            "  requirements:",
            "    - TPM 2.0 must be supported and enabled on this PC",
            "    - The PC must support Secure Boot",
            "",
            "The board HAS a TPM 2.0 chip; someone switched things off.",
        ],
        "hints": [
            "Two separate settings are required: the security chip and "
            "verified boot.",
            "The TPM is under Advanced > Trusted Computing ('Security "
            "Device Support'). Secure Boot is under Security > Secure "
            "Boot.",
            "Set Security Device Support to Enable AND Secure Boot to "
            "Enabled, then save.",
        ],
        "sabotage": {"tpm_enable": "Disable", "secure_boot": "Disabled"},
        "goal": {"tpm_enable": "Enable", "secure_boot": "Enabled"},
        "fail": {"style": "black", "lines": [
            "Windows 11 Installation Assistant",
            "",
            "This PC doesn't currently meet Windows 11 system "
            "requirements.",
            "",
            "  TPM 2.0           : Not detected",
            "  Secure Boot       : Off",
        ]},
        "success_lines": [
            "Windows 11 Installation Assistant",
            "",
            "  TPM 2.0           : Ready",
            "  Secure Boot       : On",
            "",
            "Great news - this PC meets Windows 11 requirements!",
        ],
    },
    {
        "id": "ch09_pxe",
        "title": "Lab Machines Must Netboot",
        "cpu_brand": "amd",
        "briefing": [
            "TICKET #4893 - Imaging server can't reach this PC",
            "",
            "The IT lab reimages machines overnight from a network "
            "deployment server. This is one of the new AMD Ryzen lab "
            "boxes; it never picks up an image: it boots straight from "
            "its SSD and the network boot never even starts.",
            "",
            "It must attempt an IPv4 network boot FIRST, before the "
            "local disk.",
        ],
        "hints": [
            "Network booting needs the firmware network stack, IPv4 PXE "
            "support, and the right boot order - three settings.",
            "Advanced > Network Stack Configuration: enable the stack "
            "first; only then can IPv4 PXE be changed.",
            "Finally set Boot Option #1 to 'Onboard NIC (IPV4)' on the "
            "Boot screen and save.",
        ],
        "sabotage": {"net_stack": "Disabled", "pxe4": "Disabled",
                     "boot1": WINDOWS_SSD},
        "goal": {"net_stack": "Enabled", "pxe4": "Enabled",
                 "boot1": NIC_IPV4},
        "fail": {"style": "black", "lines": [
            "Deployment server log - host LAB-07:",
            "",
            "  23:00:01  wake packet sent",
            "  23:00:34  no PXE request received",
            "  23:00:35  host booted local OS instead",
            "",
            "IMAGING: SKIPPED",
        ]},
        "success_lines": [
            "Intel(R) Boot Agent GE v1.5.43",
            "CLIENT MAC ADDR: 00 00 5E 00 53 BB",
            "DHCP... PXE-M0F: Exiting Intel Boot Agent.",
            "",
            "The deployment image downloads and installs overnight.",
        ],
    },
    {
        "id": "ch10_csm_gpu",
        "title": "Old Graphics Card, Black Screen",
        "briefing": [
            "TICKET #4901 - No display with the spare video card",
            "",
            "A vintage PCI-E graphics card (legacy VBIOS only, no UEFI "
            "GOP driver) was installed for testing. The machine powers "
            "on but the card never initializes on real hardware: legacy "
            "Option ROMs are not being executed.",
            "",
            "Legacy Option ROM support (CSM) is mutually exclusive with "
            "Secure Boot.",
        ],
        "hints": [
            "Three steps, in order - each one unlocks the next.",
            "First disable Secure Boot (Security screen). That unlocks "
            "'Launch CSM' under Boot > CSM.",
            "Enable Launch CSM, then set 'Boot from PCI-E Expansion "
            "Devices' to 'Legacy OpROM first'. Save with F10.",
        ],
        "sabotage": {"secure_boot": "Enabled", "csm": "Disabled"},
        "goal": {"secure_boot": "Disabled", "csm": "Enabled",
                 "csm_pcie": "Legacy OpROM first"},
        "fail": {"style": "black", "lines": [
            "(the spare graphics card outputs no signal)",
            "",
            "POST diagnostic: legacy Option ROM not executed.",
            "CSM is disabled or UEFI driver priority is in effect.",
        ]},
        "success_lines": [
            "Legacy VBIOS initialized at C000:0000",
            "",
            "The old card lights up and displays the boot screen.",
            "Test bench is operational.",
        ],
    },

    # ================================================================
    # ADVANCED TIER (11-20): vague symptoms only, no hints.
    # ================================================================
    {
        "id": "ch11_performance",
        "title": "Half the Machine It Was",
        "tier": "advanced",
        "cpu_brand": "amd",
        "briefing": [
            "TICKET #5102 - Workstation underperforming",
            "",
            "\"Our 8-core Ryzen render box used to chew through jobs. "
            "After someone experimented with 'power tuning' it benchmarks "
            "at less than half its old score. Task Manager shows fewer "
            "logical processors than I remember, and the clock speed "
            "never goes above base.\"",
            "",
            "Make it fast again. All of it.",
        ],
        "hints": [],
        "sabotage": {"ht": "Disabled", "active_cores": "2",
                     "speedstep": "Disabled", "turbo": "Disabled",
                     "cstates": "Disabled"},
        "goal": {"ht": "Enabled", "active_cores": "All",
                 "speedstep": "Enabled", "turbo": "Enabled"},
        "fail": {"style": "black", "lines": [
            "benchmark.exe --full",
            "",
            "  Logical processors : (reduced)",
            "  Max clock observed : base frequency only",
            "",
            "SCORE: 48% of reference. REGRESSION.",
        ]},
        "success_lines": [
            "benchmark.exe --full",
            "",
            "  All cores online, boost clocks reached.",
            "",
            "SCORE: 101% of reference. PASSED.",
        ],
    },
    {
        "id": "ch12_audio",
        "title": "The Silent Conference Room",
        "tier": "advanced",
        "cpu_brand": "amd",
        "briefing": [
            "TICKET #5110 - No sound, drivers reinstalled twice",
            "",
            "\"The conference room PC plays no audio at all. Windows "
            "shows NO playback devices - not even disabled ones. We "
            "reinstalled the sound drivers twice and the installer says "
            "'no compatible hardware found'. The speakers work on a "
            "laptop.\"",
        ],
        "hints": [],
        "sabotage": {"hd_audio": "Disabled"},
        "goal": {"hd_audio": "Enabled"},
        "fail": {"style": "black", "lines": [
            "audio-driver-setup.exe",
            "",
            "Searching for compatible hardware...",
            "",
            "ERROR: No High Definition Audio controller present",
            "on this system. Setup cannot continue.",
        ]},
        "success_lines": [
            "audio-driver-setup.exe",
            "",
            "High Definition Audio controller detected.",
            "Driver installed. Test tone plays in the conference room.",
        ],
    },
    {
        "id": "ch13_wol",
        "title": "The Machine That Sleeps Through Patch Night",
        "tier": "advanced",
        "briefing": [
            "TICKET #5121 - Host unreachable for overnight maintenance",
            "",
            "Every Wednesday night the management server wakes all "
            "workstations to install updates. This one never wakes - "
            "and stranger still, while it is OFF, its network port LED "
            "is completely dark. During the day, with Windows running, "
            "the network works fine... according to the last technician, "
            "who also 'optimized' some settings.",
        ],
        "hints": [],
        "sabotage": {"pch_lan": "Disabled", "wake_on_lan": "Disabled"},
        "goal": {"pch_lan": "Enabled", "wake_on_lan": "Enabled"},
        "fail": {"style": "black", "lines": [
            "patch-mgmt log - host WS-114:",
            "",
            "  02:00:01  magic packet sent (3 retries)",
            "  02:05:00  host did not respond",
            "",
            "PATCH WINDOW: MISSED",
        ]},
        "success_lines": [
            "patch-mgmt log - host WS-114:",
            "",
            "  02:00:01  magic packet sent",
            "  02:00:09  host online - updates installing",
            "",
            "PATCH WINDOW: OK",
        ],
    },
    {
        "id": "ch14_igpu",
        "title": "The Missing Second GPU",
        "tier": "advanced",
        "briefing": [
            "TICKET #5135 - Capture software can't find the iGPU",
            "",
            "The streaming rig has a discrete card for the game and is "
            "supposed to use the processor's integrated graphics for "
            "encoding. The capture software insists the integrated GPU "
            "does not exist, and Device Manager agrees: only one display "
            "adapter is listed. The CPU definitely has graphics on "
            "board.",
        ],
        "hints": [],
        "sabotage": {"igfx": "Disabled"},
        "goal": {"igfx": "Enabled"},
        "fail": {"style": "black", "lines": [
            "capture-suite.exe --enumerate-encoders",
            "",
            "  GPU 0 : discrete adapter (busy - game)",
            "  GPU 1 : not found",
            "",
            "Hardware encoder unavailable. Falling back to CPU (slow).",
        ]},
        "success_lines": [
            "capture-suite.exe --enumerate-encoders",
            "",
            "  GPU 0 : discrete adapter",
            "  GPU 1 : integrated graphics - QuickSync ready",
            "",
            "Hardware encoding enabled. Stream is smooth.",
        ],
    },
    {
        "id": "ch15_hotplug",
        "title": "Reboot Required (Every Single Time)",
        "tier": "advanced",
        "vendor": "award",
        "briefing": [
            "TICKET #5142 - Drive tray only appears after restart",
            "",
            "An old Pentium 4 server (Award/Phoenix BIOS) is used by the "
            "backup team. The operator swaps disks in a removable SATA "
            "tray (second port) several times a day. Inserted disks are "
            "never detected until the whole machine is restarted, which "
            "wastes about twenty minutes per swap. On the newer rack the "
            "disks appear immediately.",
        ],
        "hints": [],
        "sabotage": {"sata_p1_hotplug": "Disabled"},
        "goal": {"sata_p1_hotplug": "Enabled"},
        "fail": {"style": "black", "lines": [
            "backup-rotation.log:",
            "",
            "  09:14  tray disk inserted - no device event",
            "  09:15  operator forced a reboot (again)",
            "",
            "ROTATION TIME: 22 min (target: 2 min)",
        ]},
        "success_lines": [
            "backup-rotation.log:",
            "",
            "  09:14  tray disk inserted - device online in 4 s",
            "",
            "ROTATION TIME: 2 min. Operator is delighted.",
        ],
    },
    {
        "id": "ch16_failover_boot",
        "title": "Plan B Never Happens",
        "tier": "advanced",
        "cpu_brand": "amd",
        "briefing": [
            "TICKET #5150 - Recovery image doesn't kick in",
            "",
            "This unattended machine has a recovery USB drive mounted "
            "permanently inside the case. The design: if the primary "
            "drive ever fails, the machine should automatically fall "
            "through to the recovery image on the next start. A drill "
            "was run yesterday - primary disconnected - and instead of "
            "recovering, the machine just sat on an error message.",
        ],
        "hints": [],
        "sabotage": {"boot2": "Disabled", "numlock": "Off"},
        "goal": {"boot2": USB_DRIVE},
        "fail": {"style": "black", "lines": [
            "FAILOVER DRILL - attempt 2:",
            "",
            "  Primary disk: disconnected (simulated failure)",
            "  Machine response:",
            "",
            "  'Reboot and Select proper Boot device'",
            "",
            "DRILL RESULT: FAILED - no fallback occurred",
        ]},
        "success_lines": [
            "FAILOVER DRILL - attempt 3:",
            "",
            "  Primary disk: disconnected (simulated failure)",
            "  Machine response: booted recovery environment in 18 s",
            "",
            "DRILL RESULT: PASSED",
        ],
    },
    {
        "id": "ch17_passthrough",
        "title": "The Device That Won't Pass Through",
        "tier": "advanced",
        "cpu_brand": "amd",
        "briefing": [
            "TICKET #5163 - VM device assignment fails",
            "",
            "A Threadripper virtualization host needs to hand a PCIe "
            "card directly to a guest VM. The hypervisor refuses:",
            "",
            "  error: device assignment requires an IOMMU,",
            "  and no IOMMU groups were found.",
            "",
            "It also logs a warning about 64-bit device apertures not "
            "being mappable. The hardware supports all of this on "
            "paper.",
        ],
        "hints": [],
        "sabotage": {"vtd": "Disabled", "above_4g": "Disabled",
                     "aes": "Disabled"},
        "goal": {"vtd": "Enabled", "above_4g": "Enabled"},
        "fail": {"style": "black", "lines": [
            "hypervisor: starting guest 'gpu-worker'...",
            "",
            "error: device assignment requires an IOMMU, and no IOMMU",
            "groups were found.",
            "warning: 64-bit BAR could not be mapped below 4G.",
            "",
            "Guest failed to start.",
        ]},
        "success_lines": [
            "hypervisor: starting guest 'gpu-worker'...",
            "",
            "  IOMMU groups detected: 14",
            "  PCIe device 01:00.0 assigned to guest",
            "",
            "Guest is running with direct device access.",
        ],
    },
    {
        "id": "ch18_tpm_clear",
        "title": "Previous Owner's Ghost",
        "tier": "advanced",
        "briefing": [
            "TICKET #5171 - Repurposed machine, security chip locked",
            "",
            "This PC arrived from a decommissioned department. Disk "
            "encryption provisioning fails because the security chip "
            "still holds the previous owner's keys - and on top of "
            "that, the chip doesn't even show up in the OS right now.",
            "",
            "Policy: the chip must be wiped through the firmware so the "
            "machine can be re-provisioned from scratch on next boot.",
        ],
        "hints": [],
        "sabotage": {"tpm_enable": "Disable", "tpm_pending": "None"},
        "goal": {"tpm_enable": "Enable", "tpm_pending": "TPM Clear"},
        "fail": {"style": "black", "lines": [
            "provision-encryption.exe",
            "",
            "TPM state : foreign owner authorization present",
            "          (or device not available)",
            "",
            "Cannot take ownership. Provisioning aborted.",
        ]},
        "success_lines": [
            "(on restart, the firmware clears the security device)",
            "",
            "provision-encryption.exe",
            "",
            "TPM state : cleared, ready for ownership",
            "Encryption provisioning completed.",
        ],
    },
    {
        "id": "ch19_custom_sb",
        "title": "Signed by Us",
        "tier": "advanced",
        "briefing": [
            "TICKET #5188 - Custom-signed OS must boot, security ON",
            "",
            "The research team boots an in-house operating system "
            "signed with the company's own keys. Security policy is "
            "strict: verified boot must remain ACTIVE - simply turning "
            "it off (the previous 'fix') is a written warning waiting "
            "to happen.",
            "",
            "The firmware must keep enforcing signatures, but accept "
            "policy changes so the company keys can be enrolled by a "
            "technician.",
        ],
        "hints": [],
        "sabotage": {"secure_boot": "Disabled", "sb_mode": "Standard"},
        "goal": {"secure_boot": "Enabled", "sb_mode": "Custom"},
        "fail": {"style": "secureboot", "lines": [
            "Security Compliance Check",
            "",
            "Verified boot enforcing : REQUIRED",
            "Custom key enrollment   : REQUIRED",
            "",
            "Current state does not meet policy.",
        ]},
        "success_lines": [
            "Security Compliance Check",
            "",
            "Verified boot enforcing : YES",
            "Custom key enrollment   : AVAILABLE",
            "",
            "ResearchOS boots with its company-signed kernel. POLICY MET.",
        ],
    },
    {
        "id": "ch20_kiosk",
        "title": "The Kiosk That Keeps Getting Hacked",
        "tier": "advanced",
        "vendor": "award",
        "briefing": [
            "TICKET #5200 - Lobby kiosk tampered with again",
            "",
            "The lobby kiosk is a barely-supported Award/Phoenix box from "
            "the early 2000s. Twice this month someone rebooted it with a "
            "USB stick and got a full desktop. The night guard also "
            "reports the kiosk shows 'a wall of scrolling text' at every "
            "boot, which visitors find alarming.",
            "",
            "Lock it down: it must start fast and silently into its own "
            "system and NOTHING else, and nobody without authorization "
            "should be able to change firmware settings ever again.",
        ],
        "hints": [],
        "sabotage": {"quiet_boot": "Disabled", "fast_boot": "Disabled",
                     "boot2": USB_DRIVE, "boot3": NIC_IPV4,
                     "admin_pwd": "", "case_open_warning": "Enabled"},
        "goal": {"admin_pwd": "__nonempty__", "quiet_boot": "Enabled",
                 "fast_boot": "Enabled", "boot2": "Disabled",
                 "boot3": "Disabled"},
        "fail": {"style": "black", "lines": [
            "kiosk-hardening-audit.exe",
            "",
            "  Setup password        : ?",
            "  Silent fast startup   : ?",
            "  Alternate boot paths  : ?",
            "",
            "One or more checks FAILED. Kiosk remains vulnerable.",
        ]},
        "success_lines": [
            "kiosk-hardening-audit.exe",
            "",
            "  Setup password        : OK",
            "  Silent fast startup   : OK",
            "  Alternate boot paths  : NONE",
            "",
            "ALL CHECKS PASSED. The kiosk survives the next intern.",
        ],
    },
    # ----------------------------------------------------- multi-phase tier
    {
        "id": "ch21_storage_then_secureboot",
        "title": "Recovery USB Won't Boot After Service",
        "tier": "advanced",
        "briefing": [
            "TICKET #6017 - Workshop bench machine. The customer left "
            "their PC after a 'storage upgrade' and now it won't read the "
            "service technician's signed recovery USB.",
            "",
            "Whoever touched it last reconfigured the SATA mode and "
            "re-armed Secure Boot. The recovery USB image is signed "
            "with our shop's keys but the firmware rejects it.",
            "",
            "Fix this in two passes: first get the OS to see its disk, "
            "reboot to verify, then disable Secure Boot so the recovery "
            "USB can run its diagnostic.",
        ],
        "hints": [],
        "sabotage": {"sata_mode": RST_MODE, "secure_boot": "Enabled"},
        "goal_phases": [
            {"name": "Restore AHCI",
             "goal": {"sata_mode": "AHCI"},
             "next_sabotage": {},
             "phase_briefing_addendum": [
                 "PHASE 1 of 2: the customer's NVMe OS won't appear",
                 "until SATA Controller mode is back to AHCI. Set it,",
                 "save & exit, then reboot.",
             ]},
            {"name": "Disable Secure Boot for USB",
             "goal": {"secure_boot": "Disabled"},
             "phase_briefing_addendum": [
                 "PHASE 2 of 2: OS sees its disk again. Now the signed",
                 "recovery USB needs Secure Boot OFF to run.",
             ]},
        ],
        "fail": {"style": "bsod", "lines": [
            "INACCESSIBLE_BOOT_DEVICE",
            "",
            "Storage stack failed to enumerate during boot.",
            "Check that SATA mode matches the installed driver,",
            "and that Secure Boot is not blocking signed media.",
        ]},
        "success_lines": [
            "Recovery USB diagnostic v3.2",
            "",
            "  Storage controller : OK",
            "  Image signature    : OK (signed by Workshop CA)",
            "",
            "Diagnostic running... 0 errors found.",
        ],
    },
    {
        "id": "ch22_efi_shell_vt",
        "title": "Hypervisor Crash on AMD Workstation",
        "tier": "advanced",
        "vendor": "efi",
        "cpu_brand": "amd",
        "briefing": [
            "TICKET #6109 - The data-science group's new AMD workstation",
            "boots straight into the UEFI Shell because the previous",
            "operator removed startup.nsh. The hypervisor lab",
            "container won't start because virtualization isn't exposed.",
            "",
            "There's no Setup Utility on this firmware build. Drive",
            "it from the shell:",
            "  setvar vmx Enabled",
            "  reset cold",
            "",
            "(Type 'help' for a command list.)",
        ],
        "hints": [],
        "sabotage": {"vmx": "Disabled"},
        "goal": {"vmx": "Enabled"},
        "fail": {"style": "black", "lines": [
            "hypervisor-init.sh",
            "",
            "  KVM module load    : FAIL",
            "  Reason: AMD-V (SVM) reports DISABLED in MSR 0xC0010114.",
            "",
            "Container engine refused to start.",
        ]},
        "success_lines": [
            "hypervisor-init.sh",
            "",
            "  KVM module load    : OK",
            "  AMD-V (SVM)        : ENABLED",
            "",
            "Lab container queue accepting jobs.",
        ],
    },
    {
        "id": "ch23_award_legacy",
        "title": "Award Bench: ISA Card Refuses to Init",
        "tier": "advanced",
        "vendor": "award",
        "briefing": [
            "TICKET #6210 - Museum workshop. A vintage Award/Phoenix",
            "build with an ISA tape controller card came in: the card",
            "is detected during POST but the OS never sees it.",
            "",
            "This Award firmware predates Secure Boot, so the actual",
            "fix is to re-enable Legacy USB Support (the previous owner",
            "had switched it off, which prevents the BIOS extension ROM",
            "from running) and to put the optical drive back as the",
            "primary boot device so the loader can rebuild config.",
        ],
        "hints": [],
        "sabotage": {"legacy_usb": "Disabled", "boot1": USB_DRIVE},
        "goal": {"legacy_usb": "Enabled", "boot1": WINDOWS_SSD},
        "fail": {"style": "black", "lines": [
            "Award Modular BIOS v6.00PG, An Energy Star Ally",
            "Detecting IDE drives ...",
            "",
            "DISK BOOT FAILURE, INSERT SYSTEM DISK AND PRESS ENTER",
        ]},
        "success_lines": [
            "Starting MS-DOS...",
            "",
            "HIMEM.SYS loaded.",
            "C:\\> tapeinit",
            "  ISA tape controller initialized at I/O 280h, IRQ 5",
            "  Drive ready.",
        ],
    },
    {
        "id": "ch24_xmp_tuning",
        "title": "They Paid For 3600",
        "tier": "advanced",
        "briefing": [
            "TICKET #6313 - Enthusiast build, brand-new 3600 MT/s kit.",
            "The customer enabled XMP Profile 2 and the machine stopped",
            "POSTing: fans spin, screen stays black, then it retries.",
            "",
            "They were very clear on the phone: \"don't you dare run my",
            "RAM at 2133, I paid for the full 3600.\" Profile 2 must",
            "stay on -- make it train.",
            "",
            "(Memory controllers off the cheap shelf often need more",
            "DIMM voltage and a relaxed command rate at this speed.)",
        ],
        "hints": [],
        "sabotage": {"xmp": "Profile 2",
                     "dram_volt": "Auto",
                     "cmd_rate": "Auto",
                     "sata_lpm": "Disabled"},
        "goal": {"xmp": "Profile 2",
                 "dram_volt": "1.45V",
                 "cmd_rate": "2T"},
        "fail": {"style": "memtrain", "lines": [
            "Memory initialization error.",
            "The system DRAM failed training at the configured frequency.",
            "",
            "MRC: DDR4 training FAILED on channel A, rank 0",
        ]},
        "success_lines": [
            "Memory training passed: 3600 MT/s 17-19-19-39 @ 1.45V 2T",
            "",
            "memtest86 quick pass: 0 errors.",
            "The customer gets their sticker speed.",
        ],
    },
    {
        "id": "ch25_oc_watchdog",
        "title": "The Nephew's Overclock",
        "tier": "advanced",
        "briefing": [
            "TICKET #6377 - Gaming tower. The owner's nephew applied a",
            "'free performance upgrade' before the holidays. Since then",
            "Windows bluescreens seconds after login with",
            "CLOCK_WATCHDOG_TIMEOUT.",
            "",
            "The owner liked the extra speed, though. Keep the CPU at",
            "47x or better -- just make it stable. (And don't push past",
            "what the silicon can actually do.)",
        ],
        "hints": [],
        "sabotage": {"cpu_ratio": 49, "vcore_offset": "+0.00V"},
        "goal": {"cpu_ratio": [47, 48, 49, 50, 51, 52]},
        "fail": {"style": "bsod", "lines": [
            "Your PC ran into a problem and needs to restart. We're just",
            "collecting some error info, and then we'll restart for you.",
            "",
            "0% complete",
            "",
            "Stop code: CLOCK_WATCHDOG_TIMEOUT",
        ]},
        "success_lines": [
            "Windows loaded. 30-minute stress run: PASS.",
            "",
            "  Core ratio   : 49x",
            "  Core voltage : offset applied, thermals in range",
            "",
            "The nephew takes full credit.",
        ],
    },
    {
        "id": "ch26_fan_thermtrip",
        "title": "It Got Quieter",
        "tier": "advanced",
        "vendor": "award",
        "cpu_brand": "amd",
        "briefing": [
            "TICKET #6402 - Office tower shuts itself off moments after",
            "power-on, every time. The user proudly mentions the PC",
            "'finally got quieter' after they explored the firmware",
            "settings last week.",
            "",
            "The case is hot to the touch near the CPU. Check the",
            "hardware health readouts before you hand it back.",
        ],
        "hints": [],
        "sabotage": {"cpu_fan_profile": "Disabled"},
        "goal": {"cpu_fan_profile": ["Standard", "Silent", "Turbo"]},
        "fail": {"style": "thermtrip", "lines": [
            "CPU Over Temperature Error!",
            "CPU Fan Error!",
            "",
            "The system reached the processor thermal trip point",
            "and shut itself down.",
            "",
            "Press F1 to Resume",
        ]},
        "success_lines": [
            "PC Health Status",
            "",
            "  CPU Temperature : +47.0 C",
            "  CPU Fan Speed   : 1280 RPM",
            "",
            "The tower hums along. Slightly louder. Alive.",
        ],
        "hw_info": {
            "cpu_temp": {"by": "cpu_fan_profile",
                         "map": {"Disabled": "+96.0 C"},
                         "default": "+47.0 C"},
        },
    },
    {
        "id": "ch27_rtc_wake",
        "title": "The 3 AM Machine",
        "tier": "advanced",
        "briefing": [
            "TICKET #6451 - Building security keeps logging a PC in the",
            "accounting office powering itself on at 3 AM. Nobody",
            "admits to scheduling anything, and IT found no wake timers",
            "configured in the operating system.",
            "",
            "If it isn't the OS, it's the firmware.",
        ],
        "hints": [],
        "sabotage": {"rtc_wake": "Enabled", "rtc_wake_hour": 3},
        "goal": {"rtc_wake": "Disabled"},
        "fail": {"style": "black", "lines": [
            "security-log: 03:00:41  PC-ACCT-07 POWERED ON",
            "  wake source        : RTC ALARM (firmware)",
            "  scheduled OS tasks : none",
        ]},
        "success_lines": [
            "security-log: no unattended power-on events for 7 days.",
            "",
            "Case closed. The accounting office sleeps at night,",
            "and so does its PC.",
        ],
    },
    {
        "id": "ch28_m2_lanes",
        "title": "The Vanishing Terabytes",
        "tier": "advanced",
        "briefing": [
            "TICKET #6488 - Photo studio workstation. After a DIY M.2",
            "'upgrade attempt' the 2TB archive drive disappeared from",
            "Windows. The drive tests healthy on the bench.",
            "",
            "Two passes: first bring the archive drive back, reboot to",
            "verify, then enable hot-swap on its port -- the studio",
            "rotates backup disks in that bay every Friday.",
        ],
        "hints": [],
        "sabotage": {"m2_mode": "SATA"},
        "goal_phases": [
            {"name": "Restore SATA Port 1",
             "goal": {"m2_mode": ["Auto", "PCIe"]},
             "next_sabotage": {},
             "phase_briefing_addendum": [
                 "PHASE 1 of 2: the archive drive sits on Serial ATA",
                 "Port 1, which shares bandwidth with the M.2_2 socket.",
                 "Free the port, save, and reboot.",
             ]},
            {"name": "Enable hot-swap",
             "goal": {"sata_p1_hotplug": "Enabled"},
             "phase_briefing_addendum": [
                 "PHASE 2 of 2: the drive is back. Now mark its port",
                 "Hot Pluggable so Friday's disk rotation stops",
                 "requiring reboots.",
             ]},
        ],
        "fail": {"style": "black", "lines": [
            "Disk Management: ST2000DM008 (2TB) MISSING.",
            "  Serial ATA Port 1 : no device attached",
            "",
            "The studio's archive is unreachable.",
        ]},
        "success_lines": [
            "Disk Management: ST2000DM008 (2TB) ONLINE.",
            "  Hot-swap        : ENABLED on Serial ATA Port 1",
            "",
            "All volumes mounted. Friday rotation is one click now.",
        ],
    },
    {
        "id": "ch29_efi_clock",
        "title": "Certificates From the Future",
        "tier": "advanced",
        "vendor": "efi",
        "briefing": [
            "TICKET #6532 - Headless build server, shell-only firmware.",
            "After months unplugged in storage its RTC drifted years",
            "into the past. Now every TLS connection fails:",
            "NET::ERR_CERT_DATE_INVALID -- 'certificate not yet valid'.",
            "",
            "There is no Setup Utility on this build. The UEFI Shell",
            "can read and set the hardware clock directly:",
            "  date              (show)   date mm/dd/yyyy   (set)",
            "  time              (show)   time hh:mm:ss     (set)",
            "  reset cold        (save and reboot)",
        ],
        "hints": [],
        "sabotage": {"_time_offset_s": -94608000},
        "goal": {},
        "goal_offset": {"max_abs_days": 1},
        "fail": {"style": "black", "lines": [
            "pkg-sync: TLS handshake FAILED",
            "  NET::ERR_CERT_DATE_INVALID",
            "  Server certificate is not yet valid.",
            "",
            "  Hint: the certificate validity window starts years",
            "  after this machine's current date.",
        ]},
        "success_lines": [
            "pkg-sync: TLS handshake OK",
            "  Certificate dates valid.",
            "",
            "Build queue draining. The server rejoins the farm.",
        ],
    },
    {
        "id": "ch30_phoenix_dock",
        "title": "Corporate Laptop, Wrong Boot",
        "tier": "advanced",
        "vendor": "phoenix",
        "briefing": [
            "TICKET #6601 - Sales laptop (PhoenixBIOS). Since the user",
            "borrowed a docking station from the warehouse, the machine",
            "hangs at 'PXE-E61: Media test failure' on every cold boot",
            "and only starts Windows if they pull the network cable.",
            "",
            "The dock's NIC jumped to the top of the boot order. Put",
            "the internal disk back first and stop the firmware from",
            "fishing for a network image.",
        ],
        "hints": [],
        "sabotage": {"boot1": NIC_IPV4, "boot2": NIC_IPV4},
        "goal": {"boot1": WINDOWS_SSD, "boot2": ["Disabled", USB_DRIVE]},
        "fail": {"style": "black", "lines": [
            "Intel UNDI, PXE-2.1",
            "PXE-E61: Media test failure, check cable",
            "PXE-M0F: Exiting Intel Boot Agent.",
            "",
            "Operating System not found",
        ]},
        "success_lines": [
            "Windows Boot Manager",
            "Starting Windows...",
            "",
            "Docked or undocked, the laptop boots its own disk.",
        ],
    },
    {
        "id": "ch31_phoenix_rtc",
        "title": "The Conference Room Glow",
        "tier": "advanced",
        "vendor": "phoenix",
        "cpu_brand": "intel",
        "briefing": [
            "TICKET #6644 - The conference-room laptop (PhoenixBIOS)",
            "wakes up by itself before dawn. Facilities found it on at",
            "05:00 three days in a row; the calendar shows no meetings",
            "and the OS has no wake timers.",
            "",
            "IT policy also says corporate laptops must stay off when",
            "AC power returns after an outage -- double-check that",
            "while you're in there.",
        ],
        "hints": [],
        "sabotage": {"rtc_wake": "Enabled", "rtc_wake_hour": 5,
                     "restore_ac": "Power On"},
        "goal": {"rtc_wake": "Disabled", "restore_ac": "Power Off"},
        "fail": {"style": "black", "lines": [
            "facilities-log: 05:00  CONF-ROOM-LAPTOP powered ON",
            "  wake source : RTC ALARM (firmware)",
            "",
            "Policy check: restore-on-AC = ?",
        ]},
        "success_lines": [
            "facilities-log: no unattended power events for 7 days.",
            "Policy check: restore-on-AC = Power Off. COMPLIANT.",
        ],
    },
    {
        "id": "ch32_phoenix_fan",
        "title": "Silent Running",
        "tier": "advanced",
        "vendor": "phoenix",
        "briefing": [
            "TICKET #6688 - Presentation laptop (PhoenixBIOS). The",
            "previous presenter silenced 'that annoying fan noise'",
            "minutes before going on stage. The laptop now powers off",
            "mid-presentation with a temperature error.",
            "",
            "Check the hardware health page before returning it.",
        ],
        "hints": [],
        "sabotage": {"cpu_fan_profile": "Disabled"},
        "goal": {"cpu_fan_profile": ["Standard", "Silent", "Turbo"]},
        "fail": {"style": "thermtrip", "lines": [
            "CPU Over Temperature Error!",
            "CPU Fan Error!",
            "",
            "The system reached the processor thermal trip point",
            "and shut itself down.",
            "",
            "Press F1 to Resume",
        ]},
        "success_lines": [
            "Hardware Monitor",
            "",
            "  CPU Temperature : +47.0 C",
            "  CPU Fan Speed   : 830 RPM (Silent profile is fine too)",
            "",
            "The presentation survives past slide 4 this time.",
        ],
        "hw_info": {
            "cpu_temp": {"by": "cpu_fan_profile",
                         "map": {"Disabled": "+97.0 C"},
                         "default": "+47.0 C"},
        },
    },
    {
        "id": "ch33_cmos_battery",
        "title": "The Machine That Forgets",
        "tier": "advanced",
        "vendor": "award",
        "cpu_brand": "amd",
        "briefing": [
            "TICKET #6710 - Workshop classic: an Award-era tower that",
            "spent four years in a damp basement. The owner says they",
            "'fix the BIOS every morning' -- clock, boot order, all of",
            "it -- and by the next day it has forgotten everything.",
            "POST complains about a CMOS checksum error.",
            "",
            "Your bench toolbox is stocked. Use it if the firmware",
            "settings alone don't stick.",
        ],
        "hints": [
            "Whatever you save is gone after the next power cycle. "
            "Firmware settings live in battery-backed CMOS RAM...",
            "Check VBAT on the PC HEALTH STATUS page: 1.9V is a dead "
            "battery. Press B at the briefing screen to fit a fresh "
            "CR2032, then fix the clock and boot order again.",
        ],
        "sabotage": {"_time_offset_s": -94608000, "boot1": NIC_IPV4},
        "goal": {"boot1": WINDOWS_SSD},
        "goal_offset": {"max_abs_days": 1},
        "hw_fault": "cmos_battery",
        "bench": ["replace_battery"],
        "required_actions": ["replace_battery"],
        "hw_info": {"vbat": "+1.92 V  (LOW)"},
        "cmos_checksum_lines": [
            (3450, "CMOS checksum error - Defaults loaded"),
            (3560, "Press F1 to continue, DEL to enter SETUP"),
        ],
        "fail": {"style": "black", "lines": [
            "CMOS checksum error - Defaults loaded",
            "",
            "DISK BOOT FAILURE, INSERT SYSTEM DISK AND PRESS ENTER",
            "",
            "(the clock is wrong again and the boot order has reset:",
            " the firmware forgot everything over the power cycle)",
        ]},
        "success_lines": [
            "Award Modular BIOS v6.00PG",
            "CMOS checksum OK. RTC holds across power cycles.",
            "",
            "Windows Boot Manager",
            "  Booting Windows...",
            "",
            "Fixed once, fixed forever. The way it should be.",
        ],
    },
    {
        "id": "ch34_novideo",
        "title": "Three Short Beeps",
        "tier": "advanced",
        "briefing": [
            "TICKET #6755 - DOA tower from the gaming club. Power LED",
            "on, fans spinning, screen pitch black. The board repeats",
            "three short beeps. The owner admits they 'tuned the RAM",
            "for more FPS' the night before it died.",
            "",
            "You can't reach Setup on a machine with no video. Work",
            "the problem from the bench, then verify your fix by",
            "entering Setup and saving once video is back.",
        ],
        "hints": [
            "Three short beeps on an AMI board: memory failure before",
            "video initialization. The bad RAM profile is stored in "
            "NVRAM -- and NVRAM can be cleared without video. Press J "
            "at the briefing screen to short the CLR_CMOS jumper.",
        ],
        "sabotage": {"xmp": "Profile 2"},
        "goal": {},
        "bench": ["clear_cmos"],
        "required_actions": ["clear_cmos"],
        "post_variant": {"variant": "no_video", "beep": "memory_fail",
                         "until_action": "clear_cmos",
                         "no_video_hint":
                         "(no video -- the board repeats three short "
                         "beeps)"},
        "fail": {"style": "black", "lines": [
            "(still no video. Three short beeps, a pause, three short",
            " beeps again. The memory controller never gets past",
            " training with the stored profile.)",
        ]},
        "success_lines": [
            "AMIBIOS(C)2019 American Megatrends, Inc.",
            "Memory Testing : 16384 MB OK  (defaults loaded)",
            "",
            "Video signal restored. POST complete.",
            "The gaming club owes you a pizza.",
        ],
    },
]
