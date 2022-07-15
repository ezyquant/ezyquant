Example
=======

**ตัวอย่าง** การทำ Backtest ทั้งหมด

.. code-block::

    import numpy as np
    import ezyquant as ez
    from ezyquant.backtest import Context

    # ต่อ database
    database_path = "..."
    ez.connect_sqlite(database_path + "ezyquant.db")

    # ดึงข้อมูล
    start_date = "2020-01-01"
    end_date = "2022-05-05"
    ssc = ez.SETSignalCreator(
        start_date=start_date,
        end_date=end_date,
        index_list=[],
        symbol_list=["AOT", "BBL", "PTT"],
    )

    # สร้าง signal
    df_close = ssc.get_data("close", "daily")
    ema20 = ssc.ta.ema(df_close, 20)
    ema100 = ssc.ta.ema(df_close, 100)
    signal_df = ema20 > ema100

    # สร้าง วิธีการซื้อขาย
    def backtest_algorithm(c: Context):
        if c.symbol == "AOT":
            print("Portfoilio on ", c.ts)
            print("Port value = cash + total market value")
            print(c.port_value, " = ", c.cash, " + ", c.total_market_value)
            print("Current Position")
            print("Stock  Volume  Profit/loss")

        if c.volume > 0:
            print(
                c.symbol,
                c.volume,
                round(100 * (c.close_price / c.cost_price - 1), 2),
                "%",
            )

        if c.symbol == "PTT":
            print("------------------------------------------")

        if c.signal == True:
            return c.target_pct_port(0.2)
        else:
            return c.target_pct_port(0)

    # ส่งเข้า Backtest
    result = ez.backtest(
        signal_df=signal_df,
        backtest_algorithm=backtest_algorithm,
        start_date=start_date,
        end_date=end_date,
        initial_cash=1e6,
        pct_commission=0.25,
        pct_buy_slip=0.0,
        pct_sell_slip=0.0,
        price_match_mode="weighted",
        signal_delay_bar=1,
    )

    # Save ผลลัพธ์เป็น Excel
    result.to_excel(
        r"C:/Users/watthikorn.i/Desktop/fintech-git-project/EzyQuant/results.xlsx"
    )
