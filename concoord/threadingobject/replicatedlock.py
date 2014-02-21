"""
@author: Deniz Altinbuken
@note: JCondition Coordination Object
@copyright: See LICENSE
"""
from threading import RLock, Lock
from concoord.exception import *

class JCondition:
    def __init__(self, lock=None):
        if lock is None:
            lock = JLock()
        self.__lock = lock
        # Export the lock's lock() and unlock() methods
        self.lock = lock.lock
        self.unlock = lock.unlock
        self.__waiters = []
        self.__atomic = RLock()

    def await(self, _concoord_command):
        """Causes the current thread to wait until it is signalled or
        interrupted."""
        with self.__atomic:
        # put the caller on waitinglist and take the lock away
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot await on un-acquired lock")
            self.__waiters.append(_concoord_command)
            self.__lock.unlock(_concoord_command)
            raise BlockingReturn()

    def await(self, time, unit, _concoord_command):
        """Causes the current thread to wait until it is signalled or
        interrupted, or the specified waiting time elapses."""
        with self.__atomic:
            # for now the time is in seconds since we will probably
            # convert the time in Java before this method is called.
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot await on un-acquired lock")
            self.__waiters.append(_concoord_command)
            self.__lock.unlock(_concoord_command)
            # XXX wait until timeout
            raise BlockingReturn()

    def awaitNanos(self, nanosTimeout, _concoord_command):
        """Causes the current thread to wait until it is signalled or
        interrupted, or the specified waiting time elapses."""
        with self.__atomic:
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot await on un-acquired lock")
            self.__waiters.append(_concoord_command)
            self.__lock.unlock(_concoord_command)
            # XXX wait until timeout
            raise BlockingReturn()

    def awaitUninterruptibly(self, _concoord_command):
        """Causes the current thread to wait until it is signalled."""
        with self.__atomic:
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot await on un-acquired lock")
            self.__waiters.append(_concoord_command)
            self.__lock.unlock(_concoord_command)
            raise BlockingReturn()

    def awaitUntil(self, deadline, _concoord_command):
        """Causes the current thread to wait until it is signalled or
        interrupted, or the specified deadline elapses."""
        with self.__atomic:
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot await on un-acquired lock")
            self.__waiters.append(_concoord_command)
            self.__lock.unlock(_concoord_command)
            # XXX handle interrupt
            # XXX wait until deadline
            raise BlockingReturn()

    def signal(self, _concoord_command):
        """Wakes up one waiting thread."""
        with self.__atomic:
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot signal on un-acquired lock")
            if not self.__waiters:
                return
            waitcommand = self.__waiters.pop(0)
            # notified client should be added to the lock queue
            self.__lock._add_to_queue(waitcommand)

    def signalAll(self, _concoord_command):
        """Wakes up all waiting threads."""
        with self.__atomic:
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot signal on un-acquired lock")
            if not self.__waiters:
                return
            for waitcommand in self.__waiters:
                # notified client should be added to the lock queue
                self.__lock._add_to_queue(waitcommand)
            self.__waiters = []

    def __repr__(self):
        return "<Condition(%s, %d)>" % (self.__lock, len(self.__waiters))

    def __str__(self):
        return "<%s object>" % (self.__class__.__name__)

class JLock:
    def __init__(self):
        self.__locked = False
        self.__owner = None
        self.__queue = []
        self.__atomic = Lock()

    def lock(self, _concoord_command):
        """Acquires the lock."""
        with self.__atomic:
            if self.__locked:
                self.__queue.append(_concoord_command)
                raise BlockingReturn()
            else:
                self.__locked = True
                self.__owner = _concoord_command.client

    def lockInterruptibly(self, _concoord_command):
        """Acquires the lock unless the current thread is interrupted."""
        #XXX Check currentThread().isInterrupted(true) in Java code.
        with self.__atomic:
            if self.__locked:
                self.__queue.append(_concoord_command)
                raise BlockingReturn()
            else:
                self.__locked = True
                self.__owner = _concoord_command.client

    def newCondition(self, _concoord_command):
        """Returns a new Condition instance that is bound to this Lock instance."""
        return JCondition(self)

    def tryLock(self, _concoord_command):
        """Acquires the lock only if it is free at the time of invocation."""
        with self.__atomic:
            if not self.__locked:
                self.__locked = True
                self.__owner = _concoord_command.client
                return True
            return False

    def tryLock(self, time, unit, _concoord_command):
        """Acquires the lock if it is free within the given waiting
        time and the current thread has not been interrupted."""
        with self.__atomic:
            # for now the time is in seconds since we will probably
            # convert the time in Java before this method is called.
            if not self.__locked or time == 0:
                self.__locked = True
                self.__owner = _concoord_command.client
                return True
            else:
                # XXX Block until timeout
                timeout = time.time() + time
                self.__queue.append(_concoord_command)
                raise BlockingReturn()


    def unlock(self, _concoord_command):
        """Releases the lock."""
        with self.__atomic:
            if self.__owner != _concoord_command.client:
                raise RuntimeError("cannot release un-acquired lock")
            if len(self.__queue) > 0:
                unblockcommand = self.__queue.pop(0)
                self.__owner = unblockcommand.client
                # add the popped command to the exception args
                unblocked = {}
                unblocked[unblockcommand] = True
                raise UnblockingReturn(unblockeddict=unblocked)
            elif len(self.__queue) == 0:
                self.__owner = None
                self.__locked = False

    def __repr__(self):
        return "<%s owner=%s>" % (self.__class__.__name__, str(self.__owner))

    def __str__(self):
        return "<%s object>" % (self.__class__.__name__)

