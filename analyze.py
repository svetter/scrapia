# Copyright 2023 Simon Vetter
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

import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap

from constants import STAY_DATES
from helpers.csv_parse import parse_all_csv
from helpers.preprocess import process_all_data



# settings for filtering by price per person
filter_price_per_person = 100

# setting for rounding prices in main figure
price_rounding = 5

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

# setting for keeping tooltips centered to circle
keep_tooltips_centered_to_circle = False



# parse all CSV data and process it
all_data = parse_all_csv('collected_results')

first_scrape_date	= all_data[ 0][1]
last_scrape_date	= all_data[-1][1]



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



# preprocess data
processed_data = process_all_data(all_data, num_price_brackets, num_price_brackets_filtered, get_price_bracket_ind, get_ticket_offset, meal_filter)



def scale_avail(num_available, corr_factor=1.0):
	return (10 + (num_available * 10) + (num_available ** 1.6 * 25)) * corr_factor



# custom colormaps

colormap_urgency = LinearSegmentedColormap.from_list('urgency', ['green', 'orange', 'red'])
colormap_price = LinearSegmentedColormap.from_list('price', ['blue', 'red'])
mpl.colormaps.register(cmap=colormap_urgency)
mpl.colormaps.register(cmap=colormap_price)



# tooltips

def get_tooltip_text(start_date, price_bracket):
	bracket_ind = get_price_bracket_ind(price_bracket)
	
	rooms = []
	col_widths = [0, 0, 0, 0]
	for room in processed_data[last_scrape_date]['data'][start_date]['room_data']:
		price_per_person = room['price'] / room['size'] + get_ticket_offset(room['start_date'])
		if get_price_bracket_ind(price_per_person) == bracket_ind and meal_filter[room['meals']]:
			rooms.append((
				str(room['num_available']),
				room['description'].removesuffix("Zimmer").strip(),
				str(room['size']),
				'{:.0f}'.format(room['price'])
			))
			for i in range(len(col_widths)):
				col_widths[i] = max(col_widths[i], len(rooms[-1][i]))
	
	room_strings = []
	for room_line in rooms:
		col0 = ('{: <' + str(col_widths[0]) + '}').format(room_line[0])
		col1 = ('{: <' + str(col_widths[1]) + '}').format(room_line[1])
		col2 = ('{: <' + str(col_widths[2]) + '}').format(room_line[2])
		col3 = ('{: >' + str(col_widths[3]) + '}').format(room_line[3])
		room_strings.append('{}x {} ({} people):  {} €'.format(col0, col1, col2, col3))
	
	result = '\n'.join(room_strings)
	
	# find number of rooms already booked or price changed
	num_gone = processed_data[last_scrape_date]['data'][start_date]['num_gone_by_price_bracket'][bracket_ind]
	
	if num_gone > 0:
		if result != '':
			result += '\n\n'
		result += str(num_gone) + ' rooms already booked or price changed'
	
	return result

