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

from bs4 import BeautifulSoup



def extract_room_data(html):
	soup = BeautifulSoup(html, 'html.parser')
	
	form_rooms = soup.find('form', {'id': 'hbFormRooms'})
#	print(form_rooms.prettify())
	
	if form_rooms is None:
		return []
	
	room_info = []
	
	room_tags = form_rooms.find_all('section', recursive=False)
	
	for room_tag in room_tags:
		# parse room details
		room_description	= room_tag.find('h4', {'class': 'en-room-item__heading en-format-h4 GMS_room_title'}).find(string=True, recursive=False).strip()
		room_meals			= room_tag.find('div', {'class': 'en-room-item__text en-format-meta en-wysiwyg'}).find('p').find(string=True, recursive=False).strip()
		
		room_num_persons	= int(room_tag.find('div', {'class': 'en-room-item__info-value en-format-meta'}).find(string=True, recursive=False).strip())
		
		room_data_tag = room_tag.find('select', {'class': 'gms_rooms'})
		
		room_price			= float(room_data_tag['data-price'].strip())
		
		room_num_avail_list	= room_data_tag.find_all('option', recursive=False)
		room_num_avail		= int(room_num_avail_list[len(room_num_avail_list) - 1]['value'].strip())
		
		room_felix_id		= room_data_tag['data-felix-id'].strip()
		room_package_id		= room_data_tag['data-package-id'].strip()
		room_id				= room_data_tag['data-room-id'].strip()
		room_name_param		= room_data_tag['name'].strip()
		
		room_info.append({
			'description':		room_description,
			'meals':			room_meals,
			'size':				room_num_persons,
			'price':			room_price,
			'num_available':	room_num_avail,
			'felix-id':			room_felix_id,
			'package-id':		room_package_id,
			'room-id':			room_id,
			'name-param':		room_name_param
		})
	
	return room_info
