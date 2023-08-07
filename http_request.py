import urllib.request
import secrets



def get_html_data(num_adults, start_date, end_date):
	# generate session ID
	sid = secrets.token_hex(16)
	#print("SessionID = " + sid)
	
	# assemble URLs
	
	url1 = ('https://jufa.gob5.gms.info/61/de/rooms'
			'?action=get_hotel_rooms'
			'&lang=de'
			'&hotel-id=61'
			'&date-from=' + start_date +
			'&date-to=' + end_date +
			'&rooms%5B0%5D%5Bpeople-count%5D=' + str(num_adults) +
			'&rooms%5B0%5D%5Bchildren-count%5D=0'
			'&rooms%5B0%5D%5Bcot%5D=0'
			'&sid=' + sid)
	
	url2 = ('https://jufa.gob5.gms.info/bregenz/de/roomsdetails'
			'?sid=' + sid)
	
	user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
	headers = {'User-Agent': user_agent}
	
	# Sending HTTP requests
	#print("Sending first request:", url1)
	request2 = urllib.request.Request(url1, None, headers)
	urllib.request.urlopen(request2)
	
	#print("Sending second request:", url2)
	request2 = urllib.request.Request(url2, None, headers)
	page = urllib.request.urlopen(request2)
	
	# Processing HTTP response
	html_bytes = page.read()
	html = html_bytes.decode('utf-8')
	
	return html
