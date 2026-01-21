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

def f_general(x: float) -> float:
    if x == 0.0:
        return 0.0
    return x * math.sin(1.0 / x)

def posture_step(prev_m: float, m: float, beta_flip: float, m_zero_tol: float) -> tuple:
    # zero-tolerance: treat tiny magnitudes as exactly zero, and do not count flips
    if abs(prev_m) <= m_zero_tol:
        prev_m_eff = 0.0
    else:
        prev_m_eff = prev_m

    if abs(m) <= m_zero_tol:
        m_eff = 0.0
    else:
        m_eff = m

    prev_abs = abs(prev_m_eff)
    cur_abs = abs(m_eff)

    if prev_abs <= EPS and cur_abs <= EPS:
        lr = 0.0
    elif prev_abs <= EPS and cur_abs > EPS:
        lr = abs(math.log((cur_abs + EPS) / EPS))
    elif prev_abs > EPS and cur_abs <= EPS:
        lr = abs(math.log(EPS / (prev_abs + EPS)))
    else:
        lr = abs(math.log((cur_abs + EPS) / (prev_abs + EPS)))

    flip = 1 if (prev_m_eff * m_eff) < 0.0 else 0
    a = 1.0 / (1.0 + lr + beta_flip * float(flip))
    a = clamp_lane(a)
    return a, lr, flip, prev_m_eff, m_eff

def run_path(path_name: str, xs, a_min: float, s_max: float, r_safe: float, beta_flip: float, gamma_flip: float, m_zero_tol: float):
    rows = []
    s = 0.0
    prev_m = None
    first_deny_x = None

    for k, x in enumerate(xs):
        m = f_general(x)

        if prev_m is None:
            a = 1.0
            lr = 0.0
            flip = 0
            prev_eff = 0.0
            m_eff = 0.0 if abs(m) <= m_zero_tol else m
            status = "ALLOW"
        else:
            a, lr, flip, prev_eff, m_eff = posture_step(prev_m, m, beta_flip, m_zero_tol)

            if lr > r_safe:
                s = s + (lr - r_safe)
            if flip == 1:
                s = s + gamma_flip

            status = "ALLOW"
            if (not math.isfinite(a)) or (a < a_min) or (s > s_max):
                status = "DENY"

        _ = phi3((m, a, s))

        rows.append([
            k + 1,
            "{:.16e}".format(x),
            "{:.16e}".format(m),
            "{:.16e}".format(m_eff),
            "{:.8f}".format(a),
            "{:.8f}".format(s),
            "{:.8f}".format(lr),
            flip,
            status,
        ])

        if status == "DENY" and first_deny_x is None:
            first_deny_x = x
            break

        prev_m = m

    return rows, first_deny_x

def write_csv(path: str, rows):
    with open(path, "w", newline="", encoding="utf-8") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(["n", "x_n", "m_raw=f(x_n)", "m_eff", "a", "s", "log_ratio_abs", "sign_flip", "status"])
        for r in rows:
            w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="out_ssom_test_a3_v2")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--a_min", type=float, default=0.70)
    ap.add_argument("--s_max", type=float, default=1.00)
    ap.add_argument("--r_safe", type=float, default=0.10)
    ap.add_argument("--beta_flip", type=float, default=0.50)
    ap.add_argument("--gamma_flip", type=float, default=0.20)
    ap.add_argument("--m_zero_tol", type=float, default=1e-12)
    args = ap.parse_args()

    if args.steps < 5:
        raise ValueError("Require --steps >= 5")

    os.makedirs(args.out_dir, exist_ok=True)

    pi = math.pi

    # Paths for x_n -> 0
    xs_calm = [1.0 / (n * pi) for n in range(1, args.steps + 1)]
    xs_osc = [1.0 / (n * pi + (pi / 2.0)) for n in range(1, args.steps + 1)]

    # Make calm path exact-by-definition: override f(x_n) to 0 logically using m_zero_tol
    # We still compute m_raw in the trace for transparency; m_eff is what posture uses.

    rows_calm, deny_x_calm = run_path(
        "calm",
        xs_calm,
        args.a_min,
        args.s_max,
        args.r_safe,
        args.beta_flip,
        args.gamma_flip,
        args.m_zero_tol,
    )

    rows_osc, deny_x_osc = run_path(
        "osc",
        xs_osc,
        args.a_min,
        args.s_max,
        args.r_safe,
        args.beta_flip,
        args.gamma_flip,
        args.m_zero_tol,
    )

    out_calm = os.path.join(args.out_dir, "trace_ssom_limit_path_calm.csv")
    out_osc = os.path.join(args.out_dir, "trace_ssom_limit_path_oscillatory.csv")
    write_csv(out_calm, rows_calm)
    write_csv(out_osc, rows_osc)

    print("SSOM Test A.3.1 (v2) complete: Structural limit with path-dependent posture for f(x)=x*sin(1/x) as x->0")
    print("Output (calm path):", out_calm)
    print("Output (osc path):", out_osc)

    if deny_x_calm is None:
        print("Calm path: no DENY within steps =", args.steps)
    else:
        print("Calm path: first DENY at x ~= {:.3e}".format(deny_x_calm))

    if deny_x_osc is None:
        print("Osc path: no DENY within steps =", args.steps)
    else:
        print("Osc path: first DENY at x ~= {:.3e}".format(deny_x_osc))

if __name__ == "__main__":
    main()
