import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


# generate some random data (approximately over 5 years)
with open("./logs/tcpdump.dump", "r") as f:
    tmp_data = f.readlines()

data_rcvd = []
data_sent = []   
for line in tmp_data:
    try:
        s = line.strip().split(" ")
        t = datetime.strptime(s[0], '%H:%M:%S.%f')
        data_rcvd.append(t)
    except Exception as exc:
        # print(exc)
        continue

# print(data_rcvd)
mpl_data = mdates.date2num(data_rcvd)

# plot it
fig, ax = plt.subplots(1,1)
ax.hist(mpl_data, bins=100, color='lightblue')
locator = mdates.AutoDateLocator()
locator.intervald[mdates.SECONDLY] = [5] 
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(locator))
plt.savefig("./rcv.svg")
plt.close()