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
    return state[0]

def f_zero(x: float) -> float:
    return 0.0

def f_alt_square(x: float, blocks: int) -> float:
    # blocks must be even for exact zero integral over [0,1] with equal +1/-1 durations
    # value alternates every block of length 1/blocks
    k = int(math.floor(x * blocks))
    if k >= blocks:
        k = blocks - 1
    return 1.0 if (k % 2 == 0) else -1.0

def posture_step(prev_dm: float, dm: float, beta_flip: float, dm_zero_tol: float):
    prev_eff = 0.0 if abs(prev_dm) <= dm_zero_tol else prev_dm
    dm_eff = 0.0 if abs(dm) <= dm_zero_tol else dm

    prev_abs = abs(prev_eff)
    cur_abs = abs(dm_eff)

    if prev_abs <= EPS and cur_abs <= EPS:
        lr = 0.0
    elif prev_abs <= EPS and cur_abs > EPS:
        lr = abs(math.log((cur_abs + EPS) / EPS))
    elif prev_abs > EPS and cur_abs <= EPS:
        lr = abs(math.log(EPS / (prev_abs + EPS)))
    else:
        lr = abs(math.log((cur_abs + EPS) / (prev_abs + EPS)))

    flip = 1 if (prev_eff * dm_eff) < 0.0 else 0
    a = 1.0 / (1.0 + lr + beta_flip * float(flip))
    a = clamp_lane(a)
    return a, lr, flip, prev_eff, dm_eff

def integrate_ssom(f, xs, a_min, s_max, r_safe, beta_flip, gamma_flip, dm_zero_tol):
    rows = []
    s = 0.0
    prev_dm = None
    m = 0.0
    first_deny_x = None

    for k in range(len(xs) - 1):
        x0 = xs[k]
        x1 = xs[k + 1]
        dx = x1 - x0

        dm = f(x0) * dx
        m_new = m + dm

        if prev_dm is None:
            a = 1.0
            lr = 0.0
            flip = 0
            dm_eff = 0.0 if abs(dm) <= dm_zero_tol else dm
            status = "ALLOW"
        else:
            a, lr, flip, _, dm_eff = posture_step(prev_dm, dm, beta_flip, dm_zero_tol)

            if lr > r_safe:
                s += (lr - r_safe)
            if flip == 1:
                s += gamma_flip

            status = "ALLOW"
            if (not math.isfinite(a)) or (a < a_min) or (s > s_max):
                status = "DENY"
                if first_deny_x is None:
                    first_deny_x = x0

        _ = phi3((m_new, a, s))

        rows.append([
            k + 1,
            "{:.6f}".format(x0),
            "{:.10f}".format(dx),
            "{:.12e}".format(dm),
            "{:.12e}".format(dm_eff),
            "{:.12e}".format(m_new),
            "{:.8f}".format(a),
            "{:.8f}".format(s),
            "{:.8f}".format(lr),
            flip,
            status,
        ])

        if status == "DENY":
            break

        m = m_new
        prev_dm = dm

    return rows, first_deny_x, m

def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["step", "x", "dx", "delta_m_raw", "delta_m_eff", "m_accum", "a", "s", "log_ratio", "sign_flip", "status"])
        for r in rows:
            w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="out_ssom_test_a5")
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--blocks", type=int, default=200)
    ap.add_argument("--a_min", type=float, default=0.70)
    ap.add_argument("--s_max", type=float, default=1.00)
    ap.add_argument("--r_safe", type=float, default=0.10)
    ap.add_argument("--beta_flip", type=float, default=0.50)
    ap.add_argument("--gamma_flip", type=float, default=0.05)
    ap.add_argument("--dm_zero_tol", type=float, default=1e-15)
    args = ap.parse_args()

    if args.steps < 10:
        raise ValueError("Require --steps >= 10")
    if args.blocks < 2 or (args.blocks % 2 != 0):
        raise ValueError("Require --blocks to be an even integer >= 2")

    os.makedirs(args.out_dir, exist_ok=True)
    xs = [i / args.steps for i in range(args.steps + 1)]

    rows_zero, deny_zero, m_zero = integrate_ssom(
        f_zero,
        xs,
        args.a_min,
        args.s_max,
        args.r_safe,
        args.beta_flip,
        args.gamma_flip,
        args.dm_zero_tol,
    )

    def f_cancel(x):
        return f_alt_square(x, args.blocks)

    rows_cancel, deny_cancel, m_cancel = integrate_ssom(
        f_cancel,
        xs,
        args.a_min,
        args.s_max,
        args.r_safe,
        args.beta_flip,
        args.gamma_flip,
        args.dm_zero_tol,
    )

    out_zero = os.path.join(args.out_dir, "trace_ssom_integral_zero.csv")
    out_cancel = os.path.join(args.out_dir, "trace_ssom_integral_cancellation.csv")
    write_csv(out_zero, rows_zero)
    write_csv(out_cancel, rows_cancel)

    print("SSOM Test A.5 complete: Structural integral cancellation (same classical value, different strain)")
    print("Output (zero):", out_zero)
    print("Output (cancellation):", out_cancel)
    print("Zero integral: m_final ~= {:.6e}".format(m_zero))
    print("Cancellation integral: m_final ~= {:.6e}".format(m_cancel))

    if deny_zero is None:
        print("Zero integral: no DENY")
    else:
        print("Zero integral: first DENY at x ~= {:.3e}".format(deny_zero))

    if deny_cancel is None:
        print("Cancellation integral: no DENY")
    else:
        print("Cancellation integral: first DENY at x ~= {:.3e}".format(deny_cancel))

if __name__ == "__main__":
    main()
