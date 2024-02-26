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

import urllib.request
import secrets



def get_html_data_method1(num_adults, start_date, end_date):
	# generate session ID
	sid = secrets.token_hex(16)
#	print("SessionID = " + sid)
	
	# assemble URLs
	
	url1 = ('https://jufa.gob5.gms.info/61/de/rooms'
		'?action=get_hotel_rooms'
		'&lang=de'
		'&hotel-id=61'
		'&date-from=' + start_date.isoformat() +
		'&date-to=' + end_date.isoformat() +
		'&rooms%5B0%5D%5Bpeople-count%5D=' + str(num_adults) +
		'&rooms%5B0%5D%5Bchildren-count%5D=0'
		'&rooms%5B0%5D%5Bcot%5D=0'
		'&sid=' + sid)
	
	url2 = ('https://jufa.gob5.gms.info/bregenz/de/roomsdetails'
		'?sid=' + sid)
	
	user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
	headers = {'User-Agent': user_agent}
	
	# Sending HTTP requests
#	print("Sending first request:", url1)
	request2 = urllib.request.Request(url1, None, headers)
	urllib.request.urlopen(request2)
	
#	print("Sending second request:", url2)
	request2 = urllib.request.Request(url2, None, headers)
	page = urllib.request.urlopen(request2)
	
	# Processing HTTP response
	html_bytes = page.read()
	html = html_bytes.decode('utf-8')
	
	return html



def get_html_data_method2(num_adults, start_date, end_date):
	user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
	
	url1 = 'https://jufa-gob14.gms.info/buchen/en/bregenz'
	headers1 = {'User-Agent': user_agent}
	request1 = urllib.request.Request(url1, None, headers1)
	reponse1 = urllib.request.urlopen(request1)
	# Expecting a forward here, get the new URL and extract the uid from it
	forwarded = reponse1.geturl()
	assert forwarded.split('=')[0] == 'https://jufa-gob14.gms.info/buchen/en/bregenz?uid'
	uid = forwarded.split('=')[1]
	assert uid.isdigit() and len(uid) > 0
	# Extract response cookie 'gob65_session'
	gob65_session_cookie = reponse1.getheader('Set-Cookie').split('gob65_session=')[1].split(';')[0]
	assert len(gob65_session_cookie) > 0
	
	url2 = 'https://jufa-gob14.gms.info/bregenz/en/search?uid=' + uid + '&onepage=true'
	headers2 = {
		'User-Agent': user_agent,
		'Cookie': 'gob65_session=' + gob65_session_cookie
	}
	request2 = urllib.request.Request(url2, None, headers2)
	response2 = urllib.request.urlopen(request2).read().decode('utf-8')
	# Extract authenticity tokens from the response
	auth1 = response2.split('<form id="searchForm"')[1].split('<input type="hidden" name="authenticity_token" value="')[1].split('"')[0]
	auth2 = response2.split('<div class="button-wrapper')[1].split('<input type="hidden" name="authenticity_token" id="authenticity_token" value="')[1].split('"')[0]
	assert len(auth1) > 0 and len(auth2) > 0
	
	url3 = 'https://jufa-gob14.gms.info/bregenz/en/search?uid=' + uid
	data3 = (
		'authenticity_token=' + auth1 +
		'&search%5Badults%5D=' + str(num_adults) +
		'&search%5Bchildren%5D=0'
		'&search%5Bchildren_age%5D%5B0%5D=10'
		'&search%5Bchildren_age%5D%5B1%5D=10'
		'&search%5Bchildren_age%5D%5B2%5D=10'
		'&search%5Bchildren_age%5D%5B3%5D=10'
		'&search%5Bchildren_age%5D%5B4%5D=10'
		'&search%5Bchildren_age%5D%5B5%5D=10'
		'&search%5Bchildren_age%5D%5B6%5D=10'
		'&search%5Bchildren_age%5D%5B7%5D=10'
		'&search%5Badults%5D=' + str(num_adults) +
		'&search%5Bkat_id%5D='
		'&search%5Barrangement_id%5D='
		'&search%5Bfilter_id%5D='
		'&search%5Brule_id%5D='
		'&hotel_id=61'
		'&search%5Bdate_from%5D=' + start_date.strftime('%d.%m.%Y') +
		'&search%5Bdate_to%5D=' + end_date.strftime('%d.%m.%Y') +
		'&authenticity_token=' + auth2
	)
	# Encode the data. The supported object types include bytes, file-like objects, and iterables of bytes-like objects.
	data3 = data3.encode('utf-8')
	request3 = urllib.request.Request(url3, data3, headers2)
	urllib.request.urlopen(request3)
	
	url4 = 'https://jufa-gob14.gms.info/bregenz/en/rooms?uid=' + uid
	request4 = urllib.request.Request(url4, None, headers2)
	response4 = urllib.request.urlopen(request4)
	
	# Processing HTTP response
	html_bytes = response4.read()
	html = html_bytes.decode('utf-8')
	
	return html
