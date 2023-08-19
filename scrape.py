import os.path
import random
import time
import datetime

from html_extract import extract_room_data
from http_request import get_html_data



num_adults = '4'
dates = [
	[datetime.date(2024, 7, 17), datetime.date(2024, 7, 18)],
	[datetime.date(2024, 7, 19), datetime.date(2024, 7, 20)],
	[datetime.date(2024, 7, 20), datetime.date(2024, 7, 21)],
	[datetime.date(2024, 7, 21), datetime.date(2024, 7, 22)],
	[datetime.date(2024, 7, 23), datetime.date(2024, 7, 24)],
	[datetime.date(2024, 7, 24), datetime.date(2024, 7, 25)],
	[datetime.date(2024, 7, 25), datetime.date(2024, 7, 26)],
	[datetime.date(2024, 7, 26), datetime.date(2024, 7, 27)],
	[datetime.date(2024, 7, 27), datetime.date(2024, 7, 28)],
	[datetime.date(2024, 7, 28), datetime.date(2024, 7, 29)],
	[datetime.date(2024, 7, 30), datetime.date(2024, 7, 31)],
	[datetime.date(2024, 7, 31), datetime.date(2024, 8,  1)],
	[datetime.date(2024, 8,  1), datetime.date(2024, 8,  2)],
	[datetime.date(2024, 8,  2), datetime.date(2024, 8,  3)],
	[datetime.date(2024, 8,  3), datetime.date(2024, 8,  4)],
	[datetime.date(2024, 8,  4), datetime.date(2024, 8,  5)],
	[datetime.date(2024, 8,  6), datetime.date(2024, 8,  7)],
	[datetime.date(2024, 8,  7), datetime.date(2024, 8,  8)],
	[datetime.date(2024, 8,  9), datetime.date(2024, 8, 10)],
	[datetime.date(2024, 8, 10), datetime.date(2024, 8, 11)],
	[datetime.date(2024, 8, 11), datetime.date(2024, 8, 12)],
	[datetime.date(2024, 8, 13), datetime.date(2024, 8, 14)],
	[datetime.date(2024, 8, 16), datetime.date(2024, 8, 17)],
	[datetime.date(2024, 8, 17), datetime.date(2024, 8, 18)],
	[datetime.date(2024, 8, 18), datetime.date(2024, 8, 19)]
]



use_cached_response = True
cached_response_filename = 'cached_response.html'

room_infos_all_dates = []

sleep_time_base = 9 + 3 * random.random()

for date_pair in dates:
	print("Gathering data for " + date_pair[0].isoformat() + " to " + date_pair[1].isoformat())
	if use_cached_response:
		with open(cached_response_filename, 'r', encoding='UTF-8') as f:
			html = f.read()
	else:
		html = get_html_data(num_adults, date_pair[0], date_pair[1])
	
	room_info = extract_room_data(html)
	room_infos_all_dates.append((date_pair, room_info))
	
	sleep_time = sleep_time_base + random.gauss(3 + 2 * random.random(), 3 + 2 * random.random())
	print("\tWaiting {sleep_time:.2f}s before the next request".format(sleep_time=sleep_time))
	if not use_cached_response and date_pair != dates[len(dates)-1]:
		time.sleep(sleep_time)



today_str = datetime.date.today().isoformat()

if use_cached_response:
	results_filepath = 'results.csv'
else:
	results_filepath = os.path.join('collected_results', today_str + '.csv')
	i = 1
	while os.path.isfile(results_filepath):
		results_filepath = os.path.join('collected_results', today_str + '_' + str(i) + '.csv')
		i += 1

sep = '\t'

with open(results_filepath, 'w', encoding='UTF-8', newline='\n') as f:
	f.write(sep.join(["Check-in date", "Check-out date", "Room description", "Meals", "Room capacity", "Price", "Number available", "felix-id", "package-id", "room-id", "name-param", "Scrape date"]) + '\n')
	
	if use_cached_response:
		f.write("NOT REAL DATA!\n")
	
	for room_infos_one_date in room_infos_all_dates:
		dates_string = room_infos_one_date[0][0].isoformat() + sep + room_infos_one_date[0][1].isoformat() + sep
		for room_info in room_infos_one_date[1]:
			room_info_csv_string = dates_string
			room_info_csv_string += room_info['description'] + sep
			room_info_csv_string += str(room_info['size']) + sep
			room_info_csv_string += room_info['meals'] + sep
			room_info_csv_string += "{price:.2f}€".format(price=room_info['price']) + sep
			room_info_csv_string += str(room_info['num_available']) + sep
			
			room_info_csv_string += room_info['felix-id'] + sep
			room_info_csv_string += room_info['package-id'] + sep
			room_info_csv_string += room_info['room-id'] + sep
			room_info_csv_string += room_info['name-param'] + sep
			
			room_info_csv_string += today_str
			
			f.write(room_info_csv_string + '\n')

print("\nAll data processed and written to CSV.")
