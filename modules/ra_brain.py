# Python brain for RA - reads zones exported by MQL5 and logs them
except Exception as e:
print('MetaTrader5 module not found. Run: pip install MetaTrader5')
mt5 = None


CONFIG_PATH = 'ra_config.json'
# read config
if Path(CONFIG_PATH).exists():
cfg = json.loads(Path(CONFIG_PATH).read_text())
else:
cfg = {
"symbols": ["EURUSD","GBPUSD","USDJPY"],
"risk_per_trade": 0.01,
"data_path": "",
"poll_interval": 5
}


# Determine terminal files folder, default: same dir or user will put path in config
files_folder = cfg.get('data_path') or ''
if files_folder=='' or not Path(files_folder).exists():
# try common relative path: ./terminal_files
files_folder = os.path.join(os.getcwd(), 'terminal_files')
Path(files_folder).mkdir(parents=True, exist_ok=True)


zones_file = os.path.join(files_folder, 'ra_zones.json')
print('Using zones file:', zones_file)


# Try to initialize MT5 connection (optional)
if mt5 is not None:
if not mt5.initialize():
print('mt5.initialize() failed, continuing without MT5 connection')
else:
print('Connected to MT5, version:', mt5.version())


# Simple loop: read zones file and log new zones
seen = set()
while True:
try:
if os.path.exists(zones_file):
txt = open(zones_file,'r').read()
try:
zones = json.loads(txt)
except Exception as e:
# sometimes partially written
zones = []
for z in zones:
key = (z.get('symbol'), z.get('type'), z.get('time_from'), z.get('price_top'), z.get('price_bottom'))
if key not in seen:
seen.add(key)
print('NEW ZONE:', z)
# place for future: evaluate probability, check confluence, compute position size
# example simple rule: if zone is bull and current price returns to zone -> consider buy
else:
# try to find zones file in default MT5 terminal Files folder (Windows). We won't assume path.
pass
except Exception as e:
print('Error reading zones:', e)
time.sleep(cfg.get('poll_interval',5))
