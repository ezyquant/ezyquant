Data Reader
===========

.. currentmodule:: ezyquant.creator

Initialize
----------
เริ่มต้นใช้งานได้โดยตั้งค่าผ่าน :py:class:`SETSignalCreator`

Parameters
   * *start_date : str format [yyyy-mm-dd]*
   * *end_date : str format [yyyy-mm-dd]*
   * *index_list : List[str]*
   * *symbol_list : List[str]*

**ตัวอย่าง** การตั้งค่าเพื่อดึงข้อมูล SET50 และ หุ้น NETBAY ตั้งแต่วันที่ 1/1/2022 ถึง 4/1/2022

.. code-block::

   ssc = ez.SETSignalCreator(
      start_date="2022-01-01", # วันที่ต้องการเริ่มดึง data
      end_date="2022-01-04", # วันที่สิ้นสุดการดึง data
      index_list=['SET50'], # list index ที่ต้องการจะดึงข้อมูล ถ้าไม่ต้องการให้ใส่ list ว่าง
      symbol_list= ['NETBAY'] # list หุ้นที่ต้องการจะดึง ถ้าไม่ต้องการให้ใส่ list ว่าง
   )


GetData
-------
การดึงข้อมูลจะต้องดึงผ่านฟังก์ชั่น :py:meth:`SETSignalCreator.get_data`

Parameters
    * *field: str*
    * *timeframe: str*
    * *value_by: str = "stock"*
    * *method: str = "constant"*
    * *period: int = 1*
    * *shift: int = 0*

GetData with field and timeframe
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

การดึงข้อมูลเบื้องต้นจะต้องใส่ **field** และ **timeframe** โดยจะได้ข้อมูลออกมาเป็น dataframe รายหุ้นเรียงตามวัน

**ตัวอย่าง** การดึงราคาปิดแบบรายวัน

.. code-block::

   close_df = ssc.get_data("close", "daily")

**ตัวอย่าง** การดึงกำไรต่อหุ้นรายไตรมาส

.. code-block::

   eps_qy_df = ssc.get_data("eps", "quarterly")

**ตัวอย่าง** การดึงรายได้รวมรายปี

.. code-block::

   revenue_fy_df = ssc.get_data("total_revenue", "yearly")

**ตัวอย่าง** การดึงรายได้รวม 12 เดือนล่าสุด

.. code-block::

   revenue_ttm_df = ssc.get_data("total_revenue", "ttm")


**ตัวอย่าง** การดึงรายได้รวมถึงรอบบัญชีปีปัจจุบัน

.. code-block::

   revenue_ytd_df = ssc.get_data("total_revenue", "ytd")


GetData with shift
~~~~~~~~~~~~~~~~~~

การดึงข้อมูลย้อนหลังให้ใช้ **shift** ซึ่งข้อมูลจะเลื่อนให้ตาม timeframe ที่ใช้
โดยที่ **shift = 1** จะได้ค่าย้อนหลังไป 1 timeframe

**ตัวอย่าง** การดึงราคาปิดย้อนหลัง 5 วัน

.. code-block::

   close_t_5_df = ssc.get_data(field="close", timeframe="daily", shift=5)

**ตัวอย่าง** การดึงกำไรต่อหุ้นย้อนหลัง 1 ปี

.. code-block::

   revenue_ytd_df = ssc.get_data(field="eps", timeframe="yearly", shift=1)

GetData with value_by
~~~~~~~~~~~~~~~~~~~~~

**value_by** ใช้สำหรับดึงข้อมูลของ **industry** หรือ **sector** แทนข้อมูลหุ้นรายตัว

ซึ่งสามารถใช้ได้กับ timeframe daily เท่านั้น

**ตัวอย่าง** การดึงราคาปิดของ sector index ของหุ้นที่เลือก

.. code-block::

   close_sector_df = ssc.get_data(field="close", timeframe="daily", value_by="sector")

**ตัวอย่าง** การดึง pe ของ industry ของหุ้นที่เลือก

.. code-block::

   pe_industry_df = ssc.get_data(
        field="mkt_pe", timeframe="daily", value_by="industry"
    )


GetData with method and period
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

การดึงข้อมูลที่ต้องมีการประมวลผลเพิ่มเติมให้ใช้ **method** and **period**

**ตัวอย่าง** การดึงค่าเฉลี่ยของ eps ย้อนหลัง 3 ปี

.. code-block::

   avg_3yrs_eps_df = ssc.get_data(
        field="eps", timeframe="yearly", method="mean", period=3
    )

**ตัวอย่าง** การดึงผลรวมของ eps ย้อนหลัง 3 ปี

.. code-block::

   avg_3yrs_eps_df = ssc.get_data(
        field="eps", timeframe="yearly", method="sum", period=3
    )

Screen Universe
---------------

ใช้ในการเปลี่ยน signal หุ้นที่ไม่ได้อยู่ใน Universe หรือ โดน Banned ให้เป็นไปตาม mask ที่ตั้งไว้ ผ่านฟังก์ชั่น :py:meth:`SETSignalCreator.screen_universe`

Parameters
   * *df: pd.DataFrame*
   * *mask_value*

**ตัวอย่าง** การแปลง signal หุ้นที่ไม่ได้อยู่ใน universe กับโดน banned ให้เป็น *

.. code-block::

   final_signal = ssc.screen_universe(signal, mask_value="*")

Rank
----

ใช้ rank หุ้นทุกตัวในแต่ละวัน ผ่านฟังก์ชั่น :py:meth:`SETSignalCreator.rank`

Parameters
    * *factor_df: pd.DataFrame*
    * *quantity: Optional[int] = None*
    * *method: str = "first"*
    * *ascending: bool = True*
    * *pct: bool = False* (ถ้าเป็น True จะเป็น Percentile โดย quantity จะรับค่าระหว่าง 0.0 - 1.0 )

**ตัวอย่าง** การจัดลำดับหุ้นจากน้อยไปมากของราคาปิด และคัดให้เหลือเพียง 10 ตัว

.. code-block::

   df_close = ssc.get_data(field="close", timeframe="daily")
   df_rank_price = ssc.rank(factor_df=df_close, quantity=10, ascending=True)
