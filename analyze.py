import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from dateutil.parser import isoparse as parse_iso_date



filter_price_per_person = 100

window_title = "Room availability analysis – JUFA Hotel Bregenz 2024"

# offsets for ticket category 4 (95€/108€/121€)
ticket_price_offset_fr = -95 + 108
ticket_price_offset_sa = -95 + 121



def get_ticket_offset(date):
	weekday = date.weekday()
	if weekday == 4:	# Friday
		return ticket_price_offset_fr
	if weekday == 5:	# Saturday
		return ticket_price_offset_sa
	return 0



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
			result.append((csv_lines[1:], filename[:-4]))
	
	return result

def parse_first_csv(path):
	filenames = sorted(os.listdir(path))
	return parse_csv(os.path.join(path, filenames[0]))

def parse_last_csv(path):
	filenames = sorted(os.listdir(path))
	return parse_csv(os.path.join(path, filenames[len(filenames)-1]))

def filter_lines(lines):
	result = []
	
	for line in lines:
		price_per_person = line['price'] / line['size'] + get_ticket_offset(line['start_date'])
		if price_per_person <= filter_price_per_person and line['meals'] == "Übernachtung - Frühstück":
			result.append(line)
	
	return result



csv_data_current	= filter_lines(parse_last_csv('collected_results'))
csv_data_first		= filter_lines(parse_first_csv('collected_results'))

price_rounding = 5
prices_per_person = [line['price'] / line['size'] + get_ticket_offset(line['start_date']) for line in (csv_data_current + csv_data_first)]
min_price_per_person = min(prices_per_person)
min_price_per_person_rounded = int((min_price_per_person + price_rounding / 2) / price_rounding) * price_rounding
max_price_per_person = max(prices_per_person)

def get_price_ind(price):
	return int((price - min_price_per_person_rounded + price_rounding / 2) / price_rounding)

def get_price_bracket(price_ind):
	return price_ind * price_rounding + min_price_per_person_rounded



def sort_data_by_date(data):
	data_by_date = []
	previous_date = ''
	for line in data:
		if previous_date != line['start_date']:
			data_by_date.append([])
		data_by_date[len(data_by_date) - 1].append(line)
		previous_date = line['start_date']
	
	return data_by_date

data_by_date_current	= sort_data_by_date(csv_data_current)
data_by_date_first		= sort_data_by_date(csv_data_first)



num_avail_by_date_and_price_first = {}

for lines in data_by_date_first:
	date = lines[0]['start_date']
	
	num_avail_by_price = [0] * (get_price_ind(max_price_per_person) + 1)
	
	for line in lines:
		price_per_person = line['price'] / line['size']
		price_per_person += get_ticket_offset(date)	# take into account that tickets are more expensive some days
		num_avail_by_price[get_price_ind(price_per_person)] += line['num_available']
	
	num_avail_by_date_and_price_first[date] = num_avail_by_price



# prepare figure 1
fig1_x = []
fig1_y = []
fig1_size = []
fig1_color = []

def scale_avail(num_available):
	return 10 + (num_available * 10) + (num_available ** 1.5) * 30

max_num_avail = 1
max_num_gone = 1

for lines in data_by_date_current:
	date = lines[0]['start_date']
	
	num_avail_by_price = [0] * (get_price_ind(max_price_per_person) + 1)
	
	for line in lines:
		price_per_person = line['price'] / line['size'] + get_ticket_offset(line['start_date'])
		num_avail_by_price[get_price_ind(price_per_person)] += line['num_available']
	
	for price_ind in range(len(num_avail_by_price)):
		price_bracket = get_price_bracket(price_ind)
		
		num_available = num_avail_by_price[price_ind]
		max_num_avail = max(num_available, max_num_avail)
		
		num_gone = num_avail_by_date_and_price_first[date][price_ind] - num_available
		num_gone = max(num_gone, 0)
		max_num_gone = max(num_gone, max_num_gone)
		
		if num_available > 0 or num_gone > 0:
			fig1_x.append(date.strftime("%a %d.%m."))
			fig1_y.append(price_bracket)
			fig1_size.append(scale_avail(num_available))
			fig1_color.append(num_gone)



