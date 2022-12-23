Data Property
=============

SETSignalCreator
----------------

index_list
~~~~~~~~~~

.. csv-table::
   :file: ../_static/index.csv
   :widths: 30,30,30
   :header-rows: 1

is_universe
~~~~~~~~~~~

.. csv-table::
   :file: ../_static/is_universe.csv
   :widths: 30,30,30,30,30,40
   :header-rows: 1

GetData
-------

field
~~~~~

field ที่มามารถใช้ได้ตาม timeframe และ value_by แบบต่างๆ

* get_data(*field*, timeframe = **"daily"**)

.. csv-table::
   :file: ../_static/daily_field.csv
   :widths: 30, 70, 60
   :header-rows: 1

* get_data(*field*, timeframe = **"quarterly"**)
* get_data(*field*, timeframe = **"yearly"**)

.. csv-table::
   :file: ../_static/financial_field.csv
   :widths: 30, 70, 30
   :header-rows: 1

* get_data(*field*, timeframe = **"ytd"**)
* get_data(*field*, timeframe = **"ttm"**)

.. csv-table::
   :file: ../_static/financial_income_cashflow_field.csv
   :widths: 30, 70, 30
   :header-rows: 1

* get_data(*field*, timeframe = **"daily"**, value_by = **"sector"**)
* get_data(*field*, timeframe = **"daily"**, value_by = **"industry"**)

.. csv-table::
   :file: ../_static/sector_industry_field.csv
   :widths: 30, 90
   :header-rows: 1

timeframe
~~~~~~~~~

.. csv-table::
   :file: ../_static/timeframe.csv
   :widths: 30, 70
   :header-rows: 1

method
~~~~~~

.. csv-table::
   :file: ../_static/method.csv
   :widths: 30, 70
   :header-rows: 1

Backtest
--------

price_match_mode
~~~~~~~~~~~~~~~~

.. csv-table::
   :file: ../_static/price_match_mode.csv
   :widths: 30, 70
   :header-rows: 1