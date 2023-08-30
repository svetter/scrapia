import collections



def sort_data_by_date(data):
	data_by_date = []
	previous_date = ''
	for line in data:
		if previous_date != line['start_date']:
			data_by_date.append([])
		data_by_date[len(data_by_date) - 1].append(line)
		previous_date = line['start_date']
	
	return data_by_date



def process_all_data(raw_data, num_price_brackets, num_price_brackets_filtered, get_price_bracket_ind, get_ticket_offset, meal_filter):
	first_scrape_date = raw_data[0][1]
	result = collections.OrderedDict()
	# result has format: OrderedDict<scrape_date, scrape_date, data, max_num_avail, max_num_gone, max_num_avail_filtered, max_num_gone_filtered>
	# result[0]['data'] has format: OrderedDict<start_date, room_data, num_avail_by_price_bracket, num_gone_by_price_bracket>
	
	for data_one_scrape_date, scrape_date in raw_data:
		# in this loop, we process all data for ONE SCRAPE DATE
		dataset_sorted = sort_data_by_date(data_one_scrape_date)
		
		# results for all data as map
		processed_dataset = collections.OrderedDict()
		
		max_num_avail			= 0
		max_num_gone			= 0
		max_num_avail_filtered	= 0
		max_num_gone_filtered	= 0
		
		for lines_one_start_date in dataset_sorted:
			# in this loop, we process all data for ONE START DATE (at one scrape date)
			start_date = lines_one_start_date[0]['start_date']
			
			num_avail_by_price_bracket	= [0] * num_price_brackets
			num_gone_by_price_bracket	= [0] * num_price_brackets
			
			# sort all rooms into price brackets first
			for line in lines_one_start_date:
				# in this loop, we process all data for ONE ROOM TYPE (at one start date and one scrape date), equivalent to one CSV line
				if meal_filter is not None:
					if line['meals'] not in meal_filter:
						raise ValueError("Found unknown meal description '" + line['meals'] + "'. Please add to filter dict.")
					if not meal_filter[line['meals']]:
						continue
				
				price_per_person = line['price'] / line['size'] + get_ticket_offset(line['start_date'])
				price_bracket_ind = get_price_bracket_ind(price_per_person)
				num_avail_by_price_bracket[price_bracket_ind] += line['num_available']
			
			for price_ind in range(len(num_avail_by_price_bracket)):
				# in this loop, we process all data for ONE PRICE BRACKET (at one start date and one scrape date)
				num_available = num_avail_by_price_bracket[price_ind]
				max_num_avail = max(num_available, max_num_avail)
				if price_ind >= num_price_brackets_filtered:
					max_num_avail_filtered = max(num_available, max_num_avail_filtered)
				
				num_gone = 0
				if scrape_date != first_scrape_date:
					num_gone = result[first_scrape_date]['data'][start_date]['num_avail_by_price_bracket'][price_ind] - num_available
					num_gone = max(num_gone, 0)
					max_num_gone = max(num_gone, max_num_gone)
					if price_ind < num_price_brackets_filtered:
						max_num_gone_filtered = max(num_gone, max_num_gone_filtered)
				num_gone_by_price_bracket[price_ind] = num_gone
			
			processed_dataset[start_date] = {
				'start_date':					start_date,
				'room_data':					lines_one_start_date,
				'num_avail_by_price_bracket':	num_avail_by_price_bracket,
				'num_gone_by_price_bracket':	num_gone_by_price_bracket
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