def motion_hover(event):
	if event.inaxes != fig1_axes:
		return
	is_contained, annot_ind = fig1_plot.contains(event)
	if not is_contained:
		if fig1_annotation.get_visible():
			fig1_annotation.set_visible(False)
			fig1.canvas.draw_idle()
		return
	
	location = fig1_plot.get_offsets()[annot_ind['ind'][0]]
	hover_date = STAY_DATES[int(location[0])][0]
	hover_price_bracket = int(location[1])
	# assemble tooltip text
	tooltip_text = get_tooltip_text(hover_date, hover_price_bracket)
	if tooltip_text is None:
		return
	fig1_annotation.set_text(tooltip_text)
	fig1.canvas.draw_idle()
	# set pointer position (mouse or circle center)
	(x_point, y_point) = location if keep_tooltips_centered_to_circle else (event.xdata, event.ydata)
	fig1_annotation.xy = (x_point, y_point)
	# reposition tooltip relative to pointer
	x_frac = (x_point     - fig1_axes.get_xlim()[0]) / (fig1_axes.get_xlim()[1] - fig1_axes.get_xlim()[0])
	y_frac = (location[1] - fig1_axes.get_ylim()[0]) / (fig1_axes.get_ylim()[1] - fig1_axes.get_ylim()[0])	# y: always use circle center to avoid snapping up/down inside circle
	annot_width = fig1_annotation.get_window_extent(fig1.canvas.get_renderer()).width * 72 / fig1.dpi
	annot_height = fig1_annotation.get_window_extent(fig1.canvas.get_renderer()).height * 72 / fig1.dpi
	x_offset = -(annot_width / 2) + (annot_width * (0.5 - x_frac)) * 0.95	# keep centered, move away from edge
	y_offset = 30 if y_frac < 0.5 else -30 - annot_height
	fig1_annotation.xyann = (x_offset, y_offset)
	fig1_annotation.set_visible(True)



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
		num_gone		= data_one_start_date[ 'num_gone_by_price_bracket'][price_bracket_ind]
		
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
fig1_plot = fig1_axes.scatter(fig1_x, fig1_y, s=fig1_size, c=fig1_color, cmap='urgency', vmin=0, vmax=fig1_max_color, alpha=1)
fig1_axes.set_ylabel("Price per person (rounded to " + str(price_rounding) + "€)")
fig1_axes.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f €'))
# x-axis and legends
plt.xticks(rotation=45, ha='right')
[tick.set_color('blue' if tick.get_text().startswith('Thu') else 'black') for tick in fig1_axes.xaxis.get_ticklabels()]
# create list of sizes to show in legend
fig1_size_legend_labels = [0, 1] + [*range(2, 2 * int(fig1_max_size / 2) + 1, 2)]
fig1_size_legend_handles = [plt.scatter([],[], s=scale_avail(fig1_size_legend_labels[i]), label=fig1_size_legend_labels[i], color='gray') for i in range(len(fig1_size_legend_labels))]
# create size legend
plt.legend(handles=fig1_size_legend_handles, loc='lower right', labelspacing=1.8, borderpad=1.2)
# create color legend
fig1.colorbar(fig1_plot, label="Already booked or price changed", location='right', pad=0.025)
# format status bar coordinates
fig1_axes.format_coord = lambda x, y: (
	('' if round(x) < 0 or round(x) >= len(STAY_DATES) else ('Stay date: ' + STAY_DATES[round(x)][0].strftime("%d.%m.%Y") + ', '))
	+ 'Price/person: ' + str(round(y)) + ' €'
)
# add and connect tooltip
fig1_annotation = fig1_axes.annotate(text='', fontfamily='monospace', xy=(0, 0), xytext=(0, 0), textcoords='offset points', bbox=dict(boxstyle='square', fc='w'), zorder=10)
fig1_annotation.set_visible(False)
fig1.canvas.mpl_connect('motion_notify_event', motion_hover)



# prepare figure 2
fig2_x	= []
fig2_y1	= []
fig2_y2	= []
fig2_y3	= []
fig2_y4	= []

for data_one_scrape_date, scrape_date in all_data:
	num_avail = 0
	num_different_rooms = 0
	min_price = max_price_per_person
	avg_price = 0
	max_price = 0
	for line in data_one_scrape_date:
		if line['size'] >= 4 and meal_filter[line['meals']]:
			num_avail += line['num_available']
			num_different_rooms += 1
			price_per_person = line['price'] / line['size']
			min_price = min(min_price, price_per_person)
			avg_price += price_per_person
			max_price = max(max_price, price_per_person)
	num_avail /= len(STAY_DATES)
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
fig2_plot1 = fig2_ax1.plot(fig2_x, fig2_y1, color='black', marker='o', label='Average number of available rooms per day')
fig2_ax1.set_ylabel('Average of available rooms per day')
fig2_ax1.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
# plot 2-4 (right y-axis): minimum/average/maximum price per person
fig2_ax2 = fig2_ax1.twinx()
fig2_plot2 = fig2_ax2.plot(fig2_x, fig2_y2, color='blue',   marker='v', label='Minimum price per person')
fig2_plot3 = fig2_ax2.plot(fig2_x, fig2_y3, color='purple', marker='D', label='Average price per person')
fig2_plot4 = fig2_ax2.plot(fig2_x, fig2_y4, color='red',    marker='^', label='Maximum price per person')
fig2_ax2.set_ylabel('Price per person')
fig2_ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f €'))
fig2_ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
# legend and x-axis
plt.legend(handles=[fig2_plot1[0], fig2_plot4[0], fig2_plot3[0], fig2_plot2[0]], loc='lower center')
fig2_ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
fig2_ax1.xaxis.set_major_formatter(mdates.DateFormatter('%B %Y'))
plt.xticks(rotation=45, ha='right')
# format status bar coordinates
fig2_ax2.format_coord = lambda x, y: 'Scrape date: ' + mdates.num2date(x).strftime("%d.%m.%Y") + ', ' + 'Price/person: ' + str(round(y)) + ' €'



