import sys
import time
import threading
import logging
import bluetooth

# Area Identifier
room_name = 'Unknown' if len(sys.argv) == 1 else sys.argv[1]
# Dictionary of addresses to approximate times the device is in range for
# times are a list of tuples of discovery and out of range times in epoch time
addr_time = {}
# Dictionary of an address to the human friendly name
addr_name = {}
# Flag for saying when to stop and dump data into record
run = True
# Check args for debug flags
# Flag for if the times are formated
strdt = True
for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    if '--string_format=' in arg:
        arg = arg.split('=')
        if arg[1] == "epoch" or arg[1] == "Epoch" or arg[1] == "EPOCH":
            strdt = False
        elif arg[1] != "asctime" and arg[1] != "Asctime" and \
                arg[1] != "AscTime" and arg[1] != "ASCTIME":
            logging.warning("string_format option: '"+arg[1]+"' not" +
                            " supported. Defaulting to asctime")
    if '--debug=' in arg:
        arg = arg.split('=')
        if arg[1] == 'true' or arg[1] == 'True' or arg[1] == 't' or \
                arg[1] == 'T':
            # Set logger to print debug statements
            logging.basicConfig(level=logging.DEBUG)
        elif arg[1] != 'false' and arg[1] != 'False' and arg[1] != 'f' and \
                arg[1] != 'F':
            logging.warning("debug option: '"+arg[1]+"' not supported. " +
                            "Defaulting to false")


def run_track():
    global addr_time, addr_name, run
    while run:
        # Default duration is 8. In units of 1.28 sec. 10.24 sec default
        nearby_dev = bluetooth.discover_devices(lookup_names=True)
        cur_time = time.time()
        logging.debug("Search complete")
        logging.debug(str(len(nearby_dev)) + " device(s) found")
        logging.debug(str(nearby_dev))
        for addr, name in nearby_dev:
            # First discovery of name
            if addr not in addr_name:
                addr_name[addr] = name
            # First Discovery of address
            if addr not in addr_time:
                addr_time[addr] = [(cur_time, cur_time)]
            # Discovery after out-of-range
            # More than 1.5 minutes since last discovery means rediscovery
            elif (cur_time - addr_time[addr][-1][1]) > 90:
                addr_time[addr] += [(cur_time, cur_time)]
            # Discovery when device has not left range (it's still there)
            else:
                addr_time[addr][-1] = (addr_time[addr][-1][0], cur_time)

logging.info("Starting log...")
tracker = threading.Thread(target=run_track)
tracker.start()
# Below works but raises flake8 errors
# if sys.version_info > (3.0):
#     input("Press Enter to end track and save data.\n")
# else:
#     raw_input("Press Enter to end track and save data.\n")
try:
    import __builtin__
    input = getattr(__builtin__, 'raw_input')
except (ImportError, AttributeError):
    pass
input("Press Enter to end track and save data.\n")
# Until I understand how to lock properly I'm just going to have to deal with
# the race conditions
run = False
tracker.join()
end_time = time.time()
save_file = open("btdata_"+room_name, 'w')
save_file.write(room_name+'\n\n')
# Write each address block
for address in addr_time:
    # If name exists, write name and address, otherwise just the address
    if address in addr_name:
        save_file.write(addr_name[address]+' ('+address+')\n')
    else:
        save_file.write(address+'\n')
    # Write each of the times in the current address block
    addr_time_list = addr_time[address]
    for t in addr_time_list:
        time_start = time.asctime(time.localtime(t[0])) if strdt else str(t[0])
        if t[1] == 0:
            time_end = time.asctime(time.localtime(end_time)) if strdt else \
                str(end_time)
        else:
            time_end = time.asctime(time.localtime(t[1])) if strdt else \
                str(t[1])
        time_str = time_start + ' - ' + time_end
        save_file.write(time_str+'\n')
    save_file.write('\n')
save_file.close()
