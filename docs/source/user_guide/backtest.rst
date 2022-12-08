BacktestAlgorithm
=================

Step 0: Initialize Data
-----------------------

**ตัวอย่าง** การ setup เพื่อจำลองการซื้อขายหุ้น AOT, BBL และ PTT ตั้งแต่วันที่ 01/01/2020 ถึง 05/05/2022

.. code-block::

    import numpy as np
    import ezyquant as ez
    from ezyquant.backtesting import Context

    start_date = "2020-01-01"
    end_date = "2022-05-05"

    ssc = ez.SETSignalCreator(
        start_date=start_date,
        end_date=end_date,
        index_list=[],
        symbol_list=["AOT", "BBL", "PTT"],
    )


Step 1: Create Signal Dataframe
-------------------------------

ขั้นตอนแรกต้องมีการสร้างสัญญาณซื้อขายหุ้นขึ้นมาเก็บไว้ใน signal_df ก่อน
ซึ่งสัญญาณจะเป็น int, float หรือ boolean ก็ได้ ซึ่งจะถูกนำไปใช้งานต่อที่ BacktestAlgorithm อีกที

**ตัวอย่าง** การสร้าง signal_df ให้เป็น True เมื่อ EMA(20) > EMA(100) และ เป็น False เมื่อ EMA(20) < EMA(100)

.. code-block::

    df_close = ssc.get_data("close", "daily")
    ema20 = ssc.ta.ema(df_close, 20)
    ema100 = ssc.ta.ema(df_close, 100)
    signal_df = ema20 > ema100

Step 2: Create Backtest Algorithm
---------------------------------

.. currentmodule:: ezyquant.backtesting.context

ขั้นตอนต่อไปเป็นการเขียน Backtest Algorithm โดยจะต้อง return จำนวนหุ้นที่ต้องการซื้อขาย

โดยถ้าซื้อให้เป็นตัวเลขบวก และขายเป็นตัวเลขลบ

อย่างเช่น return 400 แปลว่าซื้อเพิ่ม 400 หุ้น หรือ return -500 แปลว่าขายออก 500 หุ้น

การรับค่ามาใช้งานให้รับจาก :py:class:`Context` ซึ่งมี attribute และ method ตามนี้

**Attribute**

.. autosummary::
    Context.cash
    Context.close_price
    Context.cost_price
    Context.port_value
    Context.signal
    Context.symbol
    Context.total_cost_value
    Context.total_market_value
    Context.volume
    Context.ts

**Method**

.. autosummary::
    Context.buy_pct_port
    Context.buy_pct_position
    Context.buy_value
    Context.sell_pct_port
    Context.sell_pct_position
    Context.sell_value
    Context.target_pct_port
    Context.target_value

**ตัวอย่าง** การสร้าง backtest_algorithm ที่เมื่อใด signal เป็น True ให้ถือ 20% ของพอร์ต และเป็น False ให้ขายทิ้งทั้งหมด

.. code-block::

    def backtest_algorithm(c: Context):
        if c.symbol == "AOT":
            print("Portfolio on ", c.ts)
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

Step 3: Run Backtesting
-----------------------

.. currentmodule:: ezyquant.backtesting.backtesting

หลังจากที่ได้ signal และ backtest algorithm แล้วให้นำมาใส่ฟังก์ชั่น :py:func:`backtest`

Parameters
    * *signal_df: pd.DataFrame*
    * *backtest_algorithm: Callable[[Context], float]*
    * *start_date: str*
    * *end_date: str*
    * *initial_cash: float*
    * *pct_commission: float = 0.0*
    * *pct_buy_slip: float = 0.0*
    * *pct_sell_slip: float = 0.0*
    * *price_match_mode: str = "open"*
    * *signal_delay_bar: int = 1*


**ตัวอย่าง** การตั้งค่า backtest ตั้งแต่วันที่ 1/1/2022 ถึง 4/1/2022 ด้วยเงินเริ่มต้น 1 ล้านบาท ค่าคอมมิชชั่น 0.25% ไม่มี slipage และซื้อที่ราคาเปิดวันถัดไป

.. code-block::

    result = ez.backtest(
        signal_df=signal_df,
        backtest_algorithm=backtest_algorithm,
        start_date=start_date,  # วันเริ่มต้นต้องตรงกับวันเริ่มที่อยู่ใน signal_df
        end_date=end_date,  # วันสิ้นสุดต้องตรงกับวันสิ้นสุดที่อยู่ใน signal_df
        initial_cash=1e6,  # เงินลงทุนตั้งต้น
        pct_commission=0.25,  # เปอร์เซ็นต์ค่าคอมมิชชั่น
        pct_buy_slip=0.0,  # เปอร์เซ็นต์การซื้อที่คลาดเคลื่อน
        pct_sell_slip=0.0,  # เปอร์เซ็นต์การขายที่คลาดเคลื่อน
        price_match_mode="open",  # ราคาที่อยากให้เกิดการซื้อขายแบบจำลอง
        signal_delay_bar=1,  # ตำแหน่งแท่งเทียนที่จะให้มีการซื้อขายหลังเกิดสัญญาณ
    )

Step 4: Export Result
---------------------

**ตัวอย่าง** การสร้าง Excel จากผลลัพธ์การ Backtest

.. code-block::

    result.to_excel(r".../results.xlsx")  # ใส่ path ที่ต้องการจะ save excel file.

