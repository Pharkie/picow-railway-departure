import utime

def log(message, level='INFO'):

    timestamp = utime.localtime(utime.time())
    formatted_timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*timestamp)
    log_message = f"{formatted_timestamp} [{level}]: {message}\n"

    print(log_message)
    # log_file = open('rail_data_log.txt', 'a')
    # log_file.write(log_message) # Assumes log_file is a global variable
    # log_file.close()