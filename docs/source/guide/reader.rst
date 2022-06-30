การอ่านข้อมูล
==========

อ่านข้อมูลด้วย SETDataReader

.. code-block::
    
    >>> from ezyquant import fields as fld
    >>> from ezyquant import SETDataReader
    >>> sdr = SETDataReader()
    >>> sdr.get_symbol_info(["BBL"])
       symbol_id symbol market industry sector sec_type native
    0          1    BBL    SET  FINCIAL   BANK        S      L
    >>> sdr.get_symbol_info(sector=fld.SECTOR_MINE)
       symbol_id symbol market industry sector sec_type native
    0        167    THL    SET  RESOURC   MINE        S      L
    1        168  THL-R    SET  RESOURC   MINE        S      R
    2        169  THL-U    SET  RESOURC   MINE        S      U
    3       2968  THL-F    SET  RESOURC   MINE        F      F