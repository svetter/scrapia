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

import locale
import math

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import LinearSegmentedColormap

from python.constants import STAY_DATES_2025 as STAY_DATES
from python.constants import ticket_price_offset_2025_fr as ticket_price_offset_fr
from python.constants import ticket_price_offset_2025_sa as ticket_price_offset_sa
from python.csv_parse import parse_all_csv
from python.preprocess import process_all_data



# settings for filtering by price per person
filter_price_per_person = 100

# setting for rounding prices in main figure
price_rounding = 5

# settings for filtering rooms by meal options (True = include)
meal_filter = {
	'Übernachtung ohne Frühstück':		False,
	'Übernachtung - Frühstück':			True,
	'Übernachtung Frühstück NonFlex':	True,
	'Übernachtung - Halbpension':		True,
	'Kultur & Natur in Bregenz':		True,
	'Overnight stay without breakfast':	False,
	'Overnight breakfast':				True,
	'Non refundable Bed & Breakfast':	True,
	'Overnight half board':				True,
}

# setting for keeping tooltips centered to circle
keep_tooltips_centered_to_circle = False



# set locale to English to ensure consistent date formatting
# call matplotlib first because it will set the locale to the system default
plt.plot()
plt.close()
locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')



# parse all CSV data and process it
data_year = STAY_DATES[0][0].year
results_dir = 'collected_results/' + str(data_year)
all_data = parse_all_csv(results_dir)
if len(all_data) == 0:
	print("No data found for " + str(data_year) + ".")
	exit()

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
num_price_brackets_filtered	= min(math.ceil(filter_price_per_person / price_rounding) + 1, num_price_brackets)



# preprocess data
processed_data = process_all_data(STAY_DATES, all_data, num_price_brackets, num_price_brackets_filtered, get_price_bracket_ind, get_ticket_offset, meal_filter)



def scale_avail(num_available, corr_factor=1.0):
	return (10 + (num_available * 10) + (num_available ** 1.6 * 25)) * corr_factor



# custom colormaps

colormap_urgency = LinearSegmentedColormap.from_list('urgency', ['green', 'orange', 'red'])
colormap_price = LinearSegmentedColormap.from_list('price', ['blue', 'red'])
mpl.colormaps.register(cmap=colormap_urgency)
mpl.colormaps.register(cmap=colormap_price)



# tooltips

def get_get_tooltip_text(y_is_scrape_date_not_price):
	def get_tooltip_text(x, y):
		start_date = STAY_DATES[x][0]
		if y_is_scrape_date_not_price:
			scrape_date = mdates.num2date(y).date()
		else:
			scrape_date = last_scrape_date
			price_bracket = y
			bracket_ind = get_price_bracket_ind(price_bracket)
		
		rooms = []
		col_widths = [0, 0, 0, 0]
		for room in processed_data[scrape_date]['data'][start_date]['room_data']:
			price_per_person = room['price'] / room['size'] + get_ticket_offset(room['start_date'])
			
			if y_is_scrape_date_not_price:
				condition_met = room['size'] >= 4
			else:
				condition_met = get_price_bracket_ind(price_per_person) == bracket_ind
			
			if condition_met and meal_filter[room['meals']]:
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
		if not y_is_scrape_date_not_price:
			num_gone = processed_data[scrape_date]['data'][start_date]['num_gone_by_price_bracket'][bracket_ind]
		else:
			num_available = 0
			for room in processed_data[scrape_date]['data'][start_date]['room_data']:
				if room['size'] >= 4 and meal_filter[room['meals']]:
					num_available += room['num_available']
			num_gone = 0
			for room in processed_data[first_scrape_date]['data'][start_date]['room_data']:
				if room['size'] >= 4 and meal_filter[room['meals']]:
					num_gone += room['num_available']
			num_gone = max(0, num_gone - num_available)
		
		if num_gone > 0:
			if result != '':
				result += '\n\n'
			result += str(num_gone) + ' rooms already booked or price changed'
		
		return result
	return get_tooltip_text

