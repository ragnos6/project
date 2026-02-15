import re
import csv
import json
from datetime import datetime

input_file = "requests.log"
output_file = "logs.csv"

pattern = r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) (\S+) "(\w+) (\S+) (HTTP/\d\.\d)" (\d+) (\d+\.\d+) (\d+) (\d+\.\d+) "(.+)"'

with open(input_file, 'r') as f_in, open(output_file, 'w', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(['Date', 'Time', 'IP', 'Method', 'Path', 'Protocol', 'Status', 
                     'TotalTime', 'SQLCount', 'SQLTime', 'Params', 'ParamKeys'])

    for line in f_in:
        match = re.match(pattern, line)
        if match:
            try:
                params_str = match.group(11)
                params = json.loads(params_str.replace("'", '"')) if params_str != "{}" else {}
 
                writer.writerow([
                    match.group(1),  # Date
                    match.group(2),  # Time
                    match.group(3),  # IP
                    match.group(4),  # Method
                    match.group(5),  # Path
                    match.group(6),  # Protocol
                    int(match.group(7)),  # Status
                    float(match.group(8)),  # TotalTime
                    int(match.group(9)),  # SQLCount
                    float(match.group(10)),  # SQLTime
                    params_str,
                    ";".join(params.keys()) if params else ""
                ])
            except Exception as e:
                print(f"Error processing line: {line.strip()} | Error: {str(e)}")
