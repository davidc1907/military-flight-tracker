TARGET_TYPES = [
    "E6", "R135", "V25", "C32", "E3TF", "B2", "E4",
    "RQ4", "U2", "B52", "B1", "K35R", "MQ9", "P8",
    "MQ4", "F35", "F22", "EUFI", "V22",
]

KNOWN_ICAO_HEX: set[str] = {
    # E-6B Mercury
    "ae040d", "ae040e", "ae040f", "ae0410", "ae0411", "ae0412",
    "ae0413", "ae0414", "ae0415", "ae0416", "ae0417", "ae0418",
    "ae0419", "ae041a", "ae041b", "ae041c",
    # E-4B Nightwatch
    "adfeb7", "adfeb8", "adfeb9", "adfeba",
    # VC-25A
    "adfdf8", "adfdf9", "adfeb2", "adfeb3",
    # C-32A
    "ae01e6", "ae01e7", "ae0201", "ae0202",
    "ae4ae8", "ae4ae9", "ae4aea", "ae4aeb",
    # RC-135 Rivet Joint
    "ae01c5", "ae01c6", "ae01c7", "ae01c8", "ae01cb",
    "ae01cd", "ae01ce", "ae01d1", "ae01d2", "ae01d3",
    "ae01d4", "ae01d5",
    # E-3 Sentry
    "ae11e3", "ae11e4", "ae11e5", "ae11e6", "ae11e7", "ae11e8",
    # RQ-4 Global Hawk
    "ae5414", "ae54b6", "ae7813",
    # U-2 Dragon Lady
    "ae094d", "ae0950", "ae0955",
    # B-52 Stratofortress
    "ae586c", "ae586d", "ae586e", "ae5871", "ae5872", "ae5873",
    "ae5874", "ae5881", "ae5889", "ae588a", "ae5893", "ae5897",
    "ae58a2", "ae58a3",
    # B-1B Lancer
    "ae04a9", "ae04aa", "ae04ab", "ae04ac",
}

SPECIAL_TARGETS: dict[str, str] = {
    "adfdf8": "🇺🇸 AIR FORCE ONE",
    "adfdf9": "🇺🇸 AIR FORCE ONE",
    "adfeb2": "🇺🇸 AIR FORCE ONE",
    "adfeb3": "🇺🇸 AIR FORCE ONE",
    "ae01e6": "🇺🇸 AIR FORCE TWO",
    "ae01e7": "🇺🇸 AIR FORCE TWO",
    "ae0201": "🇺🇸 AIR FORCE TWO",
    "ae0202": "🇺🇸 AIR FORCE TWO",
    "ae4ae8": "🇺🇸 AIR FORCE TWO",
    "ae4ae9": "🇺🇸 AIR FORCE TWO",
    "ae4aea": "🇺🇸 AIR FORCE TWO",
    "ae4aeb": "🇺🇸 AIR FORCE TWO",
}