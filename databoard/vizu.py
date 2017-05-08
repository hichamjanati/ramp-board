import numpy as np
import pandas as pd
from databoard import db_tools
from bokeh.plotting import figure
from bokeh.models.sources import ColumnDataSource
from bokeh.models.formatters import DatetimeTickFormatter
from skimage.color import gray2rgb, rgb2gray


def make_step_df(pareto_df, event):
    n_pareto = len(pareto_df)
    pareto_df = pareto_df.set_index(1 + 2 * np.arange(n_pareto))
    for i in range(2, 2 * n_pareto, 2):
        pareto_df.loc[i] = pareto_df.loc[i - 1]
        pareto_df.set_value(i, 'x', pareto_df.loc[i + 1]['x'])
    pareto_df.loc[2 * n_pareto] = pareto_df.loc[2 * n_pareto - 1]
    pareto_df.set_value(2 * n_pareto, 'x', max(pareto_df['x']))
    pareto_df.loc[0] = pareto_df.loc[1]
    if event.official_score_type.is_lower_the_better:
        pareto_df.set_value(0, 'y', max(pareto_df['y']))
    else:
        pareto_df.set_value(0, 'y', min(pareto_df['y']))
    return pareto_df.sort_index()


def color_gradient(rgb, factor_array):
    colors = np.array(
        [(255 - rgb[0], 255 - rgb[2], 255 - rgb[2]) for _ in factor_array])
    colors = rgb2gray(colors)
    colors = gray2rgb(255 - np.array([color * factor for color, factor
                                      in zip(colors, factor_array)]))[:, :, 0]
    return colors


def add_pareto(df, col, worst, is_lower_the_better):
    """Add a column col + ' pareto' with 1s where col is on Pareto front.

    It is assumed that the dataframe is oredered by the
    'x' variable that defines the Pareto front.

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe to amend.
    col : string
        The numerical 'y' column.
    worst : number
        The worst possible value of col.
    is_lower_the_better : boolean

    Returns
    ----------
    df: pd.DataFrame
        The dataframe amended with the new column col + ' pareto'
    """
    df_ = df.copy()
    df_[col + ' pareto'] = 0
    best_score = worst
    if is_lower_the_better:
        for i, row in df.iterrows():
            score = row[col]
            if score < best_score:
                best_score = score
                df_[col + ' pareto'][i] = 1
    else:
        for i, row in df.iterrows():
            score = row[col]
            if score > best_score:
                best_score = score
                df_[col + ' pareto'][i] = 1
    return df_


def score_plot(event):
    submissions = db_tools.get_submissions(event.name)
    submissions = [submission for submission in submissions
                   if submission.is_public_leaderboard and submission.is_valid]
    score_names = [score_type.name for score_type in event.score_types]
    scoress = np.array([
        [score.valid_score_cv_bag
         for score in submission.ordered_scores(score_names)]
        for submission in submissions
    ]).T

    score_plot_df = pd.DataFrame()
    score_plot_df['submitted at (UTC)'] = [
        submission.submission_timestamp for submission in submissions]
    score_plot_df['contributivity'] = [
        submission.contributivity for submission in submissions]
    score_plot_df['historical contributivity'] = [
        submission.historical_contributivity for submission in submissions]
    for score_name in score_names:  # to make sure the column is created
        score_plot_df[score_name] = 0
    for score_name, scores in zip(score_names, scoress):
        score_plot_df[score_name] = scores

    score_name = event.official_score_name
    score_plot_df = score_plot_df[
        score_plot_df['submitted at (UTC)'] > event.opening_timestamp]
    score_plot_df = score_plot_df.sort_values('submitted at (UTC)')
    score_plot_df = add_pareto(
        score_plot_df, score_name, event.official_score_type.worst,
        event.official_score_type.is_lower_the_better)

    is_open = (score_plot_df['submitted at (UTC)'] >
               event.public_opening_timestamp).values

    max_contributivity = max(
        0.0000001, max(score_plot_df['contributivity'].values))
    max_historical_contributivity = max(0.0000001, max(
        score_plot_df['historical contributivity'].values))

    fill_color_1 = (176, 23, 31)
    fill_color_2 = (16, 78, 139)
    fill_colors_1 = color_gradient(
        fill_color_1, score_plot_df['contributivity'].values /
        max_contributivity)
    fill_colors_2 = color_gradient(
        fill_color_2, score_plot_df['historical contributivity'].values /
        max_historical_contributivity)
    fill_colors = np.minimum(fill_colors_1, fill_colors_2)
    print max_historical_contributivity
    fill_colors = ["#%02x%02x%02x" % (c[0], c[1], c[2]) for c in fill_colors]

    score_plot_df['x'] = score_plot_df['submitted at (UTC)']
    score_plot_df['y'] = score_plot_df[score_name]
    score_plot_df['line_color'] = 'royalblue'
    score_plot_df['circle_size'] = 8
    score_plot_df['line_color'] = 'royalblue'
    score_plot_df['line_color'][is_open] = 'coral'
    score_plot_df['fill_color'] = fill_colors
    score_plot_df['fill_alpha'] = 0.5
    score_plot_df['line_width'] = 0
    score_plot_df['label'] = 'closed phase'
    score_plot_df['label'][is_open] = 'open phase'

    source = ColumnDataSource(score_plot_df)
    pareto_df = make_step_df(score_plot_df[
        score_plot_df[score_name + ' pareto'] == 1].copy(), event)
    source_pareto = ColumnDataSource(pareto_df)

    tools = ['pan,wheel_zoom,box_zoom,reset,previewsave,tap']
    p = figure(plot_width=900, plot_height=600, tools=tools, title='Scores')

    p.circle(
        'x', 'y', size='circle_size', line_color='line_color',
        fill_color='fill_color', fill_alpha='fill_alpha', line_width=1,
        source=source, legend='label'
    )
    p.line(
        'x', 'y', line_width=3, line_color='goldenrod', source=source_pareto,
        legend='best score', alpha=0.9
    )

    p.xaxis.formatter = DatetimeTickFormatter(formats=dict(
        hours=["%d %B %Y"],
        days=["%d %B %Y"],
        months=["%d %B %Y"],
        years=["%d %B %Y"],
    ))
    p.xaxis.major_label_orientation = np.pi / 4

    if event.official_score_type.is_lower_the_better:
        p.yaxis.axis_label = score_name + ' (the lower the better)'
        p.legend.location = 'top_right'
    else:
        p.yaxis.axis_label = score_name + ' (the greater the better)'
        p.legend.location = 'bottom_right'
    p.xaxis.axis_label = 'submission timestamp (UTC)'
    p.xaxis.axis_label_text_font_size = '14pt'
    p.yaxis.axis_label_text_font_size = '14pt'
    p.legend.label_text_font_size = '14pt'
    p.title.text_font_size = '16pt'
    p.xaxis.major_label_text_font_size = '10pt'
    p.yaxis.major_label_text_font_size = '10pt'

    return p