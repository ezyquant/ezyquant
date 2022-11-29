Colab Example
=============

สามารถเข้าไปดูตัวอย่างการใช้งานบน Colab ได้ที่ link ข้างล่างนี้

https://colab.research.google.com/drive/1OQkNa85wNG12Zjofte8YUUxxEGHAyhcL?usp=sharing

ถ้าใช้ python บน Colab ต้องเอา file database ไปวางไว้ที่ Google drive ก่อนและเชื่อม Google drive ตามนี้

.. code-block::

    from google.colab import drive
    drive.mount('/content/drive')


การใช้งานบน Colab ต้อง install ezyquant ใหม่ทุกครั้ง ที่เปิดขึ้นมาใช้งาน

.. code-block::

    !pip install ezyquant

.. code-block::

    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns

    import ezyquant as ez
    from ezyquant.backtesting import Context

    # ต่อ database
    database_path = "/content/drive/MyDrive/"
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

    # Show Result
    print("CAGR:" + str(round(result.cagr["portfolio_with_dividend"] * 100, 2)) + "%")
    result.summary_df.plot.line(x="timestamp", y="port_value_with_dividend", color="grey")
    print(
        "MaxDD:"
        + str(round(result.pct_maximum_drawdown["portfolio_with_dividend"] * 100, 2))
        + "%"
    )
    result.drawdown_percent_df.plot.area(y="portfolio_with_dividend", color="red")
    print("Win rate:" + str(round(result.pct_win_per_trade * 100, 2)) + "%")
    fig, ax = plt.subplots()
    N, bins, patches = ax.hist(
        result.summary_trade_df["pct_return"], edgecolor="white", linewidth=1
    )

    for i in range(0, len(patches)):
        if patches[i].xy[0] <= 0:
            patches[i].set_facecolor("red")
        else:
            patches[i].set_facecolor("green")

    return_table = (result.monthly_return_df.loc["portfolio"]).replace(np.nan, 0)
    f, ax = plt.subplots(figsize=(20, 6))
    sns.heatmap(
        return_table,
        annot=True,
        fmt=".1%",
        linewidths=0.5,
        ax=ax,
        cmap="PiYG",
        vmin=-0.1,
        vmax=0.1,
    )

    # Save ผลลัพธ์เป็น Excel
    result.to_excel("/content/drive/MyDrive/.../results.xlsx")
