from scrapy import Spider
from ..items import BookingScraperItem


class BookingSpider(Spider):
    name = "booking"
    allowed_domains = ["booking.com"]
    item = BookingScraperItem()
    start_urls = ["https://www.booking.com/destination.html"]

    def parse(self, response):
        regions = response.xpath(
            '//ul[@class="dest-sitemap__list"]/li[@class="dest-sitemap__list-item"]/ul[@class="dest-sitemap__sublist"]/li[@class="dst-sitemap__sublist-item\n"]')
        for region in regions:
            region_name = region.xpath('.//h4[@class="dest-sitemap__sublist-title"]/text()').extract_first().strip()
            if region_name == "Europe":
                self.item['region'] = region_name
                countries = region.xpath('.//div[@class="dst-sitemap__sublist-item-content"]/ul/li')
                for country in countries:
                    country_name = country.xpath(".//a/text()").extract_first().strip()
                    if country_name == "Austria":
                        self.item["country"] = country_name
                        country_url = country.xpath('.//a/@href').extract_first().strip()
                        yield response.follow(country_url, callback=self.parse_country)
                        break  # stop all loops because i only want to scrape a certain city in austria

    def parse_country(self, response):
        # get Erl (city) only for now
        # city_name = response.xpath('//*[@id="bodyconstraint-inner"]/div[3]/div[2]/ul/li[1]/ul/li[1]/div/ul/li[39]/a/text()').extract_first().strip() # ALTBACH
        city_name = response.xpath('//*[@id="bodyconstraint-inner"]/div[3]/div[2]/ul/li[1]/ul/li[4]/div/ul/li[67]/a/text()').extract_first().strip()  # Erl
        self.item["city"] = city_name
        city_url = response.xpath('//*[@id="bodyconstraint-inner"]/div[3]/div[2]/ul/li[1]/ul/li[4]/div/ul/li[67]/a/@href').extract_first().strip()
        yield response.follow(city_url, callback=self.parse_city)

    def parse_city(self, response):
        # find the div that says `Hotels in city_name`
        paragraphs = response.xpath("//div[@class='dest-sitemap__content']/ul[@class='dest-sitemap__list']/li[@class='dest-sitemap__list-item']")
        for p in paragraphs:
            paragraph_title = p.xpath(".//h3/text()").extract_first()
            if paragraph_title and paragraph_title.strip() == "Hotels in " + self.item["city"].strip():
                hotel_urls = p.xpath(".//ul[@class='dest-sitemap__sublist']/li/div/ul/li/a/@href").extract()
                for hotel_url in hotel_urls:
                    yield response.follow(hotel_url, callback=self.parse_hotels)
                return  # no need to loop through paragraphs since i found the hotel paragraph

    def parse_hotels(self, response):
        # parse hotel name
        hotel_name = response.xpath("//h2[@class='hp__hotel-name']/text()").extract()[1].strip()  # first one being a \n element
        hotel_address = response.xpath("//div[@class='location_block__address']/span/text()").extract()

        # parse the rooms
        rooms_xpaths = response.xpath(
            '//table[@class="roomstable rt_no_dates dr_rt_no_dates js-dr_rt_no_dates __big-buttons rt_lightbox_enabled roomstable-no-dates-expanded"]/tbody/tr/td[@class="ftd roomType"]')
        rooms = []
        for room in rooms_xpaths:
            room_type = room.xpath('.//div[@class="room-info"]/a/@data-room-name-en').extract_first()
            room_beds = room.xpath('.//li[@class="rt-bed-type"]/span/text()').extract()
            if not room_beds:
                room_beds = room.xpath('.//li[@class="bedroom_bed_type"]/span/text()').extract()  # if there are no room beds, then the beds are in "apartment_type" room
            room_beds = list(map(lambda bed: bed.strip(), room_beds))
            room_beds = list(filter(None, room_beds))
            rooms.append({
                "room_type": room_type,
                "room_beds": room_beds
            })

        hotel = {
            "hotel_name": hotel_name,
            "hotel_address": hotel_address[0].strip(),
            "rooms": rooms
        }
        if "hotels" not in self.item:
            self.item["hotels"] = [hotel]
        else:
            self.item["hotels"].append(hotel)
        return self.item
