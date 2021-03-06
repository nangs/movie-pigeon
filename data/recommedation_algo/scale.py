"""
    Using multi-linear regression to calculate the weight of each rating
    source for one user
"""
from sklearn import linear_model, exceptions
from recommedation_algo.database import DatabaseHandler
from data.public_data.controller import ETLController

import numpy


class UserScale:

    DEFAULT_WEIGHT = 1 / 3

    def __init__(self, user_id):
        self.user_id = user_id
        self.db = DatabaseHandler()
        self.controller = ETLController()

        self.model = linear_model.LinearRegression()
        self._fit_model()

    def _fit_model(self):
        """
        fit public ratings and user rating to
        a linear regression model
        :return: None
        """
        user_rating_records = self.db.get_user_history(self.user_id)

        if len(user_rating_records) == 0:  # no previous watching history
            return

        regressors = []
        responses = []

        for record in user_rating_records:
            current_movie_id = record[0]

            # regressors
            public_rating_records = self.db.get_public_rating(current_movie_id)

            if len(public_rating_records) < 3:
                continue

            if not public_rating_records:  # rating not available
                self.controller.update_single_movie_rating(current_movie_id)  # update rating
                public_rating_records = self.db.get_public_rating(current_movie_id)

            public_rating_records = sorted(public_rating_records, key=lambda x: x[1])  # sort records -> replace by sql
            current_set = []
            for regressor in public_rating_records:
                current_set.append(regressor[3])

            if None in current_set:  # skip invalid data points
                continue

            regressors.append(current_set)

            # response
            user_rating = record[1]
            responses.append(user_rating)
        self.model.fit(regressors, responses)

    def predict_user_score(self, public_ratings):
        """
        get the predicted results based on either
        history of rating, or average in the event
        that there is no history available
        :param public_ratings: list
        :return: float
        """
        try:
            self.model.predict([public_ratings])
        except exceptions.NotFittedError:
            return numpy.mean(public_ratings)

        return self.model.predict([public_ratings])
