import fcntl
import time

def get_lock(state):
    result = False
    file = open('lock', 'r+')
    fcntl.flock(file.fileno(), fcntl.LOCK_EX)
    Lock = file.readline()
    # print('acquire lock {} at 2 at {}'.format(Lock,time.time()))
    if state == True and Lock == 'False':
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
    print('acquire lock')
    file.write('False')
    file.close()


while True:
    if get_lock(True):
        print('start mig at 2 at {}'.format(time.time()))
        time.sleep(3)
        write_lock()
        print('end mig at 2 at {}'.format(time.time()))
