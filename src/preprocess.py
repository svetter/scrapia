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

import collections

from src.constants import STAY_DATES



def sort_data_by_start_date(data):
	data_by_date = collections.OrderedDict()
	for date in STAY_DATES:
		data_by_date[date[0]] = []
	
	for line in data:
		start_date = line['start_date']
		data_by_date[start_date].append(line)
	
	return data_by_date



def process_all_data(raw_data, num_price_brackets, num_price_brackets_filtered, get_price_bracket_ind, get_ticket_offset, meal_filter):
	first_scrape_date = raw_data[0][1]
	result = collections.OrderedDict()
	# result has format: OrderedDict<scrape_date, scrape_date, data, max_num_avail, max_num_gone, max_num_avail_filtered, max_num_gone_filtered>
	# result[0]['data'] has format: OrderedDict<start_date, room_data, num_avail_by_price_bracket, num_gone_by_price_bracket>
	
	for data_one_scrape_date, scrape_date in raw_data:
		# in this loop, we process all data for ONE SCRAPE DATE
		dataset_sorted = sort_data_by_start_date(data_one_scrape_date)
		
		# results for all data as map
		processed_dataset = collections.OrderedDict()
		
		max_num_avail			= 0
		max_num_gone			= 0
		max_num_avail_filtered	= 0
		max_num_gone_filtered	= 0
		
		for _, (start_date, lines_one_start_date) in enumerate(dataset_sorted.items()):
			# in this loop, we process all data for ONE START DATE (at one scrape date)
			num_avail_by_price_bracket	= [0] * num_price_brackets
			num_gone_by_price_bracket	= [0] * num_price_brackets
			num_avail_filtered_price	= 0
			num_gone_filtered_price		= 0
			
			# sort all rooms by felix-id first
			sorted_by_room = {}
			for line in lines_one_start_date:
				if sorted_by_room.get(line['felix-id']) is None:
					sorted_by_room[line['felix-id']] = []
				sorted_by_room[line['felix-id']].append(line)
			
			# for every available room, pick the cheapest package (meal option and other included benefits)
			cheapest_lines_one_start_date = []
			for room_data in sorted_by_room.values():
				cheapest_line = None
				for line in room_data:
					# in this loop, we process all data for ONE ROOM TYPE (at one start date and one scrape date), equivalent to one CSV line
					if meal_filter is not None:
						if line['meals'] not in meal_filter:
							raise ValueError("Found unknown meal description '" + line['meals'] + "'. Please add to filter dict.")
						if not meal_filter[line['meals']]:
							continue
					# keep line if it is the cheapest package for the current room so far
					if cheapest_line is None or line['price'] < cheapest_line['price']:
						cheapest_line = line
				
				cheapest_lines_one_start_date.append(cheapest_line)
				
				# we now have the cheapest package for the current room stored in cheapest_line
				# sort room into price bracket
				price_per_person = cheapest_line['price'] / cheapest_line['size'] + get_ticket_offset(cheapest_line['start_date'])
				price_bracket_ind = get_price_bracket_ind(price_per_person)
				num_avail_by_price_bracket[price_bracket_ind] += cheapest_line['num_available']
			
			for price_ind in range(len(num_avail_by_price_bracket)):
				# in this loop, we process all data for ONE PRICE BRACKET (at one start date and one scrape date)
				num_available = num_avail_by_price_bracket[price_ind]
				max_num_avail = max(num_available, max_num_avail)
				if price_ind < num_price_brackets_filtered:
					num_avail_filtered_price += num_available
					max_num_avail_filtered = max(num_available, max_num_avail_filtered)
				
				num_gone = 0
				if scrape_date != first_scrape_date:
					num_gone = result[first_scrape_date]['data'][start_date]['num_avail_by_price_bracket'][price_ind] - num_available
					num_gone = max(num_gone, 0)
					max_num_gone = max(num_gone, max_num_gone)
					if price_ind < num_price_brackets_filtered:
						num_gone_filtered_price += num_gone
						max_num_gone_filtered = max(num_gone, max_num_gone_filtered)
				num_gone_by_price_bracket[price_ind] = num_gone
			
			processed_dataset[start_date] = {
				'start_date':					start_date,
				'room_data':					cheapest_lines_one_start_date,
				'num_avail_by_price_bracket':	num_avail_by_price_bracket,
				'num_gone_by_price_bracket':	num_gone_by_price_bracket,
				'num_avail_filtered_price':		num_avail_filtered_price,
				'num_gone_filtered_price':		num_gone_filtered_price
			}
		
		result[scrape_date] = {
			'scrape_date':						scrape_date,
			'data':								processed_dataset,
			'max_num_avail':					max_num_avail,
			'max_num_gone':						max_num_gone,
			'max_num_avail_filtered':			max_num_avail_filtered,
			'max_num_gone_filtered':			max_num_gone_filtered
		}
	return result