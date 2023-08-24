# Scrapia. _Baron_ Scrapia.

> Scrapia? That licentious app which exploits the uses of Python as refinements for its data lust,
and makes both BeautifulSoup and matplotlib the servant of its wantonness!

— Mario Cavaradossi, [Tosca], [Act 1][libretto]

## Overview

Scrapia is a small tool for both collecting and analyzing data on free rooms
in the [JUFA Hotel Bregenz](https://www.jufahotels.com/hotel/bregenz), Lake Constance, Austria.

It can be used to continually (i.e., every week or so) check which rooms are still free,
visualize that information and then decide if it is time to book, as well as which date and room to choose.

The tool consists of two parts:
- The scraping script: [`scrape.py`](scrape.py)
- And the analysis script: [`analyze.py`](analyze.py)

## Usage

Usage is very simple.

#### Scraping

In order to scrape information from the website, run `python scrape.py wet`.

If the parameter `wet` is not present or contains something else, the website will not be contacted,
but other funcitonality (e.g., the HTML parser) is still checked using a cached server response.

#### Analysis

To analyze the latest data, run `python analyze.py`.

### Warning: Keep HTTP requests to a minimum!

Please make sure to never execute too many wet runs of the scraper too close together.
We neither want to accidentally DOS the hotel's booking system nor make them close
it down or block users of this script.

You can test non-HTTP-related code using dry runs of the scraper
(just run `python scrape.py` with no additional arguments), and use the previously collected
CSV files in [`collected_results/`](collected_results/) for analysis.



[Tosca]: https://en.wikipedia.org/wiki/Tosca
[libretto]: http://www.murashev.com/opera/Tosca_libretto_Italian_English
