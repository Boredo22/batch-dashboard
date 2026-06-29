#!/usr/bin/env python3
"""
Server-side closed-loop batch dosing job.

Runs the full fill -> dose -> trim sequence on a background thread so it survives
a browser/tablet disconnect (the old FillTank.svelte ran the loop in the tab).

Design (see project notes):
  P0 PRIME-FILL      fresh-water pump -> flow meter until PRIME_GALLONS (20 gal).
                     The circ/send pump can't run below 20 gal (sucks air), and
                     the peristaltic nute pumps inject *inline* into the circ
                     line, so no dosing is possible until primed.
  P1 FILL + BULK     at 20 gal: start circ pump, keep filling to target AND
                     open-loop bulk-dose the EC nutrients to EC_BULK_FRACTION of
                     recipe concurrently (fresh-water pump is separate, ~8 gpm,
                     so fill hides inside the ~18 min dose). Barrier: volume>=target
                     AND bulk dose done.
  P2 EC TRIM         closed loop: read EC -> if short, dose a small increment ->
                     recirculate/settle -> re-read. Caps on iterations + volume.
  P3 pH DOSE         bulk pH Down to recipe value (~0.5 ml/gal, deliberately under
                     the operator's 0.6-1.0 ml/gal requirement so it can't
                     overshoot), then closed-loop trim down to the pH target with
                     a hard ml/gal cap.
  P4 STABILIZE       final recirc, record EC/pH, stop circ.

EC is trimmed before pH because the nutrients are acidic and pull pH down on
their own -- measuring/trimming pH only makes sense on the fully nutrient-loaded
solution.

Overshoot (EC too high / pH too low) parks the job in NEEDS_OPERATOR with a
suggested fix (add fresh water + proportional nute, or dump-and-refill); v1 does
NOT auto-correct (that is a second coupled control loop). On a hold the
peristaltic pumps and fresh-water fill are stopped but the circ pump is left
running so the operator can add water and have it mix.

The pure decision helpers at the top intentionally import nothing from the
hardware layer, so they can be unit-tested without a Raspberry Pi (see
tools/test_dosing_logic.py). All hardware calls are imported lazily inside the
runner.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS (tunable; sensible starting values)
# =============================================================================

PRIME_GALLONS = 20.0            # firm: circ/send pump needs 20 gal or it pulls air
PUMP_ML_PER_MIN = 110.0         # peristaltic nute pump rate (for time estimates)
MAX_SINGLE_DISPENSE_ML = 2500.0  # EZO single-dispense cap (config.MAX_PUMP_VOLUME_ML)

EC_BULK_FRACTION = 0.85         # open-loop bulk dose = 85% of recipe, then trim up
EC_INCREMENT_FRACTION = 0.05    # each EC trim step adds 5% of recipe
EC_MAX_TOTAL_FRACTION = 1.20    # never dose more than 120% of recipe (runaway guard)
EC_MAX_ITERS = 12

PH_DOWN_NAME = "pH Down"
PH_INCREMENT_ML_PER_GAL = 0.05  # each pH trim step adds 0.05 ml/gal
PH_HARD_CAP_ML_PER_GAL = 1.2    # above the operator's 1.0 ml/gal ceiling -> fault
PH_MAX_ITERS = 15

DEFAULT_EC_TARGET = 2.2
DEFAULT_PH_TARGET = 6.2
DEFAULT_EC_TOL = 0.05
DEFAULT_PH_TOL = 0.1

SETTLE_SECONDS = 45             # recirculate/settle before re-reading a sensor
FILL_POLL_SECONDS = 0.5
PUMP_WAIT_BUFFER_SECONDS = 20.0  # extra slack on top of estimated dispense time


# =============================================================================
# PURE DECISION HELPERS  (no hardware imports -- unit-testable)
# =============================================================================

def ec_nutrients(recipe: Dict[str, float]) -> Dict[str, float]:
    """Recipe entries that drive EC (everything except pH Down), ml-per-gallon."""
    return {n: ml for n, ml in recipe.items() if n != PH_DOWN_NAME and ml > 0}


def scale_doses(per_gallon: Dict[str, float], gallons: float, fraction: float) -> Dict[str, float]:
    """ml-per-gallon -> absolute ml for `gallons`, scaled by `fraction`."""
    return {n: ml * gallons * fraction for n, ml in per_gallon.items()}


def ec_bulk_doses(recipe: Dict[str, float], gallons: float) -> Dict[str, float]:
    return scale_doses(ec_nutrients(recipe), gallons, EC_BULK_FRACTION)


def ec_increment_doses(recipe: Dict[str, float], gallons: float) -> Dict[str, float]:
    return scale_doses(ec_nutrients(recipe), gallons, EC_INCREMENT_FRACTION)


def ph_bulk_ml(recipe: Dict[str, float], gallons: float) -> float:
    """Bulk pH Down = the recipe's pH Down value (the operator's safe 0.5 ml/gal)."""
    return recipe.get(PH_DOWN_NAME, 0.5) * gallons


def ph_increment_ml(gallons: float) -> float:
    return PH_INCREMENT_ML_PER_GAL * gallons


def ph_hard_cap_ml(gallons: float) -> float:
    return PH_HARD_CAP_ML_PER_GAL * gallons


# Float slack so a reading sitting exactly on a tolerance edge counts as in-band
# rather than triggering one needless extra dose (e.g. 2.2 - 0.05 == 2.1500000000000004).
_TOL_EPS = 1e-9


def ec_trim_action(measured: Optional[float], target: float, tol: float) -> str:
    """EC is dosed UP. Returns 'done' | 'dose' | 'overshoot' | 'error'."""
    if measured is None:
        return 'error'
    if measured > target + tol + _TOL_EPS:
        return 'overshoot'      # too strong -- can't remove nutrient
    if measured >= target - tol - _TOL_EPS:
        return 'done'
    return 'dose'


def ph_trim_action(measured: Optional[float], target: float, tol: float) -> str:
    """pH is dosed DOWN only. Returns 'done' | 'dose' | 'overshoot' | 'error'."""
    if measured is None:
        return 'error'
    if measured < target - tol - _TOL_EPS:
        return 'overshoot'      # too acidic -- we only have pH Down
    if measured <= target + tol + _TOL_EPS:
        return 'done'
    return 'dose'


def suggest_ec_dilution(measured: float, target: float, gallons: float) -> str:
    """Fresh water needed to dilute EC from measured down to target (approx)."""
    if measured <= target or target <= 0:
        return "EC within range; no dilution needed."
    add = gallons * (measured / target - 1.0)
    return (f"EC {measured:.2f} > target {target:.2f}. Add ~{add:.0f} gal fresh water "
            f"(plus proportional Veg A/B to hold EC), or dump to ~{gallons/2:.0f} gal "
            f"and re-fill, then re-trim.")


def suggest_ph_raise(measured: float, target: float, gallons: float) -> str:
    """pH dropped below target; only lever is fresh water (~7.5 pH) or dump."""
    return (f"pH {measured:.2f} < target {target:.2f} (overshot down). Add fresh water "
            f"(~7.5 pH) to raise it -- this dilutes EC, so re-trim EC after -- or dump "
            f"to ~{gallons/2:.0f} gal and re-fill/re-dose.")


# =============================================================================
# JOB CONFIG + STATE
# =============================================================================

# State machine values
S_IDLE = 'idle'
S_PRIMING = 'priming'
S_FILL_DOSE = 'filling_dosing'
S_EC_TRIM = 'ec_trim'
S_PH_DOSE = 'ph_dosing'
S_STABILIZE = 'stabilizing'
S_COMPLETE = 'complete'
S_NEEDS_OPERATOR = 'needs_operator'
S_ERROR = 'error'
S_ABORTED = 'aborted'

TERMINAL_STATES = {S_COMPLETE, S_ERROR, S_ABORTED}


@dataclass
class BatchConfig:
    tank_id: int
    target_gallons: float
    recipe: Dict[str, float]            # {nutrient_name: ml_per_gallon}
    pump_ids: Dict[str, int]            # {nutrient_name: pump_id}
    fill_relay: int
    mix_relays: List[int]              # circ/send relay(s) -- must run to dose
    flow_meter_id: int = 1
    ec_target: float = DEFAULT_EC_TARGET
    ph_target: float = DEFAULT_PH_TARGET
    ec_tol: float = DEFAULT_EC_TOL
    ph_tol: float = DEFAULT_PH_TOL
    # Advisory ("coach") mode: the program never actuates valves or pumps. It
    # reads the real sensors (flow / EC / pH) and, at each step, recommends the
    # action it WOULD take and blocks until the operator acknowledges having
    # handled it. Because it re-reads sensors each step, it adapts to whatever
    # the operator actually did.
    advisory: bool = False


class _OperatorHold(Exception):
    def __init__(self, reason: str, suggestion: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.suggestion = suggestion


class _Aborted(Exception):
    pass


# =============================================================================
# THE JOB
# =============================================================================

class BatchDosingJob:
    """One batch run on a background thread. Read `snapshot()` for live status."""

    def __init__(self, cfg: BatchConfig, hw=None):
        self.cfg = cfg
        self.advisory = cfg.advisory
        self._hw = hw                 # injected hardware module (for tests); lazy otherwise
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._ack = threading.Event()  # advisory: operator-acknowledged the recommendation
        self._aborting = False

        self.state = S_IDLE
        self.message = ""
        self.suggestion = ""
        self.pending_action = None     # advisory: {kind, summary, detail, payload}
        self.volume_gallons = 0.0
        self.ec = None
        self.ph = None
        self.ec_dosed_fraction = 0.0
        self.ph_dosed_ml = 0.0
        self.ec_iter = 0
        self.ph_iter = 0
        self.started_at = None
        self.circ_on = False

    # ---- hardware accessor (lazy import so pure helpers stay importable) ----
    @property
    def hw(self):
        if self._hw is None:
            from hardware import hardware_comms as _hc
            self._hw = _hc
        return self._hw

    # ---- lifecycle ----------------------------------------------------------
    def start(self):
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Job already running")
        self.started_at = time.strftime('%Y-%m-%d %H:%M:%S')
        self._thread = threading.Thread(target=self._run, name="BatchDosingJob", daemon=True)
        self._thread.start()

    def abort(self):
        """Operator/E-stop: stop everything and shut hardware down safely."""
        self._aborting = True
        self._stop.set()
        self._ack.set()              # unblock any advisory wait so the thread can exit

    def ack(self) -> bool:
        """Advisory mode: operator confirms they've handled the recommended action."""
        if not self.pending_action:
            return False
        self._ack.set()
        return True

    def is_active(self) -> bool:
        return self.state not in TERMINAL_STATES

    def snapshot(self) -> dict:
        with self._lock:
            return {
                'state': self.state,
                'message': self.message,
                'suggestion': self.suggestion,
                'tank_id': self.cfg.tank_id,
                'target_gallons': self.cfg.target_gallons,
                'volume_gallons': round(self.volume_gallons, 1),
                'ec': self.ec,
                'ph': self.ph,
                'ec_target': self.cfg.ec_target,
                'ph_target': self.cfg.ph_target,
                'ec_tol': self.cfg.ec_tol,
                'ph_tol': self.cfg.ph_tol,
                'ec_dosed_fraction': round(self.ec_dosed_fraction, 3),
                'ph_dosed_ml': round(self.ph_dosed_ml, 1),
                'ec_iterations': self.ec_iter,
                'ph_iterations': self.ph_iter,
                'circ_running': self.circ_on,
                'started_at': self.started_at,
                'advisory': self.advisory,
                'pending_action': self.pending_action,
            }

    # ---- state helpers ------------------------------------------------------
    def _set(self, state, message=""):
        with self._lock:
            self.state = state
            self.message = message
        logger.info("Batch job -> %s: %s", state, message)

    def _check_abort(self):
        if self._stop.is_set():
            raise _Aborted()

    def _advise(self, kind, summary, detail="", payload=None):
        """Advisory mode: publish the recommended action and block until the
        operator acknowledges it (or the job is aborted)."""
        with self._lock:
            self.pending_action = {'kind': kind, 'summary': summary,
                                   'detail': detail, 'payload': payload or {}}
        logger.info("ADVISE [%s] %s — %s", kind, summary, detail)
        self._ack.clear()
        while not self._ack.is_set():
            if self._stop.is_set():
                raise _Aborted()
            self._ack.wait(0.2)
        with self._lock:
            self.pending_action = None
        self._check_abort()

    # ---- main sequence ------------------------------------------------------
    def _run(self):
        try:
            if self.cfg.target_gallons < PRIME_GALLONS:
                raise _OperatorHold(
                    f"Target {self.cfg.target_gallons} gal is below the {PRIME_GALLONS:.0f} gal "
                    f"prime minimum; the circ pump can't run to dose.")
            self._fill_and_bulk_dose()
            self._ec_trim_loop()
            self._ph_dose_loop()
            self._stabilize()
            self._set(S_COMPLETE, f"Batch complete. EC {self.ec}, pH {self.ph}.")
            self._full_shutdown()
        except _Aborted:
            self._set(S_ABORTED, "Aborted by operator / E-stop.")
            self._full_shutdown()
        except _OperatorHold as e:
            # Park: stop dosing + water, KEEP circ so the operator can add water.
            self._hold_shutdown()
            with self._lock:
                self.state = S_NEEDS_OPERATOR
                self.message = e.reason
                self.suggestion = e.suggestion
            logger.warning("Batch job NEEDS_OPERATOR: %s | %s", e.reason, e.suggestion)
        except Exception as e:                      # noqa: BLE001 - defensive backstop
            logger.exception("Batch job crashed")
            self._set(S_ERROR, str(e))
            self._full_shutdown()

    def _fill_and_bulk_dose(self):
        """P0+P1: prime to 20 gal (water only), then fill->target while bulk dosing."""
        if self.advisory:
            return self._advisory_fill_and_bulk_dose()
        self._set(S_PRIMING, f"Filling to {PRIME_GALLONS:.0f} gal prime level.")
        self._relay(self.cfg.fill_relay, True)               # open fill valve
        self._start_flow(self.cfg.target_gallons)            # one fill to final target

        bulk_thread: Optional[threading.Thread] = None
        bulk_err: List[Exception] = []
        while True:
            self._check_abort()
            g = self._read_gallons()
            with self._lock:
                self.volume_gallons = g
            if g >= PRIME_GALLONS and bulk_thread is None:
                # Primed: start circulation and kick off the bulk EC dose.
                self._start_circ()
                self._set(S_FILL_DOSE,
                          f"Primed at {g:.0f} gal; filling to {self.cfg.target_gallons:.0f} "
                          f"and bulk dosing EC nutrients.")
                bulk_thread = threading.Thread(
                    target=self._bulk_worker, args=(bulk_err,), daemon=True)
                bulk_thread.start()
            if g >= self.cfg.target_gallons:
                break
            time.sleep(FILL_POLL_SECONDS)

        self._stop_flow()
        self._relay(self.cfg.fill_relay, False)              # close fill valve
        with self._lock:
            self.volume_gallons = self.cfg.target_gallons

        if bulk_thread:
            bulk_thread.join()                               # BARRIER: bulk dose done
        if bulk_err:
            raise bulk_err[0]
        with self._lock:
            self.ec_dosed_fraction = EC_BULK_FRACTION

    def _bulk_worker(self, err_out: List[Exception]):
        try:
            self._dose_batch(ec_bulk_doses(self.cfg.recipe, self.cfg.target_gallons))
        except Exception as e:                                # noqa: BLE001
            err_out.append(e)

    def _dose_summary(self, dose_map: Dict[str, float]) -> str:
        return ", ".join(
            f"{name} {ml:.0f} ml (pump {self.cfg.pump_ids.get(name, '?')})"
            for name, ml in dose_map.items() if ml and ml > 0)

    def _dose_payload(self, dose_map: Dict[str, float]) -> dict:
        """Structured dose data so the UI can offer one-click actuation buttons."""
        clean = {k: round(v, 1) for k, v in dose_map.items() if v and v > 0}
        return {'doses': clean,
                'pumps': {k: self.cfg.pump_ids.get(k) for k in clean}}

    def _advisory_fill_and_bulk_dose(self):
        """Advisory P0+P1: recommend fill + circulation + bulk dose; the operator
        actuates. The flow meter is run as a SENSOR so we can observe gallons."""
        target = self.cfg.target_gallons
        self._set(S_PRIMING, f"Advisory: fill tank {self.cfg.tank_id} to {target:.0f} gal.")
        self._advise(
            'valve', f"Open fresh-water fill for tank {self.cfg.tank_id}",
            f"Bring the tank to {target:.0f} gal (fresh-water solenoid, relay {self.cfg.fill_relay}). "
            f"Circulation stays off until {PRIME_GALLONS:.0f} gal.",
            payload={'relay': self.cfg.fill_relay, 'on': True})

        self._start_flow(target)        # sensor only: enables pulse counting
        self._set(S_FILL_DOSE, "Advisory: observing fill; will recommend circulation + dosing at prime.")
        advised = False
        while True:
            self._check_abort()
            g = self._read_gallons()
            with self._lock:
                self.volume_gallons = g
            if g >= PRIME_GALLONS and not advised:
                advised = True
                self.circ_on = True
                self._advise(
                    'circulation', "Start circulation (in + out solenoids)",
                    f"Open the in & out solenoids (relays {', '.join(map(str, self.cfg.mix_relays))}). "
                    f"The pressure-switched circ pump runs on its own; flow exists while both are open. "
                    f"Required to inject nutrients inline.",
                    payload={'relays': list(self.cfg.mix_relays), 'on': True})
                bulk = ec_bulk_doses(self.cfg.recipe, target)
                self._advise('dose', "Bulk dose EC nutrients (85% of recipe)",
                             self._dose_summary(bulk), payload=self._dose_payload(bulk))
                with self._lock:
                    self.ec_dosed_fraction = EC_BULK_FRACTION
            if g >= target:
                break
            time.sleep(FILL_POLL_SECONDS)

        self._stop_flow()
        self._advise('valve', f"Close fresh-water fill for tank {self.cfg.tank_id}",
                     f"Target {target:.0f} gal reached.",
                     payload={'relay': self.cfg.fill_relay, 'on': False})
        with self._lock:
            self.volume_gallons = target

    def _ec_trim_loop(self):
        self._set(S_EC_TRIM, "Trimming EC to target.")
        cfg = self.cfg
        for _ in range(EC_MAX_ITERS):
            self._check_abort()
            self._settle()
            ec = self._read_ec()
            with self._lock:
                self.ec = ec
                self.ec_iter += 1
            action = ec_trim_action(ec, cfg.ec_target, cfg.ec_tol)
            if action == 'done':
                logger.info("EC on target: %.2f", ec)
                return
            if action == 'error':
                raise _OperatorHold("No EC reading from sensor.", "Check EZO EC probe / calibration.")
            if action == 'overshoot':
                raise _OperatorHold(f"EC overshoot ({ec:.2f} > {cfg.ec_target:.2f}).",
                                    suggest_ec_dilution(ec, cfg.ec_target, cfg.target_gallons))
            # action == 'dose'
            if self.ec_dosed_fraction + EC_INCREMENT_FRACTION > EC_MAX_TOTAL_FRACTION:
                raise _OperatorHold(
                    f"EC still low ({ec:.2f}) at the {EC_MAX_TOTAL_FRACTION:.0%} dose cap.",
                    "Recipe may be too weak for this water, or EC probe is off.")
            self._dose_batch(ec_increment_doses(cfg.recipe, cfg.target_gallons))
            with self._lock:
                self.ec_dosed_fraction += EC_INCREMENT_FRACTION
        raise _OperatorHold("EC did not converge within iteration limit.",
                            "Check probe and recipe; consider a manual top-up.")

    def _ph_dose_loop(self):
        self._set(S_PH_DOSE, "Dosing pH Down (bulk + trim).")
        cfg = self.cfg
        bulk = ph_bulk_ml(cfg.recipe, cfg.target_gallons)
        self._dose_batch({PH_DOWN_NAME: bulk})
        with self._lock:
            self.ph_dosed_ml = bulk
        cap = ph_hard_cap_ml(cfg.target_gallons)
        for _ in range(PH_MAX_ITERS):
            self._check_abort()
            self._settle()
            ph = self._read_ph()
            with self._lock:
                self.ph = ph
                self.ph_iter += 1
            action = ph_trim_action(ph, cfg.ph_target, cfg.ph_tol)
            if action == 'done':
                logger.info("pH on target: %.2f", ph)
                return
            if action == 'error':
                raise _OperatorHold("No pH reading from sensor.", "Check EZO pH probe / calibration.")
            if action == 'overshoot':
                raise _OperatorHold(f"pH overshoot ({ph:.2f} < {cfg.ph_target:.2f}).",
                                    suggest_ph_raise(ph, cfg.ph_target, cfg.target_gallons))
            inc = ph_increment_ml(cfg.target_gallons)
            if self.ph_dosed_ml + inc > cap:
                raise _OperatorHold(
                    f"pH still high ({ph:.2f}) at the {PH_HARD_CAP_ML_PER_GAL} ml/gal acid cap.",
                    "High-alkalinity water or a drifted pH probe -- check before adding more acid.")
            self._dose_batch({PH_DOWN_NAME: inc})
            with self._lock:
                self.ph_dosed_ml += inc
        raise _OperatorHold("pH did not converge within iteration limit.",
                            "Check probe; water alkalinity may be high.")

    def _stabilize(self):
        self._set(S_STABILIZE, "Final mix and readings.")
        self._settle()
        with self._lock:
            self.ec = self._read_ec()
            self.ph = self._read_ph()
        self._stop_circ()

    # ---- hardware actions (interlocked) -------------------------------------
    def _dose_batch(self, dose_map: Dict[str, float]):
        """Dispense {name: ml} concurrently. Requires circ running (inline inject)."""
        if self.advisory:
            clean = {k: v for k, v in dose_map.items() if v and v > 0}
            if clean:
                self._advise('dose', "Dose nutrients", self._dose_summary(clean),
                             payload=self._dose_payload(clean))
            return
        self._require_circ()
        threads = []
        for name, ml in dose_map.items():
            if ml is None or ml <= 0:
                continue
            pid = self.cfg.pump_ids.get(name)
            if pid is None:
                raise _OperatorHold(f"No pump mapped for '{name}'.", "Check nutrients.json pump_name_to_id.")
            t = threading.Thread(target=self._dispense_blocking, args=(pid, ml, name), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        self._check_abort()

    def _dispense_blocking(self, pump_id: int, ml: float, name: str):
        """Dispense `ml` from one pump, chunking over the single-dispense cap."""
        remaining = ml
        while remaining > 0.001:
            if self._stop.is_set():
                return
            chunk = min(remaining, MAX_SINGLE_DISPENSE_ML)
            if not self.hw.dispense_pump(pump_id, round(chunk, 1)):
                raise RuntimeError(f"Dispense failed: pump {pump_id} ({name}) {chunk:.1f} ml")
            self._wait_pump_done(pump_id, chunk)
            remaining -= chunk

    def _wait_pump_done(self, pump_id: int, ml: float):
        est = ml / PUMP_ML_PER_MIN * 60.0
        deadline = time.time() + est * 1.5 + PUMP_WAIT_BUFFER_SECONDS
        time.sleep(min(2.0, est))            # let it spin up
        while True:
            if self._stop.is_set():
                return
            st = self.hw.get_pump_status(pump_id) or {}
            if not st.get('is_dispensing', False):
                return                       # poll at least once before timing out
            if time.time() >= deadline:
                break
            time.sleep(1.0)
        logger.warning("Pump %s dispense wait timed out; stopping it.", pump_id)
        self.hw.stop_pump(pump_id)

    def _require_circ(self):
        if self.volume_gallons < PRIME_GALLONS:
            raise _OperatorHold(
                f"Refusing to dose: volume {self.volume_gallons:.0f} gal below "
                f"{PRIME_GALLONS:.0f} gal circ-pump minimum.")
        if not self.circ_on:
            raise RuntimeError("Circulation pump not running; cannot dose inline.")

    def _start_circ(self):
        if self.advisory:
            self._advise('circulation', "Start circulation (in + out solenoids)",
                         f"Open relays {', '.join(map(str, self.cfg.mix_relays))}.",
                         payload={'relays': list(self.cfg.mix_relays), 'on': True})
            self.circ_on = True
            return
        for rid in self.cfg.mix_relays:
            self._relay(rid, True)
        self.circ_on = True

    def _stop_circ(self):
        if self.advisory:
            self._advise('circulation', "Stop circulation (close in/out solenoids)",
                         f"Batch done — close relays {', '.join(map(str, self.cfg.mix_relays))}.",
                         payload={'relays': list(self.cfg.mix_relays), 'on': False})
            self.circ_on = False
            return
        for rid in self.cfg.mix_relays:
            self._relay(rid, False)
        self.circ_on = False

    def _settle(self):
        for _ in range(SETTLE_SECONDS):
            self._check_abort()
            time.sleep(1.0)

    # ---- thin hardware wrappers --------------------------------------------
    def _relay(self, rid, on):
        if self.advisory:
            self._advise('valve', f"{'Open' if on else 'Close'} relay {rid}",
                         payload={'relay': rid, 'on': bool(on)})
            return
        if not self.hw.control_relay(rid, bool(on)):
            raise RuntimeError(f"Relay {rid} {'ON' if on else 'OFF'} failed")

    def _start_flow(self, gallons):
        if not self.hw.start_flow(self.cfg.flow_meter_id, int(round(gallons))):
            raise RuntimeError("Failed to start fill flow meter")

    def _stop_flow(self):
        self.hw.stop_flow(self.cfg.flow_meter_id)

    def _read_gallons(self) -> float:
        st = self.hw.get_flow_status(self.cfg.flow_meter_id) or {}
        return float(st.get('current_gallons', 0) or 0)

    def _read_ec(self):
        r = self.hw.read_ec_ph_sensors() or {}
        return r.get('ec') if r.get('success') else None

    def _read_ph(self):
        r = self.hw.read_ec_ph_sensors() or {}
        return r.get('ph') if r.get('success') else None

    # ---- shutdown paths -----------------------------------------------------
    def _hold_shutdown(self):
        """Operator hold: stop peristaltic pumps + fill water, KEEP circ running."""
        if self.advisory:
            return                       # program never actuated; operator owns hardware
        for pid in self.cfg.pump_ids.values():
            try:
                self.hw.stop_pump(pid)
            except Exception:
                pass
        try:
            self._stop_flow()
            self.hw.control_relay(self.cfg.fill_relay, False)
        except Exception:
            pass

    def _full_shutdown(self):
        """Terminal: stop pumps, flow, and all this tank's valves (circ included)."""
        if self.advisory:
            try:
                self._stop_flow()        # flow meter is a sensor we started; stop it
            except Exception:
                pass
            self.circ_on = False
            logger.info("Advisory complete: operator should close valves / stop pumps as recommended.")
            return
        for pid in self.cfg.pump_ids.values():
            try:
                self.hw.stop_pump(pid)
            except Exception:
                pass
        try:
            self._stop_flow()
        except Exception:
            pass
        for rid in [self.cfg.fill_relay, *self.cfg.mix_relays]:
            try:
                self.hw.control_relay(rid, False)
            except Exception:
                pass
        self.circ_on = False


# =============================================================================
# SINGLE-JOB MANAGER (Flask integration)
# =============================================================================

_current: Optional[BatchDosingJob] = None
_mgr_lock = threading.Lock()


def start_batch(cfg: BatchConfig) -> BatchDosingJob:
    global _current
    with _mgr_lock:
        if _current is not None and _current.is_active():
            raise RuntimeError("A batch job is already running")
        _current = BatchDosingJob(cfg)
        _current.start()
        return _current


def get_current() -> Optional[BatchDosingJob]:
    return _current


def abort_current() -> bool:
    with _mgr_lock:
        if _current is None or not _current.is_active():
            return False
        _current.abort()
        return True


def ack_current() -> bool:
    """Advisory mode: acknowledge the current recommended action."""
    job = _current
    return job.ack() if job else False