# FIGURE 1: scatterplot with hotness
fig1 = plt.figure()
fig1_plot_title = "Available rooms below " + str(filter_price_per_person) + "€ by date and price per person"
fig1_plot_subtitle = "Circle size shows number of rooms available. All prices include (only) breakfast and are adjusted for higher ticket prices on Fr/Sa."
plt.get_current_fig_manager().set_window_title(window_title)
fig1.suptitle(fig1_plot_title, fontsize=14)
plt.title(fig1_plot_subtitle, fontsize=8)
fig1.subplots_adjust(left=0.07, right=1.1, top=0.9, bottom=0.13)
fig1.set_size_inches(12, 6)
# scatterplot
fig1_axes = plt.gca()
scatter = fig1_axes.scatter(fig1_x, fig1_y, s=fig1_size, c=fig1_color, cmap='summer', vmin=0, vmax=max_num_gone, alpha=1)
fig1_axes.set_ylabel("Price per person (rounded to " + str(price_rounding) + "€)")
fig1_axes.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f €'))
# x-axis and legends
plt.xticks(rotation=45, ha='right')
[tick.set_color('blue' if tick.get_text().startswith('Thu') else 'black') for tick in fig1_axes.xaxis.get_ticklabels()]
# create list of sizes to show in legend
size_legend_labels = [0, 1] + [*range(2, 2 * int(max_num_avail / 2) + 1, 2)]
size_legend_handles = [plt.scatter([],[], s=scale_avail(size_legend_labels[i]), label=size_legend_labels[i], color='gray') for i in range(len(size_legend_labels))]
# create size legend
plt.legend(handles=size_legend_handles, loc='lower right', labelspacing=1.8, borderpad=1.2)
# create color legend
fig1.colorbar(scatter, label="Already booked or price changed", location='right', pad=0.025)



# prepare figure 2
fig2_x = []
fig2_y1 = []
fig2_y2 = []

all_data = parse_all_csv('collected_results')
for data_one_scrape_date, scrape_date in all_data:
	days = set()
	num_avail = 0
	num_different_rooms = 0
	avg_price = 0
	for line in data_one_scrape_date:
		if line['size'] >= 4 and line['meals'] == "Übernachtung - Frühstück":
			days.add(line['start_date'])
			num_avail += line['num_available']
			num_different_rooms += 1
			avg_price += line['price'] / line['size']
	if num_avail > 0:
		fig2_x.append(parse_iso_date(scrape_date))
		fig2_y1.append(num_avail / len(days))
		fig2_y2.append(avg_price / num_different_rooms)

# FIGURE 2: line plots for changes in availability and price
fig2 = plt.figure()
fig2_plot_title = "Available rooms (for 4 or more people) and their prices over time"
fig2_plot_subtitle = "Prices are for rooms which include (only) breakfast."
plt.get_current_fig_manager().set_window_title(window_title)
fig2.suptitle(fig2_plot_title, fontsize=14)
plt.title(fig2_plot_subtitle, fontsize=8)
fig2.subplots_adjust(left=0.06, right=0.94, top=0.9, bottom=0.07)
fig2.set_size_inches(12, 6)
# plot 1 (left y-axis): number of available rooms
fig2_ax1 = plt.gca()
fig2_plot1 = fig2_ax1.plot(fig2_x, fig2_y1, color='blue', marker='o', label='Number of available rooms on each day')
fig2_ax1.set_ylabel('Average of available rooms per day')
fig2_ax1.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
# plot 2 (right y-axis): average price per person
fig2_ax2 = fig2_ax1.twinx()
fig2_plot2 = fig2_ax2.plot(fig2_x, fig2_y2, color='red', marker='o', label='Average price per person')
fig2_ax2.set_ylabel('Average price per person')
fig2_ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f €'))
fig2_ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
# legend and x-axis
plt.legend(handles=[fig2_plot1[0], fig2_plot2[0]], loc='lower center')
fig2_ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
fig2_ax1.xaxis.set_major_formatter(mdates.DateFormatter('%B %Y'))
plt.xticks(rotation=45, ha='right')



plt.show()
