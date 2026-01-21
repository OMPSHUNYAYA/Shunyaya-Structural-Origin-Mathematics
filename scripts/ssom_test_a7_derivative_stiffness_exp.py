# ssom_test_a7_derivative_stiffness_exp.py
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

def f_eps(x: float, eps_scale: float) -> float:
    # f(x) = eps * (1 - exp(-x/eps)), with f(0)=0, classical derivative f'(0)=1
    if x <= 0.0:
        return 0.0
    z = -x / eps_scale
    # for very negative z, exp(z) underflows to 0 cleanly in IEEE-754
    return eps_scale * (1.0 - math.exp(z))

def forward_slope_at_zero(h: float, eps_scale: float) -> float:
    if h <= 0.0:
        return float("nan")
    return f_eps(h, eps_scale) / h

def structural_posture(prev_m: float, m: float) -> tuple:
    prev_abs = abs(prev_m) + EPS
    cur_abs = abs(m) + EPS
    lr = abs(math.log(cur_abs / prev_abs))
    a = 1.0 / (1.0 + lr)
    a = clamp_lane(a)
    return a, lr

def write_csv(path: str, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="out_ssom_test_a7")
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--h_max", type=float, default=1e-1)
    ap.add_argument("--h_min", type=float, default=1e-18)
    ap.add_argument("--eps_scale", type=float, default=1e-6)
    ap.add_argument("--a_min", type=float, default=0.70)
    ap.add_argument("--s_max", type=float, default=1.00)
    ap.add_argument("--r_safe", type=float, default=0.10)
    args = ap.parse_args()

    if args.h_max <= 0.0 or args.h_min <= 0.0 or args.h_min >= args.h_max:
        raise ValueError("Require 0 < h_min < h_max")
    if args.steps < 5:
        raise ValueError("Require --steps >= 5")
    if args.eps_scale <= 0.0:
        raise ValueError("Require --eps_scale > 0")

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
        m = forward_slope_at_zero(h, args.eps_scale)

        if prev_m is None:
            a = 1.0
            lr = 0.0
            status = "ALLOW"
        else:
            if (not isinstance(m, (int, float))) or (not math.isfinite(m)):
                a = float("nan")
                lr = float("nan")
                status = "ABSTAIN"
            else:
                a, lr = structural_posture(prev_m, m)

                if lr > args.r_safe:
                    s += (lr - args.r_safe)

                status = "ALLOW"
                if (not math.isfinite(a)) or (a < args.a_min) or (s > args.s_max):
                    status = "DENY"

        _ = phi3((m, a, s))

        rows.append([
            k,
            "{:.3e}".format(h),
            "{:.3e}".format(args.eps_scale),
            "{:.16e}".format(m) if math.isfinite(m) else str(m),
            "{:.8f}".format(a) if math.isfinite(a) else str(a),
            "{:.8f}".format(s) if math.isfinite(s) else str(s),
            "{:.8f}".format(lr) if math.isfinite(lr) else str(lr),
            status,
        ])

        if status == "DENY" and first_deny_h is None:
            first_deny_h = h
            break

        if status == "ABSTAIN":
            break

        prev_m = m

    out_csv = os.path.join(args.out_dir, "trace_ssom_derivative_stiffness_exp_at0.csv")
    write_csv(
        out_csv,
        ["k", "h", "eps_scale", "m_slope", "a", "s", "log_ratio_abs", "status"],
        rows,
    )

    last = rows[-1][-1] if rows else "NO_TRACE"
    print("SSOM Test A.7 complete: Stiffness-like regime in derivative refinement at x=0 for f(x)=eps*(1-exp(-x/eps)) (classical f'(0)=1)")
    print("Output:", out_csv)
    print("Last status:", last)
    if first_deny_h is not None:
        print("First DENY at h ~= {:.3e}".format(first_deny_h))

if __name__ == "__main__":
    main()
