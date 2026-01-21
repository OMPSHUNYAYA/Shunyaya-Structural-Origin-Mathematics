# ssom_test_a9_derivative_geometry_invariance.py
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
    raise ValueError("phi3 expects (m,a,s)")

def f(x: float) -> float:
    return 1.0 - math.cos(x)

def forward_slope(h: float) -> float:
    return f(h) / h if h > 0 else float("nan")

def central_slope(h: float) -> float:
    return (f(h) - f(-h)) / (2.0 * h) if h > 0 else float("nan")

def structural_posture(prev_m: float, m: float):
    prev_abs = abs(prev_m) + EPS
    cur_abs = abs(m) + EPS
    lr = abs(math.log(cur_abs / prev_abs))
    a = 1.0 / (1.0 + lr)
    a = clamp_lane(a)
    return a, lr

def run_geometry(label, slope_fn, hs, a_min, s_max, r_safe):
    rows = []
    s = 0.0
    prev_m = None
    first_deny_h = None

    for k, h in enumerate(hs):
        m = slope_fn(h)

        if prev_m is None:
            a = 1.0
            lr = 0.0
            status = "ALLOW"
        else:
            if not math.isfinite(m):
                status = "ABSTAIN"
                a = float("nan")
                lr = float("nan")
            else:
                a, lr = structural_posture(prev_m, m)
                if lr > r_safe:
                    s += (lr - r_safe)
                status = "ALLOW"
                if (a < a_min) or (s > s_max):
                    status = "DENY"

        _ = phi3((m, a, s))

        rows.append([
            label,
            k,
            "{:.3e}".format(h),
            "{:.16e}".format(m) if math.isfinite(m) else str(m),
            "{:.8f}".format(a) if math.isfinite(a) else str(a),
            "{:.8f}".format(s),
            "{:.8f}".format(lr),
            status,
        ])

        if status == "DENY" and first_deny_h is None:
            first_deny_h = h
            break

        if status == "ABSTAIN":
            break

        prev_m = m

    return rows, first_deny_h

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="out_ssom_test_a9")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--h_max", type=float, default=1e-1)
    ap.add_argument("--h_min", type=float, default=1e-18)
    ap.add_argument("--a_min", type=float, default=0.70)
    ap.add_argument("--s_max", type=float, default=1.00)
    ap.add_argument("--r_safe", type=float, default=0.10)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    log_h_max = math.log10(args.h_max)
    log_h_min = math.log10(args.h_min)

    hs = [
        10 ** (log_h_max + (log_h_min - log_h_max) * i / (args.steps - 1))
        for i in range(args.steps)
    ]

    rows_fwd, deny_fwd = run_geometry(
        "forward", forward_slope, hs,
        args.a_min, args.s_max, args.r_safe
    )

    rows_ctr, deny_ctr = run_geometry(
        "central", central_slope, hs,
        args.a_min, args.s_max, args.r_safe
    )

    out_csv = os.path.join(args.out_dir, "trace_ssom_derivative_geometry.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "geometry", "k", "h", "m_slope", "a", "s", "log_ratio_abs", "status"
        ])
        for r in rows_fwd + rows_ctr:
            w.writerow(r)

    print("SSOM Test A.9 complete: Geometry invariance (forward vs central)")
    print("Output:", out_csv)
    if deny_fwd is not None:
        print("Forward diff: first DENY at h ~= {:.3e}".format(deny_fwd))
    if deny_ctr is not None:
        print("Central diff: first DENY at h ~= {:.3e}".format(deny_ctr))

if __name__ == "__main__":
    main()
