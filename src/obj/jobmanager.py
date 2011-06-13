class Job():
    """Job Object keeping information related to a specific job"""
    def __init__(self, jobname, jobid, jobtime):
        self.name = jobname
        self.id = jobid
        self.time = jobtime
        
    def __str__(self):
        return "Job %s: %s @ %s" % (str(job.id), str(job.name), str(job.time))

class Jobmanager():
    """Object to keep track of jobs in a system.
    Supports three functions:
    - add_job
    - remove_job
    - list_jobs
    """
    def __init__(self):
        self.jobs = []
        
    def add_job(self, args, **kwargs):
        job = args[0]
        self.jobs.append(job)
        
    def remove_job(self, args, **kwargs):
        job = args[0]
        self.jobs.append(job)
        
    def list_jobs(self, **kwargs):
        return self.__str__()
        
    def __str__(self):
        return " ".join([str(j) for j in self.jobs])
        
    
        
        
