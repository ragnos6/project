# Generated by Django 5.1.2 on 2024-12-04 18:15

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0039_rename_purchase_datetime_vehicle_purchase_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enterprise',
            name='timezone',
            field=models.CharField(choices=[('Asia/Riyadh', 'Asia/Riyadh'), ('Europe/Zurich', 'Europe/Zurich'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('America/Monterrey', 'America/Monterrey'), ('Asia/Jakarta', 'Asia/Jakarta'), ('America/Yakutat', 'America/Yakutat'), ('Brazil/Acre', 'Brazil/Acre'), ('America/Montreal', 'America/Montreal'), ('Africa/Lome', 'Africa/Lome'), ('America/Detroit', 'America/Detroit'), ('Europe/Tirane', 'Europe/Tirane'), ('Asia/Qatar', 'Asia/Qatar'), ('Etc/GMT+11', 'Etc/GMT+11'), ('Africa/Juba', 'Africa/Juba'), ('America/Nassau', 'America/Nassau'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Pacific/Samoa', 'Pacific/Samoa'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('Europe/Malta', 'Europe/Malta'), ('America/Cordoba', 'America/Cordoba'), ('America/Barbados', 'America/Barbados'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Asia/Kabul', 'Asia/Kabul'), ('Asia/Damascus', 'Asia/Damascus'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('W-SU', 'W-SU'), ('Europe/Kiev', 'Europe/Kiev'), ('America/Halifax', 'America/Halifax'), ('Etc/GMT-3', 'Etc/GMT-3'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('America/Curacao', 'America/Curacao'), ('MST', 'MST'), ('America/Resolute', 'America/Resolute'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('America/Glace_Bay', 'America/Glace_Bay'), ('Chile/EasterIsland', 'Chile/EasterIsland'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Indian/Mayotte', 'Indian/Mayotte'), ('America/Thule', 'America/Thule'), ('America/Belize', 'America/Belize'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Asia/Calcutta', 'Asia/Calcutta'), ('Pacific/Efate', 'Pacific/Efate'), ('Europe/Oslo', 'Europe/Oslo'), ('America/Inuvik', 'America/Inuvik'), ('Africa/Harare', 'Africa/Harare'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('America/Recife', 'America/Recife'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Africa/Bissau', 'Africa/Bissau'), ('America/Atikokan', 'America/Atikokan'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Africa/Kigali', 'Africa/Kigali'), ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'), ('Asia/Aden', 'Asia/Aden'), ('America/Kralendijk', 'America/Kralendijk'), ('America/Chihuahua', 'America/Chihuahua'), ('Indian/Cocos', 'Indian/Cocos'), ('Etc/GMT-8', 'Etc/GMT-8'), ('Asia/Oral', 'Asia/Oral'), ('America/Moncton', 'America/Moncton'), ('Africa/Windhoek', 'Africa/Windhoek'), ('America/Los_Angeles', 'America/Los_Angeles'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Africa/Asmera', 'Africa/Asmera'), ('Europe/Volgograd', 'Europe/Volgograd'), ('America/St_Kitts', 'America/St_Kitts'), ('Etc/GMT+5', 'Etc/GMT+5'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('US/Indiana-Starke', 'US/Indiana-Starke'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Pacific/Wake', 'Pacific/Wake'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('Africa/Kampala', 'Africa/Kampala'), ('EST', 'EST'), ('Europe/Riga', 'Europe/Riga'), ('Europe/Simferopol', 'Europe/Simferopol'), ('America/Dominica', 'America/Dominica'), ('America/Lima', 'America/Lima'), ('Etc/GMT-0', 'Etc/GMT-0'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Navajo', 'Navajo'), ('Etc/GMT+1', 'Etc/GMT+1'), ('America/La_Paz', 'America/La_Paz'), ('America/Marigot', 'America/Marigot'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('Australia/Tasmania', 'Australia/Tasmania'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('GMT-0', 'GMT-0'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Asia/Amman', 'Asia/Amman'), ('America/Cancun', 'America/Cancun'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('Asia/Chungking', 'Asia/Chungking'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Asia/Thimphu', 'Asia/Thimphu'), ('US/Pacific', 'US/Pacific'), ('America/Fort_Wayne', 'America/Fort_Wayne'), ('Factory', 'Factory'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('America/Guyana', 'America/Guyana'), ('Asia/Muscat', 'Asia/Muscat'), ('Africa/Djibouti', 'Africa/Djibouti'), ('America/Hermosillo', 'America/Hermosillo'), ('Mexico/General', 'Mexico/General'), ('America/St_Thomas', 'America/St_Thomas'), ('Europe/Belfast', 'Europe/Belfast'), ('Australia/South', 'Australia/South'), ('Libya', 'Libya'), ('Pacific/Niue', 'Pacific/Niue'), ('Pacific/Easter', 'Pacific/Easter'), ('America/Mendoza', 'America/Mendoza'), ('Australia/LHI', 'Australia/LHI'), ('GMT+0', 'GMT+0'), ('Asia/Tashkent', 'Asia/Tashkent'), ('America/Mexico_City', 'America/Mexico_City'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('America/Rio_Branco', 'America/Rio_Branco'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Brazil/DeNoronha', 'Brazil/DeNoronha'), ('Universal', 'Universal'), ('Asia/Thimbu', 'Asia/Thimbu'), ('Australia/NSW', 'Australia/NSW'), ('America/Sitka', 'America/Sitka'), ('Antarctica/Casey', 'Antarctica/Casey'), ('America/Anguilla', 'America/Anguilla'), ('Asia/Tehran', 'Asia/Tehran'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('America/Bahia', 'America/Bahia'), ('Europe/Busingen', 'Europe/Busingen'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Europe/Andorra', 'Europe/Andorra'), ('Asia/Karachi', 'Asia/Karachi'), ('America/Guayaquil', 'America/Guayaquil'), ('Europe/Dublin', 'Europe/Dublin'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Asia/Anadyr', 'Asia/Anadyr'), ('America/Swift_Current', 'America/Swift_Current'), ('Asia/Hovd', 'Asia/Hovd'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Etc/GMT-10', 'Etc/GMT-10'), ('America/Ensenada', 'America/Ensenada'), ('America/Godthab', 'America/Godthab'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Asia/Magadan', 'Asia/Magadan'), ('Cuba', 'Cuba'), ('Europe/Skopje', 'Europe/Skopje'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('WET', 'WET'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('CST6CDT', 'CST6CDT'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('US/Michigan', 'US/Michigan'), ('America/Guadeloupe', 'America/Guadeloupe'), ('Indian/Chagos', 'Indian/Chagos'), ('Africa/Douala', 'Africa/Douala'), ('Asia/Omsk', 'Asia/Omsk'), ('Pacific/Apia', 'Pacific/Apia'), ('Asia/Chita', 'Asia/Chita'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Zulu', 'Zulu'), ('Africa/Maputo', 'Africa/Maputo'), ('Asia/Chongqing', 'Asia/Chongqing'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Asia/Baku', 'Asia/Baku'), ('Africa/Algiers', 'Africa/Algiers'), ('Etc/GMT+2', 'Etc/GMT+2'), ('America/Cayman', 'America/Cayman'), ('America/Toronto', 'America/Toronto'), ('America/Nuuk', 'America/Nuuk'), ('Europe/Sofia', 'Europe/Sofia'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Etc/GMT-5', 'Etc/GMT-5'), ('Pacific/Kanton', 'Pacific/Kanton'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Etc/GMT-6', 'Etc/GMT-6'), ('America/Winnipeg', 'America/Winnipeg'), ('America/Mazatlan', 'America/Mazatlan'), ('NZ', 'NZ'), ('Asia/Makassar', 'Asia/Makassar'), ('America/Boa_Vista', 'America/Boa_Vista'), ('Europe/Podgorica', 'Europe/Podgorica'), ('America/Eirunepe', 'America/Eirunepe'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Israel', 'Israel'), ('Asia/Famagusta', 'Asia/Famagusta'), ('America/Menominee', 'America/Menominee'), ('America/Shiprock', 'America/Shiprock'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Indian/Reunion', 'Indian/Reunion'), ('Asia/Hebron', 'Asia/Hebron'), ('Africa/Freetown', 'Africa/Freetown'), ('Chile/Continental', 'Chile/Continental'), ('Pacific/Midway', 'Pacific/Midway'), ('Asia/Qostanay', 'Asia/Qostanay'), ('America/Belem', 'America/Belem'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Asia/Barnaul', 'Asia/Barnaul'), ('US/East-Indiana', 'US/East-Indiana'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('Africa/Timbuktu', 'Africa/Timbuktu'), ('Etc/GMT-2', 'Etc/GMT-2'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Havana', 'America/Havana'), ('America/Araguaina', 'America/Araguaina'), ('America/St_Vincent', 'America/St_Vincent'), ('Europe/Tiraspol', 'Europe/Tiraspol'), ('Europe/Kyiv', 'Europe/Kyiv'), ('America/Metlakatla', 'America/Metlakatla'), ('Poland', 'Poland'), ('Africa/Abidjan', 'Africa/Abidjan'), ('Asia/Macau', 'Asia/Macau'), ('US/Mountain', 'US/Mountain'), ('America/St_Johns', 'America/St_Johns'), ('Etc/UCT', 'Etc/UCT'), ('Asia/Singapore', 'Asia/Singapore'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Asia/Gaza', 'Asia/Gaza'), ('Europe/Madrid', 'Europe/Madrid'), ('America/Atka', 'America/Atka'), ('Australia/Yancowinna', 'Australia/Yancowinna'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('Australia/Canberra', 'Australia/Canberra'), ('Canada/Pacific', 'Canada/Pacific'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('America/Lower_Princes', 'America/Lower_Princes'), ('America/Costa_Rica', 'America/Costa_Rica'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('Europe/Brussels', 'Europe/Brussels'), ('America/Asuncion', 'America/Asuncion'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('PST8PDT', 'PST8PDT'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Canada/Saskatchewan', 'Canada/Saskatchewan'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('Etc/GMT+10', 'Etc/GMT+10'), ('Asia/Atyrau', 'Asia/Atyrau'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('US/Central', 'US/Central'), ('America/Manaus', 'America/Manaus'), ('Europe/Stockholm', 'Europe/Stockholm'), ('America/Bogota', 'America/Bogota'), ('Asia/Katmandu', 'Asia/Katmandu'), ('Asia/Dacca', 'Asia/Dacca'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Africa/Tunis', 'Africa/Tunis'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Africa/Cairo', 'Africa/Cairo'), ('Indian/Christmas', 'Indian/Christmas'), ('Etc/GMT+0', 'Etc/GMT+0'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('America/St_Lucia', 'America/St_Lucia'), ('Africa/Lagos', 'Africa/Lagos'), ('Africa/Libreville', 'Africa/Libreville'), ('Etc/GMT-4', 'Etc/GMT-4'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/Nome', 'America/Nome'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/Cayenne', 'America/Cayenne'), ('America/Scoresbysund', 'America/Scoresbysund'), ('Mexico/BajaSur', 'Mexico/BajaSur'), ('Asia/Khandyga', 'Asia/Khandyga'), ('America/Matamoros', 'America/Matamoros'), ('Asia/Colombo', 'Asia/Colombo'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Etc/GMT0', 'Etc/GMT0'), ('Asia/Nicosia', 'Asia/Nicosia'), ('America/Santarem', 'America/Santarem'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Africa/Bamako', 'Africa/Bamako'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Asia/Taipei', 'Asia/Taipei'), ('America/Jujuy', 'America/Jujuy'), ('Asia/Dubai', 'Asia/Dubai'), ('Etc/GMT', 'Etc/GMT'), ('GB-Eire', 'GB-Eire'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('Asia/Istanbul', 'Asia/Istanbul'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Europe/Nicosia', 'Europe/Nicosia'), ('America/Tijuana', 'America/Tijuana'), ('US/Samoa', 'US/Samoa'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('US/Aleutian', 'US/Aleutian'), ('Antarctica/South_Pole', 'Antarctica/South_Pole'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('America/Iqaluit', 'America/Iqaluit'), ('America/Antigua', 'America/Antigua'), ('America/Merida', 'America/Merida'), ('CET', 'CET'), ('Africa/Luanda', 'Africa/Luanda'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('America/Tortola', 'America/Tortola'), ('Europe/Istanbul', 'Europe/Istanbul'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('Africa/Niamey', 'Africa/Niamey'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Asia/Manila', 'Asia/Manila'), ('America/Grenada', 'America/Grenada'), ('America/Coral_Harbour', 'America/Coral_Harbour'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('UTC', 'UTC'), ('Etc/GMT+9', 'Etc/GMT+9'), ('Asia/Tel_Aviv', 'Asia/Tel_Aviv'), ('America/Phoenix', 'America/Phoenix'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Asia/Kashgar', 'Asia/Kashgar'), ('America/Nipigon', 'America/Nipigon'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('America/Regina', 'America/Regina'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Etc/GMT-11', 'Etc/GMT-11'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Etc/GMT-1', 'Etc/GMT-1'), ('Etc/GMT+8', 'Etc/GMT+8'), ('Australia/Queensland', 'Australia/Queensland'), ('Indian/Comoro', 'Indian/Comoro'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('Europe/Saratov', 'Europe/Saratov'), ('America/Catamarca', 'America/Catamarca'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('Iran', 'Iran'), ('HST', 'HST'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('MET', 'MET'), ('Australia/Currie', 'Australia/Currie'), ('Etc/UTC', 'Etc/UTC'), ('Etc/GMT-12', 'Etc/GMT-12'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('America/Punta_Arenas', 'America/Punta_Arenas'), ('Portugal', 'Portugal'), ('Europe/Moscow', 'Europe/Moscow'), ('ROC', 'ROC'), ('America/Santiago', 'America/Santiago'), ('Europe/Rome', 'Europe/Rome'), ('America/Campo_Grande', 'America/Campo_Grande'), ('Singapore', 'Singapore'), ('Europe/Vatican', 'Europe/Vatican'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('America/Chicago', 'America/Chicago'), ('Europe/Kirov', 'Europe/Kirov'), ('Africa/Maseru', 'Africa/Maseru'), ('America/Rosario', 'America/Rosario'), ('Europe/Berlin', 'Europe/Berlin'), ('Pacific/Truk', 'Pacific/Truk'), ('Australia/West', 'Australia/West'), ('Pacific/Guam', 'Pacific/Guam'), ('Egypt', 'Egypt'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Europe/Ulyanovsk', 'Europe/Ulyanovsk'), ('America/Edmonton', 'America/Edmonton'), ('Pacific/Yap', 'Pacific/Yap'), ('Asia/Brunei', 'Asia/Brunei'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Mexico/BajaNorte', 'Mexico/BajaNorte'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('America/Guatemala', 'America/Guatemala'), ('NZ-CHAT', 'NZ-CHAT'), ('Brazil/East', 'Brazil/East'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('America/Ojinaga', 'America/Ojinaga'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('America/Ciudad_Juarez', 'America/Ciudad_Juarez'), ('America/Knox_IN', 'America/Knox_IN'), ('America/Dawson', 'America/Dawson'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('America/Montevideo', 'America/Montevideo'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Japan', 'Japan'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Greenwich', 'Greenwich'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Canada/Central', 'Canada/Central'), ('America/Miquelon', 'America/Miquelon'), ('America/Indianapolis', 'America/Indianapolis'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('America/Maceio', 'America/Maceio'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('GB', 'GB'), ('Europe/Tallinn', 'Europe/Tallinn'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('US/Hawaii', 'US/Hawaii'), ('Europe/Budapest', 'Europe/Budapest'), ('Africa/Banjul', 'Africa/Banjul'), ('Etc/GMT+7', 'Etc/GMT+7'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('America/El_Salvador', 'America/El_Salvador'), ('GMT0', 'GMT0'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('America/Boise', 'America/Boise'), ('Europe/Vienna', 'Europe/Vienna'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Africa/Asmara', 'Africa/Asmara'), ('America/Denver', 'America/Denver'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Asia/Kolkata', 'Asia/Kolkata'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Europe/Paris', 'Europe/Paris'), ('America/Louisville', 'America/Louisville'), ('Atlantic/Azores', 'Atlantic/Azores'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('Hongkong', 'Hongkong'), ('Asia/Saigon', 'Asia/Saigon'), ('America/Noronha', 'America/Noronha'), ('Etc/Greenwich', 'Etc/Greenwich'), ('Indian/Mahe', 'Indian/Mahe'), ('EET', 'EET'), ('EST5EDT', 'EST5EDT'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Pacific/Palau', 'Pacific/Palau'), ('Canada/Eastern', 'Canada/Eastern'), ('America/Paramaribo', 'America/Paramaribo'), ('Europe/Prague', 'Europe/Prague'), ('Canada/Mountain', 'Canada/Mountain'), ('Turkey', 'Turkey'), ('Brazil/West', 'Brazil/West'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Australia/Perth', 'Australia/Perth'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('America/Buenos_Aires', 'America/Buenos_Aires'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Kwajalein', 'Kwajalein'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Eire', 'Eire'), ('America/Adak', 'America/Adak'), ('Europe/Bucharest', 'Europe/Bucharest'), ('America/Juneau', 'America/Juneau'), ('Europe/Samara', 'Europe/Samara'), ('Europe/Lisbon', 'Europe/Lisbon'), ('America/New_York', 'America/New_York'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Atlantic/Jan_Mayen', 'Atlantic/Jan_Mayen'), ('Africa/Bangui', 'Africa/Bangui'), ('Etc/GMT+12', 'Etc/GMT+12'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('Etc/GMT+3', 'Etc/GMT+3'), ('localtime', 'localtime'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Etc/GMT-7', 'Etc/GMT-7'), ('Europe/Astrakhan', 'Europe/Astrakhan'), ('Canada/Yukon', 'Canada/Yukon'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Australia/ACT', 'Australia/ACT'), ('Asia/Vientiane', 'Asia/Vientiane'), ('America/Creston', 'America/Creston'), ('America/Cuiaba', 'America/Cuiaba'), ('Africa/Khartoum', 'Africa/Khartoum'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/Martinique', 'America/Martinique'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Europe/London', 'Europe/London'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('ROK', 'ROK'), ('Etc/Universal', 'Etc/Universal'), ('Etc/GMT-9', 'Etc/GMT-9'), ('US/Arizona', 'US/Arizona'), ('Etc/GMT+4', 'Etc/GMT+4'), ('America/Anchorage', 'America/Anchorage'), ('Etc/GMT-14', 'Etc/GMT-14'), ('America/Virgin', 'America/Virgin'), ('PRC', 'PRC'), ('America/Montserrat', 'America/Montserrat'), ('America/Fort_Nelson', 'America/Fort_Nelson'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Europe/Jersey', 'Europe/Jersey'), ('America/Managua', 'America/Managua'), ('Africa/Conakry', 'Africa/Conakry'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Australia/Darwin', 'Australia/Darwin'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Etc/GMT-13', 'Etc/GMT-13'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Europe/Helsinki', 'Europe/Helsinki'), ('UCT', 'UCT'), ('Pacific/Ponape', 'Pacific/Ponape'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Asia/Macao', 'Asia/Macao'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('Asia/Tomsk', 'Asia/Tomsk'), ('Australia/Eucla', 'Australia/Eucla'), ('America/Panama', 'America/Panama'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Australia/North', 'Australia/North'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Etc/GMT+6', 'Etc/GMT+6'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('Jamaica', 'Jamaica'), ('America/Grand_Turk', 'America/Grand_Turk'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('Pacific/Wallis', 'Pacific/Wallis'), ('MST7MDT', 'MST7MDT'), ('Atlantic/Faeroe', 'Atlantic/Faeroe'), ('Australia/Victoria', 'Australia/Victoria'), ('Australia/Sydney', 'Australia/Sydney'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Africa/Malabo', 'Africa/Malabo'), ('Asia/Ashkhabad', 'Asia/Ashkhabad'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Ulan_Bator', 'Asia/Ulan_Bator'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('Indian/Maldives', 'Indian/Maldives'), ('America/Aruba', 'America/Aruba'), ('Europe/Athens', 'Europe/Athens'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Asia/Beirut', 'Asia/Beirut'), ('America/Caracas', 'America/Caracas'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('America/Whitehorse', 'America/Whitehorse'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('America/Vancouver', 'America/Vancouver'), ('Asia/Ujung_Pandang', 'Asia/Ujung_Pandang'), ('Antarctica/Troll', 'Antarctica/Troll'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('Africa/Accra', 'Africa/Accra'), ('Australia/Hobart', 'Australia/Hobart'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Asia/Harbin', 'Asia/Harbin'), ('Europe/Monaco', 'Europe/Monaco'), ('Etc/Zulu', 'Etc/Zulu'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Asia/Dili', 'Asia/Dili'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('America/Porto_Acre', 'America/Porto_Acre'), ('Iceland', 'Iceland'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Asia/Almaty', 'Asia/Almaty'), ('Asia/Urumqi', 'Asia/Urumqi'), ('America/Rainy_River', 'America/Rainy_River'), ('America/Jamaica', 'America/Jamaica'), ('Australia/Adelaide', 'Australia/Adelaide'), ('America/Fortaleza', 'America/Fortaleza'), ('Atlantic/Canary', 'Atlantic/Canary'), ('America/Yellowknife', 'America/Yellowknife'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('GMT', 'GMT'), ('Europe/Minsk', 'Europe/Minsk'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Asia/Seoul', 'Asia/Seoul'), ('US/Eastern', 'US/Eastern'), ('Africa/Dakar', 'Africa/Dakar'), ('Pacific/Gambier', 'Pacific/Gambier'), ('US/Alaska', 'US/Alaska'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Asia/Yangon', 'Asia/Yangon')], default=django.utils.timezone.get_default_timezone_name, max_length=50, verbose_name='Часовой пояс'),
        ),
    ]