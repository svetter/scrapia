import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from dateutil.parser import isoparse as parse_iso_date



filter_price_per_person = 100

window_title = "Room availability analysis – JUFA Hotel Bregenz 2024"
plot_title = "Available rooms below " + str(filter_price_per_person) + ("€ (incl. breakfast)"
				" by date and price per person, adjusted for higher ticket prices on Fr/Sa")

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
	
	for filename in os.listdir(path):
		if filename.endswith('.csv'):
			csv_lines = parse_csv(os.path.join(path, filename))
			result.append(csv_lines[1:])
	
	return result

def parse_first_csv(path):
	files = os.listdir(path)
	return parse_csv(os.path.join(path, files[0]))

def parse_last_csv(path):
	files = os.listdir(path)
	return parse_csv(os.path.join(path, files[len(files)-1]))

def filter_lines(lines):
	result = []
	
	for line in lines:
		price_per_person = line['price'] / line['size']
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



plot_x = []
plot_y = []
plot_size = []
plot_color = []

avail_scaling = 3

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
		
		num_gone = num_avail_by_date_and_price_first[date][price_ind] - num_available
		num_gone = max(num_gone, 0)
		max_num_gone = max(num_gone, max_num_gone)
		
		plot_x.append(date.strftime("%a %d.%m."))
		plot_y.append(price_bracket)
		plot_size.append((num_available * avail_scaling) ** 2 + (10 if (num_available + num_gone > 0) else 0))	# offset size for 0 availability to make num_gone visible
		plot_color.append(num_gone)



plt.rcParams['figure.figsize'] = (12, 6)
plt.get_current_fig_manager().set_window_title(window_title)
plt.title(plot_title)
plt.scatter(plot_x, plot_y, s=plot_size, c=plot_color, cmap='summer', vmin=0, vmax=max_num_gone, alpha=1)
plt.subplots_adjust(left=0.06, right=1.07, top=0.94, bottom=0.15)
plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f €'))
plt.xticks(rotation=45, ha='right')
plt.colorbar(label="Already booked or price changed", location='right', pad=0.025)

plt.show()