def get_motion_hover(fig, plot, ax, annot, get_tooltip_text):
	def motion_hover(event):
		if event.inaxes != ax:
			return
		is_contained, annot_ind = plot.contains(event)
		if not is_contained:
			if annot.get_visible():
				annot.set_visible(False)
				fig.canvas.draw_idle()
			return
		
		location = plot.get_offsets()[annot_ind['ind'][0]]
		# assemble tooltip text
		tooltip_text = get_tooltip_text(int(location[0]), int(location[1]))
		if tooltip_text is None:
			return
		annot.set_text(tooltip_text)
		fig.canvas.draw_idle()
		# set pointer position (mouse or circle center)
		(x_point, y_point) = location if keep_tooltips_centered_to_circle else (event.xdata, event.ydata)
		annot.xy = (x_point, y_point)
		# reposition tooltip relative to pointer
		x_frac = (x_point - ax.get_xlim()[0]) / (ax.get_xlim()[1] - ax.get_xlim()[0])
		y_frac = (location[1] - ax.get_ylim()[0]) / (ax.get_ylim()[1] - ax.get_ylim()[
			0])  # y: always use circle center to avoid snapping up/down inside circle
		annot_width = annot.get_window_extent(fig.canvas.get_renderer()).width * 72 / fig.dpi
		annot_height = annot.get_window_extent(fig.canvas.get_renderer()).height * 72 / fig.dpi
		x_offset = -(annot_width / 2) + (annot_width * (0.5 - x_frac)) * 0.95  # keep centered, move away from edge
		y_offset = 30 if y_frac < 0.5 else -30 - annot_height
		annot.xyann = (x_offset, y_offset)
		annot.set_visible(True)
	return motion_hover



# prepare figure 1
fig1_x		= []
fig1_y		= []
fig1_size	= []
fig1_color	= []
fig1_max_size	= processed_data[last_scrape_date]['max_num_avail_filtered']
fig1_max_color	= processed_data[last_scrape_date]['max_num_gone_filtered']

for _, (start_date, data_one_start_date) in enumerate(processed_data[last_scrape_date]['data'].items()):
	# add invisible point to ensure all x-axis ticks are shown
	fig1_x.append(start_date.strftime("%a %d.%m."))
	fig1_y.append(filter_price_per_person)
	fig1_size.append(0)
	fig1_color.append(0)
	
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
window_title = "Room availability analysis – JUFA Hotel Bregenz " + str(data_year)
fig1_plot_title = "Available rooms below " + str(filter_price_per_person) + "€ per person by date and price"
fig1_plot_subtitle = "Circle size shows number of rooms available. Prices are for cheapest option which includes breakfast, and are adjusted for higher ticket prices on Fr/Sa."
plt.get_current_fig_manager().set_window_title(window_title)
fig1.suptitle(fig1_plot_title, fontsize=14)
plt.title(fig1_plot_subtitle, fontsize=8)
fig1.subplots_adjust(left=0.07, right=1.09, top=0.9, bottom=0.14)
fig1.set_size_inches(12, 6)
# scatterplot
fig1_ax = plt.gca()
fig1_plot = fig1_ax.scatter(fig1_x, fig1_y, s=fig1_size, c=fig1_color, cmap='urgency', vmin=0, vmax=fig1_max_color, alpha=1)
fig1_ax.set_ylabel("Price per person (rounded to " + str(price_rounding) + "€)")
fig1_ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f €'))
# x-axis and legends
plt.xticks(rotation=45, ha='right')
# create list of sizes to show in legend
fig1_size_legend_labels = [0, 1] + [*range(2, 2 * int(fig1_max_size / 2) + 1, 2)]
fig1_size_legend_handles = [plt.scatter([], [], s=scale_avail(fig1_size_legend_labels[i]), label=fig1_size_legend_labels[i], color='gray') for i in range(len(fig1_size_legend_labels))]
# create size legend
plt.legend(handles=fig1_size_legend_handles, loc='lower right', labelspacing=1.8, borderpad=1.2)
# create color legend
fig1_colorbar = fig1.colorbar(fig1_plot, label="Already booked or price changed", location='right', pad=0.025)
fig1_colorbar.ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
# format status bar coordinates
fig1_ax.format_coord = lambda x, y: (
	('' if round(x) < 0 or round(x) >= len(STAY_DATES) else ('Stay date: ' + STAY_DATES[round(x)][0].strftime("%d.%m.%Y") + ', '))
	+ 'Price/person: ' + str(round(y)) + ' €'
)
# add and connect tooltip
fig1_annotation = fig1_ax.annotate(text='', fontfamily='monospace', xy=(0, 0), xytext=(0, 0), textcoords='offset points', bbox=dict(boxstyle='square', fc='w'), zorder=10)
fig1_annotation.set_visible(False)
fig1_get_tooltip_text = get_get_tooltip_text(False)
fig1_motion_hover = get_motion_hover(fig1, fig1_plot, fig1_ax, fig1_annotation, fig1_get_tooltip_text)
fig1.canvas.mpl_connect('motion_notify_event', fig1_motion_hover)



