"""Data-driven definitions of the Aptio setup pages.

Item schema:
  type:       info | option | numeric | datetime | password | submenu | action | blank
  id:         unique key for persisted items (option/numeric/password/datetime)
  label:      left-pane text ("" for blank); info items with no value act as headers
  value:      static right-column text (info)
  dynamic:    name of a model-resolved dynamic value (info)
  values:     list of strings (option)
  default:    index into values (option) or int (numeric)
  min/max:    bounds (numeric)
  help:       right-pane help text for the selected item
  disabled:   always grayed
  depends_on: (item_id, required_value) -> grayed unless satisfied
  items:      children (submenu)
  action:     action id (action)
"""

ENABLED_DISABLED = ["Enabled", "Disabled"]
DISABLED_ENABLED = ["Disabled", "Enabled"]

BOOT_DEVICES = [
    "Windows Boot Manager (Samsung SSD 970 EVO Plus 1TB)",
    "UEFI: SanDisk Ultra USB 3.0 1.00",
    "Onboard NIC (IPV4)",
    "Onboard NIC (IPV6)",
    "Disabled",
]

NAV_HELP = ("←→: Select Screen  ↑↓: Select Item  Enter: Select  "
            "+/-: Change Opt.")


def blank():
    return {"type": "blank", "label": ""}


def header(label):
    return {"type": "info", "label": label}


def info(label, value, help_=""):
    return {"type": "info", "label": label, "value": value, "help": help_}


MAIN_PAGE = {
    "id": "main", "title": "Main",
    "items": [
        header("BIOS Information"),
        info("BIOS Vendor", "American Megatrends"),
        info("Core Version", "5.14"),
        info("Compliancy", "UEFI 2.7; PI 1.6"),
        info("Project Version", "Z390M 2.60"),
        info("Build Date and Time", "04/12/2019 14:33:08"),
        blank(),
        header("Processor Information"),
        info("Brand String", "Intel(R) Core(TM) i7-9700K"),
        info("Frequency", "3600 MHz"),
        info("Processor Cores", "8"),
        info("Microcode Revision", "B4"),
        blank(),
        header("Memory Information"),
        info("Total Memory", "16384 MB"),
        {"type": "info", "label": "Memory Frequency",
         "dynamic": "hw:dram_freq_now"},
        blank(),
        {"type": "option", "id": "language", "label": "System Language",
         "values": ["English"], "default": 0,
         "help": "Choose the system default language."},
        blank(),
        {"type": "datetime", "id": "sys_date", "label": "System Date",
         "help": "Set the Date. Use Tab to switch between Date elements.\n"
                 "Default Ranges:\nYear: 1998-9999\nMonths: 1-12\n"
                 "Days: Dependent on month."},
        {"type": "datetime", "id": "sys_time", "label": "System Time",
         "help": "Set the Time. Use Tab to switch between Time elements."},
        blank(),
        info("Access Level", "Administrator"),
    ],
}

OC_PAGE = {
    "id": "oc", "title": "Ai Tweaker",
    "items": [
        header("Memory Overclocking"),
        blank(),
        {"type": "info", "label": "Target DRAM Speed",
         "dynamic": "hw:target_dram"},
        blank(),
        {"type": "option", "id": "xmp", "label": "XMP (Extreme Memory Profile)",
         "values": ["Disabled", "Profile 1", "Profile 2"], "default": 0,
         "help": "Load the DIMM's factory overclock profile. Profile 1: "
                 "3200 MT/s 1.35V. Profile 2: 3600 MT/s 1.45V. Profiles "
                 "beyond the memory controller's comfort zone may need "
                 "manual voltage and command rate tuning to train."},
        {"type": "option", "id": "dram_freq", "label": "DRAM Frequency",
         "values": ["Auto", "2133 MHz", "2666 MHz", "3200 MHz", "3600 MHz"],
         "default": 0,
         "help": "Force a memory operating frequency. Auto follows XMP or "
                 "JEDEC. Frequencies above 3200 MHz are not guaranteed to "
                 "train on this memory controller without extra voltage."},
        {"type": "option", "id": "cmd_rate", "label": "DRAM Command Rate",
         "values": ["Auto", "1T", "2T"], "default": 0,
         "help": "Delay between DRAM chip select and command. 2T relaxes "
                 "signal timing and helps high-frequency stability at a "
                 "small performance cost."},
        {"type": "option", "id": "dram_volt", "label": "DRAM Voltage",
         "values": ["Auto", "1.20V", "1.35V", "1.45V"], "default": 0,
         "help": "DRAM supply voltage. High-frequency profiles typically "
                 "require 1.35V or more to pass memory training."},
        blank(),
        header("CPU Overclocking"),
        blank(),
        {"type": "numeric", "id": "cpu_ratio", "label": "CPU Core Ratio",
         "min": 8, "max": 60, "default": 36,
         "help": "CPU multiplier applied to the 100 MHz base clock. "
                 "Ratios above stock may require a positive core voltage "
                 "offset to remain stable."},
        {"type": "option", "id": "vcore_offset", "label": "CPU Core Voltage Offset",
         "values": ["Auto", "-0.10V", "-0.05V", "+0.00V", "+0.05V",
                    "+0.10V", "+0.15V", "+0.20V"], "default": 0,
         "help": "Offset added to the CPU core voltage. Higher ratios "
                 "need more voltage; too little causes watchdog resets, "
                 "too much raises temperatures."},
    ],
}

