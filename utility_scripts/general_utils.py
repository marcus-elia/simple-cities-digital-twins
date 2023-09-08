#!/usr/bin/env python3

def get_time_estimate_string(time_elapsed, num_complete, num_total):
    percent_complete = float(num_complete) / float(num_total) * 100
    time_remaining = int(time_elapsed * (100 - percent_complete) / percent_complete)
    if time_elapsed < 120:
        time_string = "%d seconds, " % (time_elapsed)
    else:
        time_elapsed = int(time_elapsed / 60)
        if time_elapsed < 120:
            time_string = "%d minutes, " % (time_elapsed)
        else:
            time_elapsed = int(time_elapsed / 60)
            time_string = "%d hours, " % (time_elapsed)
    if time_remaining < 120:
        time_string += "%d seconds remaining." % (time_remaining)
    else:
        time_remaining = int(time_remaining / 60)
        if time_remaining < 120:
            time_string += "%d minutes remaining." % (time_remaining)
        else:
            time_remaining = int(time_remaining / 60)
            time_string += "%d hours remaining" % (time_remaining)

    return "Completed %d/%d (%.1f percent) in %s" % (num_complete, num_total, percent_complete, time_string)

