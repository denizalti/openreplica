class Job():
    """Job Object keeping information related to a specific job"""
    def __init__(self, jobname, jobid, jobtime):
        self.name = jobname
        self.id = jobid
        self.time = jobtime
        
    def __str__(self):
        return "Job %s: %s @ %s" % (str(job.id), str(job.name), str(job.time))
        
    
        
        