# prepare figure 3
fig3_x		= []
fig3_y		= []
fig3_size	= []
fig3_color	= []
fig3_max_size = 0
fig3_min_color = max_price_per_person
fig3_max_color = 0
fig3_marker_scale = 0.6

for _, (scrape_date, data_one_scrape_date) in enumerate(processed_data.items()):
	for _, (start_date, data_one_start_date) in enumerate(data_one_scrape_date['data'].items()):
		num_available = 0
		avg_price = 0
		num_different_rooms = 0
		for room in data_one_start_date['room_data']:
			if room['size'] >= 4 and meal_filter[room['meals']]:
				num_available += room['num_available']
				avg_price += room['price'] / room['size']
				num_different_rooms += 1
		avg_price /= num_different_rooms if num_different_rooms > 0 else 1
		
		if num_available > 0:
			fig3_x.append(start_date.strftime("%a %d.%m."))
			fig3_y.append(scrape_date)
			fig3_size.append(scale_avail(num_available, fig3_marker_scale))
			fig3_color.append(avg_price)
			
			fig3_max_size	= max(fig3_max_size, num_available)
			fig3_min_color	= min(fig3_min_color, avg_price)
			fig3_max_color	= max(fig3_max_color, avg_price)

# FIGURE 3: scatterplot of availability and prices over time
fig3 = plt.figure()
fig3_plot_title = "Available rooms for 4 or more people and their average price over time"
fig3_plot_subtitle = "Circle size shows number of rooms available. Prices are for room options which include (only) breakfast."
plt.get_current_fig_manager().set_window_title(window_title)
fig3.suptitle(fig3_plot_title, fontsize=14)
plt.title(fig3_plot_subtitle, fontsize=8)
fig3.subplots_adjust(left=0.07, right=1.07, top=0.9, bottom=0.14)
fig3.set_size_inches(12, 6)
fig3_ax = plt.gca()
fig3_plot = fig3_ax.scatter(fig3_x, fig3_y, s=fig3_size, c=fig3_color, cmap='price', vmin=fig3_min_color, vmax=fig3_max_color, alpha=1)
fig3_ax.invert_yaxis()
fig3_ax.yaxis.set_major_locator(mdates.MonthLocator(interval=1))
fig3_ax.yaxis.set_major_formatter(mdates.DateFormatter('%m.%Y'))
# x-axis and legends
plt.xticks(rotation=45, ha='right')
[tick.set_color('blue' if tick.get_text().startswith('Thu') else 'black') for tick in fig3_ax.xaxis.get_ticklabels()]
# create list of sizes to show in legend
fig3_size_legend_labels = [*range(2, 2 * int(fig3_max_size / 2) + 1, 2)]
fig3_size_legend_handles = [plt.scatter([], [], s=scale_avail(fig3_size_legend_labels[i], fig3_marker_scale), label=fig3_size_legend_labels[i], color='gray') for i in range(len(fig3_size_legend_labels))]
# create size legend
plt.legend(handles=fig3_size_legend_handles, loc='lower right', labelspacing=1.8, borderpad=1.2)
# create color legend
fig1.colorbar(fig3_plot, label="Average price", location='right', pad=0.025, format='%.0f €')
# format status bar coordinates
fig3_ax.format_coord = lambda x, y: (
	('' if round(x) < 0 or round(x) >= len(STAY_DATES) else ('Stay date: ' + STAY_DATES[round(x)][0].strftime("%d.%m.%Y") + ', '))
	+ 'Scrape date: ' + mdates.num2date(y).strftime("%d.%m.%Y")
)



plt.show()
