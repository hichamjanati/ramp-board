import numpy as np
from .base_prediction import BasePrediction


class Predictions(BasePrediction):

    def __init__(self, labels=None, y_pred=None, y_true=None, f_name=None,
                 n_samples=None):
        self.labels = labels
        if y_pred is not None:
            self.y_pred = np.array(y_pred)
        elif y_true is not None:
            self.y_pred = np.array(y_true)
        elif f_name is not None:
            self.y_pred = np.load(f_name)
        elif n_samples is not None:
            self.y_pred = np.empty(n_samples, dtype=float)
            self.y_pred.fill(np.nan)
        else:
            raise ValueError("Missing init argument: y_pred, y_true, f_name "
                             "or n_samples")

    def set_valid_in_train(self, predictions, test_is):
        self.y_pred[test_is] = predictions.y_pred

    @property
    def valid_indexes(self):
        return ~np.isnan(self.y_pred)

    @property
    def y_pred_comb(self):
        """Return an array which can be combined by taking means."""
        return self.y_pred

    @property
    def n_samples(self):
        return self.y_pred.shape
