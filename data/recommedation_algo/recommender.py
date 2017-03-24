"""
    Main class for recommendation operations

    # calculate raw score

    # get relevant movies pool (crude criteria) (waiting to be classified)

    # for every movie in pool
        # calculate multiplier : classification (logistic regression)
        # obtain final score (expected output)
        # sort and rank
        # store in database

"""
from database import DatabaseHandler
from public_data.controller import ETLController
from datetime import datetime
from scale import UserScale
from similarity import MovieSimilarity

import logging
import warnings


class Recommender:

    USER_CRITERION = 8.0

    SIMILARITY_CRITERION = 5.0

    RECOMMEND_CRITERION = 7.0

    SIMILAR_MOVIE_POOL_SIZE = 100

    def __init__(self):
        self.controller = ETLController()
        self.db = DatabaseHandler()

    def run(self):
        # for every user update scale
        # for every user generate recommendation if not enough
        pass

    def update_single_user_recommendations(self, user_id):
        # 1. get all liked movies by the users -> act as criteria to get similar movies movies
        logging.warning("retrieving user movie pool ...")
        user_pool = self.db.get_user_ratings(user_id)
        logging.warning("size of user pool:" + str(len(user_pool)))

        user_list = []
        for user_rating in user_pool:
            movie_id, score = user_rating
            if score >= self.USER_CRITERION:  # consider as favorable movie
                user_list.append(movie_id)

        # 2. get a pool of similar movies based the seeds
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
                highest_similarity = current_movie_similarity.get_similarity()

                if highest_similarity >= self.SIMILARITY_CRITERION and movie_id not in user_list:
                    similar_list.append(movie_id)

                # escape condition
                if len(similar_list) == 100:
                    flag = False  # break outer loop
                    break

            logging.warning("max searching for previous year ...")
            current_year -= 1  # continue to search on next year

        # 3. rank the pool using scales, recommend tops
        scale = UserScale(user_id)
        recommend_list = []
        for potential in similar_list:
            public_ratings = self.db.get_public_rating(potential)
            if not public_ratings:
                self.controller.update_single_movie_rating(potential)
                public_ratings = self.db.get_public_rating(potential)

            if any(None in element for element in public_ratings):
                continue

            imdb_rating, douban_rating, trakt_rating = public_ratings
            regressors = [imdb_rating[3], douban_rating[3], trakt_rating[3]]
            expected_score = scale.predict_user_score(regressors)[0]
            if expected_score > 7:
                recommend_list.append([potential, expected_score])

        print(recommend_list)
        return recommend_list


if __name__ == '__main__':
    warnings.filterwarnings(action="ignore", module="scipy", message="^internal gelsd")  # ignore lapack related warning
    logging.basicConfig(level=logging.INFO)
    recommender = Recommender()
    recommender.update_single_user_recommendations('8')
