"""Vendor registry: each vendor exposes draw functions, palette, POST data.

A vendor is a dict (duck-typed) holding callables and data; no ABC formality.
Lookup with `vendors.get("ami")` and dispatch by key.

Add a new vendor: import its module here and register it in VENDORS.
"""

from vendors import ami as _ami
from vendors import award as _award
from vendors import efi as _efi


VENDORS = {
    "ami": _ami.spec,
    "award": _award.spec,
    "efi": _efi.spec,
}


def get(name):
    """Return the vendor spec dict. Falls back to AMI if name is unknown."""
    return VENDORS.get(name, VENDORS["ami"])


def ids():
    return list(VENDORS.keys())
