"""Protect the 16 GB development host before browser/build acceptance tests."""

import re
from pathlib import Path

MIN_AVAILABLE_KIB = 3 * 1024 * 1024
MAX_MEMORY_PRESSURE_AVG10 = 5.0


def _mem_available_kib() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1])
    raise RuntimeError("MemAvailable is not present in /proc/meminfo")


def _memory_pressure_avg10() -> float:
    pressure_path = Path("/proc/pressure/memory")
    if not pressure_path.exists():
        return 0.0
    match = re.search(
        r"^some\s+avg10=([0-9.]+)", pressure_path.read_text(), re.MULTILINE
    )
    return float(match.group(1)) if match else 0.0


def main() -> int:
    available = _mem_available_kib()
    pressure = _memory_pressure_avg10()
    if available < MIN_AVAILABLE_KIB:
        print(
            "Resource gate failed: less than 3 GiB MemAvailable; "
            "heavy browser/build checks must not start"
        )
        return 1
    if pressure > MAX_MEMORY_PRESSURE_AVG10:
        print(
            f"Resource gate failed: memory pressure avg10 is {pressure:.2f}, "
            f"above {MAX_MEMORY_PRESSURE_AVG10:.2f}"
        )
        return 1
    print(
        f"Resource gate passed: {available / 1024 / 1024:.1f} GiB available, "
        f"memory pressure avg10={pressure:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
