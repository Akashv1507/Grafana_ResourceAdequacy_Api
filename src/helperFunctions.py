import datetime as dt

def adjustToNearestQuarter(timestamp):
    """
    Decrease the timestamp by 1 minute until it aligns with a quarter (0, 15, 30, 45).
    """
    for _ in range(15):  # Maximum 15 iterations
        if timestamp.minute % 15 == 0:
            return timestamp
        timestamp -= dt.timedelta(minutes=1)
    return timestamp  # Fallback (not expected to be reached)

def filterSchBwTwoTimestamp (schDataList:list, startTime:dt.datetime, endTime:dt.datetime ):
    
    """
    Filter a list of 96 values (15-minute blocks for a day) between two timestamps.
    
    Parameters:
    - schDataList: List of 96 values representing 15-minute blocks for a day
    - startTime: Start datetime to filter from
    - endTime: End datetime to filter until
    
    Returns:
    - List of [value, unix_timestamp_in_milliseconds] pairs for blocks within the time range
    """
        
    filteredSchListForPlot = []
    currentTime = startTime
    while currentTime<=endTime:
        currentTimeBlk = currentTime.hour *4 + int(currentTime.minute/15) +1
        #since block starts with 1 and index of list start with 0
        filteredSchListForPlot.append([schDataList[currentTimeBlk-1], int(currentTime.timestamp() * 1000)])
        currentTime = currentTime + dt.timedelta(minutes=15)
    return filteredSchListForPlot