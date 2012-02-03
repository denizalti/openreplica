"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Automatically generated bank object proxy
@date: March 20, 2011
@copyright: See COPYING.txt
"""
from concoord.clientproxy import *

class Bank():
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)

    def open(self, accntno, **kwargs):
        self.proxy.invoke_command("open", accntno)

    def close(self, accntno, **kwargs):
        self.proxy.invoke_command("close", accntno)

    def debit(self, accntno, amount, **kwargs):
        self.proxy.invoke_command("debit", accntno, amount)

    def deposit(self, accntno, amount, **kwargs):
        self.proxy.invoke_command("deposit", accntno, amount)

    def balance(self, accntno, **kwargs):
        self.proxy.invoke_command("balance", accntno)

    def __str__(self):
        self.proxy.invoke_command("__str__", )

