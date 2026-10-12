import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import scan_wifi  # noqa: E402


def test_randomized_macs_are_spotted():
    # the "locally administered" bit (0x02 in the first byte) is what phones set
    assert scan_wifi.is_randomized_mac("22:69:A3:E5:F5:1F")
    assert scan_wifi.is_randomized_mac("CA:4D:A1:91:64:19")
    assert not scan_wifi.is_randomized_mac("B4:B0:24:6F:35:40")
    assert not scan_wifi.is_randomized_mac("not a mac")


def test_format_mac():
    assert scan_wifi.format_mac("b4-b0-24-6f-35-40") == "B4:B0:24:6F:35:40"


def test_device_type_guesses():
    assert "Phone" in scan_wifi.guess_device_type("22:69:A3:E5:F5:1F", "", "")
    assert "Router" in scan_wifi.guess_device_type("B4:B0:24:6F:35:40", "_gateway", "TP-LINK")
    assert "Apple" in scan_wifi.guess_device_type("B4:B0:24:6F:35:40", "Kims-iPhone", "")
    assert "Raspberry" in scan_wifi.guess_device_type("B8:27:EB:00:00:01", "", "Raspberry Pi Foundation") \
        or "Linux" in scan_wifi.guess_device_type("B8:27:EB:00:00:01", "", "Raspberry Pi Foundation")
    assert "Unknown" in scan_wifi.guess_device_type("00:11:22:33:44:55", "", "Unknown")
