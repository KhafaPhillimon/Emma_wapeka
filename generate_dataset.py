import random
import csv
from datetime import datetime, timedelta

def generate_data():
    random.seed(42)
    
    rows = []
    
    # Mapping of service type to resource endpoint
    services = [
        ('Job Placement', '/jobs/place.php', 0.10),
        ('Job Request - Developer', '/jobs/request.php?type=developer', 0.15),
        ('Job Request - Analyst', '/jobs/request.php?type=analyst', 0.10),
        ('Job Request - Manager', '/jobs/request.php?type=manager', 0.05),
        ('Schedule Demo', '/scheduledemo.php', 0.15),
        ('Promotional Event', '/event.php', 0.10),
        ('AI Assistant', '/ai_assistant.php', 0.20),
        ('Prototype', '/prototype.php', 0.05),
        ('General', '/index.html', 0.05),
        ('General', '/images/events.jpg', 0.05)
    ]
    
    req_types = ['GET', 'POST']
    req_weights = [0.80, 0.20]
    
    status_codes = [200, 304, 404, 500]
    status_weights = [0.75, 0.15, 0.08, 0.02]
    
    countries = ['Botswana', 'South Africa', 'United States', 'United Kingdom', 'India']
    country_weights = [0.40, 0.20, 0.20, 0.10, 0.10]
    
    start_time = datetime(2023, 10, 1, 0, 0, 0)
    total_seconds = 30 * 24 * 60 * 60 # 30 days of data
    
    for i in range(1, 10001):
        ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
        rand_sec = random.randint(0, total_seconds)
        ts = start_time + timedelta(seconds=rand_sec)
        
        rtype = random.choices(req_types, weights=req_weights)[0]
        
        # Select service
        service_choice = random.choices(services, weights=[s[2] for s in services])[0]
        stype = service_choice[0]
        resource = service_choice[1]
        
        status = random.choices(status_codes, weights=status_weights)[0]
        country = random.choices(countries, weights=country_weights)[0]
        
        if status in [200, 304]:
            rt = random.randint(20, 300)
        elif status == 404:
            rt = random.randint(50, 400)
        else:
            rt = random.randint(200, 1000)
            
        fs = random.randint(10, 5000) # File size in KB
        
        row = {
            'request_id': 0,
            'ip_address': ip,
            'timestamp': ts.strftime("%Y-%m-%d %H:%M:%S"),
            'request_type': rtype,
            'requested_resource': resource,
            'status_code': status,
            'service_type': stype,
            'country': country,
            'response_time': rt,
            'file_size': fs
        }
        rows.append(row)
        
    rows.sort(key=lambda x: x['timestamp'])
    
    for idx, row in enumerate(rows):
        row['request_id'] = idx + 1

    with open('dataset.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'request_id', 'ip_address', 'timestamp', 'request_type', 
            'requested_resource', 'status_code', 'service_type', 
            'country', 'response_time', 'file_size'
        ])
        writer.writeheader()
        writer.writerows(rows)

if __name__ == '__main__':
    generate_data()
