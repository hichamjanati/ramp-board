# Author: Balazs Kegl
# License: BSD 3 clause

import os
import sys
import pandas as pd
from importlib import import_module
from sklearn.cross_validation import ShuffleSplit, train_test_split
# menu
import scores
# menu polymorphism example
from .regression_prediction import Predictions
import config_databoard

sys.path.append(os.path.dirname(os.path.abspath(config_databoard.models_path)))

hackaton_title = 'Boston housing regression (test)'
target_column_name = 'medv'

cv_test_size = config_databoard.get_ramp_field('cv_test_size')
held_out_test_size = 0.2
random_state = config_databoard.get_ramp_field('random_state')
n_CV = config_databoard.get_ramp_field('num_cpus')

raw_filename = os.path.join(
    config_databoard.raw_data_path, 'boston_housing.csv')
train_filename = os.path.join(config_databoard.public_data_path, 'train.csv')
test_filename = os.path.join(config_databoard.private_data_path, 'test.csv')

score = scores.RMSE()


def read_data(filename, index_col=None):
    data = pd.read_csv(filename, index_col=index_col)
    y_array = data[target_column_name].values
    X_array = data.drop([target_column_name], axis=1).values
    return X_array, y_array


def prepare_data():
    df = pd.read_csv(raw_filename, index_col=0)
    df_train, df_test = train_test_split(
        df, test_size=held_out_test_size, random_state=random_state)
    df_train.to_csv(train_filename)
    df_test.to_csv(test_filename)


def get_train_data():
    X_train_array, y_train_array = read_data(train_filename)
    return X_train_array, y_train_array


def get_test_data():
    X_test_array, y_test_array = read_data(test_filename)
    return X_test_array, y_test_array


def get_cv(y_train_array):
    cv = ShuffleSplit(y_train_array.shape[0], n_iter=n_CV,
                      test_size=cv_test_size, random_state=random_state)
    return cv


def train_model(module_path, X_array, y_array, cv_is):
    train_is, _ = cv_is
    regressor = import_module('.regressor', module_path)
    reg = regressor.Regressor()
    reg.fit(X_array[train_is], y_array[train_is])
    return reg


def test_model(trained_model, X_array, cv_is):
    _, test_is = cv_is
    reg = trained_model
    y_pred = reg.predict(X_array[test_is])
    return Predictions(y_pred=y_pred)