MARKET_SET = "SET"
MARKET_MAI = "MAI"

MARKET_MAP = {
    MARKET_SET: "A",
    MARKET_MAI: "S",
}


"""
SELECT
    DISTINCT("N_INDUSTRY")
FROM
    "SECTOR"
WHERE
    "F_DATA" = 'I'
    AND "D_CANCEL" is null
ORDER BY
    "N_INDUSTRY"
"""
INDUSTRY_AGRO = "AGRO"
INDUSTRY_CONSUMP = "CONSUMP"
INDUSTRY_FINCIAL = "FINCIAL"
INDUSTRY_INDUS = "INDUS"
INDUSTRY_PROPCON = "PROPCON"
INDUSTRY_RESOURC = "RESOURC"
INDUSTRY_SERVICE = "SERVICE"
INDUSTRY_TECH = "TECH"


"""
SELECT
    DISTINCT("N_SECTOR")
FROM
    "SECTOR"
WHERE
    "F_DATA" = 'S'
    AND "I_MARKET" in ('A', 'S')
    AND "D_CANCEL" is null
ORDER BY
    "N_SECTOR"
"""
# SET SECTOR
SECTOR_AGRI = "AGRI"
SECTOR_AUTO = "AUTO"
SECTOR_BANK = "BANK"
SECTOR_COMM = "COMM"
SECTOR_CONMAT = "CONMAT"
SECTOR_CONS = "CONS"
SECTOR_ENERG = "ENERG"
SECTOR_ETRON = "ETRON"
SECTOR_FASHION = "FASHION"
SECTOR_FIN = "FIN"
SECTOR_FOOD = "FOOD"
SECTOR_HELTH = "HELTH"
SECTOR_HOME = "HOME"
SECTOR_ICT = "ICT"
SECTOR_IMM = "IMM"
SECTOR_INSUR = "INSUR"
SECTOR_MEDIA = "MEDIA"
SECTOR_MINE = "MINE"
SECTOR_PAPER = "PAPER"
SECTOR_PERSON = "PERSON"
SECTOR_PETRO = "PETRO"
SECTOR_PFREIT = "PF&REIT"
SECTOR_PKG = "PKG"
SECTOR_PROF = "PROF"
SECTOR_PROP = "PROP"
SECTOR_STEEL = "STEEL"
SECTOR_TOURISM = "TOURISM"
SECTOR_TRANS = "TRANS"
# MAI SECTOR
SECTOR_AGRO = "AGRO"
SECTOR_CONSUMP = "CONSUMP"
SECTOR_FINCIAL = "FINCIAL"
SECTOR_INDUS = "INDUS"
SECTOR_PROPCON = "PROPCON"
SECTOR_RESOURC = "RESOURC"
SECTOR_SERVICE = "SERVICE"
SECTOR_TECH = "TECH"


"""
SELECT
    DISTINCT("SECTOR"."N_SECTOR")
FROM
    "SECURITY_INDEX"
    JOIN "SECTOR" USING("I_SECTOR")
"""
SYMBOL_INDEX_SETWB = "SETWB"
SYMBOL_INDEX_SETTHSI = "SETTHSI"
SYMBOL_INDEX_SETCLMV = "SETCLMV"
SYMBOL_INDEX_SETHD = "SETHD"
SYMBOL_INDEX_SSET = "sSET"
SYMBOL_INDEX_SET100 = "SET100"
SYMBOL_INDEX_SET50 = "SET50"

D_PRIOR = "prior"  # last_close
D_OPEN = "open"
D_HIGH = "high"
D_LOW = "low"
D_CLOSE = "close"
D_AVERAGE = "average"
D_LAST_BID = "last_bid"
D_LAST_OFFER = "last_offer"
D_TRANS = "trans"  # number of transactions
D_VOLUME = "volume"
D_VALUE = "value"

