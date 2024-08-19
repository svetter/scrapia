# Copyright 2023-2024 Simon Vetter
#
# This file is part of Scrapia.
#
# Scrapia is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# Scrapia is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Scrapia.
# If not, see <https://www.gnu.org/licenses/>.

import sys
import os.path
import random
import time
import datetime

from python.constants import STAY_DATES_2025 as STAY_DATES
from python.html_extract import extract_room_data
from python.http_request import get_html_data_method1
from python.http_request import get_html_data_method2



num_adults_requested = '4'



use_cached_response = len(sys.argv) < 2 or sys.argv[1] != 'wet'
cached_response_filename_method1 = 'resources/cached_response_method1.html'
cached_response_filename_method2 = 'resources/cached_response_method2.html'

room_infos_all_dates = []

sleep_time_base = 9 + 3 * random.random()

i = 0
num_dates_to_scrape = len(STAY_DATES)
for date_pair in STAY_DATES:
	if (date_pair[0] - datetime.date.today()).days < 0:
		num_dates_to_scrape -= 1
		continue	# skip past dates
	else:
		i += 1
	
	print("[{:02}/{:02}]".format(i, num_dates_to_scrape), end='\t')
	print("Gathering data for " + date_pair[0].isoformat() + " to " + date_pair[1].isoformat())
	sys.stdout.flush()
	
	if use_cached_response:
		with open(cached_response_filename_method1, 'r', encoding='UTF-8') as f:
			html1 = f.read()
		with open(cached_response_filename_method2, 'r', encoding='UTF-8') as f:
			html2 = f.read()
	else:
		html1 = get_html_data_method1(num_adults_requested, date_pair[0], date_pair[1])
		html2 = get_html_data_method2(num_adults_requested, date_pair[0], date_pair[1])
	
	room_info = extract_room_data(html1, html2)
	room_infos_all_dates.append((date_pair, room_info))
	
	sleep_time = sleep_time_base + random.gauss(3 + 2 * random.random(), 3 + 2 * random.random())
	print("\t\tWaiting {sleep_time:.2f}s before the next request".format(sleep_time=sleep_time))
	sys.stdout.flush()
	if not use_cached_response and date_pair != STAY_DATES[len(STAY_DATES) - 1]:
		time.sleep(sleep_time)



today_str = datetime.date.today().isoformat()

year = STAY_DATES[0][0].year
results_filepath = os.path.join('collected_results', str(year), today_str + '.csv')
i = 1
while os.path.isfile(results_filepath):
	results_filepath = os.path.join('collected_results', str(year), today_str + '_' + str(i) + '.csv')
	i += 1

if use_cached_response:
	results_filepath = 'collected_results/dry_results.csv'

sep = ','

with open(results_filepath, 'w', encoding='UTF-8', newline='\n') as f:
	f.write(sep.join(["Check-in date", "Check-out date", "Room description", "Room capacity", "Meals", "Price", "Number available", "felix-id", "package-id", "room-id", "name-param", "Scrape date"]) + '\n')
	
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

print("\nAll data processed and written to file " + results_filepath)
