# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TutorialItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class PosterItem(scrapy.Item):
    post_tieba = scrapy.Field()
    post_title = scrapy.Field()
    post_url = scrapy.Field()
    post_page = scrapy.Field()
    post_position = scrapy.Field()
    post_author = scrapy.Field()
    post_time = scrapy.Field()
    post_line = scrapy.Field()
    pass