# prepare figure 2
fig2_x	= []
fig2_y1	= []
fig2_y2	= []
fig2_y3	= []
fig2_y4	= []

for scrape_date, data_one_scrape_date in processed_data.items():
	num_available_rooms = 0
	min_price = max_price_per_person
	avg_price = 0
	max_price = 0
	
	for data_one_start_date in data_one_scrape_date['data'].values():
		for line in data_one_start_date['room_data']:
			if line['size'] < 4:
				continue
			
			num_available_rooms += line['num_available']
			price_per_person = line['price'] / line['size']
			min_price = min(min_price, price_per_person)
			avg_price += price_per_person * line['num_available']
			max_price = max(max_price, price_per_person)
	if num_available_rooms > 0:
		avg_price /= num_available_rooms
	avg_num_available_rooms = num_available_rooms / len(STAY_DATES)
	
	fig2_x.append(scrape_date)
	fig2_y1.append(avg_num_available_rooms)
	if num_available_rooms > 0:
		fig2_y2.append(min_price)
		fig2_y3.append(avg_price)
		fig2_y4.append(max_price)
	else:
		fig2_y2.append(fig2_y2[len(fig2_y2) - 1])
		fig2_y3.append(fig2_y3[len(fig2_y3) - 1])
		fig2_y4.append(fig2_y4[len(fig2_y4) - 1])

# FIGURE 2: line plots for changes in availability and price
fig2 = plt.figure()
fig2_plot_title = "Available rooms for 4 or more people and their prices over time"
fig2_plot_subtitle = "Prices are for cheapest option which includes breakfast."
plt.get_current_fig_manager().set_window_title(window_title)
fig2.suptitle(fig2_plot_title, fontsize=14)
plt.title(fig2_plot_subtitle, fontsize=8)
fig2.subplots_adjust(left=0.05, right=0.94, top=0.9, bottom=0.07)
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
plt.legend(handles=[fig2_plot1[0], fig2_plot4[0], fig2_plot3[0], fig2_plot2[0]], loc='upper right')
fig2_ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
fig2_ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.xticks(rotation=45, ha='right')
# format status bar coordinates
fig2_ax2.format_coord = lambda x, y: 'Scrape date: ' + mdates.num2date(x).strftime("%d.%m.%Y") + ', ' + 'Price/person: ' + str(round(y)) + ' €'



# prepare figure 3
fig3_x		= []
fig3_y		= []
fig3_size	= []
fig3_color	= []
fig3_max_size = 0
fig3_min_color = 0
fig3_max_color = 1
fig3_marker_scale = 0.6

