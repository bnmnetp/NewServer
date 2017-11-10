# ****************************************
# |docname| - Test this server under load?
# ****************************************

from locust import HttpLocust, TaskSet, task
from lxml import html
import requests as rq



def timeit(f):

    def timed(*args, **kw):

        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        print('func:%r args:[%r, %r] took: %2.4f sec' % \
          (f.__name__, args, kw, te-ts))
        return result

    return timed

class SimpleTests(TaskSet):

    @task
    def index(self):
        self.client.get("/", verify=False)

    @task
    def home(self):
        self.client.get("/runestone/course/index.html", verify=False)
        self.getAllAssets()


    ## @task
    ## def logrun(self):
    ##     self.client.post("/runestone/ajax/hsblog",
    ##         {'event': 'activecode', 'act': 'edit', 'div_id': 'logtest'},
    ##         verify=False)

    @task
    def add(self):
        return 2+2

    @task
    def dynamicpage(self):
        self.r = self.client.get("/runestone/course/PythonTurtle/TheforLoop.html", verify=False)
        self.getAllAssets()

    def getAllAssets(self):
        tree = html.fromstring(self.r.text)
        csslinks = tree.xpath('//link/@href')
        jslinks = tree.xpath('//script/@src')
        base = self.r.url[:self.r.url.rfind('/')+1]
        for l in csslinks:
            rq.get(base + l, verify=False)

        for l in jslinks:
            rq.get(base + l, verify=False)

class WebsiteUser(HttpLocust):
    task_set = SimpleTests
    min_wait = 5000
    max_wait = 15000
    host = "http://rstest"
