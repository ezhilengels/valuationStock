# =============================================================================
# screening/watchlists.py — Preset NSE Stock Watchlists
#
# Usage:
#   from screening.watchlists import get_watchlist
#   tickers = get_watchlist("nifty50")
# =============================================================================


WATCHLISTS = {

    # ── Nifty 50 ─────────────────────────────────────────────────────────────
    "nifty50": [
        "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
        "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BPCL", "BHARTIARTL",
        "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
        "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
        "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC",
        "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT",
        "LTIM", "M&M", "MARUTI", "NESTLEIND", "NTPC",
        "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN",
        "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
        "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO",
    ],

    # ── Nifty Next 50 ────────────────────────────────────────────────────────
    "niftynext50": [
        "ABB", "ADANIGREEN", "ADANITRANS", "AMBUJACEM", "BAJAJHLDNG",
        "BANKBARODA", "BERGEPAINT", "BEL", "BOSCHLTD", "CANBK",
        "CHOLAFIN", "COLPAL", "DLF", "DMART", "GODREJCP",
        "GAIL", "HAVELLS", "HAL", "ICICIGI", "ICICIPRULI",
        "INDUSTOWER", "IOC", "IRCTC", "JINDALSTEL", "LICI",
        "MARICO", "MCDOWELL-N", "MUTHOOTFIN", "NAUKRI", "NHPC",
        "NMDC", "OFSS", "PAGEIND", "PIDILITIND", "PFC",
        "PIIND", "RECLTD", "SAIL", "SHREECEM", "SIEMENS",
        "SOLARINDS", "SRF", "TATAPOWER", "TORNTPHARM", "TVSMOTOR",
        "UBL", "VEDL", "VOLTAS", "WHIRLPOOL", "ZYDUSLIFE",
    ],

    # ── Nifty Midcap 50 (curated) ─────────────────────────────────────────────
    "midcap50": [
        "ABBOTINDIA", "ABCAPITAL", "ALKEM", "APOLLOTYRE", "ASTRAL",
        "AUROPHARMA", "BALKRISIND", "BATAINDIA", "BIOCON", "CAMS",
        "CANFINHOME", "COFORGE", "CROMPTON", "CUMMINSIND", "DABUR",
        "DEEPAKNITR", "DIXON", "ELGIEQUIP", "EMAMILTD", "ESCORTS",
        "EXIDEIND", "FEDERALBNK", "GLENMARK", "GODREJIND", "GRANULES",
        "HDFCAMC", "IDFCFIRSTB", "IPCALAB", "JBCHEPHARM", "KANSAINER",
        "LALPATHLAB", "LUPIN", "METROPOLIS", "MFSL", "MOTHERSON",
        "MPHASIS", "NATCOPHARM", "OBEROIRLTY", "PERSISTENT", "PFIZER",
        "POLYCAB", "RBLBANK", "RELAXO", "SCHAEFFLER", "SUPREMEIND",
        "TATACOMM", "TORNTPOWER", "TTKPRESTIG", "VGUARD", "ZEEL",
    ],

    # ── Nifty Midcap 100 (extended — adds 50 more mid caps) ──────────────────
    "midcap100": [
        # Existing midcap50 base
        "ABBOTINDIA", "ABCAPITAL", "ALKEM", "APOLLOTYRE", "ASTRAL",
        "AUROPHARMA", "BALKRISIND", "BATAINDIA", "BIOCON", "CAMS",
        "CANFINHOME", "COFORGE", "CROMPTON", "CUMMINSIND", "DABUR",
        "DEEPAKNITR", "DIXON", "ELGIEQUIP", "EMAMILTD", "ESCORTS",
        "EXIDEIND", "FEDERALBNK", "GLENMARK", "GODREJIND", "GRANULES",
        "HDFCAMC", "IDFCFIRSTB", "IPCALAB", "JBCHEPHARM", "KANSAINER",
        "LALPATHLAB", "LUPIN", "METROPOLIS", "MFSL", "MOTHERSON",
        "MPHASIS", "NATCOPHARM", "OBEROIRLTY", "PERSISTENT", "PFIZER",
        "POLYCAB", "RBLBANK", "RELAXO", "SCHAEFFLER", "SUPREMEIND",
        "TATACOMM", "TORNTPOWER", "TTKPRESTIG", "VGUARD", "ZEEL",
        # Additional midcap 51–100
        "AAVAS", "ABFRL", "AIAENG", "AJANTPHARM", "ANGELONE",
        "ASHOKLEY", "ATGL", "ATUL", "BASF", "BFDL",
        "BLUESTARCO", "CAMPUS", "CERA", "COROMANDEL", "CRAFTSMAN",
        "DALBHARAT", "DATAPATTNS", "DELTACORP", "ERIS", "FLUOROCHEM",
        "GESHIP", "GNFC", "GRINDWELL", "HAPPSTMNDS", "HATSUN",
        "IDBI", "IGPL", "IIFL", "INDIAMART", "IRFC",
        "JKLAKSHMI", "JKPAPER", "JSWENERGY", "KAJARIACER", "KESORAMIND",
        "KIMS", "KNR", "KROMARETAIL", "LAURUSLABS", "LXCHEM",
        "MANAPPURAM", "MAZDOCK", "MRPL", "NOCIL", "NUVAMA",
        "OLECTRA", "ORIENTELEC", "PNBHOUSING", "PRESTIGE", "ROUTE",
    ],

    # ── REITs & InvITs ───────────────────────────────────────────────────────
    "reits_invits": [
        # REITs (office)
        "EMBASSY",       # Embassy Office Parks REIT
        "MINDSPACE",     # Mindspace Business Parks REIT
        "BIRET",         # Brookfield India Real Estate Trust
        "NEXUS",         # Nexus Select Trust (retail REIT)
        # InvITs (infrastructure)
        "IRBINVIT",      # IRB Infrastructure Developers InvIT
        "INDIGRID",      # India Grid Trust InvIT
        "POWERGRID",     # PowerGrid Infrastructure InvIT
        "NHAI",          # NHAI InvIT
    ],

    # ── Quality / Value Focus (Buffett-style screen) ──────────────────────────
    "value_quality": [
        "ASIANPAINT", "BRITANNIA", "COLPAL", "DABUR", "HINDUNILVR",
        "ITC", "MARICO", "NESTLEIND", "PIDILITIND", "TATACONSUM",
        "TITAN", "BAJFINANCE", "HDFCBANK", "ICICIBANK", "KOTAKBANK",
        "TCS", "INFY", "HCLTECH", "WIPRO", "LTIM",
        "SUNPHARMA", "DIVISLAB", "DRREDDY", "CIPLA", "APOLLOHOSP",
    ],

    # ── PSU Focus (dividend / value plays) ────────────────────────────────────
    "psu_dividend": [
        "COALINDIA", "ONGC", "POWERGRID", "NTPC", "SBIN",
        "BANKBARODA", "CANBK", "IOC", "BPCL", "GAIL",
        "NHPC", "NMDC", "SAIL", "PFC", "RECLTD",
    ],

    # ── Banking & Finance ─────────────────────────────────────────────────────
    "banking": [
        "HDFCBANK", "ICICIBANK", "KOTAKBANK", "SBIN", "AXISBANK",
        "INDUSINDBK", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB", "RBLBANK",
        "BAJFINANCE", "BAJAJFINSV", "CHOLAFIN", "MUTHOOTFIN", "LICHSGFIN",
    ],

    # ── IT & Technology ───────────────────────────────────────────────────────
    "it_tech": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "LTIM",
        "TECHM", "MPHASIS", "COFORGE", "PERSISTENT", "OFSS",
        "KPITTECH", "TATAELXSI", "MASTEK", "NIITTECH", "HEXAWARE",
    ],

    # ── Pharma & Healthcare ───────────────────────────────────────────────────
    "pharma": [
        "SUNPHARMA", "DIVISLAB", "DRREDDY", "CIPLA", "APOLLOHOSP",
        "LUPIN", "AUROPHARMA", "TORNTPHARM", "ALKEM", "IPCA",
        "GLENMARK", "BIOCON", "NATCOPHARM", "GRANULES", "JBCHEPHARM",
    ],

    # ── Cyclicals (Steel / Cement / Metals) ───────────────────────────────────
    "cyclicals": [
        "TATASTEEL", "JSWSTEEL", "SAIL", "HINDALCO", "VEDL",
        "NMDC", "NATIONALUM", "JINDALSTEL", "RATNAMANI", "APL",
        "ULTRACEMCO", "SHREECEM", "AMBUJACEM", "ACC", "RAMCOCEM",
    ],

    # ── Small / Custom Watchlist (edit as needed) ────────────────────────────
    "custom": [
        "INFY", "HDFCBANK", "COALINDIA",
    ],
     # ── 8 SECTORAL BUCKETS (NSE STANDARD) ───────────────────────────────────
    "financials_v2": [
        "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", 
        "BAJFINANCE", "CHOLAFIN", "RECLTD", "PFC", "HDFCLIFE", "SBILIFE",
        "MUTHOOTFIN"
    ],

    "technology_v2": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT", "COFORGE"
    ],

    "consumer_v2": [
        "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM", 
        "VBL", "TITAN", "ASIANPAINT", "BERGEPAINT", "HAVELLS", "TRENT"
    ],

    "healthcare_v2": [
        "SUNPHARMA", "CIPLA", "DRREDDY", "DIVISLAB", "APOLLOHOSP", 
        "MAXHEALTH", "MANKIND", "TORNTPHARM"
    ],

    "automobile_v2": [
        "TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT", 
        "TVSMOTOR", "HEROMOTOCO", "SONACOMS"
    ],

    "energy_v2": [
        "RELIANCE", "ONGC", "COALINDIA", "BPCL", "NTPC", 
        "POWERGRID", "ADANIGREEN", "TATAPOWER"
    ],

    "materials_v2": [
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "JINDALSTEL", 
        "ULTRACEMCO", "GRASIM", "PIDILITIND", "SRF"
    ],

    "chemicals_v2": [
        "SRF", "DEEPAKNITR", "TATACHEM", "NAVINFLUOR", "AARTIIND", "GUJGASLTD"
    ],

    "infrastructure_v2": [
        "LT", "LICI", "DLF", "BEL", "HAL", "BHEL", "ADANIPORTS", "CONCOR", "SIEMENS"
    ],

    "reliable_bluechips_v2": [
        "TCS", "HDFCBANK", "RELIANCE", "INFY", "HINDUNILVR", "ITC", 
        "LT", "ICICIBANK", "SBIN", "KOTAKBANK", "BAJFINANCE", "SRF",
        "PIDILITIND", "TITAN", "SUNPHARMA", "MARUTI", "ASIANPAINT",
        "ULTRACEMCO", "ADANIPORTS", "TRENT", "VBL"
    ],

    "defensive_v2": [
        "ONGC", "OIL", "HAL", "BEL", "MAZDOCK", "ADANIGREEN", 
        "TATAPOWER", "ITC", "NESTLEIND", "MUTHOOTFIN", "SOLARINDS"
    ],

    # ── 12 NEW SECTORAL BUCKETS ──────────────────────────────────────────────
    "fmcg_staples": [
        "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "COLPAL", "DABUR",
        "MARICO", "TATACONSUM", "GODREJCP", "VBL", "BALRAMCHIN"
    ],

    "realty_construction": [
        "DLF", "GODREJPROP", "OBEROIRLTY", "PHOENIXLTD", "PRESTIGE",
        "LODHA", "SOBHA", "BRIGADE", "SUNTECK"
    ],

    "media_entertainment": [
        "ZEEL", "SUNTV", "PVRINOX", "NETWORK18", "TV18BRDCST",
        "SAREGAMA", "NAZARA"
    ],

    "metals_mining": [
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "NATIONALUM",
        "NMDC", "SAIL", "JINDALSTEL", "HINDZINC", "COALINDIA"
    ],

    "telecom_infrastructure": [
        "BHARTIARTL", "INDUSTOWER", "IDEA", "TTML", "ROUTE", "TEJASNET"
    ],

    "consumer_durables": [
        "HAVELLS", "VOLTAS", "BLUESTARCO", "CROMPTON", "DIXON",
        "RELAXO", "BATAINDIA", "RAJESHEXPO", "TITAN", "AMBER"
    ],

    "hospitality_tourism": [
        "INDHOTEL", "EIHOTEL", "CHALET", "LEMONTREE", "INDIGO",
        "SPICEJET", "IRCTC", "EASEMYTRIP"
    ],

    "agro_fertilizers": [
        "UPL", "PIIND", "COROMANDEL", "SUMICHEM", "BAYERCROP",
        "GNFC", "CHAMBLFERT", "RALLIS"
    ],

    "logistics_shipping": [
        "ADANIPORTS", "CONCOR", "DELHIVERY", "BLUEDART", "GESHIP",
        "SCI", "GATEWAY"
    ],

    "defense_aerospace": [
        "HAL", "BEL", "BDL", "MAZDOCK", "GRSE", "COCHINSHIP",
        "DATA-PATTNS", "ZEN-TECH"
    ],

    "cement_building_mat": [
        "ULTRACEMCO", "SHREECEM", "AMBUJACEM", "ACC", "JKCEMENT",
        "RAMCOCEM", "DALBHARAT", "ASTRAL", "KAYNES"
    ],

    "insurance_amc": [
        "LICI", "HDFCLIFE", "SBILIFE", "ICICIPRULI", "GICRE",
        "NIACL", "HDFCAMC", "NAM-INDIA", "CAMS"
    ],

    # ── 10 DEEP-DIVE SECTORAL BUCKETS ───────────────────────────────────────
    "specialty_chemicals": [
        "DEEPAKNTR", "AARTIIND", "NAVINFLUOR", "VINATIORGA", "CLEAN", 
        "ATUL", "FINEORG", "AMIORG"
    ],

    "bulk_chemicals_fertilizers": [
        "TATACHEM", "GUJALKALI", "UPL", "CHAMBLFERT", "COROMANDEL", 
        "GNFC", "GSFC"
    ],

    "rubber_tyres": [
        "MRF", "APOLLOTYRE", "BALKRISIND", "CEATTD", "JKTYRE", 
        "PIXTRANS", "APCOTEXIND"
    ],

    "synthetic_fibers": [
        "GRASIM", "FILATEX", "SANGAMIND", "SARLAPOLY", "JBFIND", "MAYURUNIQ"
    ],

    "textiles_apparel": [
        "PAGEIND", "KPRMILL", "VARDHMNTEC", "TRIDENT", "WELSPUNLIV", 
        "ARVIND", "RAYMOND"
    ],

    "packaging_solutions": [
        "EPL", "UFLEX", "AGI", "MOLDTKPAC", "TCPLPACK", "HUHTAMAKI", "POLYPLEX"
    ],

    "paper_forest_products": [
        "JKPAPER", "WESTPCPAPER", "SESHAPAPER", "TNPL", "ORIENTPPR"
    ],

    "industrial_machinery": [
        "CUMMINSIND", "KIRLOSENG", "THERMAX", "ELGIEQUIP", "TRIVENI", "KSB"
    ],

    "paints_coatings": [
        "ASIANPAINT", "BERGEPAINT", "KANSAINER", "AKZOINDIA", 
        "INDIGOPNTS", "PIDILITIND"
    ],

    "footwear_luxury": [
        "RELAXO", "METROBRAND", "CAMPUS", "BATAINDIA", "KAYNES", "TITAN"
    ],

    # ── 8 HIGH-GROWTH / NICHE BUCKETS ───────────────────────────────────────
    "railway_infra": [
        "IRFC", "IRCTC", "RVNL", "IRCON", "RAILTEL", "RITES", 
        "TITAGARH", "TEXRAIL"
    ],

    "renewable_green_energy": [
        "ADANIGREEN", "SUZLON", "IREDA", "TATAPOWER", "NHPC", 
        "SJVN", "KPIEL", "SWREL", "INOXWIND"
    ],

    "liquor_spirits": [
        "UNITDSPR", "UBL", "RADICO", "SULA", "GLOBUSSPR", "TI", "SDBL"
    ],

    "sugar_ethanol": [
        "EIDPARRY", "BALRAMCHIN", "TRIVENI", "RENUKA", "DALMIASUG", 
        "DWARKESH", "BAJAJHIND", "PRAJIND"
    ],

    "new_age_tech": [
        "ZOMATO", "PAYTM", "NYKAA", "POLICYBZR", "DELHIVERY", 
        "MAPMYINDIA", "CARTRADE", "OLAELEC"
    ],

    "gems_jewelry": [
        "TITAN", "KALYANKJIL", "SENCO", "RAJESHEXPO", 
        "VAIBHAVGBL", "THANGAMAYL"
    ],

    "defence_advanced_v2": [
        "HAL", "BEL", "BDL", "MAZDOCK", "GRSE", "COCHINSHIP", 
        "DATA-PATTNS", "ZEN-TECH", "SOLARINDS", "MTARTECH"
    ],

    "agri_processing_rice": [
        "LTFOODS", "KRBL", "ADANIWILMAR", "PATANJALI", 
        "AVANTIFEED", "APOLSINHOT"
    ],

    # ── 20 GRANULAR SECTORAL BUCKETS ────────────────────────────────────────
    "cables_wires": [
        "POLYCAB", "KEI", "RRKABEL", "FINCABLES", "VGUARD"
    ],

    "pipes_fittings": [
        "ASTRAL", "SUPREMEIND", "PRINCEPIPE", "FINPIPE", "APLAPOLLO"
    ],

    "ceramics_sanitaryware": [
        "KAJARIACER", "CERA", "SOMANYCERA", "HSIL"
    ],

    "hospitals_healthcare": [
        "APOLLOHOSP", "MAXHEALTH", "FORTIS", "GLOBAL", "NARAYANA", 
        "KIMS", "MEDANTA", "RAINBOW"
    ],

    "diagnostics": [
        "DRLALPATH", "METROPOLIS", "VIJAYA", "THYROCARE"
    ],

    "medical_devices": [
        "POLYMED", "TRANSMED", "TATAELXSI"
    ],

    "stock_broking_wealth": [
        "ANGELONE", "MOTILALOFS", "ICICIGI", "MCX", "CDSL"
    ],

    "asset_management_amc": [
        "HDFCAMC", "NAM-INDIA", "UTIAMC", "ABSMCAPITAL"
    ],

    "registrars_depository": [
        "CAMS", "KFINTECH", "CDSL"
    ],

    "insurance_v2": [
        "LICI", "HDFCLIFE", "SBILIFE", "ICICIGI", "STARHEALTH"
    ],

    "power_transmission": [
        "POWERGRID", "ADANITRANS", "KPTL"
    ],

    "batteries_storage": [
        "EXIDEIND", "AMARAJABAT"
    ],

    "electronics_ems": [
        "DIXON", "KAYNES", "SYRMA", "AMBER", "OPTIMUS"
    ],

    "heavy_engineering": [
        "LT", "ABB", "SIEMENS", "CUMMINSIND", "THERMAX"
    ],

    "precision_engineering": [
        "SKFINDIA", "SCHAEFFLER", "TIMKEN", "AIAENG"
    ],

    "industrial_products": [
        "SUPREMEIND", "AIAENG", "RATNAMANI"
    ],

    "staffing_education": [
        "QUESS", "TEAMLEASE", "NIITLTD", "VERANDA"
    ],

    "ecommerce_logistics": [
        "DELHIVERY", "ECOMEXPRESS", "BLUEDART"
    ],

    "gold_loans": [
        "MUTHOOTFIN", "MANAPPURAM"
    ],

    "microfinance_mfi": [
        "CREDITACC", "SPANDANA", "FUSION", "BANDHANBNK"
    ],

    # ── 20+ NEW GRANULAR GROWW-INSPIRED BUCKETS ───────────────────────────
    "breweries_distilleries": [
        "UNITDSPR", "UBL", "RADICO", "SULA", "SDBL", "GLOBUSSPR"
    ],

    "amusement_parks_leisure": [
        "WONDERLA", "IMAGICAA", "DELTACORP"
    ],

    "hotels_resorts": [
        "INDHOTEL", "EIHOTEL", "CHALET", "LEMONTREE"
    ],

    "abrasives_industrial": [
        "GRINDWELL", "CARBORUNIV"
    ],

    "carbon_black": [
        "PCBL"
    ],

    "dyes_pigments": [
        "BODALCHEM", "KIRIINDUS", "SUDARSCHEM"
    ],

    "tea_coffee_plantations": [
        "TATACONSUM", "CCL", "HARRMALAYA", "BOMBAYBURM"
    ],

    "aquaculture_seafood": [
        "AVANTIFEED", "APEX", "WATERBASE"
    ],

    "agrochemicals_v2": [
        "UPL", "PIIND", "SUMICHEM", "BAYERCROP", "DHARMAJ"
    ],

    "bearings_v2": [
        "SKFINDIA", "SCHAEFFLER", "TIMKEN", "NRBBEARING"
    ],

    "auto_components_tier1": [
        "SONACOMS", "MOTHERSON", "UNOINDA", "ENDURANCE", "CIEINDIA"
    ],

    "castings_forgings": [
        "BHARATFORG", "RKFORGE", "MMFORG", "HAPPYFORG"
    ],

    "animation_creative_tech": [
        "NAZARA", "ZENTEC", "TATAELXSI"
    ],

    "internet_software_services": [
        "NAUKRI", "NYKAA", "ZOMATO", "PAYTM", "MAPMYINDIA"
    ],

    "ports_shipping_v2": [
        "ADANIPORTS", "CONCOR", "GESHIP", "SCI", "GPPL"
    ],

    "roads_highways_epc": [
        "IRB", "KNRCON", "PNCINFRA", "HGINFRA", "GRINFRA"
    ],

    "dredging_offshore": [
        "DREDGECORP", "HAL", "MAZDOCK"
    ],

    "packaging_flexible": [
        "UFLEX", "POLYPLEX", "EPL", "TCPLPACK"
    ],

    "printing_paper_v2": [
        "JKPAPER", "WESTPCPAPER", "SESHAPAPER", "NAVNETEDUL"
    ],

    # ── 20+ NEW SPECIALIZED INDUSTRIAL & MATERIALS ────────────────────────
    "refractories_industrial": [
        "RHIM", "VESUVIUS", "IFGLEXPOR", "RPEL"
    ],

    "graphite_electrodes": [
        "GRAPHITE", "HEG"
    ],

    "solar_glass": [
        "BORORENEW"
    ],

    "automotive_architectural_glass": [
        "ASAHIINDIA"
    ],

    "consumer_lab_glass": [
        "BOROLTD", "LAOPALA", "HALDYNG"
    ],

    "specialty_carbon_advanced": [
        "HSCL", "PCBL", "RAIN", "GOACARBON"
    ],

    "industrial_explosives": [
        "SOLARINDS", "PREMEXPLN", "GOCLCORP"
    ],

    "industrial_fasteners": [
        "SUNDRMFAST", "STERTOOLS"
    ],

    "ductile_iron_pipes": [
        "ELECTCAST", "JINDALSAW"
    ],

    "pumps_valves": [
        "KSB", "KIRLOSBROS", "SHAKTIPUMP", "WPIL"
    ],

    "transmission_towers": [
        "KPTL", "SKIPPER"
    ],

    "lab_equipment_scientific": [
        "BOROLTD"
    ],

    "precision_instruments": [
        "HONAUT", "ABB", "SIEMENS"
    ],

    "lube_oils_grease": [
        "CASTROLIND", "GULFOILLUB", "TIDEWATER"
    ],

    "flavors_fragrances": [
        "S_H_KELKAR"
    ],

    "industrial_gases": [
        "LINDEINDIA"
    ],

    "watches_wearables": [
        "TITAN", "ETHOSLTD"
    ],

    "luggage_bags": [
        "VIPIND", "SAFARI"
    ],

    "water_treatment": [
        "VA_TECH_WABAG", "ION_EXCHANGE"
    ],

    "waste_management": [
        "ANTONY_WASTE"
    ],

    # ── FINAL 11 GRANULAR SPECIALIZED BUCKETS ───────────────────────────────
    "cigarettes_tobacco": [
        "ITC", "GODFREYPHLP", "VSTIND"
    ],

    "detergents_soaps": [
        "HINDUNILVR", "GODREJCP", "JYOTHYLAB"
    ],

    "dairy_products": [
        "HATSUN", "DODLA", "HERITGFOOD", "PARAGMILK"
    ],

    "mattresses_furniture": [
        "SHEELA_FOAM", "NILKAMAL"
    ],

    "air_conditioners": [
        "VOLTAS", "BLUESTARCO", "AMBER", "JCHAC"
    ],

    "seeds_agri_genetics": [
        "KAVERI_SEED", "JKAGRI"
    ],

    "poultry_hatcheries": [
        "VENKEYS"
    ],

    "micro_irrigation": [
        "JISLJALEQS"
    ],

    "transformers_switchgear": [
        "GET&D", "ABB", "SIEMENS", "VOLTAMP"
    ],

    "credit_rating_agencies": [
        "CRISIL", "ICRA", "CAREERP"
    ],

    "online_portals_recruitment": [
        "NAUKRI", "JUSTDIAL"
    ],

    # ── GEOPOLITICAL / WAR TENSION HEDGE ───────────────────────────────────
    "war_tension_hedge": [
        "HAL", "BEL", "BDL", "MAZDOCK", "GRSE", "COCHINSHIP", 
        "DATA-PATTNS", "PREMEXPLN", "ONGC", "OIL", "SCI", "GESHIP", 
        "COALINDIA", "HINDALCO"
    ],

    # ── SEMICONDUCTOR & CHIP ECOSYSTEM (v4) ────────────────────────────────
    "semiconductors_v4": [
        "TATAELXSI", "LTTS", "CYIENT", "MOSCHIP", "TEJASNET", "SASKEN", 
        "KAYNES", "CGPOWER", "DIXON", "SYRMA", "CYIENTDLM", "AVALON", 
        "CENTUM", "ASMTEC", "RIRPOWER", "BHEL", "LINDEINDIA", 
        "GUJFLUORO", "AMIORG", "HSCL"
    ],

    # ── 4 FUTURE-TECH CLUSTERS ─────────────────────────────────────────────
    "green_hydrogen_v5": [
        "RELIANCE", "LT", "ADANIENT", "NTPC", "GAIL", "IOC", 
        "MTARTECH", "CUMMINSIND"
    ],

    "space_tech_v6": [
        "HAL", "BEL", "MTARTECH", "ASTRAMICRO", "DATAPATTNS", 
        "PARAS", "APOLLO", "CENTUM"
    ],

    "ai_infrastructure_v7": [
        "NETWEB", "TATACOMM", "LTTS", "PERSISTENT", "CYIENT", "AFFLE"
    ],

    "drones_uav_v8": [
        "IDEAFORGE", "ZENTEC", "RTNINDIA", "BHARATFORG", "DCMSRIND"
    ],

    # ── 8 EV ECOSYSTEM BUCKETS (v18-v25) ───────────────────────────────────
    "ev_oems_manufacturers_v18": [
        "TATAMOTORS", "M&M", "HYUNDAI", "ASHOKLEY", "OLA", "TVSMOTOR", 
        "BAJAJ-AUTO", "HEROMOTOCO", "OLECTRA", "JBMA"
    ],

    "ev_batteries_tech_v19": [
        "EXIDEIND", "ARE&M", "HBLPOWER", "TATACHEM", "HSCL"
    ],

    "ev_charging_infrastructure_v20": [
        "TATAPOWER", "EXICOM", "SERVOTECH", "ABB"
    ],

    "ev_components_ancillaries_v21": [
        "SONACOMS", "MOTHERSON", "UNOMINDA", "BHARATFORG"
    ],

    "ev_software_design_v22": [
        "KPITTECH", "TATAELXSI"
    ],

    "ev_thermal_management_v23": [
        "SUBROS", "MOTHERSON", "UNOMINDA"
    ],

    "ev_recycling_circular_v24": [
        "GRAVITA", "TATACHEM", "ARE&M", "EXIDEIND"
    ],

    "ev_finance_fintech_v25": [
        "IREDA", "CHOLAFIN", "M&MFIN", "SHRIRAMFIN"
    ],

    # ── HIDDEN GEMS & FUTURE THEMES (v26) ──────────────────────────────────
    "hidden_future_gems_v26": [
        "PRAJIND", "BALRAMCHIN", "ANTONY_WASTE", "VA_TECH_WABAG", "GRAVITA", 
        "ETHOSLTD", "VEDANTFASH", "BIKAJI", "SAPPHIRE", "SYNGENE", 
        "GLAND", "MEDPLUS", "GENUSPOWER", "HPL", "BORORENEW", "SIGNATURE"
    ],

    # ── HIGH-POTENTIAL MULTIBAGGERS (2025-2030) ────────────────────────────
    "multibagger_candidates_2025_2030": [
        "HAL", "BEL", "MAZDOCK", "DATAPATTNS", "ZENTEC",
        "TATAPOWER", "IREDA", "KPIGREEN", "WAAREEENER", "LT",
        "TATAMOTORS", "OLECTRA", "KPITTECH", "SONACOMS", "EXICOM",
        "DIXON", "KAYNES", "AMBER", "SYRMA", "CGPOWER",
        "TATAELXSI", "NETWEB", "PERSISTENT", "AFFLE", "ZOMATO"
    ],

    # ── 6 GRANULAR PSU BUCKETS (v27-v32) ───────────────────────────────────
    "psu_energy_giants_v27": [
        "ONGC", "NTPC", "IOC", "BPCL", "GAIL", "HINDPETRO", "OIL", 
        "POWERGRID", "COALINDIA", "NHPC", "SJVN", "MRPL", "CHENNPETRO"
    ],

    "psu_defense_engineering_v28": [
        "HAL", "BEL", "MAZDOCK", "COCHINSHIP", "BDL", "GRSE", 
        "MIDHANI", "BHEL", "BEML"
    ],

    "psu_railway_logistics_v29": [
        "IRFC", "RVNL", "IRCON", "RITES", "RAILTEL", "IRCTC", "CONCOR", "SCI"
    ],

    "psu_finance_insurance_v30": [
        "PFC", "RECLTD", "IREDA", "HUDCO", "LICI", "GICRE", "NIACL", "IFCI"
    ],

    "psu_mining_metals_infra_v31": [
        "SAIL", "NMDC", "NATIONALUM", "HINDCOPPER", "MOIL", "NLCINDIA", 
        "NBCC", "ENGINERSIN", "ITI", "MTNL"
    ],

    "psu_banks_v32": [
        "SBIN", "BANKBARODA", "CANBK", "UNIONBANK", "INDIANB", "PNB", 
        "IOB", "BANKINDIA", "MAHABANK", "CENTRALBK", "UCOBANK", "PSB"
    ],

    # ── TOTAL PSU MEGA MASTER (v33) ────────────────────────────────────────
    "psu_total_universe_v33": [
        "ONGC", "NTPC", "IOC", "BPCL", "GAIL", "HINDPETRO", "OIL", 
        "POWERGRID", "COALINDIA", "NHPC", "SJVN", "MRPL", "CHENNPETRO",
        "HAL", "BEL", "MAZDOCK", "COCHINSHIP", "BDL", "GRSE", "MIDHANI", 
        "BHEL", "BEML", "IRFC", "RVNL", "IRCON", "RITES", "RAILTEL", 
        "IRCTC", "CONCOR", "SCI", "PFC", "RECLTD", "IREDA", "HUDCO", 
        "LICI", "GICRE", "NIACL", "IFCI", "SAIL", "NMDC", "NATIONALUM", 
        "HINDCOPPER", "MOIL", "NLCINDIA", "NBCC", "ENGINERSIN", "ITI", 
        "MTNL", "SBIN", "BANKBARODA", "CANBK", "UNIONBANK", "INDIANB", 
        "PNB", "IOB", "BANKINDIA", "MAHABANK", "CENTRALBK", "UCOBANK", "PSB"
    ],

    # ── NIFTY 500 MASTER INDEX (10 PHASES) ────────────────────────────────
    "nifty500_phase_1": ['360ONE', '3MINDIA', 'ABB', 'ACC', 'ACMESOLAR', 'AIAENG', 'APLAPOLLO', 'AUBANK', 'AWL', 'AADHARHFC', 'AARTIIND', 'AAVAS', 'ABBOTINDIA', 'ACE', 'ACUTAAS', 'ADANIENSOL', 'ADANIENT', 'ADANIGREEN', 'ADANIPORTS', 'ADANIPOWER', 'ATGL', 'ABCAPITAL', 'ABFRL', 'ABLBL', 'ABREL', 'ABSLAMC', 'CPPLUS', 'AEGISLOG', 'AEGISVOPAK', 'AFCONS', 'AFFLE', 'AJANTPHARM', 'AKZOINDIA', 'ALKEM', 'ABDL', 'ARE&M', 'AMBER', 'AMBUJACEM', 'ANANDRATHI', 'ANANTRAJ', 'ANGELONE', 'ANTHEM', 'ANURAS', 'APARINDS', 'APOLLOHOSP', 'APOLLOTYRE', 'APTUS', 'ASAHIINDIA', 'ASHOKLEY', 'ASIANPAINT'],
    "nifty500_phase_2": ['ASTERDM', 'ASTRAL', 'ATHERENERG', 'ATUL', 'AUROPHARMA', 'AIIL', 'DMART', 'AXISBANK', 'BEML', 'BLS', 'BSE', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BAJAJHLDNG', 'BAJAJHFL', 'BALKRISIND', 'BALRAMCHIN', 'BANDHANBNK', 'BANKBARODA', 'BANKINDIA', 'MAHABANK', 'BATAINDIA', 'BAYERCROP', 'BELRISE', 'BERGEPAINT', 'BDL', 'BEL', 'BHARATFORG', 'BHEL', 'BPCL', 'BHARTIARTL', 'BHARTIHEXA', 'BIKAJI', 'GROWW', 'BIOCON', 'BSOFT', 'BLUEDART', 'BLUEJET', 'BLUESTARCO', 'BBTC', 'BOSCHLTD', 'FIRSTCRY', 'BRIGADE', 'BRITANNIA', 'MAPMYINDIA', 'CCL', 'CESC', 'CGPOWER', 'CRISIL'],
    "nifty500_phase_3": ['CANFINHOME', 'CANBK', 'CANHLIFE', 'CAPLIPOINT', 'CGCL', 'CARBORUNIV', 'CARTRADE', 'CASTROLIND', 'CEATLTD', 'CEMPRO', 'CENTRALBK', 'CDSL', 'CHALET', 'CHAMBLFERT', 'CHENNPETRO', 'CHOICEIN', 'CHOLAHLDNG', 'CHOLAFIN', 'CIPLA', 'CUB', 'CLEAN', 'COALINDIA', 'COCHINSHIP', 'COFORGE', 'COHANCE', 'COLPAL', 'CAMS', 'CONCORDBIO', 'CONCOR', 'COROMANDEL', 'CRAFTSMAN', 'CREDITACC', 'CROMPTON', 'CUMMINSIND', 'CYIENT', 'DCMSHRIRAM', 'DLF', 'DOMS', 'DABUR', 'DALBHARAT', 'DATAPATTNS', 'DEEPAKFERT', 'DEEPAKNTR', 'DELHIVERY', 'DEVYANI', 'DIVISLAB', 'DIXON', 'LALPATHLAB', 'DRREDDY', 'EIDPARRY'],
    "nifty500_phase_4": ['EIHOTEL', 'EICHERMOT', 'ELECON', 'ELGIEQUIP', 'EMAMILTD', 'EMCURE', 'EMMVEE', 'ENDURANCE', 'ENGINERSIN', 'ERIS', 'ESCORTS', 'ETERNAL', 'EXIDEIND', 'NYKAA', 'FEDERALBNK', 'FACT', 'FINCABLES', 'FSL', 'FIVESTAR', 'FORCEMOT', 'FORTIS', 'GAIL', 'GVT&D', 'GMRAIRPORT', 'GABRIEL', 'GALLANTT', 'GRSE', 'GICRE', 'GILLETTE', 'GLAND', 'GLAXO', 'GLENMARK', 'MEDANTA', 'GODIGIT', 'GPIL', 'GODFRYPHLP', 'GODREJCP', 'GODREJIND', 'GODREJPROP', 'GRANULES', 'GRAPHITE', 'GRASIM', 'GRAVITA', 'GESHIP', 'FLUOROCHEM', 'GMDCLTD', 'GSPL', 'HEG', 'HBLENGINE', 'HCLTECH'],
    "nifty500_phase_5": ['HDBFS', 'HDFCAMC', 'HDFCBANK', 'HDFCLIFE', 'HFCL', 'HAVELLS', 'HEROMOTOCO', 'HEXT', 'HSCL', 'HINDALCO', 'HAL', 'HINDCOPPER', 'HINDPETRO', 'HINDUNILVR', 'HINDZINC', 'POWERINDIA', 'HOMEFIRST', 'HONASA', 'HONAUT', 'HUDCO', 'HYUNDAI', 'ICICIBANK', 'ICICIGI', 'ICICIAMC', 'ICICIPRULI', 'IDBI', 'IDFCFIRSTB', 'IFCI', 'IIFL', 'IRB', 'IRCON', 'ITCHOTELS', 'ITC', 'ITI', 'INDGN', 'INDIACEM', 'INDIAMART', 'INDIANB', 'IEX', 'INDHOTEL', 'IOC', 'IOB', 'IRCTC', 'IRFC', 'IREDA', 'IGL', 'INDUSTOWER', 'INDUSINDBK', 'NAUKRI', 'INFY'],
    "nifty500_phase_6": ['INOXWIND', 'INTELLECT', 'INDIGO', 'IGIL', 'IKS', 'IPCALAB', 'JBCHEPHARM', 'JKCEMENT', 'JBMA', 'JKTYRE', 'JMFINANCIL', 'JSWCEMENT', 'JSWENERGY', 'JSWINFRA', 'JSWSTEEL', 'JAINREC', 'JPPOWER', 'J&KBANK', 'JINDALSAW', 'JSL', 'JINDALSTEL', 'JIOFIN', 'JUBLFOOD', 'JUBLINGREA', 'JUBLPHARMA', 'JWL', 'JYOTICNC', 'KPRMILL', 'KEI', 'KPITTECH', 'KAJARIACER', 'KPIL', 'KALYANKJIL', 'KARURVYSYA', 'KAYNES', 'KEC', 'KFINTECH', 'KIRLOSENG', 'KOTAKBANK', 'KIMS', 'LTF', 'LTTS', 'LGEINDIA', 'LICHSGFIN', 'LTFOODS', 'LTM', 'LT', 'LATENTVIEW', 'LAURUSLABS', 'THELEELA'],
    "nifty500_phase_7": ['LEMONTREE', 'LENSKART', 'LICI', 'LINDEINDIA', 'LLOYDSME', 'LODHA', 'LUPIN', 'MMTC', 'MRF', 'MGL', 'M&MFIN', 'M&M', 'MANAPPURAM', 'MRPL', 'MANKIND', 'MARICO', 'MARUTI', 'MFSL', 'MAXHEALTH', 'MAZDOCK', 'MEESHO', 'MINDACORP', 'MSUMI', 'MOTILALOFS', 'MPHASIS', 'MCX', 'MUTHOOTFIN', 'NATCOPHARM', 'NBCC', 'NCC', 'NHPC', 'NLCINDIA', 'NMDC', 'NSLNISP', 'NTPCGREEN', 'NTPC', 'NH', 'NATIONALUM', 'NAVA', 'NAVINFLUOR', 'NESTLEIND', 'NETWEB', 'NEULANDLAB', 'NEWGEN', 'NAM-INDIA', 'NIVABUPA', 'NUVAMA', 'NUVOCO', 'OBEROIRLTY', 'ONGC'],
    "nifty500_phase_8": ['OIL', 'OLAELEC', 'OLECTRA', 'PAYTM', 'ONESOURCE', 'OFSS', 'POLICYBZR', 'PCBL', 'PGEL', 'PIIND', 'PNBHOUSING', 'PTCIL', 'PVRINOX', 'PAGEIND', 'PARADEEP', 'PATANJALI', 'PERSISTENT', 'PETRONET', 'PFIZER', 'PHOENIXLTD', 'PWL', 'PIDILITIND', 'PINELABS', 'PIRAMALFIN', 'PPLPHARMA', 'POLYMED', 'POLYCAB', 'POONAWALLA', 'PFC', 'POWERGRID', 'PREMIERENE', 'PRESTIGE', 'PNB', 'RRKABEL', 'RBLBANK', 'RECLTD', 'RHIM', 'RITES', 'RADICO', 'RVNL', 'RAILTEL', 'RAINBOW', 'RKFORGE', 'REDINGTON', 'RELIANCE', 'RPOWER', 'SBFC', 'SBICARD', 'SBILIFE', 'SJVN'],
    "nifty500_phase_9": ['SRF', 'SAGILITY', 'SAILIFE', 'SAMMAANCAP', 'MOTHERSON', 'SAPPHIRE', 'SARDAEN', 'SAREGAMA', 'SCHAEFFLER', 'SCHNEIDER', 'SCI', 'SHREECEM', 'SHRIRAMFIN', 'SHYAMMETL', 'ENRIN', 'SIEMENS', 'SIGNATURE', 'SOBHA', 'SOLARINDS', 'SONACOMS', 'SONATSOFTW', 'STARHEALTH', 'SBIN', 'SAIL', 'SUMICHEM', 'SUNPHARMA', 'SUNTV', 'SUNDARMFIN', 'SUPREMEIND', 'SPLPETRO', 'SUZLON', 'SWANCORP', 'SWIGGY', 'SYNGENE', 'SYRMA', 'TBOTEK', 'TVSMOTOR', 'TATACAP', 'TATACHEM', 'TATACOMM', 'TCS', 'TATACONSUM', 'TATAELXSI', 'TATAINVEST', 'TMCV', 'TMPV', 'TATAPOWER', 'TATASTEEL', 'TATATECH', 'TTML'],
    "nifty500_phase_10": ['TECHM', 'TECHNOE', 'TEGA', 'TEJASNET', 'TENNIND', 'NIACL', 'RAMCOCEM', 'THERMAX', 'TIMKEN', 'TITAGARH', 'TITAN', 'TORNTPHARM', 'TORNTPOWER', 'TARIL', 'TRAVELFOOD', 'TRENT', 'TRIDENT', 'TRITURBINE', 'TIINDIA', 'UCOBANK', 'UNOMINDA', 'UPL', 'UTIAMC', 'ULTRACEMCO', 'UNIONBANK', 'UBL', 'UNITDSPR', 'URBANCO', 'USHAMART', 'VTL', 'VBL', 'VEDL', 'VIJAYA', 'VMM', 'IDEA', 'VOLTAS', 'WAAREEENER', 'WELCORP', 'WELSPUNLIV', 'WHIRLPOOL', 'WIPRO', 'WOCKPHARMA', 'YESBANK', 'ZFCVINDIA', 'ZEEL', 'ZENTEC', 'ZENSARTECH', 'ZYDUSLIFE', 'ZYDUSWELL', 'ECLERX'],

    # ── AI & DIGITAL SOFTWARE (v9) ─────────────────────────────────────────
    "ai_software_solutions_v9": [
        "HAPPISTMND", "NEWGEN", "INTELLECT", "ZENSARTECH", "SAKSOFT", "KELTONTEC"
    ],

    # ── SOLAR MANUFACTURING & EPC (v10) ────────────────────────────────────
    "solar_manufacturing_epc_v10": [
        "WAAREEENER", "PREMIERENE", "INSOLATION", "ALPEXSOLAR", 
        "WEBELSOLAR", "GENSOL", "ZODIAC", "SERVOTECH"
    ],

    # ── SOLAR SPECIALIZED COMPONENTS (v12-v14) ─────────────────────────────
    "solar_inverters_electronics_v12": [
        "SERVOTECH", "VGUARD", "HPL", "HITACHI_ENERGY"
    ],

    "solar_pumps_agri_v13": [
        "SHAKTIPUMP", "KIRLOSBROS", "KSB", "WPIL", "OSWALPUMPS"
    ],

    "solar_cables_wires_v14": [
        "APARINDS", "POLYCAB", "KEI", "RRKABEL", "VINDHYATEL"
    ],

    # ── RENEWABLE POWER & IPP (v16) ────────────────────────────────────────
    "renewable_power_ipp_v16": [
        "KPIGREEN", "SWSOLAR", "WAAREERTL", "SJVN", "NHPC"
    ],

    # ── SOLAR GLASS & CLEANROOM (v17) ──────────────────────────────────────
    "solar_glass_cleanroom_v17": [
        "BORORENEW", "LINDEINDIA", "GUJFLUORO"
    ],
}


def get_watchlist(name: str) -> list:
    """Return list of NSE ticker symbols for a given watchlist name."""
    name = name.lower().strip()
    if name not in WATCHLISTS:
        available = ", ".join(WATCHLISTS.keys())
        raise ValueError(
            f"Watchlist '{name}' not found. "
            f"Available: {available}"
        )
    return WATCHLISTS[name]


def list_watchlists() -> dict:
    """Return dict of watchlist name → count of stocks."""
    return {name: len(tickers) for name, tickers in WATCHLISTS.items()}


def add_to_custom(tickers: list):
    """Add tickers to the custom watchlist."""
    existing = WATCHLISTS["custom"]
    for t in tickers:
        t = t.upper().strip()
        if t not in existing:
            existing.append(t)
