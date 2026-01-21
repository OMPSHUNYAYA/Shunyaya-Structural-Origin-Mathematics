# ssom_test_a6_derivative_refinement_fatigue_cos.py
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

# Function: f(x) = 1 - cos(x), with f(0)=0, and classical derivative f'(0)=0
def f(x: float) -> float:
    return 1.0 - math.cos(x)

def forward_slope_at_zero(h: float) -> float:
    # m(h) = (f(h)-f(0))/h = (1-cos(h))/h
    if h <= 0.0:
        return float("nan")
    return f(h) / h

def structural_posture(prev_m: float, m: float, beta_flip: float) -> tuple:
    # Alignment lane from successive magnitude ratio + sign flips
    prev_abs = abs(prev_m) + EPS
    cur_abs  = abs(m) + EPS
    lr = abs(math.log(cur_abs / prev_abs))
    flip = 1 if (prev_m * m) < 0.0 else 0
    a = 1.0 / (1.0 + lr + beta_flip * float(flip))
    a = clamp_lane(a)
    return a, lr, flip

def write_csv(path: str, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="out_ssom_test_a6")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--h_max", type=float, default=1e-1)
    ap.add_argument("--h_min", type=float, default=1e-18)
    ap.add_argument("--a_min", type=float, default=0.70)
    ap.add_argument("--s_max", type=float, default=1.00)
    ap.add_argument("--r_safe", type=float, default=0.10)
    ap.add_argument("--beta_flip", type=float, default=0.50)
    ap.add_argument("--gamma_flip", type=float, default=0.20)
    args = ap.parse_args()

    if args.h_max <= 0.0 or args.h_min <= 0.0 or args.h_min >= args.h_max:
        raise ValueError("Require 0 < h_min < h_max")
    if args.steps < 5:
        raise ValueError("Require --steps >= 5")

    os.makedirs(args.out_dir, exist_ok=True)

    # Log-spaced refinement: h decreases from h_max to h_min
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
        m = forward_slope_at_zero(h)

        if prev_m is None:
            a = 1.0
            lr = 0.0
            flip = 0
            status = "ALLOW"
        else:
            if (not isinstance(m, (int, float))) or (not math.isfinite(m)):
                a = float("nan")
                lr = float("nan")
                flip = 0
                status = "ABSTAIN"
            else:
                a, lr, flip = structural_posture(prev_m, m, args.beta_flip)

                # strain accumulates when refinement produces unstable ratio changes
                if lr > args.r_safe:
                    s += (lr - args.r_safe)
                # explicit churn penalty when slope changes sign
                if flip == 1:
                    s += args.gamma_flip

                status = "ALLOW"
                if (not math.isfinite(a)) or (a < args.a_min) or (s > args.s_max):
                    status = "DENY"

        _ = phi3((m, a, s))

        rows.append([
            k,
            "{:.3e}".format(h),
            "{:.16e}".format(m) if math.isfinite(m) else str(m),
            "{:.8f}".format(a) if math.isfinite(a) else str(a),
            "{:.8f}".format(s) if math.isfinite(s) else str(s),
            "{:.8f}".format(lr) if math.isfinite(lr) else str(lr),
            flip,
            status,
        ])

        if status == "DENY" and first_deny_h is None:
            first_deny_h = h
            break

        if status == "ABSTAIN":
            break

        prev_m = m

    out_csv = os.path.join(args.out_dir, "trace_ssom_derivative_1minuscos_at0.csv")
    write_csv(out_csv,
              ["k", "h", "m_slope", "a", "s", "log_ratio_abs", "sign_flip", "status"],
              rows)

    last = rows[-1][-1] if rows else "NO_TRACE"
    print("SSOM Test A.6 complete: Refinement fatigue in derivative at x=0 for f(x)=1-cos(x) (classical f'(0)=0)")
    print("Output:", out_csv)
    print("Last status:", last)
    if first_deny_h is not None:
        print("First DENY at h ~= {:.3e}".format(first_deny_h))

if __name__ == "__main__":
    main()