D_PE = "pe"
D_PB = "pb"
D_PAR = "par"
D_DPS = "dps"
D_DVD_YIELD = "dvd_yield"  # last_dividend
D_MKT_CAP = "mkt_cap"
D_EPS = "eps"
D_BOOK_VALUE = "book_value"
D_QUARTER_FIN = "quarter_fin"
D_MONTH_DVD = "month_dvd"
D_AS_OF = "as_of"
D_DIVIDEND = "dividend"
D_STATUS = "status"
D_BENEFIT = "benefit"
D_SHARE_LISTED = "share_listed"
D_TURNOVER = "turnover"
D_SHARE_INDEX = "share_index"
D_NPG = "npg"
D_TOTAL_VOLUME = "total_volume"
D_TOTAL_VALUE = "total_value"
D_BETA = "beta"
D_ROI = "roi"
D_ACC_DPS = "acc_dps"
D_DVD_PAYMENT = "dvd_payment"
D_DVD_PAYOUT = "dvd_payout"
D_EARNING = "earning"
D_IV = "iv"
D_DELTA = "delta"
D_NOTICE = "notice"
D_NON_COMPLIANCE = "non_compliance"
D_STABILIZATION = "stabilization"
D_CALL_MARKET = "call_market"
D_CAUTION = "caution"
D_12M_DVD_YIELD = "12m_dvd_yield"
D_PEG = "peg"


Q_YEAR = "year"
Q_PERIOD_TYPE = "period_type"
Q_PERIOD = "period"
Q_QUARTER = "quarter"
Q_ACCUMULATE = "accumulate"
Q_AS_OF = "as_of"
Q_TOTAL_ASSET = "total_asset"
Q_TOTAL_LIABILITY = "total_liability"
Q_SHLD_EQUITY = "shld_equity"
Q_TOTAL_REVENUE = "total_revenue"
Q_TOTAL_EXPENSE = "total_expense"
Q_NET_PROFIT = "net_profit"
Q_EPS = "eps"
Q_DE = "de"
Q_NET_PROFIT_MARGIN = "net_profit_margin"
Q_GROSS_PROFIT_MARGIN = "gross_profit_margin"
Q_ROA = "roa"
Q_ROE = "roe"
Q_ASSET_TURNOVER = "asset_turnover"
Q_EBIT = "ebit"
Q_FIX_ASSET_TURNOVER = "fix_asset_turnover"
Q_CURRENT_RATIO = "current_ratio"
Q_QUICK_RATIO = "quick_ratio"
Q_INTEREST_COVERAGE = "interest_coverage"
Q_AR_TURNOVER = "ar_turnover"
Q_INVENTORY_TURNOVER = "inventory_turnover"
Q_AP_TURNOVER = "ap_turnover"
Q_CASH_CYCLE = "cash_cycle"
Q_EBITDA = "ebitda"
Q_NET_OPERATING = "net_operating"
Q_NET_INVESTING = "net_investing"
Q_NET_FINANCING = "net_financing"
Q_NET_CASHFLOW = "net_cashflow"
Q_DSCR = "dscr"
Q_IBDE = "ibde"

Q_ACCOUNT_PAYABLE = "account_payable"
Q_ACCOUNT_RECEIVABLE = "account_receivable"
Q_ACCRUED_INT_RECEIVE = "accrued_int_receive"
Q_ALLOWANCE = "allowance"
Q_CAP_PAIDIN = "cap_paidin"
Q_CAP_PAIDUP = "cap_paidup"
Q_CASH = "cash"
Q_COMMON_SHARE = "common_share"
Q_CURRENT_ASSET = "current_asset"
Q_CURRENT_LIABILITY = "current_liability"
Q_DEPOSIT = "deposit"
Q_EARNING_ASSET = "earning_asset"
Q_INT_BEARING_DEBT = "int_bearing_debt"
Q_INVENTORY = "inventory"
Q_INVEST_ASSET = "invest_asset"
Q_INVESTMENT = "investment"
Q_INVEST_SECURITY = "invest_security"
Q_LOAN = "loan"
Q_LOAN_FROM_RELATEDPARTY = "loan_from_relatedparty"
Q_LOAN_REVENUE = "loan_revenue"
Q_LOAN_TO_RELATEDPARTY = "loan_to_relatedparty"
Q_LONGTERM_LIABILITY_CURRENTPORTION = "longterm_liability_currentportion"
Q_LONGTERM_LIABILITY_NET_CURRENTPORTION = "longterm_liability_net_currentportion"
Q_MINORITY_INTEREST = "minority_interest"
Q_PPE = "ppe"
Q_PREFERRED_SHARE = "preferred_share"
Q_RETAIN_EARNING = "retain_earning"
Q_RETAIN_EARNING_UNAPPROPRIATE = "retain_earning_unappropriate"
Q_SHLD_EQUITY = "shld_equity"
Q_SHORT_INVEST = "short_invest"
Q_TOTAL_ASSET = "total_asset"
Q_TOTAL_EQUITY = "total_equity"
Q_TOTAL_LIABILITY = "total_liability"

