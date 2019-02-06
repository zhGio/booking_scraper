# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BookingScraperItem(scrapy.Item):
    region = scrapy.Field()
    country = scrapy.Field()
    city = scrapy.Field()
    hotels = scrapy.Field()

