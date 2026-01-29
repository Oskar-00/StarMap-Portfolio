# -*- coding: utf-8 -*-
import json
import sqlite3
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS, cross_origin
import logging
import random

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ustawienie folderu 'static' jako źródła plików
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

DATABASE = 'stars_database.db'
JSON_DB_FILE = 'nowegwiazdy_przeksztalcone.json'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_sold_stars_data():
    try:
        if not os.path.exists(DATABASE):
            return {}
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sold_stars';")
            if not cursor.fetchone():
                return {}
            sold_stars_rows = conn.execute('SELECT sao_number, star_name, customer_name FROM sold_stars').fetchall()
            return {row['sao_number']: {'star_name': row['star_name'], 'customer_name': row['customer_name']} for row in sold_stars_rows}
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        return {}

# --- TŁUMACZENIE KONSTELACJI NA ANGIELSKI ---
MANUAL_CONSTELLATION_OVERRIDES = {
    # 1. Boötes (Wolarz)
    "101137": "Boötes", "100949": "Boötes", "100766": "Boötes", "100706": "Boötes", "83500": "Boötes", "64589": "Boötes", "45337": "Boötes", "64203": "Boötes", "64202": "Boötes","100944": "Boötes",
    # 2. Corona Borealis (Korona Północna)
    "64769": "Corona Borealis", "83831": "Corona Borealis", "83893": "Corona Borealis", "83958": "Corona Borealis", "84019": "Corona Borealis", "84098": "Corona Borealis", "84152": "Corona Borealis",
    # 3. Hercules
    "84951": "Hercules", "85163": "Hercules", "85397": "Hercules", "85590": "Hercules", "85750": "Hercules", "65921": "Hercules", "66001": "Hercules", "66485": "Hercules", "46872": "Hercules", "45772": "Hercules", "45911": "Hercules", "46028": "Hercules", "46161": "Hercules", "102107": "Hercules", "84411": "Hercules", "65716": "Hercules", "65890": "Hercules", "65504": "Hercules", "65485": "Hercules",
    # 4. Canes Venatici (Psy Gończe)
    "63257": "Canes Venatici", "44230": "Canes Venatici",
    # 5. Serpens (Wąż)
    "101826": "Serpens", "101752": "Serpens", "101725": "Serpens", "101624": "Serpens", "121157": "Serpens", "121218": "Serpens", "140787": "Serpens", "124070": "Serpens", "142241": "Serpens", "160747": "Serpens", "160700": "Serpens", "160479": "Serpens",
    # 6. Coma Berenices (Warkocz Bereniki)
    "100443": "Coma Berenices", "82706": "Coma Berenices", "82313": "Coma Berenices",
    # 7. Ursa Major (Wielka Niedźwiedzica)
    "43309": "Ursa Major", "43268": "Ursa Major", "43629": "Ursa Major", "42630": "Ursa Major", "42661": "Ursa Major", "27289": "Ursa Major", "43886": "Ursa Major", "27408": "Ursa Major", "44752": "Ursa Major", "28737": "Ursa Major", "28315": "Ursa Major", "28179": "Ursa Major", "27876": "Ursa Major", "15384": "Ursa Major", "27401": "Ursa Major", "14573": "Ursa Major", "14908": "Ursa Major", "28738": "Ursa Major", "28553": "Ursa Major", "43310": "Ursa Major",
    # 8. Draco (Smok)
    "15532": "Draco", "7593": "Draco", "16273": "Draco", "29520": "Draco", "29765": "Draco", "17074": "Draco", "17365": "Draco", "9084": "Draco", "18222": "Draco", "30631": "Draco", "30450": "Draco", "30429": "Draco", "30653": "Draco",
    # 9. Cepheus (Cefeusz)
    "19302": "Cepheus", "34508": "Cepheus", "10057": "Cepheus", "20268": "Cepheus", "10818": "Cepheus",
    # 10. Ursa Minor (Mała Niedźwiedzica)
    "308": "Ursa Minor", "2937": "Ursa Minor", "2770": "Ursa Minor", "8328": "Ursa Minor", "8102": "Ursa Minor", "8207": "Ursa Minor", "8470": "Ursa Minor",
    # 11. Cygnus (Łabędź)
    "71070": "Cygnus", "70474": "Cygnus", "49528": "Cygnus", "49941": "Cygnus", "48796": "Cygnus", "31702": "Cygnus", "31537": "Cygnus",
    # 12. Lyra (Lira)
    "67663": "Lyra", "67174": "Lyra", "67321": "Lyra", "67559": "Lyra", "67451": "Lyra",
    # 13. Vulpecula (Lisek)
    "88428": "Vulpecula", "88071": "Vulpecula", "87883": "Vulpecula", "87261": "Vulpecula", "87010": "Vulpecula",
    # 14. Sagitta (Strzała)
    "105133": "Sagitta", "105120": "Sagitta", "105259": "Sagitta", "105500": "Sagitta",
    # 15. Aquila (Orzeł)
    "125122": "Aquila", "105223": "Aquila", "125235": "Aquila", "144150": "Aquila", "124603": "Aquila", "104461": "Aquila", "104318": "Aquila", "143021": "Aquila",
    # 16. Scutum (Tarcza)
    "161964": "Scutum", "161520": "Scutum", "142408": "Scutum", "142618": "Scutum", "142620": "Scutum",
    # 18. Ophiuchus (Wężownik)
    "121962": "Ophiuchus", "141086": "Ophiuchus", "160006": "Ophiuchus", "160332": "Ophiuchus", "185401": "Ophiuchus", "122671": "Ophiuchus", "102932": "Ophiuchus",
    # 19. Lacerta (Jaszczurka)
    "72191": "Lacerta", "52079": "Lacerta", "52055": "Lacerta", "51970": "Lacerta", "34395": "Lacerta", "34542": "Lacerta",
    # 20. Cassiopeia (Kasjopeja)
    "21133": "Cassiopeia", "21609": "Cassiopeia", "11482": "Cassiopeia", "22268": "Cassiopeia", "12031": "Cassiopeia",
    # 21. Camelopardalis (Żyrafa)
    "24054": "Camelopardalis", "13298": "Camelopardalis", "5006": "Camelopardalis", "12969": "Camelopardalis", "5496": "Camelopardalis",
    # 22. Delphinus (Delfin)
    "106230": "Delphinus", "106316": "Delphinus", "106425": "Delphinus", "106476": "Delphinus", "106357": "Delphinus",
    # 23. Equuleus (Źrebię)
    "126662": "Equuleus", "126643": "Equuleus", "126597": "Equuleus",
    # 24. Aquarius (Wodnik)
    "191683": "Aquarius", "165375": "Aquarius", "165321": "Aquarius", "145991": "Aquarius", "164861": "Aquarius", "191858": "Aquarius", "146598": "Aquarius", "146362": "Aquarius", "146181": "Aquarius", "146107": "Aquarius", "146044": "Aquarius", "145862": "Aquarius", "145457": "Aquarius", "144810": "Aquarius",
    # 25. Capricornus (Koziorożec)
    "164644": "Capricornus", "164560": "Capricornus", "164346": "Capricornus", "164132": "Capricornus", "190341": "Capricornus", "189781": "Capricornus", "189664": "Capricornus", "163481": "Capricornus", "163422": "Capricornus",
    # 26. Piscis Austrinus (Ryba Południowa)
    "191524": "Piscis Austrinus", "191318": "Piscis Austrinus", "190822": "Piscis Austrinus", "213292": "Piscis Austrinus", "213602": "Piscis Austrinus", "213883": "Piscis Austrinus", "214189": "Piscis Austrinus",
    # 27. Microscopium (Mikroskop)
    "212874": "Microscopium", "212636": "Microscopium", "212472": "Microscopium",
    # 28. Sagittarius (Strzelec)
    "229654": "Sagittarius", "229927": "Sagittarius", "229659": "Sagittarius", "211716": "Sagittarius", "188844": "Sagittarius", "188326": "Sagittarius", "187683": "Sagittarius", "187600": "Sagittarius", "210091": "Sagittarius", "209957": "Sagittarius", "209696": "Sagittarius", "185755": "Sagittarius", "186681": "Sagittarius", "186841": "Sagittarius", "186497": "Sagittarius", "187239": "Sagittarius", "187448": "Sagittarius", "187504": "Sagittarius", "187643": "Sagittarius", "162413": "Sagittarius", "162512": "Sagittarius",
    # 29. Corona Australis (Korona Południowa)
    "229111": "Corona Australis", "229299": "Corona Australis", "229461": "Corona Australis", "229513": "Corona Australis", "211005": "Corona Australis", "210990": "Corona Australis", "210928": "Corona Australis", "210781": "Corona Australis",
    # 30. Telescopium (Teleskop)
    "229047": "Telescopium", "229023": "Telescopium", "228777": "Telescopium",
    # 31. Scorpius (Skorpion)
    "208954": "Scorpius", "209163": "Scorpius", "228420": "Scorpius", "228201": "Scorpius", "227707": "Scorpius", "227402": "Scorpius", "208102": "Scorpius", "208078": "Scorpius", "184481": "Scorpius", "184415": "Scorpius", "183987": "Scorpius", "184014": "Scorpius", "159682": "Scorpius",
    # 32. Libra (Waga)
    "159563": "Libra", "159370": "Libra", "140430": "Libra", "158840": "Libra", "183139": "Libra",
    # 33. Ara (Ołtarz)
    "244725": "Ara", "228069": "Ara", "244331": "Ara", "244315": "Ara", "244168": "Ara", "253945": "Ara", "244726": "Ara",
    # 34. Virgo (Panna)
    "140090": "Virgo", "139824": "Virgo", "158427": "Virgo", "157923": "Virgo", "138917": "Virgo", "138710": "Virgo", "119035": "Virgo", "119674": "Virgo", "139420": "Virgo", "100384": "Virgo", "120238": "Virgo", "120648": "Virgo",
    # 35. Leo (Lew)
    "99809": "Leo", "99512": "Leo", "81727": "Leo", "98967": "Leo", "98955": "Leo", "81298": "Leo", "81265": "Leo", "81064": "Leo", "81004": "Leo",
    # 36. Leo Minor (Mały Lew)
    "61570": "Leo Minor", "61874": "Leo Minor", "62053": "Leo Minor", "62297": "Leo Minor",
    # 37. Lynx (Ryś)
    "61414": "Lynx", "61391": "Lynx", "61254": "Lynx", "42642": "Lynx", "42319": "Lynx", "41764": "Lynx", "26051": "Lynx", "25665": "Lynx",
    # 38. Auriga (Woźnica)
    "77168": "Auriga", "58636": "Auriga", "40750": "Auriga", "40186": "Auriga", "40026": "Auriga", "57522": "Auriga",
    # 39. Taurus (Byk)
    "77336": "Taurus", "76721": "Taurus", "94027": "Taurus", "93954": "Taurus", "93957": "Taurus", "93868": "Taurus", "93897": "Taurus", "76228": "Taurus", "93719": "Taurus", "111172": "Taurus",
    # 40. Perseus (Perseusz)
    "56673": "Perseus", "56799": "Perseus", "56856": "Perseus", "56840": "Perseus", "39053": "Perseus", "38787": "Perseus", "23789": "Perseus", "23655": "Perseus", "38592": "Perseus", "56138": "Perseus", "55928": "Perseus",
    # 41. Triangulum (Trójkąt)
    "74996": "Triangulum", "55306": "Triangulum", "55427": "Triangulum",
    # 42. Aries (Baran)
    "75596": "Aries", "75151": "Aries", "75012": "Aries", "92681": "Aries",
    # 43. Andromeda
    "73765": "Andromeda", "54058": "Andromeda", "54471": "Andromeda", "54281": "Andromeda", "36699": "Andromeda", "37734": "Andromeda",
    # 44. Pegasus (Pegaz)
    "91781": "Pegasus", "90981": "Pegasus", "108378": "Pegasus", "90734": "Pegasus", "72064": "Pegasus", "90775": "Pegasus", "90816": "Pegasus", "90238": "Pegasus", "89949": "Pegasus", "108165": "Pegasus", "108103": "Pegasus", "127340": "Pegasus", "127029": "Pegasus",
    # 45. Pisces (Ryby)
    "74546": "Pisces", "74637": "Pisces", "74571": "Pisces", "74544": "Pisces", "92484": "Pisces", "110110": "Pisces", "110291": "Pisces", "110206": "Pisces", "110065": "Pisces", "109926": "Pisces", "109627": "Pisces", "109474": "Pisces", "128513": "Pisces", "128310": "Pisces", "128374": "Pisces", "128336": "Pisces", "128186": "Pisces", "128085": "Pisces", "128126": "Pisces", "128196": "Pisces",
    # 46. Cetus (Wieloryb)
    "128694": "Cetus", "147420": "Cetus", "147632": "Cetus", "129274": "Cetus", "148059": "Cetus", "148385": "Cetus", "148528": "Cetus", "148575": "Cetus", "148445": "Cetus", "148386": "Cetus", "147986": "Cetus", "129825": "Cetus", "110665": "Cetus", "110707": "Cetus", "110920": "Cetus", "110889": "Cetus", "110723": "Cetus", "110543": "Cetus", "110635": "Cetus", "110408": "Cetus",
    # 47. Sculptor (Rzeźbiarz)
    "166716": "Sculptor", "214615": "Sculptor", "214444": "Sculptor",
    # 48. Grus (Żuraw)
    "247680": "Grus", "247593": "Grus", "231258": "Grus", "231468": "Grus", "231444": "Grus", "231154": "Grus", "230992": "Grus", "213543": "Grus", "213374": "Grus",
    # 49. Indus (Indianin)
    "247244": "Indus", "230300": "Indus", "246784": "Indus",
    # 50. Tucana (Tukan)
    "248163": "Tucana", "248202": "Tucana", "247814": "Tucana", "255193": "Tucana",
    # 51. Pavo (Paw)
    "246574": "Pavo", "254999": "Pavo", "254862": "Pavo", "254733": "Pavo", "257757": "Pavo", "257620": "Pavo", "254413": "Pavo", "254393": "Pavo", "254226": "Pavo", "254147": "Pavo", "254020": "Pavo",
    # 52. Norma (Węgielnica)
    "243454": "Norma", "243643": "Norma", "226773": "Norma", "226466": "Norma",
    # 53. Lupus (Wilk)
    "224920": "Lupus", "225128": "Lupus", "242304": "Lupus", "225071": "Lupus", "226004": "Lupus", "225938": "Lupus", "225691": "Lupus", "225335": "Lupus", "206552": "Lupus", "207208": "Lupus", "207341": "Lupus", "207040": "Lupus",
    # 54. Centaurus (Centaur)
    "225044": "Centaurus", "205188": "Centaurus", "224471": "Centaurus", "224469": "Centaurus", "204545": "Centaurus", "204371": "Centaurus", "224585": "Centaurus", "224538": "Centaurus", "241047": "Centaurus", "252838": "Centaurus", "252582": "Centaurus", "223603": "Centaurus", "223454": "Centaurus", "239689": "Centaurus", "238986": "Centaurus", "251472": "Centaurus",
    # 55. Crux (Krzyż Południa)
    "240019": "Crux", "240259": "Crux", "251904": "Crux", "239791": "Crux",
    # 56. Musca (Mucha)
    "252019": "Musca", "251974": "Musca", "256955": "Musca", "251575": "Musca",
    # 57. Sextans (Sekstant)
    "137608": "Sextans", "137366": "Sextans",
    # 58. Crater (Puchar)
    "156375": "Crater", "179624": "Crater", "156661": "Crater", "156605": "Crater", "156658": "Crater", "138296": "Crater", "156988": "Crater", "156869": "Crater",
    # 59. Corvus (Kruk)
    "180505": "Corvus", "180531": "Corvus", "180915": "Corvus", "157323": "Corvus", "157176": "Corvus",
    # 60. Hydra
    "182911": "Hydra", "182244": "Hydra", "181543": "Hydra", "202901": "Hydra", "202558": "Hydra", "156256": "Hydra", "155980": "Hydra", "155785": "Hydra", "155542": "Hydra", "136871": "Hydra", "137035": "Hydra", "117527": "Hydra", "117264": "Hydra", "117112": "Hydra", "117146": "Hydra", "116965": "Hydra", "116988": "Hydra", "117050": "Hydra",
    # 61. Cancer (Rak)
    "116569": "Cancer", "98267": "Cancer", "98087": "Cancer", "80378": "Cancer", "80416": "Cancer", "80104": "Cancer",
    # 62. Gemini (Bliźnięta)
    "79666": "Gemini", "60198": "Gemini", "79653": "Gemini", "79533": "Gemini", "59858": "Gemini", "59570": "Gemini", "79374": "Gemini", "79294": "Gemini", "96746": "Gemini", "96074": "Gemini", "95912": "Gemini", "79031": "Gemini", "78682": "Gemini", "78423": "Gemini", "78297": "Gemini", "78135": "Gemini", "77915": "Gemini",
    # 63. Canis Minor (Mały Pies)
    "115756": "Canis Minor", "115456": "Canis Minor",
    # 64. Orion
    "77911": "Orion", "77730": "Orion", "95362": "Orion", "95259": "Orion", "113389": "Orion", "113271": "Orion", "112921": "Orion", "112740": "Orion", "132444": "Orion", "132346": "Orion", "132220": "Orion", "94201": "Orion", "94359": "Orion", "94290": "Orion", "94218": "Orion", "112124": "Orion", "112106": "Orion", "112142": "Orion", "112197": "Orion", "112281": "Orion", "132071": "Orion", "132542": "Orion", "131907": "Orion",
    # 65. Monoceros (Jednorożec)
    "134986": "Monoceros", "135551": "Monoceros", "134330": "Monoceros", "133317": "Monoceros", "133012": "Monoceros", "113810": "Monoceros", "113507": "Monoceros",
    # 66. Lepus (Zając)
    "150223": "Lepus", "150345": "Lepus", "150340": "Lepus", "150239": "Lepus", "150237": "Lepus", "170051": "Lepus", "150547": "Lepus", "170457": "Lepus", "170759": "Lepus", "170926": "Lepus", "150801": "Lepus", "150957": "Lepus", "151110": "Lepus",
    # 67. Caelum (Rylec)
    "195239": "Caelum", "216926": "Caelum", "216850": "Caelum",
    # 68. Eridanus (Erydan)
    "149781": "Eridanus", "131824": "Eridanus", "131794": "Eridanus", "131568": "Eridanus", "131468": "Eridanus", "131346": "Eridanus", "130686": "Eridanus", "130564": "Eridanus", "130387": "Eridanus", "130197": "Eridanus", "148584": "Eridanus", "168249": "Eridanus", "168460": "Eridanus", "168634": "Eridanus", "168827": "Eridanus", "195148": "Eridanus", "194984": "Eridanus", "194902": "Eridanus", "194559": "Eridanus", "194550": "Eridanus", "216263": "Eridanus", "216113": "Eridanus", "215999": "Eridanus", "215996": "Eridanus", "215906": "Eridanus", "232696": "Eridanus", "232573": "Eridanus", "232481": "Eridanus",
    # 69. Reticulum (Siatka)
    "248918": "Reticulum", "233463": "Reticulum", "248969": "Reticulum", "248877": "Reticulum",
    # 70. Horologium (Zegar)
    "232981": "Horologium", "232857": "Horologium", "216710": "Horologium",
    # 71. Hydrus (Wąż Wodny)
    "248474": "Hydrus", "248545": "Hydrus", "248621": "Hydrus", "256029": "Hydrus", "255670": "Hydrus",
    # 72. Octans (Oktant)
    "257948": "Octans", "258941": "Octans", "258698": "Octans",
    # 73. Apus (Ptak Raju)
    "257193": "Apus", "257407": "Apus", "257424": "Apus",
    # 74. Triangulum Australe (Trójkąt Południowy)
    "253097": "Triangulum Australe", "253346": "Triangulum Australe", "253700": "Triangulum Australe",
    # 75. Circinus (Cyrkiel)
    "242384": "Circinus", "242463": "Circinus", "252853": "Circinus",
    # 76. Fornax (Piec)
    "168373": "Fornax", "193931": "Fornax",
    # 77. Phoenix (Feniks)
    "215093": "Phoenix", "214983": "Phoenix", "215092": "Phoenix", "215516": "Phoenix", "215365": "Phoenix", "232306": "Phoenix", "215536": "Phoenix", "215696": "Phoenix",
    # 78. Dorado (Złota Ryba)
    "233457": "Dorado", "233564": "Dorado", "249311": "Dorado", "249390": "Dorado", "249346": "Dorado",
    # 79. Pictor (Malarz)
    "249647": "Pictor", "234154": "Pictor", "234134": "Pictor",
    # 80. Mensa (Góra Stołowa)
    "256201": "Mensa", "256122": "Mensa",
    # 81. Chamaeleon (Kameleon)
    "256496": "Chamaeleon", "256731": "Chamaeleon", "256924": "Chamaeleon",
    # 82. Volans (Ryba Latająca)
    "249809": "Volans", "256374": "Volans", "256438": "Volans", "250128": "Volans", "250422": "Volans", "250228": "Volans",
    # 83. Antlia (Pompa)
    "201927": "Antlia", "201405": "Antlia", "200416": "Antlia",
    # 84. Pyxis (Kompas)
    "176559": "Pyxis", "199546": "Pyxis", "199490": "Pyxis",
    # 85. Canis Major (Wielki Pies)
    "196698": "Canis Major", "197258": "Canis Major", "172676": "Canis Major", "172797": "Canis Major", "173047": "Canis Major", "173282": "Canis Major", "173651": "Canis Major", "172839": "Canis Major", "172542": "Canis Major", "171982": "Canis Major", "151702": "Canis Major", "151428": "Canis Major", "151881": "Canis Major", "152126": "Canis Major", "152303": "Canis Major", "152071": "Canis Major",
    # 86. Columba (Gołąb)
    "195924": "Columba", "196059": "Columba", "196240": "Columba", "217650": "Columba", "196352": "Columba", "196643": "Columba", "196735": "Columba",
    # 87. Vela (Żagle)
    "219504": "Vela", "236232": "Vela", "236891": "Vela", "237522": "Vela", "222321": "Vela", "221895": "Vela", "221234": "Vela", "220878": "Vela",
    # 88. Carina (Kil)
    "234480": "Carina", "235932": "Carina", "236808": "Carina", "236693": "Carina", "250905": "Carina", "238085": "Carina", "238574": "Carina", "238813": "Carina", "251090": "Carina", "251083": "Carina", "250885": "Carina", "250495": "Carina",
    # 89. Puppis (Rufa)
    "218071": "Puppis", "234735": "Puppis", "218755": "Puppis", "198752": "Puppis", "175217": "Puppis", "174852": "Puppis", "174601": "Puppis", "197795": "Puppis",
}