CPU_CONFIG = {
    "type": "submenu", "label": "CPU Configuration",
    "help": "CPU Configuration Parameters",
    "items": [
        header("CPU Configuration"),
        blank(),
        {"type": "info", "label": "Type", "dynamic": "cpu_brand:type"},
        info("ID", "0x906EC"),
        {"type": "info", "label": "Speed", "dynamic": "cpu_brand:speed"},
        info("L1 Data Cache", "32 KB x 8"),
        info("L1 Instruction Cache", "32 KB x 8"),
        info("L2 Cache", "256 KB x 8"),
        info("L3 Cache", "12 MB"),
        {"type": "info", "label": "VMX",
         "label_variants": {"intel": "VMX", "amd": "SVM"},
         "dynamic": "cpu_brand:vmx"},
        info("SMX/TXT", "Supported"),
        blank(),
        {"type": "option", "id": "ht", "label": "Hyper-Threading",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Enabled for Windows XP and Linux (OS optimized for "
                 "Hyper-Threading Technology) and Disabled for other OS (OS "
                 "not optimized for Hyper-Threading Technology)."},
        {"type": "option", "id": "active_cores", "label": "Active Processor Cores",
         "values": ["All", "1", "2", "3", "4", "5", "6", "7"], "default": 0,
         "help": "Number of cores to enable in each processor package."},
        {"type": "option", "id": "vmx", "label": "Intel (VMX) Virtualization Technology",
         "label_variants": {
             "intel": "Intel (VMX) Virtualization Technology",
             "amd":   "AMD-V (SVM Mode)"},
         "values": ENABLED_DISABLED, "default": 0,
         "help": "When enabled, a VMM can utilize the additional hardware "
                 "capabilities provided by Vanderpool Technology."},
        {"type": "option", "id": "speedstep", "label": "Intel(R) SpeedStep(tm)",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Allows more than two frequency ranges to be supported."},
        {"type": "option", "id": "turbo", "label": "Turbo Mode",
         "values": ENABLED_DISABLED, "default": 0,
         "depends_on": ("speedstep", "Enabled"),
         "help": "Enable/Disable processor Turbo Mode (requires EMTTM enabled "
                 "too)."},
        {"type": "option", "id": "cstates", "label": "C states",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Enable/Disable CPU Power Management. Allows CPU to go to C "
                 "states when it's not 100% utilized."},
        {"type": "option", "id": "aes", "label": "AES",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Enable/Disable AES (Advanced Encryption Standard)."},
    ],
}

SATA_CONFIG = {
    "type": "submenu", "label": "SATA And RST Configuration",
    "help": "SATA Device Options Settings",
    "items": [
        header("SATA And RST Configuration"),
        blank(),
        {"type": "option", "id": "sata_enable", "label": "SATA Controller(s)",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Enable/Disable SATA Device."},
        {"type": "option", "id": "sata_mode", "label": "SATA Mode Selection",
         "values": ["AHCI", "Intel RST Premium With Intel Optane System "
                    "Acceleration"], "default": 0,
         "depends_on": ("sata_enable", "Enabled"),
         "help": "Determines how SATA controller(s) operate."},
        {"type": "option", "id": "sata_lpm", "label": "Aggressive LPM Support",
         "values": ENABLED_DISABLED, "default": 0,
         "depends_on": ("sata_enable", "Enabled"),
         "help": "Enable PCH to aggressively enter link power state."},
        {"type": "option", "id": "m2_mode", "label": "M.2_2 Configuration",
         "values": ["Auto", "PCIe", "SATA"], "default": 0,
         "help": "Operating mode of the M.2_2 socket. The socket shares "
                 "bandwidth with Serial ATA Port 1: when set to SATA, "
                 "Serial ATA Port 1 is disabled."},
        blank(),
        info("Serial ATA Port 0", "Samsung SSD 860  (500.1GB)"),
        info("  Software Preserve", "SUPPORTED"),
        {"type": "option", "id": "sata_p0_hotplug", "label": "  Hot Plug",
         "values": DISABLED_ENABLED, "default": 0,
         "help": "Designates this port as Hot Pluggable."},
        info("Serial ATA Port 1", "ST2000DM008-2FR1 (2000.3GB)"),
        info("  Software Preserve", "SUPPORTED"),
        {"type": "option", "id": "sata_p1_hotplug", "label": "  Hot Plug",
         "values": DISABLED_ENABLED, "default": 0,
         "depends_on": ("m2_mode", ["Auto", "PCIe"]),
         "help": "Designates this port as Hot Pluggable. Unavailable "
                 "while M.2_2 is in SATA mode (shared bandwidth)."},
        info("Serial ATA Port 2", "Empty"),
        info("Serial ATA Port 3", "Empty"),
    ],
}

NVME_CONFIG = {
    "type": "submenu", "label": "NVMe Configuration",
    "help": "NVMe Device Options Settings",
    "items": [
        header("NVMe Configuration"),
        blank(),
        info("M.2_1", "Samsung SSD 970 EVO Plus 1TB"),
        info("  Capacity", "1000.2 GB"),
        info("  Namespace 1 Size/Health", "1000.2 GB / Good"),
    ],
}

USB_CONFIG = {
    "type": "submenu", "label": "USB Configuration",
    "help": "USB Configuration Parameters",
    "items": [
        header("USB Configuration"),
        blank(),
        info("USB Module Version", "23"),
        blank(),
        info("USB Controllers:", "1 XHCI"),
        info("USB Devices:", "1 Drive, 1 Keyboard, 1 Mouse, 2 Hubs"),
        blank(),
        {"type": "option", "id": "legacy_usb", "label": "Legacy USB Support",
         "values": ["Enabled", "Disabled", "Auto"], "default": 0,
         "help": "Enables Legacy USB support. AUTO option disables legacy "
                 "support if no USB devices are connected. DISABLE option "
                 "will keep USB devices available only for EFI applications."},
        {"type": "option", "id": "xhci_handoff", "label": "XHCI Hand-off",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "This is a workaround for OSes without XHCI hand-off "
                 "support. The XHCI ownership change should be claimed by "
                 "XHCI driver."},
        {"type": "option", "id": "usb_mass", "label": "USB Mass Storage Driver Support",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Enable/Disable USB Mass Storage Driver Support."},
    ],
}

TPM_CONFIG = {
    "type": "submenu", "label": "Trusted Computing",
    "help": "Trusted Computing Settings",
    "items": [
        header("TPM 2.0 Device Found"),
        info("Firmware Version:", "7.85"),
        info("Vendor:", "IFX"),
        blank(),
        {"type": "option", "id": "tpm_enable", "label": "Security Device Support",
         "values": ["Enable", "Disable"], "default": 0,
         "help": "Enables or Disables BIOS support for security device. O.S. "
                 "will not show Security Device. TCG EFI protocol and INT1A "
                 "interface will not be available."},
        info("Active PCR banks", "SHA256"),
        info("Available PCR banks", "SHA-1, SHA256"),
        blank(),
        {"type": "option", "id": "tpm_pending", "label": "Pending operation",
         "values": ["None", "TPM Clear"], "default": 0,
         "depends_on": ("tpm_enable", "Enable"),
         "help": "Schedule an Operation for the Security Device. NOTE: Your "
                 "Computer will reboot during restart in order to change "
                 "State of Security Device."},
    ],
}

NETWORK_STACK = {
    "type": "submenu", "label": "Network Stack Configuration",
    "help": "Network Stack Settings",
    "items": [
        header("Network Stack Configuration"),
        blank(),
        {"type": "option", "id": "net_stack", "label": "Network Stack",
         "values": DISABLED_ENABLED, "default": 0,
         "help": "Enable/Disable UEFI Network Stack."},
        {"type": "option", "id": "pxe4", "label": "Ipv4 PXE Support",
         "values": DISABLED_ENABLED, "default": 0,
         "depends_on": ("net_stack", "Enabled"),
         "help": "Enable/Disable IPv4 PXE boot support. If disabled, IPv4 "
                 "PXE boot support will not be available."},
        {"type": "option", "id": "pxe6", "label": "Ipv6 PXE Support",
         "values": DISABLED_ENABLED, "default": 0,
         "depends_on": ("net_stack", "Enabled"),
         "help": "Enable/Disable IPv6 PXE boot support. If disabled, IPv6 "
                 "PXE boot support will not be available."},
    ],
}

APM_CONFIG = {
    "type": "submenu", "label": "APM Configuration",
    "help": "Advanced Power Management settings",
    "items": [
        header("APM Configuration"),
        blank(),
        {"type": "option", "id": "restore_ac", "label": "Restore On AC Power Loss",
         "values": ["Power Off", "Power On", "Last State"], "default": 0,
         "help": "System behavior when power is restored after an AC "
                 "power loss."},
        {"type": "option", "id": "erp", "label": "ErP Ready",
         "values": ["Disabled", "Enabled (S4+S5)"], "default": 0,
         "help": "Allows the BIOS to switch off power in S4+S5 to meet "
                 "the ErP requirement. When enabled, Wake on LAN and "
                 "Power On By RTC are not functional in those states."},
        {"type": "option", "id": "rtc_wake", "label": "Power On By RTC",
         "values": DISABLED_ENABLED, "default": 0,
         "help": "Allow the Real-Time Clock alarm to power the system on "
                 "at a scheduled time."},
        {"type": "numeric", "id": "rtc_wake_hour", "label": "RTC Alarm Hour",
         "min": 0, "max": 23, "default": 0,
         "depends_on": ("rtc_wake", "Enabled"),
         "help": "Hour (0-23) at which the RTC alarm powers the system "
                 "on."},
    ],
}

ADVANCED_PAGE = {
    "id": "advanced", "title": "Advanced",
    "items": [
        CPU_CONFIG,
        SATA_CONFIG,
        NVME_CONFIG,
        USB_CONFIG,
        TPM_CONFIG,
        NETWORK_STACK,
        APM_CONFIG,
    ],
}

MONITOR_PAGE = {
    "id": "monitor", "title": "Monitor",
    "items": [
        header("Hardware Monitor"),
        blank(),
        {"type": "info", "label": "CPU Temperature", "dynamic": "hw:cpu_temp"},
        {"type": "info", "label": "Motherboard Temperature",
         "dynamic": "hw:mb_temp"},
        blank(),
        {"type": "info", "label": "CPU Fan Speed", "dynamic": "hw:cpu_fan_rpm"},
        {"type": "info", "label": "Chassis Fan Speed",
         "dynamic": "hw:chassis_fan_rpm"},
        blank(),
        {"type": "info", "label": "CPU Core Voltage", "dynamic": "hw:vcore"},
        {"type": "info", "label": "3.3V Voltage", "dynamic": "hw:v33"},
        {"type": "info", "label": "5V Voltage", "dynamic": "hw:v5"},
        {"type": "info", "label": "12V Voltage", "dynamic": "hw:v12"},
        {"type": "info", "label": "VBAT (CMOS Battery)", "dynamic": "hw:vbat"},
        blank(),
        header("Fan Control"),
        blank(),
        {"type": "option", "id": "cpu_fan_profile", "label": "CPU Fan Profile",
         "values": ["Standard", "Silent", "Turbo", "Disabled"], "default": 0,
         "help": "Fan curve applied to the CPU fan header. Warning: "
                 "'Disabled' stops the CPU fan entirely; the processor "
                 "will overheat under load."},
        {"type": "option", "id": "chassis_fan_profile",
         "label": "Chassis Fan Profile",
         "values": ["Standard", "Silent", "Turbo", "Disabled"], "default": 0,
         "help": "Fan curve applied to the chassis fan headers."},
        {"type": "option", "id": "case_open_warning", "label": "Case Open Warning",
         "values": DISABLED_ENABLED, "default": 0,
         "help": "Halt POST with a warning when the chassis intrusion "
                 "header reports the case was opened."},
    ],
}

GRAPHICS_CONFIG = {
    "type": "submenu", "label": "Graphics Configuration",
    "help": "Graphics Configuration",
    "items": [
        header("Graphics Configuration"),
        blank(),
        {"type": "option", "id": "primary_display", "label": "Primary Display",
         "values": ["Auto", "IGFX", "PEG", "PCI"], "default": 0,
         "help": "Select which of IGFX/PEG/PCI Graphics device should be "
                 "Primary Display Or select SG for Switchable Gfx."},
        {"type": "option", "id": "igfx", "label": "Internal Graphics",
         "values": ["Auto", "Disabled", "Enabled"], "default": 0,
         "help": "Keep IGFX enabled based on the setup options."},
        {"type": "option", "id": "dvmt_pre", "label": "DVMT Pre-Allocated",
         "values": ["32M", "64M", "96M", "128M"], "default": 1,
         "help": "Select DVMT 5.0 Pre-Allocated (Fixed) Graphics Memory size "
                 "used by the Internal Graphics Device."},
        {"type": "option", "id": "dvmt_total", "label": "DVMT Total Gfx Mem",
         "values": ["128M", "256M", "MAX"], "default": 1,
         "help": "Select DVMT 5.0 Total Graphic Memory size used by the "
                 "Internal Graphics Device."},
    ],
}

MEMORY_CONFIG = {
    "type": "submenu", "label": "Memory Configuration",
    "help": "Memory Configuration Parameters",
    "items": [
        header("Memory Configuration"),
        blank(),
        info("Memory RC Version", "0.7.1.80"),
        {"type": "info", "label": "Memory Frequency",
         "dynamic": "hw:dram_freq_now"},
        info("tCL-tRCD-tRP-tRAS", "19-19-19-43"),
        blank(),
        info("DIMM_A1", "Populated & Enabled"),
        info("  Size", "8192 MB (DDR4)"),
        info("DIMM_B1", "Populated & Enabled"),
        info("  Size", "8192 MB (DDR4)"),
    ],
}

SA_CONFIG = {
    "type": "submenu", "label": "System Agent (SA) Configuration",
    "help": "System Agent (SA) Parameters",
    "items": [
        header("System Agent (SA) Configuration"),
        blank(),
        info("SA PCIe Code Version", "7.0.105.55"),
        {"type": "info", "label": "VT-d",
         "label_variants": {"intel": "VT-d", "amd": "IOMMU"},
         "dynamic": "cpu_brand:vtd"},
        blank(),
        {"type": "option", "id": "vtd", "label": "VT-d",
         "label_variants": {"intel": "VT-d", "amd": "IOMMU"},
         "values": ENABLED_DISABLED, "default": 0,
         "help": "VT-d capability."},
        {"type": "option", "id": "above_4g", "label": "Above 4GB MMIO BIOS assignment",
         "values": DISABLED_ENABLED, "default": 0,
         "help": "Enable/Disable above 4GB MemoryMappedIO BIOS assignment. "
                 "This is enabled automatically when Aperture Size is set to "
                 "2048MB."},
        blank(),
        GRAPHICS_CONFIG,
        MEMORY_CONFIG,
    ],
}

PCH_CONFIG = {
    "type": "submenu", "label": "PCH-IO Configuration",
    "help": "PCH Parameters",
    "items": [
        header("PCH-IO Configuration"),
        blank(),
        {"type": "option", "id": "pcie_clock_gating", "label": "PCI Express Clock Gating",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Enable or disable PCI Express Clock Gating for each root "
                 "port."},
        {"type": "option", "id": "pch_lan", "label": "PCH LAN Controller",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Enable or disable onboard NIC."},
        {"type": "option", "id": "wake_on_lan", "label": "Wake on LAN Enable",
         "values": ENABLED_DISABLED, "default": 0,
         "depends_on": ("pch_lan", "Enabled"),
         "help": "Enable/Disable integrated LAN to wake the system."},
        {"type": "option", "id": "hd_audio", "label": "HD Audio",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Control Detection of the HD-Audio device. Disabled = HDA "
                 "will be unconditionally disabled. Enabled = HDA will be "
                 "unconditionally enabled."},
        {"type": "option", "id": "usb3_xhci", "label": "USB3.0 (XHCI) Controller",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Enable or disable the XHCI controller."},
    ],
}

CHIPSET_PAGE = {
    "id": "chipset", "title": "Chipset",
    "items": [
        SA_CONFIG,
        PCH_CONFIG,
    ],
}

KEY_MANAGEMENT = {
    "type": "submenu", "label": "Key Management",
    "help": "Enables expert users to modify Secure Boot Policy variables "
            "without full authentication.",
    "depends_on": ("sb_mode", "Custom"),
    "items": [
        header("Key Management"),
        blank(),
        info("Vendor Keys", "Valid"),
        blank(),
        {"type": "action", "action": "factory_keys",
         "label": "Restore Factory Keys",
         "help": "Force System to User Mode. Install factory default Secure "
                 "Boot key databases."},
        {"type": "action", "action": "clear_keys",
         "label": "Reset To Setup Mode",
         "help": "Delete all Secure Boot key databases from NVRAM."},
        blank(),
        info("Platform Key (PK)", "Updated"),
        info("Key Exchange Keys (KEK)", "Updated"),
        info("Authorized Signatures (db)", "Updated"),
        info("Forbidden Signatures (dbx)", "Updated"),
    ],
}

SECURE_BOOT = {
    "type": "submenu", "label": "Secure Boot",
    "help": "Customizable Secure Boot settings",
    "items": [
        header("Secure Boot"),
        blank(),
        info("System Mode", "User"),
        blank(),
        {"type": "option", "id": "secure_boot", "label": "Secure Boot",
         "values": ENABLED_DISABLED, "default": 0,
         "help": "Secure Boot feature is Active if Secure Boot is Enabled, "
                 "Platform Key(PK) is enrolled and the System is in User "
                 "mode. The mode change requires platform reset."},
        blank(),
        {"type": "option", "id": "sb_mode", "label": "Secure Boot Mode",
         "values": ["Standard", "Custom"], "default": 0,
         "help": "Secure Boot mode options: Standard or Custom. In Custom "
                 "mode, Secure Boot Policy variables can be configured by a "
                 "physically present user without full authentication."},
        KEY_MANAGEMENT,
    ],
}

SECURITY_PAGE = {
    "id": "security", "title": "Security",
    "items": [
        header("Password Description"),
        blank(),
        info("If ONLY the Administrator's password is set,", ""),
        info("then this only limits access to Setup and is", ""),
        info("only asked for when entering Setup.", ""),
        info("If ONLY the User's password is set, then this", ""),
        info("is a power on password and must be entered to", ""),
        info("boot or enter Setup. In Setup the User will", ""),
        info("have Administrator rights.", ""),
        blank(),
        {"type": "info", "label": "Administrator Password",
         "dynamic": "pwd_status:admin_pwd"},
        {"type": "info", "label": "User Password",
         "dynamic": "pwd_status:user_pwd"},
        blank(),
        {"type": "password", "id": "admin_pwd", "label": "Administrator Password",
         "help": "Set Administrator Password"},
        {"type": "password", "id": "user_pwd", "label": "User Password",
         "help": "Set User Password"},
        blank(),
        SECURE_BOOT,
    ],
}

CSM_CONFIG = {
    "type": "submenu", "label": "CSM (Compatibility Support Module)",
    "help": "CSM configuration: Enable/Disable, Option ROM execution "
            "settings, etc.",
    "items": [
        header("Compatibility Support Module Configuration"),
        blank(),
        {"type": "option", "id": "csm", "label": "Launch CSM",
         "values": DISABLED_ENABLED, "default": 0,
         "depends_on": ("secure_boot", "Disabled"),
         "help": "This option is disabled if Secure Boot is Enabled."},
        blank(),
        {"type": "option", "id": "csm_boot_dev", "label": "Boot Device Control",
         "values": ["UEFI and Legacy", "Legacy only", "UEFI only"], "default": 0,
         "depends_on": ("csm", "Enabled"),
         "help": "Allows you to select the type of devices that you want to "
                 "boot up."},
        {"type": "option", "id": "csm_storage", "label": "Boot from Storage Devices",
         "values": ["Both, Legacy OpROM first", "Both, UEFI driver first",
                    "Legacy OpROM first", "UEFI driver first"], "default": 1,
         "depends_on": ("csm", "Enabled"),
         "help": "Allows you to select the type of storage devices that you "
                 "want to launch."},
        {"type": "option", "id": "csm_pcie", "label": "Boot from PCI-E Expansion Devices",
         "values": ["Legacy OpROM first", "UEFI driver first"], "default": 1,
         "depends_on": ("csm", "Enabled"),
         "help": "Allows you to select the type of PCI-E expansion devices "
                 "that you want to launch."},
    ],
}

BOOT_PAGE = {
    "id": "boot", "title": "Boot",
    "items": [
        header("Boot Configuration"),
        {"type": "numeric", "id": "setup_timeout", "label": "Setup Prompt Timeout",
         "default": 1, "min": 1, "max": 30,
         "help": "Number of seconds to wait for setup activation key. "
                 "65535(0xFFFF) means indefinite waiting."},
        {"type": "option", "id": "numlock", "label": "Bootup NumLock State",
         "values": ["On", "Off"], "default": 0,
         "help": "Select the keyboard NumLock state."},
        {"type": "option", "id": "quiet_boot", "label": "Quiet Boot",
         "values": DISABLED_ENABLED, "default": 1,
         "help": "Enables or disables Quiet Boot option."},
        {"type": "option", "id": "fast_boot", "label": "Fast Boot",
         "values": DISABLED_ENABLED, "default": 0,
         "help": "Enables or disables boot with initialization of a minimal "
                 "set of devices required to launch active boot option. Has "
                 "no effect for BBS boot options."},
        blank(),
        header("Boot Option Priorities"),
        {"type": "option", "id": "boot1", "label": "Boot Option #1",
         "values": BOOT_DEVICES, "default": 0,
         "help": "Sets the system boot order."},
        {"type": "option", "id": "boot2", "label": "Boot Option #2",
         "values": BOOT_DEVICES, "default": 1,
         "help": "Sets the system boot order."},
        {"type": "option", "id": "boot3", "label": "Boot Option #3",
         "values": BOOT_DEVICES, "default": 2,
         "help": "Sets the system boot order."},
        blank(),
        CSM_CONFIG,
    ],
}

SAVE_EXIT_PAGE = {
    "id": "save_exit", "title": "Save & Exit",
    "items": [
        header("Save Options"),
        {"type": "action", "action": "save_exit",
         "label": "Save Changes and Exit",
         "help": "Exit system setup after saving the changes."},
        {"type": "action", "action": "discard_exit",
         "label": "Discard Changes and Exit",
         "help": "Exit system setup without saving any changes."},
        {"type": "action", "action": "save_reset",
         "label": "Save Changes and Reset",
         "help": "Reset the system after saving the changes."},
        {"type": "action", "action": "discard_changes",
         "label": "Discard Changes",
         "help": "Discards changes done so far to any of the setup options."},
        blank(),
        header("Default Options"),
        {"type": "action", "action": "load_defaults",
         "label": "Restore Defaults",
         "help": "Restore/Load Default values for all the setup options."},
        {"type": "action", "action": "save_user_defaults",
         "label": "Save as User Defaults",
         "help": "Save the changes done so far as User Defaults."},
        {"type": "action", "action": "restore_user_defaults",
         "label": "Restore User Defaults",
         "help": "Restore the User Defaults to all the setup options."},
        blank(),
        header("Boot Override"),
        {"type": "action", "action": "boot_override",
         "label": "Windows Boot Manager (Samsung SSD 970 EVO Plus 1TB)",
         "help": "Boot the system from this device immediately, bypassing "
                 "the boot order. The selection is not retained."},
        {"type": "action", "action": "boot_override",
         "label": "UEFI: SanDisk Ultra USB 3.0 1.00",
         "help": "Boot the system from this device immediately, bypassing "
                 "the boot order. The selection is not retained."},
    ],
}

MENU = [MAIN_PAGE, OC_PAGE, ADVANCED_PAGE, CHIPSET_PAGE, SECURITY_PAGE,
        MONITOR_PAGE, BOOT_PAGE, SAVE_EXIT_PAGE]
