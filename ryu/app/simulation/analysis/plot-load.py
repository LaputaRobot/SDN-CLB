import csv
import os

import matplotlib.pyplot as plt

newestFolder = sorted(os.listdir('..\\Result'))[-1]
baseFolder = os.path.join(os.path.abspath('..\\Result'), newestFolder)


def read_csv_to_list(base_folder, controller_num):
    all_list = []
    for i in range(1, controller_num + 1):
        all_list.append(list(csv.reader(open(os.path.join(base_folder, 'Con{}.csv'.format(i))), delimiter=',')))
    return all_list


def list_to_xy(all_list, index):
    all_x = []
    if index == 0:
        start_time = float(all_list[0][1][0])
    for l in all_list:
        x=[]
        for row in range(1, len(l)):
            if index == 0:
                x.append(float(l[row][index]) - start_time)
            else:
                x.append(float(l[row][index]))
        all_x.append(x)
    return all_x


def plot_all_y(ax, x, y, label, line_width, file_num):
    for i in range(1, file_num + 1):
        ax.plot(x[i - 1], y[i - 1], label=label.format(i), linewidth=line_width)


model = 2
all_file_list = read_csv_to_list(baseFolder, 4)
all_time = list_to_xy(all_file_list, 0)
all_load = list_to_xy(all_file_list, model)

fig = plt.figure()
ax = fig.add_subplot(111)

# 添加X/Y轴描述


label = "controller{}-OUR"

plot_all_y(ax, all_time, all_load, label=label, line_width=0.7, file_num=4)
# ax.set_xlim(0,200)
# ax.set_ylim(0, 150)
ax.set_xlabel('time(s)')
if model == 2:
    ax.set_ylabel('Controller-Load(packet/s)')
elif model == 3:
    ax.set_ylabel('LBR')
ax.legend(loc=1, prop={'size': 5})
plt.show()
# fig.savefig('C:/Users/25247/Desktop/result-0801/my/load-my.png', dpi=300)
