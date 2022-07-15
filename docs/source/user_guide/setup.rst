Setup
============

Import Library
--------------

ก่อนใช้งานต้องนำเข้า library ezyquant ก่อน โดยให้ import library ตามนี้

.. code-block::

   import ezyquant as ez
   from ezyquant.backtest.account import SETAccount
   from ezyquant.backtest import Context


Connect Database
-----------------

ขั้นตอนต่อไปเป็นการเชื่อมต่อ Database โดยให้ใส่ database_path ชี้ไปยังที่อยู่ของ file 'ezyquant.db'

.. code-block::

    database_path = '...'
    ez.connect_sqlite(database_path+'ezyquant.db')
