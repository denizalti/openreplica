"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example jobmanager object
@copyright: See LICENSE
"""
class JobManager():
    def __init__(self, **kwargs):
        self.jobs = []
        
    def add_job(self, job, **kwargs):
        self.jobs.append(job)
        
    def remove_job(self, job, **kwargs):
        self.jobs.append(job)
        
    def list_jobs(self, **kwargs):
        return self.__str__()
        
    def __str__(self, **kwargs):
        return " ".join([str(j) for j in self.jobs])

class Job():
    def __init__(self, jobname, jobid, jobtime):
        self.name = jobname
        self.id = jobid
        self.time = jobtime
        
    def __str__(self):
        return "Job %s: %s @ %s" % (str(job.id), str(job.name), str(job.time))

    
        
        