Q_CHANGE_PPE = "change_ppe"
Q_DIVIDEND = "dividend"
Q_DP = "dp"
Q_NET_CASH_FLOW = "net_cash_flow"
Q_NET_FINANCING = "net_financing"
Q_NET_INVESTING = "net_investing"
Q_NET_OPERATING = "net_operating"

Q_BAD_DEBT = "bad_debt"
Q_BROKER_FEE = "broker_fee"
Q_COS = "cos"
Q_EBIT = "ebit"
Q_EBITDA = "ebitda"
Q_EBT = "ebt"
Q_INT_DVD_INCOME = "int_dvd_income"
Q_INTEREST_EXPENSE = "interest_expense"
Q_INTEREST_INCOME = "interest_income"
Q_INVEST_SEC_REV = "invest_sec_rev"
Q_LOAN_DEPOSIT_REVENUE = "loan_deposit_revenue"
Q_NET_PREMIUM = "net_premium"
Q_NET_PROFIT = "net_profit"
Q_NET_PROFIT_INCL_MINORITY = "net_profit_incl_minority"
Q_NET_PROFIT_ORDINARY = "net_profit_ordinary"
Q_OPERATING_EXPENSE = "operating_expense"
Q_OPERATING_REVENUE = "operating_revenue"
Q_PL_OTHER_ACTIVITIES = "pl_other_activities"
Q_SALE = "sale"
Q_SELLING_ADMIN = "selling_admin"
Q_SELLING_ADMIN_EXC_RENUMURATION = "selling_admin_exc_renumuration"
Q_TOTAL_EXPENSE = "total_expense"
Q_TOTAL_REVENUE = "total_revenue"
Q_EPS = "eps"


D_INDEX_HIGH = "high"
D_INDEX_LOW = "low"
D_INDEX_CLOSE = "close"
D_INDEX_TRI = "tri"

D_INDEX_TOTAL_TRANS = "total_trans"
D_INDEX_TOTAL_VOLUME = "total_volume"
D_INDEX_TOTAL_VALUE = "total_value"
D_INDEX_MKT_PE = "mkt_pe"
D_INDEX_MKT_PBV = "mkt_pbv"
D_INDEX_MKT_YIELD = "mkt_yield"
D_INDEX_MKT_CAP = "mkt_cap"
D_INDEX_MKT_PAR_VALUE = "mkt_par_value"
D_INDEX_TRADING_DAY = "trading_day"
D_INDEX_NEW_COMPANY = "new_company"
D_INDEX_DELISTED_COMPANY = "delisted_company"
D_INDEX_MOVE_IN_COMPANY = "move_in_company"
D_INDEX_MOVE_OUT_COMPANY = "move_out_company"
D_INDEX_LISTED_COMPANY = "listed_company"
D_INDEX_LISTED_STOCK = "listed_stock"


D_SECTOR_INDEX_PRIOR = "prior"
D_SECTOR_INDEX_OPEN = "open"
D_SECTOR_INDEX_HIGH = "high"
D_SECTOR_INDEX_LOW = "low"
D_SECTOR_INDEX_CLOSE = "close"
D_SECTOR_TRANS = "trans"
D_SECTOR_VOLUME = "volume"
D_SECTOR_VALUE = "value"
D_SECTOR_MKT_PE = "mkt_pe"
D_SECTOR_MKT_PBV = "mkt_pbv"
D_SECTOR_MKT_YIELD = "mkt_yield"
D_SECTOR_MKT_CAP = "mkt_cap"
D_SECTOR_TURNOVER = "turnover"
D_SECTOR_SHARE_LISTED_AVG = "share_listed_avg"
D_SECTOR_BETA = "beta"
D_SECTOR_TURNOVER_VOLUME = "turnover_volume"
D_SECTOR_12M_DVD_YIELD = "12m_dvd_yield"

