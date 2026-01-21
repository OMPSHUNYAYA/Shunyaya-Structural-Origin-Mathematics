# ssom_test1a_derivative_sqrt0.py
import argparse
import csv
import math
import os

try:
    from ssm_infinity_core import clamp_lane
except Exception:
    def clamp_lane(a: float) -> float:
        eps = 1e-12
        return max(min(a, 1.0 - eps), -1.0 + eps)

EPS = 1e-15

def phi3(state):
    if isinstance(state, tuple) and len(state) == 3:
        return state[0]
    raise ValueError("phi3 expects a (m,a,s) tuple")

def f_sqrt(x: float) -> float:
    if x < 0.0:
        return float("nan")
    return math.sqrt(x)

def fd_slope_at_zero(h: float) -> float:
    if h <= 0.0:
        return float("nan")
    return (f_sqrt(h) - 0.0) / h

def structural_posture(prev_m: float, m: float, eps: float) -> float:
    if not (isinstance(prev_m, (int, float)) and math.isfinite(prev_m)):
        return float("nan")
    if not (isinstance(m, (int, float)) and math.isfinite(m)):
        return float("nan")
    if prev_m <= 0.0 or m <= 0.0:
        return float("nan")
    lr = abs(math.log(m / max(prev_m, eps)))
    a = 1.0 / (1.0 + lr)
    return clamp_lane(a)

def write_csv(path: str, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="out_ssom_test1a")
    ap.add_argument("--h_max", type=float, default=1e-1)
    ap.add_argument("--h_min", type=float, default=1e-15)
    ap.add_argument("--steps", type=int, default=15)
    ap.add_argument("--a_min", type=float, default=0.70)
    ap.add_argument("--s_max", type=float, default=1.00)
    ap.add_argument("--r_safe", type=float, default=0.10)
    args = ap.parse_args()

    if args.h_max <= 0.0 or args.h_min <= 0.0 or args.h_min >= args.h_max:
        raise ValueError("Require 0 < h_min < h_max")
    if args.steps < 3:
        raise ValueError("Require --steps >= 3")

    os.makedirs(args.out_dir, exist_ok=True)

    log_h_max = math.log10(args.h_max)
    log_h_min = math.log10(args.h_min)

    hs = []
    for k in range(args.steps):
        t = k / (args.steps - 1)
        logh = log_h_max + (log_h_min - log_h_max) * t
        hs.append(10 ** logh)

    rows = []
    s = 0.0
    prev_m = None
    first_deny_h = None

    for k, h in enumerate(hs):
        m = fd_slope_at_zero(h)

        if prev_m is None:
            a = 1.0
            lr = 0.0
            status = "ALLOW"
        else:
            if (not isinstance(m, (int, float))) or (not math.isfinite(m)) or m <= 0.0:
                a = float("nan")
                lr = float("nan")
                status = "ABSTAIN"
            else:
                lr = abs(math.log(m / max(prev_m, EPS)))
                a = structural_posture(prev_m, m, EPS)
                if lr > args.r_safe:
                    s = s + (lr - args.r_safe)
                status = "ALLOW"
                if (not math.isfinite(a)) or (a < args.a_min) or (s > args.s_max):
                    status = "DENY"

        state = (m, a, s)
        _ = phi3(state)

        rows.append([
            k,
            "{:.3e}".format(h),
            "{:.8e}".format(m) if math.isfinite(m) else str(m),
            "{:.8f}".format(a) if math.isfinite(a) else str(a),
            "{:.8f}".format(s) if math.isfinite(s) else str(s),
            "{:.8f}".format(lr) if math.isfinite(lr) else str(lr),
            status,
        ])

        if status == "DENY" and first_deny_h is None:
            first_deny_h = h

        prev_m = m

        if status in ("DENY", "ABSTAIN"):
            break

    out_csv = os.path.join(args.out_dir, "trace_ssom_derivative_sqrt0.csv")
    write_csv(out_csv, ["k", "h", "m_slope", "a", "s", "log_ratio", "status"], rows)

    last = rows[-1][-1] if rows else "NO_TRACE"
    print("SSOM Test 1A complete: sqrt(x) forward-derivative at x=0")
    print("Output:", out_csv)
    print("Last status:", last)
    if first_deny_h is not None:
        print("First DENY at h ~= {:.3e}".format(first_deny_h))

if __name__ == "__main__":
    main()
