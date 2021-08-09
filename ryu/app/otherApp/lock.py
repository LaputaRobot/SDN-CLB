import fcntl
import time

def get_lock(state):
    result = False
    file = open('lock', 'r+')
    fcntl.flock(file.fileno(), fcntl.LOCK_EX)
    Lock = file.readline()
    if Lock=='True':
        print('other mig in progress !!!')
    if state == True and Lock == 'False':
        print('acquire lock {}  at {}'.format(Lock, time.time()))
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
    file.write('False')
    file.flush()
    file.close()
    print('write lock False at {}'.format(time.time()))
