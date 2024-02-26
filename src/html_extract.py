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

from bs4 import BeautifulSoup



def extract_room_data(html_method1, html_method2):
	soup2 = BeautifulSoup(html_method2, 'html.parser')
	rooms_section = soup2.find('section', {'class': 'rooms-main'})
	if rooms_section is None:
		return []
	
	room_groups = rooms_section.find_all('div', {'class': 'room-cell'}, recursive=False)
#	print(room_groups.prettify())
	
	room_info = []
	
	# Step 1: Parse room details using method2 data
	
	for room_group in room_groups:
		# parse room details
		room_description	= room_group.find('div', {'class': 'room-title py-2'}).find('h4').find(string=True, recursive=False).strip()
		
		room_variants = room_group.find('tbody').find_all('tr', recursive=False)
		
		for room_variant in room_variants:
			book_button = room_variant.find('button', {'class': 'book-button selectRoomBtn'})
			
			room_num_persons	= int(book_button['data-room-maxperson'].strip())

			room_meals			= book_button['data-package-name'].strip()
			
			room_price			= float(book_button['data-price'].strip())

			room_name_param		= book_button['name'].strip()
			room_felix_id		= book_button['data-room-id'].strip()
			room_package_id		= room_name_param.split('-')[2]
			
			room_info.append({
				'description':		room_description,
				'meals':			room_meals,
				'size':				room_num_persons,
				'price':			room_price,
				'num_available':	-1,
				'felix-id':			room_felix_id,
				'package-id':		room_package_id,
				'room-id':			'',
				'name-param':		room_name_param
			})
	
	# Step 2: Find number of available rooms using method1 data
	
	soup1 = BeautifulSoup(html_method1, 'html.parser')
	form_rooms = soup1.find('form', {'id': 'hbFormRooms'})
#	print(form_rooms.prettify())
	
	if form_rooms is None:
		print(html_method1)
		return []
	
	room_tags = form_rooms.find_all('section', recursive=False)
	
	for room_tag in room_tags:
		room_data_tag = room_tag.find('select', {'class': 'gms_rooms'})
		
		room_num_avail_list = room_data_tag.find_all('option', recursive=False)
		room_num_avail = int(room_num_avail_list[len(room_num_avail_list) - 1]['value'].strip())
		
		room_felix_id = room_data_tag['data-felix-id'].strip()
		
		# In room_info, find the room with the matching name_param and set the number available and room-id
		foundMatch = False
		for room in room_info:
			if room['felix-id'] == room_felix_id:
				room['num_available'] = room_num_avail
				foundMatch = True
		if not foundMatch:
			print("Warning: No matching room found from method1 for room " + room_felix_id)
	
	for room in room_info:
		if room['num_available'] == -1:
			print("Warning: No availability data found for room with name-param " + room['name-param'])
			room['num_available'] = 0
	
	return room_info