DAILY_STOCK_TRADE_MAP = {
    D_PRIOR: "Z_PRIOR",
    D_OPEN: "Z_OPEN",
    D_HIGH: "Z_HIGH",
    D_LOW: "Z_LOW",
    D_CLOSE: "Z_CLOSE",
    D_AVERAGE: "Z_AVERAGE",
    D_LAST_BID: "Z_LAST_BID",
    D_LAST_OFFER: "Z_LAST_OFFER",
    D_TRANS: "Q_TRANS",
    D_VOLUME: "Q_VOLUME",
    D_VALUE: "M_VALUE",
}

DAILY_STOCK_STAT_MAP = {
    D_PE: "R_PE",
    D_PB: "R_PB",
    D_PAR: "Z_PAR",
    D_DPS: "R_DPS",
    D_DVD_YIELD: "P_DVD_YIELD",
    D_MKT_CAP: "M_MKT_CAP",
    D_EPS: "R_EPS",
    D_BOOK_VALUE: "M_BOOK_VALUE",
    D_QUARTER_FIN: "I_QUARTER_FIN",
    D_MONTH_DVD: "Q_MONTH_DVD",
    D_AS_OF: "D_AS_OF",
    D_DIVIDEND: "D_DIVIDEND",
    D_STATUS: "N_STATUS",
    D_BENEFIT: "N_BENEFIT",
    D_SHARE_LISTED: "Q_SHARE_LISTED",
    D_TURNOVER: "R_TURNOVER",
    D_SHARE_INDEX: "Q_SHARE_INDEX",
    D_NPG: "F_NPG",
    D_TOTAL_VOLUME: "Q_TOTAL_VOLUME",
    D_TOTAL_VALUE: "M_TOTAL_VALUE",
    D_BETA: "R_BETA",
    D_ROI: "R_ROI",
    D_ACC_DPS: "R_ACC_DPS",
    D_DVD_PAYMENT: "Q_DVD_PAYMENT",
    D_DVD_PAYOUT: "R_DVD_PAYOUT",
    D_EARNING: "D_EARNING",
    D_IV: "R_IV",
    D_DELTA: "R_DELTA",
    D_NOTICE: "F_NOTICE",
    D_NON_COMPLIANCE: "F_NON_COMPLIANCE",
    D_STABILIZATION: "F_STABILIZATION",
    D_CALL_MARKET: "F_CALL_MARKET",
    D_CAUTION: "F_CAUTION",
    D_12M_DVD_YIELD: "P_12M_DVD_YIELD",
    D_PEG: "R_PEG",
}


"""
SELECT
    column_name
FROM
    information_schema.columns
WHERE
    table_name = 'FINANCIAL_SCREEN'
ORDER BY
    ordinal_position
"""
FINANCIAL_SCREEN_MAP = {
    Q_YEAR: "I_YEAR",
    Q_PERIOD_TYPE: "I_PERIOD_TYPE",
    Q_PERIOD: "I_PERIOD",
    Q_QUARTER: "I_QUARTER",
    Q_ACCUMULATE: "F_ACCUMULATE",
    Q_AS_OF: "D_AS_OF",
    Q_TOTAL_ASSET: "M_TOTAL_ASSET",
    Q_TOTAL_LIABILITY: "M_TOTAL_LIABILITY",
    Q_SHLD_EQUITY: "M_SHLD_EQUITY",
    Q_TOTAL_REVENUE: "M_TOTAL_REVENUE",
    Q_TOTAL_EXPENSE: "M_TOTAL_EXPENSE",
    Q_NET_PROFIT: "M_NET_PROFIT",
    Q_EPS: "R_EPS",
    Q_DE: "R_DE",
    Q_NET_PROFIT_MARGIN: "R_NET_PROFIT_MARGIN",
    Q_GROSS_PROFIT_MARGIN: "R_GROSS_PROFIT_MARGIN",
    Q_ROA: "R_ROA",
    Q_ROE: "R_ROE",
    Q_ASSET_TURNOVER: "R_ASSET_TURNOVER",
    Q_EBIT: "M_EBIT",
    Q_FIX_ASSET_TURNOVER: "R_FIX_ASSET_TURNOVER",
    Q_CURRENT_RATIO: "R_CURRENT_RATIO",
    Q_QUICK_RATIO: "R_QUICK_RATIO",
    Q_INTEREST_COVERAGE: "R_INTEREST_COVERAGE",
    Q_AR_TURNOVER: "R_AR_TURNOVER",
    Q_INVENTORY_TURNOVER: "R_INVENTORY_TURNOVER",
    Q_AP_TURNOVER: "R_AP_TURNOVER",
    Q_CASH_CYCLE: "Q_CASH_CYCLE",
    Q_EBITDA: "M_EBITDA",
    Q_NET_OPERATING: "M_NET_OPERATING",
    Q_NET_INVESTING: "M_NET_INVESTING",
    Q_NET_FINANCING: "M_NET_FINANCING",
    Q_NET_CASHFLOW: "M_NET_CASHFLOW",
    Q_DSCR: "R_DSCR",
    Q_IBDE: "R_IBDE",
}

