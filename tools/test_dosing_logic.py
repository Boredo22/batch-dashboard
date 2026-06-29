#!/usr/bin/env python3
"""
Tests for dosing_job pure logic + a full simulated batch run.

Runs without any hardware: the pure decision helpers import nothing from the
hardware layer, and the end-to-end run uses an injected FakeHardware that
simulates the tank (filling, EC rising with nute doses, pH dropping with acid).

    python tools/test_dosing_logic.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dosing_job as dj
from dosing_job import (
    ec_nutrients, ec_bulk_doses, ec_increment_doses, ph_bulk_ml, ph_increment_ml,
    ph_hard_cap_ml, ec_trim_action, ph_trim_action, BatchConfig, BatchDosingJob,
)

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}")


# ---------------------------------------------------------------------------
# Pure decision helpers
# ---------------------------------------------------------------------------
def test_pure():
    print("pure decision helpers:")
    recipe = {"Veg A": 30, "Veg B": 30, "pH Down": 0.5, "Runclean": 0.2}

    check("ec_nutrients excludes pH Down", set(ec_nutrients(recipe)) == {"Veg A", "Veg B", "Runclean"})
    check("ec_bulk is 85% of recipe*gal", abs(ec_bulk_doses(recipe, 80)["Veg A"] - 30 * 80 * 0.85) < 1e-6)
    check("ec_increment is 5% of recipe*gal", abs(ec_increment_doses(recipe, 80)["Veg A"] - 30 * 80 * 0.05) < 1e-6)
    check("ph_bulk uses recipe pH Down (0.5/gal)", abs(ph_bulk_ml(recipe, 80) - 40) < 1e-6)
    check("ph_increment 0.05/gal", abs(ph_increment_ml(80) - 4) < 1e-6)
    check("ph_hard_cap 1.2/gal", abs(ph_hard_cap_ml(80) - 96) < 1e-6)

    # EC dosed UP
    check("EC within tol -> done", ec_trim_action(2.18, 2.2, 0.05) == "done")
    check("EC low -> dose", ec_trim_action(2.0, 2.2, 0.05) == "dose")
    check("EC high -> overshoot", ec_trim_action(2.4, 2.2, 0.05) == "overshoot")
    check("EC no reading -> error", ec_trim_action(None, 2.2, 0.05) == "error")

    # pH dosed DOWN only
    check("pH within tol -> done", ph_trim_action(6.25, 6.2, 0.1) == "done")
    check("pH high -> dose", ph_trim_action(6.8, 6.2, 0.1) == "dose")
    check("pH too low -> overshoot", ph_trim_action(6.0, 6.2, 0.1) == "overshoot")
    check("pH no reading -> error", ph_trim_action(None, 6.2, 0.1) == "error")


# ---------------------------------------------------------------------------
# Fake hardware for a full simulated run
# ---------------------------------------------------------------------------
class FakeHardware:
    """Simulates one tank: fill flow, EC rising with nute ml, pH dropping with acid ml."""

    def __init__(self, pump_ids):
        import threading
        self._lock = threading.Lock()            # Veg A/B dose on concurrent threads
        self.pump_ids = pump_ids                 # {name: pid}
        self.id_to_name = {pid: n for n, pid in pump_ids.items()}
        self.gallons = 0.0
        self.fill_step = 8.0                     # 8 gal per poll (mimics 8 gpm)
        self.target = 0.0
        self.filling = False
        self.base_ec = 0.30
        self.ec_ml = 0.0                         # cumulative EC-nutrient ml
        self.k_ec = 0.000429                     # EC per ml (tuned so bulk lands just under target)
        self.ph = 7.0
        self.k_ph = 0.01                         # pH drop per ml pH Down
        self.relays = {}

    # relays / flow
    def control_relay(self, rid, on):
        self.relays[rid] = bool(on)
        return True

    def start_flow(self, fid, gallons):
        self.target = float(gallons)
        self.gallons = 0.0
        self.filling = True
        return True

    def stop_flow(self, fid):
        self.filling = False
        return True

    def get_flow_status(self, fid):
        if self.filling and self.gallons < self.target:
            self.gallons = min(self.target, self.gallons + self.fill_step)
        return {"current_gallons": self.gallons, "target_gallons": self.target,
                "status": 1 if self.filling else 0}

    # pumps
    def dispense_pump(self, pid, ml):
        name = self.id_to_name.get(pid, "")
        with self._lock:
            if name == "pH Down":
                self.ph -= self.k_ph * ml
            else:
                self.ec_ml += ml
        return True

    def get_pump_status(self, pid):
        return {"is_dispensing": False}          # always "done" -> fast waits

    def stop_pump(self, pid):
        return True

    # sensors
    def read_ec_ph_sensors(self):
        with self._lock:
            ec = self.base_ec + self.k_ec * self.ec_ml
            ph = self.ph
        return {"success": True, "ec": round(ec, 2), "ph": round(ph, 2)}


def run_job(cfg, fake, timeout=20.0):
    # Speed everything up so the test runs in well under a second.
    dj.SETTLE_SECONDS = 0
    dj.FILL_POLL_SECONDS = 0.0
    dj.PUMP_ML_PER_MIN = 1e9
    dj.PUMP_WAIT_BUFFER_SECONDS = 0.0

    job = BatchDosingJob(cfg, hw=fake)
    job.start()
    deadline = time.time() + timeout
    while time.time() < deadline:
        if job.state in dj.TERMINAL_STATES or job.state == dj.S_NEEDS_OPERATOR:
            break
        time.sleep(0.02)
    return job


def test_full_run_converges():
    print("full simulated batch run (should COMPLETE):")
    pump_ids = {"Veg A": 1, "Veg B": 2, "Runclean": 7, "pH Down": 8}
    recipe = {"Veg A": 30, "Veg B": 30, "Runclean": 0.2, "pH Down": 0.5}
    cfg = BatchConfig(tank_id=1, target_gallons=80, recipe=recipe, pump_ids=pump_ids,
                      fill_relay=1, mix_relays=[4, 7], flow_meter_id=1,
                      ec_target=2.2, ph_target=6.2)
    fake = FakeHardware(pump_ids)
    job = run_job(cfg, fake)
    snap = job.snapshot()
    print(f"    final state={snap['state']} ec={snap['ec']} ph={snap['ph']} "
          f"ec_iters={snap['ec_iterations']} ph_iters={snap['ph_iterations']} "
          f"vol={snap['volume_gallons']}")
    check("reached COMPLETE", snap["state"] == dj.S_COMPLETE)
    check("filled to target", snap["volume_gallons"] == 80)
    check("EC within tolerance", snap["ec"] is not None and abs(snap["ec"] - 2.2) <= 0.05 + 1e-9)
    check("pH at/under target+tol", snap["ph"] is not None and snap["ph"] <= 6.2 + 0.1 + 1e-9)
    check("circ pump left OFF after complete", snap["circ_running"] is False)


def test_ph_cap_holds_for_operator():
    print("alkaline water that won't drop (should NEEDS_OPERATOR at acid cap):")
    pump_ids = {"Veg A": 1, "Veg B": 2, "pH Down": 8}
    recipe = {"Veg A": 30, "Veg B": 30, "pH Down": 0.5}
    cfg = BatchConfig(tank_id=1, target_gallons=80, recipe=recipe, pump_ids=pump_ids,
                      fill_relay=1, mix_relays=[4, 7], ec_target=2.2, ph_target=6.2)
    fake = FakeHardware(pump_ids)
    fake.k_ph = 0.0001          # acid barely moves pH -> can't reach target before cap
    job = run_job(cfg, fake)
    snap = job.snapshot()
    print(f"    final state={snap['state']} ph={snap['ph']} ph_dosed_ml={snap['ph_dosed_ml']} msg={snap['message']!r}")
    check("parked in NEEDS_OPERATOR", snap["state"] == dj.S_NEEDS_OPERATOR)
    check("held on the pH/acid cap path", "cap" in snap["message"].lower() and snap["ph_dosed_ml"] > 0)
    check("did not exceed hard cap", snap["ph_dosed_ml"] <= ph_hard_cap_ml(80) + 1e-6)
    check("circ left RUNNING on hold", snap["circ_running"] is True)
    check("suggestion present", bool(snap["suggestion"]))


def test_target_below_prime_rejected():
    print("target below 20 gal prime (should NEEDS_OPERATOR immediately):")
    pump_ids = {"Veg A": 1, "pH Down": 8}
    recipe = {"Veg A": 30, "pH Down": 0.5}
    cfg = BatchConfig(tank_id=3, target_gallons=15, recipe=recipe, pump_ids=pump_ids,
                      fill_relay=3, mix_relays=[6, 9])
    fake = FakeHardware(pump_ids)
    job = run_job(cfg, fake)
    snap = job.snapshot()
    print(f"    final state={snap['state']} msg={snap['message']!r}")
    check("rejected below prime", snap["state"] == dj.S_NEEDS_OPERATOR)


if __name__ == "__main__":
    test_pure()
    test_full_run_converges()
    test_ph_cap_holds_for_operator()
    test_target_below_prime_rejected()
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