for _, (scrape_date, data_one_scrape_date) in enumerate(processed_data.items()):
	for _, (start_date, data_one_start_date) in enumerate(data_one_scrape_date['data'].items()):
		if scrape_date == first_scrape_date:
			# add invisible point to ensure all x-axis ticks are shown
			fig3_x.append(start_date.strftime("%a %d.%m."))
			fig3_y.append(first_scrape_date)
			fig3_size.append(0)
			fig3_color.append(0)
		
		num_available = 0
		for room in data_one_start_date['room_data']:
			if room['size'] >= 4 and meal_filter[room['meals']]:
				num_available += room['num_available']
		num_gone = 0
		for room in processed_data[first_scrape_date]['data'][start_date]['room_data']:
			if room['size'] >= 4 and meal_filter[room['meals']]:
				num_gone += room['num_available']
		num_gone = max(0, num_gone - num_available)
		
		if num_available > 0:
			fig3_x.append(start_date.strftime("%a %d.%m."))
			fig3_y.append(scrape_date)
			fig3_size.append(scale_avail(num_available, fig3_marker_scale))
			fig3_color.append(num_gone)
			
			fig3_max_size	= max(fig3_max_size, num_available)
			fig3_max_color	= max(fig3_max_color, num_gone)

# FIGURE 3: scatterplot of availability over time
fig3 = plt.figure()
fig3_plot_title = "Available rooms for 4 or more people over time"
fig3_plot_subtitle = "Circle size shows number of rooms available."
plt.get_current_fig_manager().set_window_title(window_title)
fig3.suptitle(fig3_plot_title, fontsize=14)
plt.title(fig3_plot_subtitle, fontsize=8)
fig3.subplots_adjust(left=0.07, right=1.09, top=0.9, bottom=0.14)
fig3.set_size_inches(12, 6)
fig3_ax = plt.gca()
fig3_plot = fig3_ax.scatter(fig3_x, fig3_y, s=fig3_size, c=fig3_color, cmap='price', vmin=fig3_min_color, vmax=fig3_max_color, alpha=1)
fig3_ax.invert_yaxis()
fig3_ax.yaxis.set_major_locator(mdates.MonthLocator(interval=1))
fig3_ax.yaxis.set_major_formatter(mdates.DateFormatter('%m.%Y'))
# x-axis and legends
plt.xticks(rotation=45, ha='right')
# create list of sizes to show in legend
fig3_size_legend_labels = [*range(2, 2 * int(fig3_max_size / 2) + 1, 2)]
fig3_size_legend_handles = [plt.scatter([], [], s=scale_avail(fig3_size_legend_labels[i], fig3_marker_scale), label=fig3_size_legend_labels[i], color='gray') for i in range(len(fig3_size_legend_labels))]
# create size legend
plt.legend(handles=fig3_size_legend_handles, loc='lower right', labelspacing=1.8, borderpad=1.2)
# create color legend
fig3_colorbar = fig3.colorbar(fig3_plot, label="Already booked", location='right', pad=0.025)
fig3_colorbar.ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
# format status bar coordinates
fig3_ax.format_coord = lambda x, y: (
	('' if round(x) < 0 or round(x) >= len(STAY_DATES) else ('Stay date: ' + STAY_DATES[round(x)][0].strftime("%d.%m.%Y") + ', '))
	+ 'Scrape date: ' + mdates.num2date(y).strftime("%d.%m.%Y")
)
# add and connect tooltip
fig3_annotation = fig3_ax.annotate(text='', fontfamily='monospace', xy=(0, 0), xytext=(0, 0), textcoords='offset points', bbox=dict(boxstyle='square', fc='w'), zorder=10)
fig3_annotation.set_visible(False)
fig3_get_tooltip_text = get_get_tooltip_text(True)
fig3_motion_hover = get_motion_hover(fig3, fig3_plot, fig3_ax, fig3_annotation, fig3_get_tooltip_text)
fig3.canvas.mpl_connect('motion_notify_event', fig3_motion_hover)



plt.show()
