"""
Генератор синтетических данных для пет-проекта «Корзинка».

Сервис доставки продуктов: приложения Android и iOS + веб-версия.
Период данных: 2026-05-01 .. 2026-08-31.
A/B-тест нового одностраничного чекаута: 2026-08-04 .. 2026-08-31.

Запуск:  pip install numpy pandas && python generate_data.py
Результат: CSV-файлы в папке data/
Данные детерминированы (SEED), у всех получатся одинаковые цифры.
"""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

START = pd.Timestamp("2026-05-01")
END = pd.Timestamp("2026-09-01")          # не включительно
TEST_START = pd.Timestamp("2026-08-04")
N_USERS = 40_000
N_PROMO_EXTRA = 4_000

DAY = 86_400.0
T0 = START.value / 1e9
T_END = END.value / 1e9
T_TEST = TEST_START.value / 1e9

PLATFORMS = np.array(["android", "ios", "web"])
CITIES = np.array(["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск"])
CITY_AOV = {"Москва": 1.12, "Санкт-Петербург": 1.05, "Казань": 0.90,
            "Екатеринбург": 0.95, "Новосибирск": 0.92}

# --- воронка сессии ---
P_CART = 0.48
P_CHECKOUT = 0.70
P_ORDER_OLD = 0.74
TEST_EFFECT = {"android": -0.045, "ios": 0.075, "web": 0.06}
NOVELTY = 0.05                      # затухающий «эффект новизны»
AOV_MU = {"android": np.log(1650), "ios": np.log(2050), "web": np.log(1900)}
AOV_TEST_MULT = 0.965               # убрали блок «добавьте к заказу»
WEEKDAY_ACCEPT = np.array([0.72, 0.72, 0.76, 0.80, 0.92, 1.0, 0.88])  # пн..вс

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)


def ab_group(user_id: int) -> str:
    h = int(hashlib.md5(f"checkout_v2:{user_id}".encode()).hexdigest(), 16)
    return "test" if h % 2 else "control"


# ================= пользователи =================
n_days = int((T_END - T0) / DAY)
w = np.linspace(1.0, 1.6, n_days)                       # органический рост
reg_t = T0 + rng.choice(n_days, N_USERS, p=w / w.sum()) * DAY + rng.uniform(0, DAY, N_USERS)
channel = rng.choice(["organic", "context_ads", "referral"], N_USERS, p=[0.55, 0.30, 0.15])

promo_start = pd.Timestamp("2026-07-06").value / 1e9
promo_t = promo_start + rng.uniform(0, 14 * DAY, N_PROMO_EXTRA)   # промо-кампания 6–19 июля
reg_t = np.concatenate([reg_t, promo_t])
channel = np.concatenate([channel, np.full(N_PROMO_EXTRA, "promo_july")])
n = len(reg_t)
order_idx = np.argsort(reg_t)
reg_t, channel = reg_t[order_idx], channel[order_idx]

platform = rng.choice(PLATFORMS, n, p=[0.50, 0.35, 0.15])
city = rng.choice(CITIES, n, p=[0.45, 0.22, 0.12, 0.11, 0.10])
user_ids = np.arange(100_001, 100_001 + n)

rate = rng.lognormal(np.log(1.3), 0.7, n) / 7 / DAY     # сессий в секунду
life = rng.exponential(60, n) * DAY
promo = channel == "promo_july"
rate[promo] *= 0.6
life[promo] = rng.exponential(12, promo.sum()) * DAY

# ================= сессии и заказы =================
S, O, AB = [], [], []
sid, oid = 1, 5_000_001

for i in range(n):
    uid, plat, cty = int(user_ids[i]), platform[i], city[i]
    t = reg_t[i]
    stop = min(reg_t[i] + life[i], T_END)
    assigned, group = None, None
    first = True
    while t < stop:
        wd = (int(t // DAY) + 3) % 7  # 1970-01-01 был четвергом
        if first or rng.random() < WEEKDAY_ACCEPT[wd]:
            if t >= T_TEST and assigned is None:
                assigned, group = t, ab_group(uid)
                AB.append((uid, group, t))

            cart = rng.random() < P_CART
            chk = cart and rng.random() < P_CHECKOUT
            p = P_ORDER_OLD
            if group == "test":
                p += TEST_EFFECT[plat] + NOVELTY * np.exp(-(t - assigned) / DAY / 4)
            ordered = chk and rng.random() < p
            S.append((sid, uid, t, plat, cart, chk, ordered))

            if ordered:
                mu = AOV_MU[plat] + np.log(CITY_AOV[cty])
                if group == "test":
                    mu += np.log(AOV_TEST_MULT)
                amount = round(float(rng.lognormal(mu, 0.45)), 2)
                items = max(1, int(round(amount / rng.uniform(140, 260))))
                p_cancel = 0.09 if (group == "test" and plat == "android") else 0.05
                status = "cancelled" if rng.random() < p_cancel else "delivered"
                O.append((oid, uid, sid, t + rng.integers(60, 900), plat, items, amount, status))
                oid += 1
            sid += 1
        first = False
        t += rng.exponential(1 / rate[i])
    if i % 10_000 == 0:
        print(f"  пользователей обработано: {i:,}/{n:,}")


def to_ts(x):
    return pd.to_datetime(np.asarray(x, dtype="float64"), unit="s").floor("s")


users = pd.DataFrame({
    "user_id": user_ids,
    "registered_at": to_ts(reg_t),
    "platform": platform,
    "city": city,
    "acquisition_channel": channel,
})
sessions = pd.DataFrame(S, columns=["session_id", "user_id", "session_start", "platform",
                                    "added_to_cart", "reached_checkout", "made_order"])
sessions["session_start"] = to_ts(sessions["session_start"])
orders = pd.DataFrame(O, columns=["order_id", "user_id", "session_id", "created_at",
                                  "platform", "items_cnt", "amount_rub", "status"])
orders["created_at"] = to_ts(orders["created_at"])
ab = pd.DataFrame(AB, columns=["user_id", "ab_group", "assigned_at"])
ab["assigned_at"] = to_ts(ab["assigned_at"])

# ================= «грязь», как в жизни =================
day_mask = orders["created_at"].dt.date == pd.Timestamp("2026-06-15").date()
dups = orders[day_mask].sample(frac=0.9, random_state=SEED).copy()
dups["order_id"] = np.arange(oid, oid + len(dups))
dups["created_at"] = dups["created_at"] + pd.Timedelta(seconds=2)
orders = pd.concat([orders, dups]).sort_values("created_at").reset_index(drop=True)

users.to_csv(OUT / "users.csv", index=False)
sessions.to_csv(OUT / "sessions.csv", index=False)
orders.to_csv(OUT / "orders.csv", index=False)
ab.to_csv(OUT / "ab_assignments.csv", index=False)

print(f"users: {len(users):,} | sessions: {len(sessions):,} | "
      f"orders: {len(orders):,} | ab: {len(ab):,}")