VISIBLE_FROM_POLAND = (
    "Andromeda", "Aries", "Gemini", "Cancer", "Canis Major", "Canis Minor", "Auriga",
    "Boötes", "Camelopardalis", "Cassiopeia", "Cepheus", "Coma Berenices", "Corona Borealis",
    "Cygnus", "Delphinus", "Draco", "Equuleus", "Hercules", "Lacerta", "Leo",
    "Leo Minor", "Lynx", "Lyra", "Monoceros", "Orion", "Pegasus", "Perseus",
    "Pisces", "Sagitta", "Taurus", "Triangulum", "Ursa Major",
    "Ursa Minor", "Virgo", "Vulpecula", "Canes Venatici", "Serpens", "Ophiuchus",
    "Aquila", "Scutum", "Aquarius", "Capricornus"
)

CONSTELLATIONS = [
    {"name": "Andromeda", "abbr": "And", "ra_min": 344.4, "ra_max": 39.9, "dec_min": 21.7, "dec_max": 53.3},
    {"name": "Antlia", "abbr": "Ant", "ra_min": 144.9, "ra_max": 160.1, "dec_min": -40.1, "dec_max": -28.3},
    {"name": "Apus", "abbr": "Aps", "ra_min": 208.2, "ra_max": 270.4, "dec_min": -83.1, "dec_max": -70.0},
    {"name": "Aquarius", "abbr": "Aqr", "ra_min": 309.4, "ra_max": 357.9, "dec_min": -25.0, "dec_max": 3.4},
    {"name": "Aquila", "abbr": "Aql", "ra_min": 279.3, "ra_max": 305.1, "dec_min": -11.9, "dec_max": 18.8},
    {"name": "Ara", "abbr": "Ara", "ra_min": 248.8, "ra_max": 273.8, "dec_min": -67.7, "dec_max": -45.5},
    {"name": "Aries", "abbr": "Ari", "ra_min": 26.0, "ra_max": 49.9, "dec_min": 10.6, "dec_max": 31.3},
    {"name": "Auriga", "abbr": "Aur", "ra_min": 70.3, "ra_max": 110.1, "dec_min": 28.0, "dec_max": 56.2},
    {"name": "Boötes", "abbr": "Boo", "ra_min": 205.1, "ra_max": 232.1, "dec_min": 7.5, "dec_max": 55.2},
    {"name": "Caelum", "abbr": "Cae", "ra_min": 65.2, "ra_max": 77.8, "dec_min": -41.9, "dec_max": -27.2},
    {"name": "Camelopardalis", "abbr": "Cam", "ra_min": 48.0, "ra_max": 220.0, "dec_min": 52.7, "dec_max": 86.1},
    {"name": "Cancer", "abbr": "Cnc", "ra_min": 118.0, "ra_max": 140.7, "dec_min": 6.5, "dec_max": 33.2},
    {"name": "Canes Venatici", "abbr": "CVn", "ra_min": 180.9, "ra_max": 210.0, "dec_min": 27.9, "dec_max": 52.4},
    {"name": "Canis Major", "abbr": "CMa", "ra_min": 96.0, "ra_max": 113.8, "dec_min": -33.3, "dec_max": -11.0},
    {"name": "Canis Minor", "abbr": "CMi", "ra_min": 109.5, "ra_max": 121.3, "dec_min": 0.2, "dec_max": 13.4},
    {"name": "Capricornus", "abbr": "Cap", "ra_min": 301.4, "ra_max": 328.0, "dec_min": -27.7, "dec_max": -8.3},
    {"name": "Carina", "abbr": "Car", "ra_min": 90.6, "ra_max": 168.0, "dec_min": -75.7, "dec_max": -50.7},
    {"name": "Cassiopeia", "abbr": "Cas", "ra_min": 350.5, "ra_max": 55.0, "dec_min": 46.5, "dec_max": 77.7},
    {"name": "Centaurus", "abbr": "Cen", "ra_min": 166.4, "ra_max": 225.0, "dec_min": -65.0, "dec_max": -29.9},
    {"name": "Cepheus", "abbr": "Cep", "ra_min": 301.0, "ra_max": 130.0, "dec_min": 53.0, "dec_max": 88.7},
    {"name": "Cetus", "abbr": "Cet", "ra_min": 356.1, "ra_max": 48.8, "dec_min": -24.8, "dec_max": 10.4},
    {"name": "Chamaeleon", "abbr": "Cha", "ra_min": 117.0, "ra_max": 200.0, "dec_min": -82.4, "dec_max": -75.4},
    {"name": "Circinus", "abbr": "Cir", "ra_min": 204.0, "ra_max": 229.4, "dec_min": -70.6, "dec_max": -55.6},
    {"name": "Columba", "abbr": "Col", "ra_min": 75.0, "ra_max": 101.5, "dec_min": -43.1, "dec_max": -27.1},
    {"name": "Coma Berenices", "abbr": "Com", "ra_min": 178.0, "ra_max": 201.8, "dec_min": 13.5, "dec_max": 33.5},
    {"name": "Corona Australis", "abbr": "CrA", "ra_min": 268.0, "ra_max": 286.9, "dec_min": -45.6, "dec_max": -36.8},
    {"name": "Corona Borealis", "abbr": "CrB", "ra_min": 232.0, "ra_max": 246.0, "dec_min": 25.9, "dec_max": 39.7},
    {"name": "Corvus", "abbr": "Crv", "ra_min": 178.2, "ra_max": 188.0, "dec_min": -25.3, "dec_max": -11.5},
    {"name": "Crater", "abbr": "Crt", "ra_min": 162.0, "ra_max": 175.5, "dec_min": -25.2, "dec_max": -6.7},
    {"name": "Crux", "abbr": "Cru", "ra_min": 179.0, "ra_max": 188.2, "dec_min": -64.5, "dec_max": -55.6},
    {"name": "Cygnus", "abbr": "Cyg", "ra_min": 290.8, "ra_max": 328.0, "dec_min": 27.8, "dec_max": 61.5},
    {"name": "Delphinus", "abbr": "Del", "ra_min": 303.5, "ra_max": 314.0, "dec_min": 2.2, "dec_max": 21.1},
    {"name": "Dorado", "abbr": "Dor", "ra_min": 57.0, "ra_max": 100.0, "dec_min": -69.6, "dec_max": -48.7},
    {"name": "Draco", "abbr": "Dra", "ra_min": 140.0, "ra_max": 310.0, "dec_min": 47.7, "dec_max": 86.2},
    {"name": "Equuleus", "abbr": "Equ", "ra_min": 313.0, "ra_max": 322.0, "dec_min": 2.3, "dec_max": 13.1},
    {"name": "Eridanus", "abbr": "Eri", "ra_min": 21.0, "ra_max": 77.0, "dec_min": -57.9, "dec_max": 0.0},
    {"name": "Fornax", "abbr": "For", "ra_min": 30.0, "ra_max": 57.0, "dec_min": -39.4, "dec_max": -23.7},
    {"name": "Gemini", "abbr": "Gem", "ra_min": 88.0, "ra_max": 120.0, "dec_min": 10.0, "dec_max": 35.5},
    {"name": "Grus", "abbr": "Gru", "ra_min": 323.0, "ra_max": 350.0, "dec_min": -56.4, "dec_max": -36.2},
    {"name": "Hercules", "abbr": "Her", "ra_min": 238.0, "ra_max": 284.0, "dec_min": 4.0, "dec_max": 51.5},
    {"name": "Horologium", "abbr": "Hor", "ra_min": 35.0, "ra_max": 65.0, "dec_min": -67.1, "dec_max": -39.6},
    {"name": "Hydra", "abbr": "Hya", "ra_min": 125.0, "ra_max": 235.0, "dec_min": -35.7, "dec_max": 6.7},
    {"name": "Hydrus", "abbr": "Hyi", "ra_min": 0.0, "ra_max": 70.0, "dec_min": -82.1, "dec_max": -57.8},
    {"name": "Indus", "abbr": "Ind", "ra_min": 303.0, "ra_max": 350.0, "dec_min": -74.4, "dec_max": -45.0},
    {"name": "Lacerta", "abbr": "Lac", "ra_min": 330.0, "ra_max": 343.0, "dec_min": 35.5, "dec_max": 56.9},
    {"name": "Leo", "abbr": "Leo", "ra_min": 140.0, "ra_max": 176.0, "dec_min": -6.5, "dec_max": 29.0},
    {"name": "Leo Minor", "abbr": "LMi", "ra_min": 145.0, "ra_max": 166.0, "dec_min": 22.8, "dec_max": 41.5},
    {"name": "Lepus", "abbr": "Lep", "ra_min": 73.0, "ra_max": 93.0, "dec_min": -27.0, "dec_max": -10.8},
    {"name": "Libra", "abbr": "Lib", "ra_min": 216.0, "ra_max": 238.0, "dec_min": -30.0, "dec_max": -0.8},
    {"name": "Lupus", "abbr": "Lup", "ra_min": 215.0, "ra_max": 245.0, "dec_min": -55.6, "dec_max": -29.8},
    {"name": "Lynx", "abbr": "Lyn", "ra_min": 95.0, "ra_max": 145.0, "dec_min": 32.5, "dec_max": 62.0},
    {"name": "Lyra", "abbr": "Lyr", "ra_min": 275.0, "ra_max": 288.0, "dec_min": 25.7, "dec_max": 47.7},
    {"name": "Mensa", "abbr": "Men", "ra_min": 60.0, "ra_max": 110.0, "dec_min": -85.4, "dec_max": -69.6},
    {"name": "Microscopium", "abbr": "Mic", "ra_min": 305.0, "ra_max": 322.0, "dec_min": -45.1, "dec_max": -27.5},
    {"name": "Monoceros", "abbr": "Mon", "ra_min": 88.0, "ra_max": 125.0, "dec_min": -11.4, "dec_max": 11.0},
    {"name": "Musca", "abbr": "Mus", "ra_min": 178.0, "ra_max": 200.0, "dec_min": -75.7, "dec_max": -64.6},
    {"name": "Norma", "abbr": "Nor", "ra_min": 234.0, "ra_max": 248.0, "dec_min": -60.5, "dec_max": -42.4},
    {"name": "Octans", "abbr": "Oct", "ra_min": 0.0, "ra_max": 360.0, "dec_min": -90.0, "dec_max": -74.2},
    {"name": "Ophiuchus", "abbr": "Oph", "ra_min": 240.0, "ra_max": 280.0, "dec_min": -30.0, "dec_max": 14.5},
    {"name": "Orion", "abbr": "Ori", "ra_min": 70.0, "ra_max": 95.0, "dec_min": -11.0, "dec_max": 22.9},
    {"name": "Pavo", "abbr": "Pav", "ra_min": 265.0, "ra_max": 325.0, "dec_min": -74.5, "dec_max": -56.6},
    {"name": "Pegasus", "abbr": "Peg", "ra_min": 320.0, "ra_max": 30.0, "dec_min": 2.2, "dec_max": 36.5},
    {"name": "Perseus", "abbr": "Per", "ra_min": 22.0, "ra_max": 73.0, "dec_min": 31.0, "dec_max": 59.2},
    {"name": "Phoenix", "abbr": "Phe", "ra_min": 355.0, "ra_max": 40.0, "dec_min": -57.8, "dec_max": -39.3},
    {"name": "Pictor", "abbr": "Pic", "ra_min": 70.0, "ra_max": 102.0, "dec_min": -64.2, "dec_max": -42.8},
    {"name": "Pisces", "abbr": "Psc", "ra_min": 345.0, "ra_max": 30.0, "dec_min": -6.7, "dec_max": 33.7},
    {"name": "Piscis Austrinus", "abbr": "PsA", "ra_min": 323.0, "ra_max": 348.0, "dec_min": -38.4, "dec_max": -24.5},
    {"name": "Puppis", "abbr": "Pup", "ra_min": 95.0, "ra_max": 125.0, "dec_min": -51.2, "dec_max": -11.4},
    {"name": "Pyxis", "abbr": "Pyx", "ra_min": 126.0, "ra_max": 140.0, "dec_min": -37.4, "dec_max": -17.4},
    {"name": "Reticulum", "abbr": "Ret", "ra_min": 50.0, "ra_max": 65.0, "dec_min": -67.2, "dec_max": -52.8},
    {"name": "Sagitta", "abbr": "Sge", "ra_min": 288.0, "ra_max": 302.0, "dec_min": 16.1, "dec_max": 21.5},
    {"name": "Sagittarius", "abbr": "Sgr", "ra_min": 268.0, "ra_max": 305.0, "dec_min": -45.8, "dec_max": -11.7},
    {"name": "Scorpius", "abbr": "Sco", "ra_min": 238.0, "ra_max": 268.0, "dec_min": -45.8, "dec_max": -8.3},
    {"name": "Sculptor", "abbr": "Scl", "ra_min": 350.0, "ra_max": 25.0, "dec_min": -39.4, "dec_max": -24.8},
    {"name": "Scutum", "abbr": "Sct", "ra_min": 275.0, "ra_max": 282.0, "dec_min": -16.8, "dec_max": -3.8},
    {"name": "Serpens", "abbr": "Ser", "ra_min": 228.0, "ra_max": 282.0, "dec_min": -16.2, "dec_max": 25.9},
    {"name": "Sextans", "abbr": "Sex", "ra_min": 146.0, "ra_max": 160.0, "dec_min": -11.6, "dec_max": 6.7},
    {"name": "Taurus", "abbr": "Tau", "ra_min": 50.0, "ra_max": 90.0, "dec_min": -1.5, "dec_max": 31.0},
    {"name": "Telescopium", "abbr": "Tel", "ra_min": 273.0, "ra_max": 304.0, "dec_min": -57.0, "dec_max": -45.0},
    {"name": "Triangulum", "abbr": "Tri", "ra_min": 22.0, "ra_max": 38.0, "dec_min": 25.6, "dec_max": 37.5},
    {"name": "Triangulum Australe", "abbr": "TrA", "ra_min": 223.0, "ra_max": 258.0, "dec_min": -70.4, "dec_max": -60.3},
    {"name": "Tucana", "abbr": "Tuc", "ra_min": 335.0, "ra_max": 20.0, "dec_min": -75.5, "dec_max": -56.3},
    {"name": "Ursa Major", "abbr": "UMa", "ra_min": 120.0, "ra_max": 210.0, "dec_min": 28.5, "dec_max": 73.2},
    {"name": "Ursa Minor", "abbr": "UMi", "ra_min": 0.0, "ra_max": 360.0, "dec_min": 65.5, "dec_max": 90.0},
    {"name": "Vela", "abbr": "Vel", "ra_min": 125.0, "ra_max": 165.0, "dec_min": -57.3, "dec_max": -37.2},
    {"name": "Virgo", "abbr": "Vir", "ra_min": 175.0, "ra_max": 228.0, "dec_min": -22.5, "dec_max": 15.0},
    {"name": "Volans", "abbr": "Vol", "ra_min": 105.0, "ra_max": 138.0, "dec_min": -75.5, "dec_max": -64.0},
    {"name": "Vulpecula", "abbr": "Vul", "ra_min": 288.0, "ra_max": 318.0, "dec_min": 19.5, "dec_max": 29.5}
]

