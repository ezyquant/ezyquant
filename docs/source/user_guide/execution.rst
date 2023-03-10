Execution
=========

Installation
------------

.. code-block::

    pip install ezyquant-execution

หรือ

.. code-block::

    pip install git+https://github.com/ezyquant/ezyquant-execution


Execute on timer
----------------

1. สร้าง signal จาก ezyquant หรือจากที่อื่น

.. code-block::

    signal_dict = {
        "AOT": 0.2,
        "BBL": 0.2,
        "CPALL": 0.2,
        "DTAC": 0.2,
        "EA": 0.2,
    }

2. ประกาศตัวแปรจาก settrade

.. code-block::

    from settrade_v2.user import Investor

    settrade_user = Investor(
        app_id="app_id",
        app_secret="app_secret",
        app_code="ALGO",
        broker_id="041",
    )
    account_no = "123456"
    pin = "111111"

รายละเอียดเพิ่มเติมเกี่ยวกับการใช้งาน settrade สามารถดูได้ที่ https://developer.settrade.com/open-api/api-reference

3. สร้างฟังก์ชัน on_timer

.. code-block::

    def on_timer(ctx):
        ctx.cancel_all_orders()
        ctx.target_pct_port(ctx.signal)

จากตัวอย่างจะยกเลิก order ทั้งหมดและวาง order ใหม่ตาม signal ที่ได้จาก ezyquant

.. currentmodule:: ezyquant_execution.executing

4. เริ่ม :py:func:`execute_on_timer`

.. code-block::

    from ezyquant_execution import execute_on_timer

    interval = 10

    now = datetime.now()
    start_time = now.time()
    end_time = (now + timedelta(minutes=1)).time()

    execute_on_timer(
        settrade_user=settrade_user,
        account_no=account_no,
        pin=pin,
        signal_dict=signal_dict,
        on_timer=on_timer,
        interval=interval,
        start_time=start_time,
        end_time=end_time,
    )

จากตัวอย่างจะทำงานทุกๆ 10 วินาที ตั้งแต่เวลาปัจจุบันถึง 1 นาที


สามารถดูตัวอย่างเต็มได้ที่ https://github.com/ezyquant/ezyquant-execution/blob/dev/examples/rebalancer.py
