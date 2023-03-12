import queue
import ssl
import threading
from threading import Thread
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen, URLError

from bs4 import BeautifulSoup


class Crawler(Thread):
    def __init__(self, base_url, links_to_crawl, have_visited, error_links, url_lock):
        threading.Thread.__init__(self)
        print(f"Web Crawler worker {threading.current_thread()} has started")
        self.base_url = base_url
        self.links_to_crawl = links_to_crawl
        self.have_visited = have_visited
        self.error_links = error_links
        self.url_lock = url_lock

    def run(self):
        # Creating a ssl context to we can crawl the webpage with the handshake
        my_ssl = ssl.create_default_context()
        # by default, we have to verify certificate in a handshake when sending requests to http page,
        # but we want to crawl the webpage so that is not needed
        my_ssl.check_hostname = False
        my_ssl.verify_mode = ssl.CERT_OPTIONAL
        # We make a loop till we get all the links and hence,
        while True:
            # No two threads access the same page/url
            self.url_lock.acquire()
            print(f"Queue Size: {self.links_to_crawl.qsize()}")
            link = self.links_to_crawl.get()
            self.url_lock.release()
            if link is None:
                break
            if link is self.have_visited:
                print(f"The link {link} has already been visited")
                break

            try:
                # This method constructs a full "absolute" URL by combining the
                # base url with other url. this uses components of the base URL,
                # in particular the addressing scheme, the network
                # location and  the path, to provide missing components
                # in the relative URL.
                # in short, we repair our relative url if it is broken.
                link = urljoin(self.base_url, link)
                req = Request(link, headers={'User-Agent': 'Chrome/5.0'})
                # We are requesting the ssl handshake and reading it,

                response = urlopen(req, context=my_ssl)
                # This returns the status of the current url we crawled upon

                print(f"The URL {response.geturl()} crawled with \
                            status {response.getcode()}")
                soup = BeautifulSoup(response.read(), "html.parser")
                # We return this in an html format

                # to find the links to webpages in crawling we use
                for a_tag in soup.findAll('a'):
                    if a_tag.get("href") not in self.have_visited and (urlparse(link).netloc == "www.python.org"):
                        self.links_to_crawl.put(a_tag.get("href"))
                    else:
                        print(f"The link {a_tag.get('href')} is already visited or is not part \
                            of the website")
                print(f"Adding {link} to the crawled list")
                self.have_visited.add(link)
            except URLError as e:
                print(f"URL {link} threw this error {e.reason} while trying to parse")

                self.error_links.append(link)
            finally:
                self.links_to_crawl.task_done()


print("The Crawler is started")
base_url = input("Please Enter Website to Crawl > ")
number_of_threads = input("Please Enter number of Threads > ")

links_to_crawl = queue.Queue()
url_lock = threading.Lock()
links_to_crawl.put(base_url)

have_visited = set()
crawler_threads = []
error_links = []
# base_url, links_to_crawl,have_visited, error_links,url_lock
for i in range(int(number_of_threads)):
    crawler = Crawler(base_url=base_url,
                      links_to_crawl=links_to_crawl,
                      have_visited=have_visited,
                      error_links=error_links,
                      url_lock=url_lock)

    crawler.start()
    crawler_threads.append(crawler)

    for crawler in crawler_threads:
        crawler.join()

print(f"Total Number of pages visited are {len(have_visited)}")
print(f"Total Number of Errornous links: {len(error_links)}")
