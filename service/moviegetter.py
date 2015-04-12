# coding=gbk
import sys, json, urllib2, datetime, requests, logging, re
from bs4 import BeautifulSoup
from datetime import datetime
from pymongo import Connection

reload(sys)
sys.setdefaultencoding('utf-8')

# period = 43200
num_retry = 20
con = Connection()
db = con.moviesdb
cinemas = db.cinemas
films = db.films


def get_location(pc):
    return requests.get('http://api.postcodes.io/postcodes/' + pc).json()

# -----------BUild Parser---------------
class Parser(object):

    def __init__(self, url):
        self.url = url
        req_cinemas = requests.get(self.url)
        self._htmlParser = BeautifulSoup(req_cinemas.text)

    def _parse(self):
        return []


class CinemaParser(Parser):

    def __init__(self, url):
        super(CinemaParser, self).__init__(url)

    @property
    def cinema_list(self):
        return self._parse()


class OdeonCinemaParser(CinemaParser):

    def __init__(self):
        super(OdeonCinemaParser, self).__init__('http://www.odeon.co.uk/cinemas/')

    def _parse(self):
        print 'Buildind Odeon Cinema'
        odeonCinemaParse = self._htmlParser.find('select', id="your-cinema").select('option')
        CinemaList = []

        for odeonCinema in odeonCinemaParse:
            try:
                cinema_name = odeonCinema.string.strip()
                if len(cinema_name) > 0 and cinema_name[:6] != 'Select':
                    CinemaList.append({
                        'name': cinema_name,
                        'url': self.url + 'requests/' + odeonCinema['value'],
                        'type': 'odeon'
                    })
            except:
                pass
        return CinemaList


class CineWorldCinemaParser(CinemaParser):

    def __init__(self):
        super(CineWorldCinemaParser, self).__init__('http://www.cineworld.co.uk/whatson?cinema=london-bexleyheath')
        self._pre_url = 'http://www.cineworld.co.uk/whatson?cinema='

    def _parse(self):
        print 'Buildind CineWorld Cinema'
        cineworldCinemaParse = self._htmlParser.find('form', attrs={'name':"form-location"}).find('select').select('option')
        CinemaList = []

        for cineworldCinema in cineworldCinemaParse:
            try:
                cinema_name = cineworldCinema.string.strip()
                if len(cinema_name) > 0 and cinema_name[:6] != 'Select':
                    CinemaList.append({
                        'name': cinema_name,
                        'url': self._pre_url + cineworldCinema['value'],
                        'type': 'cineworld'
                    })
            except:
                pass
        return CinemaList


class VueCinemaParser(CinemaParser):

    def __init__(self):
        super(VueCinemaParser, self).__init__('http://www.myvue.com/cinemas/')

    def _parse(self):
        print 'Buildind Vue Cinema'
        str_info = '{}'.format(self._htmlParser.find_all('script'))
        vueCinemaParse = re.findall(r'\{\".*\}', str_info)
        CinemaList = []

        for vueCinema in vueCinemaParse:
            try:
                vueCinema = json.loads(vueCinema)
                cinema_name = vueCinema['markerText'].strip()
                if len(cinema_name) > 0 and cinema_name[:6] != 'Select':
                    infoText = BeautifulSoup(vueCinema['infoText'])
                    CinemaList.append({
                        'name': cinema_name,
                        'url': infoText.find('a')['href'],
                        'type': 'vue',
                        'lat': vueCinema['lat'],
                        'lng': vueCinema['lng']
                    })
            except:
                pass
        return CinemaList


class MovieParser(Parser):

    def __init__(self, url, cinema_id):
        super(MovieParser, self).__init__(url)
        self.cinema_id = cinema_id
        print url

    def _parse_movies(self):
        return []

    def _parse_price(self):
        return []

    @property
    def movie_list(self):
        return self._parse_movies()

    @property
    def price(self):
        return self._parse_price()

    @property
    def cinema_info(self):
        return self._parse()


class VueMovieParser(MovieParser):

    def __init__(self, url, cinema_id):
        super(VueMovieParser, self).__init__(url, cinema_id)
        self._price_url = self.url.replace('about-vue-cinemas', 'ticket-prices')
        self._films_url = self.url.replace('cinemas/about-vue-cinemas', 'latest-movies')

    def _parse(self):
        return None

    def _parse_price(self):
        return {
            'price': {
                'url': self._price_url
            }
        }

    def _parse_movies(self):
        req_films = requests.get(self._films_url)
        film_parser = BeautifulSoup(req_films.text)
        film_list = []
        for film in film_parser.find_all('div', 'filmListFilm'):
            film_list.append({
                'name': film.find('h3').find('a').string.strip(),
                'img': 'http://www.myvue.com' + film.find('div', 'filmListFilmImageContainer').find('img')['src'],
                'cinema_id': self.cinema_id,
                'general_id': 'pending',
                'when': {
                    'date': datetime.today(),
                    'time': [time.string for time in film.find('ul').find_all('span')]
                }
            })

        return film_list