def get_constellation_auto(ra_deg, dec_deg):
    for const in CONSTELLATIONS:
        ra_crosses_zero = const["ra_min"] > const["ra_max"]
        dec_in_range = const["dec_min"] <= dec_deg <= const["dec_max"]
        if not dec_in_range: continue
        if ra_crosses_zero:
            if ra_deg >= const["ra_min"] or ra_deg <= const["ra_max"]: return const["name"]
        else:
            if const["ra_min"] <= ra_deg <= const["ra_max"]: return const["name"]
    return "Unknown"

# === KATEGORIE SPRZEDAŻY PO ANGIELSKU ===
def assign_sale_category(magnitude, is_constellation_star):
    if is_constellation_star:
        return "Premium Star (Physical + Digital Certificate + App)"
    else:
        if -1.9 <= magnitude <= 6.0:
            return "Bright Star (Physical + Digital Certificate + App)"
    return None

def process_star_data(star, sold_stars_data):
    try:
        sao_name_full = star['TD'][1]
        sao_number_only = sao_name_full.replace("SAO", "").strip()
        ra_deg = float(star['TD'][3])
        dec_deg = float(star['TD'][4])
        magnitude = float(star['TD'][5]) if star['TD'][5] else 9.9
        spectral_type = star['TD'][6] if len(star['TD']) > 6 else 'G'
        is_sold = sao_number_only in sold_stars_data
        star_name = None
        customer_name = None
        if is_sold:
            star_info = sold_stars_data[sao_number_only]
            star_name = star_info.get('star_name')
            customer_name = star_info.get('customer_name')
        
        is_constellation_star = sao_number_only in MANUAL_CONSTELLATION_OVERRIDES
        manual_override = sao_number_only in MANUAL_CONSTELLATION_OVERRIDES
        
        # Pobieranie konstelacji (automatycznie po angielsku dzięki zmianom w listach)
        constellation = MANUAL_CONSTELLATION_OVERRIDES.get(sao_number_only, get_constellation_auto(ra_deg, dec_deg))
        
        sale_category = assign_sale_category(magnitude, is_constellation_star)
        if is_sold:
            sale_category = "Sold Out"
        return {
            'ra': ra_deg, 'dec': dec_deg, 'magnitude': magnitude, 'name': sao_name_full,
            'constellation': constellation,
            'sale_category': sale_category,
            'spectralType': spectral_type,
            'manual_override': manual_override,
            'is_sold': is_sold,
            'star_name': star_name,
            'customer_name': customer_name,
            'TD': star['TD']
        }
    except (ValueError, IndexError, KeyError):
        return None