"""
SELECT
    DISTINCT "I_ACCT_TYPE",
    "N_ACCOUNT"
FROM
    "FINANCIAL_STAT_STD"
ORDER BY
    "I_ACCT_TYPE",
    "N_ACCOUNT"
"""
FINANCIAL_STAT_STD_MAP = {
    "B": {
        Q_ACCOUNT_PAYABLE: "m_account_payable",
        Q_ACCOUNT_RECEIVABLE: "m_account_receivable",
        Q_ACCRUED_INT_RECEIVE: "m_accrued_int_receive",
        Q_ALLOWANCE: "m_allowance",
        Q_CAP_PAIDIN: "m_cap_paidin",
        Q_CAP_PAIDUP: "m_cap_paidup",
        Q_CASH: "m_cash",
        Q_COMMON_SHARE: "m_common_share",
        Q_CURRENT_ASSET: "m_current_asset",
        Q_CURRENT_LIABILITY: "m_current_liability",
        Q_DEPOSIT: "m_deposit",
        Q_EARNING_ASSET: "m_earning_asset",
        Q_INT_BEARING_DEBT: "m_int_bearing_debt",
        Q_INVENTORY: "m_inventory",
        Q_INVEST_ASSET: "m_invest_asset",
        Q_INVESTMENT: "m_investment",
        Q_INVEST_SECURITY: "m_invest_security",
        Q_LOAN: "m_loan",
        Q_LOAN_FROM_RELATEDPARTY: "m_loan_from_relatedparty",
        Q_LOAN_REVENUE: "m_loan_revenue",
        Q_LOAN_TO_RELATEDPARTY: "m_loan_to_relatedparty",
        Q_LONGTERM_LIABILITY_CURRENTPORTION: "m_longterm_liability_currentportion",
        Q_LONGTERM_LIABILITY_NET_CURRENTPORTION: "m_longterm_liability_net_currentportion",
        Q_MINORITY_INTEREST: "m_minority_interest",
        Q_PPE: "m_ppe",
        Q_PREFERRED_SHARE: "m_preferred_share",
        Q_RETAIN_EARNING: "m_retain_earning",
        Q_RETAIN_EARNING_UNAPPROPRIATE: "m_retain_earning_unappropriate",
        Q_SHLD_EQUITY: "m_shld_equity",
        Q_SHORT_INVEST: "m_short_invest",
        Q_TOTAL_ASSET: "m_total_asset",
        Q_TOTAL_EQUITY: "m_total_equity",
        Q_TOTAL_LIABILITY: "m_total_liability",
    },
    "C": {
        Q_CHANGE_PPE: "m_change_ppe",
        Q_DIVIDEND: "m_dividend",
        Q_DP: "m_dp",
        Q_NET_CASH_FLOW: "m_net_cash_flow",
        Q_NET_FINANCING: "m_net_financing",
        Q_NET_INVESTING: "m_net_investing",
        Q_NET_OPERATING: "m_net_operating",
    },
    "I": {
        Q_BAD_DEBT: "m_bad_debt",
        Q_BROKER_FEE: "m_broker_fee",
        Q_COS: "m_cos",
        Q_EBIT: "m_ebit",
        Q_EBITDA: "m_ebitda",
        Q_EBT: "m_ebt",
        Q_INT_DVD_INCOME: "m_int_dvd_income",
        Q_INTEREST_EXPENSE: "m_interest_expense",
        Q_INTEREST_INCOME: "m_interest_income",
        Q_INVEST_SEC_REV: "m_invest_sec_rev",
        Q_LOAN_DEPOSIT_REVENUE: "m_loan_deposit_revenue",
        Q_NET_PREMIUM: "m_net_premium",
        Q_NET_PROFIT: "m_net_profit",
        Q_NET_PROFIT_INCL_MINORITY: "m_net_profit_incl_minority",
        Q_NET_PROFIT_ORDINARY: "m_net_profit_ordinary",
        Q_OPERATING_EXPENSE: "m_operating_expense",
        Q_OPERATING_REVENUE: "m_operating_revenue",
        Q_PL_OTHER_ACTIVITIES: "m_pl_other_activities",
        Q_SALE: "m_sale",
        Q_SELLING_ADMIN: "m_selling_admin",
        Q_SELLING_ADMIN_EXC_RENUMURATION: "m_selling_admin_exc_renumuration",
        Q_TOTAL_EXPENSE: "m_total_expense",
        Q_TOTAL_REVENUE: "m_total_revenue",
        Q_EPS: "r_eps",
    },
}


