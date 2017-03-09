"""
    Core objective of this etl framework. This is the highest level API.

    Each one of them will be run in backend on server, at designated
    time intervals.

    It includes four main methods in total:
        1. update movie data
        2. update movie public rating
        3. update the list of cinemas in Singapore
        4. update cinema schedule for each cinema available
"""
from cinema import CinemaList, CinemaSchedule
from movie import MovieData
from loader import Loader
from movie_id_matcher.matcher import MovieIDMatcher
from urllib import error

import utils
import time
import logging
import psycopg2


class ETLController:

    def __init__(self):
        self.loader = Loader()

    def update_movie_data(self, lower, upper, delay):
        """
        updates movie data from IMDb
        :param lower: integer
        :param upper: integer
        :param delay: integer
        :return: None
        """
        logging.info("Initialise movie data retrieval process ...")
        logging.info("Range: " + str(lower) + " to " + str(upper) + ", starting in " + str(delay) + "s ...")

        time.sleep(delay)  # delay to avoid database transaction lock during multi-thread process
        existing_movies_id = self.loader.get_movie_id_list()

        for index in range(lower, upper):  # iterate all possible titles
            current_imdb_id = self._build_imdb_id(index)

            if index % 1000 == 0:  # id monitor
                logging.info("Currently at: " + current_imdb_id)

            if current_imdb_id in existing_movies_id:
                continue

            try:
                self._update_single_movie_data(current_imdb_id)
            except error.HTTPError:
                continue
            except utils.InvalidMovieTypeException:
                continue
            except psycopg2.InterfaceError:
                logging.error("Reestablishing database connection")
                self.loader = Loader()
                continue
            except Exception as e:
                logging.error("Unknown error occurs. Please examine.")
                logging.error(e)
                logging.error(current_imdb_id)

        logging.info("Movie data update process complete.")

    def update_movie_rating(self):
        """
        updates movie rating from various websites
        """
        logging.info("Initialise movie rating update process ...")

        id_list = self.loader.get_movie_id_list()

        logging.info("Movie rating update process complete.")

    def update_cinema_list(self):
        """
        Update cinema list from various theatres websites
        :return: None
        """
        cinema_list_object = CinemaList()
        cinema_list = cinema_list_object.get_latest_cinema_list()
        self.loader.load_cinema_list(cinema_list)

    def update_cinema_schedule(self):
        """
        Update latest cinema schedule from cinema list.

        It passes an empty dictionary to each cinema schedule object,
        every iteration it will append that cinema's schedule to the
        dictionary.

        IMDb ID is obtained using MovieMatcher module in the process.


        The dictionary should be structured using title and imdb_id
        as the top level keys, follow by other data.

        {
            title: {
                "imdb_id": ...
                "content": [{
                        "cinema_id": ...
                        "schedule": [...]
                        "type": ...
                    }
                ]
            }
        }
        """
        cinema_schedule_data = {}

        # retrieve schedule
        cinema_list = self.loader.get_cinema_list()
        self._cinema_schedule_retrieve(cinema_list, cinema_schedule_data)

        # match id and check existence
        matcher = MovieIDMatcher()
        for title, content in cinema_schedule_data.items():
            imdb_id = matcher.match_imdb_id_for_cinema_schedule(title)
            content['imdb_id'] = imdb_id
            self.movie_list = self.loader.get_movie_id_list()
            self._update_single_movie_data(imdb_id)

        # load data
        self.loader.load_cinema_schedule(cinema_schedule_data)

    def _update_single_movie_data(self, imdb_id):
        """
        given imdb id, extract movie data and store it in database
        :param imdb_id: string
        :return: None
        """
        data_model = MovieData(imdb_id)
        current_movie_data = data_model.get_movie_data()
        self.loader.load_movie_data(current_movie_data)

    @staticmethod
    def _cinema_schedule_retrieve(cinema_list, cinema_schedule_data):
        for cinema in cinema_list:
            cinema_id, cinema_name, provider, cinema_url = cinema
            cinema_schedule = CinemaSchedule(cinema_name, cinema_url, provider)
            current_schedules = cinema_schedule.extract_cinema_schedule()

            # parse schedules and update data
            for movie in current_schedules:
                current_title = movie['title']
                if movie['title'] not in cinema_schedule_data:
                    cinema_schedule_data[current_title] = {}
                    current_title = cinema_schedule_data[current_title]
                    current_title['content'] = []
                else:
                    current_title = cinema_schedule_data[current_title]

                del movie['title']
                movie['cinema_id'] = cinema_id
                current_title['content'].append(movie)

    @staticmethod
    def _build_imdb_id(i):
        """
        this function takes in an integer and converts it to an imdb id
        :param i: integer
        :return: string
        """
        current_imdb_number = "{0:0=7d}".format(i)
        imdb_id = "tt" + current_imdb_number
        return imdb_id

if __name__ == '__main__':
    controller = ETLController()



