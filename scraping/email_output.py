"""Email Collector class"""
from threading import Thread
import json

class EmailOutput(Thread):
    """Email Collector Class"""
    def __init__(self, results, json_data):
        Thread.__init__(self)
        self.work = results
        self.json_data = json_data

    def run(self):
        while True:
            domain, emaillist = self.work.get()

            for item in self.json_data:
                 if item.get("url") == domain:
                    item["emails"] = emaillist

            # Write the updated JSON back to the file
            with open('results/google_maps_results.json', 'w') as file:
                json.dump(self.json_data, file, indent=4)
            
            self.work.task_done()
