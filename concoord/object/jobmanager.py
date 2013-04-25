"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example jobmanager
@copyright: See LICENSE
"""
class JobManager():
    def __init__(self):
        self.jobs = []

    def schedule(self, job):
        self.jobs.append(job)

    def deschedule(self, job):
        self.jobs.remove(job)

    def update(self, job, key, value):
        self.jobe[job].setattr(value)

    def list_jobs(self):
        return self.jobs

    def __str__(self):
        return " ".join([str(j) for j in self.jobs])

class Job():
    def __init__(self, jobname, jobid, jobtime):
        self.name = jobname
        self.id = jobid
        self.time = jobtime

    def __str__(self):
        return "Job %s: %s @ %s" % (str(job.id), str(job.name), str(job.time))




