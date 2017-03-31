"""
    Main class for recommendation operations
"""
from recommedation_algo.database import DatabaseHandler
from public_data.controller import ETLController
from datetime import datetime
from recommedation_algo.scale import UserScale
from recommedation_algo.similarity import MovieSimilarity

import logging
import warnings


class Recommender:

    USER_RATINGS_CRITERION = 8.0  # 4 stars or above can be considered a good seed for generating similar movies

    SIMILARITY_CRITERION = 0.5  # similarity index above 0.5 means roughly more than one similar feature

    RECOMMEND_CRITERION = 7.0  # user ratings are limited, a relatively lower criterion is good to generate more recom

    SIMILAR_MOVIE_POOL_SIZE = 50  # iteration wise, 50 similar movies will be selected and subjected to recommendation

    def __init__(self):
        self.controller = ETLController()
        self.db = DatabaseHandler()

    def run(self):
        """
        for each user, generate recommendations and store them
        :return: None
        """
        users = self.db.get_users()

        for user in users:
            user_id = user[0]
            recommender_list = self.get_single_user_recommendations(user_id)
            self.db.save_recommendations(recommender_list, user_id)

    def get_single_user_recommendations(self, user_id):
        """
        The recommendation logic is as follows:
            1. get all liked movies by the users,
               which will act as a selection criteria
               to get similar movies
            2. based the above criterion, select up to
               n movies from the database, order by their
               release time in descending order (recommending)
               new movies first
            3. predict the expected output using regression
               the user's historical ratings, select and recommend
               to users
        :param user_id: string
        :return: list
        """
        logging.warning("retrieving user watching history ...")
        user_history = self.db.get_user_history(user_id)

        logging.warning("size of user ratings pool:" + str(len(user_history)))

        similarity_seeds = self._generate_recommend_seeds(user_history)

        # no rating history found, directly return default list
        if len(similarity_seeds) == 0:
            logging.warning("no user rating history found, recommending default list ...")

            popular_movies = self.db.get_10_popular_movies()
            popular_list = []
            for popular in popular_movies:
                popular_list.append([popular[0], popular[1]])

            return popular_list

        similar_list = self._generate_similar_movies(similarity_seeds)
        recommend_list = self._generate_recommend_list(similar_list, user_id)
        return recommend_list

    def _generate_recommend_list(self, similar_list, user_id):
        logging.warning("initialising predicting process ...")

        scale = UserScale(user_id)
        recommend_list = []

        for potential in similar_list:
            public_ratings = self.db.get_public_rating(potential)

            if not public_ratings:
                self.controller.update_single_movie_rating(potential)
                public_ratings = self.db.get_public_rating(potential)

            if any(None in element for element in public_ratings):  # skip if the data is invalid
                continue

            imdb_rating, douban_rating, trakt_rating = public_ratings
            regressors = [imdb_rating[3], douban_rating[3], trakt_rating[3]]
            expected_score = scale.predict_user_score(regressors)[0]

            if expected_score > self.RECOMMEND_CRITERION:
                recommend_list.append([potential, expected_score])

        return recommend_list

    def _generate_similar_movies(self, user_list):
        similar_list = []
        current_year = int(datetime.now().strftime("%Y"))

        flag = True
        while flag:
            logging.warning("initialising movie pool selection ...")
            movie_pool = self.db.get_movie_id_by_year(current_year)

            logging.warning("size of pool:" + str(len(movie_pool)))

            for movie in movie_pool:
                movie_id = movie[0]

                current_movie_similarity = MovieSimilarity(user_list, movie_id)
                highest_similarity = current_movie_similarity.get_highest_similarity()
                if highest_similarity >= self.SIMILARITY_CRITERION and movie_id not in user_list:
                    similar_list.append(movie_id)

                # escape condition
                if len(similar_list) == self.SIMILAR_MOVIE_POOL_SIZE:
                    flag = False  # break outer loop
                    break

            logging.warning("searching for previous year ...")
            current_year -= 1

        return similar_list

    def _generate_recommend_seeds(self, user_pool):
        """
        given user watching history, generate similar
        movies that may be recommended
        :param user_pool: list
        :return: list
        """
        user_list = []
        for user_rating in user_pool:
            movie_id, score = user_rating
            if score >= self.USER_RATINGS_CRITERION:  # consider as favorable movie
                user_list.append(movie_id)
        return user_list


if __name__ == '__main__':
    warnings.filterwarnings(action="ignore", module="scipy", message="^internal gelsd")  # ignore lapack related warning
    logging.basicConfig(level=logging.INFO)
    recommender = Recommender()
    recommender.run()