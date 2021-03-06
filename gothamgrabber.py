#! /usr/bin/env python3

import argparse
import os
import requests
import subprocess
import urllib
from bs4 import BeautifulSoup

def get_ist_bookmarks(url, index=1):
    res = requests.get(url + "/" + str(index))
    soup = BeautifulSoup(res.text, "html.parser")
    marks = soup.findAll('a', attrs={'rel':'bookmark'})
    if len(marks) == 1000:
        marks.extend(get_ist_bookmarks(url, index + 1))        
    return marks
 
def scrape_ist_page(url):
    marks = get_ist_bookmarks(url)
    marklinks = [mark['href'] for mark in marks]
    return marklinks

def scrape_dnainfo_page(url, index=1):
    scrape_url = url + "/page/" + str(index)
    res = requests.get(scrape_url)
    soup = BeautifulSoup(res.text, "html.parser")
    links = ['https:' + link['href'] for link in soup.findAll('a',
             attrs = {'class':'headline'})]
    if len(links) == 8:
        links.extend(scrape_dnainfo_page(url, index + 1))
    return links

def log_errors(url, dirname, error_bytes):
    filename = "errors.log"
    processed_error = error_bytes.decode('utf-8').split('\n')[0]
    with open(os.path.join(dirname, filename), "a") as f:
        f.write(url + '\n')
        f.write(processed_error + '\n')

def main():
    parser = argparse.ArgumentParser(description="A script for scraping and converting to PDF all of the articles by a given author in the DNAinfo/Gothamist network. Accepts either a URL to an online author page or a list of links to articles as input.")
    infile = parser.add_mutually_exclusive_group(required=True)
    infile.add_argument("-u","--url", help="The Gothamist network or DNAinfo URL for the author page with the links you want to collect", default=None)
    infile.add_argument("-t","--textfile", help="A list of links for the grabber script to convert to PDFs", default=None)

    args = parser.parse_args()

    if args.url:
        url = args.url
        
        slug = url.split("/")[-1]

        slug = urllib.parse.unquote(slug)
        names = slug.lower().split()
        name = names[-1]

        filename = "-".join(names) + ".txt"

        dirname = os.path.join("out", name)

        if not(os.path.exists(dirname)):
            os.makedirs(dirname)

        if 'ist.com' in url:
            print("Scraping Gothamist network page. This may take take a while.")
            links = scrape_ist_page(url)
        elif 'dnainfo.com' in url:
            print("Scraping DNAinfo page. This may take a while.")
            links = scrape_dnainfo_page(url)
        else:
            print("Link must be to a page in the DNAinfo/Gothamist network.")
            return

        with open(os.path.join(dirname, filename), "w") as f:
            f.write('\n'.join(links))

    elif args.textfile:
        filename = args.textfile
        dirname = os.path.dirname(filename)

        with open(filename, "r") as f:
            links = f.read().splitlines()

    errorcount = 0

    for link in links:
        number = links.index(link) + 1
        progress = "(" + str(number) + "/" + str(len(links)) + ")"
        command = ["node", "grabber.js", "--url", link, "--outdir", dirname]
        print("Making PDF of " + link + " " + progress)
        process = subprocess.run(command, stdout=subprocess.PIPE)
        if process.returncode:
            print("Encountered an error with that URL. Logging it now.")
            errorcount += 1
            log_errors(link, dirname, process.stdout)

    completed = len(links) - errorcount
    print("Scrape complete. {completed} files should be available in {dirname}.".format(**locals()))

if __name__ == "__main__":
    main()
