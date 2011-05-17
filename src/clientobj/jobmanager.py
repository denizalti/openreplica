from job import Job

class JobManager():
    """Object to keep track of jobs in a system.
    Supports three functions:
    - add_job
    - remove_job
    - list_jobs
    """
    def __init__(self):
        self.jobs = []
        
    def add_job(self, args):
        self.jobs.append(args[0])
        
    def remove_job(self, args):
        self.jobs.append(args[0])
        
    def list_jobs(self, args):
        return self.__str__()
        
    def __str__(self):
        return " ".join([str(m) for m in self.members])
        
    
        
        