@app.route('/stars', methods=['GET'])
@cross_origin()
def get_stars():
    try:
        sold_stars_data_dict = get_sold_stars_data()
        
        with open(JSON_DB_FILE, 'r', encoding='utf-8') as file:
            stars_raw = json.load(file)

        filtered_raw_stars = []
        for star in stars_raw:
            try:
                magnitude_str = star['TD'][5]
                if magnitude_str: 
                    mag = float(magnitude_str)
                    if mag <= 6.1: 
                        filtered_raw_stars.append(star)
            except (ValueError, TypeError, IndexError, KeyError):
                continue

        app.logger.info(f"Endpoint /stars: Reduced {len(stars_raw)} stars to {len(filtered_raw_stars)} (mag <= 6.1)")
        formatted_stars = [s for s in (process_star_data(star, sold_stars_data_dict) for star in filtered_raw_stars) if s] 
        return jsonify(formatted_stars)
    except Exception as e:
        app.logger.error(f"Error in /stars: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/index.html') 
@app.route('/')
@cross_origin()
def serve_starmap():
    try:
        return send_from_directory('static', 'index.html')
    except FileNotFoundError:
        return "Error: index.html not found in static folder.", 404

@app.route('/get_star_info/<string:sao_number>', methods=['GET'])
@cross_origin()
def get_star_info(sao_number):
    sold_stars_data_dict = get_sold_stars_data()
    if sao_number in sold_stars_data_dict:
        return jsonify({'error': 'This star is already sold', 'is_sold': True}), 404
    target_star_data = None
    try:
        with open(JSON_DB_FILE, 'r', encoding='utf-8') as file:
            stars_raw = json.load(file)
            for star_raw in stars_raw:
                if star_raw.get('TD') and len(star_raw['TD']) > 1 and star_raw['TD'][1].replace("SAO", "").strip() == sao_number:
                    target_star_data = process_star_data(star_raw, sold_stars_data_dict)
                    break 
    except (IOError, json.JSONDecodeError) as e:
        return jsonify({'error': f'Data read error: {e}'}), 500
    if not target_star_data:
        return jsonify({'error': 'Star not found'}), 404
    return jsonify({
        'sao_number': sao_number,
        'constellation': target_star_data.get('constellation'),
        'sale_category': target_star_data.get('sale_category'),
        'is_sold': target_star_data.get('is_sold', False)
    })

@app.route('/find-star', methods=['GET'])
@cross_origin()
def find_star():
    try:
        chosen_constellation = request.args.get('constellation')
        chosen_brightness = request.args.get('brightness') 
        app.logger.info(f"--- Find Star Request: Constellation='{chosen_constellation}', Brightness='{chosen_brightness}' ---")
        if not chosen_constellation or not chosen_brightness:
            return jsonify({'error': 'Missing parameters'}), 400
        sold_stars_data = get_sold_stars_data()
        
        with open(JSON_DB_FILE, 'r', encoding='utf-8') as file:
            all_stars = json.load(file)
        
        matching_stars = []
        for star_data in all_stars:
            processed_star = process_star_data(star_data, sold_stars_data)
            if not processed_star or processed_star['is_sold'] or not processed_star['sale_category']: 
                continue
            
            # Widoczność z Polski (teraz po angielsku)
            is_visible_from_poland = processed_star['constellation'] in VISIBLE_FROM_POLAND
            # Tutaj zmiana: "Random" zamiast "Losowa"
            is_constellation_match = (chosen_constellation == "Random" or processed_star['constellation'] == chosen_constellation)
            is_brightness_match = (processed_star['sale_category'] and processed_star['sale_category'].strip().lower().startswith(chosen_brightness.strip().lower()))

            if is_constellation_match and is_brightness_match: 
                if chosen_constellation != "Random":
                    matching_stars.append(processed_star)
                elif is_visible_from_poland:
                    matching_stars.append(processed_star)
                    
        if matching_stars:
            chosen_star = random.choice(matching_stars)
            sao_name_full = chosen_star.get('name', '')
            sao_number_only = chosen_star.get('sao_number_only') 
            sao_number = sao_name_full.replace("SAO", "").strip() if sao_name_full.startswith("SAO") else sao_number_only
            
            if sao_number: 
                 app.logger.info(f"Found star SAO {sao_number}.")
                 return jsonify({'sao_number': sao_number, 'constellation': chosen_star['constellation'], 'sale_category': chosen_star['sale_category']}), 200
            else:
                 app.logger.error(f"Error getting SAO number")
                 return jsonify({'error': 'Server error processing star'}), 500
        else:
            app.logger.warning(f"No stars found for criteria")
            return jsonify({'error': 'No stars found matching criteria'}), 404
            
    except Exception as e:
        app.logger.error(f"CRITICAL ERROR in /find-star: {e}", exc_info=True)
        return jsonify({'error': 'Server error searching for star'}), 500

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=5001, debug=False)