# Author: Balazs Kegl
# License: BSD 3 clause

import os
import sys
import numpy as np
import pandas as pd
from importlib import import_module
from sklearn.cross_validation import ShuffleSplit, train_test_split
# menu
import databoard.scores as scores
# menu polymorphism example
from databoard.regression_prediction import Predictions
from databoard.config import config_object, submissions_path
from databoard.config import raw_data_path, public_data_path, private_data_path

sys.path.append(os.path.dirname(os.path.abspath(submissions_path)))

# should be the same as the directory in ramp, and fab publish should also be
# called with the same name as parameter
ramp_name = 'amadeus'
# will be displayed on the web site
hackaton_title = 'Number of passengers prediction'
target_column_name = 'log_PAX'
drop_column_names = ['PAX']

cv_test_size = config_object.cv_test_size
held_out_test_size = 0.2
random_state = config_object.random_state
n_CV = config_object.num_cpus

raw_filename = os.path.join(raw_data_path, 'data_amadeus.csv')
train_filename = os.path.join(public_data_path, 'train.csv')
test_filename = os.path.join(private_data_path, 'test.csv')

score = scores.RMSE()


def read_data(df_filename):
    data = pd.read_csv(df_filename)
    return data


def prepare_data():
    df = read_data(raw_filename)
    df = df.drop(drop_column_names, axis=1)
    df[target_column_name] /= 0.5362  # for hiding the real number
    df_train, df_test = train_test_split(
        df, test_size=held_out_test_size, random_state=random_state)
    df_train.to_csv(train_filename)
    df_test.to_csv(test_filename)


def get_train_data():
    df_train = read_data(train_filename)
    X_train_df = df_train.drop(target_column_name, axis=1)
    y_train_array = df_train[target_column_name].values
    return X_train_df, y_train_array


def get_test_data():
    df_test = read_data(test_filename)
    X_test_df = df_test.drop(target_column_name, axis=1)
    y_test_array = df_test[target_column_name].values
    return X_test_df, y_test_array


def get_cv(y_train_array):
    cv = ShuffleSplit(y_train_array.shape[0], n_iter=n_CV,
                      test_size=cv_test_size, random_state=random_state)
    return cv


def train_submission(module_path, X_df, y_array, cv_is):
    # Feature extraction
    feature_extractor = import_module('.feature_extractor', module_path)
    fe = feature_extractor.FeatureExtractor()
    fe.fit(X_df, y_array)
    X_array = fe.transform(X_df)
    # Regression
    train_is, _ = cv_is
    X_train_array = np.array([X_array[i] for i in train_is])
    y_train_array = np.array([y_array[i] for i in train_is])
    regressor = import_module('.regressor', module_path)
    reg = regressor.Regressor()
    reg.fit(X_train_array, y_train_array)
    return fe, reg


def test_submission(trained_model, X_df, cv_is):
    fe, reg = trained_model
    # Feature extraction
    X_array = fe.transform(X_df)
    # Regression
    _, test_is = cv_is
    X_test_array = np.array([X_array[i] for i in test_is])
    y_prediction_array = reg.predict(X_test_array)
    return Predictions(y_pred=y_prediction_array)
