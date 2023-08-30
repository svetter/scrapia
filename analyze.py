import os
import math
import collections
from dateutil.parser import isoparse as parse_iso_date
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates



# settings for filtering by price per person
filter_price_per_person = 100

# settings for filtering rooms by meal options (True = include)
meal_filter = {
	'Übernachtung ohne Frühstück':		False,
	'Übernachtung - Frühstück':			True,
	'Übernachtung Frühstück NonFlex':	True,
	'Übernachtung - Halbpension':		False,
}

# offsets for ticket category 4 (95€/108€/121€)
ticket_price_offset_fr = -95 + 108
ticket_price_offset_sa = -95 + 121



def parse_csv(filepath):
	result = []
	
	with open(filepath, 'r', encoding='UTF-8') as f:
		lines = f.read().split('\n')[1:]
	
	for line in lines:
		if line == '':
			continue
		
		values = line.split(',')
		
		start_date		= parse_iso_date(values[0])
		end_date		= parse_iso_date(values[1])
		description		= values[2]
		num_persons		= int(values[3])
		meals			= values[4]
		price			= float(values[5][:-1])
		num_avail		= int(values[6])
		felix_id		= values[7]
		package_id		= values[8]
		room_id			= values[9]
		name_param		= values[10]
		scraped_date	= parse_iso_date(values[11])
		
		result.append({
			'start_date':		start_date,
			'end_date':			end_date,
			'description':		description,
			'size':				num_persons,
			'meals':			meals,
			'price':			price,
			'num_available':	num_avail,
			'felix-id':			felix_id,
			'package-id':		package_id,
			'room-id':			room_id,
			'name-param':		name_param,
			'scraped_date':		scraped_date
		})
	
	return result

def parse_all_csv(path):
	result = []
	
	filenames = sorted(os.listdir(path))
	for filename in filenames:
		if filename.endswith('.csv'):
			csv_lines = parse_csv(os.path.join(path, filename))
			result.append((csv_lines[1:], parse_iso_date(filename[:-4])))
	
	return result



# parse all CSV data and process it
all_data = parse_all_csv('collected_results')

first_scrape_date	= all_data[ 0][1]
last_scrape_date	= all_data[-1][1]



price_rounding = 5

def get_price_bracket_ind(price):
	return round(price / price_rounding)

def get_bracket_price(bracket_ind):
	return bracket_ind * price_rounding

def get_ticket_offset(date):
	weekday = date.weekday()
	if weekday == 4:	# Friday
		return ticket_price_offset_fr
	if weekday == 5:	# Saturday
		return ticket_price_offset_sa
	return 0

def find_max_price_per_person(raw_data):
	max_price_per_person = 0
	for lines_one_scrape_date, _ in raw_data:
		for line in lines_one_scrape_date:
			price_per_person = line['price'] / line['size'] + get_ticket_offset(line['start_date'])
			max_price_per_person = max(max_price_per_person, price_per_person)
	return max_price_per_person

max_price_per_person		= find_max_price_per_person(all_data)
num_price_brackets			= math.ceil(   max_price_per_person / price_rounding)
num_price_brackets_filtered	= math.ceil(filter_price_per_person / price_rounding) + 1



def sort_data_by_date(data):
	data_by_date = []
	previous_date = ''
	for line in data:
		if previous_date != line['start_date']:
			data_by_date.append([])
		data_by_date[len(data_by_date) - 1].append(line)
		previous_date = line['start_date']
	
	return data_by_date



def process_all_data(raw_data, meal_filter=None):
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



processed_data = process_all_data(all_data, meal_filter=meal_filter)



def scale_avail(num_available):
	return 10 + (num_available * 10) + (num_available ** 1.5 * 30)



# prepare figure 1
fig1_x		= []
fig1_y		= []
fig1_size	= []
fig1_color	= []
fig1_max_size	= processed_data[last_scrape_date]['max_num_avail_filtered']
fig1_max_color	= processed_data[last_scrape_date]['max_num_gone_filtered']

for _, (start_date, data_one_start_date) in enumerate(processed_data[last_scrape_date]['data'].items()):
	for price_bracket_ind in range(num_price_brackets_filtered):
		num_available	= data_one_start_date['num_avail_by_price_bracket'][price_bracket_ind]
		num_gone		= data_one_start_date['num_gone_by_price_bracket' ][price_bracket_ind]
		
		if num_available > 0 or num_gone > 0:
			fig1_x.append(start_date.strftime("%a %d.%m."))
			fig1_y.append(get_bracket_price(price_bracket_ind))
			fig1_size.append(scale_avail(num_available))
			fig1_color.append(num_gone)



