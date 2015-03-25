import logging
import time
import sys
import re

# Dictionary from addresses to lists of locations and times
# format: address : [[location1, [time1, time2], [time1, time2], ...], ...]
addr_loc_time = {}
# Dictionary of addresses and their human friendly name if it exists
# Note: Addresses with no name will not be in here
addr_name = {}

# Check if there is a debug flag
# Current support for --string_format=epoch/asctime
# TODO: Debug output flag
str_frmt = True
for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    if '--string_format=' in arg:
        arg = arg.split('=')
        if arg[1] == "epoch" or arg[1] == "Epoch" or arg[1] == "EPOCH":
            str_frmt = False
        elif arg[1] != "asctime" and arg[1] != "Asctime" and \
                arg[1] != "AscTime" and arg[1] != "ASCTIME":
            logging.warning("string_format option: '"+arg[1]+"' not" +
                            " supported. Defaulting to asctime")
    if '--debug=' in arg:
        arg = arg.split('=')
        if arg[1] == 'true' or arg[1] == 'True' or arg[1] == 't' or \
                arg[1] == 'T':
            logging.basicConfig(level=logging.DEBUG)
        elif arg[1] != 'false' and arg[1] != 'False' and arg[1] != 'f' and \
                arg[1] != 'F':
            logging.warning("debug option: '"+arg[1]+"' not" +
                            "supported. Defaulting to false")

num_files = len(sys.argv) - 1
for cur_file_num in range(num_files):
    # Get file name from the system args and attemp to open the file
    # argv[0] is the name of this script so we need to start at 1
    file_path = sys.argv[cur_file_num+1]
    try:
        data_file = open(file_path)
    except IOError:
        logging.warning("Cannot open: "+file_path+". Skipping file.")
        continue
    # Read the file into a string and split it by the newline characters
    data = data_file.read()
    data = data.split('\n')
    # Close the file here just to free up some resources early
    data_file.close()
    loc = data[0]
    # Loop through the lines, skipping the first one since it's already used
    iterdata = iter(data)
    next(iterdata)
    for line in iterdata:
        # Used for matching time to location
        cur_addr = ''
        if line.strip() == '':
            continue
        # Addresses are 12 characters with a : every 2. If there are 5 : then
        # the line contains an address and possibly a name
        if len(line.split(':')) == 6:
            # Check if there is a name
            if '(' in line:
                addr_line = re.split('\(|\)', line)
                name = addr_line[0].strip()
                addr = addr_line[1].strip()
                if addr not in addr_name:
                    # Address is not in the name list
                    addr_name[addr] = name
                if addr not in addr_loc_time:
                    # Address is not in the time list
                    addr_loc_time[addr] = [[loc]]
                cur_addr = addr
            # Just an address
            else:
                addr = line.strip()
                if addr not in addr_loc_time:
                    addr_loc_time[addr] = [[loc]]
                cur_addr = addr
        # Line contains a time range
        else:
            # Date formated in human friendly string. Convert to epoch
            if ':' in line:
                times = line.split('-')
                time1 = time.mktime(time.strptime(times[0].strip()))
                time2 = time.mktime(time.strptime(times[1].strip()))
            # Date in epoch format. Convert from string to float
            else:
                times = line.split('-')
                time1 = float(times[0].strip())
                time2 = float(times[1].strip())
            loc_list = addr_loc_time[cur_addr]
            # Add times to the list
            if loc_list[-1][0] == loc:
                loc_list[-1] += [[time1, time2]]
            else:
                loc_list += [[loc, [time1, time2]]]
# All files compiled. Save them as one file
new_file = open("btdata_total", 'w')
for address in addr_loc_time:
    # Write name if applicable and address
    if address in addr_name:
        new_file.write(addr_name[address]+' ('+address+')\n')
    else:
        new_file.write(address+'\n')
    loc_time = addr_loc_time[address]
    # Go through each location sub-list
    for loc in loc_time:
        new_file.write(loc[0]+'\n')
        # Go through each time sub-list
        itertime = iter(loc)
        next(itertime)
        for times in itertime:
            if str_frmt:
                time1 = time.asctime(time.localtime(times[0]))
                time2 = time.asctime(time.localtime(times[1]))
                new_file.write(time1+' - '+time2+'\n')
            else:
                new_file.write(str(times[0])+' - '+str(times[1])+'\n')
        new_file.write('\n')
    new_file.write('\n\n')
new_file.close()
