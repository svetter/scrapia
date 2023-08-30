import os
from dateutil.parser import isoparse as parse_iso_date



csv_sep = ','



def parse_csv(filepath):
	result = []
	
	with open(filepath, 'r', encoding='UTF-8') as f:
		lines = f.read().split('\n')[1:]
	
	for line in lines:
		if line == '':
			continue
		
		values = line.split(csv_sep)
		
		start_date		= parse_iso_date(values[0]).date()
		end_date		= parse_iso_date(values[1]).date()
		description		= values[2]
		num_persons		= int(values[3])
		meals			= values[4]
		price			= float(values[5][:-1])
		num_avail		= int(values[6])
		felix_id		= values[7]
		package_id		= values[8]
		room_id			= values[9]
		name_param		= values[10]
		scraped_date	= parse_iso_date(values[11]).date()
		
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
			result.append((csv_lines[1:], parse_iso_date(filename[:-4]).date()))
	
	return result
