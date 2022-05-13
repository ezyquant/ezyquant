## **class SETDataReader**

```python
class SETDataReader(self, sqlite_path: str)-> None:
```

**Parameters**

- <span style="color:teal"> sqlite_path </span> (str): path to sqlite file e.g. /path/to/sqlite.db

<!------------------------------------------------------------------------------------------------------->

### **get_trading_dates**

```python title="- ดึงข้อมูล วันทำการซื้อขายของตลาดหลักทรัพย์"
def get_trading_dates(
    self,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> List[datetime.date]:
```

**Parameters**

- <span style="color:teal"> start_date </span> (Optional[date]): start of D_TRADE, by default None
- <span style="color:teal"> end_date </span> (Optional[date]): end of D_TRADE, by default None

**Return**

- <span style="color:teal"> List[date] </span>: list of trading dates

<!------------------------------------------------------------------------------------------------------->

### **is_trading_date**

```python
def is_trading_date(self, check_date: datetime.date) -> bool:
```

**Parameters**

- <span style="color:teal"> date </span> (date) : D_TRADE

**Return**

- <span style="color:teal"> bool </span>: is trading date

<!------------------------------------------------------------------------------------------------------->

### **is_today_trading_date**

```python
def is_today_trading_date(self) -> bool:
```

**Return**

- <span style="color:teal"> bool </span> : is today trading date

<!------------------------------------------------------------------------------------------------------->

### **get_symbol_info**

