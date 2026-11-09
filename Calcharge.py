"""EV charge calculator (CLI) - same logic as index.html.

Usage:
    python Calcharge.py 20            # SOC 20% -> 100%
    python Calcharge.py 20 80 -H 6    # SOC 20% -> 80%, want done in 6 hours
"""
import argparse
import sys
from datetime import datetime, timedelta

CAPACITY_KWH = 60.48
VOLT = 220.0
AMP_MAX = 32.0
AMP_MIN = 6.0
EFF = 0.90
RATE = 4.5  # baht/kWh


def calc(soc, tgt, hours=None, cap=CAPACITY_KWH, volt=VOLT, amax=AMP_MAX, eff=EFF, rate=RATE):
    amax = min(amax, AMP_MAX)
    if not (cap > 0 and volt > 0 and amax > 0 and 0.01 <= eff <= 1):
        raise ValueError("invalid parameters")
    kwh_bat = max(0.0, tgt - soc) / 100 * cap
    e_grid = kwh_bat / eff
    p_line = volt * amax / 1000
    t_full = e_grid / p_line
    result = {
        "kwh_bat": kwh_bat, "e_grid": e_grid, "amps": amax, "kw": p_line,
        "hours": t_full, "cost": e_grid * rate,
        "done_at": datetime.now() + timedelta(hours=t_full),
    }
    if hours:
        i_need = e_grid * 1000 / (volt * hours)
        result["feasible"] = i_need <= amax and amax >= AMP_MIN
        i_need = min(amax, max(AMP_MIN, i_need))
        result["i_need"] = i_need
        result["p_need"] = i_need * volt / 1000
    return result


def fmt_t(h):
    m = round(h * 60)
    return f"{m // 60} ชม. {m % 60:02d} น."


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Thai output on Windows consoles
    except AttributeError:
        pass
    ap =argparse.ArgumentParser(description="EV charge calculator")
    ap.add_argument("soc", type=float, help="battery %% now")
    ap.add_argument("target", type=float, nargs="?", default=100, help="target %% (default 100)")
    ap.add_argument("-H", "--hours", type=float, help="want to finish within N hours")
    a = ap.parse_args()

    if a.target <= a.soc:
        print("แบตถึงเป้าหมายแล้ว ไม่ต้องชาร์จ")
        return
    r = calc(a.soc, a.target, a.hours)
    print(f"เติมเข้าแบต   : {r['kwh_bat']:.1f} kWh")
    print(f"ไฟจากสาย      : {r['e_grid']:.1f} kWh")
    print(f"กระแส/กำลัง   : {r['amps']:.1f} A / {r['kw']:.2f} kW")
    print(f"ใช้เวลา       : {fmt_t(r['hours'])}")
    print(f"เสร็จประมาณ   : {r['done_at']:%H:%M} ({r['done_at']:%d/%m})")
    print(f"ค่าไฟ         : {r['cost']:.0f} บาท")
    if a.hours:
        print(f"--- ให้เสร็จใน {a.hours:g} ชม. ---")
        print(f"ตั้งกระแส     : {r['i_need']:.1f} A ({r['p_need']:.2f} kW)")
        if not r["feasible"]:
            print(f"⚠ ชาร์จไม่ทัน ต้องใช้ {fmt_t(r['hours'])} ที่กระแสสูงสุด")


if __name__ == "__main__":
    main()