class OdeonMovieParser(MovieParser):

    def __init__(self, url, cinema_id):
        super(OdeonMovieParser, self).__init__(url, cinema_id)

    def _parse(self):
        loc_parser = self._htmlParser
        post_code = loc_parser.find('div', 'gethere').find('p', 'description').text
        post_code = " ".join(post_code.split()[-2:])
        retval = {'postcode': post_code}
        try:
            result = get_location(post_code)['result']
            retval['lat'] = result['latitude']
            retval['lng'] = result['longitude']
        except:
            print 'Unable to get location of postcode: {}'.format(post_code)

        return retval
        

    def _parse_price(self):
        return {
            'price': {
                'html': '{}'.format(self._htmlParser.find('div', id="prices"))
            }
        }

    def _parse_movies(self):
        film_parser = self._htmlParser
        film_list = []
        for film in film_parser.find_all('div', 'film-detail DAY1'):
            film_list.append({
                'name': film.find('h4').find('a').string.strip(),
                'img': film.find('img')['src'],
                'cinema_id': self.cinema_id,
                'general_id': 'pending',
                'when': {
                    'date': datetime.today(),
                    'time': [time.string for time in film.find('ul', 'unstyled inline').find_all('a')]
                }
            })

        return film_list


class CineworldMovieParser(MovieParser):

    def __init__(self, url, cinema_id):
        cinema_name = url.split('=')[-1]
        info_url = 'http://www.cineworld.co.uk/cinemas/{}/information'.format(
            cinema_name
        )
        super(CineworldMovieParser, self).__init__(info_url, cinema_id)
        self._films_url = url + '&date=today'

    def _parse(self):
        loc_parser = self._htmlParser
        post_code = loc_parser.find('address').text.split('\n')[-3]
        post_code = " ".join(post_code.split()[-2:])
        retval = {'postcode': post_code}
        try:
            result = get_location(post_code)['result']
            retval['lat'] = result['latitude']
            retval['lng'] = result['longitude']
        except:
            print 'Unable to get location of postcode: {}'.format(post_code)

        return retval

    def _parse_price(self):
        return {
            'price': {
                'html': '{}'.format(self._htmlParser.find('div', 'pricing'))
            }
        }

    def _parse_movies(self):
        req_films = requests.get(self._films_url)
        film_parser = BeautifulSoup(req_films.text)
        film_list = []
        for film in film_parser.find_all('div', 'film-detail DAY1'):
            film_list.append({
                'name': film.find('h3', 'h1').find('a').string.strip(),
                'img': film.find('img')['data-original'],
                'cinema_id': self.cinema_id,
                'general_id': 'pending',
                'when': {
                    'date': datetime.today(),
                    'time': [time.string for time in film.find('ol').find_all('span')]
                }
            })

        return film_list

# -------------Build Getter----------------
class MovieGetter:

    CinemaParserList = [OdeonCinemaParser, CineWorldCinemaParser, VueCinemaParser]

    @staticmethod
    def updateMovies():
        print("Updating Movies")

        logging.basicConfig(filename='sys.log',level=logging.DEBUG)

        for cinema in cinemas.find():

            movie_parser = None
            if cinema['type'] == 'vue':
                parser = VueMovieParser
            elif cinema['type'] == 'odeon':
                parser = OdeonMovieParser
            elif cinema['type'] == 'cineworld':
                parser = CineworldMovieParser
            else:
                print 'No parser available for type {}'.format(cinema['type'])
                continue

            movie_parser = parser(cinema['url'], cinema['_id'])
            # Update Movies
            for movie in movie_parser.movie_list:
                films.update({
                    'name': movie['name'], 
                    'cinema_id': movie['cinema_id']
                }, {'$set':  movie}, upsert=True)
            # Update Location
            cinema_loc = movie_parser.cinema_info
            if not cinema_loc is None:
                cinemas.update({'_id':cinema['_id']}, {'$set':
                    cinema_loc
                }, upsert=False)
            # Update Prices
            cinemas.update({'_id':cinema['_id']}, {'$set':
                movie_parser.price
            }, upsert=False)

    @staticmethod
    def buildCinemaDB():
        print("Building Cinema DB")

        logging.basicConfig(filename='sys.log',level=logging.DEBUG)

        CinemaList = []
        for parser in MovieGetter.CinemaParserList:
            CinemaList += parser().cinema_list

        print("Finished Web Requests")

        for cinema in CinemaList:
            cinemas.update({
                    'name': cinema['name'],
                    'type': cinema['type']
                }, {'$set': cinema}, upsert=True)
            

        print("Cinema DB Built")