```python
def get_symbol_info(
    self,
    symbol_list: Union[List[str], NoneType] = None,
    market: Union[str, NoneType] = None,
    industry: Union[str, NoneType] = None,
    sector: Union[str, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None
- <span style="color:teal"> market </span> (Optional[str]) : I_MARKET e.g. 'SET', 'MAI', by default None
- <span style="color:teal"> industry </span> (Optional[str]) : SECTOR.N_INDUSTRY, by default None
- <span style="color:teal"> sector </span> (Optional[str]) : SECTOR.N_SECTOR, by default None

**Return**

- <span style="color:teal"> pd.DataFrame </span> : symbol info dataframe contain columns:

  - symbol_id: int - I_SECURITY
  - symbol: str - N_SECURITY
  - market: str - I_MARKET
  - industry: str - SECTOR.N_INDUSTRY
  - sector: str - SECTOR.N_SECTOR
  - sec_type: str - I_SEC_TYPE
  - native: str - I_NATIVE

<!------------------------------------------------------------------------------------------------------->

### **get_company_info**

```python
def get_company_info(
    self,
    symbol_list: Union[List[str], NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : SECURITY.N_SECURITY in symbol_list, case insensitive, must be unique, by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : company info dataframe contain columns:

  - company_id: int - I_COMPANY
  - symbol: str - SECURITY.N_SECURITY
  - company_name_t: str - N_COMPANY_T
  - company_name_e: str - N_COMPANY_E
  - address_t: str - A_COMPANY_T
  - address_e: str - A_COMPANY_E
  - zip: str - I_ZIP
  - tel: str - E_TEL
  - fax: str - E_FAX
  - email: str - E_EMAIL
  - url: str - E_URL
  - establish: date - D_ESTABLISH
  - dvd_policy_t: str - E_DVD_POLICY_T
  - dvd_policy_e: str - E_DVD_POLICY_E

<!------------------------------------------------------------------------------------------------------->

### **get_change_name**

```python
def get_change_name(
    self,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of effect_date (D_EFFECT), by default None

- <span style="color:teal"> end_date </span> (Optional[date]) : end of effect_date (D_EFFECT), by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : change name dataframe contain columns:

  - symbol_id: int - I_SECURITY
  - symbol: str - SECURITY.N_SECURITY
  - effect_date: date - D_EFFECT
  - symbol_old: str - N_SECURITY_OLD
  - symbol_new: str - N_SECURITY_NEW

<!------------------------------------------------------------------------------------------------------->

### **get_dividend**

```python
def get_dividend(
    self,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None,
    ca_type_list: Union[List[str], NoneType] = None,
    adjusted_list: List[str] = ['  ', 'CR', 'PC', 'RC', 'SD', 'XR']
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> symbol_list </span> : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of ex_date (D_SIGN), by default None

- <span style="color:teal"> end_date </span> (Optional[date]) : end of ex_date (D_SIGN), by default None

- <span style="color:teal"> ca_type_list </span> (Optional[List[str]]) : Coperatie action type (N_CA_TYPE), by default None

  - CD - cash dividend
  - SD - stock dividend

- <span style="color:teal"> adjusted_list </span> (List[str]) : Adjust data by ca_type, empty list for no adjust, by default [" ", "CR", "PC", "RC", "SD", "XR"]

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : dividend dataframe contain columns:

  - symbol: str - SECURITY.N_SECURITY
  - ex_date: date - D_SIGN
  - pay_date: date - D_BEG_PAID
  - ca_type: str - N_CA_TYPE
  - dps: int - Z_RIGHTS

<!------------------------------------------------------------------------------------------------------->

### **get_delisted**

```python
def get_delisted(
    self,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of delisted_date (D_DELISTED), by default None

- <span style="color:teal"> end_date </span> (Optional[date]) : end of delisted_date (D_DELISTED), by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : delisted dataframe contain columns:

  - symbol: str - SECURITY.N_SECURITY
  - delisted_date: date - D_DELISTED

<!------------------------------------------------------------------------------------------------------->

### **get_sign_posting**

```python
def get_sign_posting(
    self,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None,
    sign_list: Union[List[str], NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of hold_date (D_HOLD), by default None

- <span style="color:teal"> end_date </span> (Optional[date]) : end of hold_date (D_HOLD), by default None

- <span style="color:teal"> sign_list </span> (Optional[List[str]]) : N_SIGN in sign_list, by default None

  - C - Caution Flag
  - CM - Call Market
  - DS - Designated
  - H - Halt
  - NC - Non Compliance
  - NP - Notice Pending
  - SP - Suspension
  - ST

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : sp dataframe contain columns:

      - symbol: str - SECURITY.N_SECURITY
      - hold_date: date - D_HOLD
      - sign: str - N_SIGN

  <!------------------------------------------------------------------------------------------------------->

### **get_symbols_by_index**

```python
def get_symbols_by_index(
    self,
    index_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> index_list </span> (Optional[List[str]]) : index (SECTOR.N_SECTOR), case insensitive

  - SETWB
  - SETTHSI
  - SETCLMV
  - SETHD
  - sSET
  - SET100
  - SET50

- <span style="color:teal"> start_date </span> (Optional[date]) : start of as_of_date (D_AS_OF), by default None

- <span style="color:teal"> end_date </span> (Optional[date]) : end of as_of_date (D_AS_OF), by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : - as_of_date: date - D_AS_OF

  - index: str - SECTOR.N_SECTOR
  - symbol: str - SECURITY.N_SECURITY
  - seq: int - SECURITY_INDEX.S_SEQ

**Note**

- <span style="color:teal"> SET50 filter S_SEQ 1-50 </span>

- <span style="color:teal"> SET100 filter S_SEQ 1-100 </span>

- <span style="color:teal"> SETHD filter S_SEQ 1-30 </span>

<!------------------------------------------------------------------------------------------------------->

### **get_adjust_factor**

```python
def get_adjust_factor(
    self,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None,
    ca_type_list: Union[List[str], NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of effect_date (D_EFFECT), by default None

- <span style="color:teal"> end_date </span> (Optional[date]) : end of effect_date (D_EFFECT), by default None

- <span style="color:teal"> ca_type_list </span> (Optional[List[str]]) : Coperatie action type (N_CA_TYPE), by default None

  - 'CR' - Capital Reduction
  - 'PC' - Par Change
  - 'RC' - Ratio Change
  - 'SD' - Stock Dividend
  - 'XR' - Rights

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : adjust factor dataframe contain columns:

  - symbol: str - SECURITY.N_SECURITY
  - effect_date: date - D_EFFECT
  - ca_type: str - N_CA_TYPE
  - adjust_factor: float - R_ADJUST_FACTOR

<!------------------------------------------------------------------------------------------------------->

### **get_data_symbol_daily**

```python
def get_data_symbol_daily(
    self,
    field: str,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None,
    adjusted_list: List[str] = ['  ', 'CR', 'PC', 'RC', 'SD', 'XR']
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> field </span> (str) : Filed of data, case insensitive e.g. 'open', 'high', 'low', 'close', 'volume'. More fields can be found in ezyquant.fields

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of trade_date (D_TRADE), by default None

- <span style="color:teal"> end_date </span> (Optional[date]) : end of trade_date (D_TRADE), by default None

- <span style="color:teal"> adjusted_list </span> (List[str]) : Adjust data by ca_type, empty list for no adjust, by default [" ", "CR", "PC", "RC", "SD", "XR"]

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : dataframe contain:

  - symbol: str as column
  - trade_date: date as index

<!------------------------------------------------------------------------------------------------------->

### **get_data_symbol_quarterly**

```python
def get_data_symbol_quarterly(
    self,
    field: str,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> field </span> (str) : Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of as_of_date (D_AS_OF), by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : end of as_of_date (D_AS_OF), by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : dataframe contain:

  - symbol: str as column
  - as_of_date: date as index

<!------------------------------------------------------------------------------------------------------->

### **get_data_symbol_yearly**

```python
def get_data_symbol_yearly(
    self,
    field: str,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> field </span> (str) : Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of as_of_date (D_AS_OF), by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : end of as_of_date (D_AS_OF), by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : dataframe contain:

  - symbol: str as column
  - as_of_date: date as index

<!------------------------------------------------------------------------------------------------------->

### **get_data_symbol_ttm**

```python
def get_data_symbol_ttm(
    self,
    field: str,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> field </span> (str) : Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of as_of_date (D_AS_OF), by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : end of as_of_date (D_AS_OF), by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : dataframe contain:

  - symbol: str as column
  - as_of_date: date as index

<!------------------------------------------------------------------------------------------------------->

### **get_data_symbol_ytd**

```python
def get_data_symbol_ytd(
    self,
    field: str,
    symbol_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> field </span> (str) : Filed of data, case insensitive e.g. 'roe', 'roa', 'eps'. More fields can be found in ezyquant.fields

- <span style="color:teal"> symbol_list </span> (Optional[List[str]]) : N_SECURITY in symbol_list, case insensitive, must be unique, by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : start of as_of_date (D_AS_OF), by default None

- <span style="color:teal"> start_date </span> (Optional[date]) : end of as_of_date (D_AS_OF), by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : dataframe contain:

  - symbol: str as column
  - as_of_date: date as index

<!------------------------------------------------------------------------------------------------------->

### **get_data_index_daily**

```python
def get_data_index_daily(
    self,
    field: str,
    index_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> field </span> (str) : Filed of data, case insensitive e.g. 'high', 'low', 'close'. More fields can be found in ezyquant.fields

- <span style="color:teal"> index_list </span> (Optional[List[str]]) : N_SECTOR in index_list, case insensitive, by default None. More index can be found in ezyquant.fields

- <span style="color:teal"> start_date </span> (Optional[date]) : start of trade_date (D_TRADE), by default None

- <span style="color:teal"> end_date </span> (Optional[date]) : end of trade_date (D_TRADE), by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : dataframe contain:

  - index: str as column
  - trade_date: date as index

<!------------------------------------------------------------------------------------------------------->

### **get_data_sector_daily**

```python
def get_data_sector_daily(
    self,
    field: str,
    sector_list: Union[List[str], NoneType] = None,
    start_date: Union[datetime.date, NoneType] = None,
    end_date: Union[datetime.date, NoneType] = None
) -> pandas.core.frame.DataFrame:
```

**Parameters**

- <span style="color:teal"> field </span> (str) : Filed of data, case insensitive e.g. 'high', 'low', 'close'. More fields can be found in ezyquant.fields

- <span style="color:teal"> sector_list </span> (Optional[List[str]]) : N_SECTOR in sector_list, case insensitive, by default None. More sector can be found in ezyquant.fields

- <span style="color:teal"> start_date </span> (Optional[date]) : start of trade_date (D_TRADE), by default None

- <span style="color:teal"> end_date </span> (Optional[date]) : end of trade_date (D_TRADE), by default None

**Returns**

- <span style="color:teal"> pd.DataFrame </span> : dataframe contain:

  - sector: str as column
  - trade_date: date as index

<!------------------------------------------------------------------------------------------------------->
