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

def f_smooth(x):
    return 1.0

def f_spiky(x, eps):
    return 1.0 / math.sqrt(x + eps)

def integrate_ssom(f, xs, a_min, s_max, r_safe):
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
        else:
            lr = abs(math.log((abs(dm) + EPS) / (abs(prev_dm) + EPS)))
            a = 1.0 / (1.0 + lr)
            a = clamp_lane(a)

            if lr > r_safe:
                s += (lr - r_safe)

        status = "ALLOW"
        if a < a_min or s > s_max:
            status = "DENY"
            if first_deny_x is None:
                first_deny_x = x0

        _ = phi3((m_new, a, s))

        rows.append([
            k + 1,
            "{:.6f}".format(x0),
            "{:.8f}".format(dm),
            "{:.8f}".format(m_new),
            "{:.6f}".format(a),
            "{:.6f}".format(s),
            "{:.6f}".format(lr),
            status,
        ])

        if status == "DENY":
            break

        m = m_new
        prev_dm = dm

    return rows, first_deny_x

def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["step", "x", "delta_m", "m_accum", "a", "s", "log_ratio", "status"])
        for r in rows:
            w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="out_ssom_test_a4")
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--a_min", type=float, default=0.70)
    ap.add_argument("--s_max", type=float, default=1.00)
    ap.add_argument("--r_safe", type=float, default=0.10)
    ap.add_argument("--eps", type=float, default=1e-6)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    xs = [i / args.steps for i in range(args.steps + 1)]

    # Smooth case
    rows_smooth, deny_smooth = integrate_ssom(
        f_smooth,
        xs,
        args.a_min,
        args.s_max,
        args.r_safe,
    )

    # Spiky case (normalized)
    raw_vals = [f_spiky(x, args.eps) for x in xs]
    area = sum(raw_vals[i] * (xs[i + 1] - xs[i]) for i in range(len(xs) - 1))

    def f_spiky_norm(x):
        return f_spiky(x, args.eps) / area

    rows_spiky, deny_spiky = integrate_ssom(
        f_spiky_norm,
        xs,
        args.a_min,
        args.s_max,
        args.r_safe,
    )

    out_smooth = os.path.join(args.out_dir, "trace_ssom_integral_smooth.csv")
    out_spiky = os.path.join(args.out_dir, "trace_ssom_integral_spiky.csv")

    write_csv(out_smooth, rows_smooth)
    write_csv(out_spiky, rows_spiky)

    print("SSOM Test A.4.1 complete: Structural integral (equal area)")
    print("Output (smooth):", out_smooth)
    print("Output (spiky):", out_spiky)

    if deny_smooth is None:
        print("Smooth integral: no DENY")
    else:
        print("Smooth integral: first DENY at x ~= {:.3e}".format(deny_smooth))

    if deny_spiky is None:
        print("Spiky integral: no DENY")
    else:
        print("Spiky integral: first DENY at x ~= {:.3e}".format(deny_spiky))

if __name__ == "__main__":
    main()
