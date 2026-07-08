"""Yerel SQLite portfoy defteri: iki bagimsiz kasa (FUND: haftalik fon, DAILY: gunluk hisse)."""
from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

DB_PATH = Path(__file__).resolve().parent / "portfolio.db"

BUCKETS = {"FUND": "Haftalık Fon Kasası", "DAILY": "Günlük İşlem Kasası"}
INITIAL_BALANCE = {"FUND": 20_000.0, "DAILY": 10_000.0}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cash_ledger (
                bucket TEXT PRIMARY KEY,
                balance REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bucket TEXT NOT NULL,
                instrument_code TEXT NOT NULL,
                instrument_name TEXT,
                side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                trade_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        for bucket, initial in INITIAL_BALANCE.items():
            conn.execute(
                "INSERT OR IGNORE INTO cash_ledger (bucket, balance) VALUES (?, ?)",
                (bucket, initial),
            )
        conn.commit()
    finally:
        conn.close()


def get_balance(bucket: str) -> float:
    conn = get_connection()
    try:
        row = conn.execute("SELECT balance FROM cash_ledger WHERE bucket = ?", (bucket,)).fetchone()
        return float(row["balance"]) if row else 0.0
    finally:
        conn.close()


def set_balance(bucket: str, new_balance: float) -> None:
    """Kasa bakiyesini dogrudan gunceller (yatirilacak/planlanan butceyi elle ayarlamak icin).

    Islem gecmisini etkilemez; sadece nakit bakiyeyi yeni deger olarak yazar.
    """
    if bucket not in BUCKETS:
        raise ValueError(f"Gecersiz kasa: {bucket}")
    if new_balance < 0:
        raise ValueError("Bakiye negatif olamaz")
    conn = get_connection()
    try:
        conn.execute("UPDATE cash_ledger SET balance = ? WHERE bucket = ?", (float(new_balance), bucket))
        conn.commit()
    finally:
        conn.close()


def add_transaction(
    bucket: str,
    instrument_code: str,
    instrument_name: str,
    side: str,
    quantity: float,
    price: float,
    trade_date: dt.date,
) -> None:
    if bucket not in BUCKETS:
        raise ValueError(f"Gecersiz kasa: {bucket}")
    if side not in ("BUY", "SELL"):
        raise ValueError(f"Gecersiz islem tipi: {side}")
    if quantity <= 0 or price <= 0:
        raise ValueError("Adet ve fiyat sifirdan buyuk olmalidir")

    cost = quantity * price
    conn = get_connection()
    try:
        balance = float(conn.execute("SELECT balance FROM cash_ledger WHERE bucket = ?", (bucket,)).fetchone()["balance"])

        if side == "BUY":
            if cost > balance + 1e-6:
                raise ValueError(f"Yetersiz bakiye: kasada {balance:.2f} TL var, {cost:.2f} TL gerekiyor")
            new_balance = balance - cost
        else:
            positions = _compute_positions(conn, bucket)
            held_qty = positions.get(instrument_code.upper(), {}).get("quantity", 0.0)
            if quantity > held_qty + 1e-6:
                raise ValueError(f"Yetersiz pozisyon: elinizde {held_qty} adet var, {quantity} adet satmaya calisiyorsunuz")
            new_balance = balance + cost

        conn.execute(
            """
            INSERT INTO transactions (bucket, instrument_code, instrument_name, side, quantity, price, trade_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bucket,
                instrument_code.upper(),
                instrument_name,
                side,
                quantity,
                price,
                trade_date.isoformat(),
                dt.datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.execute("UPDATE cash_ledger SET balance = ? WHERE bucket = ?", (new_balance, bucket))
        conn.commit()
    finally:
        conn.close()


def get_transactions(bucket: str) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM transactions WHERE bucket = ? ORDER BY trade_date, id",
            (bucket,),
        ).fetchall()
    finally:
        conn.close()


@dataclass
class Position:
    instrument_code: str
    instrument_name: str
    quantity: float
    avg_cost: float
    realized_pnl: float


def _compute_positions(conn: sqlite3.Connection, bucket: str) -> dict[str, dict]:
    rows = conn.execute(
        "SELECT * FROM transactions WHERE bucket = ? ORDER BY trade_date, id",
        (bucket,),
    ).fetchall()
    positions: dict[str, dict] = {}
    for row in rows:
        code = row["instrument_code"]
        pos = positions.setdefault(
            code,
            {"instrument_name": row["instrument_name"], "quantity": 0.0, "avg_cost": 0.0, "realized_pnl": 0.0},
        )
        if row["side"] == "BUY":
            total_cost = pos["quantity"] * pos["avg_cost"] + row["quantity"] * row["price"]
            pos["quantity"] += row["quantity"]
            pos["avg_cost"] = total_cost / pos["quantity"] if pos["quantity"] else 0.0
        else:
            pos["realized_pnl"] += (row["price"] - pos["avg_cost"]) * row["quantity"]
            pos["quantity"] -= row["quantity"]
    return {code: pos for code, pos in positions.items() if pos["quantity"] > 1e-9 or pos["realized_pnl"] != 0}


def get_positions(bucket: str) -> dict[str, dict]:
    conn = get_connection()
    try:
        return _compute_positions(conn, bucket)
    finally:
        conn.close()


def get_portfolio_summary(bucket: str, price_lookup: Callable[[str], float | None]) -> dict:
    balance = get_balance(bucket)
    positions = get_positions(bucket)
    total_market_value = 0.0
    enriched = {}
    for code, pos in positions.items():
        price = price_lookup(code) if pos["quantity"] > 1e-9 else None
        market_value = (price or 0.0) * pos["quantity"]
        unrealized_pnl = (price - pos["avg_cost"]) * pos["quantity"] if price is not None else None
        total_market_value += market_value
        enriched[code] = {**pos, "guncel_fiyat": price, "piyasa_degeri": market_value, "gerceklesmemis_kz": unrealized_pnl}
    return {
        "bakiye": balance,
        "pozisyon_degeri": total_market_value,
        "toplam_deger": balance + total_market_value,
        "pozisyonlar": enriched,
    }