# FIGURE 1: scatterplot with hotness
fig1 = plt.figure()
window_title = "Room availability analysis – JUFA Hotel Bregenz 2024"
fig1_plot_title = "Available rooms below " + str(filter_price_per_person) + "€ per person by date and price"
fig1_plot_subtitle = "Circle size shows number of rooms available. All prices include (only) breakfast and are adjusted for higher ticket prices on Fr/Sa."
plt.get_current_fig_manager().set_window_title(window_title)
fig1.suptitle(fig1_plot_title, fontsize=14)
plt.title(fig1_plot_subtitle, fontsize=8)
fig1.subplots_adjust(left=0.07, right=1.09, top=0.9, bottom=0.13)
fig1.set_size_inches(12, 6)
# scatterplot
fig1_axes = plt.gca()
scatter = fig1_axes.scatter(fig1_x, fig1_y, s=fig1_size, c=fig1_color, cmap='summer', vmin=0, vmax=fig1_max_color, alpha=1)
fig1_axes.set_ylabel("Price per person (rounded to " + str(price_rounding) + "€)")
fig1_axes.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f €'))
# x-axis and legends
plt.xticks(rotation=45, ha='right')
[tick.set_color('blue' if tick.get_text().startswith('Thu') else 'black') for tick in fig1_axes.xaxis.get_ticklabels()]
# create list of sizes to show in legend
size_legend_labels = [0, 1] + [*range(2, 2 * int(fig1_max_size / 2) + 1, 2)]
size_legend_handles = [plt.scatter([],[], s=scale_avail(size_legend_labels[i]), label=size_legend_labels[i], color='gray') for i in range(len(size_legend_labels))]
# create size legend
plt.legend(handles=size_legend_handles, loc='lower right', labelspacing=1.8, borderpad=1.2)
# create color legend
fig1.colorbar(scatter, label="Already booked or price changed", location='right', pad=0.025)



# prepare figure 2
fig2_x	= []
fig2_y1	= []
fig2_y2	= []
fig2_y3	= []
fig2_y4	= []

for data_one_scrape_date, scrape_date in all_data:
	days = set()
	num_avail = 0
	num_different_rooms = 0
	min_price = max_price_per_person
	avg_price = 0
	max_price = 0
	for line in data_one_scrape_date:
		if line['size'] >= 4 and meal_filter[line['meals']]:
			days.add(line['start_date'])
			num_avail += line['num_available']
			num_different_rooms += 1
			price_per_person = line['price'] / line['size']
			min_price = min(min_price, price_per_person)
			avg_price += price_per_person
			max_price = max(max_price, price_per_person)
	num_avail /= len(days)
	avg_price /= num_different_rooms
	
	if num_avail > 0:
		fig2_x.append(scrape_date)
		fig2_y1.append(num_avail)
		fig2_y2.append(min_price)
		fig2_y3.append(avg_price)
		fig2_y4.append(max_price)

# FIGURE 2: line plots for changes in availability and price
fig2 = plt.figure()
fig2_plot_title = "Available rooms for 4 or more people and their prices over time"
fig2_plot_subtitle = "Prices are for room options which include (only) breakfast."
plt.get_current_fig_manager().set_window_title(window_title)
fig2.suptitle(fig2_plot_title, fontsize=14)
plt.title(fig2_plot_subtitle, fontsize=8)
fig2.subplots_adjust(left=0.06, right=0.94, top=0.9, bottom=0.07)
fig2.set_size_inches(12, 6)
# plot 1 (left y-axis): number of available rooms
fig2_ax1 = plt.gca()
fig2_plot1 = fig2_ax1.plot(fig2_x, fig2_y1, color='black', marker='o', label='Number of available rooms on each day')
fig2_ax1.set_ylabel('Average of available rooms per day')
fig2_ax1.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
# plot 2-4 (right y-axis): minimum/average/maximum price per person
fig2_ax2 = fig2_ax1.twinx()
fig2_plot2 = fig2_ax2.plot(fig2_x, fig2_y2, color='blue', marker='v', label='Minimum price per person')
fig2_plot3 = fig2_ax2.plot(fig2_x, fig2_y3, color='purple', marker='D', label='Average price per person')
fig2_plot4 = fig2_ax2.plot(fig2_x, fig2_y4, color='red', marker='^', label='Maximum price per person')
fig2_ax2.set_ylabel('Price per person')
fig2_ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f €'))
fig2_ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
# legend and x-axis
plt.legend(handles=[fig2_plot1[0], fig2_plot4[0], fig2_plot3[0], fig2_plot2[0]], loc='lower center')
fig2_ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
fig2_ax1.xaxis.set_major_formatter(mdates.DateFormatter('%B %Y'))
plt.xticks(rotation=45, ha='right')



plt.show()
