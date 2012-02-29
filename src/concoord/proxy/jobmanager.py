'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: JobManager proxy
@copyright: LICENSE
'''
from concoord.clientproxy import ClientProxy

class JobManager:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)
        return self.proxy.invoke_command('__init__')

    def add_job(self, job):
        return self.proxy.invoke_command('add_job', job)

    def remove_job(self, job):
        return self.proxy.invoke_command('remove_job', job)

    def list_jobs(self):
        return self.proxy.invoke_command('list_jobs')

    def __str__(self):
        return self.proxy.invoke_command('__str__')

class Job:
    def __init__(self, jobname, jobid, jobtime):
        self.name = jobname
        self.id = jobid
        self.time = jobtime

    def __str__(self):
        return 'Job %s: %s @ %s' % (str(job.id), str(job.name), str(job.time))
