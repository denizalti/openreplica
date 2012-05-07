from concoord.clientproxymultithreaded import *
from time import sleep

c = ClientProxy("128.84.227.37:14000")

sleep(10)
for i in range(30000):
    c.invoke_command("getvalue")
