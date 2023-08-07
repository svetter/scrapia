import random
import time
import datetime

from html_extract import extract_room_data
from http_request import get_html_data



num_adults = '4'
dates = [
	['2024-07-17', '2024-07-18'],
	['2024-07-19', '2024-07-20'],
	['2024-07-20', '2024-07-21'],
	['2024-07-21', '2024-07-22'],
	['2024-07-23', '2024-07-24'],
	['2024-07-24', '2024-07-25'],
	['2024-07-25', '2024-07-26'],
	['2024-07-26', '2024-07-27'],
	['2024-07-27', '2024-07-28'],
	['2024-07-28', '2024-07-29'],
	['2024-07-30', '2024-07-31'],
	['2024-07-31', '2024-08-01'],
	['2024-08-01', '2024-08-02'],
	['2024-08-02', '2024-08-03'],
	['2024-08-03', '2024-08-04'],
	['2024-08-04', '2024-08-05'],
	['2024-08-06', '2024-08-07'],
	['2024-08-07', '2024-08-08'],
	['2024-08-09', '2024-08-10'],
	['2024-08-10', '2024-08-11'],
	['2024-08-11', '2024-08-12'],
	['2024-08-13', '2024-08-14'],
	['2024-08-16', '2024-08-17'],
	['2024-08-17', '2024-08-18'],
	['2024-08-18', '2024-08-19']
]



use_cached_response = True
cached_response_filename = 'cached_response.html'

room_infos_all_dates = []

sleep_time_base = 8 + 2 * random.random() + 3 * random.random()

for date_pair in dates:
	print("Gathering data for", date_pair)
	if use_cached_response:
		with open(cached_response_filename, 'r') as f:
			html = f.read()
	else:
		html = get_html_data(num_adults, date_pair[0], date_pair[1])
	
	room_info = extract_room_data(html)
	room_infos_all_dates.append((date_pair, room_info))
	
	sleep_time = sleep_time_base + random.gauss(3 + 2 * random.random(), 3 + 2 * random.random())
	print("\tWaiting {sleep_time:.2f}s before the next request".format(sleep_time=sleep_time))
	if not use_cached_response and date_pair != dates[len(dates)-1]:
		time.sleep(sleep_time)



results_filename = 'results.csv'
sep = '\t'

with open(results_filename, 'w') as f:
	f.write(sep.join(["Ankunft", "Abreise", "Beschreibung", "Größe", "Preis", "Verfügbar", "felix-id", "package-id", "room-id", "name-param", "Abgerufen am"]) + '\n')
	
	if use_cached_response:
		f.write("NOT REAL DATA!\n")
	
	for room_infos_one_date in room_infos_all_dates:
		dates_string = room_infos_one_date[0][0] + sep + room_infos_one_date[0][1] + sep
		for room_info in room_infos_one_date[1]:
			room_info_csv_string = dates_string
			room_info_csv_string += room_info['description'] + sep
			room_info_csv_string += str(room_info['size']) + sep
			room_info_csv_string += "{price:.2f}€".format(price=room_info['price']).replace('.', ',') + sep
			room_info_csv_string += str(room_info['num_available']) + sep
			
			room_info_csv_string += room_info['felix-id'] + sep
			room_info_csv_string += room_info['package-id'] + sep
			room_info_csv_string += room_info['room-id'] + sep
			room_info_csv_string += room_info['name-param'] + sep
			
			room_info_csv_string += datetime.date.today().isoformat()
			f.write(room_info_csv_string + '\n')