MKTSTAT_DAILY_INDEX_MAP = {
    D_INDEX_HIGH: "R_INDEX_HIGH",
    D_INDEX_LOW: "R_INDEX_LOW",
    D_INDEX_CLOSE: "R_INDEX_CLOSE",
    D_INDEX_TRI: "R_TRI",
}

MKTSTAT_DAILY_MARKET = {
    D_INDEX_TOTAL_TRANS: "Q_TOTAL_TRANS",
    D_INDEX_TOTAL_VOLUME: "Q_TOTAL_VOLUME",
    D_INDEX_TOTAL_VALUE: "M_TOTAL_VALUE",
    D_INDEX_MKT_PE: "M_MKT_PE",
    D_INDEX_MKT_PBV: "M_MKT_PBV",
    D_INDEX_MKT_YIELD: "M_MKT_YIELD",
    D_INDEX_MKT_CAP: "M_MKT_CAP",
    D_INDEX_MKT_PAR_VALUE: "M_MKT_PAR_VALUE",
    D_INDEX_TRADING_DAY: "Q_TRADING_DAY",
    D_INDEX_NEW_COMPANY: "Q_NEW_COMPANY",
    D_INDEX_DELISTED_COMPANY: "Q_DELISTED_COMPANY",
    D_INDEX_MOVE_IN_COMPANY: "Q_MOVE_IN_COMPANY",
    D_INDEX_MOVE_OUT_COMPANY: "Q_MOVE_OUT_COMPANY",
    D_INDEX_LISTED_COMPANY: "Q_LISTED_COMPANY",
    D_INDEX_LISTED_STOCK: "Q_LISTED_STOCK",
}


DAILY_SECTOR_INFO_MAP = {
    D_SECTOR_INDEX_PRIOR: "R_INDEX_PRIOR",
    D_SECTOR_INDEX_OPEN: "R_INDEX_OPEN",
    D_SECTOR_INDEX_HIGH: "R_INDEX_HIGH",
    D_SECTOR_INDEX_LOW: "R_INDEX_LOW",
    D_SECTOR_INDEX_CLOSE: "R_INDEX_CLOSE",
    D_SECTOR_TRANS: "Q_TRANS",
    D_SECTOR_VOLUME: "Q_VOLUME",
    D_SECTOR_VALUE: "M_VALUE",
    D_SECTOR_MKT_PE: "M_MKT_PE",
    D_SECTOR_MKT_PBV: "M_MKT_PBV",
    D_SECTOR_MKT_YIELD: "M_MKT_YIELD",
    D_SECTOR_MKT_CAP: "M_MKT_CAP",
    D_SECTOR_TURNOVER: "R_TURNOVER",
    D_SECTOR_SHARE_LISTED_AVG: "Q_SHARE_LISTED_AVG",
    D_SECTOR_BETA: "R_BETA",
    D_SECTOR_TURNOVER_VOLUME: "Q_TURNOVER_VOLUME",
    D_SECTOR_12M_DVD_YIELD: "P_12M_DVD_YIELD",
}