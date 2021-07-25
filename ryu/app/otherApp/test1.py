import fcntl
import time

with open('lock', 'w') as f:
    f.write('False')


def get_lock(state):
    result = False
    file = open('lock', 'r+')
    fcntl.flock(file.fileno(), fcntl.LOCK_EX)
    Lock = file.readline()
    if state == True and Lock == 'False':
        print('acquire lock {} at 1 at {}'.format(Lock, time.time()))
        result = True
        file.seek(0)
        file.truncate()
        file.write('True')
        print('write True')
    file.close()
    return result


def write_lock():
    file = open('lock', 'w')
    fcntl.flock(file.fileno(), fcntl.LOCK_EX)
    # print('acquire lock')
    file.write('False')
    file.close()


while True:
    if get_lock(True):
        print('start mig at 1 at {}'.format(time.time()))
        time.sleep(0.1)
        write_lock()
        print('end mig at 1 at {}'.format(time.time()))
